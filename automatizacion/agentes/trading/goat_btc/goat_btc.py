#!/usr/bin/env python3
"""
goat_btc.py — G.O.A.T PROTOCOL BTC/USD v1.0
Main entry point for the GOAT BTC trading agent.
Orchestrates all modules: BinanceFeed, indicators, classifier, scorer,
terminal UI, SeñalesDB, SessionSummary, and ChatBTC.
"""

import sys
import os
import json
import logging
import threading
import time
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from collections import deque

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('goat_btc')

# ── Imports ──────────────────────────────────────────────────────────────────

try:
    from .core.binance_feed import BinanceFeed
except ImportError:
    from trading.goat_btc.core.binance_feed import BinanceFeed

try:
    from .core.indicadores import (
        calcular_bb, calcular_bbw, clasificar_bbw, calcular_cvd_real,
        calcular_delta_vela, calcular_adx, calcular_volumen_relativo,
        calcular_imbalance_book, clasificar_imbalance,
    )
except ImportError:
    from trading.goat_btc.core.indicadores import (
        calcular_bb, calcular_bbw, clasificar_bbw, calcular_cvd_real,
        calcular_delta_vela, calcular_adx, calcular_volumen_relativo,
        calcular_imbalance_book, clasificar_imbalance,
    )

try:
    from .core.clasificador import clasificar_toque
except ImportError:
    from trading.goat_btc.core.clasificador import clasificar_toque

try:
    from .core.scorer import calcular_score
except ImportError:
    from trading.goat_btc.core.scorer import calcular_score

try:
    from .core.terminal_ui import TerminalUI
except ImportError:
    from trading.goat_btc.core.terminal_ui import TerminalUI

try:
    from .memory.señales_db import SeñalesDB
except ImportError:
    from trading.goat_btc.memory.señales_db import SeñalesDB

try:
    from .memory.session_summary import SessionSummary
except ImportError:
    from trading.goat_btc.memory.session_summary import SessionSummary

try:
    from .conversacion.claude_chat import ChatBTC
except ImportError:
    from trading.goat_btc.conversacion.claude_chat import ChatBTC

# ── AGI Telegram client ─────────────────────────────────────────────────────

AGI_TELEGRAM_URL = os.getenv('AGI_TELEGRAM_URL', 'https://quantumhive-agi-telegram.onrender.com')
AGI_TELEGRAM_TIMEOUT = 180  # 3 minutos máximo esperando confirmación

# ── Binance Executor ────────────────────────────────────────────────────────

BINANCE_EXECUTOR_AVAILABLE = False
binance_executor = None
try:
    from .core.binance_executor import (
        ejecutar_orden, cerrar_posicion, get_posicion_activa,
        get_balance, set_leverage, BINANCE_TESTNET,
    )
    BINANCE_EXECUTOR_AVAILABLE = True
    logger.info(f"Binance Executor disponible (Testnet: {BINANCE_TESTNET})")
except Exception as e:
    logger.warning(f"Binance Executor no disponible: {e}")

# ── Event Bus ────────────────────────────────────────────────────────────────

EVENT_BUS_AVAILABLE = False
event_bus = None
try:
    from event_bus import event_bus
    EVENT_BUS_AVAILABLE = True
except Exception:
    pass

# ── Global instances ─────────────────────────────────────────────────────────

feed = BinanceFeed()
senales_db = SeñalesDB()
session_summary = SessionSummary()
try:
    chat_btc = ChatBTC()
except Exception:
    chat_btc = None
terminal = TerminalUI()

# ── Helpers ──────────────────────────────────────────────────────────────────

def _extraer_ohlcv(klines):
    opens = [k["open"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    closes = [k["close"] for k in klines]
    volumes = [k["volume"] for k in klines]
    return opens, highs, lows, closes, volumes


def _precios_tocaron_banda(klines, bb_sup, bb_inf, n=5):
    if bb_sup is None or bb_inf is None:
        return 0, False, False
    klines_list = list(klines)
    examinar = klines_list[-n:] if len(klines_list) >= n else klines_list
    count = 0
    toco_sup = False
    toco_inf = False
    for k in examinar:
        if k["high"] >= bb_sup:
            count += 1
            toco_sup = True
        if k["low"] <= bb_inf:
            count += 1
            toco_inf = True
    return count, toco_sup, toco_inf


def _calcular_deltas_velas(klines, n=5):
    klines_list = list(klines)
    deltas = []
    for k in klines_list[-n:]:
        delta = calcular_delta_vela(
            k["open"], k["high"], k["low"], k["close"], k["volume"]
        )
        deltas.append(delta)
    return deltas


# ── AGI Telegram helpers ────────────────────────────────────────────────────

def _enviar_senal_a_agi(senal_id: int, direccion: str, score: int, precio: float,
                        clasificacion: str = "", confluencias: list = None) -> Optional[int]:
    """Envía señal a AGI Telegram, devuelve pendiente_id o None si falla."""
    try:
        import requests as req
        payload = {
            "senal_id": senal_id,
            "direccion": direccion,
            "score": score,
            "precio": precio,
            "clasificacion": clasificacion,
            "confluencias": confluencias or [],
        }
        resp = req.post(f"{AGI_TELEGRAM_URL}/goat/senal", json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Señal {senal_id} enviada a AGI Telegram, pendiente_id={data.get('pendiente_id')}")
            return data.get('pendiente_id')
        logger.warning(f"AGI Telegram respondió {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        logger.warning(f"Error enviando señal a AGI Telegram: {e}")
        return None


def _esperar_confirmacion_agi(pendiente_id: int, timeout: int = AGI_TELEGRAM_TIMEOUT) -> str:
    """Espera confirmación de AGI Telegram hasta timeout. Devuelve status."""
    try:
        import requests as req
        import time as _time
        inicio = _time.time()
        while _time.time() - inicio < timeout:
            resp = req.get(f"{AGI_TELEGRAM_URL}/goat/senal/{pendiente_id}/status", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get('status', 'pendiente')
                if status != 'pendiente':
                    logger.info(f"AGI confirmación recibida: {status}")
                    return status
            _time.sleep(3)
        logger.info(f"AGI timeout {timeout}s para pendiente_id={pendiente_id}")
        return 'expirada'
    except Exception as e:
        logger.warning(f"Error esperando confirmación AGI: {e}")
        return 'error'


# ── Signal handler ───────────────────────────────────────────────────────────

_signal_received = False

def _signal_handler(sig, frame):
    global _signal_received
    logger.info(f"Señal {sig} recibida, cerrando G.O.A.T...")
    _signal_received = True
    terminal.detener()
    feed.detener()


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ── Main processing loop (runs in background thread) ────────────────────────

def _main_processing():
    signal_ids = set()
    last_signal_time = 0.0
    inicio_sesion = datetime.now(timezone.utc).isoformat()

    while not terminal.stop_event.is_set() and not _signal_received:
        try:
            # ── Get data from feed ─────────────────────────────────
            klines_1m = feed.get_klines("1m")
            klines_5m = feed.get_klines("5m")
            klines_15m = feed.get_klines("15m")
            klines_1h = feed.get_klines("1h")
            trades = feed.get_trades()
            bids, asks = feed.get_book()
            precio = feed.get_last_price()

            if precio is None or len(klines_15m) < 30 or len(klines_1h) < 30:
                time.sleep(1)
                continue

            # ── Extract OHLCV ──────────────────────────────────────
            _, highs_m15, lows_m15, closes_m15, vols_m15 = _extraer_ohlcv(klines_15m)
            _, _, _, closes_h1, _ = _extraer_ohlcv(klines_1h)
            _, _, _, closes_m5, vols_m5 = _extraer_ohlcv(klines_5m)
            _, _, _, closes_m1, _ = _extraer_ohlcv(klines_1m)

            # ── Bollinger Bands ────────────────────────────────────
            # M15
            try:
                bb_media_m15, bb_sup_m15, bb_inf_m15 = calcular_bb(closes_m15, 30, 3.0)
                bbw_m15 = calcular_bbw(bb_media_m15, bb_sup_m15, bb_inf_m15) if bb_media_m15 else 0.0
            except Exception:
                bb_media_m15 = bb_sup_m15 = bb_inf_m15 = None
                bbw_m15 = 0.0

            # H1
            try:
                bb_media_h1, bb_sup_h1, bb_inf_h1 = calcular_bb(closes_h1, 30, 3.0)
                bbw_h1 = calcular_bbw(bb_media_h1, bb_sup_h1, bb_inf_h1) if bb_media_h1 else 0.0
            except Exception:
                bb_media_h1 = bb_sup_h1 = bb_inf_h1 = None
                bbw_h1 = 0.0

            # M5
            try:
                bb_media_m5, bb_sup_m5, bb_inf_m5 = calcular_bb(closes_m5, 30, 3.0)
            except Exception:
                bb_media_m5 = bb_sup_m5 = bb_inf_m5 = None

            # M1
            try:
                bb_media_m1, bb_sup_m1, bb_inf_m1 = calcular_bb(closes_m1, 30, 3.0)
            except Exception:
                bb_media_m1 = bb_sup_m1 = bb_inf_m1 = None

            # ── ADX M15 ──────────────────────────────────────────
            try:
                adx_m15 = calcular_adx(highs_m15, lows_m15, closes_m15, 14)
            except Exception:
                adx_m15 = 0.0

            # ── CVD (Cumulative Volume Delta) ─────────────────────
            trades_list = list(trades)
            try:
                cvd_largo = calcular_cvd_real(trades_list[-1000:]) if len(trades_list) >= 1000 else calcular_cvd_real(trades_list)
            except Exception:
                cvd_largo = 0
            try:
                cvd_medio = calcular_cvd_real(trades_list[-200:]) if len(trades_list) >= 200 else calcular_cvd_real(trades_list)
            except Exception:
                cvd_medio = 0
            try:
                cvd_corto = calcular_cvd_real(trades_list[-50:]) if len(trades_list) >= 50 else calcular_cvd_real(trades_list)
            except Exception:
                cvd_corto = 0

            # ── Delta última vela (M5) ───────────────────────────
            try:
                ultima_vela = klines_5m[-1] if klines_5m else None
                if ultima_vela:
                    delta_ultima = calcular_delta_vela(
                        ultima_vela["open"], ultima_vela["high"],
                        ultima_vela["low"], ultima_vela["close"],
                        ultima_vela["volume"],
                    )
                else:
                    delta_ultima = 0.0
            except Exception:
                delta_ultima = 0.0

            # ── Volumen relativo (M15) ───────────────────────────
            try:
                vol_relativo = calcular_volumen_relativo(vols_m15)
            except Exception:
                vol_relativo = 0.0

            # ── Imbalance book ────────────────────────────────────
            try:
                imbalance = calcular_imbalance_book(bids, asks, 10)
            except Exception:
                imbalance = 0.0

            # ── Velas tocando banda (últimas 5 M5) ───────────────
            try:
                velas_tocando, toco_sup_m5, toco_inf_m5 = _precios_tocaron_banda(
                    klines_5m, bb_sup_m5, bb_inf_m5, 5
                )
            except Exception:
                velas_tocando = 0
                toco_sup_m5 = False
                toco_inf_m5 = False

            # ── Últimas deltas de velas (M5) ─────────────────────
            try:
                deltas_velas = _calcular_deltas_velas(klines_5m, 5)
            except Exception:
                deltas_velas = []

            # ── Build indicadores dict ────────────────────────────
            indicadores_dict = {
                "precio_actual": precio,
                "bb_superior_m5": bb_sup_m5,
                "bb_inferior_m5": bb_inf_m5,
                "bb_media_m5": bb_media_m5,
                "toco_bb_superior_m5": toco_sup_m5,
                "toco_bb_inferior_m5": toco_inf_m5,
                "precio_toco_superior": toco_sup_m5,
                "precio_toco_inferior": toco_inf_m5,
                "bbw_m15": bbw_m15,
                "adx_m15": adx_m15,
                "cvd_largo": cvd_largo,
                "cvd_largo_H1": cvd_largo,
                "cvd_corto": cvd_corto,
                "vol_relativo": vol_relativo,
                "vol_relativo_sostenido": vol_relativo > 1.3,
                "imbalance_book": imbalance,
                "delta_ultima_vela": delta_ultima,
                "ultimas_5_deltas": deltas_velas,
                "velas_tocando_banda": velas_tocando,
            }

            # ── Classify and score ────────────────────────────────
            try:
                clasificacion = clasificar_toque(indicadores_dict)
            except Exception:
                clasificacion = {"clasificacion": "error", "bloquear_senal": True, "confianza": 0.0}

            try:
                resultado_score = calcular_score(indicadores_dict, clasificacion)
            except Exception:
                resultado_score = {"score": 0, "direccion": None, "confluencias": [], "es_alerta": False}

            # ── Score (must be before raz_lines to avoid NameError) ─
            score = resultado_score.get("score", 0)
            bloquear = clasificacion.get("bloquear_senal", True)
            direccion = resultado_score.get("direccion")

            # ── Build terminal data ───────────────────────────────
            regimen_h1 = clasificar_bbw(bbw_h1) if bbw_h1 else "\u2014"
            regimen_m15 = clasificar_bbw(bbw_m15) if bbw_m15 else "\u2014"

            dist_sup_h1 = ((bb_sup_h1 - precio) / precio * 100) if bb_sup_h1 and precio else 0.0
            dist_inf_h1 = ((precio - bb_inf_h1) / precio * 100) if bb_inf_h1 and precio else 0.0

            macro_data = {
                "precio": precio,
                "bb_sup": bb_sup_h1,
                "bb_media": bb_media_h1,
                "bb_inf": bb_inf_h1,
                "distancia_sup_pct": dist_sup_h1,
                "distancia_inf_pct": dist_inf_h1,
                "cvd_largo": cvd_largo,
                "bbw": bbw_h1,
                "regimen": regimen_h1,
            }

            regimen_data = {
                "precio": precio,
                "bb_sup": bb_sup_m15,
                "bb_media": bb_media_m15,
                "bb_inf": bb_inf_m15,
                "adx": adx_m15,
                "bbw": bbw_m15,
                "cvd_medio": cvd_medio,
                "clasificacion": regimen_m15,
                "senal_bloqueada": clasificacion.get("bloquear_senal", False),
            }

            velas_m1 = []
            for k in list(klines_1m)[-5:]:
                d = calcular_delta_vela(
                    k["open"], k["high"], k["low"], k["close"], k["volume"]
                )
                velas_m1.append({
                    "time": datetime.fromtimestamp(k["time"], tz=timezone.utc).strftime("%H:%M"),
                    "delta": d,
                })

            flujo_data = {
                "ultimas_5_velas": velas_m1,
                "cvd_corto": cvd_corto,
                "imbalance": imbalance,
                "vol_relativo": vol_relativo,
            }

            # ── Reasoning lines ────────────────────────────────────
            raz_lines = []
            if bb_media_m15:
                raz_lines.append(f"Analizando BB 30/3.0 en M15 — Sup: ${bb_sup_m15:,.0f} Med: ${bb_media_m15:,.0f} Inf: ${bb_inf_m15:,.0f}")
            raz_lines.append(f"CVD acumulado: {cvd_largo:+,d} {'— presion compradora' if cvd_largo > 0 else '— presion vendedora' if cvd_largo < 0 else '— neutral'}")
            raz_lines.append(f"ADX {adx_m15:.1f} — {'tendencia fuerte activa' if adx_m15 > 25 else 'sin tendencia clara' if adx_m15 < 20 else 'tendencia debil'}")
            if clasificacion.get("clasificacion") == "surfeo":
                raz_lines.append("Clasificando regimen: TENDENCIA — rebotes bloqueados")
            elif clasificacion.get("clasificacion") == "rebote":
                raz_lines.append("Clasificando regimen: RANGO — rebotes habilitados")
            else:
                raz_lines.append("Clasificando regimen: modo conservador — esperando confirmacion")
            if resultado_score.get("es_alerta"):
                raz_lines.append(f"Senal detectada: {resultado_score.get('direccion', 'N/A')} | Score: {resultado_score['score']}/100")
            else:
                raz_lines.append("Monitoreando M1 para cambio de momentum...")
                if score > 0 and score < 65:
                    raz_lines.append(f"Score parcial: {score} — esperando convergencia de factores")
            for rl in raz_lines:
                terminal.agregar_razonamiento(rl)

            # ── Update terminal ───────────────────────────────────
            try:
                senales_hoy = 0
                try:
                    stats = senales_db.obtener_estadisticas()
                    senales_hoy = stats.get("total_senales", 0)
                except Exception:
                    pass
                header_data = {
                    "precio": precio,
                    "cambio_24h": 0.0,
                    "regimen": regimen_m15,
                }
                status_data = {
                    "precio": precio,
                    "cvd_largo": cvd_largo,
                    "adx": adx_m15,
                    "regimen": regimen_m15.upper(),
                    "senales_hoy": senales_hoy,
                }
                terminal.actualizar(macro_data, regimen_data, flujo_data, status_data=status_data, header_data=header_data)
            except Exception:
                pass

            # ── Signal detection ──────────────────────────────────

            if score >= 65 and direccion and not bloquear:
                ahora = time.time()
                signal_key = f"{direccion}_{precio:.2f}"

                if signal_key not in signal_ids and (ahora - last_signal_time) >= 30:
                    signal_ids.add(signal_key)
                    last_signal_time = ahora

                    if len(signal_ids) > 1000:
                        signal_ids.clear()

                    direccion_up = direccion.upper()
                    logger.info(f"\u26a1 SEÑAL DETECTADA: {direccion_up} | Score: {score}/100 | Precio: ${precio:,.0f}")

                    senal_info = {
                        "tipo": direccion_up,
                        "score": score,
                        "precio": precio,
                        "bb_inf": bb_inf_m5,
                        "confluencias": resultado_score.get("confluencias", []),
                        "clasificacion": clasificacion.get("clasificacion", ""),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    terminal.mostrar_senal(senal_info)

                    # Publish to Event Bus
                    if EVENT_BUS_AVAILABLE and event_bus is not None:
                        try:
                            event_data = {
                                "agente": "G.O.A.T",
                                "tipo": "señal_trading",
                                "direccion": direccion_up,
                                "score": score,
                                "precio": precio,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "clasificacion": clasificacion.get("clasificacion", ""),
                                "confluencias": resultado_score.get("confluencias", []),
                            }
                            event_bus.publicar("señal_trading", "G.O.A.T", payload=event_data)
                        except Exception as e:
                            logger.warning(f"Error publicando evento: {e}")

                    # Save to SQLite
                    senal_data = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "direccion": direccion,
                        "score": score,
                        "precio_entrada": precio,
                        "bb_superior": bb_sup_m5,
                        "bb_media": bb_media_m5,
                        "bb_inferior": bb_inf_m5,
                        "cvd_corto": cvd_corto,
                        "cvd_largo": cvd_largo,
                        "adx": adx_m15,
                        "bbw": bbw_m15,
                        "clasificacion": clasificacion.get("clasificacion", ""),
                        "confluencias": resultado_score.get("confluencias", []),
                    }
                    senal_id = None
                    try:
                        senal_id = senales_db.guardar_senal(senal_data)
                    except Exception as e:
                        logger.warning(f"Error guardando señal: {e}")

                    # ── AGI Telegram confirmation ──────────────────
                    pendiente_id = _enviar_senal_a_agi(
                        senal_id, direccion_up, score, precio,
                        clasificacion.get("clasificacion", ""),
                        resultado_score.get("confluencias", []),
                    )

                    if pendiente_id is not None:
                        print(f"\n⚡ Señal {direccion_up} enviada a Telegram — esperando confirmación...")
                        resultado_agi = _esperar_confirmacion_agi(pendiente_id)

                        if resultado_agi == 'ejecutada':
                            print(f"✅ Señal CONFIRMADA por Telegram: {direccion_up} @ ${precio:,.0f}")
                            logger.info(f"Señal CONFIRMADA vía AGI: {direccion_up} @ {precio}")
                            try:
                                if senal_id:
                                    senales_db.actualizar_resultado_agi(senal_id, "confirmada", "✅ Confirmada vía Telegram")
                            except Exception:
                                pass

                            # Ejecutar orden si binance_executor disponible
                            if BINANCE_EXECUTOR_AVAILABLE:
                                try:
                                    set_leverage()
                                    resultado_orden = ejecutar_orden(direccion_up, precio)
                                    logger.info(f"Orden ejecutada: {resultado_orden}")
                                except Exception as e:
                                    logger.warning(f"Error ejecutando orden: {e}")
                            else:
                                logger.info(f"[SIMULACIÓN] Orden {direccion_up} no ejecutada (sin executor)")

                        elif resultado_agi == 'rechazada':
                            print(f"❌ Señal RECHAZADA por Telegram: {direccion_up} @ ${precio:,.0f}")
                            logger.info(f"Señal RECHAZADA vía AGI: {direccion_up} @ {precio}")
                            try:
                                if senal_id:
                                    senales_db.actualizar_resultado_agi(senal_id, "saltada", "❌ Rechazada vía Telegram")
                            except Exception:
                                pass

                        else:
                            print(f"⏰ Timeout — señal {direccion_up} simulada para tracking")
                            logger.info(f"Señal expirada (timeout): {direccion_up} @ {precio}")
                            try:
                                if senal_id:
                                    senales_db.actualizar_resultado_agi(senal_id, "no_ejecutada", "⏰ Timeout AGI")
                            except Exception:
                                pass

                    else:
                        # AGI Telegram no disponible → registrar sin bloquear
                        logger.warning(f"AGI Telegram no disponible, señal {senal_id} registrada para tracking")
                        try:
                            if senal_id:
                                senales_db.actualizar_resultado_agi(
                                    senal_id, "pendiente",
                                    "AGI no disponible, pendiente de revisión"
                                )
                        except Exception:
                            pass

        except Exception as e:
            logger.warning(f"Error en ciclo principal: {e}", exc_info=True)

        time.sleep(3)

    logger.info("Ciclo principal finalizado")


# ── Main orchestrator ───────────────────────────────────────────────────────

def ejecutar():
    feed.iniciar()
    logger.info("Feed Binance iniciado, esperando datos iniciales...")
    time.sleep(3)

    logger.info("Iniciando terminal visual...")
    processing_thread = threading.Thread(target=_main_processing, daemon=True)
    processing_thread.start()

    logger.info("G.O.A.T PROTOCOL operativo — Terminal Live en pantalla principal")
    terminal.iniciar()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("G.O.A.T PROTOCOL BTC/USD v1.0 — Iniciando...")
        logger.info("=" * 60)
        ejecutar()
    except KeyboardInterrupt:
        logger.info("G.O.A.T detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
    finally:
        feed.detener()
        logger.info("G.O.A.T PROTOCOL finalizado")

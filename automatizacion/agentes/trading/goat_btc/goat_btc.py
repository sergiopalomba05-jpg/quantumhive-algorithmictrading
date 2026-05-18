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
    from .core.okx_feed import OKXFeed
except ImportError:
    from trading.goat_btc.core.okx_feed import OKXFeed

try:
    from .core.indicadores import (
        calcular_bb, clasificar_bbw, calcular_cvd_real,
        calcular_delta_vela, calcular_adx, calcular_volumen_relativo,
        calcular_imbalance_book,
    )
except ImportError:
    from trading.goat_btc.core.indicadores import (
        calcular_bb, clasificar_bbw, calcular_cvd_real,
        calcular_delta_vela, calcular_adx, calcular_volumen_relativo,
        calcular_imbalance_book,
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
    from .core.signal_engine import (
        calcular_score_scalper, verificar_bloqueos, SCORE_MINIMO_ENTRADA,
        SCORE_MINIMO_CALIDAD, SCALPER_CONFIG, BLOQUEOS_SCALPER,
    )
except ImportError:
    from trading.goat_btc.core.signal_engine import (
        calcular_score_scalper, verificar_bloqueos, SCORE_MINIMO_ENTRADA,
        SCORE_MINIMO_CALIDAD, SCALPER_CONFIG, BLOQUEOS_SCALPER,
    )

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

# ── OKX Executor (BTC-USDT-SWAP Demo) ────────────────────────────────────────

OKX_EXECUTOR_AVAILABLE = False
_ejecutar_orden = None
_cerrar_posicion = None
_get_posicion_activa = None
_get_balance = None
_set_leverage = None
_calcular_sl_tp = None
_monitorear_sl_tp = None
_get_precio_actual = None
try:
    from .core.okx_executor import (
        ejecutar_orden as _ejecutar_orden, cerrar_posicion as _cerrar_posicion,
        get_posicion_activa as _get_posicion_activa, get_balance as _get_balance,
        set_leverage as _set_leverage,
        calcular_sl_tp as _calcular_sl_tp, monitorear_sl_tp as _monitorear_sl_tp,
        get_precio_actual as _get_precio_actual,
    )
    OKX_EXECUTOR_AVAILABLE = True
    logger.info("OKX Executor (BTC-USDT-SWAP Demo) disponible")
except ImportError:
    try:
        from trading.goat_btc.core.okx_executor import (
            ejecutar_orden as _ejecutar_orden, cerrar_posicion as _cerrar_posicion,
            get_posicion_activa as _get_posicion_activa, get_balance as _get_balance,
            set_leverage as _set_leverage,
            calcular_sl_tp as _calcular_sl_tp, monitorear_sl_tp as _monitorear_sl_tp,
            get_precio_actual as _get_precio_actual,
        )
        OKX_EXECUTOR_AVAILABLE = True
        logger.info("OKX Executor (BTC-USDT-SWAP Demo) disponible")
    except Exception as e:
        logger.warning(f"OKX Executor no disponible: {e}")

# ── Event Bus ────────────────────────────────────────────────────────────────

EVENT_BUS_AVAILABLE = False
event_bus = None
try:
    from event_bus import event_bus
    EVENT_BUS_AVAILABLE = True
except Exception:
    pass

# ── Global instances ─────────────────────────────────────────────────────────

feed = OKXFeed()
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


# ── Autonomous execution ─────────────────────────────────────────────────────

AGI_TELEGRAM_URL = os.getenv('AGI_TELEGRAM_URL', 'https://quantumhive-agi-telegram.onrender.com')
CEREBRO_API_URL = f"http://localhost:{os.getenv('CEREBRO_PORT', '5001')}"


def _publicar_evento_cerebro(tipo: str, payload: dict):
    """Publica evento al Cerebro (best-effort, no bloquea)."""
    try:
        import requests as req
        req.post(f"{CEREBRO_API_URL}/evento", json={
            "tipo": tipo, "payload": payload, "origen": "goat_btc",
        }, timeout=2)
    except Exception:
        pass


def _notificar_agi(payload: dict):
    """Envía notificación a AGI Telegram (best-effort, no bloquea)."""
    try:
        import requests as req
        req.post(f"{AGI_TELEGRAM_URL}/goat/senal", json=payload, timeout=5)
    except Exception:
        pass


def _ejecutar_senal_automatica(senal_id: int, direccion: str, score: int, precio: float,
                                clasificacion: str = "", confluencias: list = None,
                                sl: float = None, tp: float = None) -> bool:
    """Ejecuta orden inmediatamente y lanza monitoreo de posición.
    Retorna True si la orden se ejecutó con éxito, False si falló.
    """
    logger.info(f"🚀 Ejecutando señal autónoma #{senal_id}: {direccion} @ ${precio:,.0f}")

    # 1. Ejecutar orden en OKX
    resultado_orden = None
    if OKX_EXECUTOR_AVAILABLE:
        try:
            resultado_orden = _ejecutar_orden(direccion, precio)
            if resultado_orden is None:
                logger.error(f"❌ Orden #{senal_id} FALLÓ — OKX retornó None (credenciales o API error)")
                return False
            logger.info(f"✅ Orden ejecutada: {resultado_orden}")
        except Exception as e:
            logger.error(f"❌ Error ejecutando orden #{senal_id}: {e}")
            try:
                senales_db.actualizar_resultado_agi(senal_id, "error_ejecucion", str(e))
            except Exception:
                pass
            return False
    else:
        logger.info(f"[SIMULACIÓN] Orden {direccion} no ejecutada (sin executor)")
        resultado_orden = {"orderId": f"sim_{int(time.time())}", "status": "SIMULATED"}

    # 2. Calcular SL/TP
    if sl is None or tp is None:
        try:
            sl, tp = _calcular_sl_tp(precio, direccion)
        except Exception:
            logger.warning("No se pudieron calcular SL/TP, usando defaults")
            sl = round(precio * 0.997, 1) if direccion.upper() == 'LONG' else round(precio * 1.003, 1)
            tp = round(precio * 1.007, 1) if direccion.upper() == 'LONG' else round(precio * 0.993, 1)

    # 3. Publicar evento al Cerebro
    _publicar_evento_cerebro("senal_detectada", {
        "direccion": direccion, "score": score, "precio": precio,
        "confluencias": confluencias or [], "senal_id": senal_id,
        "order_id": resultado_orden.get("orderId", "sim"),
    })

    # 4. Notificar entrada a AGI
    _notificar_agi({
        "tipo": "entrada",
        "senal_id": senal_id,
        "direccion": direccion,
        "precio": precio,
        "sl": sl,
        "tp": tp,
        "score": score,
        "confluencias": confluencias or [],
    })

    # 5. Iniciar monitoreo de SL/TP en background
    try:
        _monitorear_sl_tp(
            senal_id=senal_id,
            side=direccion,
            entry_price=precio,
            sl=sl,
            tp=tp,
            callback=lambda r: _on_cierre_posicion(r, senal_id, direccion, precio),
            poll_interval=5,
            breakeven_at_50pct=True,
        )
    except Exception as e:
        logger.error(f"Error iniciando monitoreo #{senal_id}: {e}")

    return True


def _on_cierre_posicion(resultado: dict, senal_id: int, direccion: str, precio_entrada: float):
    """Callback cuando una posición se cierra por SL o TP."""
    logger.info(f"📩 Cierre recibido para #{senal_id}: {resultado}")

    pnl = resultado.get('pnl_usdt', 0)
    ESTADO_TRADING["pnl_diario"] += pnl
    if pnl < 0:
        ESTADO_TRADING["perdida_diaria"] += abs(pnl)

    # Actualizar SQLite
    es_ganancia = pnl > 0
    resultado_str = "ganadora" if es_ganancia else "perdedora"
    try:
        senales_db.actualizar_cierre(
            senal_id=senal_id,
            precio_cierre=resultado['precio_cierre'],
            pnl_usdt=resultado['pnl_usdt'],
            duracion_minutos=resultado['duracion_minutos'],
            resultado=resultado_str,
        )
    except Exception as e:
        logger.warning(f"Error actualizando cierre #{senal_id}: {e}")

    # Notificar cierre a AGI
    _notificar_agi({
        "tipo": "cierre",
        "senal_id": senal_id,
        "direccion": direccion,
        "precio_entrada": precio_entrada,
        "precio_cierre": resultado['precio_cierre'],
        "pnl_usdt": resultado['pnl_usdt'],
        "pnl_pct": resultado.get('pnl_pct', 0),
        "duracion_minutos": resultado['duracion_minutos'],
        "tipo_salida": resultado.get('tipo_salida', ''),
    })

    # Publicar evento de cierre al Cerebro
    _publicar_evento_cerebro("posicion_cerrada", {
        "senal_id": senal_id, "direccion": direccion,
        "precio_entrada": precio_entrada,
        "precio_cierre": resultado['precio_cierre'],
        "pnl_usdt": resultado['pnl_usdt'],
        "duracion_minutos": resultado['duracion_minutos'],
        "tipo_salida": resultado.get('tipo_salida', ''),
    })

    # Mostrar en terminal
    try:
        emoji = "✅" if es_ganancia else "🛡️"
        terminal.agregar_razonamiento(
            f"{emoji} Posición #{senal_id} cerrada: "
            f"{'Ganancia' if es_ganancia else 'Stop Loss'} "
            f"${resultado['pnl_usdt']:+.2f} en {resultado['duracion_minutos']}min"
        )
    except Exception:
        pass


def _recuperar_posiciones_activas():
    """Recupera señales activas desde SQLite y reanuda monitoreo."""
    try:
        activas = senales_db.obtener_ejecutadas_activas()
        if activas:
            ultima = activas[0]
            senal_id = ultima['id']
            side = ultima.get('direccion', 'LONG').upper()
            precio_entrada = ultima.get('precio_entrada', 0)
            sl = ultima.get('sl')
            tp = ultima.get('tp')
            logger.info(f"Señal activa detectada en SQLite: #{senal_id} {side}")
            if precio_entrada == 0:
                precio_entrada = _get_precio_actual()
            if sl is None or tp is None:
                sl, tp = _calcular_sl_tp(precio_entrada, side)
            _monitorear_sl_tp(
                senal_id=senal_id, side=side,
                entry_price=precio_entrada, sl=sl, tp=tp,
                callback=lambda r: _on_cierre_posicion(r, senal_id, side, precio_entrada),
                poll_interval=5,
                breakeven_at_50pct=True,
            )
    except Exception as e:
        logger.warning(f"Error recuperando posiciones: {e}")


# ── Estado de trading scalper (global para callbacks) ────────────────────────

ESTADO_TRADING = {
    "posicion_activa": False,
    "ultimo_trade_time": 0.0,
    "trades_hora": 0,
    "hora_actual": 0.0,
    "perdida_diaria": 0.0,
    "pnl_diario": 0.0,
    "trades_hoy": 0,
}

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
    inicio_sesion = datetime.now(timezone.utc).isoformat()

    global ESTADO_TRADING
    ESTADO_TRADING["hora_actual"] = time.time()

    while not terminal.stop_event.is_set() and not _signal_received:
        try:
            # ── Get data from feed ─────────────────────────────────
            klines_1m = feed.get_klines("1m")
            klines_5m = feed.get_klines("5m")
            klines_1h = feed.get_klines("1h")
            trades = feed.get_trades()
            bids, asks = feed.get_book()
            precio = feed.get_last_price()

            if precio is None or len(klines_1m) < 20 or len(klines_5m) < 20 or len(klines_1h) < 30:
                time.sleep(1)
                continue

            # ── Extract OHLCV ──────────────────────────────────────
            _, highs_m5, lows_m5, closes_m5, vols_m5 = _extraer_ohlcv(klines_5m)
            _, highs_m1, lows_m1, closes_m1, _ = _extraer_ohlcv(klines_1m)
            _, highs_h1, lows_h1, closes_h1, _ = _extraer_ohlcv(klines_1h)

            # ── Bollinger Bands M1 (30/3.0) ────────────────────────
            try:
                bb_sup_m1, bb_inf_m1, bb_media_m1, bbw_m1 = calcular_bb(closes_m1, 30, 3.0)
            except Exception:
                bb_media_m1 = bb_sup_m1 = bb_inf_m1 = None
                bbw_m1 = 0.0

            # ── Bollinger Bands M5 (20/2.0) ────────────────────────
            try:
                bb_sup_m5, bb_inf_m5, bb_media_m5, bbw_m5 = calcular_bb(closes_m5, 20, 2.0)
            except Exception:
                bb_media_m5 = bb_sup_m5 = bb_inf_m5 = None
                bbw_m5 = 0.0

            # ── Bollinger Bands H1 (30/3.0) ────────────────────────
            try:
                bb_sup_h1, bb_inf_h1, bb_media_h1, bbw_h1 = calcular_bb(closes_h1, 30, 3.0)
            except Exception:
                bb_media_h1 = bb_sup_h1 = bb_inf_h1 = None
                bbw_h1 = 0.0

            # ── ADX M5 ──────────────────────────────────────────
            try:
                adx_m5 = calcular_adx(highs_m5, lows_m5, closes_m5, 14)
            except Exception:
                adx_m5 = 0.0

            # ── ADX H1 ──────────────────────────────────────────
            try:
                adx_h1 = calcular_adx(highs_h1, lows_h1, closes_h1, 14)
            except Exception:
                adx_h1 = 0.0

            # ── CVD ─────────────────────────────────────────────
            trades_list = list(trades)
            try:
                cvd_largo = calcular_cvd_real(trades_list[-1000:]) if len(trades_list) >= 1000 else calcular_cvd_real(trades_list)
            except Exception:
                cvd_largo = 0
            try:
                cvd_corto = calcular_cvd_real(trades_list[-50:]) if len(trades_list) >= 50 else calcular_cvd_real(trades_list)
            except Exception:
                cvd_corto = 0

            # ── Delta última vela M1 ───────────────────────────
            try:
                ultima_vela_m1 = klines_1m[-1] if klines_1m else None
                if ultima_vela_m1:
                    delta_ultima_m1 = calcular_delta_vela(
                        ultima_vela_m1["open"], ultima_vela_m1["high"],
                        ultima_vela_m1["low"], ultima_vela_m1["close"],
                        ultima_vela_m1["volume"],
                    )
                else:
                    delta_ultima_m1 = 0.0
            except Exception:
                delta_ultima_m1 = 0.0

            # ── Mecha rechazo M1 ──────────────────────────────
            mecha_rechazo = None
            try:
                if ultima_vela_m1:
                    from .core.indicadores import detectar_mecha
                    mecha_rechazo = detectar_mecha(
                        ultima_vela_m1["open"], ultima_vela_m1["high"],
                        ultima_vela_m1["low"], ultima_vela_m1["close"],
                    )
            except ImportError:
                try:
                    from trading.goat_btc.core.indicadores import detectar_mecha
                    if ultima_vela_m1:
                        mecha_rechazo = detectar_mecha(
                            ultima_vela_m1["open"], ultima_vela_m1["high"],
                            ultima_vela_m1["low"], ultima_vela_m1["close"],
                        )
                except Exception:
                    pass
            except Exception:
                pass

            # ── Rechazo M1 (compatibilidad) ──────────────────
            rechazo_m1 = mecha_rechazo

            # ── Volumen relativo (M5) ───────────────────────────
            try:
                vol_relativo = calcular_volumen_relativo(vols_m5)
            except Exception:
                vol_relativo = 0.0

            # ── Imbalance book ────────────────────────────────────
            try:
                imbalance = calcular_imbalance_book(bids, asks, 10)
            except Exception:
                imbalance = 0.0

            # ── RSI 7 M1 ─────────────────────────────────────
            try:
                from .core.indicadores import calcular_rsi
                rsi_7 = calcular_rsi(closes_m1, periodo=7)
            except ImportError:
                from trading.goat_btc.core.indicadores import calcular_rsi
                rsi_7 = calcular_rsi(closes_m1, periodo=7)
            except Exception:
                rsi_7 = 50

            # ── Pendiente de bandas M1 ───────────────────────
            try:
                from .core.indicadores import detectar_pendiente_bandas
                # Usar bb_media_m1 histórico si disponible
                sma_values = []
                if bb_media_m1:
                    sma_values = list(closes_m1[-60:])  # approximar con closes
                pendiente_bandas = detectar_pendiente_bandas(sma_values)
            except Exception:
                pendiente_bandas = "flat"
                sma_values = []

            # ── Retorno a media M1 ──────────────────────────
            try:
                from .core.indicadores import detectar_retorno_media
                retorno_media = detectar_retorno_media(precio, bb_media_m1)
            except Exception:
                retorno_media = False

            # ── Velas tocando banda M1 (últimas 3) ───────────────
            try:
                _, toco_sup_m1, toco_inf_m1 = _precios_tocaron_banda(
                    klines_1m, bb_sup_m1, bb_inf_m1, 3
                )
            except Exception:
                toco_sup_m1 = False
                toco_inf_m1 = False

            # ── Últimas deltas de velas M1 ─────────────────────
            try:
                deltas_velas_m1 = _calcular_deltas_velas(klines_1m, 5)
            except Exception:
                deltas_velas_m1 = []

            # ── Build indicadores dict for M1 scalper ───────────
            indicadores_dict = {
                "precio_actual": precio,
                "bb_superior_m1": bb_sup_m1,
                "bb_inferior_m1": bb_inf_m1,
                "bb_media_m1": bb_media_m1,
                "toco_bb_superior_m1": toco_sup_m1,
                "toco_bb_inferior_m1": toco_inf_m1,
                "bbw_m1": bbw_m1,
                "bbw_m5": bbw_m5,
                "adx_m5": adx_m5,
                "adx_h1": adx_h1,
                "cvd_corto": cvd_corto,
                "cvd_largo_H1": cvd_largo,
                "delta_ultima_vela": delta_ultima_m1,
                "ultimas_5_deltas": deltas_velas_m1,
                "imbalance_book": imbalance,
                "rechazo_m1": rechazo_m1,
                "mecha_rechazo_m1": mecha_rechazo,
                "rsi_7": rsi_7,
                "pendiente_bandas_m1": pendiente_bandas,
                "retorno_media_m1": retorno_media,
                "sma_m1_values": sma_values,
            }

            # ── Score M1 scalper ──────────────────────────────────
            try:
                resultado_score = calcular_score_scalper(indicadores_dict)
            except Exception:
                resultado_score = {"score": 0, "direccion": None, "confluencias": [], "es_alerta": False, "es_premium": False}

            score = resultado_score.get("score", 0)
            direccion = resultado_score.get("direccion")

            # ── Verificar bloqueos ────────────────────────────────
            try:
                resultado_bloqueos = verificar_bloqueos(indicadores_dict, ESTADO_TRADING)
                if resultado_bloqueos.get("bloqueado"):
                    logger.info(f"BLOQUEOS: {resultado_bloqueos['bloqueos']}")
            except Exception:
                resultado_bloqueos = {"bloqueado": True, "bloqueos": ["error"], "puede_entrar": False}

            # ── Build terminal data ───────────────────────────────
            regimen_m5 = clasificar_bbw(bbw_m5)
            regimen_h1 = clasificar_bbw(bbw_h1)

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
                "bb_sup": bb_sup_m5,
                "bb_media": bb_media_m5,
                "bb_inf": bb_inf_m5,
                "adx": adx_m5,
                "bbw": bbw_m5,
                "cvd_medio": cvd_corto,
                "clasificacion": regimen_m5,
                "senal_bloqueada": resultado_bloqueos.get("bloqueado", False),
            }

            velas_m1 = []
            for k in list(klines_1m)[-5:]:
                d = calcular_delta_vela(
                    k["open"], k["high"], k["low"], k["close"], k["volume"]
                )
                velas_m1.append({
                    "time": datetime.fromtimestamp(k["time"] / 1000, tz=timezone.utc).strftime("%H:%M"),
                    "delta": d,
                })

            flujo_data = {
                "ultimas_5_velas": velas_m1,
                "cvd_corto": cvd_corto,
                "imbalance": imbalance,
                "vol_relativo": vol_relativo,
                "bbw_m1": bbw_m1,
            }

            # ── Reasoning lines ────────────────────────────────────
            raz_lines = []
            if bb_media_m1:
                raz_lines.append(f"SCALPER M1 — BB 30/3.0 Sup: ${bb_sup_m1:,.0f} Med: ${bb_media_m1:,.0f} Inf: ${bb_inf_m1:,.0f}")
            modo_entrada = resultado_score.get("modo", "")
            if modo_entrada:
                raz_lines.append(f"Modo: {modo_entrada.upper()} | RSI(7): {rsi_7:.1f}")
            raz_lines.append(f"BBW M1: {bbw_m1:.4f} | BBW M5: {bbw_m5:.4f} | ADX M5: {adx_m5:.1f}")
            raz_lines.append(f"CVD corto: {cvd_corto:+,d} | CVD largo: {cvd_largo:+,d}")
            if mecha_rechazo:
                raz_lines.append(f"Mecha rechazo: {mecha_rechazo}")
            if resultado_score.get("es_alerta"):
                raz_lines.append(f"Senal M1: {resultado_score.get('direccion', 'N/A')} | Score: {resultado_score['score']}/100")
                if resultado_bloqueos.get("bloqueado"):
                    raz_lines.append(f"BLOQUEADO: {', '.join(resultado_bloqueos['bloqueos'])}")
            else:
                if score > 0:
                    raz_lines.append(f"Score parcial M1: {score} — esperando confluencias")
                raz_lines.append("Monitoreando M1...")
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

                cooldown_restante = max(0, SCALPER_CONFIG['cooldown_entre_trades'] - (time.time() - ESTADO_TRADING["ultimo_trade_time"]))

                header_data = {
                    "precio": precio,
                    "cambio_24h": 0.0,
                    "regimen": regimen_m5,
                }
                status_data = {
                    "precio": precio,
                    "cvd_largo": cvd_largo,
                    "adx": adx_m5,
                    "regimen": regimen_m5.upper(),
                    "senales_hoy": senales_hoy,
                    "trades_hoy": ESTADO_TRADING["trades_hoy"],
                    "pnl_diario": ESTADO_TRADING["pnl_diario"],
                    "cooldown": int(cooldown_restante),
                    "bbw_m1": bbw_m1,
                    "rsi_7": rsi_7,
                    "modo_entrada": resultado_score.get("modo", ""),
                    "score": score,
                }
                terminal.actualizar(macro_data, regimen_data, flujo_data, status_data=status_data, header_data=header_data)
            except Exception:
                pass

            # ── Signal detection (M1 scalper) ─────────────────────

            if score >= SCORE_MINIMO_ENTRADA and direccion:
                if not resultado_bloqueos.get("bloqueado", True):
                    ahora = time.time()
                    direccion_up = direccion.upper()
                    logger.info(f"\u26a1 SEÑAL SCALPER: {direccion_up} | Score: {score}/100 | Precio: ${precio:,.0f}")

                    senal_info = {
                        "tipo": direccion_up,
                        "score": score,
                        "precio": precio,
                        "bb_inf": bb_inf_m1,
                        "confluencias": resultado_score.get("confluencias", []),
                        "clasificacion": "scalper_m1",
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
                                "clasificacion": "scalper_m1",
                                "confluencias": resultado_score.get("confluencias", []),
                            }
                            event_bus.publicar("señal_trading", "G.O.A.T", payload=event_data)
                        except Exception as e:
                            logger.warning(f"Error publicando evento: {e}")

                    # Save to SQLite con SL/TP calculados
                    try:
                        _sl, _tp = _calcular_sl_tp(precio, direccion)
                    except Exception:
                        _sl = round(precio * 0.997, 1) if direccion.upper() == 'LONG' else round(precio * 1.003, 1)
                        _tp = round(precio * 1.007, 1) if direccion.upper() == 'LONG' else round(precio * 0.993, 1)
                    senal_data = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "direccion": direccion,
                        "score": score,
                        "precio_entrada": precio,
                        "bb_superior": bb_sup_m1,
                        "bb_media": bb_media_m1,
                        "bb_inferior": bb_inf_m1,
                        "cvd_corto": cvd_corto,
                        "cvd_largo": cvd_largo,
                        "adx": adx_m5,
                        "bbw": bbw_m1,
                        "clasificacion": "scalper_m1",
                        "confluencias": resultado_score.get("confluencias", []),
                        "sl": _sl,
                        "tp": _tp,
                    }
                    senal_id = None
                    try:
                        senal_id = senales_db.guardar_senal_con_sl_tp(senal_data)
                    except Exception as e:
                        logger.warning(f"Error guardando señal: {e}")

                    # ── Autonomous execution (SOLO si OKX confirma) ──
                    orden_exitosa = _ejecutar_senal_automatica(
                        senal_id=senal_id,
                        direccion=direccion_up,
                        score=score,
                        precio=precio,
                        clasificacion="scalper_m1",
                        confluencias=resultado_score.get("confluencias", []),
                    )

                    # SOLO actualizar contadores si la orden realmente se ejecutó
                    if orden_exitosa:
                        ESTADO_TRADING["ultimo_trade_time"] = ahora
                        ESTADO_TRADING["trades_hoy"] += 1
                        ESTADO_TRADING["trades_hora"] += 1
                        logger.info(f"✅ Trade #{senal_id} ejecutado (hora={ESTADO_TRADING['trades_hora']}, hoy={ESTADO_TRADING['trades_hoy']})")
                    else:
                        logger.warning(f"❌ Trade #{senal_id} NO se ejecutó en OKX — contadores NO actualizados")
                else:
                    if resultado_bloqueos.get("bloqueos"):
                        logger.info(f"Señal bloqueada: {', '.join(resultado_bloqueos['bloqueos'])}")

            # ── Reset conteo por hora ──────────────────────────────
            if time.time() - ESTADO_TRADING["hora_actual"] >= 3600:
                ESTADO_TRADING["trades_hora"] = 0
                ESTADO_TRADING["hora_actual"] = time.time()

        except Exception as e:
            logger.warning(f"Error en ciclo principal: {e}", exc_info=True)

        time.sleep(1)

    logger.info("Ciclo principal finalizado")


# ── Main orchestrator ───────────────────────────────────────────────────────

def ejecutar():
    feed.iniciar()
    logger.info("Feed Binance iniciado, esperando datos iniciales...")
    time.sleep(3)

    # Recuperar posiciones activas (si el proceso se reinició)
    _recuperar_posiciones_activas()

    logger.info("Iniciando terminal visual...")
    processing_thread = threading.Thread(target=_main_processing, daemon=True)
    processing_thread.start()

    logger.info("G.O.A.T PROTOCOL operativo — Terminal Live en pantalla principal")
    terminal.iniciar()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("G.O.A.T PROTOCOL BTC/USD v2.0 — SCALPER M1")
        logger.info("=" * 60)
        ejecutar()
    except KeyboardInterrupt:
        logger.info("G.O.A.T detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
    finally:
        feed.detener()
        logger.info("G.O.A.T PROTOCOL finalizado")

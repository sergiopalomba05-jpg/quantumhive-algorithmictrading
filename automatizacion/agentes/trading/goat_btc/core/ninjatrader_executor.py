"""
ninjatrader_executor.py — Ejecutor de órdenes via NinjaTrader 8 ATI (OIF files)
Reemplaza binance_executor.py para operar MBTM26 en Tradovate demo via NT8.
"""

import os
import time
import logging
import threading
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('ninjatrader_executor')

# ── Config ────────────────────────────────────────────────────────────────────

NT_SIMULATION = os.getenv('NT_SIMULATION', 'true').lower() == 'true'
NT_ACCOUNT = os.getenv('NT_ACCOUNT', 'Sim101')
NT_INSTRUMENT = os.getenv('NT_INSTRUMENT', 'MBTM26')
NT_INCOMING_DIR = os.getenv('NT_INCOMING_DIR', '')

AMOUNT_CONTRACTS = 1  # 1 contrato MBT por operacion

SYMBOL = NT_INSTRUMENT


def _get_incoming_dir() -> Path:
    if NT_INCOMING_DIR:
        return Path(NT_INCOMING_DIR)
    docs = Path.home() / 'Documents' / 'NinjaTrader 8' / 'incoming'
    if docs.exists():
        return docs
    return docs


def _write_oif(content: str) -> bool:
    incoming = _get_incoming_dir()
    try:
        incoming.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"No se pudo crear directorio {incoming}: {e}")
        return False
    filename = f"goat_{int(time.time() * 1000)}_{os.urandom(4).hex()}.txt"
    filepath = incoming / filename
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        logger.info(f"OIF escrito: {filepath} -> {content}")
        return True
    except Exception as e:
        logger.error(f"Error escribiendo OIF: {e}")
        return False


# ── Funciones publicas (misma interfaz que binance_executor) ──────────────────

def set_leverage(symbol: str = None, leverage: int = 1):
    pass


def get_precio_actual(symbol: str = None) -> float:
    try:
        resp = requests.get(
            'https://api.binance.com/api/v3/ticker/price',
            params={'symbol': 'BTCUSDT'}, timeout=5
        )
        if resp.status_code == 200:
            return float(resp.json()['price'])
    except Exception as e:
        logger.warning(f"Error obteniendo precio Binance: {e}")
    return 0.0


def ejecutar_orden(side: str, precio: float = None, symbol: str = None):
    instr = symbol or SYMBOL
    side_up = side.upper()
    if side_up not in ('BUY', 'SELL', 'LONG', 'SHORT'):
        logger.error(f"Side invalido: {side}")
        return None

    action = 'BUY' if side_up in ('BUY', 'LONG') else 'SELL'

    if NT_SIMULATION:
        logger.info(f"[SIMULACION OIF] {action} {AMOUNT_CONTRACTS} {instr}")
        return {"orderId": f"sim_{int(time.time())}", "status": "SIMULATED",
                "side": side, "symbol": instr}

    oif = f"PLACE;{NT_ACCOUNT};{instr};{action};{AMOUNT_CONTRACTS};MARKET;0;0;DAY;;;;"
    ok = _write_oif(oif)
    if ok:
        return {"orderId": f"oif_{int(time.time())}", "status": "OIF_SUBMITTED",
                "side": side, "symbol": instr}
    logger.error(f"Fallo escribiendo OIF para {action} {instr}")
    return None


def cerrar_posicion(symbol: str = None):
    instr = symbol or SYMBOL

    if NT_SIMULATION:
        logger.info(f"[SIMULACION OIF] Close {instr}")
        return {"orderId": f"sim_close_{int(time.time())}", "status": "SIMULATED"}

    oif = f"CLOSEPOSITION;{NT_ACCOUNT};{instr}"
    ok = _write_oif(oif)
    if ok:
        return {"orderId": f"oif_close_{int(time.time())}", "status": "OIF_SUBMITTED"}
    return None


def get_posicion_activa(symbol: str = None) -> dict:
    return {}


def get_balance() -> float:
    return 0.0


# ── SL/TP Monitoring (identico a binance_executor) ───────────────────────────

def calcular_sl_tp(entry_price: float, side: str) -> tuple:
    if side.upper() == 'LONG':
        sl = round(entry_price * 0.997, 1)
        tp = round(entry_price * 1.007, 1)
    else:
        sl = round(entry_price * 1.003, 1)
        tp = round(entry_price * 0.993, 1)
    return sl, tp


def calcular_pnl(entry_price: float, exit_price: float, side: str, qty: float = None) -> dict:
    if qty is None:
        qty = AMOUNT_CONTRACTS
    if side.upper() == 'LONG':
        pnl_usdt = round((exit_price - entry_price) * qty, 2)
        pnl_pct = round((exit_price - entry_price) / entry_price * 100, 2)
    else:
        pnl_usdt = round((entry_price - exit_price) * qty, 2)
        pnl_pct = round((entry_price - entry_price) / entry_price * 100, 2)
    return {"pnl_usdt": pnl_usdt, "pnl_pct": pnl_pct, "exit_price": exit_price}


def monitorear_sl_tp(senal_id: int, side: str, entry_price: float, sl: float, tp: float,
                     callback=None, poll_interval: int = 5, breakeven_at_50pct: bool = True):
    def _loop():
        logger.info(f"[{senal_id}] Monitoreando SL={sl} TP={tp} cada {poll_interval}s (breakeven={breakeven_at_50pct})")
        inicio = time.time()
        sl_actual = sl
        breakeven_activado = False
        while True:
            time.sleep(poll_interval)
            precio = get_precio_actual()
            if precio == 0:
                logger.warning(f"[{senal_id}] No se pudo obtener precio, reintentando...")
                continue

            if breakeven_at_50pct and not breakeven_activado:
                if side.upper() == 'LONG':
                    distancia_total = tp - entry_price
                    avance = precio - entry_price
                    if distancia_total > 0 and avance >= distancia_total * 0.5:
                        sl_actual = entry_price
                        breakeven_activado = True
                        logger.info(f"[{senal_id}] Breakeven activado — SL movido a ${entry_price:,.1f}")
                else:
                    distancia_total = entry_price - tp
                    avance = entry_price - precio
                    if distancia_total > 0 and avance >= distancia_total * 0.5:
                        sl_actual = entry_price
                        breakeven_activado = True
                        logger.info(f"[{senal_id}] Breakeven activado — SL movido a ${entry_price:,.1f}")

            tocado_sl = (side.upper() == 'LONG' and precio <= sl_actual) or (side.upper() == 'SHORT' and precio >= sl_actual)
            tocado_tp = (side.upper() == 'LONG' and precio >= tp) or (side.upper() == 'SHORT' and precio <= tp)

            if tocado_sl or tocado_tp:
                tipo_salida = "Stop Loss" if tocado_sl else "Take Profit"
                logger.info(f"[{senal_id}] {tipo_salida} tocado en ${precio:,.1f}")

                cierre = cerrar_posicion()
                if cierre is None and NT_SIMULATION:
                    cierre = {"orderId": f"sim_close_{int(time.time())}", "status": "SIMULATED"}

                duracion = int((time.time() - inicio) / 60)
                pnl = calcular_pnl(entry_price, precio, side, AMOUNT_CONTRACTS)

                resultado = {
                    "senal_id": senal_id,
                    "tipo_salida": tipo_salida,
                    "precio_cierre": precio,
                    "pnl_usdt": pnl["pnl_usdt"],
                    "pnl_pct": pnl["pnl_pct"],
                    "duracion_minutos": duracion,
                    "order_id": cierre.get("orderId", "unknown") if cierre else "unknown",
                }
                logger.info(f"[{senal_id}] Cerrada: {resultado}")
                if callback:
                    try:
                        callback(resultado)
                    except Exception as e:
                        logger.error(f"[{senal_id}] Error en callback: {e}")
                return

    thread = threading.Thread(target=_loop, daemon=True, name=f"monitor_{senal_id}")
    thread.start()
    logger.info(f"[{senal_id}] Thread de monitoreo iniciado (scalper: {poll_interval}s)")
    return thread

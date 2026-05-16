"""
goat_btc — BinanceExecutor
Ejecución de órdenes en Binance Testnet (Futuros).
Modo simulación hasta validación de tasa de acierto.
"""

import os
import hashlib
import hmac
import json
import time
import logging
import threading
import requests
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('binance_executor')

BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
BASE_URL = os.getenv('BINANCE_TESTNET_BASE_URL', 'https://testnet.binancefuture.com')
API_KEY = os.getenv('BINANCE_TESTNET_API_KEY', '')
SECRET_KEY = os.getenv('BINANCE_TESTNET_SECRET', '')

SYMBOL = 'BTCUSDT'
LEVERAGE = 1
AMOUNT_USDT = 10.0  # $10 por operación en simulación


def _firmar(query_string: str) -> str:
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def _request(method: str, endpoint: str, params: dict = None, signed: bool = False):
    url = f"{BASE_URL}{endpoint}"
    headers = {'X-MBX-APIKEY': API_KEY}
    if params is None:
        params = {}
    if signed:
        params['timestamp'] = int(time.time() * 1000)
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        params['signature'] = _firmar(query_string)
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        logger.error(f"Error {method} {endpoint}: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        logger.error(f"Excepción {method} {endpoint}: {e}")
        return None


def set_leverage(symbol: str = SYMBOL, leverage: int = LEVERAGE):
    return _request('POST', '/fapi/v1/leverage', {'symbol': symbol, 'leverage': leverage}, signed=True)


def get_precio_actual(symbol: str = SYMBOL) -> float:
    data = _request('GET', '/fapi/v1/ticker/price', {'symbol': symbol})
    if data:
        return float(data['price'])
    return 0.0


def get_info_symbol(symbol: str = SYMBOL) -> dict:
    data = _request('GET', '/fapi/v1/exchangeInfo')
    if data:
        for s in data.get('symbols', []):
            if s['symbol'] == symbol:
                return s
    return {}


def _calcular_cantidad(side: str, precio: float, symbol: str = SYMBOL) -> float:
    qty = AMOUNT_USDT / precio
    info = get_info_symbol(symbol)
    step_size = 0.001
    for f in info.get('filters', []):
        if f['filterType'] == 'LOT_SIZE':
            step_size = float(f['stepSize'])
            break
    precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
    qty = float(Decimal(str(qty)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))
    return round(qty, precision)


def ejecutar_orden(side: str, precio: float = None, symbol: str = SYMBOL):
    if BINANCE_TESTNET:
        logger.info(f"[SIMULACIÓN] {side} {symbol} @ {precio}")
        return {"orderId": f"sim_{int(time.time())}", "status": "SIMULATED", "side": side, "symbol": symbol}

    qty = _calcular_cantidad(side, precio or get_precio_actual(symbol))
    params = {
        'symbol': symbol,
        'side': side.upper(),
        'type': 'MARKET',
        'quantity': qty,
        'reduceOnly': 'false',
    }
    if side.upper() == 'SELL':
        params['positionSide'] = 'SHORT'

    result = _request('POST', '/fapi/v1/order', params, signed=True)
    if result:
        logger.info(f"Orden ejecutada: {side} {qty} {symbol} @ mercado")
    else:
        logger.error(f"Fallo ejecutando orden {side}")
    return result


def cerrar_posicion(symbol: str = SYMBOL):
    if BINANCE_TESTNET:
        logger.info(f"[SIMULACIÓN] Cierre de {symbol}")
        return {"orderId": f"sim_close_{int(time.time())}", "status": "SIMULATED"}

    pos = get_posicion_activa(symbol)
    if not pos:
        logger.info(f"No hay posición activa en {symbol}")
        return None

    qty = abs(float(pos['positionAmt']))
    side = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'

    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': qty,
        'reduceOnly': 'true',
    }
    result = _request('POST', '/fapi/v1/order', params, signed=True)
    if result:
        logger.info(f"Posición cerrada: {side} {qty} {symbol}")
    return result


def get_posicion_activa(symbol: str = SYMBOL) -> dict:
    data = _request('GET', '/fapi/v2/positionRisk', {'symbol': symbol}, signed=True)
    if data and len(data) > 0:
        pos = data[0]
        if float(pos.get('positionAmt', 0)) != 0:
            return pos
    return {}


def get_balance() -> float:
    data = _request('GET', '/fapi/v2/account', {}, signed=True)
    if data:
        for asset in data.get('assets', []):
            if asset['asset'] == 'USDT':
                return float(asset['walletBalance'])
    return 0.0


# ── SL/TP Monitoring ────────────────────────────────────────────────────────

def calcular_sl_tp(entry_price: float, side: str) -> tuple:
    """Calcula SL y TP basado en porcentaje. LONG: SL -0.3%, TP +0.7%."""
    if side.upper() == 'LONG':
        sl = round(entry_price * 0.997, 1)
        tp = round(entry_price * 1.007, 1)
    else:
        sl = round(entry_price * 1.003, 1)
        tp = round(entry_price * 0.993, 1)
    return sl, tp


def calcular_pnl(entry_price: float, exit_price: float, side: str, qty: float = None) -> dict:
    """Calcula P&L en USD y porcentaje."""
    if qty is None:
        qty = AMOUNT_USDT / entry_price
    if side.upper() == 'LONG':
        pnl_usdt = round((exit_price - entry_price) * qty, 2)
        pnl_pct = round((exit_price - entry_price) / entry_price * 100, 2)
    else:
        pnl_usdt = round((entry_price - exit_price) * qty, 2)
        pnl_pct = round((entry_price - exit_price) / entry_price * 100, 2)
    return {"pnl_usdt": pnl_usdt, "pnl_pct": pnl_pct, "exit_price": exit_price}


def monitorear_sl_tp(senal_id: int, side: str, entry_price: float, sl: float, tp: float,
                     callback=None, poll_interval: int = 30):
    """
    Monitorea precio cada `poll_interval` segundos.
    Si toca SL o TP → cierra posición y llama callback con resultado.
    Corre en su propio thread.
    """
    def _loop():
        logger.info(f"[{senal_id}] Monitoreando SL={sl} TP={tp} cada {poll_interval}s")
        inicio = time.time()
        while True:
            time.sleep(poll_interval)
            precio = get_precio_actual()
            if precio == 0:
                logger.warning(f"[{senal_id}] No se pudo obtener precio, reintentando...")
                continue

            tocado_sl = (side.upper() == 'LONG' and precio <= sl) or (side.upper() == 'SHORT' and precio >= sl)
            tocado_tp = (side.upper() == 'LONG' and precio >= tp) or (side.upper() == 'SHORT' and precio <= tp)

            if tocado_sl or tocado_tp:
                tipo_salida = "Stop Loss" if tocado_sl else "Take Profit"
                logger.info(f"[{senal_id}] {tipo_salida} tocado en ${precio:,.1f}")

                # Cerrar posición
                cierre = cerrar_posicion()
                if cierre is None and BINANCE_TESTNET:
                    cierre = {"orderId": f"sim_close_{int(time.time())}", "status": "SIMULATED"}

                duracion = int((time.time() - inicio) / 60)
                qty = AMOUNT_USDT / entry_price
                pnl = calcular_pnl(entry_price, precio, side, qty)

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
    logger.info(f"[{senal_id}] Thread de monitoreo iniciado")
    return thread

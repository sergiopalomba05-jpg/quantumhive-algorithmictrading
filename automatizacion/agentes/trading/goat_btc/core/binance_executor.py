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

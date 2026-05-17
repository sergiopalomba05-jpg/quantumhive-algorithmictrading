"""
OKX Executor — Ejecución autónoma en BTC-USDT-SWAP perpetuo
Demo mode: x-simulated-trading: 1
Autenticación HMAC-SHA256
"""

import os
import hmac
import hashlib
import base64
import time
import logging
import requests
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('okx_executor')

# ── Config ────────────────────────────────────────────────────────────────────

OKX_API_KEY = os.getenv('OKX_API_KEY', '')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', '')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE', '')
OKX_FLAG = os.getenv('OKX_FLAG', '1')
OKX_BASE_URL = os.getenv('OKX_BASE_URL', 'https://www.okx.com')
OKX_INSTRUMENT = os.getenv('OKX_INSTRUMENT', 'BTC-USDT-SWAP')

AMOUNT_CONTRACTS = 1

SYMBOL = OKX_INSTRUMENT


class OKXExecutor:
    """Ejecutor de órdenes via OKX Demo API."""

    def __init__(self):
        self.api_key = OKX_API_KEY
        self.secret_key = OKX_SECRET_KEY
        self.passphrase = OKX_PASSPHRASE
        self.flag = OKX_FLAG
        self.base_url = OKX_BASE_URL
        self.instrument = OKX_INSTRUMENT
        self._last_price = 0.0

    def _get_timestamp(self) -> str:
        """Timestamp ISO 8601 UTC requerido por OKX."""
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _sign(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        """Genera firma HMAC-SHA256."""
        message = f'{timestamp}{method}{path}{body}'
        mac = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()

    def _get_headers(self, method: str, path: str, body: str = '') -> dict:
        """Genera headers de autenticación OKX."""
        timestamp = self._get_timestamp()
        sign = self._sign(timestamp, method, path, body)
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'x-simulated-trading': self.flag,
            'Content-Type': 'application/json',
        }

    def _request(self, method: str, path: str, body: dict = None) -> Optional[dict]:
        """Ejecuta request autenticado contra OKX API."""
        import json
        body_str = json.dumps(body) if body else ''
        headers = self._get_headers(method, path, body_str)
        url = f'{self.base_url}{path}'
        try:
            if method == 'GET':
                resp = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                resp = requests.post(url, headers=headers, data=body_str, timeout=10)
            else:
                logger.error(f"Método no soportado: {method}")
                return None

            data = resp.json()
            if data.get('code') != '0':
                logger.error(f"OKX error {data.get('code')}: {data.get('msg', 'unknown')}")
                return None
            return data
        except requests.exceptions.Timeout:
            logger.error("OKX request timeout")
            return None
        except Exception as e:
            logger.error(f"OKX request error: {e}")
            return None

    def ejecutar_orden(self, side: str, precio: float = None) -> dict:
        """
        Ejecuta market order en BTC-USDT-SWAP.
        side: 'buy' o 'sell' (o 'long'/'short')
        Retorna: {'orderId': str, 'precio': float, 'status': str}
        """
        side_up = side.upper()
        if side_up in ('BUY', 'LONG'):
            td_mode = 'buy'
        elif side_up in ('SELL', 'SHORT'):
            td_mode = 'sell'
        else:
            logger.error(f"Side inválido: {side}")
            return None

        body = {
            'instId': self.instrument,
            'tdMode': 'cross',
            'side': td_mode,
            'ordType': 'market',
            'sz': str(AMOUNT_CONTRACTS),
        }

        result = self._request('POST', '/api/v5/trade/order', body)
        if result and result.get('data'):
            order_data = result['data'][0]
            order_id = order_data.get('ordId', '')
            logger.info(f"Orden ejecutada: {td_mode} {AMOUNT_CONTRACTS} {self.instrument} -> {order_id}")
            return {
                'orderId': order_id,
                'precio': precio or 0.0,
                'status': order_data.get('sState', 'submitted'),
                'side': side,
                'symbol': self.instrument,
            }
        logger.error(f"Fallo ejecutando orden: {side}")
        return None

    def cerrar_posicion(self, symbol: str = None) -> dict:
        """
        Cierra posición activa con close-position endpoint.
        Retorna: {'status': str, 'pnl': float}
        """
        inst = symbol or self.instrument
        body = {
            'instId': inst,
            'mgnMode': 'cross',
        }

        result = self._request('POST', '/api/v5/trade/close-position', body)
        if result and result.get('data'):
            close_data = result['data'][0]
            logger.info(f"Posición cerrada: {inst} -> {close_data.get('ordId', '')}")
            return {
                'orderId': close_data.get('ordId', ''),
                'status': close_data.get('sState', 'submitted'),
            }
        logger.error(f"Fallo cerrando posición: {inst}")
        return None

    def get_posicion_activa(self, symbol: str = None) -> Optional[dict]:
        """
        Consulta posición abierta actual.
        Retorna: {'side': str, 'precio_entrada': float,
                  'pnl_no_realizado': float, 'size': float} o None
        """
        inst = symbol or self.instrument
        params = f'?instId={inst}'
        result = self._request('GET', f'/api/v5/account/positions{params}')
        if result and result.get('data'):
            positions = result['data']
            for pos in positions:
                if pos.get('instId') == inst and pos.get('pos') != '0':
                    pos_side = pos.get('posSide', 'net')
                    avg_px = float(pos.get('avgPx', 0))
                    upnl = float(pos.get('upl', 0))
                    size = float(pos.get('pos', 0))
                    return {
                        'side': pos_side,
                        'precio_entrada': avg_px,
                        'pnl_no_realizado': upnl,
                        'size': size,
                    }
        return None

    def get_balance(self) -> float:
        """
        Retorna balance USDT disponible en cuenta demo.
        """
        result = self._request('GET', '/api/v5/account/balance')
        if result and result.get('data'):
            details = result['data'][0].get('details', [])
            for d in details:
                if d.get('ccy') == 'USDT':
                    val = d.get('availEq', '0')
                    return float(val) if val else 0.0
        return 0.0

    def get_precio_actual(self, symbol: str = None) -> float:
        """
        Obtiene precio actual de BTC-USDT-SWAP desde ticker público.
        """
        inst = symbol or self.instrument
        try:
            resp = requests.get(
                f'{self.base_url}/api/v5/market/ticker',
                params={'instId': inst},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == '0' and data.get('data'):
                    price = float(data['data'][0].get('last', 0))
                    self._last_price = price
                    return price
        except Exception as e:
            logger.warning(f"Error obteniendo precio OKX: {e}")
        return self._last_price

    def test_conexion(self) -> bool:
        """
        Verifica que las credenciales son válidas.
        Loggea balance disponible si exitoso.
        """
        try:
            balance = self.get_balance()
            if balance >= 0:
                logger.info(f"OKX Demo conectado — Balance USDT: ${balance:,.2f}")
                return True
            return False
        except Exception as e:
            logger.error(f"Test de conexión OKX fallido: {e}")
            return False


# ── Instancia global (misma interfaz que ninjatrader_executor) ────────────────

_executor = OKXExecutor()


def set_leverage(symbol: str = None, leverage: int = 1):
    """OKX usa cross margin por defecto, leverage se maneja en la cuenta."""
    pass


def get_precio_actual(symbol: str = None) -> float:
    return _executor.get_precio_actual(symbol)


def ejecutar_orden(side: str, precio: float = None, symbol: str = None) -> Optional[dict]:
    return _executor.ejecutar_orden(side, precio)


def cerrar_posicion(symbol: str = None) -> Optional[dict]:
    return _executor.cerrar_posicion(symbol)


def get_posicion_activa(symbol: str = None) -> Optional[dict]:
    return _executor.get_posicion_activa(symbol)


def get_balance() -> float:
    return _executor.get_balance()


def calcular_sl_tp(entry_price: float, side: str) -> tuple:
    """Calcula SL/TP basado en porcentaje (scalper M1)."""
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
        pnl_pct = round((entry_price - exit_price) / entry_price * 100, 2)
    return {"pnl_usdt": pnl_usdt, "pnl_pct": pnl_pct, "exit_price": exit_price}


def monitorear_sl_tp(senal_id: int, side: str, entry_price: float, sl: float, tp: float,
                     callback=None, poll_interval: int = 5, breakeven_at_50pct: bool = True):
    import threading

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
                if cierre is None:
                    cierre = {"orderId": f"okx_close_{int(time.time())}", "status": "CLOSED"}

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

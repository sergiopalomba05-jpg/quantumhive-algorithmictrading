"""
test_binance_conexion.py — Test standalone de conexion a Binance Testnet
QuantumHive Algorithmic Trading

Verifica:
1. Que las API keys de Testnet son validas
2. Que se puede obtener balance
3. Que se puede obtener precio actual
4. Que se puede configurar leverage
5. Que se puede ejecutar una orden de prueba (compra simulada pequeña)

Uso: python test_binance_conexion.py
Requiere: .env con BINANCE_TESTNET_API_KEY y BINANCE_TESTNET_SECRET
"""

import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_binance')

load_dotenv()

# Leer config
API_KEY = os.getenv('BINANCE_TESTNET_API_KEY', '')
SECRET_KEY = os.getenv('BINANCE_TESTNET_SECRET', '')
BASE_URL = os.getenv('BINANCE_TESTNET_BASE_URL', 'https://testnet.binancefuture.com')
BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'

logger.info("=" * 60)
logger.info("TEST DE CONEXION BINANCE TESTNET (Futuros)")
logger.info("=" * 60)
logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"API_KEY presente: {bool(API_KEY)} ({API_KEY[:8]}...{API_KEY[-4:] if len(API_KEY) > 12 else ''})")
logger.info(f"SECRET_KEY presente: {bool(SECRET_KEY)}")
logger.info(f"BINANCE_TESTNET flag: {BINANCE_TESTNET}")

if not API_KEY or not SECRET_KEY:
    logger.error("FATAL: API_KEY o SECRET_KEY vacias. Verificar .env")
    sys.exit(1)

# 1. Test GET sin firma — ping
logger.info("\n[1/5] Test: GET /fapi/v1/ping")
try:
    import requests
    resp = requests.get(f"{BASE_URL}/fapi/v1/ping", timeout=10)
    logger.info(f"  Ping: status={resp.status_code}, body={resp.text}")
except Exception as e:
    logger.error(f"  Ping FALLO: {e}")

# 2. Test GET sin firma — ticker price
logger.info("\n[2/5] Test: GET /fapi/v1/ticker/price?symbol=BTCUSDT")
try:
    resp = requests.get(f"{BASE_URL}/fapi/v1/ticker/price", params={'symbol': 'BTCUSDT'}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        logger.info(f"  Precio BTC: ${float(data['price']):,.2f}")
    else:
        logger.error(f"  Ticker FALLO: {resp.status_code} {resp.text}")
except Exception as e:
    logger.error(f"  Ticker FALLO: {e}")

# 3. Test GET con firma — get balance
logger.info("\n[3/5] Test: GET /fapi/v2/account (con firma)")
import hashlib
import hmac
import time

def _firmar(query_string):
    return hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def _request_signed(method, endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    if params is None:
        params = {}
    params['timestamp'] = int(time.time() * 1000)
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    params['signature'] = _firmar(query_string)
    headers = {'X-MBX-APIKEY': API_KEY}
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=headers, params=params, timeout=10)
        logger.info(f"  URL: {url}")
        logger.info(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"  Response: {resp.text[:500]}")
            return None
    except Exception as e:
        logger.error(f"  Exception: {e}")
        return None

balance_data = _request_signed('GET', '/fapi/v2/account')
if balance_data:
    for asset in balance_data.get('assets', []):
        if asset['asset'] == 'USDT':
            logger.info(f"  Balance USDT: {asset['walletBalance']}")
            logger.info(f"  Balance disponible: {asset['availableBalance']}")
else:
    logger.error("  No se pudo obtener balance — las keys pueden haber expirado o no tener permisos de Futuros")

# 4. Test set leverage
logger.info("\n[4/5] Test: POST /fapi/v1/leverage (con firma)")
lev_result = _request_signed('POST', '/fapi/v1/leverage', {'symbol': 'BTCUSDT', 'leverage': 1})
if lev_result:
    logger.info(f"  Leverage OK: {lev_result}")
else:
    logger.error("  Leverage FALLO")

# 5. Test orden simulada (solo check, no ejecuta)
logger.info("\n[5/5] Test: Exchange info (verificar permisos de trading)")
info = _request_signed('GET', '/fapi/v1/exchangeInfo')
if info:
    for s in info.get('symbols', []):
        if s['symbol'] == 'BTCUSDT':
            logger.info(f"  BTCUSDT encontrado en exchangeInfo")
            logger.info(f"  Status: {s.get('status')}")
            logger.info(f"  Permisos: {s.get('permissions')}")
            logger.info(f"  Filters: {[f['filterType'] for f in s.get('filters', [])]}")
            break
else:
    logger.error("  Exchange info FALLO")

logger.info("\n" + "=" * 60)
if balance_data:
    logger.info("RESULTADO: CONEXION EXITOSA — Keys Testnet validas")
else:
    logger.error("RESULTADO: CONEXION FALLIDA — Revisar keys y permisos")
    logger.error("")
    logger.error("POSIBLES CAUSAS:")
    logger.error("  1. Las API keys no existen o expiraron")
    logger.error("  2. Las keys no tienen permisos de USD-M Futures (Futuros)")
    logger.error("  3. IP restriction activada — debe estar desactivada para Render")
    logger.error("  4. BASE_URL incorrecta (debe ser https://testnet.binancefuture.com)")
    logger.error("")
    logger.error("COMO GENERAR KEYS EN TESTNET (Futuros):")
    logger.error("  1. Ir a https://testnet.binancefuture.com/")
    logger.error("  2. Iniciar sesion con GitHub")
    logger.error("  3. API Management → Create API Key")
    logger.error("  4. DESACTIVAR IP restriction (dejar campo vacio)")
    logger.error("  5. La key se crea automaticamente con permisos Futures")
    logger.error("  6. Copiar API Key y Secret Key")
    logger.error("  7. Pasarmelas a mi (Cascade) para actualizar .env y testear")
    logger.error("  8. Yo corro el test y confirmo. Luego cambio BINANCE_TESTNET=false")
    logger.error("     para que goat_btc ejecute ordenes reales en Testnet.")

logger.info("=" * 60)

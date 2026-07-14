"""okx_feed.py — OKX Market Data Feed para GOAT BTC
Reemplaza BinanceFeed — datos y ejecución del mismo exchange (OKX).
Usa endpoints públicos (sin autenticación) para klines, trades y order book.
"""

import requests
import time
import logging
import threading
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger('okx_feed')

OKX_BASE_URL = 'https://www.okx.com'
OKX_INSTRUMENT = 'BTC-USDT-SWAP'

# OKX API bar format: lowercase for minutes, uppercase H for hours
OKX_BAR_MAP = {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
               '1h': '1H', '1H': '1H', '2h': '2H', '4h': '4H'}


class OKXFeed:
    """Feed de datos de mercado OKX (público, sin auth)."""

    def __init__(self, instrument=None):
        self.instrument = instrument or OKX_INSTRUMENT
        self._klines = {'1m': deque(maxlen=200), '5m': deque(maxlen=200), '1h': deque(maxlen=200)}
        self._trades = deque(maxlen=500)
        self._book = {'bids': [], 'asks': []}
        self._last_price = 0.0
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def iniciar(self):
        """Inicia feed en background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name='okx_feed')
        self._thread.start()
        logger.info(f"OKX Feed iniciado — {self.instrument}")

    def detener(self):
        self._running = False

    def _loop(self):
        """Loop principal: fetch data cada 2 segundos."""
        # Carga inicial
        self._fetch_klines('1m', 200)
        self._fetch_klines('5m', 200)
        self._fetch_klines('1h', 200)
        self._fetch_trades()
        self._fetch_book()

        while self._running:
            try:
                self._fetch_klines('1m', 50)
                self._fetch_klines('5m', 50)
                self._fetch_klines('1h', 50)
                self._fetch_trades()
                self._fetch_book()
            except Exception as e:
                logger.warning(f"OKX Feed error: {e}")
            time.sleep(2)

    def _fetch_klines(self, timeframe, limit):
        """Fetch klines desde OKX public API."""
        try:
            url = f'{OKX_BASE_URL}/api/v5/market/candles'
            api_bar = OKX_BAR_MAP.get(timeframe, timeframe)
            params = {'instId': self.instrument, 'bar': api_bar, 'limit': limit}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == '0' and data.get('data'):
                    klines = []
                    for row in data['data']:
                        klines.append({
                            'time': int(row[0]),
                            'open': float(row[1]),
                            'high': float(row[2]),
                            'low': float(row[3]),
                            'close': float(row[4]),
                            'volume': float(row[5]),
                        })
                    klines.reverse()
                    with self._lock:
                        if klines:
                            self._last_price = klines[-1]['close']
                        self._klines[timeframe] = deque(klines, maxlen=200)
        except Exception as e:
            logger.warning(f"Error fetching klines {timeframe}: {e}")

    def _fetch_trades(self):
        """Fetch últimos trades desde OKX public API.
        OKX trade format: [tradeId, price, size, timestamp, side, ...]
        side: 'buy' (agresivo comprador) o 'sell' (agresivo vendedor)
        """
        try:
            url = f'{OKX_BASE_URL}/api/v5/market/trades'
            params = {'instId': self.instrument, 'limit': 100}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == '0' and data.get('data'):
                    trades = []
                    for row in data['data']:
                        trades.append({
                            'time': int(row[3]),      # timestamp ms
                            'price': float(row[1]),
                            'amount': float(row[2]),
                            'is_buyer_maker': row[4] == 'sell',  # sell=agresivo vendedor
                        })
                    with self._lock:
                        self._trades = deque(trades, maxlen=500)
        except Exception as e:
            logger.warning(f"Error fetching trades: {e}")

    def _fetch_book(self):
        """Fetch order book desde OKX public API."""
        try:
            url = f'{OKX_BASE_URL}/api/v5/market/books'
            params = {'instId': self.instrument, 'sz': '20'}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == '0' and data.get('data'):
                    book = data['data'][0]
                    bids = [[float(b[0]), float(b[1])] for b in book.get('bids', [])]
                    asks = [[float(a[0]), float(a[1])] for a in book.get('asks', [])]
                    with self._lock:
                        self._book = {'bids': bids, 'asks': asks}
        except Exception as e:
            logger.warning(f"Error fetching book: {e}")

    def get_klines(self, timeframe):
        with self._lock:
            return list(self._klines.get(timeframe, []))

    def get_trades(self):
        with self._lock:
            return list(self._trades)

    def get_book(self):
        with self._lock:
            return self._book['bids'], self._book['asks']

    def get_last_price(self):
        return self._last_price

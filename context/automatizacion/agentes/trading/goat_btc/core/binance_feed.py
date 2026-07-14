import json
import logging
import threading
import time
import urllib.request
from collections import deque
from typing import Optional

try:
    import websocket
except ImportError:
    websocket = None

logger = logging.getLogger(__name__)

BASE_URL = "wss://stream.binance.com:9443/ws"
REST_URL = "https://api.binance.com/api/v3/klines"

STREAMS = {
    "btcusdt@kline_1m": "klines_1m",
    "btcusdt@kline_5m": "klines_5m",
    "btcusdt@kline_1h": "klines_1h",
    "btcusdt@depth20": "depth20",
    "btcusdt@aggTrade": "aggTrade",
}

KLINE_BUFFER_MAX = 200
TRADES_BUFFER_MAX = 500


class BinanceFeed:
    def __init__(self):
        self.conns: dict[str, websocket.WebSocketApp] = {}
        self.running: bool = False
        self._retry_counts: dict[str, int] = {}
        self._threads: list[threading.Thread] = []

        self.buffers = {
            "klines_1m": deque(maxlen=KLINE_BUFFER_MAX),
            "klines_5m": deque(maxlen=KLINE_BUFFER_MAX),
            "klines_1h": deque(maxlen=KLINE_BUFFER_MAX),
            "trades": deque(maxlen=TRADES_BUFFER_MAX),
            "bids": [],
            "asks": [],
        }

    def _on_message(self, stream_name: str, buffer_key: str, ws, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning("[%s] JSON parse error: %s", stream_name, message[:200])
            return

        if buffer_key.startswith("klines_"):
            self._handle_kline(stream_name, buffer_key, data)
        elif buffer_key == "depth20":
            self._handle_depth(data)
        elif buffer_key == "aggTrade":
            self._handle_trade(stream_name, data)

    def _handle_kline(self, stream_name: str, buffer_key: str, data: dict):
        try:
            kline = data.get("k")
            if not kline:
                return
            parsed = {
                "time": float(kline["T"]) / 1000.0,
                "open": float(kline["o"]),
                "high": float(kline["h"]),
                "low": float(kline["l"]),
                "close": float(kline["c"]),
                "volume": float(kline["v"]),
            }
            self.buffers[buffer_key].append(parsed)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("[%s] Error parsing kline: %s", stream_name, e)

    def _handle_depth(self, data: dict):
        try:
            raw_bids = data.get("b", [])
            raw_asks = data.get("a", [])
            self.buffers["bids"] = [
                (float(level[0]), float(level[1])) for level in raw_bids if len(level) >= 2
            ]
            self.buffers["asks"] = [
                (float(level[0]), float(level[1])) for level in raw_asks if len(level) >= 2
            ]
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Error parsing depth: %s", e)

    def _handle_trade(self, stream_name: str, data: dict):
        try:
            parsed = {
                "price": float(data["p"]),
                "quantity": float(data["q"]),
                "time": float(data["T"]) / 1000.0,
                "is_buyer_maker": bool(data["m"]),
            }
            self.buffers["trades"].append(parsed)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("[%s] Error parsing aggTrade: %s", stream_name, e)

    def _on_error(self, stream_name: str, ws, error):
        logger.error("[%s] WebSocket error: %s", stream_name, error)
        self.reconectar(stream_name)

    def _on_close(self, stream_name: str, ws, close_status_code, close_msg):
        logger.warning("[%s] WebSocket closed (%s): %s", stream_name, close_status_code, close_msg)
        if self.running:
            self.reconectar(stream_name)

    def _on_open(self, stream_name: str, ws):
        logger.info("[%s] WebSocket connected", stream_name)
        self._retry_counts[stream_name] = 0

    def _fetch_historical_klines(self, interval: str, limit: int = 50) -> list[dict]:
        try:
            url = f"{REST_URL}?symbol=BTCUSDT&interval={interval}&limit={limit}"
            resp = urllib.request.urlopen(url, timeout=10)
            raw = json.loads(resp.read().decode())
            parsed = []
            for k in raw:
                parsed.append({
                    "time": float(k[0]) / 1000.0,
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                })
            return parsed
        except Exception as e:
            logger.warning("Error fetching historical klines for %s: %s", interval, e)
            return []

    def iniciar(self):
        if websocket is None:
            logger.error("No WebSocket library available (websocket-client not installed)")
            return

        self.running = True
        self.conns.clear()

        logger.info("Fetching historical klines from Binance REST API...")
        HISTORICAL_MAP = {"1m": "1m", "5m": "5m", "1h": "1h"}
        for buf_key, interval in HISTORICAL_MAP.items():
            historical = self._fetch_historical_klines(interval, 50)
            key = f"klines_{buf_key}"
            if key in self.buffers and historical:
                self.buffers[key].extend(historical)
                logger.info("Loaded %d historical klines for %s", len(historical), buf_key)

        for stream_name, buffer_key in STREAMS.items():
            url = f"{BASE_URL}/{stream_name}"

            ws = websocket.WebSocketApp(
                url,
                on_open=lambda ws, sn=stream_name: self._on_open(sn, ws),
                on_message=lambda ws, msg, sn=stream_name, bk=buffer_key: self._on_message(sn, bk, ws, msg),
                on_error=lambda ws, err, sn=stream_name: self._on_error(sn, ws, err),
                on_close=lambda ws, close_status_code, close_msg, sn=stream_name: self._on_close(sn, ws, close_status_code, close_msg),
            )

            self.conns[stream_name] = ws

            t = threading.Thread(target=ws.run_forever, daemon=True, kwargs={"ping_interval": 30, "ping_timeout": 10})
            t.start()
            self._threads.append(t)

            logger.info("[%s] Connection initiated to %s", stream_name, url)
            time.sleep(1)

    def detener(self):
        self.running = False
        for stream_name, ws in self.conns.items():
            try:
                ws.close()
                logger.info("[%s] WebSocket closed", stream_name)
            except Exception as e:
                logger.warning("[%s] Error closing WebSocket: %s", stream_name, e)
        self.conns.clear()

    def reconectar(self, stream_name: str):
        if not self.running:
            return

        retry_count = self._retry_counts.get(stream_name, 0) + 1
        self._retry_counts[stream_name] = retry_count
        backoff = min(30, 2 ** retry_count)

        logger.info("[%s] Reconnecting in %ds (attempt %d)", stream_name, backoff, retry_count)

        old_ws = self.conns.get(stream_name)
        if old_ws:
            try:
                old_ws.close()
            except Exception:
                pass

        time.sleep(backoff)

        buffer_key = STREAMS.get(stream_name)
        if buffer_key is None:
            logger.error("[%s] Unknown stream, cannot reconnect", stream_name)
            return

        url = f"{BASE_URL}/{stream_name}"
        ws = websocket.WebSocketApp(
            url,
            on_open=lambda ws, sn=stream_name: self._on_open(sn, ws),
            on_message=lambda ws, msg, sn=stream_name, bk=buffer_key: self._on_message(sn, bk, ws, msg),
            on_error=lambda ws, err, sn=stream_name: self._on_error(sn, ws, err),
            on_close=lambda ws, close_status_code, close_msg, sn=stream_name: self._on_close(sn, ws, close_status_code, close_msg),
        )

        self.conns[stream_name] = ws
        t = threading.Thread(target=ws.run_forever, daemon=True, kwargs={"ping_interval": 30, "ping_timeout": 10})
        t.start()
        self._threads.append(t)

        logger.info("[%s] Reconnection initiated (attempt %d)", stream_name, retry_count)

    def get_klines(self, tf: str) -> deque:
        key = f"klines_{tf}"
        return self.buffers.get(key, deque())

    def get_trades(self) -> deque:
        return self.buffers.get("trades", deque())

    def get_book(self) -> tuple[list, list]:
        return self.buffers.get("bids", []), self.buffers.get("asks", [])

    def get_last_price(self) -> Optional[float]:
        klines_1m = self.buffers.get("klines_1m", deque())
        if klines_1m:
            return klines_1m[-1]["close"]
        trades = self.buffers.get("trades", deque())
        if trades:
            return trades[-1]["price"]
        return None

    def get_precios(self, tf: str) -> list[float]:
        klines = self.get_klines(tf)
        return [k["close"] for k in klines]

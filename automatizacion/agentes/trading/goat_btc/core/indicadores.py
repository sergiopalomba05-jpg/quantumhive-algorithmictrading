"""Cálculos de indicadores técnicos para GOAT BTC Trading Agent.
Funciones puras sin dependencias del proyecto. Solo math, statistics, typing, collections.
"""

import math
import statistics
from typing import Any
from collections import deque


def calcular_bb(precios: list, periodo: int = 30, desviacion: float = 3.0) -> tuple:
    """Calcula Bollinger Bands: media, superior, inferior.
    media = SMA de precios (últimos `periodo`)
    desviacion_std = desviación estándar poblacional de los últimos `periodo` precios
    superior = media + desviacion * desviacion_std
    inferior = media - desviacion * desviacion_std
    Si len(precios) < periodo, retorna (None, None, None)
    """
    if not precios or len(precios) < periodo:
        return (None, None, None)
    ventana = precios[-periodo:]
    media = statistics.mean(ventana)
    std = statistics.pstdev(ventana)
    superior = media + desviacion * std
    inferior = media - desviacion * std
    return (media, superior, inferior)


def calcular_bbw(media: float, superior: float, inferior: float) -> float:
    """BBW = (superior - inferior) / media.
    Si media es 0 o None, retorna 0.0
    """
    if media is None or media == 0.0:
        return 0.0
    if superior is None or inferior is None:
        return 0.0
    return (superior - inferior) / media


def clasificar_bbw(bbw: float) -> str:
    """Clasifica el estado del mercado según el ancho de banda.
    bbw < 0.025 -> rango
    bbw > 0.035 -> tendencia
    else -> transicion
    """
    if bbw < 0.025:
        return "rango"
    if bbw > 0.035:
        return "tendencia"
    return "transicion"


def calcular_cvd_real(trades: list) -> int:
    """Calcula Cumulative Volume Delta real.
    trades es lista de dicts con keys: price (float), quantity (float), is_buyer_maker (bool)
    Agresivo comprador (is_buyer_maker=False): CVD += quantity
    Agresivo vendedor (is_buyer_maker=True): CVD -= quantity
    """
    if not trades:
        return 0
    cvd = 0.0
    for t in trades:
        if not isinstance(t, dict):
            continue
        qty = t.get("quantity", 0.0)
        if not t.get("is_buyer_maker", True):
            cvd += qty
        else:
            cvd -= qty
    return int(round(cvd))


def calcular_delta_vela(open: float, high: float, low: float, close: float, volume: float) -> float:
    """Calcula delta de una vela.
    Si high == low: retorna 0.0
    delta_ratio = (close - open) / (high - low)
    delta = delta_ratio * volume
    """
    if high == low:
        return 0.0
    delta_ratio = (close - open) / (high - low)
    return delta_ratio * volume


def calcular_adx(highs: list, lows: list, closes: list, periodo: int = 14) -> float:
    """Calcula ADX (Average Directional Index) de Wilder.
    TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
    +DM = high - prev_high si es positivo y > prev_low - low, sino 0
    -DM = prev_low - low si es positivo y > high - prev_high, sino 0
    Suavizado exponencial de TR, +DM, -DM por periodo.
    DX = abs(+DI - -DI) / (+DI + -DI) * 100
    ADX = SMA(DX, periodo)
    Si no hay suficientes datos, retorna 0.0
    """
    if not highs or not lows or not closes:
        return 0.0
    n = len(closes)
    if n < periodo + 1:
        return 0.0

    tr_values = []
    plus_dm_values = []
    minus_dm_values = []

    for i in range(1, n):
        high = highs[i]
        low = lows[i]
        prev_high = highs[i - 1]
        prev_low = lows[i - 1]
        prev_close = closes[i - 1]

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_values.append(tr)

        up_move = high - prev_high
        down_move = prev_low - low

        if up_move > down_move and up_move > 0:
            plus_dm_values.append(up_move)
        else:
            plus_dm_values.append(0.0)

        if down_move > up_move and down_move > 0:
            minus_dm_values.append(down_move)
        else:
            minus_dm_values.append(0.0)

    tr_smooth = _ema_wilder(tr_values, periodo)
    plus_smooth = _ema_wilder(plus_dm_values, periodo)
    minus_smooth = _ema_wilder(minus_dm_values, periodo)

    dx_values = []
    for tr_s, p_s, m_s in zip(tr_smooth, plus_smooth, minus_smooth):
        if tr_s == 0.0:
            continue
        plus_di = 100.0 * p_s / tr_s
        minus_di = 100.0 * m_s / tr_s
        di_sum = plus_di + minus_di
        if di_sum == 0.0:
            dx_values.append(0.0)
        else:
            dx = abs(plus_di - minus_di) / di_sum * 100.0
            dx_values.append(dx)

    if len(dx_values) < periodo:
        return 0.0

    adx = statistics.mean(dx_values[-periodo:])
    return adx


def _ema_wilder(valores: list, periodo: int) -> list:
    """Suavizado exponencial estilo Wilder (alpha = 1/periodo)."""
    if not valores:
        return []
    alpha = 1.0 / periodo
    ema = []
    # Wilder usa SMA inicial
    if len(valores) >= periodo:
        ema.append(statistics.mean(valores[:periodo]))
    else:
        ema.append(valores[0])
    for v in valores[periodo:]:
        ema.append(v * alpha + ema[-1] * (1 - alpha))
    return ema


def calcular_volumen_relativo(volumenes: list, indice_actual: int = -1) -> float:
    """Volumen actual / promedio de últimos 20 volúmenes antes del actual.
    Retorna 0.0 si el promedio es 0.
    """
    if not volumenes:
        return 0.0
    idx = indice_actual if indice_actual >= 0 else len(volumenes) - 1
    if idx < 0 or idx >= len(volumenes):
        return 0.0
    volumen_actual = volumenes[idx]
    antes = volumenes[max(0, idx - 20):idx]
    if not antes:
        return 0.0
    promedio = statistics.mean(antes)
    if promedio == 0.0:
        return 0.0
    return volumen_actual / promedio


def calcular_imbalance_book(bids: list, asks: list, top_n: int = 10) -> float:
    """Calcula imbalance del libro de órdenes.
    bids y asks son listas de (precio, cantidad)
    imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
    Rango -1 a 1. Retorna 0.0 si suma es 0.
    """
    if not bids or not asks:
        return 0.0
    bid_vol = sum(qty for _, qty in bids[:top_n])
    ask_vol = sum(qty for _, qty in asks[:top_n])
    total = bid_vol + ask_vol
    if total == 0.0:
        return 0.0
    return (bid_vol - ask_vol) / total


def clasificar_imbalance(imbalance: float) -> str:
    """Clasifica el imbalance del libro.
    > 0.3 -> presion_compradora
    < -0.3 -> presion_vendedora
    else -> neutro
    """
    if imbalance > 0.3:
        return "presion_compradora"
    if imbalance < -0.3:
        return "presion_vendedora"
    return "neutro"

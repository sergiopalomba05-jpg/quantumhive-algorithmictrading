"""indicadores.py — GOAT BTC Indicadores Técnicos Mejorados
BB 30/3.0 (reemplaza 20/2.0) | RSI 7 | Detección de mechas
Pendiente de bandas | Retorno a media
Incluye: ADX, CVD, BBW, delta velas, volumen relativo, imbalance
"""

import numpy as np
import logging

logger = logging.getLogger('indicadores')


def calcular_bb(precios, periodo=30, desviaciones=3.0):
    """Bollinger Bands M1 — período 30, desviación 3.0"""
    if len(precios) < periodo:
        return None, None, None, None
    sma = np.mean(precios[-periodo:])
    std = np.std(precios[-periodo:])
    bb_sup = sma + (desviaciones * std)
    bb_inf = sma - (desviaciones * std)
    bbw = (bb_sup - bb_inf) / sma if sma else 0
    return bb_sup, bb_inf, sma, bbw


def calcular_bbw(media, sup, inf):
    if not media or media == 0:
        return 0.0
    return (sup - inf) / media


def clasificar_bbw(bbw, umbral_bajo=0.025, umbral_alto=0.035):
    if bbw < umbral_bajo:
        return "RANGO"
    elif bbw < umbral_alto:
        return "TRANSICION"
    return "TENDENCIA"


def calcular_rsi(precios, periodo=7):
    """RSI período 7 — más sensible para scalping M1"""
    if len(precios) < periodo + 1:
        return 50
    deltas = np.diff(precios[-periodo-1:])
    ganancias = np.where(deltas > 0, deltas, 0)
    perdidas = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(ganancias)
    avg_loss = np.mean(perdidas)
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def detectar_mecha(open_p, high, low, close):
    """Detecta mecha de rechazo: 'long', 'short', o None.
    Mecha debe ser >= 2x el cuerpo.
    """
    cuerpo = abs(close - open_p)
    if cuerpo == 0:
        return None
    mecha_inf = min(open_p, close) - low
    mecha_sup = high - max(open_p, close)
    ratio_inf = mecha_inf / cuerpo
    ratio_sup = mecha_sup / cuerpo
    if ratio_inf >= 2.0:
        return "long"
    if ratio_sup >= 2.0:
        return "short"
    return None


def detectar_pendiente_bandas(sma_values, n=5):
    """Detecta dirección de la banda media (SMA).
    Retorna: 'up', 'down', 'flat'
    """
    if not sma_values or len(sma_values) < n * 2:
        return "flat"
    recientes = sma_values[-n:]
    anteriores = sma_values[-n*2:-n]
    prom_reciente = sum(recientes) / len(recientes)
    prom_anterior = sum(anteriores) / len(anteriores)
    diff = (prom_reciente - prom_anterior) / prom_anterior if prom_anterior else 0
    if diff > 0.0001:
        return "up"
    elif diff < -0.0001:
        return "down"
    return "flat"


def detectar_retorno_media(precio, sma):
    """Detecta si precio está retornando a la banda media.
    Retorna True si está dentro de 0.15% de la media.
    """
    if not sma or not precio:
        return False
    dist_pct = abs(precio - sma) / sma
    return dist_pct < 0.0015


def calcular_atr(highs, lows, closes, periodo=14):
    """Average True Range — para SL/TP dinámico"""
    if len(closes) < periodo + 1:
        return 0
    trs = []
    for i in range(-periodo, 0):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i-1]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return np.mean(trs)


def calcular_adx(highs, lows, closes, periodo=14):
    """ADX simplificado usando Wilder's smoothing"""
    if len(closes) < periodo * 2:
        return 0.0
    n = periodo
    tr_list, plus_dm_list, minus_dm_list = [], [], []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_list.append(tr)
        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        plus_dm_list.append(up_move if up_move > down_move and up_move > 0 else 0)
        minus_dm_list.append(down_move if down_move > up_move and down_move > 0 else 0)
    # Wilder smoothing
    atr = np.mean(tr_list[-n:])
    if atr == 0:
        return 0.0
    plus_di = 100 * np.mean(plus_dm_list[-n:]) / atr
    minus_di = 100 * np.mean(minus_dm_list[-n:]) / atr
    di_sum = plus_di + minus_di
    if di_sum == 0:
        return 0.0
    dx = 100 * abs(plus_di - minus_di) / di_sum
    return round(min(100, dx), 1)


def calcular_cvd_real(trades):
    """Cumulative Volume Delta desde lista de trades.
    buyer_maker=False → agresivo comprador → positivo
    buyer_maker=True → agresivo vendedor → negativo
    """
    cvd = 0
    for t in trades:
        amount = t.get('amount', t.get('qty', 0))
        if t.get('is_buyer_maker', True):
            cvd -= amount
        else:
            cvd += amount
    return cvd


def calcular_delta_vela(open_p, high, low, close, volume):
    """Delta de una vela: presión compradora/vendedora firmada.
    Fórmula: ((close - open) / (high - low)) * volume
    """
    rango = high - low
    if rango == 0:
        return 0.0
    delta = ((close - open_p) / rango) * volume
    return round(delta, 2)


def calcular_volumen_relativo(volumes, periodo=20):
    """Volumen relativo: ratio del último volumen vs promedio."""
    if len(volumes) < periodo:
        return 1.0
    avg_vol = np.mean(volumes[-periodo:])
    if avg_vol == 0:
        return 1.0
    return float(volumes[-1]) / float(avg_vol)


def calcular_imbalance_book(bids, asks, levels=10):
    """Order book imbalance: (bid_vol - ask_vol) / (bid_vol + ask_vol)"""
    bid_vol = sum(b[1] for b in bids[:levels]) if bids else 0
    ask_vol = sum(a[1] for a in asks[:levels]) if asks else 0
    total = bid_vol + ask_vol
    if total == 0:
        return 0.0
    return round((bid_vol - ask_vol) / total, 4)


def clasificar_imbalance(imbalance):
    if imbalance > 0.2:
        return "presion_compra"
    elif imbalance < -0.2:
        return "presion_venta"
    return "neutral"


def calcular_indicadores_m1(velas, bb_sup_prev=None, bb_inf_prev=None, sma_values=None):
    """Calcula todos los indicadores M1 con BB 30/3.0"""
    if not velas or len(velas) < 30:
        return {}
    closes = [v['close'] for v in velas]
    highs = [v['high'] for v in velas]
    lows = [v['low'] for v in velas]
    opens = [v['open'] for v in velas]
    precio_actual = closes[-1]
    bb_sup, bb_inf, bb_media, bbw = calcular_bb(closes, periodo=30, desviaciones=3.0)
    rsi_7 = calcular_rsi(closes, periodo=7)
    atr = calcular_atr(highs, lows, closes)
    mecha = detectar_mecha(opens[-1], highs[-1], lows[-1], closes[-1])
    toco_sup = False
    toco_inf = False
    if bb_sup and bb_inf:
        toco_sup = highs[-1] >= bb_sup
        toco_inf = lows[-1] <= bb_inf
    if sma_values is None:
        sma_values = []
    if bb_media:
        sma_values.append(bb_media)
        if len(sma_values) > 100:
            sma_values = sma_values[-100:]
    pendiente = detectar_pendiente_bandas(sma_values)
    retorno = detectar_retorno_media(precio_actual, bb_media)
    return {
        'bb_superior_m1': bb_sup, 'bb_inferior_m1': bb_inf,
        'bb_media_m1': bb_media, 'bbw_m1': bbw, 'rsi_7': rsi_7,
        'atr_m1': atr, 'mecha_rechazo_m1': mecha,
        'toco_bb_superior_m1': toco_sup, 'toco_bb_inferior_m1': toco_inf,
        'pendiente_bandas_m1': pendiente, 'retorno_media_m1': retorno,
        'sma_m1_values': sma_values, 'precio_actual': precio_actual,
    }

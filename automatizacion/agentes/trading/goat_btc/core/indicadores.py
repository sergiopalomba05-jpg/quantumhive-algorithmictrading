"""indicadores.py — GOAT BTC Indicadores Técnicos Mejorados
BB 30/3.0 (reemplaza 20/2.0) | RSI 7 | Detección de mechas
Pendiente de bandas | Retorno a media
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
    """Detecta tipo de mecha: long_wick, short_wick, o None.
    Mecha debe ser >= 2x el cuerpo.
    """
    cuerpo = abs(close - open_p)
    if cuerpo == 0:
        return None
    mecha_inf = min(open_p, close) - low
    mecha_sup = high - max(open_p, close)
    
    ratio_inf = mecha_inf / cuerpo if cuerpo > 0 else 0
    ratio_sup = mecha_sup / cuerpo if cuerpo > 0 else 0
    
    if ratio_inf >= 2.0:
        return "long_wick"
    if ratio_sup >= 2.0:
        return "short_wick"
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


def calcular_indicadores_m1(velas, bb_sup_prev=None, bb_inf_prev=None, sma_values=None):
    """Calcula todos los indicadores M1 con BB 30/3.0"""
    if not velas or len(velas) < 30:
        return {}
    
    closes = [v['close'] for v in velas]
    highs = [v['high'] for v in velas]
    lows = [v['low'] for v in velas]
    opens = [v['open'] for v in velas]
    
    precio_actual = closes[-1]
    
    # BB 30/3.0
    bb_sup, bb_inf, bb_media, bbw = calcular_bb(closes, periodo=30, desviaciones=3.0)
    
    # RSI 7
    rsi_7 = calcular_rsi(closes, periodo=7)
    
    # ATR
    atr = calcular_atr(highs, lows, closes)
    
    # Mecha última vela
    mecha = detectar_mecha(opens[-1], highs[-1], lows[-1], closes[-1])
    
    # Toco bandas
    toco_sup = False
    toco_inf = False
    if bb_sup and bb_inf:
        toco_sup = highs[-1] >= bb_sup
        toco_inf = lows[-1] <= bb_inf
    
    # Pendiente de bandas
    if sma_values is None:
        sma_values = []
    if bb_media:
        sma_values.append(bb_media)
        if len(sma_values) > 100:
            sma_values = sma_values[-100:]
    pendiente = detectar_pendiente_bandas(sma_values)
    
    # Retorno a media
    retorno = detectar_retorno_media(precio_actual, bb_media)
    
    return {
        'bb_superior_m1': bb_sup,
        'bb_inferior_m1': bb_inf,
        'bb_media_m1': bb_media,
        'bbw_m1': bbw,
        'rsi_7': rsi_7,
        'atr_m1': atr,
        'mecha_rechazo_m1': mecha,
        'toco_bb_superior_m1': toco_sup,
        'toco_bb_inferior_m1': toco_inf,
        'pendiente_bandas_m1': pendiente,
        'retorno_media_m1': retorno,
        'sma_m1_values': sma_values,
        'precio_actual': precio_actual,
    }

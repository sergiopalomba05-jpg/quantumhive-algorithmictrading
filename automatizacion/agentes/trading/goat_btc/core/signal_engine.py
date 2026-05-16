"""signal_engine.py — M1 Scalper Scoring Engine for GOAT BTC
Nuevo sistema de scoring agresivo para operar en M1 con filtro M5.
Timeframe principal: M1 (decision de entrada)
Filtro de regimen: M5 (reemplaza M15)
Contexto macro: H1 (se mantiene)
"""

import time
import logging

logger = logging.getLogger('signal_engine')

SCORING_SCALPER_M1 = {
    'precio_en_bb_inf_m1': 15,
    'precio_en_bb_sup_m1': 15,
    'precio_en_media_m1': 8,
    'vela_rechazo_m1': 12,
    'cvd_alineado_m1': 12,
    'cvd_divergencia_m1': 10,
    'delta_confirma_m1': 8,
    'imbalance_favor': 5,
    'regimen_m5_rango': 15,
    'bbw_m5_bajo': 10,
}

SCORE_MINIMO_ENTRADA = 55
SCORE_MINIMO_CALIDAD = 70

SCALPER_CONFIG = {
    'sl_multiplicador_atr': 0.3,
    'tp_multiplicador_atr': 0.6,
    'max_posiciones_simultaneas': 1,
    'cooldown_entre_trades': 60,
    'max_trades_por_hora': 8,
    'max_perdida_diaria': 20,
}

BLOQUEOS_SCALPER = [
    'bbw_m1_extremo',
    'adx_m5_mayor_50',
    'posicion_activa',
    'cooldown_activo',
    'max_trades_hora',
    'drawdown_diario',
]


def _detectar_rechazo(open_p: float, high: float, low: float, close: float) -> str:
    body = abs(close - open_p)
    if body == 0:
        return None
    upper_wick = high - max(open_p, close)
    lower_wick = min(open_p, close) - low
    if close > open_p and lower_wick > body * 1.5:
        return "alcista"
    if close < open_p and upper_wick > body * 1.5:
        return "bajista"
    return None


def calcular_score_scalper(indicadores: dict) -> dict:
    """Evalua condiciones M1 y retorna score (0-100), direccion y confluencias.

    Condiciones para COMPRA:
    1. Precio toca o cruza BB inferior M1
    2. Vela de rechazo alcista en M1 (mecha inferior larga)
    3. CVD corto positivo o divergencia alcista
    4. M5 en regimen rango (BBW < 0.003)
    5. H1 no en tendencia bajista fuerte (ADX < 40 o CVD positivo)

    Condiciones para VENTA:
    1. Precio toca o cruza BB superior M1
    2. Vela de rechazo bajista en M1 (mecha superior larga)
    3. CVD corto negativo o divergencia bajista
    4. M5 en regimen rango
    5. H1 no en tendencia alcista fuerte
    """
    score = 0
    confluencias = []
    direccion = None

    precio = indicadores.get("precio_actual", 0)
    bb_sup_m1 = indicadores.get("bb_superior_m1")
    bb_inf_m1 = indicadores.get("bb_inferior_m1")
    bb_media_m1 = indicadores.get("bb_media_m1")
    toco_sup_m1 = indicadores.get("toco_bb_superior_m1", False)
    toco_inf_m1 = indicadores.get("toco_bb_inferior_m1", False)

    bbw_m5 = indicadores.get("bbw_m5", 99)
    adx_m5 = indicadores.get("adx_m5", 99)
    cvd_corto = indicadores.get("cvd_corto", 0)
    deltas = indicadores.get("ultimas_5_deltas", [])
    delta_vela = indicadores.get("delta_ultima_vela", 0)
    imbalance = indicadores.get("imbalance_book", 0)

    cvd_largo_h1 = indicadores.get("cvd_largo_H1", 0)
    adx_h1 = indicadores.get("adx_h1", 0)

    rechazo = indicadores.get("rechazo_m1")

    # --- Determinar direccion potencial ---
    if toco_inf_m1 and not toco_sup_m1:
        direccion = "long"
    elif toco_sup_m1 and not toco_inf_m1:
        direccion = "short"
    elif toco_inf_m1 and toco_sup_m1:
        dist_sup = abs(precio - bb_sup_m1) if bb_sup_m1 else 999
        dist_inf = abs(precio - bb_inf_m1) if bb_inf_m1 else 999
        direccion = "short" if dist_sup < dist_inf else "long"

    if direccion is None:
        return {"score": 0, "direccion": None, "confluencias": [], "es_alerta": False, "es_premium": False}

    # --- Precio (40 puntos) ---
    if direccion == "long" and toco_inf_m1:
        score += SCORING_SCALPER_M1['precio_en_bb_inf_m1']
        confluencias.append("toco_bb_inferior_m1")
    elif direccion == "short" and toco_sup_m1:
        score += SCORING_SCALPER_M1['precio_en_bb_sup_m1']
        confluencias.append("toco_bb_superior_m1")

    if bb_media_m1:
        dist_media = abs(precio - bb_media_m1) / precio
        if dist_media < 0.001:
            score += SCORING_SCALPER_M1['precio_en_media_m1']
            confluencias.append("rebote_media_m1")

    if rechazo == "alcista" and direccion == "long":
        score += SCORING_SCALPER_M1['vela_rechazo_m1']
        confluencias.append("vela_rechazo_alcista_m1")
    elif rechazo == "bajista" and direccion == "short":
        score += SCORING_SCALPER_M1['vela_rechazo_m1']
        confluencias.append("vela_rechazo_bajista_m1")

    # --- Momentum (35 puntos) ---
    if direccion == "long" and cvd_corto > 0:
        score += SCORING_SCALPER_M1['cvd_alineado_m1']
        confluencias.append("cvd_alineado_long")
    elif direccion == "short" and cvd_corto < 0:
        score += SCORING_SCALPER_M1['cvd_alineado_m1']
        confluencias.append("cvd_alineado_short")

    if len(deltas) >= 3:
        if direccion == "long" and deltas[-1] > deltas[-3]:
            score += SCORING_SCALPER_M1['cvd_divergencia_m1']
            confluencias.append("divergencia_cvd_alcista")
        elif direccion == "short" and deltas[-1] < deltas[-3]:
            score += SCORING_SCALPER_M1['cvd_divergencia_m1']
            confluencias.append("divergencia_cvd_bajista")

    if direccion == "long" and delta_vela > 0:
        score += SCORING_SCALPER_M1['delta_confirma_m1']
        confluencias.append("delta_confirma_long")
    elif direccion == "short" and delta_vela < 0:
        score += SCORING_SCALPER_M1['delta_confirma_m1']
        confluencias.append("delta_confirma_short")

    if direccion == "long" and imbalance > 0.2:
        score += SCORING_SCALPER_M1['imbalance_favor']
        confluencias.append("imbalance_favorable_long")
    elif direccion == "short" and imbalance < -0.2:
        score += SCORING_SCALPER_M1['imbalance_favor']
        confluencias.append("imbalance_favorable_short")

    # --- Regimen M5 (25 puntos) ---
    if bbw_m5 < 0.025:
        score += SCORING_SCALPER_M1['regimen_m5_rango']
        confluencias.append("regimen_m5_rango")
    elif bbw_m5 < 0.035:
        score += 5
        confluencias.append("regimen_m5_transicion")

    if bbw_m5 < 0.003:
        score += SCORING_SCALPER_M1['bbw_m5_bajo']
        confluencias.append("bbw_m5_comprimido")

    # --- Penalidad por tendencia fuerte en H1 en contra ---
    if adx_h1 > 40:
        if (direccion == "long" and cvd_largo_h1 < 0) or (direccion == "short" and cvd_largo_h1 > 0):
            score = max(0, score - 20)
            confluencias.append("penalidad_h1_contra")

    score = min(100, max(0, score))

    return {
        "score": score,
        "direccion": direccion,
        "confluencias": confluencias,
        "es_alerta": score >= SCORE_MINIMO_ENTRADA,
        "es_premium": score >= SCORE_MINIMO_CALIDAD,
    }


def verificar_bloqueos(indicadores: dict, estado_trading: dict) -> dict:
    """Verifica todas las condiciones de bloqueo.

    estado_trading debe contener:
        - posicion_activa: bool
        - ultimo_trade_time: float (timestamp)
        - trades_hora: int (cantidad en la ultima hora)
        - perdida_diaria: float (perdida acumulada en el dia)
    """
    bloqueos = []
    bbw_m1 = indicadores.get("bbw_m1", 0)
    adx_m5 = indicadores.get("adx_m5", 0)

    if bbw_m1 > 0.005:
        bloqueos.append("bbw_m1_extremo")
    if adx_m5 > 50:
        bloqueos.append("adx_m5_mayor_50")
    if estado_trading.get("posicion_activa", False):
        bloqueos.append("posicion_activa")

    ahora = time.time()
    cooldown = SCALPER_CONFIG['cooldown_entre_trades']
    ultimo_trade = estado_trading.get("ultimo_trade_time", 0)
    if (ahora - ultimo_trade) < cooldown:
        bloqueos.append("cooldown_activo")
    if estado_trading.get("trades_hora", 0) >= SCALPER_CONFIG['max_trades_por_hora']:
        bloqueos.append("max_trades_hora")
    if estado_trading.get("perdida_diaria", 0) >= SCALPER_CONFIG['max_perdida_diaria']:
        bloqueos.append("drawdown_diario")

    return {
        "bloqueado": len(bloqueos) > 0,
        "bloqueos": bloqueos,
        "puede_entrar": not any(b in bloqueos for b in ["posicion_activa", "cooldown_activo", "max_trades_hora", "drawdown_diario"]),
    }

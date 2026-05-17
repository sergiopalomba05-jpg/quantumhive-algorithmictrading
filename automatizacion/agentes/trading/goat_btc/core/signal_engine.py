"""signal_engine.py — GOAT BTC Signal Engine
Estrategia: Bollinger Bands 30/3.0 — tocar banda = entrada
Score mínimo: 25 (tocar banda solo = 40 puntos, entra directo)
"""

import time
import logging

logger = logging.getLogger('signal_engine')

SCORING_SCALPER_M1 = {
    'precio_en_bb_inf_m1': 40,
    'precio_en_bb_sup_m1': 40,
    'precio_en_media_m1': 10,
    'vela_rechazo_m1': 15,
    'cvd_alineado_m1': 5,
    'rsi_confirmacion': 5,
    'regimen_favorable': 5,
}

SCORE_MINIMO_ENTRADA = 25
SCORE_MINIMO_CALIDAD = 50

SCALPER_CONFIG = {
    'sl_multiplicador_atr': 0.3,
    'tp_multiplicador_atr': 0.6,
    'max_posiciones_simultaneas': 1,
    'cooldown_entre_trades': 10,
    'max_trades_por_hora': 999,
    'max_perdida_diaria': 50,
}

BLOQUEOS_SCALPER = [
    'bbw_m1_extremo',
    'posicion_activa',
    'cooldown_activo',
    'max_trades_hora',
    'drawdown_diario',
]


def calcular_score_scalper(indicadores: dict) -> dict:
    """Evalua condiciones M1. Tocar banda = entrada directa."""
    score = 0
    confluencias = []
    direccion = None
    modo = None

    precio = indicadores.get("precio_actual", 0)
    bb_sup_m1 = indicadores.get("bb_superior_m1")
    bb_inf_m1 = indicadores.get("bb_inferior_m1")
    bb_media_m1 = indicadores.get("bb_media_m1")
    toco_sup_m1 = indicadores.get("toco_bb_superior_m1", False)
    toco_inf_m1 = indicadores.get("toco_bb_inferior_m1", False)

    bbw_m5 = indicadores.get("bbw_m5", 99)
    cvd_corto = indicadores.get("cvd_corto", 0)
    delta_vela = indicadores.get("delta_ultima_vela", 0)
    rsi_7 = indicadores.get("rsi_7", 50)
    mecha_rechazo = indicadores.get("mecha_rechazo_m1")
    pendiente_bandas = indicadores.get("pendiente_bandas_m1", "flat")
    retorno_media = indicadores.get("retorno_media_m1", False)

    # ── PRIORIDAD 1: Tocar banda = entrada directa ──
    if toco_inf_m1:
        direccion = "long"
        modo = "reversion"
        score += SCORING_SCALPER_M1['precio_en_bb_inf_m1']
        confluencias.append("toco_bb_inferior_m1")

        if mecha_rechazo == "long":
            score += SCORING_SCALPER_M1['vela_rechazo_m1']
            confluencias.append("mecha_rechazo_long")
        if rsi_7 < 35:
            score += SCORING_SCALPER_M1['rsi_confirmacion']
            confluencias.append("rsi_sobreventa")
        elif rsi_7 < 45:
            score += 3
            confluencias.append("rsi_bajo")
        if cvd_corto > 0:
            score += SCORING_SCALPER_M1['cvd_alineado_m1']
            confluencias.append("cvd_comprador")

    elif toco_sup_m1:
        direccion = "short"
        modo = "reversion"
        score += SCORING_SCALPER_M1['precio_en_bb_sup_m1']
        confluencias.append("toco_bb_superior_m1")

        if mecha_rechazo == "short":
            score += SCORING_SCALPER_M1['vela_rechazo_m1']
            confluencias.append("mecha_rechazo_short")
        if rsi_7 > 65:
            score += SCORING_SCALPER_M1['rsi_confirmacion']
            confluencias.append("rsi_sobrecompra")
        elif rsi_7 > 55:
            score += 3
            confluencias.append("rsi_alto")
        if cvd_corto < 0:
            score += SCORING_SCALPER_M1['cvd_alineado_m1']
            confluencias.append("cvd_vendedor")

    # ── PRIORIDAD 2: Rebote en media (si no tocó banda) ──
    elif retorno_media and pendiente_bandas != "flat":
        if pendiente_bandas == "up":
            direccion = "long"
            modo = "rebote_media"
            score += SCORING_SCALPER_M1['precio_en_media_m1']
            confluencias.append("rebote_media_up")
            if delta_vela > 0:
                score += 5
                confluencias.append("delta_positivo")
        elif pendiente_bandas == "down":
            direccion = "short"
            modo = "rebote_media"
            score += SCORING_SCALPER_M1['precio_en_media_m1']
            confluencias.append("rebote_media_down")
            if delta_vela < 0:
                score += 5
                confluencias.append("delta_negativo")

    if direccion is None or score == 0:
        return {"score": 0, "direccion": None, "confluencias": [], "es_alerta": False, "es_premium": False, "modo": None}

    # Bonus régimen
    if bbw_m5 < 0.025:
        score += SCORING_SCALPER_M1['regimen_favorable']
        confluencias.append("regimen_rango")

    score = min(100, max(0, score))

    return {
        "score": score,
        "direccion": direccion,
        "confluencias": confluencias,
        "es_alerta": score >= SCORE_MINIMO_ENTRADA,
        "es_premium": score >= SCORE_MINIMO_CALIDAD,
        "modo": modo,
    }


def verificar_bloqueos(indicadores: dict, estado_trading: dict) -> dict:
    """Verifica condiciones de bloqueo.
    Sin bloqueo por posición activa — opera independiente de trades manuales.
    """
    bloqueos = []
    bbw_m1 = indicadores.get("bbw_m1", 0)

    if bbw_m1 > 0.12:
        bloqueos.append("bbw_m1_extremo")

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
        "puede_entrar": not any(b in bloqueos for b in ["cooldown_activo", "max_trades_hora", "drawdown_diario"]),
    }

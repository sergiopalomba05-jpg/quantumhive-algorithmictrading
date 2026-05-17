"""signal_engine.py — GOAT BTC Multi-Mode Signal Engine
3 modos de entrada:
  Modo A: Reversión en bandas (precio sale de banda + mecha rechazo)
  Modo B: Rebote en media (tendencia + retorno a banda media)
  Modo C: Surf de momentum (precio fuera de bandas, momentum)
Cooldown: 30s | Risk: $5/trade | Target: $10 (1:2)
"""

import time
import logging

logger = logging.getLogger('signal_engine')

SCORING_SCALPER_M1 = {
    'precio_en_bb_inf_m1': 15,
    'precio_en_bb_sup_m1': 15,
    'precio_en_media_m1': 10,
    'vela_rechazo_m1': 15,
    'cvd_alineado_m1': 10,
    'cvd_divergencia_m1': 8,
    'delta_confirma_m1': 6,
    'imbalance_favor': 5,
    'rsi_confirmacion': 8,
    'regimen_favorable': 12,
    'pendiente_bandas': 10,
}

SCORE_MINIMO_ENTRADA = 35
SCORE_MINIMO_CALIDAD = 55

SCALPER_CONFIG = {
    'sl_multiplicador_atr': 0.3,
    'tp_multiplicador_atr': 0.6,
    'max_posiciones_simultaneas': 1,
    'cooldown_entre_trades': 15,
    'max_trades_por_hora': 12,
    'max_perdida_diaria': 20,
}

BLOQUEOS_SCALPER = [
    'bbw_m1_extremo',
    'posicion_activa',
    'cooldown_activo',
    'max_trades_hora',
    'drawdown_diario',
]


def calcular_score_scalper(indicadores: dict) -> dict:
    """Evalua condiciones M1 con 3 modos de entrada.

    Modo A (Reversión): Precio sale de banda + mecha rechazo + RSI
    Modo B (Rebote media): Tendencia + retorno a media + confirmación
    Modo C (Surf): Precio fuera de bandas + momentum + CVD
    """
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
    deltas = indicadores.get("ultimas_5_deltas", [])
    delta_vela = indicadores.get("delta_ultima_vela", 0)
    imbalance = indicadores.get("imbalance_book", 0)

    cvd_largo_h1 = indicadores.get("cvd_largo_H1", 0)
    adx_h1 = indicadores.get("adx_h1", 0)

    mecha_rechazo = indicadores.get("mecha_rechazo_m1")
    pendiente_bandas = indicadores.get("pendiente_bandas_m1", "flat")
    retorno_media = indicadores.get("retorno_media_m1", False)
    rsi_7 = indicadores.get("rsi_7", 50)

    # Modo A: Reversión en bandas
    if mecha_rechazo in ("long", "short"):
        direccion = mecha_rechazo
        modo = "reversion"
        if direccion == "long":
            score += SCORING_SCALPER_M1['precio_en_bb_inf_m1']
            confluencias.append("toco_bb_inferior_m1")
            score += SCORING_SCALPER_M1['vela_rechazo_m1']
            confluencias.append("mecha_rechazo_long")
            if rsi_7 < 35:
                score += SCORING_SCALPER_M1['rsi_confirmacion']
                confluencias.append("rsi_sobreventa")
            elif rsi_7 < 45:
                score += 4
                confluencias.append("rsi_bajo")
        elif direccion == "short":
            score += SCORING_SCALPER_M1['precio_en_bb_sup_m1']
            confluencias.append("toco_bb_superior_m1")
            score += SCORING_SCALPER_M1['vela_rechazo_m1']
            confluencias.append("mecha_rechazo_short")
            if rsi_7 > 65:
                score += SCORING_SCALPER_M1['rsi_confirmacion']
                confluencias.append("rsi_sobrecompra")
            elif rsi_7 > 55:
                score += 4
                confluencias.append("rsi_alto")

    # Modo B: Rebote en media (tendencia)
    elif retorno_media and pendiente_bandas != "flat":
        if pendiente_bandas == "up":
            direccion = "long"
            modo = "rebote_media"
            score += SCORING_SCALPER_M1['precio_en_media_m1']
            confluencias.append("rebote_media_up")
            score += SCORING_SCALPER_M1['pendiente_bandas']
            confluencias.append("bandas_pendiente_up")
            if delta_vela > 0:
                score += SCORING_SCALPER_M1['delta_confirma_m1']
                confluencias.append("delta_positivo")
            if rsi_7 > 45:
                score += 5
                confluencias.append("rsi_neutro_alcista")
        elif pendiente_bandas == "down":
            direccion = "short"
            modo = "rebote_media"
            score += SCORING_SCALPER_M1['precio_en_media_m1']
            confluencias.append("rebote_media_down")
            score += SCORING_SCALPER_M1['pendiente_bandas']
            confluencias.append("bandas_pendiente_down")
            if delta_vela < 0:
                score += SCORING_SCALPER_M1['delta_confirma_m1']
                confluencias.append("delta_negativo")
            if rsi_7 < 55:
                score += 5
                confluencias.append("rsi_neutro_bajista")

    # Modo C: Surf de momentum
    elif toco_inf_m1 or toco_sup_m1:
        if toco_inf_m1 and cvd_corto > 0 and delta_vela > 0:
            direccion = "long"
            modo = "surf"
            score += SCORING_SCALPER_M1['precio_en_bb_inf_m1']
            confluencias.append("surf_long_cvd")
            score += SCORING_SCALPER_M1['cvd_alineado_m1']
            confluencias.append("cvd_alfavor")
        elif toco_sup_m1 and cvd_corto < 0 and delta_vela < 0:
            direccion = "short"
            modo = "surf"
            score += SCORING_SCALPER_M1['precio_en_bb_sup_m1']
            confluencias.append("surf_short_cvd")
            score += SCORING_SCALPER_M1['cvd_alineado_m1']
            confluencias.append("cvd_en_contra")

    # Fallback: lógica original si ningún modo activó
    if direccion is None:
        if toco_inf_m1 and not toco_sup_m1:
            direccion = "long"
        elif toco_sup_m1 and not toco_inf_m1:
            direccion = "short"
        elif toco_inf_m1 and toco_sup_m1:
            dist_sup = abs(precio - bb_sup_m1) if bb_sup_m1 else 999
            dist_inf = abs(precio - bb_inf_m1) if bb_inf_m1 else 999
            direccion = "short" if dist_sup < dist_inf else "long"

    if direccion is None or score == 0:
        return {"score": 0, "direccion": None, "confluencias": [], "es_alerta": False, "es_premium": False, "modo": None}

    # Momentum adicional
    if direccion == "long" and cvd_corto > 0 and modo != "reversion":
        score += SCORING_SCALPER_M1['cvd_alineado_m1']
        confluencias.append("cvd_alineado_long")
    elif direccion == "short" and cvd_corto < 0 and modo != "reversion":
        score += SCORING_SCALPER_M1['cvd_alineado_m1']
        confluencias.append("cvd_alineado_short")

    if len(deltas) >= 3:
        if direccion == "long" and deltas[-1] > deltas[-3]:
            score += SCORING_SCALPER_M1['cvd_divergencia_m1']
            confluencias.append("divergencia_cvd_alcista")
        elif direccion == "short" and deltas[-1] < deltas[-3]:
            score += SCORING_SCALPER_M1['cvd_divergencia_m1']
            confluencias.append("divergencia_cvd_bajista")

    if direccion == "long" and imbalance > 0.2:
        score += SCORING_SCALPER_M1['imbalance_favor']
        confluencias.append("imbalance_favorable_long")
    elif direccion == "short" and imbalance < -0.2:
        score += SCORING_SCALPER_M1['imbalance_favor']
        confluencias.append("imbalance_favorable_short")

    # Régimen M5
    if bbw_m5 < 0.025:
        score += SCORING_SCALPER_M1['regimen_favorable']
        confluencias.append("regimen_m5_rango")
    elif bbw_m5 < 0.035:
        score += 5
        confluencias.append("regimen_m5_transicion")
    else:
        if modo == "surf":
            score += 8
            confluencias.append("regimen_m5_tendencia_surf")

    # Penalidad H1 en contra
    if adx_h1 > 40:
        if (direccion == "long" and cvd_largo_h1 < 0) or (direccion == "short" and cvd_largo_h1 > 0):
            score = max(0, score - 15)
            confluencias.append("penalidad_h1_contra")

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
    Eliminado bloqueo ADX > 50 — ahora se opera en tendencia.
    """
    bloqueos = []
    bbw_m1 = indicadores.get("bbw_m1", 0)

    if bbw_m1 > 0.12:
        bloqueos.append("bbw_m1_extremo")

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

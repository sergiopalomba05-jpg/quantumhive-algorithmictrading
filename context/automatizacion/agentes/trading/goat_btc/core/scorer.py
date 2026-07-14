def calcular_score(indicadores: dict, clasificacion: dict) -> dict:
    """Calcula un score de 0-100 para la senal de trading.

    Evalua confluencias tecnicas: CVD alineado, regimen M15, toque de BB,
    divergencia de CVD corto, delta de vela, volumen relativo e
    imbalance de libro. Aplica penalidad si es surfeo.
    """
    score = 0
    confluencias = []

    toco_inf = indicadores.get("toco_bb_inferior_m5", False)
    toco_sup = indicadores.get("toco_bb_superior_m5", False)
    direccion = None
    if toco_inf and not toco_sup:
        direccion = "long"
    elif toco_sup and not toco_inf:
        direccion = "short"
    elif toco_inf and toco_sup:
        bb_sup = indicadores.get("bb_superior_m5", 0)
        bb_inf = indicadores.get("bb_inferior_m5", 0)
        bb_med = indicadores.get("bb_media_m5", 0)
        precio = indicadores.get("precio_actual", bb_med)
        dist_sup = abs(precio - bb_sup) if bb_sup else 999
        dist_inf = abs(precio - bb_inf) if bb_inf else 999
        if dist_sup < dist_inf:
            direccion = "short"
        elif dist_inf < dist_sup:
            direccion = "long"

    precio_toco_sup = indicadores.get("precio_toco_superior", False)
    precio_toco_inf = indicadores.get("precio_toco_inferior", False)
    cvd_largo_h1 = indicadores.get("cvd_largo_H1", 0)
    if (precio_toco_inf and cvd_largo_h1 > 0) or (precio_toco_sup and cvd_largo_h1 < 0):
        score += 20
        confluencias.append("cvd_h1_alineado")

    bbw_m15 = indicadores.get("bbw_m15", 99)
    adx_m15 = indicadores.get("adx_m15", 99)
    if bbw_m15 < 0.025 and adx_m15 < 25:
        score += 20
        confluencias.append("regimen_m15_favorable")

    if toco_sup or toco_inf:
        score += 15
        confluencias.append("toque_bb_m5")

    deltas = indicadores.get("ultimas_5_deltas", [])
    if direccion is not None and len(deltas) >= 3:
        if direccion == "long" and deltas[-1] > deltas[-3]:
            score += 15
            confluencias.append("divergencia_cvd_corto")
        elif direccion == "short" and deltas[-1] < deltas[-3]:
            score += 15
            confluencias.append("divergencia_cvd_corto")

    delta_vela = indicadores.get("delta_ultima_vela", 0)
    if direccion == "long" and delta_vela > 0:
        score += 15
        confluencias.append("delta_confirma_long")
    elif direccion == "short" and delta_vela < 0:
        score += 15
        confluencias.append("delta_confirma_short")

    if indicadores.get("vol_relativo", 0) > 1.3:
        score += 10
        confluencias.append("volumen_elevado")

    imbalance = indicadores.get("imbalance_book", 0)
    if direccion == "long" and imbalance > 0.3:
        score += 5
        confluencias.append("imbalance_favorable")
    elif direccion == "short" and imbalance < -0.3:
        score += 5
        confluencias.append("imbalance_favorable")

    if clasificacion.get("clasificacion") == "surfeo":
        score = max(0, score - 30)

    score = min(100, max(0, score))

    return {
        "score": score,
        "direccion": direccion,
        "confluencias": confluencias,
        "es_alerta": score >= 65,
        "es_premium": score >= 80,
    }

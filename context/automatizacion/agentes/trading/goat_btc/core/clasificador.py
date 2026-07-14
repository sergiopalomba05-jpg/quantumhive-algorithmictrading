def clasificar_toque(indicadores: dict) -> dict:
    """Clasifica si el toque de banda de Bollinger es SURFEO o REBOTE.

    Evalua condiciones de surfeo (tendencia fuerte, velas consecutivas,
    CVD alineado, volumen sostenido) y de rebote (rango, divergencia CVD,
    volumen normal). Retorna clasificacion, confianza y lista de condiciones.
    """
    condiciones_surfeo = []
    condiciones_rebote = []

    if indicadores.get("bbw_m15", 0) > 0.035:
        condiciones_surfeo.append("tendencia_fuerte")
    if indicadores.get("adx_m15", 0) > 25:
        condiciones_surfeo.append("tendencia_fuerte")
    if indicadores.get("velas_tocando_banda", 0) >= 3:
        condiciones_surfeo.append("velas_consecutivas")
    toco_sup = indicadores.get("precio_toco_superior", False)
    toco_inf = indicadores.get("precio_toco_inferior", False)
    cvd_largo = indicadores.get("cvd_largo", 0)
    if (toco_sup and cvd_largo > 0) or (toco_inf and cvd_largo < 0):
        condiciones_surfeo.append("cvd_alineado")
    if indicadores.get("vol_relativo_sostenido", False):
        condiciones_surfeo.append("volumen_sostenido")

    num_surfeo = len(condiciones_surfeo)

    if num_surfeo >= 2:
        confianza = num_surfeo / 5.0
        return {
            "clasificacion": "surfeo",
            "confianza": confianza,
            "condiciones_surfeo": condiciones_surfeo,
            "condiciones_rebote": [],
            "bloquear_senal": True,
        }

    if indicadores.get("bbw_m15", 1) < 0.025:
        condiciones_rebote.append("rango_confirmado")
    if indicadores.get("adx_m15", 100) < 25:
        condiciones_rebote.append("sin_tendencia")
    if indicadores.get("velas_tocando_banda", 99) <= 2:
        condiciones_rebote.append("toque_leve")
    if (toco_sup and cvd_largo < 0) or (toco_inf and cvd_largo > 0):
        condiciones_rebote.append("divergencia_cvd")
    if indicadores.get("vol_relativo", 99) < 1.5:
        condiciones_rebote.append("volumen_normal")

    num_rebote = len(condiciones_rebote)

    if num_rebote >= 3:
        confianza = num_rebote / 5.0
        return {
            "clasificacion": "rebote",
            "confianza": confianza,
            "condiciones_surfeo": condiciones_surfeo,
            "condiciones_rebote": condiciones_rebote,
            "bloquear_senal": False,
        }

    confianza = num_surfeo / 5.0
    return {
        "clasificacion": "surfeo",
        "confianza": confianza,
        "condiciones_surfeo": condiciones_surfeo,
        "condiciones_rebote": condiciones_rebote,
        "bloquear_senal": True,
    }

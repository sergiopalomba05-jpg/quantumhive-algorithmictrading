"""
Anomaly Detector — Evalúa reglas y detecta anomalías en el estado global.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from .estado_global import EstadoGlobal, Alerta

logger = logging.getLogger(__name__)

REGLAS = [
    {
        "nombre": "goat_sin_heartbeat",
        "severidad": "CRITICA",
        "mensaje": "⚠️ goat_btc no responde hace más de 10 minutos",
    },
    {
        "nombre": "drawdown_diario",
        "severidad": "ALTA",
        "mensaje": "🛑 Drawdown diario superó $20 — considerar pausar",
    },
    {
        "nombre": "posicion_abierta_mucho_tiempo",
        "severidad": "MEDIA",
        "mensaje": "⏰ Posición abierta hace más de 4 horas sin resolución",
    },
    {
        "nombre": "render_dormido_con_posicion",
        "severidad": "CRITICA",
        "mensaje": "🚨 AGI dormida con posición abierta en Binance",
    },
    {
        "nombre": "winrate_cayendo",
        "severidad": "ALTA",
        "mensaje": "📉 Winrate de la semana cayó por debajo del 40%",
    },
]


class AnomalyDetector:

    def __init__(self):
        self._anomalias_activas: List[Alerta] = []
        self._cache: set = set()

    def evaluar(self, estado: EstadoGlobal) -> List[Alerta]:
        ahora = datetime.now()
        nuevas: List[Alerta] = []
        nombres_activos = set()

        # Regla 1: goat sin heartbeat
        if estado.goat_btc_ultimo_heartbeat:
            try:
                ultimo_hb = datetime.fromisoformat(estado.goat_btc_ultimo_heartbeat)
                if (ahora - ultimo_hb) > timedelta(minutes=10):
                    nuevas.append(Alerta(
                        nombre="goat_sin_heartbeat", severidad="CRITICA",
                        mensaje=REGLAS[0]["mensaje"], timestamp=ahora.isoformat(),
                    ))
                    nombres_activos.add("goat_sin_heartbeat")
            except Exception:
                pass

        # Regla 2: drawdown diario
        if estado.btc_pnl_hoy < -20:
            nuevas.append(Alerta(
                nombre="drawdown_diario", severidad="ALTA",
                mensaje=REGLAS[1]["mensaje"], timestamp=ahora.isoformat(),
            ))
            nombres_activos.add("drawdown_diario")

        # Regla 3: posición abierta > 4h
        if estado.btc_posicion_activa:
            try:
                ts_entrada = datetime.fromisoformat(estado.btc_posicion_activa.timestamp_entrada)
                if (ahora - ts_entrada) > timedelta(hours=4):
                    nuevas.append(Alerta(
                        nombre="posicion_abierta_mucho_tiempo", severidad="MEDIA",
                        mensaje=REGLAS[2]["mensaje"], timestamp=ahora.isoformat(),
                    ))
                    nombres_activos.add("posicion_abierta_mucho_tiempo")
            except Exception:
                pass

        # Regla 4: render dormido con posición
        if estado.render_dormido and estado.btc_posicion_activa:
            nuevas.append(Alerta(
                nombre="render_dormido_con_posicion", severidad="CRITICA",
                mensaje=REGLAS[3]["mensaje"], timestamp=ahora.isoformat(),
            ))
            nombres_activos.add("render_dormido_con_posicion")

        # Regla 5: winrate bajo
        if 0 < estado.btc_winrate_semana < 0.4:
            nuevas.append(Alerta(
                nombre="winrate_cayendo", severidad="ALTA",
                mensaje=REGLAS[4]["mensaje"], timestamp=ahora.isoformat(),
            ))
            nombres_activos.add("winrate_cayendo")

        # Detectar nuevas anomalías (no cacheadas)
        resultado = []
        for a in nuevas:
            if a.nombre not in self._cache:
                resultado.append(a)
                self._cache.add(a.nombre)
                logger.warning(f"⚠️ Anomalía detectada: {a.nombre} — {a.mensaje}")

        # Limpiar anomalías resueltas del cache
        self._cache = nombres_activos

        return resultado

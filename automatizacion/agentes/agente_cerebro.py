"""
AGENTE CEREBRO — Sistema Nervioso Central de QuantumHive
========================================================
Responsabilidades:
1. Leer eventos del Event Bus en tiempo real
2. Construir y mantener el estado global del sistema
3. Proveer contexto enriquecido a AGI en cada request (HTTP y directo)
4. Detectar anomalías y alertar proactivamente
5. Exponer API interna en puerto 5001

Arquitectura:
  cerebro/estado_global.py   → dataclasses EstadoGlobal, Posicion, Senal, Alerta
  cerebro/event_bus_reader.py → lee eventos del SQLite del Event Bus
  cerebro/context_builder.py  → construye bloque de contexto para AGI
  cerebro/anomaly_detector.py → detecta anomalías por reglas
  cerebro/api_interna.py      → Flask en puerto 5001

Integración:
  agi_telegram.py → requests.get('http://localhost:5001/contexto_agi')
  goat_btc.py     → POST /evento con señal_detectada, orden_ejecutada, posicion_cerrada
"""

import logging
import threading
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Módulos del Cerebro ─────────────────────────────────────────────────────

try:
    from cerebro.estado_global import EstadoGlobal, Posicion, Senal, Alerta, determinar_horario_operativo
    from cerebro.event_bus_reader import EventBusReader
    from cerebro.context_builder import construir_contexto_completo, construir_contexto_minimo
    from cerebro.anomaly_detector import AnomalyDetector
    from cerebro.api_interna import app as cerebro_api, init_api
    CEREBRO_MODULES_OK = True
except ImportError:
    logger.warning("Módulos cerebro/ no disponibles, usando modo legacy")
    CEREBRO_MODULES_OK = False


# ── Constantes ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "agentes" / "agi_memoria_telegram.db"
CEREBRO_PORT = int(os.getenv('CEREBRO_PORT', '5001'))
POLL_INTERVAL = 5  # segundos entre lecturas del Event Bus

# Eventos que AGI DEBE conocer (legacy — mantener compatibilidad)
EVENTOS_CRITICOS = [
    "error_critico", "deploy_fallido", "agente_caido",
    "alerta_drawdown", "senal_trading", "decision_ceo",
    "idea_nueva", "bot_resultado"
]
EVENTOS_CONTEXTO = [
    "heartbeat", "briefing_diario", "reporte_agente",
    "metrica_actualizada", "colmena_update"
]


class AgenteCerebro:
    """
    Sistema Nervioso Central de QuantumHive.
    Mantiene el estado global actualizado y provee contexto a AGI.
    """

    def __init__(self):
        self.db_path = DB_PATH
        self.estado = EstadoGlobal()
        self.event_reader: Optional[EventBusReader] = None
        self.anomaly_detector = AnomalyDetector()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Legacy: tablas SQLite y suscripción al Event Bus
        self._inicializar_tablas()

        if CEREBRO_MODULES_OK:
            self.event_reader = EventBusReader(str(self.db_path))
            init_api(self.estado)
            logger.info(f"🧠 Agente Cerebro v2.0 — Sistema Nervioso Central activo")

    def _inicializar_tablas(self):
        """Legacy: crea tablas SQLite para compatibilidad."""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS contexto_agi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT NOT NULL,
                        resumen TEXT NOT NULL,
                        datos_json TEXT,
                        prioridad TEXT DEFAULT 'normal',
                        leido INTEGER DEFAULT 0,
                        timestamp TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS estado_sistema_agi (
                        clave TEXT PRIMARY KEY,
                        valor TEXT,
                        actualizado TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error inicializando tablas legacy: {e}")

    # ── Loop principal ──────────────────────────────────────────────────────

    def _loop(self):
        """Loop background: lee Event Bus, actualiza estado, detecta anomalías."""
        logger.info("🧠 Cerebro loop iniciado")
        while self._running:
            try:
                if self.event_reader:
                    # 1. Leer nuevos eventos del Event Bus
                    n = self.event_reader.sincronizar(self.estado, max_eventos=50)
                    if n > 0:
                        logger.info(f"🧠 {n} eventos procesados")

                    # 2. Actualizar precio desde Binance
                    try:
                        from .trading.goat_btc.core.binance_executor import get_precio_actual
                        precio = get_precio_actual()
                        if precio:
                            self.estado.btc_precio_actual = precio
                    except Exception:
                        pass

                    # 3. Detectar anomalías
                    nuevas_anomalias = self.anomaly_detector.evaluar(self.estado)
                    for anom in nuevas_anomalias:
                        self.estado.alertas_pendientes.append(anom)
                        self._enviar_alerta_telegram(anom)

                    # 4. Actualizar horario operativo
                    self.estado.sergio_en_horario_operativo = determinar_horario_operativo()

            except Exception as e:
                logger.error(f"Error en loop Cerebro: {e}")

            time.sleep(POLL_INTERVAL)
        logger.info("🧠 Cerebro loop finalizado")

    def start(self):
        """Inicia el loop background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("🧠 Cerebro corriendo en background")

    def stop(self):
        self._running = False

    # ── Alertas a Telegram ──────────────────────────────────────────────────

    def _enviar_alerta_telegram(self, alerta: Alerta):
        """Envía alerta directa a Sergio por Telegram."""
        try:
            import requests
            token = os.getenv('TELEGRAM_TOKEN', '')
            chat_id = os.getenv('USER_TELEGRAM_ID', '')
            if token and chat_id:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                prefijo = "🚨" if alerta.severidad == "CRITICA" else "⚠️"
                texto = f"{prefijo} <b>Cerebro: {alerta.nombre}</b>\n{alerta.mensaje}"
                requests.post(url, json={
                    'chat_id': chat_id, 'text': texto, 'parse_mode': 'HTML',
                }, timeout=5)
        except Exception as e:
            logger.warning(f"Error enviando alerta Telegram: {e}")

    # ── API pública (compatible con agi_telegram.py) ─────────────────────────

    def generar_briefing_para_agi(self) -> str:
        """
        Genera briefing completo del estado actual.
        Usado por agi_telegram.py línea 859.
        """
        if CEREBRO_MODULES_OK and self.event_reader:
            self.event_reader.sincronizar(self.estado, max_eventos=20)
            return construir_contexto_completo(self.estado)

        # Legacy fallback
        return self._generar_briefing_legacy()

    def _generar_briefing_legacy(self) -> str:
        """Fallback legacy con consulta SQLite directa."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            try:
                agentes = conn.execute(
                    "SELECT estado, COUNT(*) FROM agentes GROUP BY estado"
                ).fetchall()
                agentes_str = " | ".join([f"{e}: {c}" for e, c in agentes]) if agentes else "Sin datos"
            except Exception:
                agentes_str = "Sin datos"
            try:
                alertas = conn.execute(
                    "SELECT descripcion FROM alertas WHERE estado='activa' ORDER BY fecha DESC LIMIT 3"
                ).fetchall()
                alertas_str = "\n".join([f"  ⚠️ {a[0]}" for a in alertas]) if alertas else "  ✅ Sin alertas activas"
            except Exception:
                alertas_str = "  Sin datos"
            conn.close()
            return f"""
⚡ BRIEFING QUANTUMHIVE — {datetime.now().strftime('%d/%m/%Y %H:%M')} ARG

📊 AGENTES: {agentes_str}

⚠️ ALERTAS ACTIVAS:
{alertas_str}
"""
        except Exception as e:
            logger.error(f"Error generando briefing legacy: {e}")
            return "⚡ Error generando briefing."

    def obtener_contexto_para_agi(self, limite: int = 20, solo_no_leidos: bool = True) -> str:
        """Legacy: retorna contexto desde SQLite. Mantiene compatibilidad."""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                if solo_no_leidos:
                    rows = conn.execute("""
                        SELECT tipo, resumen, prioridad, timestamp
                        FROM contexto_agi WHERE leido = 0
                        ORDER BY CASE prioridad WHEN 'critica' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
                        timestamp DESC LIMIT ?
                    """, (limite,)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT tipo, resumen, prioridad, timestamp
                        FROM contexto_agi ORDER BY timestamp DESC LIMIT ?
                    """, (limite,)).fetchall()
            if not rows:
                return "📋 Sin novedades recientes."
            contexto = "📋 NOVEDADES DE LA COLMENA:\n"
            for tipo, resumen, prioridad, timestamp in rows:
                contexto += f"• {resumen}\n"
            return contexto
        except Exception as e:
            logger.error(f"Error obteniendo contexto legacy: {e}")
            return "📋 Sin novedades recientes."

    def marcar_leidos(self):
        """Legacy: marca contexto como leído en SQLite."""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE contexto_agi SET leido = 1 WHERE leido = 0")
                conn.commit()
        except Exception as e:
            logger.error(f"Error marcando leídos: {e}")

    def ejecutar(self):
        """Punto de entrada."""
        return self.generar_briefing_para_agi()


# ── Instancia global ─────────────────────────────────────────────────────────

agente_cerebro = AgenteCerebro()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Iniciar cerebro en background
    agente_cerebro.start()

    # Iniciar API Flask en puerto CEREBRO_PORT
    logger.info(f"🧠 Cerebro API en puerto {CEREBRO_PORT}")
    cerebro_api.run(host='0.0.0.0', port=CEREBRO_PORT, debug=False)

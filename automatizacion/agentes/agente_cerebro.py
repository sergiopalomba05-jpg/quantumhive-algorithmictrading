"""
Agente Cerebro — QuantumHive
Puente entre el Event Bus y AGI (CEO I)
Mantiene el contexto de AGI actualizado en tiempo real

Macro 2 — Operaciones Internas
Autor: Arquitecto (Gemini CLI) — Brief Claude CEO II
Fecha: 9 de mayo de 2026
"""

import sqlite3
import logging
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ruta portable al SQLite - Regla 15
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "agentes" / "agi_memoria_telegram.db"

# Eventos que AGI DEBE conocer (alta prioridad)
EVENTOS_CRITICOS = [
    "error_critico",
    "deploy_fallido", 
    "agente_caido",
    "alerta_drawdown",
    "senal_trading",
    "decision_ceo",
    "idea_nueva",
    "bot_resultado"
]

# Eventos de contexto (baja prioridad — solo guardar)
EVENTOS_CONTEXTO = [
    "heartbeat",
    "briefing_diario",
    "reporte_agente",
    "metrica_actualizada",
    "colmena_update"
]


class AgenteCerebro:
    """
    Puente entre el Event Bus y AGI.
    Mantiene el contexto de AGI actualizado con todos los eventos
    de la Colmena en tiempo real.
    """

    def __init__(self):
        self.db_path = DB_PATH
        self._inicializar_tablas()
        self._suscribir_eventos()
        logger.info("🧠 Agente Cerebro inicializado — puente Event Bus → AGI activo")

    def _inicializar_tablas(self):
        """Crea las tablas necesarias si no existen."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Tabla principal de contexto para AGI
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
                # Tabla de estado del sistema para AGI
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS estado_sistema_agi (
                        clave TEXT PRIMARY KEY,
                        valor TEXT,
                        actualizado TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                """)
                conn.commit()
            logger.info("✅ Tablas contexto_agi y estado_sistema_agi verificadas")
        except Exception as e:
            logger.error(f"Error inicializando tablas en {self.db_path}: {e}")

    def _suscribir_eventos(self):
        """Suscribe al Event Bus para recibir todos los eventos."""
        try:
            # Asegurar que el path incluya el directorio de agentes
            agentes_dir = str(Path(__file__).parent)
            if agentes_dir not in sys.path:
                sys.path.insert(0, agentes_dir)
            
            from event_bus import event_bus

            # Suscribir a eventos críticos
            for evento in EVENTOS_CRITICOS:
                event_bus.suscribir(evento, self._procesar_evento_critico)

            # Suscribir a eventos de contexto
            for evento in EVENTOS_CONTEXTO:
                event_bus.suscribir(evento, self._procesar_evento_contexto)

            # Suscribir a todos los eventos como catch-all
            event_bus.suscribir("*", self._registrar_evento_general)

            logger.info(f"✅ Suscrito a {len(EVENTOS_CRITICOS)} eventos críticos y {len(EVENTOS_CONTEXTO)} de contexto")

        except ImportError as e:
            logger.warning(f"Event Bus no disponible aún: {e}")
        except Exception as e:
            logger.error(f"Error suscribiendo al Event Bus: {e}")

    def _procesar_evento_critico(self, evento: dict):
        """Procesa eventos críticos — los guarda con alta prioridad."""
        try:
            tipo = evento.get('tipo', 'desconocido')
            datos = evento.get('payload', {})
            resumen = self._formatear_resumen(tipo, datos, critico=True)
            self._guardar_contexto(
                tipo=tipo,
                resumen=resumen,
                datos=datos,
                prioridad="critica"
            )
            logger.warning(f"🔴 Evento crítico procesado para AGI: {tipo}")
        except Exception as e:
            logger.error(f"Error procesando evento crítico {evento}: {e}")

    def _procesar_evento_contexto(self, evento: dict):
        """Procesa eventos de contexto — los guarda con prioridad normal."""
        try:
            tipo = evento.get('tipo', 'desconocido')
            datos = evento.get('payload', {})
            resumen = self._formatear_resumen(tipo, datos, critico=False)
            self._guardar_contexto(
                tipo=tipo,
                resumen=resumen,
                datos=datos,
                prioridad="normal"
            )
        except Exception as e:
            logger.error(f"Error procesando evento de contexto {evento}: {e}")

    def _registrar_evento_general(self, evento: dict):
        """Catch-all para cualquier evento no clasificado."""
        tipo = evento.get('tipo', 'desconocido')
        if tipo not in EVENTOS_CRITICOS and tipo not in EVENTOS_CONTEXTO:
            try:
                datos = evento.get('payload', {})
                self._guardar_contexto(
                    tipo=tipo,
                    resumen=f"Evento: {tipo}",
                    datos=datos,
                    prioridad="baja"
                )
            except Exception as e:
                logger.error(f"Error registrando evento general {tipo}: {e}")

    def _formatear_resumen(self, evento: str, datos: Dict, critico: bool) -> str:
        """Formatea un resumen legible del evento para AGI."""
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        prefijo = "🔴" if critico else "📋"

        # Formateos específicos por tipo de evento
        if evento == "error_critico":
            return f"{prefijo} [{timestamp}] Error crítico: {datos.get('mensaje', 'Sin detalle')} en {datos.get('agente', 'desconocido')}"
        elif evento == "deploy_fallido":
            return f"{prefijo} [{timestamp}] Deploy fallido: {datos.get('motivo', 'Sin detalle')}"
        elif evento == "alerta_drawdown":
            return f"{prefijo} [{timestamp}] ALERTA DRAWDOWN: {datos.get('porcentaje', '?')}% en cuenta {datos.get('cuenta', '?')}"
        elif evento == "senal_trading":
            return f"📊 [{timestamp}] Señal {datos.get('direccion', '?')} en {datos.get('par', '?')} — Score: {datos.get('score', '?')}"
        elif evento == "decision_ceo":
            return f"👑 [{timestamp}] Decisión CEO: {datos.get('titulo', 'Sin título')}"
        elif evento == "idea_nueva":
            return f"💡 [{timestamp}] Nueva idea: {datos.get('nombre', 'Sin nombre')} — Score: {datos.get('score', '?')}/100"
        elif evento == "heartbeat":
            agentes_activos = datos.get('agentes_activos', '?')
            return f"💓 [{timestamp}] Heartbeat — {agentes_activos} agentes activos"
        else:
            # Resumen genérico
            datos_str = str(datos)[:100] if datos else "Sin datos"
            return f"{prefijo} [{timestamp}] {evento}: {datos_str}"

    def _guardar_contexto(self, tipo: str, resumen: str, datos: Dict, prioridad: str):
        """Guarda el contexto en SQLite para que AGI lo lea."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO contexto_agi (tipo, resumen, datos_json, prioridad)
                    VALUES (?, ?, ?, ?)
                """, (tipo, resumen, json.dumps(datos, default=str), prioridad))
                conn.commit()
        except Exception as e:
            logger.error(f"Error guardando contexto: {e}")

    def obtener_contexto_para_agi(self, limite: int = 20, solo_no_leidos: bool = True) -> str:
        """
        Retorna el contexto reciente formateado para inyectar en AGI.
        Este método es llamado por agi_telegram.py al inicio de cada sesión.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if solo_no_leidos:
                    rows = conn.execute("""
                        SELECT tipo, resumen, prioridad, timestamp
                        FROM contexto_agi
                        WHERE leido = 0
                        ORDER BY 
                            CASE prioridad 
                                WHEN 'critica' THEN 1 
                                WHEN 'normal' THEN 2 
                                ELSE 3 
                            END,
                            timestamp DESC
                        LIMIT ?
                    """, (limite,)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT tipo, resumen, prioridad, timestamp
                        FROM contexto_agi
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limite,)).fetchall()

            if not rows:
                return "📋 Sin novedades recientes de la Colmena."

            contexto = "📋 NOVEDADES DE LA COLMENA:\n"
            for tipo, resumen, prioridad, timestamp in rows:
                contexto += f"• {resumen}\n"

            return contexto
        except Exception as e:
            logger.error(f"Error obteniendo contexto: {e}")
            return "📋 Error obteniendo novedades de la Colmena."

    def marcar_leidos(self):
        """Marca todos los contextos no leídos como leídos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE contexto_agi SET leido = 1 WHERE leido = 0")
                conn.commit()
        except Exception as e:
            logger.error(f"Error marcando como leídos: {e}")

    def actualizar_estado_sistema(self, clave: str, valor: str):
        """Actualiza el estado del sistema para que AGI lo consulte."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO estado_sistema_agi (clave, valor, actualizado)
                    VALUES (?, ?, datetime('now', 'localtime'))
                """, (clave, valor))
                conn.commit()
        except Exception as e:
            logger.error(f"Error actualizando estado del sistema: {e}")

    def generar_briefing_para_agi(self) -> str:
        """
        Genera un briefing completo del estado actual de QuantumHive
        para inyectar en AGI al inicio de cada conversación.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Contar agentes por estado
                try:
                    agentes = conn.execute("""
                        SELECT estado, COUNT(*) 
                        FROM agentes 
                        GROUP BY estado
                    """).fetchall()
                    agentes_str = " | ".join([f"{e}: {c}" for e, c in agentes]) if agentes else "Sin datos"
                except:
                    agentes_str = "Sin datos"

                # Últimas alertas no resueltas
                try:
                    alertas = conn.execute("""
                        SELECT descripcion FROM alertas 
                        WHERE estado = 'activa' 
                        ORDER BY fecha DESC LIMIT 3
                    """).fetchall()
                    alertas_str = "\n".join([f"  ⚠️ {a[0]}" for a in alertas]) if alertas else "  ✅ Sin alertas activas"
                except:
                    alertas_str = "  Sin datos"

                # Últimas decisiones
                try:
                    decisiones = conn.execute("""
                        SELECT descripcion FROM decisiones 
                        ORDER BY fecha DESC LIMIT 3
                    """).fetchall()
                    decisiones_str = "\n".join([f"  • {d[0]}" for d in decisiones]) if decisiones else "  Sin decisiones recientes"
                except:
                    decisiones_str = "  Sin datos"

                # Novedades del Event Bus
                novedades = self.obtener_contexto_para_agi(limite=10)

            briefing = f"""
⚡ BRIEFING QUANTUMHIVE — {datetime.now().strftime('%d/%m/%Y %H:%M')} ARG

📊 AGENTES: {agentes_str}

⚠️ ALERTAS ACTIVAS:
{alertas_str}

👑 ÚLTIMAS DECISIONES:
{decisiones_str}

{novedades}
"""
            return briefing.strip()
        except Exception as e:
            logger.error(f"Error generando briefing: {e}")
            return "⚡ Error generando briefing QuantumHive."

    def ejecutar(self):
        """Punto de entrada para ejecución directa."""
        briefing = self.generar_briefing_para_agi()
        # En producción esto podría guardarse o enviarse
        return briefing


# Instancia global para importar desde otros módulos
agente_cerebro = AgenteCerebro()


if __name__ == "__main__":
    cerebro = AgenteCerebro()
    print(cerebro.generar_briefing_para_agi())

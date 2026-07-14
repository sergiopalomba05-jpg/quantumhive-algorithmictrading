"""
Agente Grafana Reporter — QuantumHive
Actualiza métricas en SQLite para visualización en Grafana
Macro 12 — Infraestructura y Plataforma

Autor: Arquitecto (Trae) — Brief Claude CEO II
Fecha: 9 de mayo de 2026
"""

import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "agi_memoria_telegram.db"

class AgenteGrafanaReporter:
    """Actualiza métricas de la Colmena para visualización en Grafana."""

    def __init__(self):
        self.db_path = DB_PATH
        self._inicializar_tablas()

    def _inicializar_tablas(self):
        """Crea tablas de métricas si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metricas_grafana (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    valor REAL,
                    categoria TEXT,
                    timestamp TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def reportar_estado_colmena(self):
        """Genera reporte del estado actual de todos los agentes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total por estado
                estados = conn.execute("""
                    SELECT estado, COUNT(*) as total
                    FROM agentes GROUP BY estado
                """).fetchall()
                
                for estado, total in estados:
                    conn.execute("""
                        INSERT INTO metricas_grafana (nombre, valor, categoria)
                        VALUES (?, ?, 'agentes')
                    """, (f"agentes_{estado}", total, ))
                
                # Total por macrodivision
                macros = conn.execute("""
                    SELECT macrodivision, COUNT(*) as total
                    FROM agentes GROUP BY macrodivision
                """).fetchall()
                
                for macro, total in macros:
                    conn.execute("""
                        INSERT INTO metricas_grafana (nombre, valor, categoria)
                        VALUES (?, ?, 'macrodivision')
                    """, (f"macro_{macro}_agentes", total))
                
                conn.commit()
                logger.info("✅ Métricas Grafana actualizadas")
                return True
                
        except Exception as e:
            logger.error(f"Error reportando métricas: {e}")
            return False

    def ejecutar(self):
        """Punto de entrada principal."""
        return self.reportar_estado_colmena()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agente = AgenteGrafanaReporter()
    agente.ejecutar()
"""
GOAT BTC — SeñalesDB
Almacenamiento SQLite de señales de trading para el agente GOAT BTC.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class SeñalesDB:

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "goat_señales.db"
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._crear_tabla()

    def _crear_tabla(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goat_señales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    direccion TEXT,
                    score INTEGER,
                    precio_entrada REAL,
                    bb_superior REAL,
                    bb_media REAL,
                    bb_inferior REAL,
                    cvd_corto REAL,
                    cvd_largo REAL,
                    adx REAL,
                    bbw REAL,
                    clasificacion TEXT,
                    confluencias TEXT,
                    resultado TEXT NULL,
                    comentario_trader TEXT NULL,
                    score_real_posterior REAL NULL
                )
            """)
            conn.commit()
        logger.info("Tabla goat_señales lista")

    def guardar_senal(self, senal: dict) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO goat_señales
                   (timestamp, direccion, score, precio_entrada,
                    bb_superior, bb_media, bb_inferior,
                    cvd_corto, cvd_largo, adx, bbw,
                    clasificacion, confluencias)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    senal.get("timestamp", datetime.now().isoformat()),
                    senal.get("direccion"),
                    senal.get("score"),
                    senal.get("precio_entrada"),
                    senal.get("bb_superior"),
                    senal.get("bb_media"),
                    senal.get("bb_inferior"),
                    senal.get("cvd_corto"),
                    senal.get("cvd_largo"),
                    senal.get("adx"),
                    senal.get("bbw"),
                    senal.get("clasificacion"),
                    json.dumps(senal.get("confluencias", [])),
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.info(f"Señal guardada ID {row_id}")
            return row_id

    def actualizar_resultado(self, senal_id: int, resultado: str, comentario: str = "", score_real: float = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE goat_señales
                   SET resultado = ?, comentario_trader = ?, score_real_posterior = ?
                   WHERE id = ?""",
                (resultado, comentario, score_real, senal_id),
            )
            conn.commit()
            logger.info(f"Resultado actualizado ID {senal_id}: {resultado}")

    def obtener_ultimas(self, limite: int = 10) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM goat_señales ORDER BY id DESC LIMIT ?", (limite,)
            ).fetchall()
            result = []
            for row in rows:
                d = dict(row)
                if d.get("confluencias"):
                    try:
                        d["confluencias"] = json.loads(d["confluencias"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                result.append(d)
            return result

    def obtener_estadisticas(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM goat_señales").fetchone()[0]
            ganadoras = conn.execute(
                "SELECT COUNT(*) FROM goat_señales WHERE resultado = 'ganadora'"
            ).fetchone()[0]
            perdedoras = conn.execute(
                "SELECT COUNT(*) FROM goat_señales WHERE resultado = 'perdedora'"
            ).fetchone()[0]
            no_ejecutadas = conn.execute(
                "SELECT COUNT(*) FROM goat_señales WHERE resultado = 'no_ejecutada'"
            ).fetchone()[0]
            score_promedio = conn.execute(
                "SELECT AVG(score) FROM goat_señales"
            ).fetchone()[0] or 0.0
        ejecutadas = ganadoras + perdedoras
        tasa_acierto = round(ganadoras / ejecutadas, 4) if ejecutadas > 0 else 0.0
        return {
            "total_senales": total,
            "ganadoras": ganadoras,
            "perdedoras": perdedoras,
            "no_ejecutadas": no_ejecutadas,
            "tasa_acierto": tasa_acierto,
            "score_promedio": round(score_promedio, 2),
        }

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
                    score_real_posterior REAL NULL,
                    sl REAL NULL,
                    tp REAL NULL,
                    precio_cierre REAL NULL,
                    pnl_real REAL NULL,
                    pnl_usdt REAL NULL,
                    duracion_minutos INTEGER NULL
                )
            """)
            conn.commit()
            # Migración: agregar columnas si no existen (para bases existentes)
            try:
                conn.execute("ALTER TABLE goat_señales ADD COLUMN sl REAL NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE goat_señales ADD COLUMN tp REAL NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE goat_señales ADD COLUMN precio_cierre REAL NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE goat_señales ADD COLUMN pnl_real REAL NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE goat_señales ADD COLUMN pnl_usdt REAL NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE goat_señales ADD COLUMN duracion_minutos INTEGER NULL")
            except Exception:
                pass
            conn.commit()
        logger.info("Tabla goat_señales lista")

    def guardar_senal_con_sl_tp(self, senal: dict) -> int:
        """Guarda señal con SL, TP y datos de ejecución autónoma."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO goat_señales
                   (timestamp, direccion, score, precio_entrada,
                    bb_superior, bb_media, bb_inferior,
                    cvd_corto, cvd_largo, adx, bbw,
                    clasificacion, confluencias, resultado,
                    sl, tp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    "ejecutada",
                    senal.get("sl"),
                    senal.get("tp"),
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.info(f"Señal autónoma guardada ID {row_id}")
            return row_id

    def actualizar_cierre(self, senal_id: int, precio_cierre: float, pnl_usdt: float,
                          duracion_minutos: int, resultado: str = "ganadora"):
        """Actualiza datos de cierre de una señal."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE goat_señales
                   SET precio_cierre = ?, pnl_usdt = ?,
                       duracion_minutos = ?, resultado = ?
                   WHERE id = ?""",
                (precio_cierre, pnl_usdt, duracion_minutos, resultado, senal_id),
            )
            conn.commit()
            logger.info(f"Cierre actualizado ID {senal_id}: {resultado} PnL=${pnl_usdt:.2f}")

    def obtener_ejecutadas_activas(self) -> list[dict]:
        """Obtiene señales ejecutadas que aún no tienen cierre."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM goat_señales WHERE resultado = 'ejecutada' AND precio_cierre IS NULL ORDER BY id DESC"
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

    def actualizar_resultado_agi(self, senal_id: int, resultado: str, comentario: str = ""):
        """Actualiza resultado desde confirmación AGI Telegram."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE goat_señales
                   SET resultado = ?, comentario_trader = ?
                   WHERE id = ?""",
                (resultado, comentario, senal_id),
            )
            conn.commit()
            logger.info(f"Resultado AGI ID {senal_id}: {resultado}")

    def obtener_pendiente_agi(self, senal_id: int) -> Optional[dict]:
        """Obtiene una señal pendiente de confirmación AGI."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM goat_señales WHERE id = ?", (senal_id,)
            ).fetchone()
            if row is None:
                return None
            d = dict(row)
            if d.get("confluencias"):
                try:
                    d["confluencias"] = json.loads(d["confluencias"])
                except (json.JSONDecodeError, TypeError):
                    pass
            return d

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

"""
GOAT BTC — SessionSummary
Resumen diario de sesión de trading con persistencia en GitHub Memory y JSON local.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionSummary:

    def __init__(self):
        self.github_memory = None
        try:
            from automatizacion.agentes.agi_memory.github_memory import github_memory
            self.github_memory = github_memory
        except (ImportError, AttributeError):
            logger.warning("GitHub Memory no disponible, solo respaldo local")

    def guardar_resumen(self, metricas: dict) -> bool:
        fecha = metricas.get("fecha", "desconocida")
        summary_text = (
            f"=== SESIÓN GOAT BTC {fecha} ===\n"
            f"Señales totales: {metricas.get('total_senales', 0)}\n"
            f"Alertadas: {metricas.get('senales_alertadas', 0)}\n"
            f"Confirmadas: {metricas.get('senales_confirmadas', 0)}\n"
            f"Ganadoras: {metricas.get('ganadoras', 0)}\n"
            f"Perdedoras: {metricas.get('perdedoras', 0)}\n"
            f"Score promedio: {metricas.get('score_promedio', 0)}\n"
            f"Mejor score: {metricas.get('mejor_score', 0)}\n"
            f"Apertura: {metricas.get('precio_apertura', 'N/A')}\n"
            f"Cierre: {metricas.get('precio_cierre', 'N/A')}\n"
            f"Cambio %: {metricas.get('cambio_pct', 0)}%\n"
        )
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        local_path = data_dir / f"sesion_{fecha}.json"
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(metricas, f, ensure_ascii=False, indent=2)
        if self.github_memory is None:
            return False
        try:
            self.github_memory.actualizar_contexto("goat_btc_sesion", summary_text)
            logger.info(f"Resumen de sesión {fecha} guardado en GitHub Memory")
            return True
        except Exception as e:
            logger.error(f"Error guardando resumen en GitHub: {e}")
            return False

    def obtener_ultimo_resumen(self) -> str:
        if self.github_memory is not None:
            try:
                resultado = self.github_memory.leer_contexto("goat_btc_sesion")
                if resultado:
                    return resultado
            except Exception as e:
                logger.error(f"Error leyendo contexto GitHub: {e}")
        data_dir = Path(__file__).parent.parent / "data"
        if not data_dir.exists():
            return "No hay resumen disponible"
        archivos = sorted(data_dir.glob("sesion_*.json"), reverse=True)
        if not archivos:
            return "No hay resumen disponible"
        try:
            with open(archivos[0], "r", encoding="utf-8") as f:
                metricas = json.load(f)
            fecha = metricas.get("fecha", archivos[0].stem.replace("sesion_", ""))
            lines = [
                f"=== SESIÓN GOAT BTC {fecha} ===",
                f"Señales totales: {metricas.get('total_senales', 0)}",
                f"Alertadas: {metricas.get('senales_alertadas', 0)}",
                f"Confirmadas: {metricas.get('senales_confirmadas', 0)}",
                f"Ganadoras: {metricas.get('ganadoras', 0)}",
                f"Perdedoras: {metricas.get('perdedoras', 0)}",
                f"Score promedio: {metricas.get('score_promedio', 0)}",
                f"Mejor score: {metricas.get('mejor_score', 0)}",
                f"Apertura: {metricas.get('precio_apertura', 'N/A')}",
                f"Cierre: {metricas.get('precio_cierre', 'N/A')}",
                f"Cambio %: {metricas.get('cambio_pct', 0)}%",
            ]
            return "\n".join(lines)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error leyendo resumen local: {e}")
            return "No hay resumen disponible"

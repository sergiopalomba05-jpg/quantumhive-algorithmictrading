"""
AGI Autonomous — AGI UPGRADE v2.0
Sistema autónomo principal que coordina todos los módulos.
"""

import logging
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class AGIAutonomous:
    """Sistema autónomo principal de AGI."""
    
    def __init__(self):
        self.active = True
        logger.info("AGIAutonomous inicializado")
    
    def start(self):
        """Inicia el sistema autónomo."""
        logger.info("AGI Autonomous iniciado")
        self.active = True
    
    def stop(self):
        """Detiene el sistema autónomo."""
        logger.info("AGI Autonomous detenido")
        self.active = False
    
    def get_status(self) -> Dict:
        """Obtiene el estado del sistema autónomo con métricas reales."""
        agentes_dir = Path(__file__).resolve().parents[1] / "agentes"
        agentes_reales = len([p for p in agentes_dir.glob("*.py") if p.is_file() and p.name != "__init__.py"])
        return {
            "active": self.active,
            "status": "running" if self.active else "stopped",
            "agentes_creados_reales": agentes_reales,
        }

    def obtener_estado(self) -> Dict:
        """Alias para compatibilidad con llamadas legacy."""
        return self.get_status()
    
    def process_autonomous_action(self, action: Dict) -> Dict:
        """Procesa una acción autónoma."""
        try:
            return {
                "status": "processed",
                "action": action.get("type", "unknown")
            }
        except Exception as e:
            logger.error(f"Error en process_autonomous_action: {e}")
            return {"status": "failed", "error": str(e)}

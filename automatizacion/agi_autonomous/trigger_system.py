"""
Trigger System — AGI UPGRADE v2.0
Sistema de triggers para acciones automáticas.
"""

import logging
from typing import Dict, List, Callable

logger = logging.getLogger(__name__)


class TriggerSystem:
    """Sistema de triggers."""
    
    def __init__(self):
        self.triggers = []
        logger.info("TriggerSystem inicializado")
    
    def register_trigger(self, condition: Callable, action: Callable):
        """Registra un trigger."""
        self.triggers.append({
            "condition": condition,
            "action": action
        })
    
    def check_triggers(self, context: Dict) -> List[Dict]:
        """Verifica todos los triggers y ejecuta los que cumplan la condición."""
        results = []
        for trigger in self.triggers:
            try:
                if trigger["condition"](context):
                    result = trigger["action"](context)
                    results.append(result)
            except Exception as e:
                logger.error(f"Error verificando trigger: {e}")
        return results

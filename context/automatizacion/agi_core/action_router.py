"""
Action Router — AGI UPGRADE v2.0
Enruta acciones a los agentes correspondientes.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ActionRouter:
    """Router de acciones para agentes."""
    
    def __init__(self):
        self.routes = {}
        logger.info("ActionRouter inicializado")
    
    def register_route(self, action_type: str, handler):
        """Registra un route para un tipo de acción."""
        self.routes[action_type] = handler
    
    def route_action(self, action: Dict) -> Optional[str]:
        """Enruta una acción al handler correspondiente."""
        try:
            action_type = action.get("type", "general")
            handler = self.routes.get(action_type)
            if handler:
                return handler(action)
            return None
        except Exception as e:
            logger.error(f"Error en route_action: {e}")
            return None

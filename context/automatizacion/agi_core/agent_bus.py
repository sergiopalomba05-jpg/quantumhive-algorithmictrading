"""
Agent Bus — AGI UPGRADE v2.0
Bus de comunicación entre agentes.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class AgentBus:
    """Bus de comunicación entre agentes."""
    
    def __init__(self):
        self.subscribers = {}
        logger.info("AgentBus inicializado")
    
    def subscribe(self, agent_name: str, callback):
        """Suscribe un agente al bus."""
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
        self.subscribers[agent_name].append(callback)
    
    def publish(self, message: Dict):
        """Publica un mensaje a todos los suscriptores."""
        for agent_name, callbacks in self.subscribers.items():
            for callback in callbacks:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error en callback de {agent_name}: {e}")
    
    def send_to_agent(self, agent_name: str, message: Dict):
        """Envía un mensaje a un agente específico."""
        callbacks = self.subscribers.get(agent_name, [])
        for callback in callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error en callback de {agent_name}: {e}")

"""
Heartbeat Monitor — AGI UPGRADE v2.0
Monitorea el heartbeat de los agentes.
"""

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """Monitor de heartbeat para agentes."""
    
    def __init__(self):
        self.heartbeats = {}
        logger.info("HeartbeatMonitor inicializado")
    
    def register_agent(self, agent_name: str):
        """Registra un agente para monitoreo."""
        self.heartbeats[agent_name] = time.time()
    
    def update_heartbeat(self, agent_name: str):
        """Actualiza el heartbeat de un agente."""
        self.heartbeats[agent_name] = time.time()
    
    def check_heartbeats(self, timeout: int = 60) -> Dict[str, bool]:
        """Verifica los heartbeats de todos los agentes."""
        status = {}
        current_time = time.time()
        for agent_name, last_heartbeat in self.heartbeats.items():
            status[agent_name] = (current_time - last_heartbeat) < timeout
        return status

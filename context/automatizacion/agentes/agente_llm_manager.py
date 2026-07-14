#!/usr/bin/env python3
"""
Agente LLM Manager - Gestiona automáticamente el cambio de motores LLM
Cuando un motor se queda sin tokens, cambia automáticamente al siguiente disponible.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Motores LLM disponibles en orden de preferencia
LLM_ENGINES = ['openrouter', 'groq', 'anthropic', 'ollama']

@dataclass
class EngineStatus:
    """Estado de un motor LLM."""
    name: str
    active: bool = False
    rate_limited: bool = False
    rate_limit_until: Optional[str] = None
    last_error: Optional[str] = None
    last_success: Optional[str] = None
    error_count: int = 0

class AgenteLLMManager:
    """Agente para gestionar automáticamente el cambio de motores LLM."""
    
    def __init__(self, db_path: str = "automatizacion/data/llm_manager.db"):
        self.db_path = db_path
        self.current_engine = os.getenv('LLM_ENGINE', 'openrouter').lower()
        self.engine_status: Dict[str, EngineStatus] = {}
        
        # Inicializar base de datos
        self._init_db()
        
        # Cargar estado de motores
        self._load_engine_status()
        
        logger.info(f"AgenteLLMManager inicializado - Motor actual: {self.current_engine}")
    
    def _init_db(self):
        """Inicializa la base de datos SQLite."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engine_status (
                name TEXT PRIMARY KEY,
                active BOOLEAN,
                rate_limited BOOLEAN,
                rate_limit_until TEXT,
                last_error TEXT,
                last_success TEXT,
                error_count INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_engine_status(self):
        """Carga el estado de los motores desde la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM engine_status')
        rows = cursor.fetchall()
        
        for row in rows:
            name, active, rate_limited, rate_limit_until, last_error, last_success, error_count = row
            self.engine_status[name] = EngineStatus(
                name=name,
                active=bool(active),
                rate_limited=bool(rate_limited),
                rate_limit_until=rate_limit_until,
                last_error=last_error,
                last_success=last_success,
                error_count=error_count
            )
        
        conn.close()
        
        # Inicializar motores que no están en la base de datos
        for engine in LLM_ENGINES:
            if engine not in self.engine_status:
                self.engine_status[engine] = EngineStatus(name=engine, active=(engine == self.current_engine))
    
    def _save_engine_status(self, engine: str):
        """Guarda el estado de un motor en la base de datos."""
        status = self.engine_status[engine]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO engine_status 
            (name, active, rate_limited, rate_limit_until, last_error, last_success, error_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            status.name,
            status.active,
            status.rate_limited,
            status.rate_limit_until,
            status.last_error,
            status.last_success,
            status.error_count
        ))
        
        conn.commit()
        conn.close()
    
    def report_success(self, engine: str):
        """Reporta un éxito en un motor LLM."""
        if engine not in self.engine_status:
            self.engine_status[engine] = EngineStatus(name=engine)
        
        self.engine_status[engine].last_success = datetime.now().isoformat()
        self.engine_status[engine].error_count = 0
        self.engine_status[engine].rate_limited = False
        self.engine_status[engine].rate_limit_until = None
        self.engine_status[engine].last_error = None
        
        self._save_engine_status(engine)
        logger.info(f"Motor {engine} reportó éxito - error_count reseteado a 0")
    
    def report_error(self, engine: str, error: str, is_rate_limit: bool = False):
        """Reporta un error en un motor LLM."""
        if engine not in self.engine_status:
            self.engine_status[engine] = EngineStatus(name=engine)
        
        self.engine_status[engine].last_error = error
        self.engine_status[engine].error_count += 1
        
        if is_rate_limit:
            self.engine_status[engine].rate_limited = True
            # Estimar tiempo de recuperación (1 hora para Groq, ajustable)
            self.engine_status[engine].rate_limit_until = datetime.now().isoformat()
            logger.warning(f"Motor {engine} tiene rate limit - marcado como no disponible")
        
        self._save_engine_status(engine)
        logger.error(f"Motor {engine} reportó error: {error} - error_count: {self.engine_status[engine].error_count}")
    
    def get_available_engines(self) -> List[str]:
        """Retorna la lista de motores disponibles (no rate limited)."""
        available = []
        now = datetime.now()
        
        for engine in LLM_ENGINES:
            status = self.engine_status.get(engine)
            if status and not status.rate_limited:
                available.append(engine)
            elif status and status.rate_limited and status.rate_limit_until:
                # Verificar si el rate limit expiró
                limit_time = datetime.fromisoformat(status.rate_limit_until)
                if now > limit_time:
                    status.rate_limited = False
                    status.rate_limit_until = None
                    self._save_engine_status(engine)
                    available.append(engine)
        
        return available
    
    def switch_engine(self, new_engine: str) -> bool:
        """Cambia al motor especificado."""
        if new_engine not in LLM_ENGINES:
            logger.error(f"Motor {new_engine} no está en la lista de motores disponibles")
            return False
        
        # Desactivar motor actual
        if self.current_engine in self.engine_status:
            self.engine_status[self.current_engine].active = False
            self._save_engine_status(self.current_engine)
        
        # Activar nuevo motor
        self.current_engine = new_engine
        if new_engine not in self.engine_status:
            self.engine_status[new_engine] = EngineStatus(name=new_engine)
        
        self.engine_status[new_engine].active = True
        self._save_engine_status(new_engine)
        
        # Actualizar variable de entorno
        os.environ['LLM_ENGINE'] = new_engine
        
        logger.info(f"Motor cambiado a {new_engine}")
        return True
    
    def auto_switch_on_rate_limit(self, current_engine: str) -> Optional[str]:
        """Cambia automáticamente al siguiente motor disponible si hay rate limit."""
        if current_engine not in self.engine_status:
            return None
        
        status = self.engine_status[current_engine]
        
        # Solo cambiar si hay rate limit y hay errores consecutivos
        if not status.rate_limited and status.error_count < 3:
            return None
        
        # Obtener motores disponibles
        available = self.get_available_engines()
        
        # Filtrar el motor actual
        available = [e for e in available if e != current_engine]
        
        if not available:
            logger.error("No hay motores disponibles para cambiar")
            return None
        
        # Cambiar al siguiente motor disponible
        next_engine = available[0]
        if self.switch_engine(next_engine):
            return next_engine
        
        return None
    
    def get_current_engine(self) -> str:
        """Retorna el motor actual."""
        return self.current_engine
    
    def get_status_report(self) -> Dict:
        """Retorna un reporte del estado de todos los motores."""
        report = {
            'current_engine': self.current_engine,
            'engines': {}
        }
        
        for engine in LLM_ENGINES:
            if engine in self.engine_status:
                report['engines'][engine] = asdict(self.engine_status[engine])
        
        return report

# Instancia global del agente
llm_manager = AgenteLLMManager()

# Funciones de conveniencia para uso en otros módulos
def report_llm_success(engine: str):
    """Reporta un éxito en un motor LLM."""
    llm_manager.report_success(engine)

def report_llm_error(engine: str, error: str, is_rate_limit: bool = False):
    """Reporta un error en un motor LLM."""
    llm_manager.report_error(engine, error, is_rate_limit)
    # Intentar cambiar automáticamente si es rate limit
    if is_rate_limit:
        new_engine = llm_manager.auto_switch_on_rate_limit(engine)
        if new_engine:
            logger.info(f"Motor cambiado automáticamente de {engine} a {new_engine} por rate limit")

def get_current_llm_engine() -> str:
    """Retorna el motor LLM actual."""
    return llm_manager.get_current_engine()

def get_llm_status_report() -> Dict:
    """Retorna el reporte de estado de los motores LLM."""
    return llm_manager.get_status_report()

if __name__ == "__main__":
    # Test del agente
    print("Agente LLM Manager - Test")
    print(f"Motor actual: {llm_manager.get_current_engine()}")
    print(f"Estado: {json.dumps(llm_manager.get_status_report(), indent=2)}")
    
    # Simular rate limit
    print("\nSimulando rate limit en openrouter...")
    report_llm_error("openrouter", "Rate limit exceeded", is_rate_limit=True)
    
    print(f"Motor actual después de rate limit: {llm_manager.get_current_engine()}")
    print(f"Estado: {json.dumps(llm_manager.get_status_report(), indent=2)}")

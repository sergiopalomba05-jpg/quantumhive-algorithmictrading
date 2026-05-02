"""
Punto de entrada principal del sistema autónomo de QuantumHive.
Este proceso corre 24/7 en Render y activa todo el sistema.
"""

import sys
import os
import logging
import threading
from pathlib import Path

# Añadir directorios al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'nucleo'))
sys.path.insert(0, str(Path(__file__).parent))

from event_bus import EventBus
from eventos_quantumhive import Eventos

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'agi_memoria_telegram.db')


def registrar_suscriptores_core():
    """
    Registra los handlers de los agentes core en el Event Bus.
    Estos son los agentes implementados en DÍA 4.
    """
    bus = EventBus(DB_PATH)

    # AGENTE 1: Optimizador de Errores y Procesos
    try:
        from automatizacion.agentes.agente_optimizador_procesos import AgenteOptimizadorProcesos
        opt_procesos = AgenteOptimizadorProcesos(db_path=DB_PATH, event_bus=bus)

        def manejar_error_critico(evento):
            """Handler para error_critico."""
            payload = evento['payload']
            opt_procesos.registrar_error(
                proceso=payload.get('proceso', 'desconocido'),
                tipo_error=payload.get('tipo_error', 'critico'),
                descripcion=payload.get('descripcion'),
                agente=payload.get('agente'),
                causa_raiz=payload.get('causa_raiz'),
                impacto=payload.get('impacto'),
                tags=payload.get('tags')
            )

        def manejar_deploy_fallido(evento):
            """Handler para deploy_fallido."""
            payload = evento['payload']
            opt_procesos.registrar_error_deploy(
                error_log=payload.get('error_log'),
                modelo_ia=payload.get('modelo_ia'),
                variable_faltante=payload.get('variable_faltante')
            )

        def manejar_agente_problema(evento):
            """Handler para agente_problema."""
            payload = evento['payload']
            opt_procesos.registrar_error(
                proceso=payload.get('proceso', 'agente'),
                tipo_error=payload.get('tipo_error', 'agente_fallo'),
                descripcion=payload.get('descripcion'),
                agente=payload.get('agente'),
                causa_raiz=payload.get('causa_raiz'),
                impacto=payload.get('impacto'),
                tags=payload.get('tags')
            )

        bus.suscribir('error_critico', manejar_error_critico)
        bus.suscribir('deploy_fallido', manejar_deploy_fallido)
        bus.suscribir('agente_problema', manejar_agente_problema)
        logger.info("✅ Agente Optimizador Procesos suscrito al Event Bus")

    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Optimizador Procesos: {e}")

    # AGENTE 2: Optimizador de Agentes (no requiere suscripciones, solo publica eventos)
    logger.info("ℹ️  Agente Optimizador Agentes no requiere suscripciones (solo publica)")

    # AGENTE 3: Recolector Inteligente (no requiere suscripciones, solo publica eventos)
    logger.info("ℹ️  Agente Recolector Inteligente no requiere suscripciones (solo publica)")

    return bus


def iniciar_scheduler():
    """Inicia el scheduler de tareas periódicas en hilo separado."""
    import threading
    logger.info("Scheduler: iniciando en hilo background...")
    
    # Nota: El scheduler ya existe en automatizacion/scheduler.py
    # Este función es un placeholder para integración futura
    # Por ahora, los agentes tienen sus propias funciones para scheduler
    
    return True


if __name__ == "__main__":
    logger.info("=== QuantumHive Sistema Autónomo — Iniciando ===")
    
    # 1. Registrar todos los suscriptores
    logger.info("Registrando suscriptores en Event Bus...")
    bus = registrar_suscriptores_core()
    
    # 2. Iniciar scheduler en hilo separado
    hilo_scheduler = threading.Thread(target=iniciar_scheduler, daemon=True)
    hilo_scheduler.start()
    
    # 3. Correr el Event Bus (blocking — corre para siempre)
    logger.info("Sistema autónomo activo — esperando eventos")
    logger.info("Event Bus iniciado — polling cada 5 segundos")
    
    try:
        bus.iniciar()
    except KeyboardInterrupt:
        logger.info("Sistema autónomo detenido por usuario")
        bus.detener()

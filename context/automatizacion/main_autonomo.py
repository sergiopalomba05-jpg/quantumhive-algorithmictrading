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

    # AGENTE SEGURIDAD - Suscribir a eventos de seguridad
    try:
        from automatizacion.agentes.agente_seguridad import AgenteSeguridad
        seguridad = AgenteSeguridad()
        
        def manejar_acceso_credential(evento):
            """Handler para accesos a credenciales."""
            payload = evento['payload']
            # AgenteSeguridad maneja esto internamente
            logger.info(f"Acceso a credential registrado: {payload.get('credential_id')}")
        
        bus.suscribir('credential_acceso', manejar_acceso_credential)
        logger.info("✅ Agente Seguridad suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Seguridad: {e}")

    # AGENTE RENDER - Suscribir a eventos de deploy
    try:
        from automatizacion.agentes.agente_render import AgenteRender
        render = AgenteRender()
        
        def manejar_deploy_solicitado(evento):
            """Handler para deploy solicitado."""
            payload = evento['payload']
            logger.info(f"Deploy solicitado para: {payload.get('servicio')}")
            # AgenteRender maneja el deploy
        
        bus.suscribir('deploy_solicitado', manejar_deploy_solicitado)
        logger.info("✅ Agente Render suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Render: {e}")

    # AGENTE EXPERTO ERRORES - Suscribir a errores complejos
    try:
        from automatizacion.agentes.agente_experto_errores import AgenteExpertoErrores
        experto = AgenteExpertoErrores()
        
        def manejar_error_complejo(evento):
            """Handler para errores complejos que requieren investigación."""
            payload = evento['payload']
            logger.info(f"Error complejo para investigación: {payload.get('descripcion')}")
        
        bus.suscribir('error_complejo', manejar_error_complejo)
        logger.info("✅ Agente Experto Errores suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Experto Errores: {e}")

    # AGENTE LIMPIADOR BASURA - Ejecutar vía scheduler (no requiere suscripción)
    logger.info("ℹ️  Agente Limpiador Basura ejecuta vía scheduler")

    # AGENTE INFORMES LOGS - Suscribir a eventos de logging
    try:
        from automatizacion.agentes.agente_informes_logs import AgenteInformesLogs
        informes = AgenteInformesLogs()
        
        def manejar_log_generado(evento):
            """Handler para logs generados."""
            payload = evento['payload']
            logger.info(f"Log generado para análisis: {payload.get('tipo')}")
        
        bus.suscribir('log_generado', manejar_log_generado)
        logger.info("✅ Agente Informes Logs suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Informes Logs: {e}")

    # RECOLECTORES - Publican eventos, no requieren suscripción
    logger.info("ℹ️  Recolectores (nubes, estrategias, recursos) publican eventos")

    # AGENTE INVESTIGACION MODELOS - Suscribir a eventos de modelos
    try:
        from automatizacion.agentes.agente_investigacion_modelos import AgenteInvestigacionModelos
        investigador = AgenteInvestigacionModelos()
        
        def manejar_modelo_deprecado(evento):
            """Handler para modelos deprecados."""
            payload = evento['payload']
            logger.info(f"Modelo deprecado detectado: {payload.get('modelo')}")
        
        bus.suscribir('modelo_deprecado', manejar_modelo_deprecado)
        logger.info("✅ Agente Investigación Modelos suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Investigación Modelos: {e}")

    # AGENTE GESTOR GMAIL - Suscribir a eventos de tokens
    try:
        from automatizacion.agentes.agente_gestor_gmail import AgenteGestorGmail
        gestor = AgenteGestorGmail()
        
        def manejar_token_agotado(evento):
            """Handler para tokens agotados."""
            payload = evento['payload']
            logger.info(f"Token agotado: {payload.get('cuenta')}")
        
        bus.suscribir('token_agotado', manejar_token_agotado)
        logger.info("✅ Agente Gestor Gmail suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Gestor Gmail: {e}")

    # AGENTE AI TOWN - Suscribir a eventos de AI Town
    try:
        from automatizacion.agentes.agente_ai_town import AgenteAITown
        ai_town = AgenteAITown()
        
        def manejar_ai_town_error(evento):
            """Handler para errores en AI Town."""
            payload = evento['payload']
            logger.info(f"Error AI Town: {payload.get('descripcion')}")
        
        bus.suscribir('ai_town_error', manejar_ai_town_error)
        logger.info("✅ Agente AI Town suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente AI Town: {e}")

    # AGENTE CREAR BOT TELEGRAM - Suscribir a eventos de creación
    try:
        from automatizacion.agentes.agente_crear_bot_telegram import AgenteCrearBotTelegram
        creador = AgenteCrearBotTelegram()
        
        def manejar_bot_solicitado(evento):
            """Handler para bots solicitados."""
            payload = evento['payload']
            logger.info(f"Bot solicitado: {payload.get('nombre')}")
        
        bus.suscribir('bot_solicitado', manejar_bot_solicitado)
        logger.info("✅ Agente Crear Bot Telegram suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Crear Bot Telegram: {e}")

    # AGENTE CONFIGURAR WEBHOOK META - Suscribir a eventos de webhook
    try:
        from automatizacion.agentes.agente_configurar_webhook_meta import AgenteConfigurarWebhookMeta
        webhook = AgenteConfigurarWebhookMeta()
        
        def manejar_webhook_solicitado(evento):
            """Handler para webhooks solicitados."""
            payload = evento['payload']
            logger.info(f"Webhook solicitado: {payload.get('telefono')}")
        
        bus.suscribir('webhook_solicitado', manejar_webhook_solicitado)
        logger.info("✅ Agente Configurar Webhook Meta suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Configurar Webhook Meta: {e}")

    # AGENTE GIT COMMIT - Suscribir a eventos de git
    try:
        # AgenteGitCommit es un script funcional, no una clase
        def manejar_commit_solicitado(evento):
            """Handler para commits solicitados."""
            payload = evento['payload']
            logger.info(f"Commit solicitado: {payload.get('mensaje')}")
        
        bus.suscribir('commit_solicitado', manejar_commit_solicitado)
        logger.info("✅ Agente Git Commit suscrito al Event Bus")
    except Exception as e:
        logger.error(f"❌ Error suscribiendo Agente Git Commit: {e}")

    # FABRICA DE BOTS - Agentes de la división
    logger.info("ℹ️  Agentes Fábrica de Bots ejecutan vía scheduler")

    # RECURSOS GRATIS - Agentes de la división
    logger.info("ℹ️  Agentes Recursos Gratis ejecutan vía scheduler")

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

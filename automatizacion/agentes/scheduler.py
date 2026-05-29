"""
Scheduler — QuantumHive Autonomous Intelligence System
Gestiona tareas periódicas automáticas de la Colmena.
"""

import os
import logging
import threading
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Importar AGI para notificaciones
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
USER_TELEGRAM_ID = os.getenv('USER_TELEGRAM_ID', '')

# Importar Agente Cerebro
try:
    from agente_cerebro import agente_cerebro
    CEREBRO_DISPONIBLE = True
except ImportError:
    agente_cerebro = None
    CEREBRO_DISPONIBLE = False

def notificar_sergio(mensaje: str):
    """Envía notificación a Sergio via Telegram."""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            'chat_id': USER_TELEGRAM_ID,
            'text': mensaje
        }, timeout=10)
    except Exception as e:
        logger.error(f"Error notificando a Sergio: {e}")


# ============================================================
# JOBS DEL SCHEDULER
# ============================================================

def job_heartbeat():
    """Cada 5 minutos: verificar que AGI está viva."""
    logger.info(f"[Heartbeat] Sistema activo — {datetime.now().strftime('%H:%M')}")


def job_monitor_bots():
    """Cada 15 minutos: verificar estado de bots de trading."""
    try:
        import sqlite3
        conn = sqlite3.connect('agi_memoria_telegram.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, estado, score_reputacion 
            FROM agentes 
            WHERE estado != 'operativo'
        """)
        agentes_problema = cursor.fetchall()
        conn.close()

        if agentes_problema:
            for agente in agentes_problema:
                logger.warning(f"Agente con problema: {agente[0]} — {agente[1]}")
                # Publicar evento al bus
                publicar_evento('agente_problema', 'scheduler',
                               {'agente': agente[0], 'estado': agente[1]})
    except Exception as e:
        logger.error(f"Error monitor bots: {e}")


def job_briefing_diario():
    """Todos los días a las 9:00 ARG: enviar briefing a Sergio."""
    try:
        from agi_autonomous.briefing_generator import BriefingGenerator
        bg = BriefingGenerator()
        briefing = bg.generar_briefing()
        notificar_sergio(f"📊 BRIEFING DIARIO QUANTUMHIVE\n{briefing}")
        logger.info("Briefing diario enviado a Sergio")
    except Exception as e:
        logger.error(f"Error briefing diario: {e}")
        notificar_sergio("📊 Briefing diario: sistema activo, sin datos suficientes aún.")


def job_limpiar_historial():
    """Cada día a las 3:00: limpiar historial antiguo de SQLite."""
    try:
        import sqlite3
        conn = sqlite3.connect('agi_memoria_telegram.db')
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM conversaciones
            WHERE id NOT IN (
                SELECT id FROM conversaciones
                ORDER BY fecha DESC LIMIT 200
            )
        """)
        eliminados = cursor.rowcount
        conn.commit()
        conn.close()
        if eliminados > 0:
            logger.info(f"Historial limpiado: {eliminados} mensajes eliminados")
    except Exception as e:
        logger.error(f"Error limpiando historial: {e}")


def job_verificar_alertas():
    """Cada 30 minutos: revisar alertas activas y notificar."""
    try:
        import sqlite3
        conn = sqlite3.connect('agi_memoria_telegram.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tipo, severidad, descripcion
            FROM alertas
            WHERE estado = 'activa' AND severidad = 'critica'
            ORDER BY fecha DESC LIMIT 5
        """)
        alertas = cursor.fetchall()
        conn.close()

        for alerta in alertas:
            notificar_sergio(
                f"🔴 ALERTA CRÍTICA\n"
                f"Tipo: {alerta[0]}\n"
                f"Descripción: {alerta[2]}"
            )
    except Exception as e:
        logger.error(f"Error verificando alertas: {e}")


def job_ceo_dashboard():
    """Cada hora: actualizar dashboard CEO."""
    try:
        from division_sala_inversion.agente_ceo_sala import AgenteCEOSala
        agente = AgenteCEOSala()
        dashboard = agente.obtener_dashboard_ceo()
        logger.info(f"Dashboard CEO actualizado: {dashboard.get('resumen', {})}")
        agente.cerrar()
    except Exception as e:
        logger.error(f"Error dashboard CEO: {e}")


def job_control_calidad():
    """Cada 6 horas: revisar pruebas pendientes de control de calidad."""
    try:
        from division_biblioteca_fabrica_bots.agente_control_calidad import AgenteControlCalidad
        agente = AgenteControlCalidad()
        pruebas_pendientes = agente.obtener_pruebas_bot(estado='EN_PROGRESO')
        if pruebas_pendientes:
            logger.info(f"Control calidad: {len(pruebas_pendientes)} pruebas en progreso")
        agente.cerrar()
    except Exception as e:
        logger.error(f"Error control calidad: {e}")


def job_base_conocimiento():
    """Cada día a las 4:00: limpiar y optimizar base de conocimiento."""
    try:
        from division_uci.agente_base_conocimiento import AgenteBaseConocimiento
        agente = AgenteBaseConocimiento()
        stats = agente.obtener_estadisticas(dias=1)
        logger.info(f"Base conocimiento: {stats}")
        agente.cerrar()
    except Exception as e:
        logger.error(f"Error base conocimiento: {e}")


def publicar_evento(tipo: str, origen: str, payload: dict = None):
    """Publica un evento en el Event Bus via SQLite."""
    try:
        import sqlite3
        import json
        conn = sqlite3.connect('agi_memoria_telegram.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO eventos (tipo, origen, payload, estado)
            VALUES (?, ?, ?, 'pendiente')
        """, (tipo, origen, json.dumps(payload or {})))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error publicando evento: {e}")


class QuantumHiveScheduler:
    """Scheduler central de QuantumHive."""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')
        self._registrar_jobs()
        logger.info("QuantumHiveScheduler inicializado")

    def _registrar_jobs(self):
        """Registra todos los jobs del sistema."""

        # Heartbeat cada 5 minutos
        self.scheduler.add_job(
            func=job_heartbeat,
            trigger=IntervalTrigger(minutes=5),
            id='heartbeat',
            name='Heartbeat del sistema'
        )

        # Monitor de bots cada 15 minutos
        self.scheduler.add_job(
            func=job_monitor_bots,
            trigger=IntervalTrigger(minutes=15),
            id='monitor_bots',
            name='Monitor de bots y agentes'
        )

        # Briefing diario a las 9:00 ARG
        self.scheduler.add_job(
            func=job_briefing_diario,
            trigger=CronTrigger(hour=9, minute=0),
            id='briefing_diario',
            name='Briefing diario a Sergio'
        )

        # Limpiar historial cada día a las 3:00
        self.scheduler.add_job(
            func=job_limpiar_historial,
            trigger=CronTrigger(hour=3, minute=0),
            id='limpiar_historial',
            name='Limpieza de historial SQLite'
        )

        # Verificar alertas cada 30 minutos
        self.scheduler.add_job(
            func=job_verificar_alertas,
            trigger=IntervalTrigger(minutes=30),
            id='verificar_alertas',
            name='Verificación de alertas críticas'
        )

        # Dashboard CEO cada hora
        self.scheduler.add_job(
            func=job_ceo_dashboard,
            trigger=IntervalTrigger(hours=1),
            id='ceo_dashboard',
            name='Dashboard CEO'
        )

        # Control calidad cada 6 horas
        self.scheduler.add_job(
            func=job_control_calidad,
            trigger=IntervalTrigger(hours=6),
            id='control_calidad',
            name='Control de calidad'
        )

        # Base conocimiento cada día a las 4:00
        self.scheduler.add_job(
            func=job_base_conocimiento,
            trigger=CronTrigger(hour=4, minute=0),
            id='base_conocimiento',
            name='Base de conocimiento'
        )

        # Agente Cerebro — briefing horario para AGI
        if CEREBRO_DISPONIBLE and agente_cerebro:
            try:
                if hasattr(agente_cerebro, 'ejecutar'):
                    self.scheduler.add_job(
                        func=agente_cerebro.ejecutar,
                        trigger=IntervalTrigger(hours=1),
                        id='agente_cerebro_briefing',
                        name='Agente Cerebro — briefing horario para AGI'
                    )
            except Exception as e:
                logger.error(f"Error registrando Agente Cerebro en scheduler: {e}")

        # Grafana Reporter — actualiza métricas cada 5 minutos
        try:
            from agente_grafana_reporter import AgenteGrafanaReporter
            self.agente_grafana_reporter = AgenteGrafanaReporter()
            self.scheduler.add_job(
                func=self.agente_grafana_reporter.ejecutar,
                trigger=IntervalTrigger(minutes=5),
                id='grafana_reporter',
                name='Grafana Reporter — métricas Colmena'
            )
        except Exception as e:
            logger.error(f"Error registrando Grafana Reporter: {e}")

        logger.info(f"Jobs registrados: {len(self.scheduler.get_jobs())}")

    def iniciar(self):
        """Inicia el scheduler en background."""
        self.scheduler.start()
        logger.info("Scheduler iniciado — jobs activos")

    def detener(self):
        """Detiene el scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler detenido")

    def estado(self) -> dict:
        """Retorna estado actual del scheduler."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'nombre': job.name,
                'proxima_ejecucion': str(job.next_run_time)
            })
        return {
            'activo': self.scheduler.running,
            'jobs': jobs,
            'total_jobs': len(jobs)
        }


# Instancia global
scheduler_qh = QuantumHiveScheduler()

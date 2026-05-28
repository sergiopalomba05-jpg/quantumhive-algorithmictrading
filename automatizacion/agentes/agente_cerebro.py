"""
Agente Cerebro — QuantumHive Autonomous Intelligence System
Puente entre Event Bus y AGI Telegram.
Escucha pasiva, clasifica eventos por prioridad, escribe en cola_cerebro (SQLite).
AGI consulta cada 60s y envía prioridad-1 a Sergio por Telegram.
"""

import sqlite3
import json
import time
import logging
import threading
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = 'agi_memoria_telegram.db'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
USER_TELEGRAM_ID = os.getenv('USER_TELEGRAM_ID', '')

# Mapa de prioridades por tipo de evento
PRIORIDADES = {
    # Prioridad 1 — Crítico, notificar ya
    'ERROR_CRITICO': 1,
    'BOT_PAUSADO': 1,
    'DRAWDOWN': 1,
    # Prioridad 2 — Importante, reporte diario
    'SENAL_TRADING': 2,
    'SENAL_FINANCIERA': 2,
    'SENAL_RIESGO': 2,
    'AGENTE_PROBLEMA': 2,
    'SOLICITUD_RETIRO': 2,
    'CLIENTE_NUEVO': 2,
    'PAGO_CONFIRMADO': 2,
    # Prioridad 3 — Informativo, reporte semanal
    'DECISION_CEO': 3,
    'PRUEBA_COMPLETADA': 3,
    'VENTA_BOT': 3,
    'CONOCIMIENTO_AGREGADO': 3,
    'TRADER_RECOLECTADO': 3,
    'PREDICCION': 3,
}

def _enviar_telegram(mensaje: str):
    """Envía mensaje a Sergio por Telegram."""
    if not TELEGRAM_TOKEN or not USER_TELEGRAM_ID:
        logger.warning("TELEGRAM_TOKEN o USER_TELEGRAM_ID no configurados")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': USER_TELEGRAM_ID,
            'text': mensaje,
            'parse_mode': 'HTML'
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"Mensaje Telegram enviado: {mensaje[:80]}")
        return True
    except Exception as e:
        logger.error(f"Error enviando Telegram: {e}")
        return False


class AgenteCerebro:
    """Puente Event Bus → AGI. Clasifica eventos y los encola."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.event_bus = None
        self._corriendo = False
        self._crear_tablas()
        logger.info("AgenteCerebro inicializado")

    def _crear_tablas(self):
        """Crea tabla cola_cerebro si no existe."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cola_cerebro (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        evento_id INTEGER,
                        tipo_evento TEXT NOT NULL,
                        origen TEXT NOT NULL,
                        mensaje TEXT NOT NULL,
                        prioridad INTEGER DEFAULT 3,
                        leido INTEGER DEFAULT 0,
                        enviado_telegram INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
            logger.info("Tabla cola_cerebro verificada/creada")
        except Exception as e:
            logger.error(f"Error creando tabla cola_cerebro: {e}")

    def _clasificar_prioridad(self, tipo: str) -> int:
        """Determina prioridad según tipo de evento."""
        return PRIORIDADES.get(tipo, 3)

    def _generar_mensaje(self, evento: dict) -> str:
        """Genera mensaje legible a partir del evento."""
        tipo = evento.get('tipo', 'desconocido')
        origen = evento.get('origen', 'desconocido')
        payload = evento.get('payload', {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                payload = {}
        detalle = ""
        if isinstance(payload, dict):
            partes = [f"{k}={v}" for k, v in payload.items() if not k.startswith('_')]
            if partes:
                detalle = " | ".join(partes)
        return f"[{tipo}] desde {origen}: {detalle}" if detalle else f"[{tipo}] desde {origen}"

    def manejar_evento(self, evento: dict):
        """Handler para el Event Bus. Clasifica y escribe en cola."""
        try:
            tipo = evento.get('tipo', 'desconocido')
            origen = evento.get('origen', 'desconocido')
            mensaje = self._generar_mensaje(evento)
            prioridad = self._clasificar_prioridad(tipo)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO cola_cerebro (evento_id, tipo_evento, origen, mensaje, prioridad)
                    VALUES (?, ?, ?, ?, ?)
                """, (evento.get('id'), tipo, origen, mensaje, prioridad))
                conn.commit()

            logger.info(f"Cerebro encoló evento {tipo} (prioridad {prioridad})")
        except Exception as e:
            logger.error(f"Error en manejar_evento: {e}")

    def _notificar_prioridad_1(self):
        """Revisa cola_cerebro cada 10s y envía prioridad-1 no enviados."""
        while self._corriendo:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, mensaje FROM cola_cerebro
                        WHERE prioridad = 1 AND leido = 0 AND enviado_telegram = 0
                        ORDER BY id ASC LIMIT 5
                    """)
                    pendientes = cursor.fetchall()

                for row_id, mensaje in pendientes:
                    texto = f"\U0001f6a8 <b>Cerebro QH — Alerta Prioridad 1</b>\n\n{mensaje}"
                    ok = _enviar_telegram(texto)
                    with sqlite3.connect(self.db_path) as conn:
                        if ok:
                            conn.execute("UPDATE cola_cerebro SET leido=1, enviado_telegram=1 WHERE id=?", (row_id,))
                        else:
                            conn.execute("UPDATE cola_cerebro SET enviado_telegram=1, leido=1 WHERE id=?", (row_id,))
                        conn.commit()
            except Exception as e:
                logger.error(f"Error en notificar_prioridad_1: {e}")
            time.sleep(10)

    def iniciar(self, event_bus):
        """Inicia el cerebro: registra handler en Event Bus y arranca notificador."""
        try:
            self.event_bus = event_bus
            event_bus.suscribir('*', self.manejar_evento)
            self._corriendo = True
            hilo = threading.Thread(target=self._notificar_prioridad_1, daemon=True)
            hilo.start()
            logger.info("AgenteCerebro iniciado — escuchando todos los eventos")
        except Exception as e:
            logger.error(f"Error iniciando AgenteCerebro: {e}")

    def detener(self):
        """Detiene el cerebro."""
        self._corriendo = False
        logger.info("AgenteCerebro detenido")

    def obtener_pendientes(self, prioridad_min: int = 1, limite: int = 20):
        """Obtiene mensajes no leídos desde la prioridad dada."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, fecha, tipo_evento, origen, mensaje, prioridad
                    FROM cola_cerebro
                    WHERE leido = 0 AND prioridad <= ?
                    ORDER BY prioridad ASC, fecha DESC
                    LIMIT ?
                """, (prioridad_min, limite))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error obteniendo pendientes: {e}")
            return []

    def marcar_leidos(self, ids: list):
        """Marca mensajes como leídos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                placeholders = ','.join('?' * len(ids))
                conn.execute(f"UPDATE cola_cerebro SET leido=1 WHERE id IN ({placeholders})", ids)
                conn.commit()
        except Exception as e:
            logger.error(f"Error marcando leídos: {e}")


# Instancia singleton a nivel módulo (importada por agi_telegram.py)
agente_cerebro = AgenteCerebro()

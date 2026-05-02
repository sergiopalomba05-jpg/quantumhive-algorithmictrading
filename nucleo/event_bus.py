"""
Event Bus — QuantumHive Autonomous Intelligence System
Proceso que detecta eventos en SQLite y activa los agentes correspondientes.
Corre en background thread dentro de agi_telegram.py
"""

import sqlite3
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Callable

logger = logging.getLogger(__name__)

DB_PATH = 'agi_memoria_telegram.db'
INTERVALO_POLLING = 5  # segundos


class EventBus:
    """Bus de eventos central de QuantumHive."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.suscriptores: Dict[str, List[Callable]] = {}
        self._corriendo = False
        logger.info("EventBus inicializado")

    def suscribir(self, tipo_evento: str, handler: Callable):
        """Suscribe un handler a un tipo de evento."""
        if tipo_evento not in self.suscriptores:
            self.suscriptores[tipo_evento] = []
        self.suscriptores[tipo_evento].append(handler)
        logger.info(f"Suscriptor: {handler.__name__} → {tipo_evento}")

    def publicar(self, tipo: str, origen: str, payload: dict = None):
        """Publica un evento en el bus."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO eventos (tipo, origen, payload, estado)
                VALUES (?, ?, ?, 'pendiente')
            """, (tipo, origen, json.dumps(payload or {})))
            conn.commit()
            conn.close()
            logger.info(f"Evento publicado: {tipo} desde {origen}")
        except Exception as e:
            logger.error(f"Error publicando evento {tipo}: {e}")

    def _obtener_pendientes(self) -> List[dict]:
        """Obtiene eventos pendientes."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, tipo, origen, payload, intentos
                FROM eventos
                WHERE estado = 'pendiente' AND intentos < 3
                ORDER BY fecha ASC LIMIT 10
            """)
            eventos = []
            for row in cursor.fetchall():
                eventos.append({
                    'id': row[0], 'tipo': row[1],
                    'origen': row[2],
                    'payload': json.loads(row[3] or '{}'),
                    'intentos': row[4]
                })
            conn.close()
            return eventos
        except Exception as e:
            logger.error(f"Error obteniendo eventos: {e}")
            return []

    def _marcar_procesado(self, evento_id: int, procesado_por: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE eventos
            SET estado='procesado', procesado_en=CURRENT_TIMESTAMP,
                procesado_por=?
            WHERE id=?
        """, (procesado_por, evento_id))
        conn.commit()
        conn.close()

    def _marcar_fallido(self, evento_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE eventos
            SET intentos = intentos + 1,
                estado = CASE WHEN intentos+1 >= 3 THEN 'fallido'
                         ELSE 'pendiente' END
            WHERE id=?
        """, (evento_id,))
        conn.commit()
        conn.close()

    def _procesar(self, evento: dict):
        handlers = self.suscriptores.get(evento['tipo'], [])
        if not handlers:
            self._marcar_procesado(evento['id'], 'sin_suscriptor')
            return
        for handler in handlers:
            try:
                handler(evento)
                self._marcar_procesado(evento['id'], handler.__name__)
            except Exception as e:
                logger.error(f"Error en handler {handler.__name__}: {e}")
                self._marcar_fallido(evento['id'])

    def _loop(self):
        """Loop principal del Event Bus."""
        logger.info("EventBus loop iniciado")
        while self._corriendo:
            try:
                for evento in self._obtener_pendientes():
                    hilo = threading.Thread(
                        target=self._procesar,
                        args=(evento,),
                        daemon=True
                    )
                    hilo.start()
                time.sleep(INTERVALO_POLLING)
            except Exception as e:
                logger.error(f"Error en loop EventBus: {e}")
                time.sleep(INTERVALO_POLLING)

    def iniciar(self):
        """Inicia el Event Bus en un hilo background."""
        self._corriendo = True
        hilo = threading.Thread(target=self._loop, daemon=True)
        hilo.start()
        logger.info("EventBus corriendo en background")

    def detener(self):
        self._corriendo = False
        logger.info("EventBus detenido")


# Instancia global
event_bus = EventBus()

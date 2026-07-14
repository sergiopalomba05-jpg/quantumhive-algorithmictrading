"""
Event Bus Reader — Lee eventos del SQLite del Event Bus y actualiza el Estado Global.
"""

import sqlite3
import json
import logging
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .estado_global import EstadoGlobal, Evento, Senal, Posicion

logger = logging.getLogger(__name__)

EVENTOS_RELEVANTES = [
    "senal_detectada", "orden_ejecutada", "posicion_cerrada",
    "sl_alcanzado", "tp_alcanzado", "error_critico",
    "goat_heartbeat", "regimen_cambio", "score_actualizado",
    "señal_trading",
]


class EventBusReader:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ultimo_id = 0

    def leer_nuevos_eventos(self) -> List[Evento]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT id, tipo, origen, payload, fecha
                   FROM eventos
                   WHERE id > ? AND tipo IN ({})
                   ORDER BY id ASC LIMIT 50
                """.format(','.join('?' for _ in EVENTOS_RELEVANTES)),
                [self._ultimo_id] + EVENTOS_RELEVANTES
            ).fetchall()
            conn.close()

            eventos = []
            for row in rows:
                evento = Evento(
                    id=row['id'],
                    tipo=row['tipo'],
                    origen=row['origen'],
                    payload=json.loads(row['payload'] or '{}'),
                    timestamp=row['fecha'] or datetime.now().isoformat(),
                )
                eventos.append(evento)
                if row['id'] > self._ultimo_id:
                    self._ultimo_id = row['id']

            return eventos
        except Exception as e:
            logger.warning(f"Error leyendo eventos: {e}")
            return []

    def procesar_evento(self, evento: Evento, estado: EstadoGlobal):
        tipo = evento.tipo
        p = evento.payload

        if tipo == "señal_trading":
            senal = Senal(
                id=evento.id,
                direccion=p.get("direccion", ""),
                score=p.get("score", 0),
                precio=p.get("precio", 0),
                timestamp=evento.timestamp,
                clasificacion=p.get("clasificacion", ""),
                confluencias=p.get("confluencias", []),
            )
            estado.btc_ultima_senal = senal
            estado.btc_senales_hoy += 1
            estado.ultimas_senales.insert(0, senal)
            if len(estado.ultimas_senales) > 10:
                estado.ultimas_senales.pop()

        elif tipo == "orden_ejecutada":
            estado.btc_posicion_activa = Posicion(
                senal_id=p.get("senal_id", 0),
                side=p.get("direccion", "LONG"),
                entry_price=p.get("precio", 0),
                sl=p.get("sl", 0),
                tp=p.get("tp", 0),
                cantidad=p.get("cantidad", 0),
                timestamp_entrada=evento.timestamp,
            )

        elif tipo in ("posicion_cerrada", "sl_alcanzado", "tp_alcanzado"):
            estado.btc_posicion_activa = None
            pnl = p.get("pnl_usdt", 0)
            estado.btc_pnl_hoy += pnl
            estado.btc_trades_hoy += 1

        elif tipo == "goat_heartbeat":
            estado.goat_btc_activo = True
            estado.goat_btc_ultimo_heartbeat = evento.timestamp
            estado.render_dormido = False

        elif tipo == "error_critico":
            from .estado_global import Alerta
            estado.alertas_pendientes.append(Alerta(
                nombre="error_critico",
                severidad="CRITICA",
                mensaje=p.get("mensaje", "Error sin detalle"),
                timestamp=evento.timestamp,
            ))

        estado.ultimos_eventos.insert(0, evento)
        if len(estado.ultimos_eventos) > 5:
            estado.ultimos_eventos.pop()

    def sincronizar(self, estado: EstadoGlobal, max_eventos: int = 50):
        eventos = self.leer_nuevos_eventos()
        for ev in eventos[:max_eventos]:
            self.procesar_evento(ev, estado)
        return len(eventos)

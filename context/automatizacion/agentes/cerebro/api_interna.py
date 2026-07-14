"""
API Interna — Endpoints Flask en puerto 5001 para AGI y goat_btc.
"""

import logging
from flask import Flask, jsonify, request
from datetime import datetime

from .estado_global import EstadoGlobal
from .context_builder import construir_contexto_completo, construir_contexto_minimo

logger = logging.getLogger(__name__)

app = Flask(__name__)
estado: EstadoGlobal = None


def init_api(estado_global: EstadoGlobal):
    global estado
    estado = estado_global


@app.route('/snapshot', methods=['GET'])
def snapshot():
    if estado is None:
        return jsonify({'error': 'Cerebro no inicializado'}), 503
    pos = None
    if estado.btc_posicion_activa:
        pos = {
            "senal_id": estado.btc_posicion_activa.senal_id,
            "side": estado.btc_posicion_activa.side,
            "entry_price": estado.btc_posicion_activa.entry_price,
            "sl": estado.btc_posicion_activa.sl,
            "tp": estado.btc_posicion_activa.tp,
            "pnl_actual": estado.btc_posicion_activa.pnl_actual,
        }
    ultima_senal = None
    if estado.btc_ultima_senal:
        ultima_senal = {
            "id": estado.btc_ultima_senal.id,
            "direccion": estado.btc_ultima_senal.direccion,
            "score": estado.btc_ultima_senal.score,
            "precio": estado.btc_ultima_senal.precio,
            "timestamp": estado.btc_ultima_senal.timestamp,
        }
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "btc": {
            "precio_actual": estado.btc_precio_actual,
            "posicion_activa": pos,
            "ultima_senal": ultima_senal,
            "pnl_hoy": estado.btc_pnl_hoy,
            "trades_hoy": estado.btc_trades_hoy,
            "winrate_semana": estado.btc_winrate_semana,
        },
        "sistema": {
            "goat_btc_activo": estado.goat_btc_activo,
            "render_dormido": estado.render_dormido,
        },
        "alertas": [
            {"nombre": a.nombre, "severidad": a.severidad, "mensaje": a.mensaje}
            for a in estado.alertas_pendientes
        ],
    })


@app.route('/contexto_agi', methods=['GET'])
def contexto_agi():
    if estado is None:
        return jsonify({'contexto': '⚠️ Cerebro no disponible — operando sin contexto en tiempo real'}), 200
    modo = request.args.get('modo', 'completo')
    if modo == 'minimo':
        ctx = construir_contexto_minimo(estado)
    else:
        ctx = construir_contexto_completo(estado)
    return jsonify({'contexto': ctx})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'precio': estado.btc_precio_actual if estado else 0,
    })


@app.route('/evento', methods=['POST'])
def recibir_evento():
    """Recibe eventos de goat_btc u otros agentes."""
    if estado is None:
        return jsonify({'error': 'Cerebro no inicializado'}), 503
    data = request.json
    if not data:
        return jsonify({'error': 'payload vacío'}), 400
    tipo = data.get('tipo', 'desconocido')
    payload = data.get('payload', {})

    from .event_bus_reader import EventBusReader
    reader = EventBusReader('')
    from .estado_global import Evento
    evento = Evento(
        id=0, tipo=tipo, origen=data.get('origen', 'api'),
        payload=payload, timestamp=datetime.now().isoformat(),
    )
    reader.procesar_evento(evento, estado)
    return jsonify({'status': 'procesado', 'tipo': tipo}), 200


@app.route('/alertas', methods=['GET'])
def alertas():
    if estado is None:
        return jsonify({'alertas': []}), 200
    return jsonify({
        'alertas': [
            {"nombre": a.nombre, "severidad": a.severidad, "mensaje": a.mensaje, "timestamp": a.timestamp}
            for a in estado.alertas_pendientes
        ]
    })


@app.route('/performance', methods=['GET'])
def performance():
    if estado is None:
        return jsonify({'error': 'no data'}), 200
    return jsonify({
        'pnl_hoy': estado.btc_pnl_hoy,
        'trades_hoy': estado.btc_trades_hoy,
        'senales_hoy': estado.btc_senales_hoy,
        'winrate_semana': estado.btc_winrate_semana,
        'precio_actual': estado.btc_precio_actual,
    })

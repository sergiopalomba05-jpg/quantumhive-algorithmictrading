"""
Handlers de la Colmena — QuantumHive
Funciones que se activan automáticamente cuando ocurre un evento.
"""

import logging
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
USER_TELEGRAM_ID = os.getenv('USER_TELEGRAM_ID', '')


def _notificar_sergio(mensaje: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            'chat_id': USER_TELEGRAM_ID,
            'text': mensaje
        }, timeout=10)
    except Exception as e:
        logger.error(f"Error notificando: {e}")


# ============================================================
# HANDLERS DE TRADING
# ============================================================

def manejar_senal_trading(evento: dict):
    """
    Handler para señales de trading generadas por bots.
    Recibe la señal, la valida y la distribuye
    al canal de Telegram de señales.
    Registra en SQLite tabla metricas.
    """
    logger.info(f"[COLMENA] Señal de trading recibida: {evento}")
    # Por ahora registra la señal — implementación completa en brief futuro
    pass


def manejar_drawdown(evento: dict):
    """Se activa cuando un bot supera el límite de drawdown."""
    payload = evento.get('payload', {})
    bot = payload.get('bot', 'desconocido')
    drawdown = payload.get('drawdown', 0)
    cuenta = payload.get('cuenta', 'desconocida')

    logger.warning(f"DRAWDOWN ALERT: {bot} — {drawdown}% en {cuenta}")

    _notificar_sergio(
        f"🔴 DRAWDOWN ALERT\n"
        f"Bot: {bot}\n"
        f"Drawdown: {drawdown}%\n"
        f"Cuenta: {cuenta}\n"
        f"Acción: pausar operaciones manualmente"
    )


def manejar_compliance(evento: dict):
    """Registra eventos de compliance para PropFirms."""
    import sqlite3
    payload = evento.get('payload', {})
    try:
        conn = sqlite3.connect('agi_memoria_telegram.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alertas (tipo, severidad, descripcion)
            VALUES (?, ?, ?)
        """, ('compliance', 'alta', str(payload)))
        conn.commit()
        conn.close()
        logger.info(f"Compliance registrado: {payload}")
    except Exception as e:
        logger.error(f"Error en compliance: {e}")


def manejar_bot_pausado(evento: dict):
    """Registra cuando un bot es pausado."""
    payload = evento.get('payload', {})
    logger.info(f"Bot pausado registrado: {payload}")
    _notificar_sergio(
        f"⏸️ BOT PAUSADO\n"
        f"Bot: {payload.get('bot', 'desconocido')}\n"
        f"Razón: {payload.get('razon', 'sin especificar')}"
    )


# ============================================================
# HANDLERS DE CLIENTES
# ============================================================

def manejar_cliente_nuevo(evento: dict):
    """Se activa cuando entra un cliente nuevo."""
    payload = evento.get('payload', {})
    nombre = payload.get('nombre', 'Nuevo cliente')
    logger.info(f"Cliente nuevo: {nombre}")
    _notificar_sergio(
        f"🎉 CLIENTE NUEVO\n"
        f"Nombre: {nombre}\n"
        f"Acción: enviar bienvenida y crear accesos"
    )


def manejar_pago_confirmado(evento: dict):
    """Se activa cuando se confirma un pago."""
    payload = evento.get('payload', {})
    logger.info(f"Pago confirmado: {payload}")
    _notificar_sergio(
        f"💰 PAGO CONFIRMADO\n"
        f"Cliente: {payload.get('cliente', 'desconocido')}\n"
        f"Monto: {payload.get('monto', '?')}"
    )


# ============================================================
# HANDLERS DE SISTEMA
# ============================================================

def manejar_agente_problema(evento: dict):
    """Se activa cuando un agente tiene problemas."""
    payload = evento.get('payload', {})
    agente = payload.get('agente', 'desconocido')
    estado = payload.get('estado', 'error')
    logger.warning(f"Agente con problema: {agente} — {estado}")
    _notificar_sergio(
        f"⚠️ AGENTE CON PROBLEMA\n"
        f"Agente: {agente}\n"
        f"Estado: {estado}"
    )


def manejar_error_critico(evento: dict):
    """Se activa ante errores críticos del sistema."""
    payload = evento.get('payload', {})
    _notificar_sergio(
        f"🚨 ERROR CRÍTICO\n"
        f"Origen: {evento.get('origen', 'desconocido')}\n"
        f"Detalle: {payload.get('descripcion', 'sin detalle')}"
    )


# ============================================================
# HANDLERS DE SALA DE INVERSIÓN
# ============================================================

def manejar_solicitud_retiro(evento: dict):
    """Se activa cuando se crea una solicitud de retiro."""
    payload = evento.get('payload', {})
    cliente = payload.get('cliente', 'desconocido')
    monto = payload.get('monto', 0)
    logger.info(f"Solicitud retiro: {cliente} - ${monto}")
    _notificar_sergio(
        f"💸 SOLICITUD DE RETIRO\n"
        f"Cliente: {cliente}\n"
        f"Monto: ${monto}\n"
        f"Acción: revisar y aprobar/rechazar"
    )


def manejar_decision_ceo(evento: dict):
    """Se activa cuando el CEO toma una decisión estratégica."""
    payload = evento.get('payload', {})
    tipo = payload.get('tipo', 'desconocido')
    descripcion = payload.get('descripcion', '')
    logger.info(f"Decisión CEO: {tipo} - {descripcion}")
    _notificar_sergio(
        f"🎯 DECISIÓN CEO\n"
        f"Tipo: {tipo}\n"
        f"Descripción: {descripcion}"
    )


# ============================================================
# HANDLERS DE FÁBRICA DE BOTS
# ============================================================

def manejar_prueba_completada(evento: dict):
    """Se activa cuando se completa una prueba de control de calidad."""
    payload = evento.get('payload', {})
    bot = payload.get('bot', 'desconocido')
    resultado = payload.get('resultado', 'desconocido')
    logger.info(f"Prueba completada: {bot} - {resultado}")
    if resultado == 'APROBADO':
        _notificar_sergio(
            f"✅ PRUEBA APROBADA\n"
            f"Bot: {bot}\n"
            f"Resultado: {resultado}\n"
            f"Acción: bot listo para producción"
        )


def manejar_venta_bot(evento: dict):
    """Se activa cuando se vende un bot."""
    payload = evento.get('payload', {})
    bot = payload.get('bot', 'desconocido')
    cliente = payload.get('cliente', 'desconocido')
    monto = payload.get('monto', 0)
    logger.info(f"Venta bot: {bot} a {cliente} - ${monto}")
    _notificar_sergio(
        f"💰 VENTA BOT\n"
        f"Bot: {bot}\n"
        f"Cliente: {cliente}\n"
        f"Monto: ${monto}"
    )


# ============================================================
# HANDLERS DE UCI (Conocimiento)
# ============================================================

def manejar_conocimiento_agregado(evento: dict):
    """Se activa cuando se agrega conocimiento a la base."""
    payload = evento.get('payload', {})
    tipo = payload.get('tipo', 'desconocido')
    fuente = payload.get('fuente', 'desconocida')
    logger.info(f"Conocimiento agregado: {tipo} - Fuente: {fuente}")


def manejar_trader_recolectado(evento: dict):
    """Se activa cuando se recolecta un perfil de trader."""
    payload = evento.get('payload', {})
    nombre = payload.get('nombre', 'desconocido')
    plataforma = payload.get('plataforma', 'desconocida')
    logger.info(f"Trader recolectado: {nombre} - {plataforma}")
    _notificar_sergio(
        f"👤 TRADER RECOLECTADO\n"
        f"Nombre: {nombre}\n"
        f"Plataforma: {plataforma}\n"
        f"Acción: analizar estrategias"
    )


# ============================================================
# CATÁLOGO DE EVENTOS
# ============================================================

class Eventos:
    ALERTA_DRAWDOWN = "alerta_drawdown"
    BOT_PAUSADO = "bot_pausado"
    CLIENTE_NUEVO = "cliente_nuevo"
    PAGO_CONFIRMADO = "pago_confirmado"
    AGENTE_PROBLEMA = "agente_problema"
    ERROR_CRITICO = "error_critico"
    SEÑAL_TRADING = "señal_trading"
    # Nuevos eventos para agentes M1 D16
    SOLICITUD_RETIRO = "solicitud_retiro"
    DECISION_CEO = "decision_ceo"
    # Nuevos eventos para agentes M4 D8
    PRUEBA_COMPLETADA = "prueba_completada"
    VENTA_BOT = "venta_bot"
    # Nuevos eventos para agentes M4 D18
    CONOCIMIENTO_AGREGADO = "conocimiento_agregado"
    TRADER_RECOLECTADO = "trader_recolectado"


def registrar_suscriptores(bus):
    """Registra todos los handlers en el Event Bus."""
    bus.suscribir(Eventos.ALERTA_DRAWDOWN, manejar_drawdown)
    bus.suscribir(Eventos.ALERTA_DRAWDOWN, manejar_compliance)
    bus.suscribir(Eventos.BOT_PAUSADO, manejar_bot_pausado)
    bus.suscribir(Eventos.CLIENTE_NUEVO, manejar_cliente_nuevo)
    bus.suscribir(Eventos.PAGO_CONFIRMADO, manejar_pago_confirmado)
    bus.suscribir(Eventos.AGENTE_PROBLEMA, manejar_agente_problema)
    bus.suscribir(Eventos.ERROR_CRITICO, manejar_error_critico)
    bus.suscribir(Eventos.SEÑAL_TRADING, manejar_senal_trading)
    # Handlers M1 D16 - Sala de Inversión
    bus.suscribir(Eventos.SOLICITUD_RETIRO, manejar_solicitud_retiro)
    bus.suscribir(Eventos.DECISION_CEO, manejar_decision_ceo)
    # Handlers M4 D8 - Fábrica de Bots
    bus.suscribir(Eventos.PRUEBA_COMPLETADA, manejar_prueba_completada)
    bus.suscribir(Eventos.VENTA_BOT, manejar_venta_bot)
    # Handlers M4 D18 - UCI
    bus.suscribir(Eventos.CONOCIMIENTO_AGREGADO, manejar_conocimiento_agregado)
    bus.suscribir(Eventos.TRADER_RECOLECTADO, manejar_trader_recolectado)
    logger.info("Todos los handlers registrados en EventBus")

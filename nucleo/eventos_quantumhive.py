"""
Catálogo de eventos estándar de QuantumHive.
Todos los agentes usan estos tipos para publicar y suscribirse.
"""

class Eventos:
    """Tipos de eventos estándar de la Colmena."""
    
    # TRADING
    ALERTA_DRAWDOWN = "alerta_drawdown"
    SEÑAL_TRADING = "señal_trading"
    ORDEN_EJECUTADA = "orden_ejecutada"
    BOT_ACTIVADO = "bot_activado"
    BOT_PAUSADO = "bot_pausado"
    CUENTA_ROTADA = "cuenta_rotada"
    
    # CLIENTES
    CLIENTE_NUEVO = "cliente_nuevo"
    PAGO_CONFIRMADO = "pago_confirmado"
    CHALLENGE_CREADO = "challenge_creado"
    CLIENTE_INACTIVO = "cliente_inactivo"
    
    # SISTEMA
    AGENTE_EN_CUARENTENA = "agente_en_cuarentena"
    AGENTE_RECUPERADO = "agente_recuperado"
    ERROR_CRITICO = "error_critico"
    HEARTBEAT = "heartbeat"
    
    # CONTENIDO
    SEÑAL_FORMATEADA = "señal_formateada"
    POST_GENERADO = "post_generado"
    INFOPRODUCTO_CREADO = "infoproducto_creado"
    
    # FABRICA DE BOTS
    BOT_ENTRENADO = "bot_entrenado"
    BACKTESTING_COMPLETADO = "backtesting_completado"
    BOT_APROBADO_PRODUCCION = "bot_aprobado_produccion"


# Mapa de eventos → agentes responsables (documentación)
MAPA_RESPONSABILIDADES = {
    Eventos.ALERTA_DRAWDOWN:         ["AgenteRiesgo", "AgenteCompliance", "AGI"],
    Eventos.SEÑAL_TRADING:           ["AgenteFormateadorSeñales", "AgenteTelegram"],
    Eventos.CLIENTE_NUEVO:           ["AgenteBienvenida", "AgenteOnboarding"],
    Eventos.PAGO_CONFIRMADO:         ["AgenteChallenge", "AgenteCRM"],
    Eventos.AGENTE_EN_CUARENTENA:    ["AGI"],
    Eventos.BOT_ENTRENADO:           ["AgenteBacktesting"],
    Eventos.BACKTESTING_COMPLETADO:  ["AgenteValidadorConversacional"],
    Eventos.BOT_APROBADO_PRODUCCION: ["AgenteDeployBot"],
}

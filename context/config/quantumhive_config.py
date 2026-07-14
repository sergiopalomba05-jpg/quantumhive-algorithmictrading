"""
QUANTUMHIVE CONFIG - Configuración Centralizada
Centraliza toda la configuración del sistema QuantumHive.
"""

import os
from typing import Dict, List, Optional


class QuantumHiveConfig:
    """Clase de configuración centralizada del sistema."""
    
    # ==================== RUTAS DE ARCHIVOS Y DIRECTORIOS ====================
    
    # Directorios principales
    DIR_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DIR_NUCLEO = os.path.join(DIR_PROYECTO, 'nucleo')
    DIR_AUTOMATIZACION = os.path.join(DIR_PROYECTO, 'automatizacion')
    DIR_LOGS = os.path.join(DIR_PROYECTO, 'logs')
    DIR_DATASETS = os.path.join(DIR_PROYECTO, 'datasets')
    DIR_REPORTES = os.path.join(DIR_PROYECTO, 'reportes')
    DIR_TESTS = os.path.join(DIR_PROYECTO, 'tests')
    
    # Subdirectorios del núcleo
    DIR_GOVERNANCE = os.path.join(DIR_NUCLEO, 'governance')
    DIR_DLRI = os.path.join(DIR_NUCLEO, 'dlri')
    DIR_PERSISTENCIA = os.path.join(DIR_NUCLEO, 'persistencia')
    DIR_UGCC = os.path.join(DIR_NUCLEO, 'ugcc')
    DIR_SEGURIDAD = os.path.join(DIR_NUCLEO, 'seguridad')
    DIR_GVCA = os.path.join(DIR_NUCLEO, 'gvca')
    DIR_INTELIGENCIA_INFINITA = os.path.join(DIR_NUCLEO, 'inteligencia_infinita')
    DIR_UVID = os.path.join(DIR_NUCLEO, 'uvid')
    
    # Archivos de configuración y datos
    ARCHIVO_CONFIG_REPUTACION = os.path.join(DIR_GOVERNANCE, 'config_reputation.json')
    ARCHIVO_HISTORIAL_IDEAS = os.path.join(DIR_INTELIGENCIA_INFINITA, 'historial_ideas.json')
    ARCHIVO_IDEAS = os.path.join(DIR_INTELIGENCIA_INFINITA, 'ideas.json')
    ARCHIVO_VISION_CEO = os.path.join(DIR_PROYECTO, 'vision_ceo.md')
    ARCHIVO_CONTEXTO_MAESTRO = os.path.join(DIR_PROYECTO, 'CONTEXTO_MAESTRO.md')
    
    # Archivos DLRI
    ARCHIVO_INTELLIGENCE_REPORT = os.path.join(DIR_DLRI, 'intelligence_report.md')
    
    # Archivos UVID
    ARCHIVO_DESIGN_SYSTEM = os.path.join(DIR_UVID, 'design_system.json')
    ARCHIVO_VERSIONES_DASHBOARD = os.path.join(DIR_UVID, 'versiones_dashboard.json')
    ARCHIVO_HISTORIAL_QA = os.path.join(DIR_UVID, 'historial_qa.json')
    
    # Archivos GVCA
    ARCHIVO_VPS_REGISTRY = os.path.join(DIR_GVCA, 'vps_registry.json')
    ARCHIVO_BOT_REGISTRY = os.path.join(DIR_GVCA, 'bot_registry.json')
    
    # ==================== PARÁMETROS DEL SISTEMA DE REPUTACIÓN ====================
    
    # Niveles de reputación
    NIVELES_REPUTACION = {
        'cuarentena': {'min_score': 0, 'max_score': 39, 'modelo': None},
        'bronce': {'min_score': 40, 'max_score': 59, 'modelo': 'claude-haiku-3-5'},
        'operativo': {'min_score': 60, 'max_score': 89, 'modelo': 'claude-sonnet-4-6'},
        'elite': {'min_score': 90, 'max_score': 100, 'modelo': 'claude-opus-4-6'}
    }
    
    # Ajustes de score
    AJUSTE_TAREA_EXITOSA = 5
    AJUSTE_TAREA_FALLIDA = -10
    AJUSTE_TAREA_CRITICA_FALLIDA = -20
    SCORE_INICIAL_AGENTE = 50
    
    # Umbral para cuarentena automática
    UMBRAL_CUARENTENA = 30
    UMBRAL_SALIDA_CUARENTENA = 50
    
    # ==================== LÍMITES DE OPERACIONES POR DÍA ====================
    
    # Límites de tokens por agente por día
    LIMITE_TOKENS_DIA_HAIKU = 100000
    LIMITE_TOKENS_DIA_SONNET = 200000
    LIMITE_TOKENS_DIA_OPUS = 500000
    
    # Límites de llamadas API por día
    LIMITE_LLAMADAS_ANTHROPIC_DIA = 100
    LIMITE_LLAMADAS_GROQ_DIA = 500
    LIMITE_LLAMADAS_GEMINI_DIA = 300
    LIMITE_LLAMADAS_OPENROUTER_DIA = 200
    
    # Límites de operaciones por división
    LIMITE_OPERACIONES_DIA = 1000
    LIMITE_OPERACIONES_HORA = 100
    
    # ==================== HORARIOS OPERATIVOS ====================
    
    # Horarios de trading (UTC)
    HORARIO_TRADING_INICIO = '13:00'  # 9:00 AM EST
    HORARIO_TRADING_FIN = '21:00'     # 5:00 PM EST
    HORARIO_TRADING_DIAS = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']  # Lunes a Viernes
    
    # Horarios de mantenimiento
    HORARIO_MANTENIMIENTO_INICIO = '22:00'  # 6:00 PM EST
    HORARIO_MANTENIMIENTO_FIN = '23:00'     # 7:00 PM EST
    DIAS_MANTENIMIENTO = ['SAB']  # Sábados
    
    # ==================== UMBRALES DE ALERTAS ====================
    
    # Alertas de drawdown
    UMBRAL_DRAWDOWN_WARNING = 0.10  # 10%
    UMBRAL_DRAWDOWN_CRITICAL = 0.20  # 20%
    UMBRAL_DRAWDOWN_EMERGENCY = 0.30  # 30%
    
    # Alertas de tasa de éxito
    UMBRAL_TASA_EXITO_MINIMA = 0.35  # 35%
    UMBRAL_TASA_EXITO_WARNING = 0.25  # 25%
    
    # Alertas de errores
    UMBRAL_ERRORES_CONSECUTIVOS = 5
    UMBRAL_ERRORES_TOTALES = 20
    
    # Alertas de memoria
    UMBRAL_MEMORIA_WARNING = 0.80  # 80%
    UMBRAL_MEMORIA_CRITICAL = 0.90  # 90%
    
    # ==================== CONFIGURACIÓN DE APIs ====================
    
    # Nombres de variables de entorno (sin keys)
    ENV_ANTHROPIC_API_KEY = 'ANTHROPIC_API_KEY'
    ENV_GROQ_API_KEY = 'GROQ_API_KEY'
    ENV_GEMINI_API_KEY = 'GEMINI_API_KEY'
    ENV_OPENROUTER_API_KEY = 'OPENROUTER_API_KEY'
    
    # Telegram
    ENV_TELEGRAM_BOT_TOKEN = 'TELEGRAM_BOT_TOKEN'
    ENV_TELEGRAM_CHAT_ID_SERGIO = 'TELEGRAM_CHAT_ID_SERGIO'
    ENV_TELEGRAM_CHAT_ID_ALERTAS = 'TELEGRAM_CHAT_ID_ALERTAS'
    
    # WhatsApp
    ENV_WHATSAPP_TOKEN = 'WHATSAPP_TOKEN'
    ENV_WHATSAPP_PHONE_ID = 'WHATSAPP_PHONE_ID'
    
    # MetaTrader 5
    ENV_MT5_LOGIN = 'MT5_LOGIN'
    ENV_MT5_PASSWORD = 'MT5_PASSWORD'
    ENV_MT5_SERVER = 'MT5_SERVER'
    
    # ==================== PARÁMETROS DE BACKTESTING ====================
    
    # Períodos de backtesting
    PERIODO_BACKTEST_DEFAULT = '2023-01-01'
    PERIODO_BACKTEST_MINIMO = '2022-01-01'
    
    # Métricas mínimas para aprobación
    WINRATE_MINIMO = 0.35  # 35%
    PROFIT_FACTOR_MINIMO = 1.5
    MAX_DRAWDOWN_MAXIMO = 0.20  # 20%
    
    # Parámetros de walk-forward
    WALK_FORWARD_TRAIN_SIZE = 0.7  # 70% entrenamiento
    WALK_FORWARD_TEST_SIZE = 0.3   # 30% test
    
    # ==================== PARÁMETROS DE ENTRENAMIENTO RL ====================
    
    # Parámetros PPO
    PPO_LEARNING_RATE = 0.0003
    PPO_GAMMA = 0.99
    PPO_GAE_LAMBDA = 0.95
    PPO_CLIP_EPSILON = 0.2
    PPO_EPOCHS = 10
    
    # Steps de entrenamiento
    STEPS_ENTRENAMIENTO_MINIMO = 500000
    STEPS_ENTRENAMIENTO_RECOMENDADO = 1000000
    STEPS_ENTRENAMIENTO_MAXIMO = 5000000
    
    # ==================== PARÁMETROS DE MONETIZACIÓN (SISTEMA 8) ====================
    
    # UMI - Low Ticket
    UMI_LT_PRECIO_MINIMO = 10
    UMI_LT_PRECIO_MAXIMO = 100
    UMI_LT_VOLUMEN_MINIMO = 100
    
    # UMI - High Ticket
    UMI_HT_PRECIO_MINIMO = 1000
    UMI_HT_PRECIO_MAXIMO = 50000
    UMI_HT_FIT_SCORE_MINIMO = 70
    
    # ==================== PARÁMETROS DE DASHBOARD (SISTEMA 10) ====================
    
    # Actualización de métricas
    DASHBOARD_UPDATE_INTERVAL = 60  # segundos
    
    # Retención de datos históricos
    DASHBOARD_RETENCION_DIAS = 30
    
    # ==================== PARÁMETROS DE AGENTES INICIALES (SISTEMA 12) ====================
    
    # Scheduler
    SCHEDULER_INTERVAL_MINIMO = 60  # segundos
    SCHEDULER_INTERVAL_RECOMENDADO = 900  # 15 minutos
    
    # Compliance
    COMPLIANCE_CHECK_INTERVAL = 3600  # 1 hora
    COMPLIANCE_SCORE_MINIMO = 80
    
    # Recolector
    RECOLECTOR_INTERVAL = 86400  # 24 horas
    RECOLECTOR_RETENCION_DIAS = 90
    
    # ==================== PARÁMETROS DE LOGGING ====================
    
    # Niveles de logging
    LOG_LEVEL_DEFAULT = 'INFO'
    LOG_LEVEL_DEBUG = 'DEBUG'
    LOG_LEVEL_ERROR = 'ERROR'
    
    # Rotación de logs
    LOG_RETENCION_DIAS = 30
    LOG_RETENCION_BACKUP = 90
    
    # Formato de logs
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # ==================== PARÁMETROS DE SEGURIDAD ====================
    
    # Intentos máximos de autenticación
    MAX_INTENTOS_AUTENTICACION = 3
    
    # Tiempo de bloqueo después de fallos
    TIEMPO_BLOQUEO_MINUTOS = 15
    
    # Longitud mínima de contraseñas
    LONGITUD_CONTRASENA_MINIMA = 12
    
    # ==================== PARÁMETROS DE VPS Y CUENTAS (SISTEMA 7) ====================
    
    # Regla de oro: 1 bot por VPS por PropFirm
    REGLA_ORO_BOT_VPS_PROPFIRM = True
    
    # Umbrales de uptime
    UPTIME_MINIMO = 0.95  # 95%
    UPTIME_WARNING = 0.90  # 90%
    
    # Límites de cuentas por VPS
    MAX_CUENTAS_POR_VPS = 5
    
    # ==================== PARÁMETROS DE INTELIGENCIA INFIMITA (SISTEMA 11) ====================
    
    # Fases recomendadas
    FASE_INVESTIGACION = 1
    FASE_PROTOTIPO = 2
    FASE_MVP = 3
    FASE_BETA = 4
    FASE_PRODUCCION = 5
    
    # Score de viabilidad mínimo para despachar
    SCORE_VIABILIDAD_MINIMO_DESPACHO = 70
    
    # ==================== MÉTODOS DE UTILIDAD ====================
    
    @classmethod
    def obtener_ruta(cls, *partes: str) -> str:
        """Obtiene una ruta completa combinando el directorio del proyecto."""
        return os.path.join(cls.DIR_PROYECTO, *partes)
    
    @classmethod
    def crear_directorios_necesarios(cls):
        """Crea todos los directorios necesarios si no existen."""
        directorios = [
            cls.DIR_LOGS,
            cls.DIR_DATASETS,
            cls.DIR_REPORTES,
            cls.DIR_TESTS,
            cls.DIR_DLRI,
            cls.DIR_INTELIGENCIA_INFINITA,
            os.path.join(cls.DIR_INTELIGENCIA_INFINITA, 'briefs'),
            cls.DIR_UVID,
            cls.DIR_GVCA,
            os.path.join(cls.DIR_AUTOMATIZACION, 'agentes', 'umi'),
            os.path.join(cls.DIR_AUTOMATIZACION, 'agentes', 'iniciales')
        ]
        
        for directorio in directorios:
            os.makedirs(directorio, exist_ok=True)
    
    @classmethod
    def obtener_configuracion_completa(cls) -> Dict:
        """Retorna toda la configuración como diccionario."""
        return {
            'rutas': {
                'directorio_proyecto': cls.DIR_PROYECTO,
                'directorio_nucleo': cls.DIR_NUCLEO,
                'directorio_automatizacion': cls.DIR_AUTOMATIZACION,
                'directorio_logs': cls.DIR_LOGS,
                'directorio_datasets': cls.DIR_DATASETS,
                'directorio_reportes': cls.DIR_REPORTES
            },
            'reputacion': {
                'niveles': cls.NIVELES_REPUTACION,
                'ajuste_tarea_exitosa': cls.AJUSTE_TAREA_EXITOSA,
                'ajuste_tarea_fallida': cls.AJUSTE_TAREA_FALLIDA,
                'score_inicial': cls.SCORE_INICIAL_AGENTE
            },
            'limites': {
                'limite_tokens_dia_haiku': cls.LIMITE_TOKENS_DIA_HAIKU,
                'limite_tokens_dia_sonnet': cls.LIMITE_TOKENS_DIA_SONNET,
                'limite_tokens_dia_opus': cls.LIMITE_TOKENS_DIA_OPUS,
                'limite_operaciones_dia': cls.LIMITE_OPERACIONES_DIA
            },
            'horarios': {
                'trading_inicio': cls.HORARIO_TRADING_INICIO,
                'trading_fin': cls.HORARIO_TRADING_FIN,
                'mantenimiento_inicio': cls.HORARIO_MANTENIMIENTO_INICIO,
                'mantenimiento_fin': cls.HORARIO_MANTENIMIENTO_FIN
            },
            'umbrales': {
                'drawdown_warning': cls.UMBRAL_DRAWDOWN_WARNING,
                'drawdown_critical': cls.UMBRAL_DRAWDOWN_CRITICAL,
                'tasa_exito_minima': cls.UMBRAL_TASA_EXITO_MINIMA,
                'errores_consecutivos': cls.UMBRAL_ERRORES_CONSECUTIVOS
            },
            'apis': {
                'anthropic_api_key': cls.ENV_ANTHROPIC_API_KEY,
                'groq_api_key': cls.ENV_GROQ_API_KEY,
                'gemini_api_key': cls.ENV_GEMINI_API_KEY,
                'telegram_bot_token': cls.ENV_TELEGRAM_BOT_TOKEN
            },
            'backtesting': {
                'winrate_minimo': cls.WINRATE_MINIMO,
                'profit_factor_minimo': cls.PROFIT_FACTOR_MINIMO,
                'max_drawdown_maximo': cls.MAX_DRAWDOWN_MAXIMO
            },
            'entrenamiento_rl': {
                'learning_rate': cls.PPO_LEARNING_RATE,
                'gamma': cls.PPO_GAMMA,
                'steps_minimo': cls.STEPS_ENTRENAMIENTO_MINIMO,
                'steps_recomendado': cls.STEPS_ENTRENAMIENTO_RECOMENDADO
            }
        }


# Instancia global de configuración
config = QuantumHiveConfig


def main():
    """Función principal para probar la configuración."""
    print("QuantumHive Config - Configuración Centralizada")
    print("=" * 60)
    
    # Crear directorios necesarios
    config.crear_directorios_necesarios()
    print("✅ Directorios creados/verificados")
    
    # Mostrar configuración completa
    cfg = config.obtener_configuracion_completa()
    print(f"\nDirectorio del proyecto: {cfg['rutas']['directorio_proyecto']}")
    print(f"Niveles de reputación: {list(cfg['reputacion']['niveles'].keys())}")
    print(f"Límite de operaciones por día: {cfg['limites']['limite_operaciones_dia']}")
    print(f"Horario de trading: {cfg['horarios']['trading_inicio']} - {cfg['horarios']['trading_fin']}")
    print(f"Winrate mínimo: {cfg['backtesting']['winrate_minimo'] * 100}%")
    
    print("\nConfiguración cargada correctamente.")


if __name__ == '__main__':
    main()

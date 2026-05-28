import os
import sys

BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'automatizacion', 'agentes')
SALIDA = os.path.join(os.path.dirname(__file__), '..', '..', 'INVENTARIO_TOTAL_QH.md')

DESCRIPCION_DIVISIONES = {
    'division_propfirms': (
        'Gestión de cuentas en prop firms. Monitoreo de drawdown, cumplimiento de rules, '
        'anti-detección de patrones algorítmicos, rotación de VPS, dispersión de entradas y selección de lotaje.'
    ),
    'division_fondeo': (
        'Gestión del programa de fondeo: challenges, cuentas fondeadas, cobro de fondeo, '
        'afiliaciones y onboarding de clientes.'
    ),
    'division_sala_inversion': (
        'Pool de capital, distribución de ganancias, sala de inversión visual, '
        'retiros y CEO de sala.'
    ),
    'division_uci': (
        'Unidad de Captación de Inteligencia: recolección de videos, procesamiento de PDFs, '
        'generación de CNN, base de conocimiento y recolección de traders.'
    ),
    'division_biblioteca_fabrica_bots': (
        'Fábrica de bots: control de calidad, pricing, catálogo, análisis de rendimiento, '
        'combinación de estrategias, walk-forward analysis, filtro de combinaciones, '
        'marketing de bots y recolección de estrategias.'
    ),
    'division_recursos_gratis': (
        'Recolección y administración de recursos gratuitos: GPUs, nubes, '
        'y API de consultas para la colmena.'
    ),
    'trading': (
        'GOAT BTC: agente de trading algorítmico para BTC/USD-SWAP en OKX. '
        'Incluye feeds, ejecutores, signal engine, scorer y terminal UI.'
    ),
    'agi_memory': (
        'Sistema de memoria persistente de AGI: GitHub Memory, Memory Manager, '
        'clasificador de intenciones y challenge mode.'
    ),
    'cerebro': (
        'Agente Cerebro: sistema de monitoreo central con detección de anomalías, '
        'API interna, constructor de contexto, estado global y lector de event bus.'
    ),
    'd12_crecimiento': (
        'División de crecimiento: AGI WhatsApp para atención al cliente.'
    ),
    'biblioteca_fabrica': (
        'Biblioteca de fábrica: repositorio de bots rentables y estrategias empaquetadas.'
    ),
    'data': (
        'Datos y reportes auxiliares de la colmena.'
    ),
    'agi_core': (
        'Núcleo del sistema AGI: LLM wrapper con rotación OpenRouter/Groq/Ollama, '
        'event bus, action router, approval gate, keys vault, memory loader, '
        'supabase client y voice processor.'
    ),
    'utils': (
        'Utilidades del sistema: generador de inventario, mapeador de empresa, '
        'convertidor ONNX, purga de archivos, seguridad, guardrail terminal y shadow backup.'
    ),
    'macro4': (
        'Estrategia MACRO4: filtro NY open, ingesta de datos y entrenamiento de modelo NY Predator.'
    ),
}

DESCRIPCION_AGENTES = {
    # PropFirms
    'agente_monitor_drawdown.py': 'Monitorea drawdown diario y máximo en cuentas de prop firms',
    'agente_compliance_propfirm.py': 'Verifica cumplimiento de reglas de cada prop firm',
    'agente_gestor_cuentas.py': 'Gestiona múltiples cuentas en prop firms',
    'agente_rotacion_vps.py': 'Rota VPS automáticamente para evitar detección',
    'agente_anti_deteccion.py': 'Evita detección de patrones algorítmicos por prop firms',
    'agente_dispersor_entradas.py': 'Dispersa entradas en el tiempo para evitar patrones sospechosos',
    'agente_selector_lotaje.py': 'Selecciona lotaje óptimo según saldo y reglas de cada prop firm',
    # Fondeo
    'agente_challenge.py': 'Gestiona challenges de fondeo (evaluación de traders)',
    'agente_cuentas_fondeadas.py': 'Administra cuentas fondeadas post-challenge',
    'agente_cobro_fondeo.py': 'Procesa cobros del programa de fondeo',
    'agente_afiliaciones.py': 'Gestiona programa de afiliados del fondeo',
    'agente_onboarding_cliente.py': 'Onboarding de nuevos clientes del programa de fondeo',
    # Sala Inversión
    'agente_pool_capital.py': 'Administra pool de capital colectivo',
    'agente_distribucion_ganancias.py': 'Distribuye ganancias entre participantes del pool',
    'agente_sala_visual.py': 'Dashboard visual de la sala de inversión',
    'agente_retiros.py': 'Procesa solicitudes de retiro de capital',
    'agente_ceo_sala.py': 'CEO virtual de la sala de inversión, toma decisiones ejecutivas',
    # UCI
    'agente_recolector_videos.py': 'Recolecta videos de traders e influencers',
    'agente_procesador_pdfs.py': 'Procesa y extrae información de PDFs',
    'agente_generador_cnn.py': 'Genera contenido para CNN (Cripto Noticias Network)',
    'agente_base_conocimiento.py': 'Mantiene base de conocimiento centralizada',
    'agente_recolector_traders.py': 'Recolecta datos y perfiles de traders',
    # Fábrica Bots
    'agente_control_calidad.py': 'Control de calidad de bots antes de publicación',
    'agente_pricing.py': 'Fija precios de bots según rendimiento y demanda',
    'agente_catalogo.py': 'Catálogo de bots disponibles para venta',
    'agente_analizador_rendimiento.py': 'Analiza rendimiento histórico de bots',
    'agente_combinador_estrategias.py': 'Combina estrategias para crear bots híbridos',
    'agente_estructurador_estrategias.py': 'Estructura y normaliza estrategias de trading',
    'agente_filtro_combinaciones.py': 'Filtra combinaciones de estrategias no viables',
    'agente_marketing_bots.py': 'Marketing y promoción de bots',
    'agente_recolector_estrategias.py': 'Recolecta estrategias de diversas fuentes',
    'agente_walk_forward_analysis.py': 'Realiza walk-forward optimization en estrategias',
    'fabrica_automatizada.py': 'Orquestador de la fábrica de bots automatizada',
    'procesar_bots_rentables.py': 'Procesa y clasifica bots rentables',
    # Recursos Gratis
    'agente_administrador_recursos.py': 'Administra recursos gratuitos de la colmena',
    'agente_gestor_nubes.py': 'Gestiona cuentas de nubes gratuitas',
    'agente_investigador_gpus.py': 'Investiga GPUs gratuitas disponibles',
    'agente_recolector_nubes.py': 'Recolecta ofertas de nubes gratuitas',
    'agente_recolector_recursos_varios.py': 'Recolecta recursos gratuitos varios',
    'agente_reporteador.py': 'Genera reportes de recursos disponibles',
    'api_agi_consultas.py': 'API de consultas para la colmena',
    # Trading / GOAT BTC
    'goat_btc.py': 'Agente principal de trading BTC/USD-SWAP en OKX Demo',
    'okx_feed.py': 'Feed de datos en tiempo real desde OKX',
    'okx_executor.py': 'Ejecutor de órdenes en OKX con risk $5',
    'signal_engine.py': 'Motor de señales basado en Bandas de Bollinger',
    'scorer.py': 'Sistema de puntuación de señales',
    'terminal_ui.py': 'Interfaz de terminal para monitoreo de GOAT BTC',
    'indicadores.py': 'Indicadores técnicos personalizados',
    'clasificador.py': 'Clasificador de condiciones de mercado',
    'binance_feed.py': 'Feed alternativo desde Binance (no utilizado actualmente)',
    'binance_executor.py': 'Ejecutor alternativo para Binance (no utilizado actualmente)',
    'ninjatrader_executor.py': 'Ejecutor para NinjaTrader (no utilizado actualmente)',
    'claude_chat.py': 'Chat conversacional con Claude para GOAT BTC',
    'session_summary.py': 'Resumen de sesión de trading',
    'señales_db.py': 'Base de datos de señales generadas',
    # AGI Core
    'llm_wrapper.py': 'Wrapper de LLM con rotación automática OpenRouter/Groq/Ollama',
    'event_bus.py': 'Bus de eventos con polling SQLite cada 5s y threading',
    'action_router.py': 'Router de acciones para AGI',
    'agent_bus.py': 'Bus de comunicación entre agentes',
    'approval_gate.py': 'Gate de aprobación para acciones críticas',
    'keys_vault.py': 'Bóveda segura de API keys',
    'memory_loader.py': 'Cargador de memoria persistente',
    'supabase_client.py': 'Cliente Supabase para persistencia cloud',
    'voice_processor.py': 'Procesador de voz usando Groq Whisper',
    # Cerebro
    'agi_telegram.py': 'AGI principal - interfaz Telegram, orquesta toda la colmena',
    'agente_cerebro.py': 'Handler universal de eventos con tabla cola_cerebro y prioridades',
    'handlers_colmena.py': 'Handlers de eventos de la colmena',
    'scheduler.py': 'Planificador de tareas periódicas (8 jobs activos)',
    'anomaly_detector.py': 'Detector de anomalías en el sistema',
    'api_interna.py': 'API interna para comunicación entre agentes',
    'context_builder.py': 'Constructor de contexto para AGI',
    'estado_global.py': 'Estado global del sistema',
    'event_bus_reader.py': 'Lector del event bus para monitoreo',
    # Utilidades
    'generar_inventario.py': 'Genera INVENTARIO_TOTAL_QH.md automáticamente',
    'mapear_empresa.py': 'Genera QUANTUM_ESTADO_MAESTRO.md escaneando el proyecto',
    'changelog.py': 'Registro de cambios del proyecto',
    'onnx_converter.py': 'Conversor de modelos a formato ONNX',
    'purga_paperclip.py': 'Limpieza de archivos temporales',
    'reorganizar_paperclip.py': 'Reorganización de estructura de archivos',
    'seguridad_archivos.py': 'Scripts de seguridad de archivos',
    'guardrail_terminal.ps1': 'Guarda de seguridad del terminal (HARD-SHIELD)',
    'shadow_backup.ps1': 'Backup automático cada hora',
    'github_memory.py': 'Memoria persistente entre sesiones vía GitHub',
    'memory_manager.py': 'Gestor de memoria persistente AGI UPGRADE v2.0',
    'intent_classifier.py': 'Clasificador de intenciones de mensajes',
    'challenge_mode.py': 'Modo desafío para pruebas de AGI',
    # Memoria
    'agi_whatsapp.py': 'AGI WhatsApp para atención al cliente (División Crecimiento)',
    # MACRO4
    'filtrar_ny_open.py': 'Filtro de apertura de NY para estrategia MACRO4',
    'ingesta_datos.py': 'Ingesta de datos para MACRO4',
    'train_ny_predator.py': 'Entrenamiento de modelo NY Predator',
}

def escanear():
    """Genera INVENTARIO_TOTAL_QH.md con descripciones semánticas."""
    total = 0
    with open(SALIDA, 'w', encoding='utf-8') as f:
        f.write('# INVENTARIO TOTAL QH — QuantumHive Algorithmic Trading\n\n')
        f.write('**Generado:** ' + __import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '\n\n')
        f.write('---\n\n')

        # Primero: archivos raíz de agentes/
        f.write('## Agentes raíz (orquestación central)\n\n')
        f.write('Agentes que operan directamente en la raíz de la colmena.\n\n')
        raices = sorted([a for a in os.listdir(BASE) if a.endswith('.py') and not a.startswith('_')])
        for a in raices:
            desc_a = DESCRIPCION_AGENTES.get(a, '')
            if desc_a:
                f.write(f'- **{a}** — {desc_a}\n')
            else:
                f.write(f'- {a}\n')
            total += 1
        f.write('\n---\n\n')

        for entry in sorted(os.listdir(BASE)):
            ruta = os.path.join(BASE, entry)
            if not os.path.isdir(ruta) or entry.startswith('_') or entry.startswith('.'):
                continue
            macro = entry.replace('_', ' ').title()
            desc = DESCRIPCION_DIVISIONES.get(entry, '')
            f.write(f'## {macro}\n\n')
            if desc:
                f.write(f'{desc}\n\n')
            archivos = sorted([a for a in os.listdir(ruta) if a.endswith('.py') and not a.startswith('_')])
            if not archivos:
                for sub in sorted(os.listdir(ruta)):
                    subruta = os.path.join(ruta, sub)
                    if os.path.isdir(subruta) and not sub.startswith('_'):
                        f.write(f'### {sub}\n\n')
                        subs = sorted([a for a in os.listdir(subruta) if a.endswith('.py') and not a.startswith('_')])
                        for a in subs:
                            desc_a = DESCRIPCION_AGENTES.get(a, '')
                            if desc_a:
                                f.write(f'- **{a}** — {desc_a}\n')
                            else:
                                f.write(f'- {a}\n')
                            total += 1
                        f.write('\n')
            else:
                for a in archivos:
                    desc_a = DESCRIPCION_AGENTES.get(a, '')
                    if desc_a:
                        f.write(f'- **{a}** — {desc_a}\n')
                    else:
                        f.write(f'- {a}\n')
                    total += 1
                f.write('\n')
        f.write('---\n\n')
        f.write(f'**Total: {total} archivos de agente en producción**\n')
    print(f'INVENTARIO_TOTAL_QH.md generado: {total} archivos')
    return total

if __name__ == '__main__':
    escanear()

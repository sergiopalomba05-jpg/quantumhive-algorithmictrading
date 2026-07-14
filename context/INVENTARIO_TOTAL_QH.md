# INVENTARIO TOTAL QH — QuantumHive Algorithmic Trading

**Generado:** 29/05/2026 05:11:51

---

## Agentes raíz (orquestación central)

Agentes que operan directamente en la raíz de la colmena.

- actualizar_render_llm.py
- agente_ai_town.py
- **agente_cerebro.py** — Handler universal de eventos con tabla cola_cerebro y prioridades
- agente_configurar_webhook_meta.py
- agente_crear_bot_telegram.py
- agente_experto_errores.py
- agente_gestor_gmail.py
- agente_git_commit.py
- agente_grafana_reporter.py
- agente_informes_logs.py
- agente_investigacion_modelos.py
- agente_limpiador_basura.py
- agente_llm_manager.py
- agente_optimizador_agentes.py
- agente_optimizador_procesos.py
- agente_recolector_inteligencia.py
- agente_render.py
- agente_seguridad.py
- agi_desktop.py
- **agi_telegram.py** — AGI principal - interfaz Telegram, orquesta toda la colmena
- **agi_whatsapp.py** — AGI WhatsApp para atención al cliente (División Crecimiento)
- check_logs.py
- configurar_agi_telegram.py
- **event_bus.py** — Bus de eventos con polling SQLite cada 5s y threading
- **handlers_colmena.py** — Handlers de eventos de la colmena
- investigar_groq.py
- keep_alive_render.py
- migrar_claves_vault.py
- **scheduler.py** — Planificador de tareas periódicas (8 jobs activos)

---

## Agi Memory

Sistema de memoria persistente de AGI: GitHub Memory, Memory Manager, clasificador de intenciones y challenge mode.

- **challenge_mode.py** — Modo desafío para pruebas de AGI
- **github_memory.py** — Memoria persistente entre sesiones vía GitHub
- **intent_classifier.py** — Clasificador de intenciones de mensajes
- **memory_manager.py** — Gestor de memoria persistente AGI UPGRADE v2.0

## Biblioteca Fabrica

Biblioteca de fábrica: repositorio de bots rentables y estrategias empaquetadas.

### bots_rentables


## Cerebro

Agente Cerebro: sistema de monitoreo central con detección de anomalías, API interna, constructor de contexto, estado global y lector de event bus.

- **anomaly_detector.py** — Detector de anomalías en el sistema
- **api_interna.py** — API interna para comunicación entre agentes
- **context_builder.py** — Constructor de contexto para AGI
- **estado_global.py** — Estado global del sistema
- **event_bus_reader.py** — Lector del event bus para monitoreo

## D12 Crecimiento

División de crecimiento: AGI WhatsApp para atención al cliente.

- **agi_whatsapp.py** — AGI WhatsApp para atención al cliente (División Crecimiento)

## Data

Datos y reportes auxiliares de la colmena.

## Division Biblioteca Fabrica Bots

Fábrica de bots: control de calidad, pricing, catálogo, análisis de rendimiento, combinación de estrategias, walk-forward analysis, filtro de combinaciones, marketing de bots y recolección de estrategias.

- **agente_analizador_rendimiento.py** — Analiza rendimiento histórico de bots
- **agente_catalogo.py** — Catálogo de bots disponibles para venta
- **agente_combinador_estrategias.py** — Combina estrategias para crear bots híbridos
- **agente_control_calidad.py** — Control de calidad de bots antes de publicación
- **agente_estructurador_estrategias.py** — Estructura y normaliza estrategias de trading
- **agente_filtro_combinaciones.py** — Filtra combinaciones de estrategias no viables
- **agente_marketing_bots.py** — Marketing y promoción de bots
- **agente_pricing.py** — Fija precios de bots según rendimiento y demanda
- **agente_recolector_estrategias.py** — Recolecta estrategias de diversas fuentes
- **agente_walk_forward_analysis.py** — Realiza walk-forward optimization en estrategias
- **fabrica_automatizada.py** — Orquestador de la fábrica de bots automatizada
- **procesar_bots_rentables.py** — Procesa y clasifica bots rentables

## Division Fondeo

Gestión del programa de fondeo: challenges, cuentas fondeadas, cobro de fondeo, afiliaciones y onboarding de clientes.

- **agente_afiliaciones.py** — Gestiona programa de afiliados del fondeo
- **agente_challenge.py** — Gestiona challenges de fondeo (evaluación de traders)
- **agente_cobro_fondeo.py** — Procesa cobros del programa de fondeo
- **agente_cuentas_fondeadas.py** — Administra cuentas fondeadas post-challenge
- **agente_onboarding_cliente.py** — Onboarding de nuevos clientes del programa de fondeo

## Division Propfirms

Gestión de cuentas en prop firms. Monitoreo de drawdown, cumplimiento de rules, anti-detección de patrones algorítmicos, rotación de VPS, dispersión de entradas y selección de lotaje.

- **agente_anti_deteccion.py** — Evita detección de patrones algorítmicos por prop firms
- **agente_compliance_propfirm.py** — Verifica cumplimiento de reglas de cada prop firm
- **agente_dispersor_entradas.py** — Dispersa entradas en el tiempo para evitar patrones sospechosos
- **agente_gestor_cuentas.py** — Gestiona múltiples cuentas en prop firms
- **agente_monitor_drawdown.py** — Monitorea drawdown diario y máximo en cuentas de prop firms
- **agente_rotacion_vps.py** — Rota VPS automáticamente para evitar detección
- **agente_selector_lotaje.py** — Selecciona lotaje óptimo según saldo y reglas de cada prop firm

## Division Recursos Gratis

Recolección y administración de recursos gratuitos: GPUs, nubes, y API de consultas para la colmena.

- **agente_administrador_recursos.py** — Administra recursos gratuitos de la colmena
- **agente_gestor_nubes.py** — Gestiona cuentas de nubes gratuitas
- **agente_investigador_gpus.py** — Investiga GPUs gratuitas disponibles
- **agente_recolector_nubes.py** — Recolecta ofertas de nubes gratuitas
- **agente_recolector_recursos_varios.py** — Recolecta recursos gratuitos varios
- **agente_reporteador.py** — Genera reportes de recursos disponibles
- **api_agi_consultas.py** — API de consultas para la colmena

## Division Sala Inversion

Pool de capital, distribución de ganancias, sala de inversión visual, retiros y CEO de sala.

- **agente_ceo_sala.py** — CEO virtual de la sala de inversión, toma decisiones ejecutivas
- **agente_distribucion_ganancias.py** — Distribuye ganancias entre participantes del pool
- **agente_pool_capital.py** — Administra pool de capital colectivo
- **agente_retiros.py** — Procesa solicitudes de retiro de capital
- **agente_sala_visual.py** — Dashboard visual de la sala de inversión

## Division Uci

Unidad de Captación de Inteligencia: recolección de videos, procesamiento de PDFs, generación de CNN, base de conocimiento y recolección de traders.

- **agente_base_conocimiento.py** — Mantiene base de conocimiento centralizada
- **agente_generador_cnn.py** — Genera contenido para CNN (Cripto Noticias Network)
- **agente_procesador_pdfs.py** — Procesa y extrae información de PDFs
- **agente_recolector_traders.py** — Recolecta datos y perfiles de traders
- **agente_recolector_videos.py** — Recolecta videos de traders e influencers

## Macro4

Estrategia MACRO4: filtro NY open, ingesta de datos y entrenamiento de modelo NY Predator.

- **filtrar_ny_open.py** — Filtro de apertura de NY para estrategia MACRO4
- **ingesta_datos.py** — Ingesta de datos para MACRO4
- **train_ny_predator.py** — Entrenamiento de modelo NY Predator

## Trading

GOAT BTC: agente de trading algorítmico para BTC/USD-SWAP en OKX. Incluye feeds, ejecutores, signal engine, scorer y terminal UI.

### goat_btc

- **goat_btc.py** — Agente principal de trading BTC/USD-SWAP en OKX Demo

---

**Total: 84 archivos de agente en producción**

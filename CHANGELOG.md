# CHANGELOG

Todos los cambios notables del proyecto.
## [2026-05-28] - FIX
**Commit:** ee93e4d2
**MÛdulo:** agi_telegram
- Contexto AGI: GitHub API autenticada para repo privado, fallback local, GITHUB_TOKEN en AGI Space, INVENTARIO regenerado, GH Action mejorado


## [2026-05-28] - FEAT
**Commit:** 381658a1
**MÛdulo:** arquitecto
- HF Space 2 (quantumhive-arquitecto): arquitecto.py, gestor_github.py, ejecutor_codigo.py, gestor_tareas.py. AGI detecta ordenes y las redirige al Arquitecto. POST /cerebro para recibir resultados.


## [2026-05-28] - FIX
**Commit:** e0fdfdf0
**MÛdulo:** agi_telegram
- Corregidos bugs en agi_telegram.py: generar_briefing_para_agi -> obtener_pendientes(), marcar_leidos(ids) con IDs reales


## [2026-05-28] - FEAT
**Commit:** ad28bc94
**MÛdulo:** agente_cerebro
- Agente Cerebro v3: handler universal con suscripcion a todos los eventos, tabla cola_cerebro con prioridad 1-3, notificador automatico de alertas criticas, endpoint /cerebro en AGI


## [2026-05-27] - FEAT
**Commit:** 31d5652d
**MÛdulo:** infra
- Deploy AGI Telegram a HF Spaces (Docker python:3.10-slim, puerto 7860, commit 835c3de)


## [2026-05-27] - FEAT
**Commit:** 31d5652d
**MÛdulo:** infra
- Deploy AGI Telegram a HF Spaces (Docker python:3.10-slim, puerto 7860, commit 835c3de)


## [2026-05-18] - FIX
**Commit:** b71d1efc
**MÛdulo:** goat_btc
- CVD OKX: corregido indice de side (row[4]=sell/buy). Balance bajo: contratos limitados a 1% del balance


## [2026-05-18] - FIX
**Commit:** b71d1efc
**MÛdulo:** goat_btc
- CVD OKX: corregido Ìndice de side (row[4]=sell/buy vs row[3]=timestamp). Balance bajo: contratos limitados a 1%% del balance disponible


## [2026-05-16] - FEAT
**Commit:** f795d74d
**MÛdulo:** goat_btc
- ninjatrader_executor.py creado ó OIF files para NT8 AT Interface. goat_btc.py migrado de Binance a NT executor con monitoreo SL/TP y precio via Binance public API


## [2026-05-16] - FIX
**Commit:** 8966ba59
**MÛdulo:** general
- BRIEF 2: migrado testnet.binancefuture.com + actualizado test script


## [2026-05-16] - FIX
**Commit:** 16ad527b
**MÛdulo:** general
- BRIEF 1+2: Gemini default engine + fix ejecucion Binance Testnet + test conexion


## [2026-05-16] - REFACTOR
**Commit:** 5dfdb019
**MÛdulo:** general
- SCALPER M1: goat_btc migrado a M1 (20/2.0) + signal_engine.py + fix import executor + ATR + monitoreo 5s + breakeven + contador trades/P&L/cooldown


## [2026-05-14] - FEAT
**Commit:** 8c7090b2
**MÛdulo:** goat_btc
- G.O.A.T PROTOCOL BTC/USD v1.0 - agente de analisis BTC en tiempo real con Binance WebSocket, BB 30/3.0, CVD real, ADX, scoring 0-100, clasificador rebote/surfeo, terminal rich, Event Bus + SQLite


## [2026-05-13] - FEAT
**Commit:** 3b6dd925
**MÛdulo:** agi_telegram, agi_desktop
- Audio largo: SYSTEM_PROMPT sin limite de lineas + max_tokens 1024 a 4096 para audios de 1-3 min


## [2026-05-13] - FIX
**Commit:** f5fb9f45
**MÛdulo:** agi_telegram, agi_desktop
- Audio invisible para el LLM: SYSTEM_PROMPT sin mencion de audio + sin prefijo, todo el audio es transparente en codigo


## [2026-05-13] - FIX
**Commit:** b75ce735
**MÛdulo:** agi_telegram, agi_desktop
- Audio: SYSTEM_PROMPT mas directo + prefijo [RESPUESTA POR VOZ AUTOMATICA] + timeout 30s para sendVoice


## [2026-05-13] - FIX
**Commit:** 1d0a6cc3
**MÛdulo:** agi_telegram, agi_desktop
- Audio: solo audio cuando envian voz (sin texto duplicado) + AGI Desktop con contexto completo (Event Bus, GitHub Memory, Agente Cerebro, v2)


## [2026-05-13] - FIX
**Commit:** 869e1a6c
**MÛdulo:** agi_telegram, agi_desktop
- SYSTEM_PROMPT sin prefijo [TIPO] + instruccion explicita de audio/vision


## [2026-05-13] - FEAT
**Commit:** a1c60b7a
**MÛdulo:** agi_telegram, agi_desktop
- Imagenes en AGI Telegram (Gemini vision) + AGI Desktop (Gradio) + SYSTEM_PROMPT actualizado


## [2026-05-13] - FEAT
**Commit:** b041bcbe
**MÛdulo:** agi_core
- Gemini como motor en LLM Wrapper (Groq -> Gemini -> OpenRouter -> Ollama) + agi_local.py CLI con archivos e imagenes + SYSTEM_PROMPT dice que AGI puede responder con audio


## [2026-05-13] - FIX
**Commit:** 843957ea
**MÛdulo:** agi_telegram
- diagnostico audio: prints en voice_processor y handler de audio + verificacion GROQ_API_KEY + logs de descarga y transcripcion


## [2026-05-13] - FIX
**Commit:** 92a3baec
**MÛdulo:** agi_telegram
- SYSTEM_PROMPT toxico eliminado, audio fallido guarda [Audio no disponible], early returns corregidos, historial sanitizado


## [2026-05-13] - FIX
**Commit:** 8786c64f
**MÛdulo:** agi_telegram
- AGI Telegram Fix Completo: sys.path corregido, tabla eventos creada, async removido, Procfile apunta a agi_telegram


## [2026-05-10] - REFACTOR
**Commit:** 8786c64f
**MÛdulo:** AGI_Voice
- MigraciÛn de transcripciÛn OpenAI Whisper a Groq Whisper (whisper-large-v3)


## [2026-05-10] - FIX
**Commit:** 8032b53e
**MÛdulo:** AGI/Cerebro
- Agente Cerebro (Bridge Event Bus -> AGI) + Real-time context + Audio Fix integration


## [2026-05-09] - FEAT
**Commit:** 1512e5de
**MÛdulo:** grafana
- Dashboard Grafana: Agregado panel Node Graph para visualizar la jerarquÌa Colmena -> Macrodivisiones -> Agentes estructuralmente


## [2026-05-09] - FEAT
**Commit:** 5c78e3a5
**MÛdulo:** grafana
- Dashboard Grafana: instalaciÛn local, datasource SQLite, 13 Macrodivisiones, agente reporter


## [2026-05-08] - FIX
**Commit:** d9aa0f71
**MÛdulo:** agi_telegram
- suero de la verdad: prompt anti-alucinacion, estado real de agentes y voice openai


## [2026-05-08] - FIX
**Commit:** e754553f
**MÛdulo:** agi_telegram
- rearquitectura CEO I, bus de realidad y whisper fallback


## [2026-05-03] - SOLUCI”N URGENTE: MOVER BOTS_RENTABLES A BOTS_TERMINADOS/ PARA PREVENIR P…RDIDA DE ARCHIVOS CRÕTICOS
**Commit:** 4242efb1
**MÛdulo:** general
- ['automatizacion/agentes/division_biblioteca_fabrica_bots/agente_marketing_bots.py', 'scripts/backup_proyecto.py']


## [2026-05-03] - AGREGAR SECCI”N DE WINDSURF CUSTOMIZATIONS EN CASCADE-SYSTEM-PROMPT.MD CON REGLAS, SKILLS Y WORKFLOWS
**Commit:** 9729d5eb
**MÛdulo:** general
- ['.windsurf/cascade-system-prompt.md']


## [2026-05-03] - AGREGAR REGLA OBLIGATORIA DE DOCUMENTACI”N EN ARCHIVOS MAESTROS DIOSMADRE A RULES, SKILLS Y WORKFLOWS
**Commit:** e08da3b0
**MÛdulo:** general
- ['.windsurf/rules/quantumhive.md', '.windsurf/skills/consultar-errores.md', '.windsurf/skills/registrar-cambio.md', '.windsurf/workflows/implementar-brief.md', '.windsurf/workflows/deploy-completo.md', '.windsurf/workflows/nuevo-agente.md']


## [2026-05-03] - CORRECCI”N ESTRUCTURA .WINDSURF + AGENTS.MD + HANDLER SE—AL_TRADING
**Commit:** 57349c9a
**MÛdulo:** general
- ['AGENTS.md', '.windsurf/rules/quantumhive.md', '.windsurf/skills/consultar-errores.md', '.windsurf/skills/registrar-cambio.md', '.windsurf/workflows/implementar-brief.md', '.windsurf/workflows/deploy-completo.md', '.windsurf/workflows/nuevo-agente.md', 'automatizacion/agentes/handlers_colmena.py']



## [2026-05-03] - FEAT
**M√≥dulo:** agentes
- Creados 26 nuevos agentes para M1 Trading Core y M4 F√°brica de Bots
- M1 D1: agente_monitor_drawdown, agente_compliance_propfirm
- M1 D2: agente_challenge, agente_cuentas_fondeadas, agente_cobro_fondeo, agente_afiliaciones, agente_onboarding_cliente
- M1 D2B: agente_gestor_cuentas, agente_rotacion_vps, agente_anti_deteccion, agente_dispersor_entradas, agente_selector_lotaje
- M1 D16: agente_pool_capital, agente_distribucion_ganancias, agente_sala_visual, agente_retiros, agente_ceo_sala
- M4 D8: agente_control_calidad, agente_pricing, agente_catalogo
- M4 D18: agente_recolector_videos, agente_procesador_pdfs, agente_generador_cnn, agente_base_conocimiento, agente_recolector_traders
- Scheduler: agregados jobs para ceo_dashboard, control_calidad, base_conocimiento
- Handlers: agregados handlers para sala_inversi√≥n, fabrica_bots, uci
## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M√≥dulo:** diosmadre
- Corregir numeraci√≥n duplicada de productos en PART_2A


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M√≥dulo:** diosmadre
- Agregar tracci√≥n actual al inicio del cap√≠tulo 13 de PART_3


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M√≥dulo:** diosmadre
- Agregar anexo de agentes al final de PART_1


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M√≥dulo:** diosmadre
- Agregar Software 3 FreeEngine en MACRO 13 de PART_1


## [2026-05-02] - FEAT
**Commit:** bc3cf27d
**M√≥dulo:** event_bus
- Event Bus completo con nucleo/event_bus.py, eventos_quantumhive.py y main_autonomo.py con suscripciones de agentes core


## [2026-05-02] - FEAT
**Commit:** 66144924
**M√≥dulo:** agentes
- Agente Recolector Inteligente centralizado con orquestaci√≥n de recolectores, normalizaci√≥n, deduplicaci√≥n y distribuci√≥n a Colmena


## [2026-05-02] - FEAT
**Commit:** a395d6e0
**M√≥dulo:** agentes
- Agente Optimizador de Agentes con escaneo, detecci√≥n de duplicados, an√°lisis de gaps funcionales y generaci√≥n de mapa de Colmena


## [2026-05-02] - FEAT
**Commit:** 4303e746
**M√≥dulo:** agentes
- Agente Optimizador de Errores y Procesos con memoria institucional SQLite, pre-carga de 5 errores hist√≥ricos, b√∫squeda de soluciones r√°pidas y reportes diarios




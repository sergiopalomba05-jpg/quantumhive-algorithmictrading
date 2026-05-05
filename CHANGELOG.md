# CHANGELOG

Todos los cambios notables del proyecto.
## [2026-05-03] - SOLUCI覰 URGENTE: MOVER BOTS_RENTABLES A BOTS_TERMINADOS/ PARA PREVENIR P蒖DIDA DE ARCHIVOS CR蚑ICOS
**Commit:** 4242efb1
**M骴ulo:** general
- ['automatizacion/agentes/division_biblioteca_fabrica_bots/agente_marketing_bots.py', 'scripts/backup_proyecto.py']


## [2026-05-03] - AGREGAR SECCI覰 DE WINDSURF CUSTOMIZATIONS EN CASCADE-SYSTEM-PROMPT.MD CON REGLAS, SKILLS Y WORKFLOWS
**Commit:** 9729d5eb
**M骴ulo:** general
- ['.windsurf/cascade-system-prompt.md']


## [2026-05-03] - AGREGAR REGLA OBLIGATORIA DE DOCUMENTACI覰 EN ARCHIVOS MAESTROS DIOSMADRE A RULES, SKILLS Y WORKFLOWS
**Commit:** e08da3b0
**M骴ulo:** general
- ['.windsurf/rules/quantumhive.md', '.windsurf/skills/consultar-errores.md', '.windsurf/skills/registrar-cambio.md', '.windsurf/workflows/implementar-brief.md', '.windsurf/workflows/deploy-completo.md', '.windsurf/workflows/nuevo-agente.md']


## [2026-05-03] - CORRECCI覰 ESTRUCTURA .WINDSURF + AGENTS.MD + HANDLER SE袮L_TRADING
**Commit:** 57349c9a
**M骴ulo:** general
- ['AGENTS.md', '.windsurf/rules/quantumhive.md', '.windsurf/skills/consultar-errores.md', '.windsurf/skills/registrar-cambio.md', '.windsurf/workflows/implementar-brief.md', '.windsurf/workflows/deploy-completo.md', '.windsurf/workflows/nuevo-agente.md', 'automatizacion/agentes/handlers_colmena.py']



## [2026-05-03] - FEAT
**M贸dulo:** agentes
- Creados 26 nuevos agentes para M1 Trading Core y M4 F谩brica de Bots
- M1 D1: agente_monitor_drawdown, agente_compliance_propfirm
- M1 D2: agente_challenge, agente_cuentas_fondeadas, agente_cobro_fondeo, agente_afiliaciones, agente_onboarding_cliente
- M1 D2B: agente_gestor_cuentas, agente_rotacion_vps, agente_anti_deteccion, agente_dispersor_entradas, agente_selector_lotaje
- M1 D16: agente_pool_capital, agente_distribucion_ganancias, agente_sala_visual, agente_retiros, agente_ceo_sala
- M4 D8: agente_control_calidad, agente_pricing, agente_catalogo
- M4 D18: agente_recolector_videos, agente_procesador_pdfs, agente_generador_cnn, agente_base_conocimiento, agente_recolector_traders
- Scheduler: agregados jobs para ceo_dashboard, control_calidad, base_conocimiento
- Handlers: agregados handlers para sala_inversi贸n, fabrica_bots, uci
## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M贸dulo:** diosmadre
- Corregir numeraci贸n duplicada de productos en PART_2A


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M贸dulo:** diosmadre
- Agregar tracci贸n actual al inicio del cap铆tulo 13 de PART_3


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M贸dulo:** diosmadre
- Agregar anexo de agentes al final de PART_1


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**M贸dulo:** diosmadre
- Agregar Software 3 FreeEngine en MACRO 13 de PART_1


## [2026-05-02] - FEAT
**Commit:** bc3cf27d
**M贸dulo:** event_bus
- Event Bus completo con nucleo/event_bus.py, eventos_quantumhive.py y main_autonomo.py con suscripciones de agentes core


## [2026-05-02] - FEAT
**Commit:** 66144924
**M贸dulo:** agentes
- Agente Recolector Inteligente centralizado con orquestaci贸n de recolectores, normalizaci贸n, deduplicaci贸n y distribuci贸n a Colmena


## [2026-05-02] - FEAT
**Commit:** a395d6e0
**M贸dulo:** agentes
- Agente Optimizador de Agentes con escaneo, detecci贸n de duplicados, an谩lisis de gaps funcionales y generaci贸n de mapa de Colmena


## [2026-05-02] - FEAT
**Commit:** 4303e746
**M贸dulo:** agentes
- Agente Optimizador de Errores y Procesos con memoria institucional SQLite, pre-carga de 5 errores hist贸ricos, b煤squeda de soluciones r谩pidas y reportes diarios




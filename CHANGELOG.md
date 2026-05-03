# CHANGELOG

Todos los cambios notables del proyecto.

## [2026-05-03] - FEAT
**Módulo:** agentes
- Creados 26 nuevos agentes para M1 Trading Core y M4 Fábrica de Bots
- M1 D1: agente_monitor_drawdown, agente_compliance_propfirm
- M1 D2: agente_challenge, agente_cuentas_fondeadas, agente_cobro_fondeo, agente_afiliaciones, agente_onboarding_cliente
- M1 D2B: agente_gestor_cuentas, agente_rotacion_vps, agente_anti_deteccion, agente_dispersor_entradas, agente_selector_lotaje
- M1 D16: agente_pool_capital, agente_distribucion_ganancias, agente_sala_visual, agente_retiros, agente_ceo_sala
- M4 D8: agente_control_calidad, agente_pricing, agente_catalogo
- M4 D18: agente_recolector_videos, agente_procesador_pdfs, agente_generador_cnn, agente_base_conocimiento, agente_recolector_traders
- Scheduler: agregados jobs para ceo_dashboard, control_calidad, base_conocimiento
- Handlers: agregados handlers para sala_inversión, fabrica_bots, uci
## [2026-05-03] - FIX
**Commit:** 0a0e5045
**Módulo:** diosmadre
- Corregir numeración duplicada de productos en PART_2A


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**Módulo:** diosmadre
- Agregar tracción actual al inicio del capítulo 13 de PART_3


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**Módulo:** diosmadre
- Agregar anexo de agentes al final de PART_1


## [2026-05-03] - FIX
**Commit:** 0a0e5045
**Módulo:** diosmadre
- Agregar Software 3 FreeEngine en MACRO 13 de PART_1


## [2026-05-02] - FEAT
**Commit:** bc3cf27d
**Módulo:** event_bus
- Event Bus completo con nucleo/event_bus.py, eventos_quantumhive.py y main_autonomo.py con suscripciones de agentes core


## [2026-05-02] - FEAT
**Commit:** 66144924
**Módulo:** agentes
- Agente Recolector Inteligente centralizado con orquestación de recolectores, normalización, deduplicación y distribución a Colmena


## [2026-05-02] - FEAT
**Commit:** a395d6e0
**Módulo:** agentes
- Agente Optimizador de Agentes con escaneo, detección de duplicados, análisis de gaps funcionales y generación de mapa de Colmena


## [2026-05-02] - FEAT
**Commit:** 4303e746
**Módulo:** agentes
- Agente Optimizador de Errores y Procesos con memoria institucional SQLite, pre-carga de 5 errores históricos, búsqueda de soluciones rápidas y reportes diarios




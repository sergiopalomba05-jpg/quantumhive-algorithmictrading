# MEMORIA MANUAL - REGLAS Y PENDIENTES

## REGLAS CRÍTICAS

### REGLA 1 - NUNCA PREGUNTAR "CONTINUE"
- Cuando el usuario me pide una tarea, ejecutarla DIRECTAMENTE
- NUNCA preguntar "continue", "quieres que continúe", o similar
- Ejecutar sin confirmación intermedia
- Esta regla es CRÍTICA - el usuario no quiere ver el botón "continue" NUNCA MÁS

### REGLA 2 - MEMORIA PERSISTENTE NO FUNCIONA
- El sistema de memoria persistente NO está recuperando conversaciones anteriores
- "No MEMORIES were retrieved" aparece en cada sesión nueva
- NO puedo confiar en el sistema de memoria automático
- DEBO usar memoria manual (este archivo) para registrar contexto importante

## PENDIENTES DE SESIONES ANTERIORES

### Pendiente: Flujos de LLM (ayer)
- Estado: NO RESUELTO
- Fecha: 1 de mayo 2026 (ayer)
- Contexto: Algo relacionado con flujos de LLM quedó pendiente
- Archivos relacionados:
  - automatizacion/agi_core/llm_wrapper.py
  - automatizacion/agentes/actualizar_render_llm.py
- Acción requerida: Investigar qué es este pendiente y resolverlo

### Pendiente: Event Bus Semana 2
- Estado: PENDIENTE
- Fecha: 2 de mayo 2026
- Contexto: Conectar agentes existentes al Event Bus
- Agentes activos: 26
- Ya conectados: 3 (optimizador_procesos, optimizador_agentes, recolector_inteligencia)
- Pendientes: 23 agentes para conectar
- Acción requerida: Conectar los 23 agentes restantes al Event Bus

## PROYECTO QUANTUMHIVE - ESTADO ACTUAL

### DÍA 4 - 3 Agentes Core COMPLETADOS
- ✅ agente_optimizador_procesos.py (commit a395d6e)
- ✅ agente_optimizador_agentes.py (commit 6614492)
- ✅ agente_recolector_inteligencia.py (commit bc3cf27)

### DÍA 1 - Event Bus COMPLETADO (Semana 1)
- ✅ nucleo/event_bus.py (commit 29639cf)
- ✅ nucleo/eventos_quantumhive.py (commit 29639cf)
- ✅ automatizacion/main_autonomo.py (commit 29639cf)
- ✅ Suscripciones de agentes core conectadas

### PENDIENTE: Flujos de LLM
- Fecha: 1 de mayo 2026
- Estado: INVESTIGACIÓN REQUERIDA

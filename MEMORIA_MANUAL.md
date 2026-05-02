# MEMORIA MANUAL - REGLAS Y PENDIENTES

## REGLAS CRÍTICAS

### REGLA 1 - NO EJECUTAR TAREAS AUTOMÁTICAMENTE
- NO ejecutar tareas automáticamente sin que el usuario o AGI lo pidan
- Esperar instrucciones explícitas del usuario o de AGI antes de ejecutar
- Esto es para evitar ejecutar tareas antes de estar completas
- La regla es: ESPERAR instrucciones, NO ejecutar automáticamente

### REGLA 2 - MEMORIA PERSISTENTE NO FUNCIONA
- El sistema de memoria persistente NO está recuperando conversaciones anteriores
- "No MEMORIES were retrieved" aparece en cada sesión nueva
- NO puedo confiar en el sistema de memoria automático
- DEBO usar memoria manual (este archivo) para registrar contexto importante

## PENDIENTES DE SESIONES ANTERIORES

### Pendiente: Flujos de LLM (ayer - 1 de mayo 2026)
- Estado: IDENTIFICADO
- Fecha: 1 de mayo 2026 (ayer)
- Contexto: agi_telegram.py tiene fallback a Anthropic directo con modelo incorrecto
- Archivo: automatizacion/agentes/agi_telegram.py
- Problema: Líneas 1187-1195 usan Anthropic directo con modelo "claude-sonnet-4-6" (no existe)
- Solución requerida: Corregir modelo a "claude-3-sonnet-20240229" o eliminar fallback
- Estado del wrapper: ✅ llm_wrapper.py está implementado y funcional
- Integración: ✅ agi_telegram.py ya usa llm_wrapper cuando disponible (líneas 1071-1087)
- Acción requerida: Corregir fallback en agi_telegram.py

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

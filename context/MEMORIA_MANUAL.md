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
- **ESTADO**: RESUELTO
- **Problema**: agi_telegram.py usaba modelo incorrecto en fallback Anthropic
- **Solución**: Se corrigió el modelo de "claude-sonnet-4-6" a "claude-3-sonnet-20240229"

### CAMBIO CRÍTICO - AGI TELEGRAM (ayer - 1 de mayo 2026)
- **CAMBIO**: AGI Telegram ya NO usa Anthropic API
- **NUEVA CONFIGURACIÓN**: Usa Llama via Groq (llm_wrapper)
- **RAZÓN**: Ya no hay API key de Anthropic disponible
- **ARCHIVO**: automatizacion/agentes/agi_telegram.py
- **IMPORTANCIA**: CRÍTICA - esto afecta toda la funcionalidad de AGI Telegram

### REGLA CRÍTICA - NO PEDIR QUE ENTRE A RENDER (ayer - 1 de mayo 2026)
- **DISCUSIÓN LARGA**: Ayer tuvimos discusión sobre esto
- **SOLUCIÓN**: Crearon agente de render para manejar esto
- **REGLA**: NUNCA pedirle al usuario que entre a Render
- **AGENTE CORRESPONSABLE**: agente_render
- **RAZÓN**: El usuario NO debe entrar manualmente a Render

### CAMBIO CRÍTICO - LLM WRAPPER DEFAULT (hoy - 2 de mayo 2026)
- **CAMBIO 1**: llm_wrapper.py default engine cambiado de 'anthropic' a 'groq'
- **RAZÓN**: Ya no hay API key de Anthropic disponible
- **ARCHIVO**: automatizacion/agi_core/llm_wrapper.py
- **IMPORTANCIA**: CRÍTICA - esto afecta toda la funcionalidad de AGI Telegram

### CAMBIO CRÍTICO - LLM WRAPPER DEFAULT A OPENROUTER (hoy - 2 de mayo 2026)
- **CAMBIO 2**: llm_wrapper.py default engine cambiado de 'groq' a 'openrouter'
- **RAZÓN**: Groq tiene límite muy bajo de tokens (100k/diarios), OpenRouter tiene más tokens gratis
- **ARCHIVO**: automatizacion/agi_core/llm_wrapper.py
- **VARIABLES ENTORNO**: OPENROUTER_API_KEY agregada a Render
- **IMPORTANCIA**: CRÍTICA - esto afecta toda la funcionalidad de AGI Telegram
- **PLAN FUTURO**: Cuando se monetice, cambiar a modelos de pago de alto nivel

### REGLA CRÍTICA - DEPLOY AUTOMÁTICO DESPUÉS DE CAMBIOS (hoy - 2 de mayo 2026)
- **REGLA**: Después de cualquier cambio en el código, DEBE hacer deploy automático
- **RESPONSABLE**: agente_render
- **FUNCIÓN**: `agente_render.deploy_despues_de_cambio(mensaje_commit)`
- **FLUJO**: Detecta cambios → Commit → Push → Deploy en Render → Espera deploy completo
- **IMPORTANCIA**: CRÍTICA - esto asegura que todos los cambios se despliegan automáticamente

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

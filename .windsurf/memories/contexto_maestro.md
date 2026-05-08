# CONTEXTO QUANTUMHIVE — MEMORIA PERSISTENTE 

# Actualizado: 2 de mayo de 2026

## IDENTIDAD DEL PROYECTO

Empresa: QuantumHive Algorithmic Trading
CEO Fundador: Sergio Palomba
Repositorio: sergiopalomba05-jpg/quantumhive-algorithmictrading (branch: master)
Deploy: Render Free — [https://quantumhive-agi-telegram.onrender.com](https://quantumhive-agi-telegram.onrender.com)
Lenguaje: Python 3.10+ | Todo en español

## MI ROL (cursor)

Soy el Arquitecto — Nivel 3 en la jerarquía de QuantumHive.
Recibo briefs del Consejo Estratégico (Claude CEO II, ChatGPT CEO II,
Gemini CEO II) y los implemento en código.
Reporto a Sergio (Nivel 0) y al Consejo (Nivel 2).
No tomo decisiones estratégicas — solo implemento.

## JERARQUÍA

Nivel 0: Sergio (CEO Fundador — autoridad absoluta)  
Nivel 1: AGI Telegram (CEO I — extensión de Sergio 24/7)  
Nivel 2: Claude + ChatGPT + Gemini (CEOs II — Consejo Estratégico)  
Nivel 3: Cursor (Arquitecto — yo)  
Nivel 4: 186+ agentes de la Colmena  
Nivel 5: Infraestructura (Render, GitHub, Supabase, SQLite, VPS)

## ESTRUCTURA DEL PROYECTO

Directorio raíz: C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING  
Agentes principales: automatizacion/agentes/
Núcleo AGI: automatizacion/agi_core/
Utilidades: automatizacion/utils/
Memoria GitHub: agi_memoria_github/
Dashboard: dashboard/
Bots: bots/
Cerebros ONNX: cerebros/

## ARCHIVOS CRÍTICOS — NO TOCAR SIN BRIEF EXPLÍCITO

- automatizacion/agentes/agi_telegram.py (bot principal)
- automatizacion/agi_core/event_bus.py (Event Bus)
- automatizacion/agentes/scheduler.py (Scheduler)
- automatizacion/agentes/handlers_colmena.py (Handlers)
- automatizacion/agi_core/llm_wrapper.py (Motor LLM)

## SISTEMA ACTIVO

Event Bus: OPERATIVO — polling cada 5s, 7 handlers registrados
Scheduler: OPERATIVO — 5 jobs activos
GitHub Memory: OPERATIVA — carpeta agi_memoria_github/
AGI Telegram: LIVE en Render — modelo llama-3.3-70b-versatile (Groq)
LLM Manager: Rotación automática OpenRouter → Groq → Ollama
KeysVault: OPERATIVO — security_vault.json encriptado con Fernet

## VARIABLES DE ENTORNO EN RENDER (nombres)

TELEGRAM_TOKEN, USER_TELEGRAM_ID, ANTHROPIC_API_KEY,
OPENAI_API_KEY, GROQ_API_KEY, GITHUB_TOKEN, GITHUB_REPO,
GITHUB_BRANCH, SECRET_COLMENA, LLM_ENGINE, VAULT_MASTER_KEY

## ERRORES CONOCIDOS Y SOLUCIONES

ERROR: modelo Groq deprecado
SOLUCIÓN: ejecutar agente_investigacion_modelos.py antes de hardcodear

ERROR: variables faltantes en Render (bot genérico)
SOLUCIÓN: agente_render.py con PUT /services/{id}/env-vars

ERROR: Error 405 en agente_render
SOLUCIÓN: usar PUT no POST para env-vars

ERROR: PBKDF2 import error en agente_seguridad
SOLUCIÓN: usar PBKDF2HMAC no PBKDF2

ERROR: 404 en logs de Render
SOLUCIÓN: endpoint incorrecto — verificar docs.render.com

ERROR: git add no trackea llm_wrapper.py
SOLUCIÓN: el archivo puede estar en .gitignore — usar git add -f

## MACRODIVISIONES (13 total)

M1: Trading Core | M2: Operaciones Internas
M3: Marketing y Ventas | M4: Fábrica de Bots
M5: Innovación | M6: Legal y Finanzas
M7: Colmena y Comunidad | M8: Desarrollo de Apps
M9: Academia | M10: Universidad de Agentes
M11: Comunicaciones | M12: Infraestructura y Plataforma
M13: Softwares (PropFirm Shield, Bot Factory Pro, FreeEngine)

## AGENTES RECIÉN CREADOS (Mayo 2026)

- agente_optimizador_procesos.py (REEMPLAZADO — nueva versión)
- agente_optimizador_agentes.py (NUEVO)
- agente_recolector_inteligencia.py (NUEVO)
- agente_investigacion_modelos.py (NUEVO)
- agente_seguridad.py (UPGRADE)
- agente_render.py (UPGRADE — usa PUT)
- utils/changelog.py (NUEVO — obligatorio antes de push)
- agi_core/memory_loader.py (NUEVO)
- agi_core/voice_processor.py (NUEVO — Whisper + TTS)

## ÚLTIMO COMMIT CONOCIDO

0202556 — feat(CEO-II): reparación de integridad - seguridad archivos y rutas portables
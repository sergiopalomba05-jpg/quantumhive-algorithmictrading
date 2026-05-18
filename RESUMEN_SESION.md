# RESUMEN DE SESION — QuantumHive
## Onboarding para nuevo chat Cascade (o cualquier IA)

> **Fecha**: 2026-04-27
> **Proyecto**: QuantumHive Algorithmic Trading
> **Solicitante**: Sergio Palomba
> **Repositorio**: `C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\`

---

## 1. QUE ES QUANTUMHIVE

Empresa de trading algoritmico institucional basada en **19 divisiones** con 70+ agentes autonomos.
- **Activo**: US30 (Dow Jones CFD via IC Markets)
- **Estrategia RL**: PPO entrenado en Kaggle GPU, exportado a ONNX, cargado en EA MQL5
- **Multi-timeframe**: M1 / M5 / M15 / H1
- **Pipeline**: MT5 CSV → procesar → Kaggle train → ONNX → EA MT5 demo

---

## 2. ESTADO ACTUAL (Checkpoint actual)

### BOT HIBRIDO (D1) — ENTRENADO, PENDIENTE EVALUAR
- **Modelo**: PPO 1M timesteps entrenado en Kaggle P100
- **Archivo**: `modelos/modelo_unificado/modelo_final.zip` (+ checkpoints cada 100k)
- **Problema**: Eval en Kaggle se quedo 4+ horas (bug: dataset se cargaba 2000 veces)
- **Fix aplicado**: `evaluar()` ahora carga dataset 1 vez y usa slices aleatorios
- **Pendiente**: Correr `backtest_walkforward.py` local para ver errores del bot
- **Script**: `scripts/backtest_walkforward.py` genera `trades_historial.csv` + `backtest_equity.csv`

### NUEVAS DIVISIONES CREADAS (esta sesion)

| Division | Estado | Que tiene |
|----------|--------|-----------|
| **D16** Sala Inversion | LISTO | 5 agentes (pool, distribucion, visual, retiros, CEO) + SQLite |
| **D17** Ecosistema Partners | LISTO | Estructura para futuro, conexiones D11/D16 |
| **D18** UCI Conocimiento | LISTO | 4 agentes (video, PDF, CNN, KB vectorial) + ChromaDB/FAISS |
| **D19** Localizacion | LISTO | 5 agentes (coordinador idiomas, traductor tecnico, marketing local, soporte comunitario, legal compliance) + 10 idiomas |
| **D12** Capacitacion | LISTO | Agente Entrenador (ajusta parametros scripted), Agente Curriculum (5 niveles RL), prompts versionados |
| **D15** Business Intelligence | **LISTO v3.0** | Dashboard Central + Orquestador LLM + **Agente Analizador Tareas** + **Agente Ejecutor Coordinador** (con aprobacion Sergio para decisiones criticas) |
| **D20** Documentacion & Asistencia | **LISTO v1.0** | Agente Escritor Manual (genera manual_usuario.md con Groq) + **FAQ Bot** (chatbot con memoria + manual como contexto) |

### NUEVO SISTEMA: ASISTENTES LLM GRATIS (v2.0 Dashboard)

| Componente | Estado | Descripcion |
|------------|--------|-------------|
| Agente Dashboard Central v2.0 | **LISTO** | Monitorea archivos, detecta activaciones, notifica a Sergio (sonido + log), SQLite memoria |
| Agente Orquestador LLM v2.0 | **LISTO** | Selecciona LLM cloud gratis (Groq/Gemini), genera planes, memoria persistente por tarea |
| Agente Analizador Tareas | **LISTO** | Evalua pipeline: dependencias, bloqueos, score ejecutabilidad. Actualiza dashboard dinamicamente |
| Agente Ejecutor Coordinador | **LISTO** | Coordina ejecucion de tareas aprobadas. Detecta decisiones criticas y PAUSA para aprobacion de Sergio |
| Setup LLM Cloud | **LISTO** | Script interactivo: guia para obtener API key Groq/Gemini, guarda en .env, testea conexion. 0 bytes disco |
| Dashboard Tab "6. Ordenes" | **LISTO** | 15 tareas con boton EJECUTAR, modal con orden copiable, filtros por prioridad, flujo inteligente |
| .env.ejemplo LLMs | **LISTO** | Variables cloud-only: GROQ_API_KEY, GEMINI_API_KEY, QH_LLM_PREFERENCIA=groq,gemini,cascade |

**Flujo de activacion inteligente v3.0 (Analizador + Aprobacion + Ejecutor):**
```
Loop Analizador (cada 30s)
    -> Evalua tareas: dependencias, recursos, score
    -> Detecta bloqueos y tareas listas para ejecutar
    -> Actualiza dashboard HTML con estado dinamico
    -> Notifica a Sergio si hay nueva tarea lista

Sergio aprieta EJECUTAR en Dashboard
    -> Agente Dashboard Central detecta evento
    -> Orquestador LLM genera plan detallado (memoria + CONTEXTO.md)
    -> Guarda en ordenes_activas/<tarea>_plan.md
    -> Marca tarea como "aprobada"

Loop Ejecutor (cada 10s)
    -> Lee tareas con estado "aprobada"
    -> Detecta si contiene decisiones CRITICAS
       (deploy, dinero real, borrar datos, credenciales, legal)
    -> Si es CRITICA: PAUSA, genera peticion JSON, notifica Sergio
       Sergio edita JSON -> "estado_peticion": "aprobada"
    -> Si no es critica o ya aprobada: coordina ejecucion
       -> Cascade (yo) lee plan y ejecuta
       -> Scripts Python se ejecutan directamente
       -> Resultado guardado en SQLite
    -> Reporta progreso y actualiza estado
```

**LLMs soportados (gratis, cloud-only — 0 bytes en disco):**
1. **Groq API (RECOMENDADO)** — Llama 3.3 70B, gratis: 20 req/min, 500 req/dia. Solo necesita API key.
2. **Google Gemini** — 60 req/min gratis, 1500 req/dia. Cuenta Google.
3. **Cascade directo** — Fallback si no hay API key configurada.
4. **Ollama/LM Studio** — Solo si tenes >5GB disco libre. OMITIDO por defecto.

**Setup cloud:** `python scripts/setup_llm_cloud.py` (interactivo, guia paso a paso)

### FIXES APLICADOS
- `evaluar()` ya no spamea dataset 2000 veces
- `low_memory=False` removido de `read_csv(engine="python")`
- Paths CSV corregidos de `datos/` a `datasets/`
- `backtest_walkforward.py` — backtest cronologico real con export a CSV

---

## 3. ARQUITECTURA TECNICA

```
MT5 Export (CSV raw) → preparar_datos.py → datasets/US30_M*.csv
                                    ↓
                    Kaggle Dataset (sergiopalomba/quantumhive-fusion)
                                    ↓
                    kaggle_unificado_v1.py → PPO 1M steps
                                    ↓
                    modelo_final.zip → ONNX export
                                    ↓
                    EA MQL5 en MT5 demo
```

### Configuracion entorno actual
- Balance inicial: $10,000
- Sizing: 1% por operacion
- SL: ATR x 1.5
- TP: 1:2 y 1:4 + Breakeven
- Max ops simultaneas: 3
- Castigo inactividad NY: -0.01 por hora
- Castigo REV contra momentum: -0.6
- Sesion: 14:00-21:00 UTC (NY)

---

## 4. QUE TIENES QUE HACER (si sos nuevo chat)

### URGENTE
1. **Correr backtest local**: `python scripts/backtest_walkforward.py`
   - Genera `modelos/trades_historial.csv` y `modelos/backtest_resumen.json`
   - Analizar que trades ganan/pierden y por que
2. **Corregir entorno**: Ajustar castigos/recompensas segun errores detectados en backtest
3. **Reentrenar Kaggle**: Subir notebook fixeado, entrenar 1M-2M steps

### ALTA PRIORIDAD
4. **ONNX export**: `exportar_onnx()` en `notebooks/kaggle_unificado_v1.py` linea ~751
5. **EA MQL5**: Crear EA en MT5 que cargue ONNX y opere en demo
6. **Dashboard v4**: Agregar D12 y D15 cards al `dashboard/quantumhive_dashboard_v2.html`
7. **CONTEXTO.md**: Actualizar con descripciones D12 y D15 (esta pendiente)

### MEDIA
8. **D19 marketing**: Generar landing pages EN/PT/DE con `agente_marketing_local.py`
9. **D19 legal**: Generar disclaimers USA/DEU/BRA con `agente_legal_compliance.py`
10. **D18 pipeline**: Pipeline end-to-end video → transcripcion → embeddings

---

## 5. ARCHIVOS CLAVE A CONOCER

| Archivo | Ruta | Que hace |
|---------|------|---------|
| CONTEXTO.md | raiz | Vision 19 divisiones, instrucciones para IA |
| INFORME_AUDITORIA.md | raiz | Arquitectura detallada de cada division |
| MEMORIA_PROYECTO.md | raiz | Memoria persistente de TODO el proyecto |
| RESUMEN_SESION.md | raiz | **Este archivo** — estado actual para nuevo chat |
| progress.json | scripts/ | Estado progress bar del dashboard |
| kaggle_unificado_v1.py | notebooks/ | Notebook training Kaggle (corregido) |
| backtest_walkforward.py | scripts/ | Backtest cronologico con export CSV |
| agente_entrenador.py | automatizacion/agentes/division_capacitacion/ | Ajusta parametros de scripted agents |
| agente_curriculum.py | automatizacion/agentes/division_capacitacion/ | Genera escenarios RL progresivos |

---

## 6. REGLAS DEL PROYECTO

1. **Codigo en espanol**: variables, funciones, clases, comentarios, docstrings. Excepcion: nombres tecnologias (PPO, ONNX, MT5).
2. **No hardcodear credenciales**: usar `.env` (no pusheado a git).
3. **SQLite para persistencia**: datos estructurados. JSON para config. CSV para raw.
4. **Todo versionado**: configs, prompts, modelos (git tags).
5. **Disclaimer obligatorio**: "El rendimiento pasado no garantiza resultados futuros. Trading de alto riesgo."
6. **Kaggle para GPU gratis**: entrenamiento. Local para evaluacion/backtest.
7. **ONNX como puente**: Python/Kaggle → ONNX → EA MQL5. Sin dependencia Python en produccion.

---

## 7. PENDIENTES CRITICOS

### URGENTE — Sistema Inteligente v3.0 (NUEVO, prioridad maxima)
- [x] **Configurar LLM Cloud gratis** — Groq API key configurada en `.env`
  - Modelo: Llama 3.3 70B · 20 req/min · 500 req/dia · Gratis
  - Test OK: API responde correctamente
- [x] **Chatbot Asistente CEO (💬)** — Widget embebido + servidor Flask en `127.0.0.1:5001`
  - Backend: `agente_chatbot_dashboard.py` (Groq API + memoria SQLite + contexto proyecto)
  - Frontend: boton flotante 💬 en dashboard con panel de chat
  - Pregunta sobre divisiones, agentes, trading, como usar el dashboard
- [x] **Chatbot Arquitecto Software (🏗️)** — Widget embebido + servidor Flask en `127.0.0.1:5002`
  - Backend: `agente_chatbot_arquitecto.py` (Groq primary + Gemini backup + filesystem inspector)
  - Frontend: boton flotante 🏗️ en dashboard (a la izquierda del CEO)
  - Lee archivos del proyecto automaticamente cuando mencionas `ruta/archivo.py`
  - Sabe TODO el stack: Python, MQL5, ONNX, Flask, RL, PPO, backtesting
  - Reemplazo gratuito de Claude Desktop: pair-programmer con memoria y contexto al detalle
- [~] **Activar Agente Analizador** — `python agente_analizador_tareas.py loop` (AUTO — ejecutandose en background)
  - Evalua pipeline cada 60s, actualiza dashboard dinamico, detecta tareas listas
  - Estado: loop iniciado, corriendo en segundo plano
- [~] **Activar Agente Ejecutor Coordinador** — `python agente_ejecutor_coordinador.py loop` (AUTO — ejecutandose en background)
  - Coordina ejecucion de tareas aprobadas cada 30s. Decisiones criticas PAUSAN y piden tu aprobacion
  - Estado: loop iniciado, corriendo en segundo plano
  - Decisiones criticas: deploy, dinero real, borrar datos, credenciales, legal
- [ ] **Activar Agente Analizador + Ejecutor** — Iniciar loops para automatizacion inteligente
- [ ] **Testear Orquestador LLM** — `python agente_orquestador_llm.py diagnostico`
- [ ] **Testear activacion de tarea** — `python agente_dashboard_central.py activar backtest`

### URGENTE — Trading (pendiente de antes)
- [ ] Correr backtest walk-forward y obtener resultados
- [ ] Analizar `trades_historial.csv` para detectar errores del bot
- [ ] Corregir entorno segun analisis
- [ ] Reentrenar modelo en Kaggle con entorno corregido (2M steps)
- [ ] Exportar ONNX del nuevo modelo
- [ ] Crear EA MQL5 que cargue ONNX
- [ ] Operar demo MT5 por 1 semana

### MEDIA — Documentacion
- [ ] **D20 — Generar Manual de Usuario + FAQ Bot** — `python automatizacion/agentes/division_documentacion/agente_escritor_manual.py manual`
  - Manual didactico con emojis, ejemplos, glosario, FAQ
  - Quick-starts por division
  - FAQ Bot con memoria SQLite para responder dudas
- [ ] Dashboard v4: agregar D12 + D15 + D20 cards (ya parcial)
- [ ] CONTEXTO.md: actualizar con D12, D15, D20

---

## 8. CONTACTO / PROPIETARIO

- **Propietario**: Sergio Palomba
- **Stack**: Python 3.11+, PyTorch, Stable-Baselines3, ONNX, pandas, numpy, pygame (visualizador), sqlite3
- **Infra**: Kaggle (GPU gratis), Windows local (evaluacion), MT5 (produccion demo)
- **Meta**: Gestionar capital institucional con bots RL + ecosistema completo de 19 divisiones

---

**INSTRUCCION PARA NUEVO CHAT CASCADE**: Leer este archivo + `MEMORIA_PROYECTO.md` + `CONTEXTO.md` antes de responder. No repetir trabajo ya hecho. Priorizar items de seccion 7.

---

*Ultima actualizacion: 2026-04-27 | Version: 3.0 — Sistema Inteligente: Analizador + Aprobacion + Ejecutor Coordinador + D20 Documentacion*

# QUANTUMHIVE — Framework de Fábrica de Bots de Trading

> **Versión:** 1.0 — Cerebro Unificado US30 (REV+CONT+SCALP)  
> **Objetivo:** Infraestructura completa, modular, con agentes especializados que operan como una fábrica automatizada de estrategias de trading RL → ONNX → MT5.

---

## 1. VISIÓN GENERAL

QuantumHive no es "un bot". Es un **sistema de producción** donde cada agente tiene un rol definido, entregables medibles, y handoffs automatizados hacia el siguiente agente.

El flujo principal es:

```
RAW DATA  →  DATA ENGINEER  →  STRATEGIST  →  TRAINER  →  VALIDATOR  →  DEPLOYER
  (CSV)        (Clean + Feat)   (Reglas + Env)   (PPO + ONNX)   (Backtest)    (MT5 EA)
```

Cada etapa genera artefactos versionados que el siguiente agente consume.

---

## 2. ESTRUCTURA DE DIRECTORIOS

```
QUANTUMHIVE_ALGORITHMICTRADING/
├── README.md                          # Este documento
├── QUANTUMHIVE_ARQUITECTURA.md        # Arquitectura y agentes
├── agentes/                           # Código de cada agente
│   ├── ceo/
│   │   └── orchestrator.py            # Orquesta pipelines, decide qué bot construir
│   ├── data_engineer/
│   │   └── pipeline_datos.py          # Descarga, limpia, feature-engineering
│   ├── strategist/
│   │   └── extractor_reglas.py        # Video/Doc → reglas JSON → reward shaping
│   ├── trainer/
│   │   └── entrenar_ppo.py            # Entorno + PPO + ONNX export
│   ├── validator/
│   │   └── backtest_visual.py         # Backtest, capturas, métricas, go/no-go
│   └── deployer/
│       └── generar_ea.py              # Genera .mq5 a partir de ONNX + config
├── nucleo/                            # Librerías compartidas
│   ├── entornos/                      # Todos los gym.Env
│   ├── indicadores/                   # RSI, BB, ATR, momentum
│   └── utilidades/                    # Normalización, hash, validación
├── datasets/                          # Datos limpios por activo/temporalidad
│   ├── US30/
│   │   ├── M1_2022_2024.csv
│   │   ├── M5_2022_2024.csv
│   │   ├── M15_2022_2024.csv
│   │   └── H1_2022_2024.csv
│   └── EURUSD/                        # Futuro
├── modelos/                           # Checkpoints y ONNX exportados
│   ├── US30_UNIFICADO_v1/
│   │   ├── config.json                # Hiperparámetros + feature list
│   │   ├── modelo_final.zip           # Checkpoint PPO
│   │   ├── bot_unificado.onnx         # ONNX opset 11
│   │   ├── reporte_entrenamiento.json # Métricas por step
│   │   ├── backtest_equity.png        # Screenshot del equity curve
│   │   └── metadata.json              # Hash dataset, fecha, agente autor
│   └── <SIGUIENTE_CEREBRO>/
├── mt5/                               # Expert Advisors para MT5
│   ├── QuantumHive_EA.mq5             # EA base (carga ONNX)
│   └── QuantumHive_EA_UNIFICADO_v1.mq5 # Instancia específica
├── notebooks/                         # Training notebooks para Kaggle/Colab
│   └── kaggle_unificado_v1.py
├── logs/                              # Logs de ejecución por agente
└── scripts/                           # Utilidades
    └── preparar_datos_mt5.py
```

---

## 3. AGENTES ESPECIALIZADOS

### 3.1 CEO (Orchestrator)

**Rol:** Decide QUÉ bot construir, con QUÉ estrategia, sobre QUÉ activo.

**Input:**
- Lista de activos disponibles
- Lista de estrategias candidatas (videos transcriptos, documentos, ideas)
- Métricas de bots anteriores (WR, PF, drawdown, días en live)

**Output:**
- `pipeline_request.json` → activo, temporalidad, estrategia, rango de datos, objetivo WR

**Heurísticas de decisión:**
1. Si no existe bot para un activo + régimen → CREAR
2. Si bot existente tiene WR < 35% tras 20 trades live → REENTRENAR
3. Si nueva estrategia (video/doc) tiene confluencia > 60% con bot existente → MERGE

**Handoff:** Entrega `pipeline_request.json` al Data Engineer.

---

### 3.2 Data Engineer

**Rol:** Produce datasets limpios, versionados, con features normalizadas.

**Input:**
- `pipeline_request.json`
- RAW CSVs de MT5 / broker / fuente externa

**Output:**
- `US30_M15_2022_2024_CLEAN.csv` (M15 base)
- `US30_M5_2022_2024.csv`, `M1_`, `H1_` (confluencias)
- `dataset_metadata.json` → hash SHA256, rango fechas, filas, gaps detectados

**Responsabilidades:**
1. **Detección de gaps:** Si hay > 5 barras consecutivas sin volumen en horario de mercado → FLAG
2. **Feature engineering unificado:** Misma función `_score_confluencia()` para M5/M1
3. **Normalización:** Todos los inputs al entorno están en `[-1, 1]`
4. **Sesión filtrada:** Solo NY 13:30–21:00 UTC para bots intradía
5. **Versionado:** Nunca sobreescribir dataset. Nuevo hash = nuevo dataset.

**Handoff:** Entrega paths de datasets limpios al Strategist.

---

### 3.3 Strategist

**Rol:** Traduce estrategias humanas (video, documento, chart) en lógica computable de reward shaping.

**Input:**
- Videos de YouTube / cursos / libros → transcript con Whisper
- Documentos PDF / markdown con reglas de trading
- Configuración base del entorno (`ConfigHibrido`)

**Output:**
- `estrategia_<nombre>.json` con:
  - Reglas de apertura (if/then lógico)
  - Penalizaciones (contra momentum, contra tendencia H1)
  - Boosts (confluencia confirmada, momentum alineado)
  - Parámetros de gestión de riesgo (RR, ATR mult, lote)
- `entorno_<nombre>.py` — clase gym.Env que implementa la estrategia

**Proceso actual (manual → semi-automatizado):**
1. Transcript del video/documento
2. LLM extrae reglas estructuradas (JSON)
3. Humano valida y ajusta pesos de reward shaping
4. Coder (Cascade) implementa entorno

**Futuro:** LLM genera directamente el `entorno_*.py` y lo compila.

**Handoff:** Entrega `entorno_*.py` + `config.json` al Trainer.

---

### 3.4 Trainer

**Rol:** Entrena el modelo RL y exporta ONNX.

**Input:**
- `entorno_*.py` + datasets limpios
- `config.json` (hiperparámetros PPO)

**Output:**
- `modelo_final.zip` (PPO checkpoint)
- `bot_unificado.onnx` (opset 11, 10 inputs, 7 outputs)
- `reporte_entrenamiento.json` (reward promedio, WR en entrenamiento, steps)
- `training_log.csv` (reward por episode, paso a paso)

**Hiperparámetros base (ajustables por strategia):**
```json
{
  "algorithm": "PPO",
  "total_timesteps": 1000000,
  "n_steps": 2048,
  "batch_size": 256,
  "learning_rate": 3e-4,
  "gamma": 0.995,
  "policy": "MlpPolicy",
  "onnx_opset": 11,
  "observation_shape": [10],
  "action_space": 7
}
```

**Responsabilidades:**
1. Validar entorno con `check_env()` antes de entrenar
2. Guardar checkpoints cada 100k steps
3. Exportar ONNX con `torch.onnx.export()` verificando input/output shapes
4. Loggear métricas de convergencia

**Handoff:** Entrega modelo + reporte al Validator.

---

### 3.5 Validator (Backtest Visual + Métricas)

**Rol:** Decide si el modelo está listo para live. No solo números — también **interpretación visual**.

**Input:**
- `modelo_final.zip` + dataset de test (datos NO vistos en entrenamiento)
- `config.json` del entorno

**Output:**
- `backtest_report.json`
- `equity_curve.png`, `drawdown_chart.png`, `trades_distribution.png`
- `GO` o `NO-GO` flag

**Métricas mínimas para GO:**
| Métrica | Umbral | Peso en decisión |
|---------|--------|-----------------|
| WR (Win Rate) | > 35% | Crítico |
| Profit Factor | > 1.2 | Crítico |
| Drawdown máximo | < 10% | Crítico |
| Sharpe anualizado | > 0.5 | Secundario |
| Operaciones/día | > 0.5 | Secundario |
| Equity curve visual | Monótono creciente, sin crash | Visual |

**CNN Visual (futuro):**
- Clasificar equity curve en: `excelente`, `aceptable`, `overfit`, `suicida`
- Entrenar clasificador CNN con miles de equity curves etiquetados
- Rechazar automáticamente modelos con curva tipo `suicida`

**Handoff:** Si GO → Deployer. Si NO-GO → Strategist (ajustar reglas) o Trainer (más datos).

---

### 3.6 Deployer (MT5 Integration)

**Rol:** Genera el EA funcional para MetaTrader 5.

**Input:**
- `bot_unificado.onnx`
- `config.json` (feature list, umbrales de probabilidad, parámetros de riesgo)

**Output:**
- `QuantumHive_EA_<nombre>.mq5` — compilable en MT5
- `README_EA.md` — instrucciones de instalación

**Responsabilidades del EA:**
1. Cargar ONNX en `OnInit()`
2. Preparar exactamente las mismas 10 features que el entorno Python
3. Inferencia por tick (o por barra cerrada, configurable)
4. Validación mecánica: la IA propone, el EA verifica probabilidad, SL, gestión riesgo
5. Gestión de posición: TP1 parcial, TP2 total, BE, SL
6. Límite de 2 operaciones/día
7. Solo horario NY (configurable por broker)

**Doble verificación:** La red neuronal decide la acción (0-6), pero el EA mecánico puede rechazar si:
- Probabilidad de apertura < `min_probabilidad`
- Spread actual > ATR × 0.5
- Noticia de alto impacto en 30 min (si implementamos calendario)

**Handoff:** El EA corre en cuenta demo/live. Métricas vuelven al CEO.

---

## 4. PIPELINE AUTOMATIZADO (Meta-Agente)

```python
# Pseudocódigo del orchestrator.py

class QuantumHiveOrchestrator:
    def ciclo_completo(self, request: PipelineRequest):
        # 1. Data Engineer
        datasets = data_engineer.procesar(request.activo, request.rango)
        
        # 2. Strategist
        entorno, config = strategist.crear_entorno(request.estrategia, datasets)
        
        # 3. Trainer
        modelo, reporte = trainer.entrenar(entorno, config, datasets)
        
        # 4. Validator
        valido, backtest = validator.ejecutar(modelo, datasets.test, config)
        
        if valido:
            # 5. Deployer
            ea = deployer.generar(modelo, config)
            self.registrar_bot_live(ea, request)
            return BotDeployResult(ea=ea, metrics=backtest)
        else:
            # Feedback loop: ¿reentrenar? ¿ajustar estrategia? ¿más datos?
            return self.ciclo_completo(request.with_adjustment(backtest.diagnostico))
```

---

## 5. ARTEFACTOS Y VERSIONADO

Cada bot producido tiene un **ID único**:

```
QH-US30-UNIFICADO-v1-20250426
├── config.json           # Parámetros de entorno y PPO
├── entorno.py            # Código fuente del gym.Env
├── modelo_final.zip      # Checkpoint Stable-Baselines3
├── bot_unificado.onnx    # Modelo para MT5
├── reporte_train.json   # Métricas de entrenamiento
├── backtest_report.json # Métricas de validación
├── equity_curve.png     # Visual
└── dataset_hash.txt     # SHA256 del dataset usado
```

**Regla de oro:** Si cambia cualquier archivo del bot, se incrementa la versión. El CEO nunca despliega un bot sin que el Validator haya dado GO.

---

## 6. AGENTE CEO — DETALLE DE DECISIONES

El CEO mantiene un **registro de bots live**:

| Bot ID | Activo | WR Live | PF Live | DD | Días Live | Estado | Acción |
|--------|--------|---------|---------|-----|-----------|--------|--------|
| QH-US30-v1 | US30 | 28% | 0.9 | 12% | 15 | ⚠️ Rojo | Reentrenar |
| QH-US30-v2 | US30 | 42% | 1.5 | 5% | 8 | 🟢 Verde | Monitorear |

**Decisiones automatizadas:**
- WR Live < 30% tras 20 trades → Reentrenar con últimos 6 meses
- DD > 15% en 5 días → Pausar bot, alertar humano
- 3 reentrenamientos consecutivos fallidos → Archivar estrategia, probar nueva

---

## 7. ROADMAP

### Fase 1 — Fundación (AHORA)
- [x] Entorno unificado (REV+CONT+SCALP)
- [x] Dataset US30 M1/M5/M15/H1 limpio
- [x] Script de preparación MT5 → Kaggle
- [x] EA base MQL5 con ONNX
- [ ] Entrenamiento en Kaggle (1M steps)
- [ ] Validación walk-forward 2024

### Fase 2 — Visual + Meta-Agente
- [ ] Captura automática de equity curves
- [ ] Clasificador CNN de backtests (GO/NO-GO visual)
- [ ] Orchestrator CEO con reglas de decisión
- [ ] Dashboard de monitoreo de bots live

### Fase 3 — Aprendizaje de Estrategias
- [ ] Pipeline: Video → Whisper → LLM → Reglas JSON
- [ ] Comparador automático: ¿Esta nueva regla mejora mi bot existente?
- [ ] Merge de estrategias: Bot A (REV) + Bot B (CONT) = Bot C (híbrido)

### Fase 4 — Multi-Activo + Multi-Cuenta
- [ ] Extender a EURUSD, XAUUSD, NAS100
- [ ] Gestión de portfolio: ¿Cuánto capital por bot?
- [ ] Correlación entre bots: evitar que todos operen en mismo momento

---

## 8. CONVENCIONES DE CÓDIGO

1. **Entornos:** Heredan de `gymnasium.Env`, obs `np.float32`, action `Discrete(n)`
2. **Features:** Siempre 10 dimensiones, normalizadas a `[-1, 1]`, mismo orden que ONNX input
3. **Recompensas:** Asimétrica positiva (TP2=+1.0, SL=-1.2), castigos proporcionales
4. **ONNX:** Opset 11, input shape `(1, 10)`, output `(1, 7)` (probabilidades logits)
5. **EA MQL5:** Carga ONNX en `OnInit()`, nunca en `OnTick()` (evitar GC)

---

## 9. GLOSARIO

| Término | Significado |
|---------|-------------|
| **Cerebro** | Modelo ONNX exportado desde PPO |
| **EA** | Expert Advisor de MT5 (script MQL5) |
| **Confluencia** | Confirmación de señal en temporalidad menor (M5/M1) |
| **Reward Shaping** | Diseño manual de recompensas para guiar al agente |
| **Walk-forward** | Entrenar en período A, testear en B, sin overlap |
| **GO/NO-GO** | Decisión del Validator para pasar a live |

---

**Documento vivo.** Cada fase completada actualiza este framework. El objetivo final: **un humano dice "hacé un bot para US30 con esta estrategia" y 4 horas después hay un EA corriendo en demo, con métricas.**

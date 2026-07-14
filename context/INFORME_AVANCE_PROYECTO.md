# INFORME DE AVANCE — QuantumHive Trading Systems
## Fecha: 2026-04-26 | Estado: Pivot estratégico hacia arquitectura 2-bot híbrido

---

## 1. VISIÓN EMPRESARIAL

**QuantumHive** es una empresa de trading algorítmico basada en:
- **Colmena de agentes IA** organizados por divisiones (P0-P5)
- **Bots de trading** entrenados con RL (PPO/RecurrentPPO) sobre datos institucionales
- **Automatización completa** desde adquisición de datos hasta ejecución en MT5
- **Estrategia de apilamiento**: Reversión + Continuación + Scalper coordinados

**Meta inmediata**: Tener 1-2 bots rentables operando en demo → pasar a real → generar cashflow para escalar.

---

## 2. LO QUE FUNCIONA ✅

### Infraestructura Base
| Componente | Estado | Detalle |
|------------|--------|---------|
| **Bus de datos** | ✅ Listo | `data/bus_de_datos.json` — IPC central |
| **Kill-switch** | ✅ Listo | `STOP.txt` + semáforo en scheduler |
| **Scheduler** | ✅ Listo | `scheduler.py` con jobs cron y semáforo |
| **15 Divisiones** | ✅ Listo | Documentadas en `CONTEXTO.md` y `AGENTES.md` |
| **Agentes P0** | ✅ Listo | Monitoreo, dashboard, alertas, supervisor, bienvenida |
| **Agentes P1** | ✅ Listo | Challenge, cuentas fondeadas, gestor grupos, closer, backup, métricas |
| **Agentes P2** | ✅ Listo | Métricas trading, entrenador bots, CEO estratégico, cobros, retención, **mecánico bots** |
| **Pipeline datos** | ✅ Listo | `preparar_dataset_institucional.py` con CSVs MT5 |
| **EA MQL5 v2** | ✅ Listo | `QuantumHiveEA_v2.mq5` con 4 bots ONNX |

### Datos e Indicadores
- ✅ Fusión multitemporal (M1, M5, M15, H1, H4, D1)
- ✅ 14+ features técnicas: RSI, EMA, BB% (Bollinger %B), BBW (BandWidth), ATR, ADX, MACD
- ✅ Confluencias multitemporales
- ✅ Dataset exportable a Parquet/CSV

---

## 3. LO QUE FALLÓ ❌ (Lecciones Clave)

### v2 Kaggle — Entrenamiento (Abril 2026)
```
madre        | WR=56.46% | PF=1.00 | MR=-0.0007
reversion    | WR=57.10% | PF=0.91 | MR=-0.0117  ← Pierde
continuacion | WR=58.89% | PF=0.92 | MR=-0.0082  ← Pierde
scalper      | WR=66.62% | PF=1.87 | MR=0.0822   ← Gana, probable overfit
```

**Diagnóstico:**
1. **4 entornos aislados** — cada bot tenía su balance virtual, sin coordinación real
2. **Subsets de entrenamiento** — Reversión entrenó solo en RSI<30/>70, nunca vió mercado "normal"
3. **Horizon fijo 60 barras** — cerraba trades prematuramente, matando la magia del apilamiento
4. **Sin trailing SL real** — SL estático, sin BE ni gestión profesional
5. **Sin costos** — sin modelar spread, comisión, swap
6. **Export ONNX falló** — faltaba `onnxscript`, typo `iterid` → `iterdir`

**Veredicto:** v2 no sirve para producción. Es baseline para entender qué NO hacer.

---

## 4. PIVOT ESTRATÉGICO → ARQUITECTURA 2-BOT HÍBRIDO

### Por qué cambiamos de enjambre 4-bot a 2-bot híbrido

| Problema v2 | Solución 2-bot |
|-------------|--------------|
| 4 entornos aislados | **1 entorno por bot**, entrenado en dataset COMPLETO |
| Subsets (cada bot ve solo su régimen) | **Todos ven todo**, filtro de régimen en el EA, no en entrenamiento |
| Madre + 3 hijos complejos | **2 bots independientes** + agente mecánico coordinador |
| Horizon 60 fijo | **Trailing SL + BE + TP2 dinámico** (hasta 240 barras) |
| Cada bot cierra cuando quiere | **Gestión centralizada** en EA MQL5 |
| Scalper opera solo | **Scalper es trigger de Continuación** (no bot separado) |

### Bots Definidos

#### Bot A: REVERSIÓN (Mean Reversion)
- **Trigger**: Precio toca banda de Bollinger + RSI extremo + mecha visible
- **Entrada**: LIMIT en banda (no market, para mejor precio)
- **Gestión**: 
  - SL inicial: 150 pts (1.5 ATR)
  - Posición 1: TP 1:2 (300 pts), cierra 50% lotaje
  - Posición 2: Trailing SL desde BE, objetivo 1:4 (600 pts)
- **Filtros**: Solo apertura NY, BB% < 0.05 o > 0.95, RSI < 25 o > 75

#### Bot B: CONTINUACIÓN (Trend Following)
- **Trigger**: ADX > 25 + MACD cruce + precio rompe banda con cuerpo (no mecha)
- **Entrada**: MARKET en ruptura
- **Gestión**:
  - SL inicial: 150 pts (1.5 ATR)
  - Posición 1: TP 1:2, cierra 50%
  - Posición 2: Trailing, objetivo 1:4
- **Filtros**: Solo cuando BBW > 0.10 (bandas expandidas), momentum confirmado
- **Habilita Scalper**: Cuando Continuación está en profit > 1:1, EA abre micro-posiciones M1 en momentum

### Coordinación (Agente Mecánico)
- Solo 1 bot puede abrir nueva posición por vez
- Si Reversión tiene pos abierta, Continuación no abre nueva (pero puede "sumarse" al mismo lado si régimen cambia)
- Drawdown por bot: max 3% diario. Global: max 6%.
- Si WR diario < 40% después de 10 trades → pausar bot hasta siguiente sesión

---

## 5. ARQUITECTURA TÉCNICA ACTUAL

```
┌─────────────────────────────────────────┐
│           COLMENA DE AGENTES            │
│  (P0-P5 organizados, con bus de datos)  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      AGENTE MECÁNICO DE BOTS            │
│  - Carga ONNX según régimen             │
│  - Gestiona kill-switch por bot         │
│  - Monitorea DD y WR en tiempo real     │
│  - Reporta al bus cada minuto           │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         EA MQL5 — QUANTUMHIVE           │
│  ┌─────────┐  ┌─────────────┐            │
│  │  REV    │  │    CONT     │            │
│  │ ONNX    │  │   ONNX      │            │
│  │ Trailing│  │  Trailing   │            │
│  │ SL/BE   │  │   SL/BE     │            │
│  │ TP1/TP2 │  │  TP1/TP2    │            │
│  └─────────┘  └─────────────┘            │
│         │           │                    │
│         └─────┬─────┘                    │
│               ▼                         │
│        ┌─────────────┐                   │
│        │  SCALPER    │  ← Solo cuando   │
│        │  (micro)    │    CONT en +1:1  │
│        └─────────────┘                   │
│                                         │
│  Filtros: NY Session, DD Global,        │
│  Kill-switch, Horario noticias          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│              MT5 / BROKER               │
│  Ejecución, slippage, datos ticks       │
└─────────────────────────────────────────┘
```

---

## 6. ARCHIVOS CLAVE DEL PROYECTO

| Ruta | Propósito | Estado |
|------|-----------|--------|
| `notebooks/kaggle_hibrido_retrain.py` | Script Kaggle para 1 bot híbrido (caballito batalla) | 🆕 Creado |
| `notebooks/kaggle_v3_enjambre.py` | Script Kaggle para enjambre v3 (reserva) | 🆕 Creado |
| `notebooks/preparar_dataset_institucional.py` | Pipeline CSV → Parquet con features | ✅ |
| `ea_mql5/PlantillaEAHibrido.mq5` | EA base con ONNX + trailing | ✅ (v1) |
| `ea_mql5/QuantumHiveEA_v2.mq5` | EA con 4 bots (deprecar) | ✅ |
| `automatizacion/agentes/trading/agente_mecanico_bots.py` | Coordinador mecánico | 🆕 Creado |
| `data/bus_de_datos.json` | IPC central | ✅ |
| `CONTEXTO.md` | 15 divisiones empresa | ✅ |
| `AGENTES.md` | Inventario agentes | ✅ |

---

## 7. PRÓXIMOS PASOS (Prioridad)

### Fase 1: Bot Reversión Funcional (Esta semana)
1. ✅ Armar script Kaggle para reentrenar con datos institucionales
2. ⬜ Subir a Kaggle, entrenar con GPU V100
3. ⬜ Validar backtest offline con trailing SL real
4. ⬜ Exportar ONNX válido (opset 12)
5. ⬜ Integrar en EA MQL5 PlantillaEAHibrido.mq5
6. ⬜ Test en Strategy Tester MT5 (visual)
7. ⬜ Demo account 2 semanas

### Fase 2: Bot Continuación + Scalper (Siguiente semana)
1. ⬜ Entrenar Bot Continuación con mismo dataset
2. ⬜ Definir trigger exacto para scalper (micro-posiciones)
3. ⬜ Coordinar ambos en EA MQL5
4. ⬜ Test conjunto en demo

### Fase 3: Agente Mecánico + Dashboard (Paralelo)
1. ✅ Crear agente mecánico de bots
2. ⬜ Dashboard visual con avatares (HTML/Streamlit)
3. ⬜ Conectar agente a MT5 vía ZeroMQ
4. ⬜ Automatizar reporte diario

### Fase 4: Escalar Empresa
1. ⬜ Challenge de fondeo (FTMO/PropFirm)
2. ⬜ Señales de pago (Telegram/WhatsApp)
3. ⬜ Community Management

---

## 8. PROMPTS RECOMENDADOS PARA CLAUDE (Cascade)

### Prompt Tipo A: Entrenamiento Bot
```
"Necesito entrenar el Bot [Reversión/Continuación] en Kaggle. 
El dataset es datatb_fusion.parquet con features [lista]. 
El entorno debe tener: SL ATR×1.5, TP1 1:2, TP2 1:4 con trailing desde BE, 
horizon 240 barras, costos spread 0.02% + comisión 0.01%. 
Entrenar con PPO, 500k steps, GPU V100. Exportar ONNX opset 12. 
Validar con backtest offline mostrando equity curve y drawdown."
```

### Prompt Tipo B: EA MQL5
```
"Actualizar PlantillaEAHibrido.mq5 para cargar 2 modelos ONNX: 
bot_reversion.onnx y bot_continuacion.onnx. 
Cada uno con su propia observación (14 features). 
Coordinación: solo 1 abre por vez, trailing SL dinámico, 
BE después de TP1, cierre parcial 50% en TP1. 
Filtro horario NY 14:00-21:00 UTC. Kill-switch global."
```

### Prompt Tipo C: Dashboard Visual
```
"Crear dashboard HTML/Streamlit con avatares para cada agente de la colmena. 
Mostrar: estado bots (activo/pausado/stopped), equity curve, WR diario, 
DD actual, régimen de mercado. Estilo cyberpunk/fintech. 
Actualizar en tiempo real leyendo bus_de_datos.json."
```

### Prompt Tipo D: Debug Kaggle
```
"El notebook Kaggle da error [X] en celda [Y]. 
Diagnóstico: [descripción]. Necesito fix profesional, no workaround. 
Prioridad: que el entrenamiento termine y exporte ONNX válido."
```

---

## 9. MÉTRICAS OBJETIVO

| Métrica | Bot Reversión | Bot Continuación | Combinado |
|---------|---------------|------------------|-----------|
| WinRate | > 55% | > 50% | — |
| Profit Factor | > 1.3 | > 1.2 | > 1.5 |
| Max Drawdown | < 3% diario | < 4% diario | < 6% global |
| Trades/día | 2-4 | 1-3 | 3-6 |
| Expectancy | > 0.5R | > 0.3R | > 0.6R |
| Sharpe (demo) | > 1.0 | > 0.8 | > 1.2 |

---

## 10. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Overfitting en entrenamiento | Alta | Alto | Walk-forward validation, train/test temporal |
| Slippage en vivo vs backtest | Media | Medio | Test en demo 2 semanas mínimo |
| Broker bloquea EA | Baja | Alto | Tener 2 brokers listos |
| DD > 6% en demo | Media | Alto | Kill-switch automático, reducir lotaje 50% |
| Datos no estacionarios | Alta | Medio | Reentrenar mensual con últimos 6 meses |

---

## 11. DECISIONES PENDIENTES DEL CEO (Sergio)

1. **¿Confirmamos 2-bot híbrido como MVP?** (vs seguir con enjambre 4-bot)
2. **¿Broker para demo?** (FTMO, Darwinex, IC Markets)
3. **¿Capital inicial demo?** ($10k, $50k, $100k)
4. **¿Fecha target para primer trade en real?** (sugerido: 30 días después de WR > 55% en demo)

---

*Informe generado por Cascade (AI Coding Assistant) para QuantumHive Trading Systems.*
*Próxima actualización: después del primer entrenamiento v3-híbrido en Kaggle.*

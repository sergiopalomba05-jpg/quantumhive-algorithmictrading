# CONTEXTO TECNICO — QuantumHive

## Arquitectura 3+1 Modelos

Sistema hibrido de trading algoritmico basado en Reinforcement Learning (PPO) + CNN visual + reglas mecanicas.

### 1. EntornoMadre

**14 features** (macro H1/H4/D1/W1 + estado operativo). Accion {REVERSIÓN(0), CONTINUACIÓN(1), SCALPER(2)}. Sin opcion "no operar". NY obligatorio.

El Madre clasifica QUE operar, nunca SI operar.

**Features:**
1. BBW H1
2. BBW H4
3. Pendiente EMA50 H1
4. RSI(14) H1
5. Estructura H4 (0-3)
6. Tendencia D1 EMA50
7. Pos vs EMA200 D1
8. Dist S/R D1
9. Tendencia W1 EMA50
10. Pos vs EMA200 W1
11. Dist S/R W1
12. Score confluencia
13. Ops hoy
14. PnL dia

### 2. EntornoReversión

**15 features**, activado solo por Madre. Confirmaciones M5/M1 en observation.

Condiciones: toca banda + mecha, RSI extremo, BBW plano, confluencia M5/M1.
- SL ~150 pts
- TP 300-600

### 3. EntornoContinuación

**17 features**, activado solo por Madre. Confirmaciones M5/M1 en observation.

Condiciones: cuerpo fuera BB, BBW expandiendose, RSI zona tendencia, EMA50/200.
- SL ~150 pts
- TP 300-600

### 4. EntornoScalperM5 (Autónomo)

**19 features** (6 M5 context + 7 M1 timing + 6 estado secuencia). AUTONOMO del Bot Madre.

- Operaciones M1 cortas: SL ~50 pts (ATR×1.2), TP ~100 pts (ratio 1:2)
- Trailing stop sube 0.8 ATR cuando avanza 1 ATR
- Secuencia interes compuesto 3-5 trades:
  - Trade 1 = 1% riesgo (solo si M5 y M1 confirman)
  - Trade 2 = 0.5% riesgo (M5 sigue surfeando + M1 pullback confirmado)
  - Trade 3+ = 0.25% riesgo (mismas condiciones)
  - Total acumulado maximo: 1.75% riesgo
- Max 5 trades/secuencia, max 2 secuencias/dia
- Solo NY

---

## Score Definitivo 0-160

**Maximo teorico:** 160 (sin correlacion cruzada entre activos).
**Minimo para operar:** 60 (baja a 50 solo en emergencia diaria si < 2 ops).

### Componentes del Score

| Componente | Score | Detalle |
|------------|-------|---------|
| RSI extremo | +20 | <20 o >80 |
| Toque BB | +20 | Low <= BB inferior / High >= BB superior |
| BBW expansion | +10 | BBW > percentil 80% |
| M5 confirma | +15 | Setup valido en M5 |
| M1 confirma | +10 | Setup valido en M1 |
| EMAs | +15 | Posicion relativa EMA50/200 |
| Cruce M5 | +10 | Confirmacion de cruce |
| Sentimiento | +25 | Algoritmo de sentimiento |
| Regimen | +10 | Tendencia macro identificada |
| Sesion correcta | +10 | Dentro de ventana NY |
| O/D fresca | +35 | Order block sin testear |
| Cerca O/D | +20 | Proximidad a order block |
| S/R clave | +15 | Zona de soporte/resistencia |
| Zona fresca extra | +10 | Zona adicional sin testear |
| Trampa a favor | +20 | Liquidez barrida a favor de posicion |

### Penalizaciones

| Penalizacion | Score | Detalle |
|--------------|-------|---------|
| Sentimiento contra | -30 | |
| Divergencia | -20 | RSI vs precio |
| Zona contra | -15 | En zona adversa |
| Noticia | -50 | Evento macro de alto impacto |
| Zona testeada | -10 | Zona ya tocada recientemente |
| Trampa contra | -25 | Liquidez barrida en contra |

### Umbral de Riesgo segun Score

| Score | Riesgo permitido |
|-------|-----------------|
| 60-79 | 0.5% |
| 80-99 | 1.0% |
| 100-119 | 1.5% |
| >=120 | 2.0% (max 1.5% challenge) |

---

## Confluencia Multi-Timeframe

- M15 base siempre: el bot primario opera en M15, siempre presente.
- M5 confirma: +15 pts al score (bueno)
- M1 confirma: +10 pts al score (bueno)
- M5 + M1 juntos: +30 pts al score (excelente, maxima probabilidad — bonus exponencial, no lineal)

Implementado en `calcular_score_confluencia()` en `skills_trading.py`. Los entornos hijos tienen features `confirmacion_m5`, `confirmacion_m1`, `confirmacion_ambos` en su observation space.

---

## Horario Oficial del Proyecto

- Apertura NY invierno: 10:30hs Argentina = 13:30hs servidor MT5 (NY en EST)
- Apertura NY verano (DST): 11:30hs Argentina = 14:30hs servidor MT5 (NY en EDT)
- DST activo: segundo domingo marzo -> primer domingo noviembre
- Python: `detectar_horario_ny_activo()` con `pytz`
- MQL5: `EstaEnAperturaNY()` con calculo dinamico de domingos

---

## Bot Scalper M5 — Especificacion Completa

- Autonomo: no necesita activacion del Bot Madre. Puede operar simultaneamente con un bot primario.
- Solo sesion NY (10:30-17:00hs Argentina).
- Maximo 3 operaciones scalping por dia (cada una puede sumar hasta 3 entradas).
- Interes compuesto en surfeo de banda (ver Arquitectura 3+1, punto 4).
- SL conjunto: ATR(14) * 1.2 desde la primera entrada.
- TP dinamico: ratio 2.0-3.5 segun `AnalizadorM1.calcular_ratio_tp_sugerido()`.
- Salida inmediata: si M5 cierra dentro de banda, o si M1 muestra reversión fuerte (3 velas contra), cerrar TODO.
- Observation space: 17 features combinadas M5 (7) + M1 (7) + state (3).

---

## Entorno Hibrido Unificado v3.3

Durante fase de simplificacion, el entorno `EntornoHibridoUnificado` reune la logica de decision en un solo modelo PPO con scoring visual estricto.

### Configuracion Actual (v3.3)

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `ventana_apertura_barras` | 4 | 1 hora post apertura NY |
| `max_ops_dia` | 2 | Maximo 2 operaciones por dia |
| `min_probabilidad` | 0.85 | Setup casi perfecto requerido |
| `incentivo_apertura` | 0.02 | Minima recompensa por abrir |
| `castigo_sin_condiciones` | -0.5 | Castigo fuerte si no hay setup |
| `castigo_inactividad_ventana` | -0.15 | Presion a operar en ventana |
| `castigo_contra_tendencia_h1` | -0.4 | No operar contra H1 |
| `costo_holding` | -0.005 | Costo por barra en posicion |
| `recompensa_tp1` | 0.8 | Primer take profit |
| `recompensa_tp2` | 1.0 | Segundo take profit |
| `recompensa_be` | 0.4 | Break-even |
| `castigo_sl` | -1.2 | Stop loss |
| `rsi_rev_long_max` | 20.0 | RSI extremo compra |
| `rsi_rev_short_min` | 80.0 | RSI extremo venta |
| `castigo_sobreoperacion` | -0.5 | Castigo por exceder ops/dia |
| `castigo_streak_perdidas` | -0.3 | Castigo por racha perdedora |
| `streak_umbral` | 3 | Racha que activa castigo |
| `recompensa_no_operar` | 0.05 | Recompensa por esperar setup |

### Scoring Visual Estricto (v3.3)

Setup PERFECTO (score 0.7) requiere TODAS las condiciones:
1. Toque de banda Bollinger: Low <= BB inferior (compra) / High >= BB superior (venta)
2. RSI extremo: <20 (compra) / >80 (venta)
3. Mecha de reversión >35% del rango de la vela

Score parcial:
- 0.35: toca banda + RSI <25 (compra) / >75 (venta)
- 0.2: cerca de banda (<=5% del ancho) + RSI <25 / >75
- 0.0-0.15: setup debil o sin direccion

### Anti-Sobreoperacion

- Maximo 2 ops/dia (reducido desde 3)
- Castigo por streak de perdidas: >=3 perdidas consecutivas -> penalizacion creciente
- Recompensa por no operar sin setup: +0.05 por barra de espera en ventana de apertura
- Castigo por operar contra tendencia H1: -0.4

---

## Pipeline ONNX

1. Entrenamiento RL (PPO en Kaggle GPU T4)
2. Export a ONNX opset 14
3. Validacion ort vs torch (diff < 1e-5)
4. Copia a EA MQL5
5. Carga en MT5 via ONNX Runtime
6. Ejecucion en cuenta demo -> live

**Archivo EA base:** `ea_mql5/PlantillaEAHibrido.mq5` — EA completo con includes, ONNX, doble TP/BE, gestion riesgo.

Incluye:
- `FiltroHorario.mqh` — DST NY automatico, sesiones Asia/Europa/NY, apertura NY 90min
- `GestorRiesgoEA.mqh` — CalcularLote(), AplicarBreakEven(), CerrarParcial(), CuentaDentroDeRiesgo(), CalcularDDDiario()

---

## Configuracion MT5

- Activos principales: US30 (DJIA), NAS100, GER40
- Timeframes: M15 (primario), M5 (confirmacion), M1 (timing), H1/H4/D1/W1 (macro)
- Broker: multi-broker (PropFirms: FTMO, FundingPips, Apex, MyFundedFX)
- VPS: 1 bot = 1 grupo de cuentas = 1 VPS distinto = 1 PropFirm distinta
- EA MQL5 objetivo: `QuantumHiveEA.mq5` que carga 3 ONNX (Madre + Hijo activo + Scalper) + CNN opcional

---

## Backtest Walk-Forward v2

- Datos historicos CSV: `US30_M15_2022_2024.csv`, `M5`, `M1`, `H1`
- Formato MetaTrader: tab-separado, columnas con angle brackets (`<DATE>`, `<TIME>`, `<OPEN>`...)
- Loader normaliza: lower-case, strip `<>`, datetime desde date+time
- Filtro sesion NY: hora Argentina 14-21 (equivalente 10:30-17:30 NY)
- Walk-forward: entrenar en año N, validar en año N+1, rotar

---

## Decisiones Tecnicas Tomadas

1. Gymnasium + Stable-Baselines3 (PPO) para RL en vez de librerias propietarias. Razon: estandar, documentado, export ONNX soportado.
2. ONNX opset 14 para maxima compatibilidad MT5. Razon: MT5 soporta ONNX Runtime nativo.
3. 3 modelos separados + 1 autonomo en vez de 1 solo modelo. Razon: especializacion por estrategia, entrenamiento mas rapido, debuggable.
4. 14-19 features en vez de >50. Razon: dimensionalidad baja = entrenamiento mas rapido, menos overfitting, interpretable.
5. Reglas mecanicas como safety layer sobre RL. Razon: RL puede alucinar en edge cases; las reglas son hard constraints.
6. CNN ResNet18 como capa adicional sobre score numerico. Razon: confirmacion visual de setups, no reemplaza scoring.
7. SQLite para persistencia en orquestador. Razon: portable, zero-config, suficiente para estado secuencia scalper.
8. Telegram para alertas en vez de email/SMS. Razon: instantaneo, API simple, gratis.

---

## Estado de Archivos Completados

### Nucleo (COMPLETADO)

- `nucleo/config.yaml` — global: activos, sesiones MT5 con DST, riesgo, Telegram, Kaggle, entrenamiento_visual
- `nucleo/indicadores.py` — RSI(7), Bollinger experto (30/3 + features avanzadas), BB doble, BBW dinamico, ATR(14), EMA50, confluencia multi-timeframe, divergencia
- `nucleo/entorno_base.py` — gymnasium.Env: sizing 1%, SL ATR×1.5, doble TP 1:2/1:4 + BE, filtros horario/noticias, modos challenge/live, metricas finales, obs 14 features
- `nucleo/utilidades.py` — logging, metricas (winrate, PF, DD, Sharpe), checkpoints, Telegram, reportes, deteccion horario NY
- `nucleo/skills_trading.py` — detectar_sesion(), detectar_trampas_liquidez(), calcular_score_confluencia() 0-160
- `nucleo/gestor_riesgo_global.py` — GestorRiesgoGlobal: DD enjambre 3%, pausa automatica, alertas Telegram
- `nucleo/validador_operacion.py` — ValidadorOperacion: 8 verificaciones (score, horario, noticias, pausas, sizing, doble exposicion)
- `nucleo/exportador_onnx.py` — ExportadorONNX: SB3→ONNX opset14, validacion ort vs torch, versionado
- `nucleo/estructura_mercado.py` — detectar_swings(), detectar_bos_choch(), detectar_zonas_liquidez(), detectar_soporte_resistencia()
- `nucleo/analizador_m1.py` — AnalizadorM1: detecta explosiones momentum M1, sugiere ratio TP dinamico 2.0-3.5
- `nucleo/entornos/entorno_madre.py` — EntornoMadre: 14 features, clasifica QUE operar
- `nucleo/entornos/entorno_reversion.py` — EntornoReversion: 15 features, confirmaciones M5/M1
- `nucleo/entornos/entorno_continuacion.py` — EntornoContinuacion: 17 features, confirmaciones M5/M1
- `nucleo/entornos/entorno_scalper_m5.py` — EntornoScalperM5: 19 features, autonomo, interes compuesto
- `nucleo/entornos/entorno_hibrido_unificado.py` — EntornoHibridoUnificado: entorno unificado v3.3, scoring estricto, anti-sobreoperacion
- `nucleo/orquestador.py` — Orquestador: coordina Madre→Hijo→Scalper, BE conjunto, ratio TP dinamico, persistencia SQLite
- `nucleo/entrenamiento_visual/generador_imagenes_entrenamiento.py` — PNG 224×224 setups perfectos
- `nucleo/entrenamiento_visual/entrenador_cnn.py` — ResNet18 transfer learning, early stopping, ONNX
- `nucleo/entrenamiento_visual/capturador_grafico.py` — captura chart actual a imagen 224×224
- `nucleo/lector_pdfs_estrategia.py` — procesa PDFs Bollinger, extrae condiciones, guarda JSON

### Bots (COMPLETADO)

- `automatizacion/generar_bot.py` — genera estructura de nuevo bot
- `bots/live/bot_live_ger40/config.yaml` — configuracion GER40 sesion Europa
- `bots/europa/bot_europa_us30/config.yaml` — configuracion US30 sesion Europa

### EA MQL5 (PARCIAL)

- `ea_mql5/FiltroHorario.mqh` — DST NY automatico
- `ea_mql5/GestorRiesgoEA.mqh` — lote, BE, parcial, DD
- `ea_mql5/PlantillaEAHibrido.mq5` — EA completo base
- PENDIENTE: `QuantumHiveEA.mq5` con carga 3 ONNX + CNN

### Scripts y Notebooks (ACTIVOS)

- `scripts/entrenar_rapido_test.py` — entrenamiento local PPO 100K steps, evaluacion post-training
- `notebooks/kaggle_unificado_v3.py` — script Kaggle completo: datos, entorno, PPO, evaluacion, ONNX export, reporte JSON

### Marketing (PARCIAL)

- `marketing/generador_prueba_social.py` — imagenes Instagram challenge superado
- `marketing/crm_clientes.py` — pipeline LEAD→CLIENTE

### Registro (COMPLETADO)

- `registro/auditoria/auditoria_operaciones.py` — registro append-only SHA256
- `registro/reporte_mensual_inversor.py` — PDF/HTML equity curve, metricas

---

## Proyectos Futuros Tecnicos

- PROYECTO 2: Enjambre Smart Money (Order Flow, DOM, BOS, CHoCH, FVG, Liquidity Pools).
- PROYECTO 3: Enjambre correlacion cruzada (US30/NAS100/GER40) — independiente del enjambre principal.
- Agentes adicionales: noticias, sentimiento social, copy trading, backtesting continuo.
- Tests unitarios para `validador_operacion`, `gestor_riesgo_global`, `calcular_score_confluencia`.
- Integrar `estructura_mercado.py` en entornos como feature adicional.
- PDFs Bollinger en `documentos/` para `lector_pdfs_estrategia.py`.
- `pyproject.toml` (requirements.txt creado, .env.ejemplo creado).
- Notebook Kaggle completo con pipeline secuencial: Madre → Reversión/Continuación → Scalper.

---

## Dependencias

### Base
- `gymnasium>=0.28.1`
- `stable-baselines3>=2.0.0`
- `pandas>=1.5.0`
- `numpy>=1.23.0`
- `python-dotenv>=0.19.0`
- `python-telegram-bot>=20.0`
- `onnxruntime>=1.15.0`
- `torch>=2.0.0`
- `pytz>=2023.1`

### Entrenamiento Visual (D18)
- `yt-dlp>=2024.1.0`
- `openai-whisper>=20231117`
- `chromadb>=0.4.0`
- `faiss-cpu>=1.7.4`
- `sentence-transformers>=2.2.0`

---

*Sistema auto-administrado. QuantumHive v3.0*

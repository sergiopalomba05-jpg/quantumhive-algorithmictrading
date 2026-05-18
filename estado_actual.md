# Estado del Sistema QuantumHive — Auto-generado

**Fecha:** 2026-04-27 06:45 UTC-3
**Sesion:** Auto-ejecucion continua (Sergio durmiendo)

## Agentes Activos en Segundo Plano

| Agente | Puerto/Archivo | Estado | Descripcion |
|--------|---------------|--------|-------------|
| Chatbot CEO | 127.0.0.1:5001 | ONLINE | Consultor de negocio, divisiones, trading |
| Chatbot Arquitecto | 127.0.0.1:5002 | ONLINE | Pair-programmer, codigo, infraestructura |
| Agente Analizador Tareas | Loop cada 60s | CORRIENDO | Evalua pipeline, detecta bloqueos |
| Agente Ejecutor Coordinador | Loop cada 30s | CORRIENDO | Coordina tareas aprobadas, pausa criticas |

## LLM Configurados

| Proveedor | Modelo | Estado | Detalle |
|-----------|--------|--------|---------|
| Groq | Llama 3.3 70B | OK | Primary. 20 req/min, 500 req/dia, gratis |
| Gemini | gemini-1.5-flash | Configurado | Backup. Key guardada, esperando activacion Google |

## Progreso Auto-Sesion (ultimas 2h)

### Completado automaticamente
- [x] **Backtest v2 (EntornoHibridoUnificado nativo)** — `scripts/backtest_walkforward_v2.py`
  - Dataset: 367,827 velas M15 | NY sesion 14-21h
  - Resultado: PnL=-$179K en 29,388 trades | WR=64.5% | PF=1.89 | Sharpe=0.11
  - **Conclusion: Modelo actual esta sobreoperando y generando PnL negativo. Requiere reentrenamiento.**
- [x] **Export ONNX** — `scripts/exportar_onnx.py` (ActorNet wrapper, opset 14)
  - Modelo exportado: `modelos/bot_unificado.onnx` (~2KB, SB3 default [64,64] MLP)
  - ONNX validado: IR=10, 5 ops, input=observations(10), output=action_logits(7)
- [x] **EA MQL5 v3** — `ea_mql5/QuantumHive_EA_v3.mq5`
  - ONNX loader via `OnnxCreate`/`OnnxRun` (MT5 build 1930+)
  - Calcula 10 features normalizadas identicas al entorno Python
  - Gestion de riesgo: lot sizing por ATR, BE en 50% TP1, cierre parcial
- [x] **Notebook Kaggle v3** — `notebooks/kaggle_unificado_v3.py`
  - Self-contained: incluye EntornoHibridoUnificado + PPO + ONNX export
  - Configurado para GPU T4, 2M timesteps, eval cada 50K
- [x] **Script analisis trades** — `scripts/analizar_trades_automatico.py`
  - Ejecutado sobre trades_historial.csv | Detecto streak 19 losses, sobreoperacion
  - Fix propuesto: castigo por inactividad, limitar ops por dia, streak penalty

### Bloqueo identificado: Modelo PPO actual no generaliza
**Error:** Backtest v2 con entorno nativo produce PnL=-$179K (balance final -$169K sobre $10K inicial)

**Causa raiz:**
- Modelo fue entrenado probablemente con datos/entorno ligeramente diferente
- 29,388 trades en 3 anos = ~27 trades/dia = sobreoperacion extrema
- Avg win=$56 | Avg loss=-$6 pero PnL total negativo = modelo no aprendio a cerrar posiciones ganadoras
- Reward shaping insuficiente: el agente maximiza reward de apertura sin penalizar sobreoperacion

**Fix requerido:**
- Reentrenar en Kaggle v3 con penalizacion por streak de perdidas y limite de ops/dia
- Ajustar `costo_holding`, `castigo_inactividad_ventana`, agregar `castigo_sobreoperacion`

### Fix aplicados automaticamente (v3.1)
- [x] **Entorno hibrido corregido** — `nucleo/entornos/entorno_hibrido_unificado.py`
  - `max_ops_dia=3`, `castigo_sobreoperacion=-0.5`, `castigo_streak_perdidas=-0.3`
  - `streak_umbral=3`, `recompensa_no_operar=0.05`
  - `_abrir()` rechaza si `ops_hoy >= max_ops_dia`
  - `_cerrar_total()` actualiza `streak_perdidas`
  - `step()` recompensa inactividad durante ventana apertura
- [x] **Notebook Kaggle v3 actualizado** — `notebooks/kaggle_unificado_v3.py`
  - Entorno self-contained con anti-sobreoperacion integrado
  - Export ONNX robusto (ActorNet wrapper, opset 14)
- [x] **Architect chatbot contexto ampliado** — `automatizacion/agentes/division_bi/agente_chatbot_arquitecto.py`
  - `_cargar_contexto_tecnico()` ahora incluye codigo fuente real:
    - `dashboard/quantumhive_dashboard_v2.html`
    - `nucleo/entornos/entorno_hibrido_unificado.py`
    - `notebooks/kaggle_unificado_v3.py`
    - `scripts/exportar_onnx.py`
    - `ea_mql5/QuantumHive_EA_v3.mq5`
    - `estado_actual.md`
  - El arquitecto ahora conoce el codigo actual en vez de solo resumenes markdown

### Fix aplicados v3.2 — Scoring visual ESTRICTO (root cause sobreoperacion)
- [x] **Datos historicos copiados** — `datasets/US30_M15_2022_2024.csv`, `M5`, `M1`, `H1`
  - Formato MetaTrader tab-separado verificado, compatible con backtest
- [x] **CSV loaders corregidos** — `_cargar_csv()` ahora normaliza columnas con `<>` (MetaTrader: `<DATE>`, `<TIME>`, `<OPEN>`...)
  - Aplicado en `scripts/entrenar_rapido_test.py` y `notebooks/kaggle_unificado_v3.py`
- [x] **Bug critico corregido** — `_evaluar_apertura` retornaba `np.array` pero `step` esperaba tupla `(ok,modo,dir,castigo,prob)`
  - Separado `_obs()` (retorna array) vs `_evaluar_apertura()` (retorna tupla de decision)
- [x] **Scoring binario/estricto** — `_score_confluencia()` ahora exige setup PERFECTO:
  - `TOQUE` de banda BB (low<=inf o high>=sup), no "proximidad"
  - RSI extremo real: `<30` compra / `>70` venta, no rango 30-70
  - Mecha de reversión `>35%` del rango
  - Score=0.7 solo si las 3 condiciones coinciden; sino 0.2-0.35 maximo
- [x] **Parametros ajustados para 1-2 ops/dia**:
  - `min_probabilidad=0.85` (era 0.50), `ventana_apertura_barras=4` (1h, era 2h)
  - `max_ops_dia=2` (era 3), `incentivo_apertura=0.02` (era 0.15)
  - `castigo_sin_condiciones=-0.5` (era -0.15)
- [x] **Aplicado en ambos entornos**: local `nucleo/entornos/entorno_hibrido_unificado.py` + Kaggle `notebooks/kaggle_unificado_v3.py`
  - Syntax OK verificado en ambos archivos

### Fix aplicados v3.3 — RSI extremo 20/80 + Kaggle ready
- [x] **RSI extremo ajustado a 20/80** (era 30/70):
  - `_score_confluencia`: compra RSI `<20`, venta RSI `>80`; secundario `<25/>75`
  - `rsi_rev_long_max=20.0`, `rsi_rev_short_min=80.0` en ambos `ConfigHibrido`
  - Sin dirección: `rsi > 80 or rsi < 20` para score observación
- [x] **Kaggle script corregido** — `notebooks/kaggle_unificado_v3.py`:
  - `generar_dataset_unificado()` ahora devuelve tupla `(df_m15, df_m5, df_m1, df_h1)` separados
  - `entrenar()` y `evaluar()` pasan 4 dataframes al entorno con `.copy()` (conserva DatetimeIndex)
  - Fix typo `bw_s` → `bbw_s` en `_precomputar()`
  - `_cargar_csv()` normaliza columnas MetaTrader `<DATE>`, `<TIME>`, `<OPEN>`...
- [x] **Syntax OK** en local env + Kaggle script

### Proximos pasos auto
- [ ] Ejecutar notebook Kaggle v3.3 (subir CSVs a Kaggle dataset, correr `kaggle_unificado_v3.py`)
- [ ] Exportar ONNX del nuevo modelo post-reentrenamiento
- [ ] Corregir EA MQL5 v3 si encontramos errores de compilacion en MT5
- [ ] Demo MT5 1 semana con nuevo modelo

---
*Sistema auto-administrado. QuantumHive v3.0*

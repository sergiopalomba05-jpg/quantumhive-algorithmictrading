# INFORME DE AUDITORÍA — BotsCuanticos

> Fecha: 2026-04-25 | Fase 1 completada + Correcciones QuantumHive (macro D1/W1, scalper 19 features, interés compuesto, 7 divisiones)
> Autor: Cascade (agente IA de desarrollo)

---

## 1. NÚCLEO

### `nucleo/config.yaml`
- **Función**: Configuración global del ecosistema.
- **Dependencias**: `pyyaml`.
- **Contenido clave**: activos (US30/NAS100/GER40/XAUUSD), horarios MT5 con DST NY/Argentina, sesiones, riesgo challenge/live, filtros noticias, Telegram/Kaggle vía env.
- **Mejoras**: agregar endpoint de calendario económico; migrar credenciales a `.env` exclusivo.

### `nucleo/entorno_base.py`
- **Clase**: `EntornoBaseTradingIA(gymnasium.Env)`
- **Funciones clave**: `_abrir()`, `_gestionar_posicion_abierta()`, `_calcular_metricas_finales()`, `reset()`, `step()`, `_observacion()`.
- **Dependencias**: `gymnasium`, `pandas`, `numpy`.
- **Estado**: COMPLETO — doble TP 1:2/1:4 + BE, SL ATR×1.5, sizing 1%, filtros horario/noticias, modos challenge/live, 14 features normalizados.
- **Mejoras**: agregar logging de cada step a `registro/auditoria/`; serializar métricas por episodio en JSONL.

### `nucleo/indicadores.py`
- **Funciones clave**: `calcular_rsi()`, `calcular_bollinger()`, `calcular_bbw_dinamico()`, `calcular_atr()`, `calcular_tendencia()`, `detectar_toques_bandas()`, `detectar_cierre_bandas()`, `calcular_confluencia_rsi()`, `detectar_divergencia()`, `calcular_todos_indicadores()`.
- **Dependencias**: `pandas`, `numpy`.
- **Estado**: COMPLETO.
- **Mejoras**: cachear cálculos de rolling windows en entorno RL para reducir CPU; vectorizar `calcular_confluencia_rsi`.

### `nucleo/utilidades.py`
- **Funciones clave**: `configurar_logs()`, `calcular_metricas()`, `guardar_checkpoint()`, `cargar_checkpoint()`, `enviar_telegram()`, `formatear_reporte()`.
- **Nuevas**: `detectar_horario_ny_activo()`, `esta_en_sesion_ny()`, `esta_en_ventana_apertura_ny()`.
- **Dependencias**: `numpy`, `urllib` (stdlib).
- **Estado**: COMPLETO.
- **Mejoras**: agregar retry con backoff en `enviar_telegram`; cachear resultado de `detectar_horario_ny_activo` por minuto.

### `nucleo/skills_trading.py`
- **Funciones clave**: `detectar_horario_ny_activo()`, `detectar_sesion()`, `detectar_trampas_liquidez()`, `calcular_score_confluencia()`.
- **Dependencias**: `pytz`, `pandas`, `numpy`.
- **Estado**: COMPLETO — score 0-160, 4 trampas detectadas, 8 verificaciones de validador.
- **Mejoras**: agregar `calcular_confluencia_skills` que combine skills 1-11 en un dict unificado; optimizar `detectar_trampas_liquidez` para evitar recalcular máximos en cada tick.

### `nucleo/gestor_riesgo_global.py`
- **Clase**: `GestorRiesgoGlobal`
- **Funciones clave**: `registrar_cuenta()`, `verificar_enjambre()`, `verificar_cuenta()`, `registrar_op()`, `estado()`, `reset_diario()`.
- **Dependencias**: `pyyaml`, `nucleo.utilidades`.
- **Estado**: COMPLETO — DD enjambre 3%, DD cuenta challenge/live, pausas auto, alertas Telegram.
- **Mejoras**: persistir estado en SQLite para recuperación tras reinicio; agregar webhook además de Telegram.

### `nucleo/validador_operacion.py`
- **Clase**: `ValidadorOperacion`
- **Funciones clave**: `validar()`, `cerrar_posicion()`, `pausar_bot()`, `reanudar_bot()`.
- **Estado**: COMPLETO — 8 verificaciones en cascada, log aprobadas/rechazos en JSONL.
- **Mejoras**: integrar `nucleo/gestor_riesgo_global.py` como dependencia en lugar de leer de cfg_bot; agregar test unitarios con pytest.

### `nucleo/exportador_onnx.py`
- **Clase**: `ExportadorONNX`
- **Funciones clave**: `exportar()`, `validar_compatibilidad()`.
- **Dependencias**: `torch`, `stable-baselines3`, `onnx`, `onnxruntime`, `pyyaml`.
- **Estado**: COMPLETO — exporta SB3→ONNX opset12, valida diff <0.001, versiona, copia a EA.
- **Mejoras**: agregar firma digital del modelo; generar graphviz del grafo ONNX para auditoría visual.

### `nucleo/estructura_mercado.py`
- **Funciones clave**: `detectar_swings(ventana=5)`, `detectar_bos_choch(ventana_swing=5)`, `detectar_zonas_liquidez(ventana=20, umbral_pips=15)`, `detectar_soporte_resistencia(ventana=50, min_toques=2)`, `estructura_completa(df_h1, df_h4=None)`.
- **Inputs/Outputs**: Recibe DataFrames OHLCV H1/H4. Retorna DataFrames con columnas `swing_high/low`, `bos_alcista/bajista`, `choch_alcista/bajista`, `estructura_tendencia`, `equal_highs/lows`, `zona_liquidez`, `nivel_sr`, `tipo_sr`, `distancia_sr`, `dentro_zona_sr`.
- **Dependencias**: `pandas`, `numpy`.
- **Estado**: COMPLETO — swings con ventana centrada, BOS/CHoCH por ruptura de ultimo swing, S/R por clustering de pivots redondeados, liquidez por equal highs/lows.
- **Mejoras**: optimizar clustering S/R con DBSCAN; validar BOS/CHoCH con datos reales de US30.

### `nucleo/analizador_m1.py`
- **Clase**: `AnalizadorM1`
- **Funciones clave**: `detectar_explosion(df_m1, direccion, precio_referencia)`, `calcular_ratio_tp_sugerido(df_m1, atr_m15)`.
- **Inputs/Outputs**: DataFrame M1 + direccion. Retorna dict con `explosion`, `velocidad`, `volumen`, `consistencia`, `ratio_tp`.
- **Estado**: COMPLETO — detecta explosiones por velocidad, volumen relativo, ATR, consistencia direccional 3 velas. Ratio TP dinámico 2.0-3.5.
- **Mejoras**: agregar filtro de horario (solo NY) en `detectar_explosion`.

### `nucleo/entornos/entorno_madre.py`
- **Clase**: `EntornoMadre(gymnasium.Env)`
- **Config**: `ConfigMadre(balance_inicial=10000, bb_periodo=30, bb_desv=3.0, rsi_periodo=7, ema_periodo=50, ventana_ny=90)`.
- **Observation space**: 10 features (pos_sup, pos_inf, bbw_h1, rsi_h1, rsi_h4, pend_ema_h1, pend_ema_h4, tend_h4, swing, sesion).
- **Action space**: Discrete(3) — ESPERAR(0), REVERSIÓN(1), CONTINUACIÓN(2).
- **Reglas clave**: NY obligatorio (penaliza -2.0 si no abre en apertura NY). Asia/Europa opcional. Solo 1 régimen por paso.
- **Estado**: COMPLETO.
- **Mejoras**: conectar `estructura_mercado.py` para features de S/R macro; entrenar modelo PPO.

### `nucleo/entornos/entorno_reversion.py`
- **Clase**: `EntornoReversion(gymnasium.Env)`
- **Config**: `ConfigReversion(balance_inicial=10000, riesgo_pct=0.01, bb_periodo=30, bb_desv=3.0, rsi_periodo=7, atr_periodo=14, atr_sl_mult=1.5, ratio_tp=2.0, score_min=60, rsi_long_max=20, rsi_short_min=80, bbw_max=0.05)`.
- **Observation space**: 15 features — incluye `confirmacion_m5`, `confirmacion_m1`, `confirmacion_ambos`.
- **Condiciones**: toca banda + mecha (no cuerpo fuera), RSI extremo, BBW bajo, confluencia M5/M1.
- **Estado**: COMPLETO.
- **Mejoras**: integrar `calcular_score_confluencia()` del `skills_trading.py` para reward shaping; agregar S/R macro desde `estructura_mercado.py`.

### `nucleo/entornos/entorno_continuacion.py`
- **Clase**: `EntornoContinuacion(gymnasium.Env)`
- **Config**: `ConfigContinuacion(balance_inicial=10000, riesgo_pct=0.01, bb_periodo=30, bb_desv=3.0, rsi_periodo=7, atr_periodo=14, atr_sl_mult=1.5, ratio_tp=3.0, bbw_min_expansion=0.03)`.
- **Observation space**: 17 features — incluye `confirmacion_m5`, `confirmacion_m1`, `confirmacion_ambos`, EMA200.
- **Condiciones**: cuerpo fuera de banda, BBW expandiéndose (≥0.03), RSI zona tendencia (40-75 alcista / 25-60 bajista), EMA50/200 alineadas, momentum M5 confirmado.
- **Estado**: COMPLETO.
- **Mejoras**: integrar `estructura_mercado.py` para validar ruptura de S/R con cuerpo; usar BB doble para timing de pullback.

### `nucleo/entornos/entorno_scalper_m5.py`
- **Clase**: `EntornoScalperM5(gymnasium.Env)`
- **Config**: `ConfigScalperM5(balance_inicial=10000, riesgo_pct=0.01, riesgo_pct_2=0.005, riesgo_pct_3=0.0025, bb_periodo=30, bb_desv=3.0, rsi_periodo=7, atr_periodo=14, atr_sl_mult=1.2, ratio_tp=2.5, bbw_exp_min=1.2, velas_surf_min=2, cuerpo_pct_min=0.6, rsi_mom_long=65, rsi_mom_short=35, rsi_m1_low=45, rsi_m1_high=55, max_ops_dia=3)`.
- **Observation space**: 17 features — M5 context (7) + M1 timing (7) + state (3).
- **Lógica**: M5 define contexto surfeo (BBW expansión, velas consecutivas fuera, RSI momentum, cuerpo >60%). M1 define timing (pullback a banda media, RSI intermedio rebota, cuerpo fuerte, BBW creciendo).
- **Interés compuesto**: 1ra 1.0%, 2da 0.5%, 3ra 0.25% = 1.75% max. SL conjunto ATR×1.2 desde primera entrada.
- **Salida inmediata**: si M5 cierra dentro de banda, o M1 reversión 3 velas contra.
- **Estado**: COMPLETO.
- **Mejoras**: agregar filtro de sesión NY explicito; conectar `AnalizadorM1` para TP dinámico real.

### `nucleo/orquestador.py`
- **Clase**: `Orquestador`
- **Dataclass**: `EstadoOperacion(activa, bot, direccion, precio_entrada, sl, tp, lote, be_aplicado, pnl_acumulado, paso_apertura)`.
- **Funciones clave**: `evaluar_macro()`, `abrir_primaria()`, `monitorizar_m1()`, `sumar_posicion()`, `gestionar_posiciones()`, `puede_operar_hoy()`, `tick()`, `guardar_estado()`, `cargar_estado()`.
- **Flujo**: Madre→Hijo primario→Scalper secundario. BE conjunto (primaria alcanza BE → ajusta SL secundaria). Ratio TP dinámico por `AnalizadorM1`. Límite 2 ops/2 pérdidas diarias.
- **Persistencia**: SQLite (`registro/auditoria/orquestador.sqlite`) con tabla `estado_orquestador`. Recupera `primaria_json`, `secundaria_json`, `ops_dia`, `perdidas_hoy` tras crash.
- **Dependencias**: `EntornoMadre`, `EntornoReversion`, `EntornoContinuacion`, `EntornoScalperM5`, `AnalizadorM1`, `ValidadorOperacion`, `GestorRiesgoGlobal`, `sqlite3`.
- **Estado**: COMPLETO — placeholder en `action_space.sample()` para modelo entrenado; SQLite implementado; logging JSONL.
- **Mejoras**: reemplazar `sample()` por `modelo.predict()` cuando los modelos estén entrenados; agregar healthcheck endpoint HTTP.

### `nucleo/entrenamiento_visual/generador_imagenes_entrenamiento.py`
- **Funciones clave**: `generar_imagen_setup_reversion()`, `generar_imagen_setup_continuacion()`, `generar_imagen_setup_scalper()`, `generar_dataset_imagenes_completo()`.
- **Inputs/Outputs**: DataFrames M15/M5 + indice_entrada + score. Retorna ruta PNG 224×224.
- **Formato visual**: fondo oscuro #1e1e1e, velas color #26a69a/#ef5350, BB naranja/azul dashed, EMA50 morada, RSI cyan con líneas 30/70, flecha amarilla entrada, zonas TP/SL sombreadas.
- **Dependencias**: `matplotlib`, `pandas`, `numpy`.
- **Estado**: COMPLETO — genera muestras placeholder cada 500 velas. Requiere integración con backtesting real para filtrar solo setups ganadores con score≥80.
- **Mejoras**: conectar con pipeline de backtesting para etiquetar correctamente ganadores/perdedores; agregar watermark BotsCuanticos.

### `nucleo/entrenamiento_visual/entrenador_cnn.py`
- **Funciones clave**: `preparar_dataset_cnn(ruta_imagenes, proporcion_val=0.2)`, `entrenar_cnn(epochs=50, batch_size=32, lr=0.001)`, `exportar_cnn_onnx(ruta_modelo)`, `evaluar_setup_visual(imagen_actual)`.
- **Arquitectura**: ResNet18 preentrenada (ImageNet), `fc` reemplazado por Linear(in_features, 1). BCEWithLogitsLoss. ReduceLROnPlateau. Early stopping 5 epochs.
- **Dataset**: `SetupDataset` con augmentation (rotación 5°, color jitter). Normalización [-1, 1].
- **Exportación**: ONNX opset 11, input (1,3,224,224), output probabilidad.
- **Dependencias**: `torch`, `torchvision`, `Pillow`.
- **Estado**: COMPLETO — placeholder en dataset (solo imágenes válidas, falta agregar negativas).
- **Mejoras**: generar dataset balanceado (50% setups válidos, 50% charts aleatorios); agregar augmentation más agresiva; entrenar en Kaggle T4×2.

### `nucleo/entrenamiento_visual/capturador_grafico.py`
- **Funciones clave**: `grafico_en_tiempo_real_a_imagen(df_actual, velas=50)`, `capturar_grafico_mt5(simbolo, timeframe, velas=50)`.
- **Inputs/Outputs**: DataFrame velas actuales → numpy array 224×224×3 (RGB uint8).
- **Formato**: IDENTICO al de entrenamiento (mismos colores, mismos indicadores, mismo layout 2 paneles).
- **Estado**: COMPLETO — `grafico_en_tiempo_real_a_imagen` listo. `capturar_grafico_mt5` requiere conexión ZMQ a MT5.
- **Mejoras**: implementar conexión ZeroMQ a MT5 para velas en tiempo real; cachear última imagen generada.

### `nucleo/lector_pdfs_estrategia.py`
- **Funciones clave**: `procesar_pdf_bollinger(ruta_pdf)`, `construir_contexto_estrategia(ruta_documentos)`, `validar_setup_con_teoria(setup_detectado, conocimiento_pdf)`.
- **Inputs/Outputs**: PDF Bollinger → JSON estructurado con condiciones_reversion, condiciones_continuacion, configuraciones, squeeze, reglas_b_bw.
- **Motor**: `pdfplumber` (primario) o `PyPDF2` (fallback).
- **Estado**: COMPLETO — parsing por keywords. Requiere PDFs en carpeta `documentos/`.
- **Mejoras**: usar NLP/LLM para extracción semántica de reglas en lugar de keyword matching; integrar con Bot Madre como system prompt.

---

## 2. BOTS

### `automatizacion/generar_bot.py`
- **Función**: Genera estructura de carpetas y config para nuevo bot.
- **Estado**: COMPLETO.
- **Mejoras**: agregar plantilla de `entrenar_bot.py` y `backtest_bot.py` auto-generados.

### `bots/live/bot_live_ger40/config.yaml`
- **Estado**: COMPLETO — config específica GER40, sesión Europa 09:00-13:30 MT5.

### `bots/europa/bot_europa_us30/config.yaml`
- **Estado**: COMPLETO — config US30 sesión Europa, sin solapamiento con apertura NY.

---

## 3. AGENTES

### `automatizacion/agentes/agente_auditoria.py`
- **Clase**: `AgenteAuditoria`
- **Funciones clave**: `auditar_operaciones_recientes()`, `verificar_integridad_cuentas()`, `generar_reporte_auditoria()`.
- **Estado**: COMPLETO.
- **Mejoras**: implementar `verificar_integridad_cuentas` con comparación MT5 vs interno vía MetaTrader5 API.

### `automatizacion/agentes/agente_compliance.py`
- **Clase**: `AgenteCompliance`
- **Funciones clave**: `verificar_cuenta_challenge()`, `calcular_progreso_challenge()`, `reporte_compliance_diario()`.
- **Estado**: COMPLETO.
- **Mejoras**: integrar cuenta real de MT5 para DD en tiempo real; agregar proyección Monte Carlo de superación de challenge.

### `automatizacion/agentes/agente_optimizador.py`
- **Clase**: `AgenteOptimizador`
- **Funciones clave**: `analizar_rendimiento_skills()`, `ajustar_parametros_automaticamente()`, `detectar_degradacion_modelo()`.
- **Estado**: COMPLETO.
- **Mejoras**: usar tests estadísticos (chi-square) para significancia de winrate por skill combo; limitar frecuencia de ajustes a 1 por semana.

### `automatizacion/scheduler.py`
- **Función**: `iniciar_scheduler()` — BlockingScheduler APScheduler.
- **Jobs**: 1min (riesgo, compliance), 5min (recolector), 15min (riesgo global), diarios (9:45, 10:00, 10:25, 17:00, 20:00, 22:00, 23:00), semanales (dom 19:00, 20:00; lun 9:00; mie 19:00; vie 19:00), mensuales (día 1 8:00, 9:00).
- **Estado**: COMPLETO.
- **Mejoras**: agregar healthcheck endpoint HTTP; persistir job state en SQLite; manejar Daylight Saving en triggers.

---

## 4. EA MQL5

### `ea_mql5/FiltroHorario.mqh`
- **Funciones clave**: `EsVeranoNY()`, `AperturaNYServidor()`, `EstaEnSesionNY()`, `EstaEnAperturaNY()`, `EstaEnSesionAsia()`, `EstaEnSesionEuropa()`, `SesionActual()`.
- **Estado**: COMPLETO — cálculo dinámico de segundos domingos marzo/noviembre.
- **Mejoras**: verificar con datos históricos de DST de NYSE; test unitarios en MQL5 con `OnTester`.

### `ea_mql5/GestorRiesgoEA.mqh`
- **Funciones clave**: `CalcularLote()`, `AplicarBreakEven()`, `CerrarParcial()`, `CuentaDentroDeRiesgo()`, `CalcularDDDiario()`, `CalcularDDTotal()`, `GetFillingMode()`.
- **Estado**: COMPLETO.
- **Mejoras**: leer balance inicial challenge desde archivo externo; implementar trailing stop como opción adicional al BE fijo.

### `ea_mql5/PlantillaEAHibrido.mq5`
- **Función**: `OnInit()`, `OnDeinit()`, `OnTick()`, `GestionarPosicionAbierta()`.
- **Inputs**: NombreBot, RutaONNX, RiesgoPct, RatioTP1/2, PipsBE, ModoChallenge, Límites DD, MinutosVentanaApertura, ATRPeriodo, ATRMultiplicadorSL.
- **Estado**: COMPLETO — incluye FiltroHorario + GestorRiesgoEA, ONNX load, doble TP/BE.
- **Mejoras**: agregar manejo de errores ONNX (`OnnxGetLastError`); log a archivo CSV en `MQL5/Files/BotsCuanticos/`.

---

## 5. REGISTRO Y TRANSPARENCIA

### `registro/auditoria/auditoria_operaciones.py`
- **Clase**: `AuditoriaOperaciones`
- **Funciones clave**: `registrar()`, `verificar_integridad()`, `exportar_para_cliente()`.
- **Estado**: COMPLETO — append-only SHA256.
- **Mejoras**: firmar digitalmente cada línea con clave privada del sistema; agregar API REST para consulta de clientes.

### `registro/reporte_mensual_inversor.py`
- **Función**: `generar_reporte_pdf()`
- **Estado**: COMPLETO — PDF con fpdf2 o fallback HTML, equity curve matplotlib.
- **Mejoras**: agregar firma digital del PDF; enviar automáticamente por email; estilizar HTML con Tailwind si se usa fallback.

---

## 6. MARKETING

### `marketing/generador_prueba_social.py`
- **Funciones clave**: `generar_imagen_challenge_superado()`, `generar_imagen_resultado_semanal()`, `generar_imagen_estadisticas_bot()`.
- **Dependencias**: `matplotlib`, `PIL`.
- **Estado**: COMPLETO.
- **Mejoras**: agregar watermark más visible; exportar también en formato Stories (1080×1920); integrar API de Instagram para upload automático.

### `marketing/crm_clientes.py`
- **Clase**: `CRMClientes`
- **Funciones clave**: `agregar_lead()`, `actualizar_estado()`, `leads_para_seguimiento_hoy()`, `calcular_conversion()`, `generar_propuesta()`.
- **Estado**: COMPLETO.
- **Mejoras**: migrar a SQLite/PostgreSQL en lugar de YAML; agregar recordatorio automático por Telegram; integrar calendario Google.

---

## 7. DOCUMENTACIÓN

### `LEEME.md`, `CONTEXTO.md`, `AGENTES.md`, `.windsurfrules`
- **Estado**: COMPLETO.
- **Mejoras**: mantener sincronizados tras cada fase; agregar diagrama de arquitectura Mermaid.

---

## 8. DEPENDENCIAS GLOBALES

**Core**: `python>=3.12`, `gymnasium`, `stable-baselines3`, `pandas`, `numpy`, `pyyaml`, `pytz`
**ML/ONNX**: `torch`, `onnx`, `onnxruntime`
**Visualización**: `matplotlib`, `Pillow`, `fpdf2` (opcional)
**Scheduler**: `apscheduler`
**Broker**: `MetaTrader5` (opcional, para operación real)
**CrewAI**: `crewai` (pendiente para orquestador)

---

## 9. RIESGOS IDENTIFICADOS

1. **Timeout API**: varios archivos largos requirieron división en secciones menores. Riesgo de inconsistencia si se editan por partes.
2. **MQL5 ONNX**: `OnnxCreate` requiere build MT5 compatible con ONNX. Verificar en build real antes de deploy.
3. **DST NY**: cálculo en MQL5 debe probarse con fechas de transición 2024-2030.
4. **Score 160**: máximo teórico no garantiza que todas las condiciones sean simultáneamente alcanzables. Requiere calibración con datos reales.
5. **Hash SHA256**: auditabilidad depende de que nadie modifique el archivo `.jsonl` directamente. Agregar firma asimétrica en FASE 2.

---

## NUEVAS DIVISIONES Y AGENTES (Expansión FASE 2)

### División 2 — Gestión de Fondeo y Challenges
- `agente_challenge.py` ✅ — Gestión de pase de challenge, monitoreo DD/profit/días.
- `agente_cuentas_fondeadas.py` ✅ — Registro cuentas fondeadas, balance, DD, cobro pendiente QH.
- `agente_cobro_fondeo.py` ✅ — Cobro parte QH cuando PropFirm paga.
- `agente_afiliaciones.py` ✅ — Acuerdos con PropFirms, cupones, comisiones.
- `agente_onboarding_cliente.py` ✅ — Alta de nuevo cliente, asigna bot challenge.

### División 2B — PropFirms y Dispersión de Cuentas
- `reglas_propfirms.yaml` ✅ — Reglas de 4 PropFirms: FTMO, FundingPips, Apex, MyFundedFX. Límites DD diario/total, riesgo por operación, delay min/max, variación lote, hedging, detección copy, cuentas simultáneas.
- `agente_selector_cuenta.py` ✅ — Detecta PropFirm por nombre de servidor MT5, genera perfil único por cuenta (UUID, agresividad 0.7-1.0, preferencia TP, delay base, variación lote). Guarda en `registro/cuentas/perfiles.json` con append + hash SHA256.
- `agente_dispersor.py` ✅ — Recibe señal del bot, distribuye a todas las cuentas activas con delay y variación únicos. Agrupa por PropFirm, evita solapamiento de delay en misma firma. Registra en `registro/auditoria/dispersiones.jsonl`.
- `agente_monitor_propfirm.py` ✅ — Monitorea DD cada 5 minutos. 60% = Telegram amarillo, 80% = pausa + naranja, 95% = cierre forzado + rojo + registro en `bus_de_datos.json`.
- `GestorEnjambreDisperso.mqh` ✅ — EA MQL5. `EjecutarConDispersion()` calcula delay aleatorio, factor de variación de lote, valida mínimo/máximo/step del símbolo, abre operación con magic number D2B.
- `agente_gestor_rotacion_cuentas.py` ✅ — Gestiona portafolio multi-cuenta con rotación dinámica. Congela cuentas tras racha perdedora (2 días estándar, 3 días crítica), sugiere retiros al alcanzar 3% ganancia individual o portafolio, selecciona qué cuentas operan hoy evitando alta correlación de signo (>75%). Genera `plan_diario.json`.

### División 8 — Fábrica de Bots y Mercado Interno
- Sin agentes implementados aún (pendiente FASE 3).

### División 9 — Limpieza y Mantenimiento
- Sin agentes implementados aún.

### División 10 — Diseño y Optimización Web
- Sin agentes implementados aún.

### División 4 — Marketing y Captación (Expandido)
- `agente_partnerships_traders.py` ✅ — Pipeline IDENTIFICADO→CONTACTADO→INTERESADO→NEGOCIANDO→CERRADO→RECHAZADO. Genera propuesta PDF/JSON con términos estándar (30/70 split, naming técnico propio, sin promesas rendimiento). Trackea oportunidades activas. Base de datos en `datos/traders_objetivo.yaml`.
- `agente_captacion_seguidores.py` ✅ — Infraestructura captación post-acuerdo CERRADO. Rate limit 50 mensajes/día por cuenta. Deriva interesados a bienvenida ventas. Inactivo sin acuerdo cerrado.
- `agente_naming_bots.py` ✅ — Genera nombres técnicos propios (BandEdge, Quantum Reversal, etc.) por tipo de estrategia. Verifica no duplicado en `datos/catalogo_bots.yaml`. Nunca usa nombre del trader.
- `agente_marketing_infoproductos.py` ✅ — Planifica campanas PRE-LAUNCH, OPEN-CART, LAST-CHANCE, EVERGREEN. Genera copy organico (IG carousel/reel, X threads, email broadcasts). UTM tracking. Lee catalogo de D5. Fases con budget y KPIs por campana.

### División 5 — Infoproductos y Afiliados (Activado)
- `agente_creador_infoproductos.py` ✅ — Genera estructuras completas de cursos: 4 tipos (bot mecanico $297, hibrido $497, framework $997, propfirm $197). Modulos con lecciones, objetivos, materiales requeridos. Pipeline produccion semanal (pre-produccion → grabacion → post → lanzamiento). Guarda catalogo en `datos/catalogo_infoproductos.json`.
- `agente_analista_tendencias_infoproductos.py` ✅ — Analiza 6 nichos (trading algoritmico, mql5, python trading, propfirm, automatizacion, ia financiera). Score oportunidad basado en volumen busqueda + crecimiento + competencia. Recomienda precio, formato, estrategia lanzamiento. Ideas validadas automaticamente si score >= 60.
- `agente_entrenador_ventas_infoproductos.py` ✅ — 7 modulos capacitacion (fundamentos, copywriting, email, funnels, launch, afiliados, retencion). Secuencias email pre-disenadas (bienvenida 5d, lanzamiento 9d, carrito abandonado). Templates copy PAS, hero section, testimonios, oferta. Guiones venta por tipo de producto con hook, problema, agitate, solucion, oferta, urgencia, cierre.

### División 11 — Atención al Cliente y Ventas
- `agente_bienvenida.py` ✅ — Primer contacto, calificación de leads, derivación.
- `agente_closer.py` ✅ — Cierra ventas, genera links de pago, seguimiento.
- `agente_ventas_infoproductos.py` ✅ — Pipeline completo de ventas digitales: VISITANTE → LEAD → PROSPECTO_CALIDO → INTERESADO_COMPRA → CLIENTE → CLIENTE_ACTIVO → UPSELL_ABIERTO → CLIENTE_PREMIUM → AMBASSADOR. Transiciones validadas por maquina de estados. Registra contactos, compras, refunds. Metricas: conversion rate, revenue total, CAC estimado. Scripts de objeciones pre-cargados (precio, confianza, tiempo, conocimiento, pruebas). Secuencias nurturing por segmento (LEAD, PROSPECTO, ABANDONO, CLIENTE).

### División 12 — Crecimiento y Optimización
- `agente_supervisor_global.py` ✅ — Cruza datos de todas las áreas, detecta cuellos de botella.

### División 13 — Legal y Compliance
- `agente_terminos.py` ✅ — Términos de servicio versionados.
- `agente_contratos.py` ✅ — Contratos PDF clientes fondeo.
- `agente_regulaciones.py` ✅ — Monitorea regulaciones por país.
- `agente_propfirm_compliance.py` ✅ — Reglas PropFirms, alerta cambios.
- `agente_privacidad.py` ✅ — GDPR, eliminación datos.
- `agente_legal_marketing.py` ✅ — Verifica campañas antes de publicar: marcas ajenas, promesas rendimiento, TOS Instagram/Telegram. Reporte BAJO/MEDIO/ALTO. Bloquea si ALTO.
- `agente_legal_senales.py` ✅ — Analiza regulación servicio señales por país (CNV AR, CNMV ES, CNBV MX). Sugiere estructura educativa vs señales. Alerta umbral clientes para licencia.
- `agente_legal_sala_inversion.py` ✅ — Compliance D16. Monitorea beta ≤20 clientes, genera términos por país, alerta capital gestionado que requiera registro como gestor.
- `agente_legal_propfirms.py` ✅ — Verifica TOS de cada PropFirm mensualmente (hash comparativo). Detecta cambios. Verifica que dispersión no viole TOS (hedging, delay, variación lote, cuentas simultáneas).
- `agente_legal_uci.py` ✅ — Copyright + fair use para D18. Detecta copyright explícito, clasifica fair use educativo (puntuación 0-7), rechaza si fuente prohibida. Log en `registro/legal/uci/log_fuentes_procesadas.jsonl`.
- `agente_coordinador_legal.py` ✅ — Recibe reportes de todos los sub-agentes. Genera `registro/legal/reporte_diario.json` consolidado. Escala alertas ALTO a Sergio vía Telegram.

### División 14 — Infraestructura y DevOps
- `agente_monitoreo_sistema.py` ✅ — Monitorea procesos críticos cada 5 min, reinicia.
- `agente_alertas_criticas.py` ✅ — Sistema de alertas VERDE→NEGRO por niveles de DD.
- `agente_backup.py` ✅ — Backup diario comprimido de ONNX/SQLite/config.

### División 15 — Business Intelligence
- `agente_dashboard_ejecutivo.py` ✅ — Reporte diario KPIs todas divisiones.
- `agente_metricas_negocio.py` ✅ — MRR, churn, LTV, CAC, proyecciones.

### División 16 — Sala de Inversión Colmena
- **Estado**: EN DESARROLLO — beta cerrada con 5-10 personas antes del lanzamiento público.
- `agente_pool_capital.py` ✅ — SQLite append-only. Trackea capital por cliente, % del pool, PnL proporcional, historial movimientos.
- `agente_distribucion_ganancias.py` ✅ — Calcula distribución 80/20 al cierre sesión. Genera comprobante JSON por cliente + resumen diario.
- `agente_sala_visual.py` ✅ — Métricas en vivo: PnL del día, capital total, operaciones abiertas, equity curve. Persistencia JSON + SQLite.
- `agente_retiros.py` ✅ — Gestiona solicitudes PENDIENTE→VERIFICADA→COMPLETADA|RECHAZADA. Verifica fondos, anti money laundering (24h desde depósito), fee $2 si <$100.
- `agente_ceo_sala.py` ✅ — Supervisión DD pool. Umbrales: AMARILLO (2%), NARANJA (3.5%, reduce sizing 50%), ROJO (5%, kill-switch total). Cooldown 15 min entre decisiones. Hash SHA256 en cada decisión.
- **Comisión**: 20% QH / 80% cliente. Distribución proporcional al % del pool.
- **Requiere habilitación legal**: División 13 trabaja en habilitación como gestor de inversiones.
- **Dependencias**: `sqlite3`, `decimal`, `hashlib`.

### División 17 — Ecosistema de Partners
- **Estado**: FUTURO — se desarrolla cuando QuantumHive tenga track record y renombre establecido.
- **Concepto**: Empresas de fondeo, traders independientes, gestores se suman al ecosistema. QH provee infraestructura, agentes, automatización. Partner trae marca y clientes.
- **Visión técnica**: Cada partner tiene sala propia en el visualizador Pygame. API white-label para branding personalizado. Revenue share automático.
- **Sin agentes implementados aún**: solo documentado en CONTEXTO.md como visión estratégica Fase 6+.

### División 18 — Unidad de Conocimiento e Inteligencia (UCI)
- **Estado**: EN DESARROLLO — PRÓXIMO SPRINT (usa en próximo entrenamiento CNN).
- **18A — Recolector de Video**:
  - `agente_recolector_videos.py` ✅ — yt-dlp descarga audio YouTube, Whisper transcribe, heurísticas extraen patrones de trading (RSI+BB, Breakout, Smart Money). Output: JSON estructurado en `datos/conocimiento_extraido/`.
  - Modelo Whisper: configurable por env `WHISPER_MODEL` (tiny/base/small/medium/large). Default: `base`.
  - Cache: audio WAV en `datos/cache_videos/` + metadata JSON.
  - **Dependencias**: `yt-dlp>=2024.1.0`, `openai-whisper>=20231117`.
- **18B — Procesador de PDFs**:
  - `agente_procesador_pdfs.py` ✅ — pdfplumber primario, PyMuPDF fallback. Extrae texto, tablas, heurísticas detectan setups, reglas gestión, timeframes, indicadores. Output: JSON en `datos/conocimiento_extraido/`.
  - Directorio fuente: `documentos/estrategias/*.pdf`.
  - **Dependencias**: `pdfplumber`, `PyMuPDF`.
- **18C — Generador CNN**:
  - `agente_generador_cnn.py` ✅ — Captura/genera imágenes 224×224 de setups. Modo SYNTHETIC: genera charts con velas, Bollinger, EMA, señal de entrada. Modo LIVE: placeholder para captura MT5 real.
  - Etiquetado automático: PENDIENTE → (espera resultado) → GANÓ/PERDIÓ por pips. Mueve imagen a `datos/imagenes_entrenamiento/validas/` o `invalidas/`.
  - Dataset objetivo: ≥500 imágenes balanceadas para entrenamiento ResNet18.
  - **Dependencias**: `Pillow`, `matplotlib`, `numpy`, `pandas`.
- **18D — Base de Conocimiento**:
  - `agente_base_conocimiento.py` ✅ — Indexa documentos procesados en base vectorial. Soporta ChromaDB (persistente, recomendado) y FAISS (in-memory + serialización).
  - Embeddings: `sentence-transformers` modelo `all-MiniLM-L6-v2` (384 dim, por defecto). Configurable por env `EMBEDDING_MODEL`.
  - API de consulta: `consultar_para_agente(query, k=5, tipo_filtro=None)` retorna resultados con relevancia 0-1 y recomendación automática.
  - Flujo: YouTube/PDF/captura → transcripción/extracción → JSON → embeddings → indexación → query semántica → alimenta RL+CNN.
  - **Dependencias**: `sentence-transformers>=2.2.0`, `chromadb>=0.4.0` o `faiss-cpu>=1.7.4`.
- **18E — Recolector de Traders**:
  - `agente_recolector_traders.py` ✅ — Activado solo cuando trader en `traders_objetivo.yaml` tiene estado CERRADO. Descarga contenido público (YouTube/Podcast), transcribe con Whisper, extrae patrones de entrada, reglas gestión, contexto mercado, indicadores y timeframes en JSON estructurado. Pasa a `agente_base_conocimiento.py` para indexación. Verificación legal previa via `agente_legal_uci.py` — si no es APROBADO, no procesa. Log en `registro/uci/recoleccion_traders.jsonl`.

---

## 10. PRÓXIMA SESIÓN — CHECKLIST

- [x] `requirements.txt` completo con versiones exactas (Python 3.13)
- [x] `.env.ejemplo` con todas las variables de entorno
- [x] `agente_recolector.py` descarga automática M1/M5/M15/H1/H4/D1/W1
- [x] EntornoMadre: 14 features con macro D1/W1, action space sin "esperar"
- [x] EntornoScalperM5: 19 features, interés compuesto 3-5 trades, trailing stop, SL ~50 pts, TP ~100 pts
- [ ] Notebook Kaggle completo con pipeline secuencial: Madre → Reversión/Continuación → Scalper
- [ ] EA MQL5 `QuantumHiveEA.mq5` carga 3 ONNX + CNN opcional, ejecuta flujo completo
- [ ] `pyproject.toml` (pendiente de formato PEP 621)
- [ ] Tests unitarios para `validador_operacion`, `gestor_riesgo_global`, `calcular_score_confluencia`
- [ ] Integrar `estructura_mercado.py` features en entornos RL hijos
- [ ] PDFs Bollinger en `documentos/` para `lector_pdfs_estrategia.py`
- [ ] Dashboard visual QuantumHive (React + WebSocket) — FASE 2

---

**Fin del informe.**

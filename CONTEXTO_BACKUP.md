# CONTEXTO

Este documento es el **punto de reanudación** para cualquier IA/desarrollador que continúe BotsCuanticos.

## Visión completa del negocio — QuantumHive (19 Divisiones)

QuantumHive es una empresa de trading algorítmico de alto nivel que gestiona grandes capitales de inversores institucionales y privados. Estructura multinacional con operaciones en 8+ jurisdicciones.

- **División 1 — Enjambre de Trading**: bots híbridos EA MQL5 + ONNX (Madre + Reversión + Continuación + Scalper) ejecutando en MT5.
- **División 2 — Gestión de Fondeo y Challenges**: challenge cliente → cuenta live → split 40/40/20 (QH/Cliente/PropFirm).
- **División 2B — PropFirms y Dispersión de Cuentas**: gestión multi-cuenta en PropFirms (FTMO, FundingPips, Apex, MyFundedFX). Selector de cuenta por servidor MT5, dispersor con delay/variación únicos por cuenta, monitor de drawdown contra límites de firma, EA MQL5 `GestorEnjambreDisperso.mqh`, gestor de rotación de cuentas (congelamiento por racha perdedora, scheduling diario, retiros sistemáticos).
- **División 3 — Grupo de Señales**: embudo señales gratis 3 días → suscripción semanal/mensual → Colmena.
- **División 4 — Marketing y Captación**: contenido automático con resultados reales del enjambre. Pipeline de partnerships con traders reconocidos (`agente_partnerships_traders.py`), captación de seguidores post-acuerdo con rate limit 50/día (`agente_captacion_seguidores.py`), generador de nombres técnicos propios para bots (`agente_naming_bots.py`).
- **División 5 — Infoproductos y Afiliados**: infoproductos digitales (cursos de bots mecanicos, hibridos, frameworks de automatizacion) + software (EAs, datasets, modelos ONNX). Agentes: creador de infoproductos (`agente_creador_infoproductos.py` — estructuras modulares, guiones, pipeline produccion), analista de tendencias (`agente_analista_tendencias_infoproductos.py` — nichos hot, pricing, estrategias lanzamiento), entrenador de ventas (`agente_entrenador_ventas_infoproductos.py` — copywriting, email marketing, funnels, afiliados).
- **División 6 — High Ticket Enterprise**: venta del framework a hedge funds y prop firms (licencia SaaS).
- **División 7 — PropFirm y Broker (FASE 5)**: fondea traders con los propios bots. Capital objetivo: 8 cifras.
- **División 8 — Fábrica de Bots y Mercado Interno**: EAs mecánicos/asistidos/híbridos + tienda + comunidad Telegram.
- **División 9 — Limpieza y Mantenimiento**: limpieza datos/modelos/logs/prompts cada domingo.
- **División 10 — Diseño y Optimización Web**: quantumhive.io + dashboard + SEO + A/B testing.
- **División 11 — Atención al Cliente y Ventas**: pipeline Lead→Bot Bienvenida→Especialista→Closer→Onboarding→Retención.
- **División 12 — Crecimiento y Optimización (meta-división)**: CEO estratégico, Scout, Clasificador, Entrenadores bots/divisiones, Supervisor global, Premios, Unidad de Capacitación (agente entrenador que ajusta parámetros de scripted agents, agente curriculum con 5 niveles de escenarios RL progresivos), prompts versionados para IA asistidas. Gestiona la evolución continua de todo el ecosistema.
- **División 13 — Legal y Compliance**: términos, contratos, regulaciones, propfirm compliance, privacidad GDPR. Sub-agentes especializados: marketing (marca ajena, promesas rendimiento, TOS plataformas), señales (CNV/CNMV/CNBV por país), sala inversión (beta ≤20, capital gestionado), PropFirms (cambios TOS mensuales), UCI (copyright/fair use). Coordinador central genera reporte diario consolidado y escala ALTO a Sergio vía Telegram.
- **División 14 — Infraestructura y DevOps**: monitoreo, backup, actualizaciones, performance, alertas críticas.
- **División 15 — Business Intelligence**: dashboard ejecutivo, métricas trading/negocio, alertas negocio, reportes inversores. Agente Dashboard Central que escanea logs de todas las divisiones, detecta estado activo/inactivo de cada agente, genera reportes ejecutivos periódicos, actualiza el dashboard HTML automáticamente y alerta tareas críticas con SLA vencido.
- **División 16 — Sala de Inversión Colmena**: hedge fund gamificado. Bots operando cuentas reales visibles en tiempo real. Clientes depositan capital, ven PnL en vivo, retiran cuando quieren. Comisión 20% QH / 80% cliente. Requiere habilitación legal antes de lanzamiento masivo.
- **División 17 — Ecosistema de Partners**: empresas de fondeo, traders independientes y gestores se suman al ecosistema. QH provee infraestructura, agentes y automatización. Cada partner tiene su sala propia en el visualizador. Estado: FUTURO — se desarrolla cuando haya track record establecido.
- **División 18 — Unidad de Conocimiento e Inteligencia (UCI)**: fábrica de datos de entrenamiento para todos los bots. Automatiza recolección, procesamiento y estructurado de conocimiento desde videos, PDFs y capturas de pantalla. Alimenta directamente entrenamiento CNN y modelos RL. Subdivisiones: 18A Recolector Video, 18B Procesador PDFs, 18C Generador CNN, 18D Base de Conocimiento vectorial, 18E Recolector Traders (descarga contenido público de traders con acuerdo CERRADO, transcribe con Whisper, extrae patrones estructurados, indexa en base vectorial con verificación legal previa).
- **División 19 — Localización y Expansión Multinacional**: gestiona la adaptación cultural, legal y lingüística de toda la operativa para 10+ mercados internacionales. Subdivisiones: 19A Coordinador de Idiomas (glosario técnico unificado), 19B Traductor Técnico (docs, notebooks, código comentado), 19C Marketing Local (landing pages por región), 19D Soporte Comunitario (FAQs, tickets, comunidades), 19E Legal Compliance por Jurisdicción (disclaimers, términos, validación regulatoria). Prioridad: EN, ES, PT, DE, FR, ZH (Fase 1); JA, RU, IT, AR (Fase 2). Integración con D4 Marketing, D11 Atención, D13 Legal.

## Instrucciones para la IA

- Respuestas cortas, paso a paso.
- Todo el código y nomenclatura en español (variables, funciones, clases, comentarios y docstrings).
- No hardcodear credenciales: usar `.env`.
- Prioridad de implementación:
  1) `nucleo/`
  2) `bots/`
  3) `automatizacion/` (agentes + scheduler)
  4) `marketing/`
- Al terminar cada archivo: confirmar qué se hizo y qué sigue.

## Estado del proyecto

### COMPLETADO

**Núcleo:**
- `nucleo/config.yaml` - global: activos, sesiones MT5 con DST, riesgo, Telegram, Kaggle, entrenamiento_visual.
- `nucleo/indicadores.py` - RSI(7), Bollinger experto (30/3 + features avanzadas: percentiles, velocidad, aceleracion, curvatura, distancias pips, toques, cierres fuera, velas consecutivas, compresion/expansion/squeeze roto), BB doble (30/3 + 25/2.5), BBW dinámico, ATR(14), EMA50, toques/cierres bandas, confluencia RSI M1/M5/M15, divergencia, funcion maestra.
- `nucleo/entorno_base.py` - gymnasium.Env: sizing 1%, SL ATR×1.5, doble TP 1:2/1:4 + BE, filtros horario/noticias, modos challenge/live, métricas finales, obs 14 features.
- `nucleo/utilidades.py` - logging por bot, métricas (winrate, PF, DD, Sharpe), checkpoints, Telegram, reportes. + detectar_horario_ny_activo(), esta_en_sesion_ny(), esta_en_ventana_apertura_ny().
- `nucleo/skills_trading.py` - detectar_sesion() con DST automático, detectar_trampas_liquidez(), calcular_score_confluencia() con score 0-160 y confluencia multi-timeframe flexible (M15 base, +15 M5, +10 M1, +30 triple).
- `nucleo/gestor_riesgo_global.py` - GestorRiesgoGlobal: DD enjambre 3%, DD cuenta challenge/live, pausa automática, alertas Telegram.
- `nucleo/validador_operacion.py` - ValidadorOperacion: 8 verificaciones (score, horario, noticias, pausas, sizing, doble exposición), log aprobadas/rechazos.
- `nucleo/exportador_onnx.py` - ExportadorONNX: SB3→ONNX opset12, validación ort vs torch, versionado, copia a EA, reporte Telegram.
- `nucleo/estructura_mercado.py` - detectar_swings(), detectar_bos_choch(), detectar_zonas_liquidez(), detectar_soporte_resistencia(), estructura_completa(H1/H4). S/R reales desde swings + clustering.
- `nucleo/analizador_m1.py` - AnalizadorM1: detecta explosiones momentum M1, sugiere ratio TP dinámico 2.0-3.5.
- `nucleo/entornos/entorno_madre.py` - EntornoMadre: **14 features** (macro H1/H4/D1/W1 + estado operativo). Acción {REVERSIÓN, CONTINUACIÓN, SCALPER}. SIEMPRE opera en sesión NY. El Madre clasifica QUÉ operar, nunca SI operar.
- `nucleo/entornos/entorno_reversion.py` - EntornoReversion: 15 features, confirmacion_m5/m1/ambos. Condiciones: toca banda + mecha, RSI extremo, BBW plano, confluencia M5/M1.
- `nucleo/entornos/entorno_continuacion.py` - EntornoContinuacion: 17 features, confirmacion_m5/m1/ambos. Condiciones: cuerpo fuera BB, BBW expandiéndose, RSI zona tendencia, EMA50/200.
- `nucleo/entornos/entorno_scalper_m5.py` - EntornoScalperM5: **19 features** (6 M5 context + 7 M1 timing + 6 estado secuencia). Operaciones M1 cortas: SL ~50 pts, TP ~100 pts (ratio 1:2). Trailing stop activa al avanzar 1 ATR. **Interés compuesto**: 3-5 trades consecutivos. Trade 1 = 1% riesgo. Trade 2 = 1% + ganancia_t1. Trade 3+ = 1% + ganancias acumuladas, cierra 80% en TP + 20% trailing. Max 5 trades/secuencia, max 2 secuencias/día. Autónomo del Bot Madre. Solo NY.
- `nucleo/orquestador.py` - Orquestador: coordina Madre→Hijo→Scalper, BE conjunto, ratio TP dinámico, límite 2 ops/2 pérdidas diarias, persistencia SQLite.
- `nucleo/entrenamiento_visual/generador_imagenes_entrenamiento.py` - genera PNG 224×224 de setups perfectos (reversión, continuación, scalper) con BB, EMA50, RSI.
- `nucleo/entrenamiento_visual/entrenador_cnn.py` - entrena ResNet18 transfer learning, early stopping, exporta ONNX.
- `nucleo/entrenamiento_visual/capturador_grafico.py` - captura gráfico actual a imagen 224×224 para CNN en producción.
- `nucleo/lector_pdfs_estrategia.py` - procesa PDFs Bollinger para Bot Madre y CrewAI. Extrae condiciones, squeeze, %B, reglas. Guarda JSON estructurado.

**Bots:**
- `automatizacion/generar_bot.py` - genera estructura de nuevo bot y registra en config.
- `bots/live/bot_live_ger40/config.yaml` - configuración GER40 sesión Europa.
- `bots/europa/bot_europa_us30/config.yaml` - configuración US30 sesión Europa, sin solapamiento con apertura NY.

**Agentes División 1 (Trading):**
- `automatizacion/agentes/agente_auditoria.py` - audita operaciones 24hs, anomalías, integridad, reporte.
- `automatizacion/agentes/agente_compliance.py` - verifica FTMO challenge/live, zona riesgo 80%, pausas, progreso, reporte diario 22hs.
- `automatizacion/agentes/agente_optimizador.py` - análisis skills, ajuste automático score_min (55-75), degradación modelo.
- `automatizacion/agentes/agente_recolector.py` - descarga datos de MT5 todos los timeframes.
- `automatizacion/scheduler.py` - BlockingScheduler APScheduler: jobs 1min/5min/15min + diarios + semanales + mensuales.

**Agentes División 2 (Fondeo):**
- `automatizacion/agentes/division_fondeo/agente_challenge.py` - gestión de pase de challenge por cliente.
- `automatizacion/agentes/division_fondeo/agente_cuentas_fondeadas.py` - registro cuentas fondeadas, balance, DD, cobro pendiente QH.
- `automatizacion/agentes/division_fondeo/agente_cobro_fondeo.py` - cobro parte QH cuando PropFirm paga.
- `automatizacion/agentes/division_fondeo/agente_afiliaciones.py` - acuerdos con PropFirms, cupones, comisiones.
- `automatizacion/agentes/division_fondeo/agente_onboarding_cliente.py` - alta de nuevo cliente, asigna bot challenge.

**Agentes División 3 (Señales):**
- `automatizacion/agentes/division_senales/agente_formateador_senales.py` - formatea señales para Telegram.
- `automatizacion/agentes/division_senales/agente_gestor_grupos.py` - gestiona accesos trial/pago/expiración.
- `automatizacion/agentes/division_senales/agente_cobro_senales.py` - cobro suscripciones MP/Stripe.
- `automatizacion/agentes/division_senales/agente_retencion.py` - clientes sin renovar, descuento recuperación.
- `automatizacion/agentes/division_senales/agente_captacion_senales.py` - publica resultados en redes, gestiona DMs.

**Agentes División 8 (Fábrica):**
- `automatizacion/agentes/division_fabrica/agente_control_calidad.py` - backtest automático, aprobación/rechazo.
- `automatizacion/agentes/division_fabrica/agente_pricing.py` - análisis mercado EAs, precio óptimo.
- `automatizacion/agentes/division_fabrica/agente_catalogo.py` - catálogo productos, descripciones, métricas.

**Agentes División 9 (Limpieza):**
- `automatizacion/agentes/division_limpieza/agente_limpieza_datos.py` - elimina datos antiguos, comprime parquet.
- `automatizacion/agentes/division_limpieza/agente_limpieza_modelos.py` - archiva ONNX obsoletos.
- `automatizacion/agentes/division_limpieza/agente_limpieza_logs.py` - rota logs >30 días, comprime .gz.
- `automatizacion/agentes/division_limpieza/agente_limpieza_prompts.py` - archiva prompts de sesiones anteriores.

**Agentes División 10 (Web):**
- `automatizacion/agentes/division_web/agente_analytics_web.py` - Google Analytics/Plausible, funnel.
- `automatizacion/agentes/division_web/agente_seo.py` - keywords competidores, contenido, posicionamiento.
- `automatizacion/agentes/division_web/agente_ab_testing.py` - variantes landing pages, conversión.
- `automatizacion/agentes/division_web/agente_diseno_contenido.py` - assets visuales web automáticos.

**Agentes División 11 (Ventas):**
- `automatizacion/agentes/division_ventas/agente_bienvenida.py` - primer contacto, califica lead, deriva.
- `automatizacion/agentes/division_ventas/agente_especialista_senales.py` - experto grupo señales.
- `automatizacion/agentes/division_ventas/agente_especialista_fondeo.py` - experto gestión challenges.
- `automatizacion/agentes/division_ventas/agente_especialista_bots.py` - experto venta EAs/bots.
- `automatizacion/agentes/division_ventas/agente_closer.py` - cierra ventas, links pago, seguimiento.
- `automatizacion/agentes/division_ventas/agente_onboarding_ventas.py` - acceso post-pago, instrucciones.
- `automatizacion/agentes/division_ventas/agente_retencion_ventas.py` - clientes inactivos, campaña retención.

**Agentes División 12 (Crecimiento):**
- `automatizacion/agentes/division_crecimiento/agente_ceo_estrategico.py` - evalúa métricas globales diarias.
- `automatizacion/agentes/division_crecimiento/agente_scout.py` - busca repos/papers/herramientas nuevas.
- `automatizacion/agentes/division_crecimiento/agente_clasificador.py` - evalúa hallazgos del scout.
- `automatizacion/agentes/division_crecimiento/agente_entrenador_bots.py` - monitorea métricas, decide reentrenar.
- `automatizacion/agentes/division_crecimiento/agente_entrenador_divisiones.py` - monitorea KPIs divisiones.
- `automatizacion/agentes/division_crecimiento/agente_supervisor_global.py` - cruza datos áreas, cuellos de botella.
- `automatizacion/agentes/division_crecimiento/agente_premios.py` - registra mejoras >5% en 7 días.

**Agentes División 13 (Legal):**
- `automatizacion/agentes/division_legal/agente_terminos.py` - términos de servicio versionados.
- `automatizacion/agentes/division_legal/agente_contratos.py` - contratos PDF clientes fondeo.
- `automatizacion/agentes/division_legal/agente_regulaciones.py` - monitorea regulaciones por país.
- `automatizacion/agentes/division_legal/agente_propfirm_compliance.py` - reglas PropFirms, alerta cambios.
- `automatizacion/agentes/division_legal/agente_privacidad.py` - GDPR, eliminación datos.

**Agentes División 14 (Infra):**
- `automatizacion/agentes/division_infra/agente_monitoreo_sistema.py` - verifica procesos cada 5 min, reinicia.
- `automatizacion/agentes/division_infra/agente_backup.py` - backup diario ONNX/SQLite/config.
- `automatizacion/agentes/division_infra/agente_actualizaciones.py` - versiones nuevas dependencias.
- `automatizacion/agentes/division_infra/agente_performance.py` - CPU/RAM/disco, alerta >80%.
- `automatizacion/agentes/division_infra/agente_alertas_criticas.py` - alertas por niveles VERDE→NEGRO.

**Agentes División 15 (BI):**
- `automatizacion/agentes/division_bi/agente_dashboard_ejecutivo.py` - reporte diario KPIs todas divisiones.
- `automatizacion/agentes/division_bi/agente_metricas_trading.py` - winrate, PF, DD, Sharpe diario.
- `automatizacion/agentes/division_bi/agente_metricas_negocio.py` - MRR, churn, LTV, CAC, proyecciones.
- `automatizacion/agentes/division_bi/agente_alertas_negocio.py` - alerta si KPI cae bajo umbral.
- `automatizacion/agentes/division_bi/agente_reportes_inversores.py` - PDF mensual profesional.

**Agentes División 16 (Sala de Inversión Colmena):**
- `automatizacion/agentes/division_sala_inversion/agente_pool_capital.py` - trackea capital de cada cliente, porcentaje del pool, PnL proporcional, historial de movimientos.
- `automatizacion/agentes/division_sala_inversion/agente_distribucion_ganancias.py` - calcula distribución 80/20 al cierre de cada sesión, genera comprobante por cliente.
- `automatizacion/agentes/division_sala_inversion/agente_sala_visual.py` - actualiza métricas en vivo de la sala: PnL del día, capital total, operaciones abiertas, equity curve.
- `automatizacion/agentes/division_sala_inversion/agente_retiros.py` - gestiona solicitudes de retiro, verifica fondos disponibles, ejecuta transferencia vía API de pago.
- `automatizacion/agentes/division_sala_inversion/agente_ceo_sala.py` - supervisa la sala, activa kill-switch si DD supera el 5% del pool total, reporta al dashboard ejecutivo.

**Agentes División 18 (Unidad de Conocimiento e Inteligencia):**
- `automatizacion/agentes/division_uci/agente_recolector_videos.py` - recibe URLs de YouTube, descarga audio con yt-dlp, transcribe con Whisper, extrae conocimiento estructurado.
- `automatizacion/agentes/division_uci/agente_procesador_pdfs.py` - procesa PDFs de `documentos/estrategias/`, extrae patrones de entrada, reglas de gestión, ejemplos de setups.
- `automatizacion/agentes/division_uci/agente_generador_cnn.py` - captura pantallazos desde MT5 en momentos de señal, los etiqueta automáticamente según resultado (ganó/perdió), guarda en `datos/imagenes_entrenamiento/validas/` e `invalidas/`.
- `automatizacion/agentes/division_uci/agente_base_conocimiento.py` - indexa todo el conocimiento procesado en base vectorial (ChromaDB/FAISS), responde consultas de otros agentes, actualiza la base cuando llega material nuevo.

**EA MQL5:**
- `ea_mql5/FiltroHorario.mqh` - DST NY automático, sesiones Asia/Europa/NY, apertura NY 90min.
- `ea_mql5/GestorRiesgoEA.mqh` - CalcularLote(), AplicarBreakEven(), CerrarParcial(), CuentaDentroDeRiesgo(), CalcularDDDiario().
- `ea_mql5/PlantillaEAHibrido.mq5` - EA completo con includes, ONNX, doble TP/BE, gestión riesgo.

**Registro y transparencia:**
- `registro/auditoria/auditoria_operaciones.py` - registro append-only con hash SHA256, verificación integridad, export por cliente.
- `registro/reporte_mensual_inversor.py` - PDF/HTML con equity curve, métricas, tablas. Fallback HTML si falta fpdf2.

**Marketing:**
- `marketing/generador_prueba_social.py` - imágenes Instagram: challenge superado, resultados semanales, estadísticas bot. Matplotlib + Pillow.
- `marketing/crm_clientes.py` - CRM: pipeline LEAD→CLIENTE, seguimiento, conversión, propuestas personalizadas.

**Documentación:**
- `LEEME.md`, `CONTEXTO.md`, `AGENTES.md`, `.windsurfrules`.

### PENDIENTE

- `pyproject.toml` (requirements.txt creado, .env.ejemplo creado).
- Notebook Kaggle completo con pipeline secuencial: Madre → Reversión/Continuación → Scalper.
- EA MQL5 `QuantumHiveEA.mq5` que carga 3 ONNX (Madre + Hijo activo + Scalper) + CNN opcional y ejecuta flujo completo del orquestador.
- Tests unitarios para `validador_operacion`, `gestor_riesgo_global`, `calcular_score_confluencia`.
- Integrar `estructura_mercado.py` en entornos como feature adicional.
- PDFs Bollinger en `documentos/` para `lector_pdfs_estrategia.py`.
- **División 16 — Sala de Inversión Colmena**: crear agentes `pool_capital`, `distribucion_ganancias`, `sala_visual`, `retiros`, `ceo_sala`. Requiere habilitación legal (División 13) antes de lanzamiento masivo. Beta cerrada: 5-10 personas.
- **División 18 — UCI**: crear agentes `recolector_videos` (yt-dlp + Whisper), `procesador_pdfs` (pdfplumber), `generador_cnn` (captura + etiquetado auto), `base_conocimiento` (ChromaDB/FAISS). Dependencias: yt-dlp, openai-whisper, chromadb, faiss-cpu, sentence-transformers.
- PROYECTO 2: Enjambre Smart Money (Order Flow, DOM, BOS, CHoCH, FVG).
- PROYECTO 3: Enjambre correlación cruzada (US30/NAS100/GER40).

### Dependencias nuevas (D18 — UCI)
- `yt-dlp>=2024.1.0` — descarga audio YouTube.
- `openai-whisper>=20231117` — transcripción audio a texto.
- `chromadb>=0.4.0` — base de conocimiento vectorial (alternativa FAISS).
- `faiss-cpu>=1.7.4` — búsqueda vectorial de alta performance.
- `sentence-transformers>=2.2.0` — embeddings semánticos para indexación.

## Confluencia multi-timeframe

- **M15 base siempre**: el bot primario opera en M15, siempre presente.
- **M5 confirma**: +15 pts al score (bueno)
- **M1 confirma**: +10 pts al score (bueno)
- **M5 + M1 juntos**: +30 pts al score (excelente, máxima probabilidad — bonus exponencial, no lineal)
- Implementado en `calcular_score_confluencia()` en `skills_trading.py`.
- Los entornos hijos tienen features `confirmacion_m5`, `confirmacion_m1`, `confirmacion_ambos` en su observation space.

## Bot Scalper M5

- **Autónomo**: no necesita activación del Bot Madre. Puede operar simultáneamente con un bot primario.
- **Solo sesión NY** (10:30-17:00hs Argentina).
- **Máximo 3 operaciones scalping por día** (cada una puede sumar hasta 3 entradas).
- **Interés compuesto en surfeo de banda**:
  - 1ra entrada: 1.0% riesgo (solo si M5 y M1 confirman)
  - 2da entrada: 0.5% riesgo (M5 sigue surfeando + M1 pullback confirmado)
  - 3ra entrada: 0.25% riesgo (mismas condiciones)
  - Total acumulado máximo: 1.75% riesgo
- **SL conjunto**: ATR(14) × 1.2 desde la primera entrada.
- **TP dinámico**: ratio 2.0-3.5 según `AnalizadorM1.calcular_ratio_tp_sugerido()`.
- **Salida inmediata**: si M5 cierra dentro de banda, o si M1 muestra reversión fuerte (3 velas contra), cerrar TODO.
- Observation space: 17 features combinadas M5 (7) + M1 (7) + state (3).

## Arquitectura de entrenamiento visual

- **CNN ResNet18** como capa adicional de confirmación sobre el score numérico.
- **Generación offline**: `generador_imagenes_entrenamiento.py` produce PNG 224×224 de setups perfectos históricos (score ≥ 80 + ganadores).
- **Entrenamiento en Kaggle**: GPU T4 ×2, 50 epochs, batch 32, early stopping (5 epochs sin mejora).
- **Exporta a ONNX** igual que los modelos RL para cargar en el EA.
- **Integración**: si CNN probabilidad > 0.70 Y score numérico ≥ 60 → operar. Si CNN < 0.50 aunque score ≥ 80 → NO operar (override visual).
- **No bloquea el sistema actual**: se activa cuando haya 500+ imágenes. Por ahora genera dataset offline mientras el bot opera.
- Configuración en `nucleo/config.yaml` → sección `entrenamiento_visual`.

## Decisiones técnicas tomadas

- `nucleo/entorno_base.py` implementa:
  - Balance/equity
  - Sizing por riesgo 1%
  - SL por ATR(14) * 1.5
  - Doble salida TP1 1:2 (50%) y TP2 1:4 (50%) con break-even tras TP1
  - Filtro horario por sesión + filtro anti-noticias
  - Modos: `challenge` y `live` con límites de drawdown
  - Métricas: winrate, profit factor, drawdown máximo, Sharpe

## Horario oficial del proyecto

- Apertura NY = **10:30hs Argentina** = **13:30hs servidor MT5** (invierno, NY en EST).
- Apertura NY = **11:30hs Argentina** = **14:30hs servidor MT5** (verano DST, NY en EDT).
- Siempre usar `detectar_horario_ny_activo()` en Python.
- Siempre usar `EstaEnAperturaNY()` en MQL5.
- DST activo: segundo domingo marzo → primer domingo noviembre.
- El sistema detecta DST automáticamente con `pytz` (Python) y cálculo dinámico de domingos (MQL5).

## Score definitivo

- **Máximo teórico**: 160 (sin correlación cruzada entre activos).
- **Mínimo para operar**: 60 (baja a 50 solo en emergencia diaria si < 2 ops).
- **Umbral riesgo**:
  - 60-79: 0.5% riesgo
  - 80-99: 1.0% riesgo
  - 100-119: 1.5% riesgo
  - ≥120: 2.0% riesgo (máx 1.5% challenge)

### Componentes del score
- Técnicos base: RSI extremo (+20), toque BB (+20), BBW expansión (+10)
- Multi-timeframe: M5 confirma (+15), M1 confirma (+10), EMAs (+15), cruce M5 (+10)
- Contexto: sentimiento (+25), régimen (+10), sesión correcta (+10)
- Zonas: O/D fresca (+35), cerca O/D (+20), S/R clave (+15), zona fresca extra (+10)
- Trampas: trampa a favor (+20)
- Penalizaciones: sentimiento contra (-30), divergencia (-20), zona contra (-15), noticia (-50), zona testeada (-10), trampa contra (-25)

## Arquitectura de 3+1 modelos

1. **EntornoMadre** — **14 features** (macro H1/H4/D1/W1 + estado operativo). Acción {REVERSIÓN(0), CONTINUACIÓN(1), SCALPER(2)}. Sin opción "no operar". NY obligatorio. El Madre clasifica QUÉ operar, nunca SI operar.
   - Features: BBW H1, BBW H4, Pendiente EMA50 H1, RSI(14) H1, Estructura H4 (0-3), Tendencia D1 EMA50, Pos vs EMA200 D1, Dist S/R D1, Tendencia W1 EMA50, Pos vs EMA200 W1, Dist S/R W1, Score confluencia, Ops hoy, PnL día.
2. **EntornoReversión** — 15 features, activado solo por Madre. Confirmaciones M5/M1 en obs. Condiciones: toca banda + mecha, RSI extremo, BBW plano, confluencia M5/M1. SL ~150 pts, TP 300-600.
3. **EntornoContinuación** — 17 features, activado solo por Madre. Confirmaciones M5/M1 en obs. Condiciones: cuerpo fuera BB, BBW expandiéndose, RSI zona tendencia, EMA50/200. SL ~150 pts, TP 300-600.
4. **EntornoScalperM5** — **19 features** (6 M5 context + 7 M1 timing + 6 estado secuencia). AUTÓNOMO del Bot Madre. Operaciones M1 cortas: SL ~50 pts (ATR×1.2), TP ~100 pts (ratio 1:2). Trailing stop sube 0.8 ATR cuando avanza 1 ATR. **Secuencia interés compuesto 3-5 trades**: Trade 1 = 1% riesgo. Trade 2 = 1% + ganancia_t1. Trade 3+ = 1% + ganancias acumuladas, cierra 80% en TP + 20% trailing. Max 5 trades/secuencia, max 2 secuencias/día. Solo NY.
- Doble TP 1:2/1:4 + BE en modelos primarios hijos; TP dinámico 2.0-3.5 en Scalper.
- Sistema DEBE generar mínimo 2 operaciones por día (Madre obliga NY). Scalper puede sumar posiciones adicionales.

## Próximos pasos priorizados

1) **FASE 2**: Entrenamiento Kaggle del bot us30_apertura con arquitectura de 3 modelos (Madre + Reversión + Continuación).
2) Notebook Kaggle adaptado con pipeline secuencial: Madre → Reversión/Continuación.
3) Backtesting integrado de los 3 modelos funcionando juntos.
4) EA MQL5 final que carga los 3 ONNX y ejecuta flujo completo.
5) `requirements.txt`, `pyproject.toml`, `.env.ejemplo`.

### Proyectos futuros
- **PROYECTO 2**: Enjambre Smart Money (Order Flow, DOM, BOS, CHoCH, FVG, Liquidity Pools).
- **PROYECTO 3**: Enjambre correlación cruzada (US30/NAS100/GER40) — independiente del enjambre principal.
- Agentes adicionales: noticias, sentimiento social, copy trading, backtesting continuo.

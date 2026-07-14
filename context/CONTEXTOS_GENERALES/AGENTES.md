# AGENTES QuantumHive (CrewAI)

QuantumHive opera 7 Divisiones, cada una con agentes autónomos especializados.

---

## DIVISION 1 — Enjambre de Trading (OPERATIVA)

### `agente_recolector.py` ✅
- Descarga automática de **todos los timeframes**: M1, M5, M15, H1, H4, D1, W1.
- Para todos los activos configurados en `config.yaml`.
- El Bot Madre siempre tiene datos macro (D1, W1) disponibles.
- Guarda en `datos/historicos/` (parquet) y `datos/en_vivo/`.
- Corre cada 5 minutos.

### `agente_riesgo.py` ✅
- Monitorea drawdown en tiempo real del enjambre completo.
- Pausa bots según reglas:
  - Challenge: máx -4% diario, -8% total.
  - Live: máx -3% diario, -6% total.
  - Enjambre: DD global 3%.

### `agente_auditoria.py` ✅
- Audita operaciones 24hs, anomalías, integridad de cuentas.
- Registro append-only SHA256.
- Reporte diario 17:00hs.

### `agente_compliance.py` ✅
- Verifica FTMO challenge/live, zona riesgo 80%.
- Reporte diario 22:00hs.

### `agente_optimizador.py` ✅
- Análisis de skills, ajuste automático score_min (55-75).
- Detecta degradación de modelo, sugiere re-entrenamiento.
- Ajustes semanales limitados a 1 por semana.

### `agente_entrenador.py` (PENDIENTE)
- Detecta necesidad de reentrenamiento.
- Lanza jobs en Kaggle vía API con GPU T4 x2.
- Descarga checkpoints y modelos ONNX.
- Notifica por Telegram.

### `agente_tester.py` (PENDIENTE)
- Backtesting automático con datos históricos.
- Evalúa por sesión (Asia/Europa/NY).
- Reporta winrate, drawdown, profit factor, Sharpe.

---

## DIVISION 2 — Gestión de Fondeo y Challenges (FASE 2)

### `agente_challenge.py` ✅ (P0)
- Gestiona pase de challenge: AGRESIVO / PASAR RÁPIDO.
- Monitorea DD, profit target, días operados.
- Persiste estado en `datos/challenges.json`.

### `agente_cuentas_fondeadas.py` ✅ (P1)
- Registra cuentas fondeadas activas: balance, DD, ganancia.
- Calcula cobro pendiente QuantumHive (split 40% QH / 40% cliente / 20% PropFirm).
- Historial de retiros en `datos/cuentas_fondeadas.json`.

### `agente_cobro_fondeo.py` (PENDIENTE)
- Cobra parte QuantumHive cuando PropFirm paga.
- MercadoPago, PayPal, cripto, transferencia.

### `agente_afiliaciones.py` (PENDIENTE)
- Acuerdos con PropFirms oficiales.
- Cupones, enlaces, seguimiento comisiones.

### `agente_onboarding_cliente.py` (PENDIENTE)
- Alta de nuevo cliente en challenge.
- Asigna bot, entrega documentación.

---

## DIVISION 3 — Grupo de Señales (FASE 2)

### `agente_formateador_senales.py` ✅ (P0)
- Toma decisión del orquestador y formatea mensaje para Telegram.
- Incluye entrada, SL, TP1, TP2, contexto, sesión.
- Persiste en `registro/senales_enviadas.json`.

### `agente_gestor_grupos.py` ✅ (P1)
- Gestiona trial 3 días / pago semanal / pago mensual.
- Expulsa vencidos automáticamente.
- Persiste en `datos/suscriptores_señales.json`.

### `agente_cobro_senales.py` (PENDIENTE)
- Links de pago automáticos por MercadoPago / Stripe.
- Gestiona pagos semanales y mensuales.

### `agente_retencion.py` (PENDIENTE)
- Detecta clientes sin renovar, envía descuento recuperación.

### `agente_captacion_senales.py` (PENDIENTE)
- Publica resultados en redes, gestiona DMs.

---

## DIVISION 4 — Marketing y Captación (FASE 2)

### `agente_contenido_instagram.py` ✅ (base en marketing/)
- Genera imágenes con resultados reales del enjambre.
- Stories, posts, carrusel.

### `agente_viral_seo.py` (PENDIENTE)
- Optimiza contenido para viralización y SEO.

### `agente_captacion_dms.py` (PENDIENTE)
- Responde DMs automáticamente, califica leads.

### `agente_cierre_ventas.py` (PENDIENTE)
- Cierra ventas automáticamente con propuestas personalizadas.

---

## DIVISION 5 — Infoproductos y Afiliados (FASE 3)

### `agente_creador_infoproductos.py` (PENDIENTE)
- Usa Claude API para crear cursos completos:
  - "Crear bots IA para trading"
  - "Sistema Bollinger profesional"
  - "Pasar challenges de fondeo"
  - "Trading algorítmico desde cero"

### `agente_publicador_hotmart.py` (PENDIENTE)
- Publica cursos en Hotmart/Udemy/Teachable.

### `agente_marketplace_productos.py` (PENDIENTE)
- Gestiona marketplace propio + MQL5 Market.
- EAs híbridos, EAs 100% IA, scripts, datasets, modelos ONNX.

### `agente_afiliados.py` (PENDIENTE)
- Tracking de afiliados y pagos automáticos de comisiones.

---

## DIVISION 6 — High Ticket Enterprise (FASE 4)

### `agente_enterprise_sales.py` (PENDIENTE)
- Venta del framework QuantumHive a hedge funds y prop firms.

### `agente_gestor_licencias.py` (PENDIENTE)
- Gestiona licencias SaaS mensuales del framework.

### `agente_soporte_tecnico.py` (PENDIENTE)
- Soporte dedicado a clientes enterprise.

---

## DIVISION 7 — PropFirm y Broker (FASE 5)

### `agente_propfirm.py` (PENDIENTE)
- Fondea traders con los propios bots de QuantumHive.
- Gestión de capital institucional.

### `orquestador.py` ✅
- Coordina todos los agentes de Division 1 en tiempo real.
- Prioridades, reintentos, manejo de errores.
- Persistencia SQLite para recuperación tras crash.

---

## DIVISION 8 — Fábrica de Bots y Mercado Interno (FASE 3)

### `agente_control_calidad.py` (PENDIENTE)
- Backtest automático, aprobación/rechazo de bots.

### `agente_pricing.py` (PENDIENTE)
- Análisis mercado EAs, precio óptimo.

### `agente_catalogo.py` (PENDIENTE)
- Catálogo productos, descripciones, métricas.

---

## DIVISION 9 — Limpieza y Mantenimiento

### `agente_limpieza_datos.py` (PENDIENTE)
- Elimina datos antiguos, comprime parquet.

### `agente_limpieza_modelos.py` (PENDIENTE)
- Archiva ONNX obsoletos.

### `agente_limpieza_logs.py` (PENDIENTE)
- Rota logs >30 días, comprime .gz.

### `agente_limpieza_prompts.py` (PENDIENTE)
- Archiva prompts de sesiones anteriores.

---

## DIVISION 10 — Diseño y Optimización Web

### `agente_analytics_web.py` (PENDIENTE)
- Google Analytics / Plausible, funnel conversiones.

### `agente_seo.py` (PENDIENTE)
- Keywords competidores, contenido, posicionamiento.

### `agente_ab_testing.py` (PENDIENTE)
- Variantes landing pages, conversión.

### `agente_diseno_contenido.py` (PENDIENTE)
- Assets visuales web automáticos.

---

## DIVISION 11 — Atención al Cliente y Ventas

### `agente_bienvenida.py` ✅ (P0)
- Primer contacto, califica lead (señales / fondeo / bots).
- Deriva a especialista. SLA: 5 minutos.

### `agente_especialista_senales.py` (PENDIENTE)
- Expertos en grupo de señales.

### `agente_especialista_fondeo.py` (PENDIENTE)
- Expertos en gestión de challenges.

### `agente_especialista_bots.py` (PENDIENTE)
- Expertos en venta de EAs / bots.

### `agente_closer.py` ✅ (P1)
- Cierra ventas, links pago MP/Stripe/cripto, seguimiento.

### `agente_onboarding_ventas.py` (PENDIENTE)
- Acceso post-pago, instrucciones, documentación.

### `agente_retencion_ventas.py` (PENDIENTE)
- Clientes inactivos, campaña retención.

---

## DIVISION 12 — Crecimiento y Optimización (Meta-División)

### `agente_ceo_estrategico.py` (PENDIENTE)
- Evalúa métricas globales diarias, ordena auditoría.

### `agente_scout.py` (PENDIENTE)
- Busca repos / papers / herramientas nuevas.

### `agente_clasificador.py` (PENDIENTE)
- Evalúa hallazgos del scout, relevancia/prioridad.

### `agente_entrenador_bots.py` (PENDIENTE)
- Monitorea métricas bots, decide reentrenar.

### `agente_entrenador_divisiones.py` (PENDIENTE)
- Monitorea KPIs divisiones, ajusta agentes.

### `agente_supervisor_global.py` ✅ (P0)
- Cruza datos áreas, detecta cuellos de botella.

### `agente_premios.py` (PENDIENTE)
- Registra mejoras >5% en 7 días.

---

## DIVISION 13 — Legal y Compliance

### `agente_terminos.py` (PENDIENTE)
- Términos de servicio versionados.

### `agente_contratos.py` (PENDIENTE)
- Contratos PDF clientes fondeo.

### `agente_regulaciones.py` (PENDIENTE)
- Monitorea regulaciones por país.

### `agente_propfirm_compliance.py` (PENDIENTE)
- Reglas PropFirms, alerta cambios.

### `agente_privacidad.py` (PENDIENTE)
- GDPR, eliminación datos.

---

## DIVISION 14 — Infraestructura y DevOps

### `agente_monitoreo_sistema.py` ✅ (P0)
- Verifica procesos críticos cada 5 min, reinicia.
- Heartbeat de todos los agentes.

### `agente_backup.py` ✅ (P1)
- Backup diario ONNX / SQLite / config.

### `agente_actualizaciones.py` (PENDIENTE)
- Versiones nuevas dependencias.

### `agente_performance.py` (PENDIENTE)
- CPU/RAM/disco, alerta >80%.

### `agente_alertas_criticas.py` ✅ (P0)
- Alertas por niveles: VERDE → NEGRO.
- DD 50% / 75% / 90% / superado.

---

## DIVISION 15 — Business Intelligence

### `agente_dashboard_ejecutivo.py` ✅ (P0)
- Reporte diario KPIs todas las divisiones.
- 20:00 Argentina → Telegram Sergio.

### `agente_metricas_trading.py` (PENDIENTE)
- Winrate, PF, DD, Sharpe diario.

### `agente_metricas_negocio.py` ✅ (P1)
- MRR, churn, LTV, CAC, proyecciones.

### `agente_alertas_negocio.py` (PENDIENTE)
- Alerta si KPI cae bajo umbral.

### `agente_reportes_inversores.py` (PENDIENTE)
- PDF mensual profesional.

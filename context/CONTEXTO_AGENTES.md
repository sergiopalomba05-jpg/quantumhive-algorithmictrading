# CONTEXTO AGENTES — Registro Completo

## Leyenda

| Campo | Descripcion |
|-------|-------------|
| Nombre | Identificador unico del agente |
| Macro | Macrodivision asignada |
| Division | Division dentro de la macro |
| Funcion | Responsabilidad principal |
| Archivo | Ruta del archivo fuente |
| Estado | Activo / Planificado / En desarrollo |
| Score SPPR | Score actual (inicial 70, max 100) |

---

## Macro 1 — Trading Core

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| agente_auditoria | D1 Enjambre CFDs | Audita operaciones 24h, anomalias, integridad, reporte | `automatizacion/agentes/agente_auditoria.py` | Activo | 70 |
| agente_compliance | D1 Enjambre CFDs | Verifica FTMO challenge/live, zona riesgo 80%, pausas, progreso | `automatizacion/agentes/agente_compliance.py` | Activo | 70 |
| agente_optimizador | D1 Enjambre CFDs | Analisis skills, ajuste automatico score_min (55-75), degradacion modelo | `automatizacion/agentes/agente_optimizador.py` | Activo | 70 |
| agente_recolector | D1 Enjambre CFDs | Descarga datos de MT5 todos los timeframes | `automatizacion/agentes/agente_recolector.py` | Activo | 70 |
| agente_challenge | D2 Fondeo | Gestion pase challenge por cliente | `automatizacion/agentes/division_fondeo/agente_challenge.py` | Activo | 70 |
| agente_cuentas_fondeadas | D2 Fondeo | Registro cuentas fondeadas, balance, DD, cobro QH | `automatizacion/agentes/division_fondeo/agente_cuentas_fondeadas.py` | Activo | 70 |
| agente_cobro_fondeo | D2 Fondeo | Cobro parte QH cuando PropFirm paga | `automatizacion/agentes/division_fondeo/agente_cobro_fondeo.py` | Activo | 70 |
| agente_afiliaciones | D2 Fondeo | Acuerdos con PropFirms, cupones, comisiones | `automatizacion/agentes/division_fondeo/agente_afiliaciones.py` | Activo | 70 |
| agente_onboarding_cliente | D2 Fondeo | Alta nuevo cliente, asigna bot challenge | `automatizacion/agentes/division_fondeo/agente_onboarding_cliente.py` | Activo | 70 |
| selector_cuenta | D2B PropFirms Dispersion | Asigna cuenta por servidor MT5, firma, riesgo residual | `automatizacion/agentes/division_fondeo/selector_cuenta.py` | Planificado | 70 |
| dispersor_cuentas | D2B PropFirms Dispersion | Delay/variacion unicos por cuenta para evitar deteccion | `automatizacion/agentes/division_fondeo/dispersor_cuentas.py` | Planificado | 70 |
| monitor_dd_prop | D2B PropFirms Dispersion | Alerta contra limites de firma | `automatizacion/agentes/division_fondeo/monitor_dd_prop.py` | Planificado | 70 |
| gestor_rotacion | D2B PropFirms Dispersion | Congelamiento por racha perdedora, scheduling diario, retiros | `automatizacion/agentes/division_fondeo/gestor_rotacion.py` | Planificado | 70 |
| agente_pool_capital | D16 Sala Colmena | Tracking capital por cliente, porcentaje pool, PnL proporcional | `automatizacion/agentes/division_sala_inversion/agente_pool_capital.py` | Planificado | 70 |
| agente_distribucion_ganancias | D16 Sala Colmena | Calculo 80/20 por sesion, comprobantes por cliente | `automatizacion/agentes/division_sala_inversion/agente_distribucion_ganancias.py` | Planificado | 70 |
| agente_sala_visual | D16 Sala Colmena | Metricas en vivo: PnL dia, capital total, ops abiertas, equity | `automatizacion/agentes/division_sala_inversion/agente_sala_visual.py` | Planificado | 70 |
| agente_retiros | D16 Sala Colmena | Gestiona solicitudes retiro, verifica fondos, transferencia API | `automatizacion/agentes/division_sala_inversion/agente_retiros.py` | Planificado | 70 |
| agente_ceo_sala | D16 Sala Colmena | Supervisa sala, kill-switch si DD>5% pool, reporte dashboard | `automatizacion/agentes/division_sala_inversion/agente_ceo_sala.py` | Planificado | 70 |
| bot_manager | D-NEW GVCA | Monitorea estado, logs, metricas, reinicio automatico por bot | `automatizacion/agentes/gvca/bot_manager.py` | Planificado | 70 |
| vps_manager | D-NEW GVCA | Provisioning, escalado, rotacion, costos VPS | `automatizacion/agentes/gvca/vps_manager.py` | Planificado | 70 |
| anti_deteccion | D-NEW GVCA | Fingerprint unico por instancia, proxies rotativos | `automatizacion/agentes/gvca/anti_deteccion.py` | Planificado | 70 |
| compliance_prop | D-NEW GVCA | Verifica TOS de cada firma, detecta cambios, ajusta bot | `automatizacion/agentes/gvca/compliance_prop.py` | Planificado | 70 |
| cloud_infra | D-NEW GVCA | Orquestacion containers, balanceo, failover | `automatizacion/agentes/gvca/cloud_infra.py` | Planificado | 70 |

---

## Macro 2 — Operaciones Internas

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| the_cleaner | D9 Limpieza | Comprime logs >7 dias, elimina duplicados, hot/cold storage | `automatizacion/agentes/division_limpieza/the_cleaner.py` | Planificado | 70 |
| the_optimizer | D9 Limpieza | Monitorea latencia agentes, mueve agentes lentos a modelos mas rapidos | `automatizacion/agentes/division_limpieza/the_optimizer.py` | Planificado | 70 |
| agente_limpieza_datos | D9 Limpieza | Elimina datos antiguos, comprime parquet | `automatizacion/agentes/division_limpieza/agente_limpieza_datos.py` | Activo | 70 |
| agente_limpieza_modelos | D9 Limpieza | Archiva ONNX obsoletos | `automatizacion/agentes/division_limpieza/agente_limpieza_modelos.py` | Activo | 70 |
| agente_limpieza_logs | D9 Limpieza | Rota logs >30 dias, comprime .gz | `automatizacion/agentes/division_limpieza/agente_limpieza_logs.py` | Activo | 70 |
| agente_limpieza_prompts | D9 Limpieza | Archiva prompts de sesiones anteriores | `automatizacion/agentes/division_limpieza/agente_limpieza_prompts.py` | Activo | 70 |
| agente_ceo_estrategico | D12 Crecimiento | Evalua metricas globales diarias | `automatizacion/agentes/division_crecimiento/agente_ceo_estrategico.py` | Activo | 70 |
| agente_scout | D12 Crecimiento | Busca repos/papers/herramientas nuevas | `automatizacion/agentes/division_crecimiento/agente_scout.py` | Activo | 70 |
| agente_clasificador | D12 Crecimiento | Evalua hallazgos del scout | `automatizacion/agentes/division_crecimiento/agente_clasificador.py` | Activo | 70 |
| agente_entrenador_bots | D12 Crecimiento | Monitorea metricas bots, decide reentrenar | `automatizacion/agentes/division_crecimiento/agente_entrenador_bots.py` | Activo | 70 |
| agente_entrenador_divisiones | D12 Crecimiento | Monitorea KPIs divisiones | `automatizacion/agentes/division_crecimiento/agente_entrenador_divisiones.py` | Activo | 70 |
| agente_supervisor_global | D12 Crecimiento | Cruza datos areas, detecta cuellos de botella | `automatizacion/agentes/division_crecimiento/agente_supervisor_global.py` | Activo | 70 |
| agente_premios | D12 Crecimiento | Registra mejoras >5% en 7 dias | `automatizacion/agentes/division_crecimiento/agente_premios.py` | Activo | 70 |
| auditor_sppr | D12 Crecimiento | Califica outputs agentes, devuelve feedback, actualiza score | `automatizacion/agentes/division_crecimiento/auditor_sppr.py` | Planificado | 70 |
| agente_terminos | D13 Legal | Terminos de servicio versionados | `automatizacion/agentes/division_legal/agente_terminos.py` | Activo | 70 |
| agente_contratos | D13 Legal | Contratos PDF clientes fondeo | `automatizacion/agentes/division_legal/agente_contratos.py` | Activo | 70 |
| agente_regulaciones | D13 Legal | Monitorea regulaciones por pais | `automatizacion/agentes/division_legal/agente_regulaciones.py` | Activo | 70 |
| agente_propfirm_compliance | D13 Legal | Reglas PropFirms, alerta cambios TOS | `automatizacion/agentes/division_legal/agente_propfirm_compliance.py` | Activo | 70 |
| agente_privacidad | D13 Legal | GDPR, eliminacion datos | `automatizacion/agentes/division_legal/agente_privacidad.py` | Activo | 70 |
| agente_monitoreo_sistema | D14 Infra | Verifica procesos cada 5 min, reinicia | `automatizacion/agentes/division_infra/agente_monitoreo_sistema.py` | Activo | 70 |
| agente_backup | D14 Infra | Backup diario ONNX/SQLite/config | `automatizacion/agentes/division_infra/agente_backup.py` | Activo | 70 |
| agente_actualizaciones | D14 Infra | Versiones nuevas dependencias | `automatizacion/agentes/division_infra/agente_actualizaciones.py` | Activo | 70 |
| agente_performance | D14 Infra | CPU/RAM/disco, alerta >80% | `automatizacion/agentes/division_infra/agente_performance.py` | Activo | 70 |
| agente_alertas_criticas | D14 Infra | Alertas por niveles VERDE->NEGRO | `automatizacion/agentes/division_infra/agente_alertas_criticas.py` | Activo | 70 |
| agente_dashboard_ejecutivo | D15 BI | Reporte diario KPIs todas divisiones | `automatizacion/agentes/division_bi/agente_dashboard_ejecutivo.py` | Activo | 70 |
| agente_metricas_trading | D15 BI | Winrate, PF, DD, Sharpe diario | `automatizacion/agentes/division_bi/agente_metricas_trading.py` | Activo | 70 |
| agente_metricas_negocio | D15 BI | MRR, churn, LTV, CAC, proyecciones | `automatizacion/agentes/division_bi/agente_metricas_negocio.py` | Activo | 70 |
| agente_alertas_negocio | D15 BI | Alerta si KPI cae bajo umbral | `automatizacion/agentes/division_bi/agente_alertas_negocio.py` | Activo | 70 |
| agente_reportes_inversores | D15 BI | PDF mensual profesional | `automatizacion/agentes/division_bi/agente_reportes_inversores.py` | Activo | 70 |
| the_broker | D-NEW DLRI | Administra API keys, asigna API por nivel reputacion, rotacion 429 | `automatizacion/agentes/dlri/the_broker.py` | Planificado | 70 |
| the_hunter | D-NEW DLRI | Busca APIs gratuitas, creditos bienvenida, modelos OpenRouter $0 | `automatizacion/agentes/dlri/the_hunter.py` | Planificado | 70 |
| ugcc_manager | D-NEW UGCC | Divide archivos contexto, mantiene indice maestro, referencias cruzadas | `automatizacion/agentes/ugcc/ugcc_manager.py` | Planificado | 70 |
| vault | D-NEW USEC | Credenciales, rotacion automatica keys, cifrado reposo | `automatizacion/agentes/usec/vault.py` | Planificado | 70 |
| firewall | D-NEW USEC | Control accesos, deteccion anomalias uso, alerta patrones sospechosos | `automatizacion/agentes/usec/firewall.py` | Planificado | 70 |
| anti_colapso | D-NEW USEC | Monitorea CPU/RAM/disco/tokens en tiempo real, frena procesos | `automatizacion/agentes/usec/anti_colapso.py` | Planificado | 70 |
| backup_usec | D-NEW USEC | Snapshot automatico antes cambio mayor, rollback <60 seg | `automatizacion/agentes/usec/backup_usec.py` | Planificado | 70 |
| guardrails | D-NEW USEC | Valida outputs entre divisiones, frena codigo contradictorio | `automatizacion/agentes/usec/guardrails.py` | Planificado | 70 |

---

## Macro 3 — Marketing y Ventas

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| agente_formateador_senales | D3 Senales | Formatea senales para Telegram | `automatizacion/agentes/division_senales/agente_formateador_senales.py` | Activo | 70 |
| agente_gestor_grupos | D3 Senales | Gestiona accesos trial/pago/expiracion | `automatizacion/agentes/division_senales/agente_gestor_grupos.py` | Activo | 70 |
| agente_cobro_senales | D3 Senales | Cobro suscripciones MP/Stripe | `automatizacion/agentes/division_senales/agente_cobro_senales.py` | Activo | 70 |
| agente_retencion | D3 Senales | Clientes sin renovar, descuento recuperacion | `automatizacion/agentes/division_senales/agente_retencion.py` | Activo | 70 |
| agente_captacion_senales | D3 Senales | Publica resultados en redes, gestiona DMs | `automatizacion/agentes/division_senales/agente_captacion_senales.py` | Activo | 70 |
| agente_partnerships_traders | D4 Marketing | Pipeline con traders reconocidos | `automatizacion/agentes/division_marketing/agente_partnerships_traders.py` | Activo | 70 |
| agente_captacion_seguidores | D4 Marketing | Post-acuerdo con rate limit 50/dia | `automatizacion/agentes/division_marketing/agente_captacion_seguidores.py` | Activo | 70 |
| agente_naming_bots | D4 Marketing | Generador nombres tecnicos propios para bots | `automatizacion/agentes/division_marketing/agente_naming_bots.py` | Activo | 70 |
| agente_analytics_web | D4 Marketing | Google Analytics/Plausible, funnel | `automatizacion/agentes/division_web/agente_analytics_web.py` | Activo | 70 |
| agente_seo | D4 Marketing | Keywords competidores, contenido, posicionamiento | `automatizacion/agentes/division_web/agente_seo.py` | Activo | 70 |
| agente_ab_testing | D4 Marketing | Variantes landing pages, conversion | `automatizacion/agentes/division_web/agente_ab_testing.py` | Activo | 70 |
| agente_diseno_contenido | D4 Marketing | Assets visuales web automaticos | `automatizacion/agentes/division_web/agente_diseno_contenido.py` | Activo | 70 |
| agente_creador_infoproductos | D5 Infoproductos | Estructuras modulares, guiones, pipeline produccion | `automatizacion/agentes/division_infoproductos/agente_creador_infoproductos.py` | Activo | 70 |
| agente_analista_tendencias | D5 Infoproductos | Nichos hot, pricing, estrategias lanzamiento | `automatizacion/agentes/division_infoproductos/agente_analista_tendencias.py` | Activo | 70 |
| agente_entrenador_ventas | D5 Infoproductos | Copywriting, email marketing, funnels, afiliados | `automatizacion/agentes/division_infoproductos/agente_entrenador_ventas.py` | Activo | 70 |
| agente_bienvenida | D11 Ventas | Primer contacto, califica lead, deriva | `automatizacion/agentes/division_ventas/agente_bienvenida.py` | Activo | 70 |
| agente_especialista_senales | D11 Ventas | Experto grupo senales | `automatizacion/agentes/division_ventas/agente_especialista_senales.py` | Activo | 70 |
| agente_especialista_fondeo | D11 Ventas | Experto gestion challenges | `automatizacion/agentes/division_ventas/agente_especialista_fondeo.py` | Activo | 70 |
| agente_especialista_bots | D11 Ventas | Experto venta EAs/bots | `automatizacion/agentes/division_ventas/agente_especialista_bots.py` | Activo | 70 |
| agente_closer | D11 Ventas | Cierra ventas, links pago, seguimiento | `automatizacion/agentes/division_ventas/agente_closer.py` | Activo | 70 |
| agente_onboarding_ventas | D11 Ventas | Acceso post-pago, instrucciones | `automatizacion/agentes/division_ventas/agente_onboarding_ventas.py` | Activo | 70 |
| agente_retencion_ventas | D11 Ventas | Clientes inactivos, campana retencion | `automatizacion/agentes/division_ventas/agente_retencion_ventas.py` | Activo | 70 |
| humanizador_agentes | D-NEW Humanizacion | Comportamiento humano simulado, variacion semantica/temporal | `automatizacion/agentes/humanizacion/humanizador_agentes.py` | Planificado | 70 |
| explorador_lt | D-NEW UMI-LT | Detecta oportunidades ingreso rapido, bajo costo, alto volumen | `automatizacion/agentes/umi/explorador_lt.py` | Planificado | 70 |
| optimizador_division_lt | D-NEW UMI-LT | Adapta productos existentes a formatos low ticket | `automatizacion/agentes/umi/optimizador_division_lt.py` | Planificado | 70 |
| afiliados_externos | D-NEW UMI-LT | Gestiona red afiliados fuera ecosistema Colmena | `automatizacion/agentes/umi/afiliados_externos.py` | Planificado | 70 |
| lanzamientos_rapidos | D-NEW UMI-LT | Micro-productos en <72h desde idea | `automatizacion/agentes/umi/lanzamientos_rapidos.py` | Planificado | 70 |
| pricing_dinamico | D-NEW UMI-LT | Ajusta precios segun demanda, competencia, momento mes | `automatizacion/agentes/umi/pricing_dinamico.py` | Planificado | 70 |
| explorador_ht | D-NEW UMI-HT | Identifica empresas objetivo, contactos C-level, oportunidades B2B | `automatizacion/agentes/umi/explorador_ht.py` | Planificado | 70 |
| propuestas_enterprise | D-NEW UMI-HT | Genera propuestas personalizadas, ROI calculado, casos exito | `automatizacion/agentes/umi/propuestas_enterprise.py` | Planificado | 70 |
| nicho_hunter | D-NEW UMI-HT | Descubre nichos desatendidos con alto poder adquisitivo | `automatizacion/agentes/umi/nicho_hunter.py` | Planificado | 70 |
| partnerships_estrategicos | D-NEW UMI-HT | Alianzas con propfirms, brokers, plataformas educativas | `automatizacion/agentes/umi/partnerships_estrategicos.py` | Planificado | 70 |
| mentorship_pipeline | D-NEW UMI-HT | Gestiona lista espera mentorship Sergio, filtra calidad | `automatizacion/agentes/umi/mentorship_pipeline.py` | Planificado | 70 |
| director_umi | D-NEW UMI-DIR | Consolida estrategia precios global, evita canibalizacion | `automatizacion/agentes/umi/director_umi.py` | Planificado | 70 |
| metricas_monetizacion | D-NEW UMI-DIR | ARPU, LTV, CAC por canal, cohort analysis, churn predictivo | `automatizacion/agentes/umi/metricas_monetizacion.py` | Planificado | 70 |
| ceo_ucmi | D-NEW UCMI | Supervisa flujos captacion, mide CPA, optimiza ganchos ROI por canal | `automatizacion/agentes/ucmi/ceo_ucmi.py` | Futuro | 70 |
| gancho_masivo | D-NEW UCMI | Crea grupos Telegram lanzamiento, logica urgencia 48hs gratis | `automatizacion/agentes/ucmi/gancho_masivo.py` | Futuro | 70 |
| explorador_puntos_calientes | D-NEW UCMI | Escanea Twitter/Reddit/Telegram/YouTube comunidades sin estructura | `automatizacion/agentes/ucmi/explorador_puntos_calientes.py` | Futuro | 70 |
| influencer_hunter | D-NEW UCMI | Encuentra influencers nicho, engagement real, audiencia traders | `automatizacion/agentes/ucmi/influencer_hunter.py` | Futuro | 70 |
| closer_influencers | D-NEW UCMI | Contacta influencers, presenta propuesta, negocia terminos | `automatizacion/agentes/ucmi/closer_influencers.py` | Futuro | 70 |

---

## Macro 4 — Fábrica de Bots e Infoproductos

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| agente_control_calidad | D8 Fabrica | Backtest automatico, aprobacion/rechazo antes de release | `automatizacion/agentes/division_fabrica/agente_control_calidad.py` | Activo | 70 |
| agente_pricing | D8 Fabrica | Analisis mercado EAs, precio optimo | `automatizacion/agentes/division_fabrica/agente_pricing.py` | Activo | 70 |
| agente_catalogo | D8 Fabrica | Catalogo productos, descripciones, metricas | `automatizacion/agentes/division_fabrica/agente_catalogo.py` | Activo | 70 |
| agente_recolector_videos | D18 UCI | Recibe URLs YouTube, descarga audio yt-dlp, transcribe Whisper | `automatizacion/agentes/division_uci/agente_recolector_videos.py` | Planificado | 70 |
| agente_procesador_pdfs | D18 UCI | Procesa PDFs estrategias, extrae patrones, guarda JSON | `automatizacion/agentes/division_uci/agente_procesador_pdfs.py` | Planificado | 70 |
| agente_generador_cnn | D18 UCI | Captura pantallazos MT5, etiqueta auto, guarda validas/invalidas | `automatizacion/agentes/division_uci/agente_generador_cnn.py` | Planificado | 70 |
| agente_base_conocimiento | D18 UCI | Indexa conocimiento en ChromaDB/FAISS, responde consultas agentes | `automatizacion/agentes/division_uci/agente_base_conocimiento.py` | Planificado | 70 |
| agente_clonador | D-NEW Pipeline Fábrica | Genera variantes bot con distintos activos y parametros | `automatizacion/agentes/division_fabrica/agente_clonador.py` | Futuro | 70 |
| backtester_automatico | D-NEW Pipeline Fábrica | Corre backtest cada clon, reporte WR/DD/factor beneficio | `automatizacion/agentes/division_fabrica/backtester_automatico.py` | Futuro | 70 |
| publisher | D-NEW Pipeline Fábrica | Sube bot aprobado MQL5 Market, gestiona precio, actualizaciones | `automatizacion/agentes/division_fabrica/publisher.py` | Futuro | 70 |
| experimentador | D-NEW Pipeline Fábrica | Combina estrategias, prueba cerebro ONNX activos nuevos | `automatizacion/agentes/division_fabrica/experimentador.py` | Futuro | 70 |
| qa_fabrica | D-NEW Pipeline Fábrica | Test obligatorio antes publicar, backtest walk-forward, validacion | `automatizacion/agentes/division_fabrica/qa_fabrica.py` | Futuro | 70 |

---

## Macro 5 — Innovacion y Proyectos Futuros

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| gestor_partners | D17 Ecosistema Partners | Onboarding partners, licencia tecnologia, revenue share tracking | `automatizacion/agentes/division_partners/gestor_partners.py` | Planificado | 70 |
| monitor_track_record | D17 Ecosistema Partners | Valida requisitos entrada partner (track record 6m, capital 500K) | `automatizacion/agentes/division_partners/monitor_track_record.py` | Planificado | 70 |
| desarrollador_smart_money | Proyecto 2 | Implementa Order Flow, DOM, BOS, CHoCH, FVG, Liquidity Pools | `automatizacion/agentes/proyectos/desarrollador_smart_money.py` | Planificado | 70 |
| analista_correlacion | Proyecto 3 | Detector correlacion rolling 20 barras, arbitraje estadistico | `automatizacion/agentes/proyectos/analista_correlacion.py` | Planificado | 70 |

---

## Macro 6 — Legal, Finanzas & Advisory

### Macro 6A — Legal & Advisory

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| consejero_legal_ia | D13 Legal | Explica implicancias legales pre-accion, alerta preventiva, escala abogado | `automatizacion/agentes/division_legal/consejero_legal_ia.py` | Planificado | 70 |
| generador_contratos | D13 Legal | Automatiza templates documentales, variables CRM, PDF, firma digital | `automatizacion/agentes/division_legal/generador_contratos.py` | Planificado | 70 |
| monitor_regulatorio | D13 Legal | Monitorea cambios normativos 24h, alerta afectacion operativa | `automatizacion/agentes/division_legal/monitor_regulatorio.py` | Planificado | 70 |
| validador_certificados | Legal Educativo | Genera diploma digital con hash verificable, pagina validacion publica | `automatizacion/agentes/division_legal/validador_certificados.py` | Planificado | 70 |
| ip_guardian | IP Guardian | Registro marca QuantumHive, documenta autoría Git, monitorea plagio | `automatizacion/agentes/division_legal/ip_guardian.py` | Futuro | 70 |
| firmas_electronicas | IP Guardian | Gestiona firma digital contratos, archivo firmados, alertas vencimiento | `automatizacion/agentes/division_legal/firmas_electronicas.py` | Futuro | 70 |
| legal_ucmi | UCMI Legal | Genera contratos automaticos influencers, PDFs, chatbot asistencia legal | `automatizacion/agentes/division_legal/legal_ucmi.py` | Futuro | 70 |

### Macro 6B — Finanzas, Contabilidad y Cobros

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| agente_cfo | CFO | Consolida informes financieros, reporte semanal Sergio, reporta CEO II | `automatizacion/agentes/division_finanzas/agente_cfo.py` | Futuro | 70 |
| agente_contabilidad | Contabilidad | Registra ingresos/egresos, genera balances, libros contables digitales | `automatizacion/agentes/division_finanzas/agente_contabilidad.py` | Futuro | 70 |
| cobros_internacional | Cobros | Infraestructura cobros USDT/crypto, Wise, Binance Pay, MercadoPago | `automatizacion/agentes/division_finanzas/cobros_internacional.py` | Futuro | 70 |
| bancos_y_cuentas | Bancos | Apertura cuentas internacionales, gestion distribucion fondos | `automatizacion/agentes/division_finanzas/bancos_y_cuentas.py` | Futuro | 70 |
| finanzas_personales_sergio | Finanzas Personales | Registra retiros CEO, presupuesto personal, inversiones personales | `automatizacion/agentes/division_finanzas/finanzas_personales_sergio.py` | Futuro | 70 |
| agente_facturacion | Facturación | Facturas automaticas por cliente, suscripciones recurrentes, alertas vencidos | `automatizacion/agentes/division_finanzas/agente_facturacion.py` | Futuro | 70 |

---

## Macro 7 — Colmena & Comunidad

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| gestor_rangos | D-NEW Jerarquias | Asigna y actualiza rangos (Abeja a Reina), calcula progreso | `automatizacion/agentes/colmena/gestor_rangos.py` | Planificado | 70 |
| rastreador_afiliados | D-NEW Afiliados | Tracking codigos unicos, comisiones recurrentes, payouts | `automatizacion/agentes/colmena/rastreador_afiliados.py` | Planificado | 70 |
| sorteador_beneficios | D-NEW Retencion | Sorteos automaticos mensuales/trimestrales/anuales por nivel | `automatizacion/agentes/colmena/sorteador_beneficios.py` | Planificado | 70 |
| retencion_proactiva | D-NEW Retencion | Detecta inactividad, envia notificaciones escalonadas 7/14/30 dias | `automatizacion/agentes/colmena/retencion_proactiva.py` | Planificado | 70 |
| gamificador_misiones | D-NEW Retencion | Genera misiones semanales, otorga puntos, muestra ranking | `automatizacion/agentes/colmena/gamificador_misiones.py` | Planificado | 70 |

---

## Macro 8 — Desarrollo de Apps

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| arquitecto_visual | D-NEW UVID | Define design_system.json, colores, tipografia, componentes base | `automatizacion/agentes/apps/arquitecto_visual.py` | Planificado | 70 |
| dashboard_optimizer | D-NEW UVID | Backup versiones dashboard, A/B testing layouts, metricas uso | `automatizacion/agentes/apps/dashboard_optimizer.py` | Planificado | 70 |
| app_designer | D-NEW UVID | Wireframes, maximo 3 toques por funcion, flujos <3 taps | `automatizacion/agentes/apps/app_designer.py` | Planificado | 70 |
| sala_virtual_designer | D-NEW UVID | Prototipo interactivo casino cuantico, inmersivo, futurista | `automatizacion/agentes/apps/sala_virtual_designer.py` | Planificado | 70 |
| qa_visual | D-NEW UVID | Checklist contraste, legibilidad movil, consistencia, pass/fail | `automatizacion/agentes/apps/qa_visual.py` | Planificado | 70 |
| ux_researcher | D-NEW UVID | Detecta fricciones por analytics, heatmaps, reporte semanal | `automatizacion/agentes/apps/ux_researcher.py` | Planificado | 70 |
| desarrollador_app_ceo | App CEO (Fase 1) | Backend FastAPI, frontend React Native, auth biometrico, push alerts | `automatizacion/agentes/apps/desarrollador_app_ceo.py` | Planificado | 70 |
| desarrollador_app_colmena | App Colmena (Fase 2) | Backend tenant separado, pagos Stripe/MP, Firebase FCM | `automatizacion/agentes/apps/desarrollador_app_colmena.py` | Planificado | 70 |

---

## Macro 9 — Academia QuantumHive

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| generador_cursos_genericos | D8+Fábrica | Crea cursos genericos para Academia (video+PDF+quiz+certificado) | `automatizacion/agentes/academia/generador_cursos_genericos.py` | Planificado | 70 |
| evaluador_examenes | D-NEW Academia | Genera examenes, califica automaticamente, emite diplomas | `automatizacion/agentes/academia/evaluador_examenes.py` | Planificado | 70 |
| pipeline_talento | D-NEW Academia | Detecta alumnos destacados (>90%), evalua proyectos, entrevista Sergio | `automatizacion/agentes/academia/pipeline_talento.py` | Planificado | 70 |
| mentor_virtual | D-NEW Academia | Responde dudas alumnos, guia por track, sugiere recursos | `automatizacion/agentes/academia/mentor_virtual.py` | Planificado | 70 |

---

## Macro 10 — Universidad de Agentes

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| ceo_universidad | CEO Universidad | Supervisa sistema educativo, coordina flujo aprendizaje, reporta CEO II | `automatizacion/agentes/universidad/ceo_universidad.py` | Futuro | 70 |
| recolector_conocimiento | Aprendizaje | Descarga videos YouTube, transcribe Whisper, monitorea canales | `automatizacion/agentes/universidad/recolector_conocimiento.py` | Futuro | 70 |
| conversor_universal | Aprendizaje | Convierte cualquier formato a PDF estructurado estandarizado | `automatizacion/agentes/universidad/conversor_universal.py` | Futuro | 70 |
| profesor_general | Enseñanza | Recibe PDF, extrae conceptos, genera curriculum, transmite a bots | `automatizacion/agentes/universidad/profesor_general.py` | Futuro | 70 |
| profesor_cnn | Enseñanza CNN | Especialista imagenes setups, entrena modelo CNN, clasifica automatico | `automatizacion/agentes/universidad/profesor_cnn.py` | Futuro | 70 |
| mantenimiento_educativo | Mantenimiento | Monitorea rendimiento, detecta quien necesita mejorar, envia Universidad | `automatizacion/agentes/universidad/mantenimiento_educativo.py` | Futuro | 70 |
| qa_universidad | QA | Test validacion conocimiento antes egreso, aprueba regreso productivo | `automatizacion/agentes/universidad/qa_universidad.py` | Futuro | 70 |

---

## Macro 11 — Comunicaciones QuantumHive

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| ceo_comunicaciones | CEO Comunicaciones | Supervisa canales, garantiza respuesta SLA, reporta CEO II | `automatizacion/agentes/comunicaciones/ceo_comunicaciones.py` | Futuro | 70 |
| telegram_manager | Telegram | Administra grupos/canales, modera, responde, escala especialistas | `automatizacion/agentes/comunicaciones/telegram_manager.py` | Futuro | 70 |
| whatsapp_business | WhatsApp | Atencion personalizada clientes premium, integrado jerarquias Colmena | `automatizacion/agentes/comunicaciones/whatsapp_business.py` | Futuro | 70 |
| chatbot_landing_pages | Chatbots | Chatbot por landing, entrenado producto, deriva canal correcto | `automatizacion/agentes/comunicaciones/chatbot_landing_pages.py` | Futuro | 70 |
| chatbot_legal | Chatbots | Resuelve dudas legales, escala MACRO 6A, genera PDFs respuestas | `automatizacion/agentes/comunicaciones/chatbot_legal.py` | Futuro | 70 |
| chatbot_academia | Chatbots | Resuelve dudas cursos, integrado certificacion, guia progreso | `automatizacion/agentes/comunicaciones/chatbot_academia.py` | Futuro | 70 |
| chatbot_colmena | Chatbots | Resuelve dudas challenges, muestra estado cuenta, integrado metricas | `automatizacion/agentes/comunicaciones/chatbot_colmena.py` | Futuro | 70 |
| monitor_comunicaciones | Monitor | Detecta insatisfechos, alertas SLA, reporta CEO Comunicaciones | `automatizacion/agentes/comunicaciones/monitor_comunicaciones.py` | Futuro | 70 |

---

## Unidad: Inteligencia Infinita

| Nombre | Division | Funcion | Archivo | Estado | Score |
|--------|----------|---------|---------|--------|-------|
| consejero_estrategico | II — CEO Unidad | Coordina todo el flujo, prioriza, resuelve conflictos | `automatizacion/agentes/ii/consejero_estrategico.py` | Planificado | 70 |
| analizador_viabilidad | II — Procesamiento | Evalua tecnicamente si idea es ejecutable, score 0-100 | `automatizacion/agentes/ii/analizador_viabilidad.py` | Planificado | 70 |
| optimizador_ideas | II — Procesamiento | Refina propuestas, reduce complejidad, mejora ROI estimado | `automatizacion/agentes/ii/optimizador_ideas.py` | Planificado | 70 |
| predictor_impacto | II — Procesamiento | Simula escenarios: tiempo, costo API, riesgo, retorno | `automatizacion/agentes/ii/predictor_impacto.py` | Planificado | 70 |
| memorizador_vision | II — Memoria | Guarda decisiones estrategicas, aprende preferencias Sergio | `automatizacion/agentes/ii/memorizador_vision.py` | Planificado | 70 |
| despachador | II — Operativo | Asigna tareas a CEOs Macro, genera tickets, monitorea SLA | `automatizacion/agentes/ii/despachador.py` | Planificado | 70 |

---

## Resumen por Estado

| Estado | Cantidad |
|--------|----------|
| Activo | 46 |
| Planificado | 58 |
| Futuro | 28 |
| **Total agentes registrados** | **132** |

---

*Última actualización: 28 de abril de 2026 — sesión estratégica CEO*
*Agregados agentes de MACRO 6B Finanzas, MACRO 6A IP Guardian, MACRO 3 UCMI, MACRO 4 Pipeline Fábrica, MACRO 10 Universidad, MACRO 11 Comunicaciones*

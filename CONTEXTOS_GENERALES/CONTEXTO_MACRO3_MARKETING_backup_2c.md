# CONTEXTO MACRO 3 — MARKETING Y VENTAS

## D3 — Grupo de Señales

**Embudo:** Señales gratis 3 días → Suscripción semanal/mensual → Colmena (cliente activo del ecosistema).

**Agentes existentes:**
- `agente_formateador_senales.py` — formatea señales para Telegram
- `agente_gestor_grupos.py` — gestiona accesos trial/pago/expiración
- `agente_cobro_senales.py` — cobro suscripciones MP/Stripe
- `agente_retencion.py` — clientes sin renovar, descuento recuperación
- `agente_captacion_senales.py` — publica resultados en redes, gestiona DMs

---

## D4 — Marketing y Captación

**Contenido automático con resultados reales del enjambre.**

**Agentes existentes:**
- `agente_partnerships_traders.py` — pipeline con traders reconocidos
- `agente_captacion_seguidores.py` — post-acuerdo con rate limit 50/día
- `agente_naming_bots.py` — generador de nombres técnicos propios para bots
- `agente_analytics_web.py` — Google Analytics/Plausible, funnel
- `agente_seo.py` — keywords competidores, contenido, posicionamiento
- `agente_ab_testing.py` — variantes landing pages, conversión
- `agente_diseno_contenido.py` — assets visuales web automáticos

**Activos existentes de marketing:**
- Instagram con historial de challenges superados de empresa anterior — prueba social verificable
- Videos grabados de sesiones reales de distintas cuentas para extraer operaciones ganadoras y armar contenido inicial
- Tarea pendiente Sergio: catalogar videos y preparar 5 clips editados para arranque

---

## D5 — Infoproductos y Afiliados

**Infoproductos digitales:** cursos de bots mecánicos, híbridos, frameworks de automatización.

**Software:** EAs, datasets, modelos ONNX.

**Agentes existentes:**
- `agente_creador_infoproductos.py` — estructuras modulares, guiones, pipeline producción
- `agente_analista_tendencias_infoproductos.py` — nichos hot, pricing, estrategias lanzamiento
- `agente_entrenador_ventas_infoproductos.py` — copywriting, email marketing, funnels, afiliados

---

## D6 — High Ticket Enterprise

**Venta del framework a hedge funds y prop firms (licencia SaaS).**

**Estado:** Fase 1 — definición de propuesta de valor y pricing enterprise.

**Objetivo:** Licenciar el stack completo (bots + infra + dashboard) a gestores institucionales.

---

## D11 — Atención al Cliente y Ventas

**Pipeline:** Lead → Bot Bienvenida → Especialista → Closer → Onboarding → Retención.

**Agentes existentes:**
- `agente_bienvenida.py` — primer contacto, califica lead, deriva
- `agente_especialista_senales.py` — experto grupo señales
- `agente_especialista_fondeo.py` — experto gestión challenges
- `agente_especialista_bots.py` — experto venta EAs/bots
- `agente_closer.py` — cierra ventas, links pago, seguimiento
- `agente_onboarding_ventas.py` — acceso post-pago, instrucciones
- `agente_retencion_ventas.py` — clientes inactivos, campaña retención

---

## D19 — Localización y Expansión Multinacional

**Gestiona adaptación cultural, legal y lingüística para 10+ mercados.**

**Subdivisiones:**
- 19A Coordinador de Idiomas — glosario técnico unificado
- 19B Traductor Técnico — docs, notebooks, código comentado
- 19C Marketing Local — landing pages por región
- 19D Soporte Comunitario — FAQs, tickets, comunidades
- 19E Legal Compliance por Jurisdicción — disclaimers, términos, validación regulatoria

**Prioridad:** EN, ES, PT, DE, FR, ZH (Fase 1); JA, RU, IT, AR (Fase 2).

**Integración:** D4 Marketing, D11 Atención, D13 Legal.

---

## D-NEW Humanización de Agentes

**Objetivo:** Evitar detección de bots en redes sociales.

- Comportamiento humano simulado: variación de patrones de publicación, tiempos de respuesta, redacción natural
- Gestión de identidades digitales únicas por plataforma
- Crítico para proteger cuentas de marketing masivo
- No usar templates repetitivos. Cada post, DM o comentario debe tener variación semántica y temporal.

**Stack:** Perfiles de personalidad generados por LLM, scheduling con jitter aleatorio, detección de engagement humano vs bot.

---

## D-NEW UMI — Unidad de Monetización Inteligente

### Subdivisión A — Low Ticket Masivo

- **Agente Explorador LT** — detecta oportunidades de ingreso rápido, bajo costo, alto volumen
- **Agente Optimizador por División LT** — adapta productos existentes a formatos low ticket
- **Agente Afiliados Externos** — gestiona red de afiliados fuera del ecosistema Colmena
- **Agente Lanzamientos Rápidos** — micro-productos en <72h desde idea
- **Agente Pricing Dinámico** — ajusta precios según demanda, competencia, momento del mes

### Subdivisión B — High Ticket Enterprise

- **Agente Explorador HT** — identifica empresas objetivo, contactos C-level, oportunidades B2B
- **Agente Propuestas Enterprise** — genera propuestas personalizadas, ROI calculado, casos de éxito
- **Agente Nicho Hunter** — descubre nichos desatendidos con alto poder adquisitivo
- **Agente Partnerships Estratégicos** — alianzas con propfirms, brokers, plataformas educativas
- **Agente Mentorship Pipeline** — gestiona lista de espera para mentorship con Sergio, filtra calidad

### Dirección UMI

- **Agente Director UMI** — consolata estrategia de precios global, evita canibalización entre productos
- **Agente Métricas de Monetización** — ARPU, LTV, CAC por canal, cohort analysis, churn predictivo

---

## Estrategia de Pricing Referencial

| Nivel | Precio | Productos |
|-------|--------|-----------|
| **Gancho gratis** | $0 | Cursos introductorios, señales 3 días, webinars |
| **Low ticket** | $9-$47 | Cursos básicos, EAs simples, ebooks, templates |
| **Mid ticket** | $97-$297 | Suscripción anual señales, cursos avanzados, packs EAs |
| **High ticket** | $500+ | Gestión de challenge, licencias enterprise, Mentorship Sergio |

**Regla:** Todo producto low ticket debe ser auto-sustentable (no requiere soporte humano). Mid y high ticket pueden incluir atención personalizada.

---

*Sistema auto-administrado. QuantumHive v3.0*

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

## D-NEW UCMI — Unidad de Captación Masiva e Influencers

### CEO UCMI

**Rol:** Supervisa todos los flujos de captación, mide costo por cliente adquirido por canal, optimiza ganchos e influencers por ROI.

**Funciones:**
- Supervisa todos los flujos de captación masiva
- Mide costo por cliente adquirido por canal (CPA)
- Optimiza ganchos e influencers por ROI
- Reporta a CEO MACRO 3
- Coordina interacción con D3 Señales (producto ofrecido)
- A/B testing de estrategias de captación

---

### Agente Gancho Masivo

**Rol:** Crea grupos Telegram con oferta lanzamiento y lógica de urgencia.

**Lógica de urgencia:**
- Unirse en 48hs = 1-2 semanas gratis
- Después del período free: oferta suscripción con descuento por haber entrado en lanzamiento
- Se activa automáticamente una vez por mes (evita saturación)

**Funciones:**
- Crea grupos Telegram temporales con oferta lanzamiento
- Gestiona lógica de urgencia y temporizadores
- Analiza métricas: quién se queda vs se va
- Optimiza el siguiente lanzamiento con esos datos
- Segmenta usuarios por comportamiento post-lanzamiento

**Integración:** Conectado con Agente Humanización para comportamiento natural en grupos.

---

### Agente Explorador de Puntos Calientes

**Rol:** Escanea Twitter/X, Reddit, Telegram, YouTube detectando comunidades de traders sin estructura.

**Funciones:**
- Escanea Twitter/X, Reddit, Telegram, YouTube
- Detecta comunidades de traders sin estructura — "enjambres sin colmena"
- Identifica momentos de mercado caliente para maximizar captación
- Analiza sentimiento de comunidades hacia trading algorítmico
- Reporta oportunidades al CEO UCMI

**KPIs:**
- Comunidades detectadas por semana
- Sentimiento promedio de cada comunidad
- Potencial de conversión estimado

---

### Agente Influencer Hunter

**Rol:** Encuentra influencers del nicho con criterios de calificación específicos.

**Criterios de calificación:**
- Engagement real verificable (no bots)
- Audiencia de traders activos
- Mínimo 5k seguidores
- Contenido alineado con QuantumHive
- Historial de colaboración con productos similares

**Funciones:**
- Encuentra influencers del nicho trading/crypto
- Genera lista priorizada con perfil completo
- Analiza métricas: engagement rate, audiencia, tipo de contenido
- Clasifica por potencial de colaboración
- Reporta al CEO UCMI con ranking de oportunidades

---

### Agente Closer de Influencers

**Rol:** Contacta influencers identificados, presenta propuesta de afiliación QuantumHive y negocia términos.

**Funciones:**
- Contacta influencers identificados por Influencer Hunter
- Presenta propuesta de afiliación QuantumHive
- Negocia: comisión por cliente, contenido, exclusividad, duración
- Hace seguimiento hasta cerrar el acuerdo
- Coordina con Agente Legal de la Unidad para contratos

**Términos típicos a negociar:**
- Comisión por cliente (10-30% según volumen)
- Exclusividad vs no-exclusividad
- Tipo de contenido requerido (posts, videos, lives)
- Duración del acuerdo (3-12 meses)
- Pagos por adelantado vs recurrentes

---

### Agente Legal UCMI

**Rol:** Genera contratos automáticos con influencers y proporciona asistencia legal.

**Funciones:**
- Genera contratos automáticos con influencers
- PDFs con firma digital (integrado con MACRO 6A Firmas Electrónicas)
- Términos claros: comisión, exclusividad, duración, condiciones de pago
- Chatbot de asistencia legal para influencers
- Coordina con MACRO 6A para casos complejos

**Contratos estándar:**
- Acuerdo de Afiliación Influencer
- Acuerdo de Exclusividad
- Acuerdo de Contenido Pagado
- NDA para información confidencial

---

### Interconexión con Agentes Existentes

**Agentes existentes que se interconectan con UCMI sin duplicarse:**

- **Agente Humanización (MACRO 3):** Cubre comportamiento natural en Telegram para grupos de captación
- **Agente Afiliados Externos (UMI):** Se coordina con Closer para términos de comisión
- **D3 Señales:** Es el producto que se ofrece en los grupos de captación masiva

**Principio:** No duplicar funcionalidad. UCMI se enfoca en captación masiva e influencers, mientras que agentes existentes cubren aspectos específicos de humanización y gestión de afiliados.

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

# CONTEXTO MACRO 6 — LEGAL, FINANZAS & ADVISORY

## MACRO 6A — LEGAL & ADVISORY

### Consejero Legal IA

**Rol:** Explica implicancias legales y regulatorias **antes** de cada acción importante de Sergio. No reemplaza abogado humano, pero reduce riesgo de errores por desconocimiento.

**Funciones:**
- Análisis pre-acción: "Sergio quiere lanzar Sala Colmena en Argentina → implicancias CNV, alcance, requisitos, riesgo penal"
- Alerta preventiva: detecta cuando una decisión de otra Macro tiene implicancia legal no considerada
- Escalación automática: si riesgo legal >70/100, bloquea acción y requiere abogado humano

**Integración:** Conectado a todos los CEOs de Macro. Ningún lanzamiento masivo sin approval legal.

---

### Generador de Contratos y Términos

**Automatización documental:**

| Documento | Trigger | Revisión humana |
|-----------|---------|-----------------|
| Términos de servicio (web) | Cambio en producto / nueva jurisdicción | Requerido si modifica derechos usuario |
| Contrato cliente fondeo | Nuevo cliente D2 | Requerido primera vez, luego template |
| Contrato partner (D17) | Nuevo partner Macro 5 | SIEMPRE requerido |
| NDA empleado/colaborador | Nuevo desarrollador / trader | Template aprobado, relleno auto |
| Acuerdo afiliado | Nuevo afiliado Macro 3 / 7 | Template, validación automática |

**Stack:** Templates en LaTeX/Markdown, variables extraídas de CRM, generación PDF, firma digital (DocuSign API futuro).

---

### IP Guardian — Subdivisión de Protección Intelectual

**Rol:** Protege la propiedad intelectual de QuantumHive, registra marca y documenta autoría del sistema.

**Funciones:**
- Registro de marca QuantumHive en Argentina y jurisdicciones clave (EEUU, UE, Dubai)
- Documenta autoría del sistema con Git timestamps (commits con firma digital)
- Prepara documentación para patente de software cuando corresponda
- Registra dominios: quantumhive.io, quantumhive.com, quantumhive.ai, quantumhive.trade
- Genera NDAs para colaboradores, desarrolladores, partners
- Monitorea plagio del sistema en repositorios públicos y plataformas de venta
- Prepara documentación para venta futura del software con titularidad limpia

**Acción Inmediata para Sergio:**
- Crear repositorio GitHub PRIVADO hoy
- Nunca usar repositorio público
- Migrar a GitLab self-hosted con VPS Oracle

---

### Agente Firmas Electrónicas

**Rol:** Gestiona firma digital de contratos de manera automatizada.

**Funciones:**
- Integrado con DocuSign o equivalente gratuito (HelloSign, PandaDoc)
- Archivo de todos los contratos firmados con metadata
- Alertas de contratos por vencer (30 días antes)
- Generación automática de recordatorios de firma
- Validación de identidad del firmante
- Auditoría de firmas: quién firmó, cuándo, desde qué IP

**Integración:** Conectado con Generador de Contratos y todos los sistemas que requieren acuerdos legales.

---

### Monitor Regulatorio por Jurisdicción

**Jurisdicciones activas (Fase 1):**

| País | Regulador | Estado | Riesgo principal |
|------|-----------|--------|-----------------|
| **Argentina** | CNV | Monitoreo activo | Señales de trading sin licencia, gestión capital ajeno |
| **Uruguay** | BCU | Evaluación | Constitución empresa, estabilidad legal |
| **EEUU** | CFTC / SEC / estatal (Wyoming/Delaware) | Planeamiento | PropFirms reguladas como brokers? tokens? |
| **Dubai** | VARA / DFSA | Opción futura | Crypto, licencias especiales, cero impuestos |

**Agente `agente_regulaciones.py` monitorea:**
- Cambios normativos cada 24h (scraping + RSS feeds reguladores)
- Alertas cuando una norma nueva afecta operación actual
- Comparativa reguladoria: dónde es más barato/legal operar cada servicio

**Opciones de constitución empresarial:**
- **Wyoming LLC (EEUU):** rápido, barato, crypto-friendly, buena reputación internacional
- **Delaware C-Corp:** si buscamos inversores institucionales (venture capital)
- **Uruguay SAS:** estabilidad macroeconómica, treaty con EEUU/UE, cerca de Sergio
- **Dubai Free Zone:** cero impuestos, licencias específicas fintech/crypto

**Recomendación actual:** Constituir en Wyoming LLC (rápido, online) + operar desde Uruguay (equipo, banca). Revisar anualmente.

---

## Legal Educativo

**Responsabilidades específicas para Academia (Macro 9):**

1. **Validación de certificados:**
   - Diploma digital con hash verificable
   - Página pública de verificación por número de certificado
   - Validez internacional sin homologación (es un certificado de empresa privada)

2. **Propiedad intelectual de cursos:**
   - Contenido propio: copyright registrado
   - Contenido de traders externos: acuerdo de licencia o fair use documentado
   - Código de EAs: licencia propietaria, no open source sin decisión explícita

3. **Diplomas por jurisdicción:**
   - Disclaimer obligatorio: "Este certificado no habilita para operar mercados regulados"
   - Variante por país si regulación local exige frases específicas
   - Revisión legal antes de primera emisión masiva

4. **Contratos con colaboradores:**
   - Autores de cursos: royalty vs fee fijo vs revenue share
   - Traders que prestan contenido para UCI: acuerdo de uso, no-exclusividad
   - Mentores: contrato de servicios, confidencialidad, no-compete suave

---

## Compliance Fase 1 Activo

**Áreas de compliance operativas desde el día 1:**

### PropFirms
- Cumplir TOS de cada firma (FTMO, FundingPips, Apex, MyFundedFX)
- Monitoreo automático de cambios TOS (agente `agente_propfirm_compliance.py`)
- No copiar operaciones idénticas entre cuentas (delay + variación)
- Reporte mensual de compliance a cada firma (si lo requieren)

### GDPR / Privacidad
- Consentimiento explícito de usuarios (web, app, comunidad)
- Derecho a olvido: eliminación datos en <30 días si solicitado
- Datos financieros: encriptación en reposo y tránsito
- No compartir datos con terceros sin consentimiento

### Señales por País
- Argentina (CNV): señales = opinión, no asesoramiento. Disclaimer obligatorio.
- España (CNMV): mismo tratamiento + MiFID II si escala a UE
- México (CNBV): evaluación pendiente, no activar sin review
- Colombia: evaluación pendiente

### Sala de Inversión (D16)
- **CRÍTICO:** En Argentina, gestionar capital ajeno sin autorización CNV es ilícito penal (art. 307 CP)
- Opciones legales antes de lanzamiento:
  a) Solicitar registro como Agente de Bolsa / FCI (lento, caro)
  b) Operar como consultoría tecnológica, no gestora (cliente opera su propia cuenta, bot es "software")
  c) Constituir en jurisdicción amigable (Dubai, Wyoming) con licencia correspondiente
  d) Beta cerrada <10 personas con contrato de prueba tecnológica (no inversión)

**Decisión pendiente:** Sergio + abogado. Bloquear lanzamiento masivo hasta resolución.

---

## Alerta Crítica: D16 Colmena y D2 Gestión Capital Ajeno

**ANTES de lanzamiento masivo de cualquiera de estas divisiones:**

1. Opinión legal escrita por abogado especializado en mercados de capitales
2. Estructura societaria definida y constituida
3. Licencias/registros aplicables obtenidos (si corresponden)
4. Contratos de cliente revisados y aprobados por legal externo
5. Seguro de errores y omisiones (E&O) contratado
6. Plan de contingencia regulatoria: qué hacemos si nos investigan

**Timeline estimado:** 3-6 meses desde decisión hasta lanzamiento legalmente blindado.

**Mientras tanto:**
- D2: operar como servicio tecnológico (el cliente opera su cuenta, nosotros proveemos software)
- D16: beta cerrada con 5-10 personas, contrato de prueba beta, sin promesas de rendimiento

---

## MACRO 6B — FINANZAS, CONTABILIDAD Y COBROS

### Agente CFO

**Rol:** CEO de la unidad financiera, consolida informes financieros y reporta al CEO Inteligencia Infinita.

**Funciones:**
- Consolida informes financieros de todas las macrodivisiones
- Reporte financiero semanal a Sergio
- Reporta al CEO Inteligencia Infinita consolidado
- Análisis de cash flow y proyecciones
- Gestión de presupuesto por macrodivisión
- KPIs financieros: LTV, CAC, MRR, Churn, EBITDA

---

### Agente Contabilidad

**Rol:** Registra ingresos y egresos, genera balances mensuales y documentación fiscal.

**Funciones:**
- Registro diario de ingresos y egresos
- Genera balances mensuales y trimestrales
- Libros contables digitales
- Documentación para impuestos
- Conciliación bancaria automática
- Reportes de gastos por categoría y proyecto
- Integración con sistemas de cobros para registro automático de ingresos

**Herramientas:** Software contable (QuickBooks, Xero o equivalente), integración API con sistemas de pago.

---

### Agente Cobros Internacional

**Rol:** Infraestructura de cobros multicanal para clientes internacionales y locales.

**Infraestructura de cobros:**
- **USDT/Crypto para internacional:** Billetera USDT (USDT-TRC20), integración con gateways (Binance Pay, CoinPayments)
- **Wise Business:** Para transferencias internacionales con mejor tipo de cambio
- **Binance Pay:** Opción cripto adicional para clientes que prefieren pago directo
- **MercadoPago:** Para mercado local (Argentina, Latinoamérica)

**Funciones:**
- Registra cada cobro con origen, monto y destino
- Conciliación automática entre canales de pago
- Alertas de cobros fallidos o pendientes
- Generación de facturas automáticas por cobro
- Reembolsos y devoluciones gestionados
- Reportes de ingresos por canal y región

**Integración:** Conectado con MACRO 6B Contabilidad para registro automático y MACRO 7 Colmena para distribución de fondos.

---

### Agente Bancos y Cuentas

**Rol:** Investiga y gestiona apertura de cuentas internacionales para operaciones empresariales.

**Prioridades de apertura:**
- **Mercury Bank USA:** Cuenta empresarial para EEUU, fintech-friendly
- **Wise Business:** Para transferencias internacionales multi-moneda
- **Payoneer Business:** Para recibir pagos de plataformas globales
- **Cuentas locales:** Banco en Uruguay para operaciones del equipo

**Funciones:**
- Investigación de requisitos para cada banco
- Preparación de documentación necesaria
- Seguimiento del proceso de apertura
- Gestión de distribución de fondos entre cuentas
- Optimización de fees de transferencia
- Monitoreo de saldos y alertas de bajo saldo

**Integración:** Conectado con MACRO 6B Contabilidad y Agente Cobros Internacional.

---

### Agente Finanzas Personales Sergio

**Rol:** Separado completamente de la empresa, registra retiros del CEO y gestiona presupuesto personal.

**Principio fundamental:** Finanzas personales de Sergio 100% separadas de QuantumHive.

**Funciones:**
- Registra retiros del CEO de la empresa (sueldo, dividendos, otros)
- Presupuesto personal mensual
- Inversiones personales (separadas de capital empresa)
- Registro de gastos personales
- Reporte mensual de finanzas personales a Sergio
- Planificación fiscal personal

**Separación legal:**
- Cuentas bancarias personales separadas
- Inversiones personales en nombre de Sergio, no QuantumHive
- Documentación clara de qué es gasto personal vs empresarial

---

### Agente Facturación

**Rol:** Facturas automáticas por cliente, gestiona suscripciones recurrentes y alertas de cobros vencidos.

**Funciones:**
- Facturas automáticas por cliente (según jerarquía y servicio)
- Gestiona suscripciones recurrentes (mensuales, trimestrales, anuales)
- Alertas de cobros vencidos (7, 15, 30 días)
- Generación de PDF de facturas
- Integrado con jerarquías Colmena (facturación según nivel)
- Reportes de facturación mensuales por tipo de servicio
- Conciliación con sistemas de cobros

**Integración:** Conectado con MACRO 6B Contabilidad, MACRO 7 Colmena y MACRO 11 Comunicaciones.

---

*Última actualización: 28 de abril de 2026 — sesión estratégica CEO*

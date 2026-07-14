# CONTEXTO MACRO 6 — LEGAL & ADVISORY

## Consejero Legal IA

**Rol:** Explica implicancias legales y regulatorias **antes** de cada acción importante de Sergio. No reemplaza abogado humano, pero reduce riesgo de errores por desconocimiento.

**Funciones:**
- Análisis pre-acción: "Sergio quiere lanzar Sala Colmena en Argentina → implicancias CNV, alcance, requisitos, riesgo penal"
- Alerta preventiva: detecta cuando una decisión de otra Macro tiene implicancia legal no considerada
- Escalación automática: si riesgo legal >70/100, bloquea acción y requiere abogado humano

**Integración:** Conectado a todos los CEOs de Macro. Ningún lanzamiento masivo sin approval legal.

---

## Generador de Contratos y Términos

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

## Monitor Regulatorio por Jurisdicción

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

*Sistema auto-administrado. QuantumHive v3.0*

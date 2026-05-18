# CONTEXTO MACRO 8 — DESARROLLO DE APPS

## Principio Fundamental

**DOS apps en total.** Desarrollo **secuencial**, **NUNCA simultáneo**.

**Secuencia inquebrantable:**
1. App CEO (Fase 1) — PRIMERA y ÚNICA prioridad de desarrollo mobile
2. App Colmena (Fase 2) — SOLO después de que App CEO esté en producción estable

---

## App CEO (Fase 1 — PRIMERA)

**Audiencia:** Solo Sergio.

**Propósito:** Dashboard móvil de control total del sistema QuantumHive.

### Funcionalidades

| Sección | Contenido | Prioridad |
|---------|-----------|-----------|
| **Estado de agentes** | Lista de todos los agentes activos, inactivos, en cuarentena. Score SPPR, modelo asignado, última tarea. | Alta |
| **Métricas de bots** | PnL en vivo, WR del día, operaciones abiertas, equity curve. Por bot, por cuenta, por firma. | Alta |
| **Alertas críticas** | DD>3%, bot caído, rate limit, SLA vencido, error legal. Push inmediato. | Alta |
| **Botones de mando** | Pause bot, force close, emergency BE, kill-switch Sala Colmena, modo ahorro extremo, modo máxima inteligencia. | Alta |
| **Telemetría** | Tokens gastados hoy, costo estimado, ahorro APIs, eficiencia de datos. | Media |
| **Pipeline** | Estado de proyectos: entrenamiento RL, integración ONNX, desarrollo App Colmena, partnerships. | Media |
| **Inbox** | Mensajes de CEOs de Macro, alertas de Legal, aprobaciones pendientes. | Media |
| **Modo voz (futuro)** | "Sergio, el bot US30 abrió long con score 0.91" — lectura automática de eventos. | Fase 2 |

### Tecnología sugerida

- **Backend:** FastAPI + PostgreSQL (datos) + Redis (cache en vivo)
- **Frontend:** React Native (una sola app iOS + Android)
- **Realtime:** WebSocket para métricas bots, push notifications para alertas
- **Auth:** Biométrico + PIN (solo Sergio, no hay registro público)
- **Seguridad:** Cert pinning, no screenshot en pantallas sensibles, wipe remoto

### MVP Fase 1 (6 semanas)

Semana 1-2: Backend + API endpoints estado agentes + métricas bots
Semana 3-4: Frontend móvil con navegación jerárquica (ver sección Dashboard)
Semana 5: Botones de mando funcionales (conectados a APIs de control)
Semana 6: Alertas push + testing + deploy a TestFlight/Internal Testing

---

## App Colmena (Fase 2 — DESPUÉS de App CEO)

**Audiencia:** Todos los clientes de QuantumHive.

**Propósito:** App única para todo el ecosistema. Una sola puerta de entrada.

### Secciones Internas

| Sección | Funcionalidad | Integración |
|---------|---------------|-------------|
| **PropFirm y Challenges** | Estado de tu challenge, cuenta fondeada, progreso, próximo payout | D2, D2B |
| **Métricas bots y cuentas** | PnL en vivo de TUS cuentas, WR, equity curve, operaciones abiertas | D1, D16 |
| **Inversión y PnL** | Capital depositado, rendimiento histórico, retiros, comprobantes | D16 |
| **Señales y suscripciones** | Señales en vivo, estado de suscripción, renovación, upgrade | D3 |
| **Academia y cursos** | Cursos comprados, progreso, exámenes, diploma, certificación | Macro 9 |
| **Afiliados y jerarquías** | Tu código, referidos, comisiones ganadas, ranking, próximo rango | Macro 7 |
| **Comunidad y engagement** | Chat por rango, eventos, sorteos activos, misiones gamificación | Macro 7 |
| **Notificaciones y alertas** | Push inteligente: bot abrió operación, subiste de rango, hay sorteo, curso nuevo | Todas |
| **Sorteos y beneficios** | Sorteos activos, beneficios por rango, historia de ganancias | Macro 7 |

### Tecnología sugerida

- **Backend:** FastAPI + PostgreSQL + Redis (mismo stack que App CEO, tenant separado por seguridad)
- **Frontend:** React Native (comparte componentes con App CEO donde aplica)
- **Auth:** Email + OTP / Google / Apple Sign In
- **Pagos:** Stripe / MercadoPago (según país)
- **Notificaciones:** Firebase Cloud Messaging

---

## D-NEW UVID — Unidad de Visual Intelligence

**Responsabilidad:** Todo lo que un humano ve en las apps o dashboards. Diseño, UX, QA visual, optimización.

### Agentes

| Agente | Rol | Output |
|--------|-----|--------|
| **Arquitecto Visual** | Define design_system.json: colores, tipografía, espaciado, componentes base, dark/light mode | `design_system.json` versionado |
| **Dashboard Optimizer** | Backup automático de cada versión de dashboard + A/B testing de layouts + métricas de uso | Versiones de dashboard + heatmaps de clics |
| **App Designer** | Máximo 3 toques por función. Cada flujo debe completarse en <3 taps desde home. | Wireframes validados |
| **Sala Virtual** | Diseña interfaz "casino cuántico": inmersivo, futurista, animaciones sutiles de datos fluyendo | Prototipo interactivo |
| **QA Visual** | Aprueba cada cambio visual antes de deploy. Checklist: contraste, legibilidad móvil, consistencia | Checklist pass/fail |
| **UX Researcher** | Detecta fricciones por analytics (dónde abandonan, dónde tardan, heatmaps) | Reporte semanal fricciones |

### Regla de Oro

**Ningún cambio visual sin pasar por QA Visual.**

Flujo:
```
Desarrollador cambia UI
    ↓
QA Visual ejecuta checklist automático + manual
    ↓
Pass → merge
    ↓
Fail → devuelve con especificación exacta del problema
```

---

## Dashboard Navegación Jerárquica Interactiva

**Estructura de navegación para App CEO (aplicable a App Colmena con permisos diferenciados):**

### Nivel 0 — Vista Macro (9 burbujas)

Pantalla inicial: 9 burbujas/tarjetas, una por Macro.

Cada burbuja muestra:
- Nombre de la Macro
- Estado en color: 🟢 operativa / 🟡 alerta / 🔴 crítica / ⚫ inactiva
- 1 métrica clave (ej: Macro 1 = PnL hoy, Macro 3 = leads hoy, Macro 7 = miembros activos)
- Toque → expande a Nivel 1

### Nivel 1 — Tarjetas de Divisiones

Lista de tarjetas horizontales o vertical, una por división dentro de la Macro.

Cada tarjeta:
- Nombre división + código (D1, D2, etc.)
- Agente CEO de la división
- Número de agentes activos / total
- Score promedio SPPR de la división
- Toque largo → panel completo (Nivel 3)
- Toque corto → descripción (Nivel 2)

### Nivel 2 — Descripción División + Agentes

Pantalla con:
- Misión de la división (2 líneas)
- Lista de agentes con: nombre, score, estado, última tarea
- Botones: ver logs, pausar agente, reasignar modelo, forzar tarea

### Nivel 3 — Panel Completo Agente

Pantalla dedicada a un agente:
- Score SPPR (0-100) con historial de 30 días
- Modelo asignado actual + recomendación de upgrade/downgrade
- Logs recientes (últimos 20)
- Botones de control: pausar, reanudar, reiniciar, cambiar modelo, enviar a cuarentena, forzar tarea específica
- Input: nota de Sergio para el agente (guardada en contexto)

---

## Roadmap de Desarrollo

| Fase | App | Semanas | Milestone |
|------|-----|---------|-----------|
| 1 | CEO | 6 | Sergio controla todo desde el celular |
| 2 | Colmena MVP | 8 | Clientes ven PnL, cursos, rangos |
| 3 | Colmena full | 12 | Pagos integrados, comunidad chat, sorteos en app |
| 4 | CEO v2 | 4 | Modo voz, alertas proactivas, predicciones IA |
| 5 | Sala Virtual | 6 | Entorno 3D/VR para eventos Reina |

**Regla:** No se inicia Fase N+1 hasta que Fase N tiene >95% uptime y Sergio aprueba.

---

*Sistema auto-administrado. QuantumHive v3.0*

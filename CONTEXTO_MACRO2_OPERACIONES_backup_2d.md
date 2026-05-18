# CONTEXTO MACRO 2 — OPERACIONES INTERNAS

## D9 — Limpieza y Mantenimiento (absorbe DOSD)

**Responsabilidad:** Mantener el sistema operativo limpio, eficiente y sin degradación acumulativa.

**Agentes incorporados:**

### The Cleaner
- Comprime logs antiguos (>7 días) a .tar.gz
- Elimina duplicados de datos y modelos
- Hot/cold storage: datos recientes en disco rápido, históricos >90 días en almacenamiento frío
- Métrica de eficiencia de tokens: tokens procesados por dólar de API, reporte semanal

### The Optimizer
- Monitorea latencia de cada agente (tiempo respuesta, tokens/segundo)
- Detecta agentes lentos o costosos
- Mueve agentes lentos a modelos más rápidos/cheaper automáticamente
- Reporte de optimización mensual con recomendaciones

**Frecuencia:** Limpieza profunda todos los domingos. Optimización continua (cada 6 horas).

---

## D12 — Crecimiento y Optimización (absorbe DGCR)

**Responsabilidad:** Evolución continua de todo el ecosistema. Meta-división que gestiona el aprendizaje organizacional.

### Sistema de Reputación de Agentes (SPPR)

**Score 0-100 por agente. Todos arrancan en 70 (Operativo).**

| Nivel | Score | Modelo asignado | Autonomía |
|-------|-------|-----------------|-----------|
| Élite | 90-100 | Claude Opus | Total — puede actuar sin validación |
| Operativo | 60-89 | Claude Sonnet | Validación requerida para tareas críticas |
| Bronce | 40-59 | Claude Haiku | Solo lectura, no ejecuta cambios |
| Cuarentena | <40 | — | Bloqueado. System Prompt reescrito automáticamente. Requiere review humano. |

**Lógica de puntuación:**
- +5 por tarea exitosa completada sin errores
- -15 por error crítico o alucinación
- Upgrade/downgrade automático de modelo según score
- Auditor asignado por cada 5 departamentos

**Retroalimentación en bucle cerrado:**
```
Agente A genera output
    ↓
Auditor califica (0-100)
    ↓
Devuelve error + contexto a Agente A
    ↓
Agente A corrige y regenera
    ↓
Auditor re-califica
    ↓
Score actualizado en registro persistente
```

**Agentes existentes:**
- `agente_ceo_estrategico.py` — evalúa métricas globales diarias
- `agente_scout.py` — busca repos/papers/herramientas nuevas
- `agente_clasificador.py` — evalúa hallazgos del scout
- `agente_entrenador_bots.py` — monitorea métricas, decide reentrenar
- `agente_entrenador_divisiones.py` — monitorea KPIs divisiones
- `agente_supervisor_global.py` — cruza datos áreas, detecta cuellos de botella
- `agente_premios.py` — registra mejoras >5% en 7 días

---

## D13 — Legal y Compliance

**Responsabilidad:** Términos, contratos, regulaciones, PropFirm compliance, privacidad GDPR.

**Sub-agentes especializados:**
- **Marketing:** marca ajena, promesas de rendimiento, TOS plataformas
- **Señales:** CNV/CNMV/CNBV por país (Argentina, España, México, Colombia)
- **Sala inversión:** beta ≤20, capital gestionado, disclaimer inversión
- **PropFirms:** cambios TOS mensuales, monitoreo automático
- **UCI:** copyright/fair use de contenido recolectado

**Coordinador central:** genera reporte diario consolidado y escala ALTO a Sergio vía Telegram.

**Agentes existentes:**
- `agente_terminos.py` — términos de servicio versionados
- `agente_contratos.py` — contratos PDF clientes fondeo
- `agente_regulaciones.py` — monitorea regulaciones por país
- `agente_propfirm_compliance.py` — reglas PropFirms, alerta cambios
- `agente_privacidad.py` — GDPR, eliminación datos

---

## D14 — Infraestructura y DevOps (absorbe CPC)

**Responsabilidad:** Monitoreo, backup, actualizaciones, performance, alertas críticas.

### Capa de Persistencia de Contexto (nueva)

**Cada agente guarda `agente_status.json` antes de cerrar sesión o cambiar de API.**

Campos obligatorios:
- `Agent_ID` — identificador único
- `Current_Task` — tarea en progreso
- `Last_Summary` — resumen de lo último hecho
- `Critical_Data` — datos críticos que no pueden perderse
- `Memory_Pointer` — referencia a memoria externa si aplica

**Protocolo trasplante de cerebro:**
```
Agente inicia con nueva API
    ↓
Lee su agente_status.json
    ↓
Se autoinyecta el contexto
    ↓
Continúa desde donde quedó
```

**shared_knowledge/:** carpeta común donde todos los agentes depositan hallazgos terminados. Estructura:
- `hallazgos/` — descubrimientos validados
- `errores/` — errores documentados con solución
- `procedimientos/` — SOPs versionados

**Base vectorial:**
- Fase 1: ChromaDB local (sin costo, embeddings locales)
- Escalafutura: Pinecone (cloud, alta performance)

**Bus de comunicación central:** canal común entre macros para mensajes estructurados (JSON). No es chat libre: es API con schema definido.

**Agentes existentes:**
- `agente_monitoreo_sistema.py` — verifica procesos cada 5 min, reinicia
- `agente_backup.py` — backup diario ONNX/SQLite/config
- `agente_actualizaciones.py` — versiones nuevas dependencias
- `agente_performance.py` — CPU/RAM/disco, alerta >80%
- `agente_alertas_criticas.py` — alertas por niveles VERDE→NEGRO

---

## D15 — Business Intelligence (absorbe Dashboard CEO)

**Responsabilidad:** Dashboard ejecutivo, métricas trading/negocio, alertas negocio, reportes inversores.

### Secretary Agent
- Reporte ejecutivo al CEO cada vez que entra al sistema
- Estado de todas las macros en una pantalla
- Alertas que requieren atención inmediata
- Próximos deadlines y milestones

### Botón Rojo
Tres modos de emergencia accesibles desde cualquier dashboard:
1. **Modo ahorro extremo** — apaga todos los agentes no críticos, reduce modelos a Haiku, pausa entrenamientos
2. **Modo máxima inteligencia** — sube todo a Opus, paraleliza tareas, prioriza calidad sobre costo
3. **Reinicio de división** — resetea estado de una macro completa, reasigna agentes, limpia errores acumulados

### Telemetría completa
- Tokens gastados por agente, por día, por macro
- Ahorro APIs: comparativo costo esperado vs real
- Salud del sistema: uptime, latencia, errores/hora
- Eficiencia de datos: bytes procesados por unidad de resultado

**Agentes existentes:**
- `agente_dashboard_ejecutivo.py` — reporte diario KPIs todas divisiones
- `agente_metricas_trading.py` — winrate, PF, DD, Sharpe diario
- `agente_metricas_negocio.py` — MRR, churn, LTV, CAC, proyecciones
- `agente_alertas_negocio.py` — alerta si KPI cae bajo umbral
- `agente_reportes_inversores.py` — PDF mensual profesional

---

## D-NEW DLRI — Logística de Recursos e Inteligencia

**Objetivo:** Costo operativo cercano a cero. API paga solo como último recurso.

### The Broker
- Administra `keys_vault.py` — registro centralizado de todas las API keys
- Asigna API por nivel de reputación del agente (Élite=Opus, Operativo=Sonnet)
- Rotación automática ante rate limit 429
- Anthropic solo para tareas críticas (score ≥ 80)

### The Hunter
- Busca constantemente nuevas APIs gratuitas, créditos de bienvenida, modelos OpenRouter costo $0
- Reporta semanalmente hallazgos con evaluación de calidad
- Mantiene lista priorizada: gratuito > crédito > barato > pago
- Monitorea comunidades de devs para nuevas ofertas

---

## D-NEW UGCC — Unidad de Gestión de Conocimiento y Contexto

**Responsabilidad:** Mantener el sistema de contexto saludable, interrelacionado y versionado.

- Divide automáticamente archivos de contexto cuando superan tamaño óptimo (>500 líneas o >50KB)
- Mantiene índice maestro actualizado (`CONTEXTO_MAESTRO.md`)
- Interrelaciona archivos mediante referencias cruzadas explícitas
- Detecta información desactualizada y propone updates
- Versiona cambios con historial (git implícito, pero también metadatos en archivos)
- Valida consistencia: si un parámetro cambia en `CONTEXTO_TECNICO.md`, propaga a otros archivos

---

## D-NEW USEC — Unidad de Seguridad

**Responsabilidad:** Proteger credenciales, prevenir colapsos, validar outputs, mantener backups.

| Agente | Función |
|--------|---------|
| **Vault** | Credenciales, rotación automática de keys, cifrado en reposo |
| **Firewall** | Control de accesos, detección de anomalías de uso, alerta patrones sospechosos |
| **Anti-Colapso** | Monitorea CPU/RAM/disco/tokens en tiempo real. Frena procesos antes de saturar |
| **Backup** | Snapshot automático antes de cada cambio mayor. Rollback en <60 segundos |
| **Guardrails** | Valida outputs entre divisiones. Si un agente genera código contradictorio, frena y escala |

**Regla crítica:** Ningún cambio en producción sin pasar por Guardrails + Backup.

---

*Sistema auto-administrado. QuantumHive v3.0*

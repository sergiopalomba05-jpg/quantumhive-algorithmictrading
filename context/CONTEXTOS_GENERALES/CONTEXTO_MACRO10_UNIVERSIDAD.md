# CONTEXTO MACRO 10 — UNIVERSIDAD DE AGENTES

## Concepto Central

Los agentes y bots no son estáticos. Aprenden continuamente desde fuentes externas procesadas por un sistema educativo con profesor IA como intermediario. El mantenimiento detecta quién necesita mejorar y lo envía a la Universidad.

---

## Flujo Completo de Aprendizaje

```
Sergio/Recolector encuentra material
    ↓
Agente Conversor → PDF estructurado
    ↓
Agente Profesor recibe conocimiento
    ↓
Agente Profesor transmite al bot/agente que necesita aprender
    ↓
Agente QA valida que aprendió correctamente
    ↓
Bot mejorado regresa al sistema productivo
```

**Ciclo continuo:** Los bots y agentes nunca están "terminados". Están en constante evolución a través de la Universidad.

---

## Agente Recolector de Conocimiento

**Rol:** Descarga y procesa material educativo de fuentes externas.

**Funciones:**
- Descarga videos YouTube con yt-dlp
- Transcribe con Whisper (IA de reconocimiento de voz)
- Traduce si está en otro idioma
- Convierte PDFs externos al formato interno
- Monitorea canales marcados por Sergio:
  - Hobbie Code (activo)
  - Otros canales que Sergio marque
- Escaneo semanal automático buscando contenido nuevo relevante
- Guarda todo en `universidad/biblioteca/`

**Fuentes monitoreadas:**
- YouTube (canales de trading, ML, Python)
- ArXiv (papers de ML, RL)
- GitHub (repos de trading algorítmico)
- Blogs técnicos (Medium, Towards Data Science)
- Documentación oficial de librerías

**Integración:** Conectado con Agente Conversor Universal.

---

## Agente Conversor Universal

**Rol:** Convierte cualquier formato de conocimiento a PDF estructurado estandarizado.

**Conversiones soportadas:**
- Video → transcripción → PDF estructurado
- Imagen → descripción → PDF
- Web → artículo → PDF
- Código → documentación → PDF
- Audio → transcripción → PDF

**Output estandarizado (siempre incluye):**
- Resumen ejecutivo
- Conceptos técnicos extraídos
- Aplicación específica al sistema QuantumHive
- Parámetros sugeridos para bots correspondientes
- Referencias y fuentes

**Funciones:**
- Convierte cualquier formato a PDF estandarizado
- Aplica formato consistente a todo el conocimiento
- Extrae conceptos clave aplicables al sistema
- Genera parámetros sugeridos para cada bot relevante
- Todo guardado en `universidad/biblioteca/`

**Integración:** Conectado con Recolector y Agente Profesor General.

---

## Agente Profesor General

**Rol:** Recibe PDF procesado por Conversor y transmite conocimiento a bots y agentes.

**Funciones:**
- Recibe PDF procesado por Conversor
- Extrae conceptos clave aplicables al sistema
- Genera curriculum específico para cada bot
- Transmite conocimiento en formato consumible
- Registra qué aprendió cada bot en `universidad/registros/agente_id_curriculum.json`

**Formato de transmisión:**
- Para bots de trading: parámetros nuevos, reglas mecánicas, features
- Para agentes de marketing: ganchos, copywriting, estrategias
- Para agentes legales: actualizaciones regulatorias, precedentes
- Para agentes financieros: KPIs, métricas, reportes

**Registro educativo:**
```json
{
  "agente_id": "agente_trading_us30",
  "fecha_ultima_lectura": "2026-04-28",
  "conceptos_aprendidos": [
    {"concepto": "RSI filtrado", "aplicacion": "Filtrar señales RSI <30 y >70"},
    {"concepto": "Walk-forward", "aplicacion": "Validar estrategia en datos out-of-sample"}
  ],
  "score_aprendizaje": 85,
  "certificado_educativo": true
}
```

---

## Agente Profesor CNN

**Rol:** Especialista en imágenes de sesiones y aperturas de trading.

**Fase inicial (supervisada por Sergio):**
- Sergio recolecta fotos de setups manualmente
- Agente clasifica y estructura las imágenes
- Categorías:
  - Setup válido (para tomar)
  - Setup inválido (para evitar)
  - Reversión (cambio de tendencia)
  - Continuación (seguimiento de tendencia)
  - Scalp (operaciones rápidas)
- Etiquetado manual por Sergio para ground truth

**Fase automatizada posterior:**
- Entrena modelo CNN con los patrones visuales
- Clasificación automática de nuevas imágenes
- Retroalimentación constante del modelo
- Aprendizaje continuo de nuevos patrones

**Funciones:**
- Clasifica imágenes de setups de trading
- Entrena modelo CNN con patrones visuales
- Genera dataset de imágenes etiquetadas
- Aplica clasificación a nuevas imágenes automáticamente
- Retroalimenta al sistema de trading con insights visuales

**Integración:** Conectado con MACRO 4 Fábrica y MACRO 1 Trading.

---

## Agente Mantenimiento Educativo

**Rol:** Monitorea rendimiento de todos los bots y agentes, detecta quién necesita mejorar y lo envía a la Universidad.

**Triggers para enviar a Universidad:**
- Score de reputación cae por debajo de 60 (sistema DGCR MACRO 2)
- WR del bot baja más de 10% en 2 semanas
- Recolector trae info nueva aplicable al bot
- CEO Inteligencia Infinita lo solicita
- Errores recurrentes en operaciones
- Feedback negativo de clientes

**Funciones:**
- Monitorea rendimiento de todos los bots y agentes
- Coordina con D12 sistema de reputación (MACRO 2)
- Registra historial educativo de cada agente
- Determina qué agente necesita qué conocimiento
- Envía agentes a Universidad cuando corresponde
- Aprueba regreso al sistema productivo

**Registro de envíos:**
```json
{
  "envio_id": "envio_001",
  "agente_id": "agente_trading_us30",
  "motivo": "WR bajó 15% en 2 semanas",
  "fecha_envio": "2026-04-28",
  "conocimiento_asignado": "nuevas_reglas_filtrado.pdf",
  "fecha_egreso": "2026-05-05",
  "estado": "en_progreso"
}
```

---

## Agente QA Universidad

**Rol:** Antes de que un bot egrese de la Universidad, aplica test de validación del conocimiento.

**Funciones:**
- Aplica test de validación del conocimiento
- Verifica que el aprendizaje fue incorporado
- Aprueba regreso al sistema productivo
- Si no aprueba: ciclo adicional con Profesor
- Genera certificado de aprendizaje

**Test de validación:**
- Para bots de trading: backtest con nuevos parámetros, WR mejorado
- Para agentes de marketing: A/B test con nuevo copy, conversión mejorada
- Para agentes legales: simulación de casos, cumplimiento normativo
- Para agentes financieros: reporte con nuevos KPIs, precisión mejorada

**Criterios de aprobación:**
- Incorporación efectiva del conocimiento (verificado por test)
- No degradación de rendimiento existente
- Mejora medible en métricas relevantes
- Sin efectos secundarios negativos

---

## Biblioteca Compartida

**Estructura de directorios:**
```
universidad/
├── biblioteca/           # Todos los PDFs procesados
│   ├── trading/          # Conocimiento específico de trading
│   ├── ml/               # Machine learning, RL, CNN
│   ├── marketing/        # Marketing, captación, copywriting
│   ├── legal/            # Legal, compliance, regulación
│   ├── finanzas/         # Finanzas, contabilidad, cobros
│   └── general/          # Conocimiento general aplicable
├── registros/            # Historial por agente
│   ├── agente_trading_us30_curriculum.json
│   ├── agente_marketing_curriculum.json
│   └── ...
└── curricula/            # Planes de estudio por tipo de agente
    ├── curriculum_trading.md
    ├── curriculum_marketing.md
    ├── curriculum_legal.md
    └── ...
```

**Características:**
- Accesible por todos los agentes del sistema
- Indexada por tema, activo y tipo de estrategia
- Versionado: cada PDF tiene timestamp y versión
- Búsqueda semántica: encontrar conocimiento relevante rápidamente
- Métricas: qué PDFs son más consultados, qué agentes aprenden más rápido

---

## CEO Universidad de Agentes

**Rol:** Supervisa todo el sistema educativo de la Universidad.

**Funciones:**
- Supervisa flujo completo de aprendizaje
- Coordina interacción entre Recolector, Conversor, Profesores y QA
- Determina prioridades de aprendizaje
- Reporta al CEO Inteligencia Infinita
- Optimiza proceso educativo continuamente

**KPIs:**
- Tiempo promedio de aprendizaje por agente
- Tasa de aprobación en QA
- Mejora de rendimiento post-Universidad
- Cantidad de agentes en Universidad en un momento dado
- Utilización de biblioteca (PDFs consultados por mes)

---

## Integración con Otras Macros

**MACRO 1 Trading:**
- Bots de trading envían a Universidad cuando WR baja
- Profesor CNN entrena con imágenes de setups
- Conocimiento de trading aplicado directamente

**MACRO 2 Operaciones:**
- Sistema de reputación DGCR coordina con Mantenimiento Educativo
- Score <60 trigger para envío a Universidad

**MACRO 3 Marketing:**
- Agentes de marketing aprenden nuevas estrategias de captación
- UCMI se beneficia de conocimiento de influencers

**MACRO 4 Fábrica:**
- Pipeline de bots se beneficia de conocimiento nuevo
- Agente de Experimentación coordina con Universidad

**MACRO 6 Legal:**
- Actualizaciones regulatorias transmitidas a agentes legales
- Compliance aprende de nuevos precedentes

---

## Fase de Implementación

**Fase 1 (Actual):**
- Implementar Recolector de Conocimiento
- Implementar Conversor Universal
- Implementar Profesor General
- Crear estructura de biblioteca

**Fase 2:**
- Implementar Profesor CNN
- Implementar Mantenimiento Educativo
- Implementar QA Universidad
- Integrar con sistema de reputación

**Fase 3:**
- Sistema completamente automatizado
- Aprendizaje continuo de todos los agentes
- Métricas de mejora de rendimiento

---

*Última actualización: 28 de abril de 2026 — sesión estratégica CEO*

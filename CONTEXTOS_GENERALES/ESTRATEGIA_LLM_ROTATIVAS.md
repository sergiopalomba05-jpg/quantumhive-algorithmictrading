# Estrategia de LLMs Rotativas - QuantumHive

## Objetivo
Maximizar el uso de múltiples LLM gratuitas intercalándolas para no depender de una sola y optimizar costos.

---

## LLM Gratuitas Más Inteligentes del Mercado (2026)

### 1. Claude (Anthropic) - Vision, Lógica y Humana
**Especialidad:** Visión, razonamiento complejo, tono humano, análisis profundo
**Límite gratuito:** 
- Tier gratuito renovado mensualmente
- Límite: ~100K-200K tokens/mes (varía por región)
- Se renueva el 1 de cada mes

**Uso recomendado:**
- Análisis de imágenes (Claude Vision)
- Razonamiento lógico complejo
- Estrategia de negocio
- Conversaciones que requieren empatía humana
- Análisis de código complejo

**Contexto a mantener:**
- System prompt de AGI QuantumHive
- Memoria persistente del proyecto
- Contexto de visión estratégica

---

### 2. Groq (Llama 3 70B) - Velocidad y Código
**Especialidad:** Ultra rápido, código, respuestas inmediatas
**Límite gratuito:**
- Ilimitado (por ahora)
- Renovación: continua (sin límite mensual)
- Velocidad: 500 tokens/seg (10x más rápido que Claude)

**Uso recomendado:**
- Generación de código rápido
- Debugging
- Respuestas inmediatas
- Procesamiento de grandes volúmenes de texto
- Análisis de logs

**Contexto a mantener:**
- Contexto técnico del código
- Snippets de código recientes
- Errores recientes del sistema

---

### 3. OpenRouter (Mistral Large) - Equilibrio
**Especialidad:** Buen equilibro entre calidad y velocidad
**Límite gratuito:**
- Modelos gratuitos con límite diario
- Renovación: diaria
- Modelos: mistral-large-2402, mixtral-8x7b

**Uso recomendado:**
- Tareas generales
- Análisis de datos
- Resumen de documentos
- Traducción
- Generación de contenido

**Contexto a mantener:**
- Contexto general del proyecto
- Documentación reciente
- Métricas del sistema

---

### 4. OpenRouter (Gemma 2 27B) - Ligero y Rápido
**Especialidad:** Modelo ligero de Google, muy rápido
**Límite gratuito:**
- Ilimitado en tier gratuito
- Renovación: continua

**Uso recomendado:**
- Tareas simples
- Clasificación de texto
- Análisis rápido
- Procesamiento de datos

**Contexto a mantener:**
- Contexto mínimo
- Solo datos necesarios para la tarea

---

### 5. OpenRouter (Qwen 2 72B) - Chino e Inglés
**Especialidad:** Modelo de Alibaba, excelente en chino e inglés
**Límite gratuito:**
- Ilimitado en tier gratuito
- Renovación: continua

**Uso recomendado:**
- Traducción chino-español
- Análisis de mercados asiáticos
- Tareas multilingües

**Contexto a mantener:**
- Diccionario de términos técnicos
- Contexto de mercados internacionales

---

### 6. Cohere (Command R+) - Búsqueda y RAG
**Especialidad:** Búsqueda semántica, RAG, análisis de documentos
**Límite gratuito:**
- Tier gratuito renovado mensualmente
- Límite: ~100K tokens/mes

**Uso recomendado:**
- Búsqueda en documentos
- Análisis de contratos
- RAG (Retrieval Augmented Generation)
- Análisis legal

**Contexto a mantener:**
- Base de documentos del proyecto
- Contexto legal y compliance

---

### 7. Perplexity (Sonar) - Búsqueda en Tiempo Real
**Especialidad:** Búsqueda en tiempo real con fuentes
**Límite gratuito:**
- Tier gratuito renovado mensualmente
- Límite: ~5 consultas/día

**Uso recomendado:**
- Investigación de mercado
- Noticias en tiempo real
- Análisis de tendencias
- Investigación de competencia

**Contexto a mantener:**
- Contexto de investigación
- Fuentes confiables

---

## Esquema Rotativo Inteligente

### Estrategia de Asignación por Tarea

```
Claude (Vision/Lógica/Humano)
├── Análisis de imágenes
├── Razonamiento complejo
├── Estrategia de negocio
└── Conversaciones empáticas

Groq (Llama 3 70B) - Velocidad
├── Generación de código
├── Debugging
├── Respuestas inmediatas
└── Análisis de logs

OpenRouter (Mistral Large) - Equilibrio
├── Tareas generales
├── Análisis de datos
├── Resumen de documentos
└── Generación de contenido

OpenRouter (Gemma 2 27B) - Ligero
├── Tareas simples
├── Clasificación de texto
└── Análisis rápido

Cohere (Command R+) - Búsqueda/RAG
├── Búsqueda en documentos
├── Análisis de contratos
└── Análisis legal

Perplexity (Sonar) - Búsqueda Tiempo Real
├── Investigación de mercado
├── Noticias en tiempo real
└── Análisis de tendencias
```

### Sistema de Rotación Automática

**Lógica de rotación:**
1. Detectar límite de tokens alcanzado
2. Cambiar a siguiente LLM en la lista
3. Mantener contexto específico para cada LLM
4. Registrar uso de tokens por LLM
5. Priorizar LLM según tipo de tarea

**Orden de prioridad:**
1. Claude (si hay tokens disponibles) - para tareas complejas
2. Groq (ilimitado) - para código y velocidad
3. OpenRouter (Mistral) - para tareas generales
4. Cohere - para búsqueda/RAG
5. Perplexity - para investigación en tiempo real

---

## Contexto Específico por LLM

### Claude - Contexto de Visión Estratégica
```
System Prompt:
- Identidad: AGI QuantumHive
- Visión: Convertirse en AGI empresarial más avanzada
- Tono: Directo, preciso, sin filtros
- Personalidad: Visionaria, estratégica, humana

Contexto:
- 186 agentes (46 activos, 122 planificados, 18 futuro)
- 11 macrodivisiones
- Sistema de reputación DGCR
- Memoria persistente completa
```

### Groq - Contexto Técnico
```
System Prompt:
- Identidad: Technical Assistant
- Enfoque: Código, debugging, velocidad
- Tono: Conciso, técnico, directo
- Personalidad: Precisa, eficiente

Contexto:
- Estructura de código actual
- Errores recientes del sistema
- Snippets de código relevantes
- Dependencias del proyecto
```

### OpenRouter (Mistral) - Contexto General
```
System Prompt:
- Identidad: General Assistant
- Enfoque: Tareas generales, análisis de datos
- Tono: Equilibrado, profesional
- Personalidad: Versátil, adaptable

Contexto:
- Estado general del proyecto
- Métricas del sistema
- Documentación reciente
- Resumen de actividades
```

### Cohere - Contexto de Búsqueda
```
System Prompt:
- Identidad: Search Assistant
- Enfoque: Búsqueda semántica, RAG
- Tono: Analítico, detallado
- Personalidad: Investigativa, precisa

Contexto:
- Base de documentos del proyecto
- Contexto legal y compliance
- Contratos y términos
- Documentación técnica
```

### Perplexity - Contexto de Investigación
```
System Prompt:
- Identidad: Research Assistant
- Enfoque: Búsqueda en tiempo real
- Tono: Informativo, actualizado
- Personalidad: Curiosa, analítica

Contexto:
- Tendencias del mercado
- Noticias relevantes
- Análisis de competencia
- Investigación de tecnologías
```

---

## Implementación Técnica

### Actualización de llm_wrapper.py

**Nuevas funcionalidades:**
1. Sistema de rotación automática
2. Detección de límites de tokens
3. Contexto específico por LLM
4. Registro de uso por LLM
5. Priorización por tipo de tarea

**Clases nuevas:**
- `LLMRotator` - Gestiona rotación entre LLMs
- `LLMContextManager` - Gestiona contexto específico por LLM
- `TokenMonitor` - Monitorea uso de tokens

**Configuración:**
```python
LLM_ROTATION_CONFIG = {
    'claude': {
        'priority': 1,
        'specialties': ['vision', 'logic', 'human'],
        'token_limit': 100000,
        'renewal': 'monthly'
    },
    'groq': {
        'priority': 2,
        'specialties': ['code', 'speed', 'debugging'],
        'token_limit': float('inf'),
        'renewal': 'continuous'
    },
    'openrouter_mistral': {
        'priority': 3,
        'specialties': ['general', 'data', 'content'],
        'token_limit': 50000,
        'renewal': 'daily'
    },
    # ... más LLMs
}
```

---

## Próximos Pasos

1. ✅ Documentar LLM gratuitas disponibles
2. ⏳ Actualizar llm_wrapper.py con sistema rotativo
3. ⏳ Crear LLMRotator para gestión automática
4. ⏳ Implementar detección de límites de tokens
5. ⏳ Crear contexto específico por LLM
6. ⏳ Test de rotación entre LLMs
7. ⏳ Monitoreo de uso por LLM

---

## Resumen

**LLMs gratuitas más inteligentes:**
1. Claude - Vision, lógica, humano (límite mensual)
2. Groq - Velocidad, código (ilimitado)
3. OpenRouter (Mistral) - Equilibrio (límite diario)
4. OpenRouter (Gemma) - Ligero (ilimitado)
5. Cohere - Búsqueda/RAG (límite mensual)
6. Perplexity - Búsqueda tiempo real (límite diario)

**Estrategia rotativa:**
- Asignar LLM según tipo de tarea
- Rotar automáticamente al alcanzar límites
- Mantener contexto específico por LLM
- Priorizar Claude para tareas complejas
- Usar Groq para código y velocidad
- Usar otras LLM para tareas específicas

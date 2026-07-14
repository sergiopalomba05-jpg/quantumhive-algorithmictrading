# Configuración de IA Gratuita — QuantumHive AGI

## Problema
Claude (Anthropic) tiene costos altos. Gastaste $10 USD hoy y te quedaste sin tokens. No puedes afortar más de $10 USD diarios antes de monetizar.

## Solución
Wrapper LLM que permite alternativas GRATUITAS sin modificar la estructura AGI ni el system prompt.

## Opciones Gratuitas Disponibles

### 1. OpenRouter (Recomendado - Fácil de usar)
- **Modelos gratuitos:** Llama 3 8B, Mistral 7B, Gemma 7B
- **Costo:** $0 (modelos marcados como ":free")
- **Setup:**
  1. Crear cuenta en https://openrouter.ai/
  2. Obtener API key gratuita
  3. Agregar a .env:
     ```
     LLM_ENGINE=openrouter
     OPENROUTER_API_KEY=tu_api_key_aqui
     ```

### 2. Groq (Muy rápido - Recomendado)
- **Modelos gratuitos:** Llama 3 8B, Mixtral 8x7B, Gemma 7B
- **Costo:** $0
- **Velocidad:** Ultra rápido (500 tokens/seg)
- **Setup:**
  1. Crear cuenta en https://console.groq.com/
  2. Obtener API key gratuita
  3. Agregar a .env:
     ```
     LLM_ENGINE=groq
     GROQ_API_KEY=tu_api_key_aqui
     ```

### 3. Ollama (Local - Totalmente gratuito)
- **Modelos gratuitos:** Llama 3 8B, Mistral 7B, Gemma 7B
- **Costo:** $0 (corre localmente)
- **Ventaja:** Sin límites, sin API keys, 100% privado
- **Setup:**
  1. Descargar Ollama: https://ollama.ai/
  2. Instalar y ejecutar: `ollama run llama3:8b`
  3. Agregar a .env:
     ```
     LLM_ENGINE=ollama
     OLLAMA_BASE_URL=http://localhost:11434
     ```

## Configuración en .env

Agrega estas variables a tu archivo `.env`:

```bash
# Motor IA a usar (opciones: anthropic, openrouter, groq, ollama)
LLM_ENGINE=groq

# API Keys (solo la del motor que uses)
ANTHROPIC_API_KEY=sk-ant-xxx (opcional, si usas Claude)
OPENROUTER_API_KEY=sk-or-xxx (opcional, si usas OpenRouter)
GROQ_API_KEY=gsk_xxx (opcional, si usas Groq)
OLLAMA_BASE_URL=http://localhost:11434 (opcional, si usas Ollama)
```

## Instalación de Dependencias

```bash
cd automatizacion/agentes
pip install -r requirements.txt
```

## Verificación

El sistema automáticamente detectará:
- ✅ Qué motor estás usando
- ✅ Si es gratuito o de pago
- ✅ Fallback automático si falla

## Recomendación

**Para ahora (fase desarrollo):**
- Usa **Groq** (más rápido, totalmente gratuito)
- API key gratuita: https://console.groq.com/
- Modelos: llama3-8b-8192 (muy rápido y capaz)

**Para producción (cuando monetices):**
- Vuelve a Claude (mejor calidad)
- Solo cambia `LLM_ENGINE=anthropic` en .env

## Sin tocar la estructura AGI

El wrapper permite cambiar el motor IA sin modificar:
- ❌ System prompt
- ❌ Estructura de AGI
- ❌ Lógica de negocio
- ✅ Solo cambia el motor IA (como cambiar el motor de un auto)

## Archivos Modificados

1. `automatizacion/agi_core/llm_wrapper.py` - Wrapper universal
2. `automatizacion/agentes/agi_telegram.py` - Integración del wrapper
3. `automatizacion/agentes/requirements.txt` - Dependencias agregadas

## Próximos Pasos

1. Obtener API key gratuita de Groq o OpenRouter
2. Agregar a .env
3. Reiniciar el bot AGI
4. Verificar logs para confirmar motor gratuito activo

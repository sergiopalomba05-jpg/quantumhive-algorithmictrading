"""
Script para configurar GROQ_API_KEY en Render
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Agregar path al directorio de agentes
sys.path.insert(0, str(Path(__file__).parent / 'automatizacion' / 'agentes'))

from agente_render import AgenteRender

print("=== CONFIGURANDO GROQ_API_KEY EN RENDER ===\n")

# Cargar variables locales
load_dotenv()
groq_key = os.getenv('GROQ_API_KEY', '')

if not groq_key:
    print("ERROR: GROQ_API_KEY no encontrada en .env local")
    sys.exit(1)

print(f"GROQ_API_KEY local encontrada: {groq_key[:10]}...")

agente = AgenteRender()

# Configurar GROQ_API_KEY en Render
resultado = agente.agregar_variable_entorno('GROQ_API_KEY', groq_key)

if resultado:
    print("✅ GROQ_API_KEY configurada en Render")
else:
    print("❌ Error configurando GROQ_API_KEY en Render")

# Configurar LLM_ENGINE como groq
resultado_llm = agente.agregar_variable_entorno('LLM_ENGINE', 'groq')

if resultado_llm:
    print("✅ LLM_ENGINE configurada como groq en Render")
else:
    print("❌ Error configurando LLM_ENGINE en Render")

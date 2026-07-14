"""
Script para verificar GROQ_API_KEY en Render
"""
import sys
from pathlib import Path

# Agregar path al directorio de agentes
sys.path.insert(0, str(Path(__file__).parent / 'automatizacion' / 'agentes'))

from agente_render import AgenteRender

print("=== VERIFICANDO GROQ_API_KEY EN RENDER ===\n")

agente = AgenteRender()

# Obtener variables de entorno
env_vars = agente.obtener_variables_entorno()

print("Variables de entorno en Render:")
for var in env_vars:
    if 'GROQ' in var.get('key', '').upper() or 'LLM' in var.get('key', '').upper():
        key = var.get('key', 'N/A')
        value = var.get('value', 'N/A')
        if value and len(value) > 10:
            value = value[:10] + "..."
        print(f"  {key}: {value}")

print(f"\nTotal de variables: {len(env_vars)}")

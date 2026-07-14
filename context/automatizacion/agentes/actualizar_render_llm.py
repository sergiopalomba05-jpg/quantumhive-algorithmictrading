from agente_render import AgenteRender

agente = AgenteRender()

# Actualizar LLM_ENGINE a groq
resultado = agente.agregar_variable_entorno('LLM_ENGINE', 'groq')
print(f'LLM_ENGINE actualizado: {resultado}')

# Verificar variables actuales
vars_actuales = agente.obtener_variables_entorno()
print(f'\nVariables de entorno actuales ({len(vars_actuales)}):')
for var in vars_actuales:
    print(f"  - {var.get('key')}")

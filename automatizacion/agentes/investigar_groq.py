from agente_investigacion_modelos import AgenteInvestigacionModelos

agente = AgenteInvestigacionModelos()
modelos = agente.investigar_modelos_groq()

print('=== MODELOS GROQ DISPONIBLES ===')
print(f'Total: {len(modelos.get("groq", []))} modelos\n')

for m in modelos.get('groq', []):
    print(f"- {m['id']}")

# Obtener modelo funcional recomendado
modelo_funcional = agente.obtener_modelo_funcional_groq()
print(f'\n=== MODELO FUNCIONAL RECOMENDADO ===')
print(f'{modelo_funcional}')

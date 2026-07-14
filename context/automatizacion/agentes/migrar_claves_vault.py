"""
Migración de Claves a Vault — QuantumHive
Migra claves existentes desde variables de entorno al vault encriptado.
"""

import os
from agente_seguridad import agente_seguridad

# Claves a migrar según Brief Día 3
CLAVES_A_MIGRAR = {
    'TELEGRAM_TOKEN': 'COMUNICACIONES',
    'ANTHROPIC_API_KEY': 'INFRA',
    'OPENAI_API_KEY': 'INFRA',
    'GROQ_API_KEY': 'INFRA',
    'GITHUB_TOKEN': 'INTERNO',
    'RENDER_API_KEY': 'INFRA'
}

def migrar_claves():
    """Migra claves desde variables de entorno al vault."""
    print("=== MIGRACIÓN DE CLAVES AL VAULT ===\n")
    
    migradas = 0
    fallidas = 0
    
    for nombre_clave, categoria in CLAVES_A_MIGRAR.items():
        valor = os.getenv(nombre_clave, '')
        
        if valor and len(valor) > 10:
            # Clave encontrada, migrar al vault
            resultado = agente_seguridad.agregar_credencial(nombre_clave, valor, categoria)
            if resultado:
                print(f"✅ {nombre_clave} → {categoria}")
                migradas += 1
            else:
                print(f"❌ {nombre_clave} → Error al migrar")
                fallidas += 1
        else:
            print(f"⚠️ {nombre_clave} → No encontrada o inválida")
            fallidas += 1
    
    print(f"\n=== RESUMEN ===")
    print(f"Migradas: {migradas}")
    print(f"Fallidas: {fallidas}")
    
    # Reporte del vault
    print(f"\n{agente_seguridad.reporte_estado()}")

if __name__ == "__main__":
    migrar_claves()

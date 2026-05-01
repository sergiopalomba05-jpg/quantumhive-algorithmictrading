"""
Agente Experto en Errores
Investiga y soluciona errores complejos en el sistema
"""
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
import re

class AgenteExpertoErrores:
    def __init__(self):
        self.log_errores = []
        self.soluciones_encontradas = []
    
    def investigar_ai_town(self, ruta_ai_town="d:\\quantumhive-town"):
        """Investiga el error de AI Town y propone soluciones."""
        print("=" * 70)
        print("🔍 INVESTIGANDO ERROR DE AI TOWN")
        print("=" * 70)
        
        if not os.path.exists(ruta_ai_town):
            print(f"❌ Directorio AI Town no encontrado: {ruta_ai_town}")
            return None
        
        analisis = {
            "ruta": ruta_ai_town,
            "fecha": datetime.now().isoformat(),
            "errores_encontrados": [],
            "soluciones_propuestas": []
        }
        
        # 1. Verificar estructura del proyecto
        print("\n📍 PASO 1: Verificando estructura del proyecto...")
        try:
            archivos = os.listdir(ruta_ai_town)
            print(f"✅ Archivos encontrados: {len(archivos)}")
        except Exception as e:
            print(f"❌ Error leyendo estructura: {e}")
            analisis["errores_encontrados"].append(f"Error estructura: {e}")
        
        # 2. Verificar node_modules
        print("\n📍 PASO 2: Verificando node_modules...")
        node_modules_path = os.path.join(ruta_ai_town, "node_modules")
        if os.path.exists(node_modules_path):
            print("✅ node_modules existe")
        else:
            print("❌ node_modules NO existe - necesita npm install")
            analisis["errores_encontrados"].append("node_modules no existe")
            analisis["soluciones_propuestas"].append("Ejecutar: npm install --legacy-peer-deps")
        
        # 3. Generar reporte
        print("\n📍 PASO 3: Generando reporte...")
        reporte = {
            "analisis_completo": analisis,
            "recomendacion_principal": "Ejecutar npm install --legacy-peer-deps y luego npm run dev"
        }
        
        return reporte

def main():
    agente = AgenteExpertoErrores()
    agente.investigar_ai_town()

if __name__ == "__main__":
    main()

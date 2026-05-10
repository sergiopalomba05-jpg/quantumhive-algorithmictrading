"""
Configurador automático de datasource SQLite en Grafana
QuantumHive — Ejecutar después de instalar Grafana
"""

import requests
import json
from pathlib import Path
import os

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin"  # Cambiar después del primer login

# Ruta absoluta al SQLite (Grafana necesita ruta absoluta)
DB_PATH = str(Path(__file__).parent.parent.parent / 
              "automatizacion" / "data" / "agi_memoria_telegram.db")

def configurar_datasource():
    """Configura el datasource SQLite en Grafana via API."""
    
    datasource = {
        "name": "QuantumHive-SQLite",
        "type": "frser-sqlite-datasource",
        "access": "proxy",
        "jsonData": {
            "path": DB_PATH
        },
        "isDefault": True
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        json=datasource
    )
    
    if response.status_code in [200, 409]:
        print(f"✅ Datasource configurado: {DB_PATH}")
        return True
    else:
        print(f"❌ Error: {response.status_code} — {response.text}")
        return False

if __name__ == "__main__":
    configurar_datasource()

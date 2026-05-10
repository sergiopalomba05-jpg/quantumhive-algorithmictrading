"""
Setup maestro de Grafana para QuantumHive
Ejecutar una sola vez para dejar todo configurado
"""

import subprocess
import time
import requests
from pathlib import Path

def verificar_grafana_corriendo():
    """Verifica que Grafana esté respondiendo."""
    for i in range(12):  # Espera hasta 60 segundos
        try:
            r = requests.get("http://localhost:3000/api/health", timeout=5)
            if r.status_code == 200:
                print("✅ Grafana está corriendo")
                return True
        except:
            pass
        print(f"Esperando Grafana... ({(i+1)*5}s)")
        time.sleep(5)
    return False

def verificar_sqlite():
    """Verifica que el SQLite de QuantumHive existe."""
    db_path = Path(__file__).parent.parent.parent / \
              "automatizacion" / "data" / "agi_memoria_telegram.db"
    if db_path.exists():
        print(f"✅ SQLite encontrado: {db_path}")
        return str(db_path)
    else:
        print(f"❌ SQLite no encontrado en: {db_path}")
        return None

def main():
    print("=" * 50)
    print("🐝 QUANTUMHIVE — Setup Grafana Dashboard")
    print("=" * 50)
    
    # 1. Verificar SQLite
    db_path = verificar_sqlite()
    if not db_path:
        print("❌ Abortando: SQLite no encontrado")
        return
    
    # 2. Verificar Grafana
    if not verificar_grafana_corriendo():
        print("❌ Grafana no está corriendo.")
        print("Ejecutar instalar_grafana.ps1 como Administrador primero.")
        return
    
    # 3. Configurar datasource
    print("\n📦 Configurando datasource SQLite...")
    from configurar_datasource import configurar_datasource
    configurar_datasource()
    
    # 4. Crear dashboard
    print("\n📊 Creando dashboard principal...")
    from crear_dashboard import crear_dashboard
    crear_dashboard()
    
    print("\n" + "=" * 50)
    print("✅ Setup completo")
    print("🌐 Abrí: http://localhost:3000")
    print("👤 Usuario: admin | Password: admin")
    print("📊 Dashboard: QuantumHive — Colmena Dashboard")
    print("=" * 50)

if __name__ == "__main__":
    main()
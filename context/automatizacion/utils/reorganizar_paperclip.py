"""
Script para reorganización jerárquica de Paperclip
Construcción del Consejo y población de Macros 2 y 4
"""
import requests
import os
from pathlib import Path
from typing import List, Dict, Optional

PAPERCLIP_PORTS = [3100, 3101, 3102]
COMPANY_ID = "4e83ada7-4b92-4c3d-bcef-21ebdd2a389e"
AGENTES_PATH = Path(__file__).resolve().parents[2] / "automatizacion" / "agentes"

def detectar_puerto():
    for port in PAPERCLIP_PORTS:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/api/companies", timeout=2)
            if response.status_code == 200:
                return port
        except:
            continue
    return None

def registrar_agente(puerto, nombre, agente_id, rol, descripcion, reports_to_id=None):
    """Registra un agente en Paperclip"""
    url = f"http://127.0.0.1:{puerto}/api/companies/{COMPANY_ID}/agents"
    
    payload = {
        "name": nombre,
        "id": agente_id,
        "role": rol,
        "description": descripcion
    }
    
    if reports_to_id:
        payload["reportsTo"] = reports_to_id
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code in [200, 201]:
            agente_data = response.json()
            return agente_data.get("id")
        else:
            print(f"✗ {nombre} falló: {response.text}")
            return None
    except Exception as e:
        print(f"Error registrando {nombre}: {e}")
        return None

def obtener_agente_id_por_nombre(puerto, nombre):
    """Obtiene el ID de un agente existente por su nombre"""
    try:
        url = f"http://127.0.0.1:{puerto}/api/companies/{COMPANY_ID}/agents"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            agentes = response.json()
            for agente in agentes:
                if agente["name"] == nombre:
                    return agente["id"]
        return None
    except Exception as e:
        print(f"Error obteniendo ID del agente {nombre}: {e}")
        return None

def escanear_agentes_macro(carpeta_macro):
    """Escanea agentes en una carpeta específica"""
    agentes = []
    ruta_macro = AGENTES_PATH / carpeta_macro
    
    if not ruta_macro.exists():
        print(f"WARNING: Carpeta {carpeta_macro} no existe")
        return agentes
    
    for file in ruta_macro.glob("*.py"):
        if file.is_file() and not file.name.startswith("__"):
            nombre = file.stem.replace("_", " ").title()
            agente_id = file.stem
            agentes.append({
                "nombre": nombre,
                "id": agente_id,
                "ruta": str(file.relative_to(AGENTES_PATH))
            })
    
    return agentes

def main():
    print("="*60)
    print("REORGANIZACIÓN JERÁRQUICA - PAPERCLIP")
    print("="*60)
    
    puerto = detectar_puerto()
    if not puerto:
        print("ERROR: No se detectó Paperclip")
        return
    
    print(f"Paperclip detectado en puerto: {puerto}")
    
    # PASO 1: Construir el Consejo (Nivel 0, 1, 2)
    print("\n" + "="*60)
    print("PASO 1: CONSTRUYENDO EL CONSEJO")
    print("="*60)
    
    # Nivel 0: Sergio Palomba (Fundador)
    sergio_id = registrar_agente(
        puerto, 
        "Sergio Palomba", 
        "sergio_palomba", 
        "ceo", 
        "Fundador - Nivel 0"
    )
    
    if sergio_id:
        print(f"✓ Sergio Palomba registrado (ID: {sergio_id[:8]}...)")
    else:
        print("✗ Sergio Palomba falló")
        return
    
    # Nivel 1: AGI Telegram (CEO I) -> Reporta a Sergio
    agi_id = registrar_agente(
        puerto,
        "AGI Telegram",
        "agi_telegram_ceo_i",
        "cto",
        "CEO I - Nivel 1 - Reporta a Sergio",
        reports_to_id=sergio_id
    )
    
    if agi_id:
        print(f"✓ AGI Telegram registrado (ID: {agi_id[:8]}...)")
    else:
        # Intentar obtener ID si ya existe
        agi_id = obtener_agente_id_por_nombre(puerto, "AGI Telegram")
        if agi_id:
            print(f"✓ AGI Telegram ya existe (ID: {agi_id[:8]}...)")
        else:
            print("✗ AGI Telegram falló")
            return
    
    # Nivel 2: CONSEJO ESTRATÉGICO -> Reporta a AGI
    consejo_id = registrar_agente(
        puerto,
        "Consejo Estratégico",
        "consejo_estrategico",
        "cmo",
        "Nivel 2 - Reporta a AGI Telegram",
        reports_to_id=agi_id
    )
    
    if consejo_id:
        print(f"✓ Consejo Estratégico registrado (ID: {consejo_id[:8]}...)")
    else:
        print("✗ Consejo Estratégico falló")
        return
    
    # Nivel 2: 3 agentes virtuales -> Reportan al Consejo
    agentes_virtuales = [
        ("Gemini", "gemini_legal", "security", "Legal/Estructura - Reporta al Consejo"),
        ("Claude", "claude_estrategia", "researcher", "Estrategia - Reporta al Consejo"),
        ("ChatGPT", "chatgpt_visuales", "designer", "Visuales - Reporta al Consejo")
    ]
    
    for nombre, agente_id, rol, descripcion in agentes_virtuales:
        id_agente = registrar_agente(puerto, nombre, agente_id, rol, descripcion, reports_to_id=consejo_id)
        if id_agente:
            print(f"✓ {nombre} registrado (ID: {id_agente[:8]}...)")
        else:
            print(f"✗ {nombre} falló")
    
    # PASO 2: Poblar Macro 4
    print("\n" + "="*60)
    print("PASO 2: POBLANDO MACRO 4 (FÁBRICA DE BOTS)")
    print("="*60)
    
    agentes_macro4 = escanear_agentes_macro("macro4")
    print(f"Agentes encontrados en Macro 4: {len(agentes_macro4)}")
    
    for agente in agentes_macro4:
        # Reportan al Consejo Estratégico
        id_agente = registrar_agente(
            puerto,
            agente["nombre"],
            f"macro4_{agente['id']}",
            "engineer",
            f"Fábrica de Bots - {agente['ruta']}",
            reports_to_id=consejo_id
        )
        if id_agente:
            print(f"✓ {agente['nombre']} registrado (ID: {id_agente[:8]}...)")
        else:
            print(f"✗ {agente['nombre']} falló")
    
    # PASO 3: Poblar Macro 2
    print("\n" + "="*60)
    print("PASO 3: POBLANDO MACRO 2 (OPERACIONES)")
    print("="*60)
    
    agentes_macro2 = escanear_agentes_macro("macro2")
    print(f"Agentes encontrados en Macro 2: {len(agentes_macro2)}")
    
    for agente in agentes_macro2:
        # Reportan al Consejo Estratégico
        id_agente = registrar_agente(
            puerto,
            agente["nombre"],
            f"macro2_{agente['id']}",
            "devops",
            f"Operaciones - {agente['ruta']}",
            reports_to_id=consejo_id
        )
        if id_agente:
            print(f"✓ {agente['nombre']} registrado (ID: {id_agente[:8]}...)")
        else:
            print(f"✗ {agente['nombre']} falló")
    
    # Reporte final
    print("\n" + "="*60)
    print("REPORTE FINAL - ORGANIGRAMA")
    print("="*60)
    print(f"Sergio Palomba (Fundador - Nivel 0)")
    print(f"  └─ AGI Telegram (CEO I - Nivel 1)")
    print(f"     └─ Consejo Estratégico (Nivel 2)")
    print(f"        ├─ Gemini (Legal/Estructura)")
    print(f"        ├─ Claude (Estrategia)")
    print(f"        ├─ ChatGPT (Visuales)")
    print(f"        ├─ Macro 4: {len(agentes_macro4)} agentes")
    print(f"        └─ Macro 2: {len(agentes_macro2)} agentes")
    print(f"\nPanel de Paperclip: http://127.0.0.1:{puerto}")
    print("="*60)

if __name__ == "__main__":
    main()

"""
Sincronizador de Colmena - Auto-Discovery para Paperclip
Escanea agentes en automatizacion/agentes/ y los registra vía API en Paperclip
"""

import os
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional

# Configuración
PAPERCLIP_PORTS = [3101, 3100, 3102]  # Puertos comunes de Paperclip (3101 prioritario)
AGENTES_PATH = Path(__file__).parent.parent / "agentes"

# Mapeo de carpetas a roles válidos de Paperclip
MACRODIVISIONES = {
    "division_biblioteca_fabrica_bots": "engineer",
    "division_fondeo": "devops",
    "division_propfirms": "security",
    "division_marketing": "cmo",
    "division_academia": "researcher",
    "division_innovacion": "researcher",
    "division_infraestructura": "devops",
    "division_operaciones": "pm",
    "division_ia": "engineer",
    "division_comunicaciones": "cmo",
    "": "general"  # Agentes en la raíz
}

# Mapeo de carpetas desconocidas a roles válidos
OTRAS_DIVISIONES = {
    "division_recursos_humanos": "pm",
    "division_finanzas": "cfo",
    "division_legal": "security",
    "division_ventas": "cmo",
    "division_soporte": "qa",
    "division_desarrollo": "engineer",
}

# Definición de Teams (Macrodivisiones) según ADN de QuantumHive
TEAMS_DEFINITION = [
    {"id": "trading_core", "name": "Trading Core", "description": "Macro 1 - Operaciones de trading y prop firms"},
    {"id": "operaciones_internas", "name": "Operaciones Internas", "description": "Macro 2 - Gestión operativa interna"},
    {"id": "ventas_captacion", "name": "Ventas y Captación", "description": "Macro 3 - Marketing y adquisición de clientes"},
    {"id": "fabrica_bots", "name": "Fábrica de Bots", "description": "Macro 4 - Ingeniería de bots y estrategias"},
    {"id": "legal_finanzas", "name": "Legal y Finanzas", "description": "Macro 6 - Asuntos legales y financieros"},
    {"id": "infraestructura", "name": "Infraestructura", "description": "Macro 12 - DevOps, seguridad y sistemas"},
    {"id": "softwares_qh", "name": "Softwares QH", "description": "Macro 13 - Desarrollo de software interno"},
]

# Mapeo de carpetas a Teams (para metadata)
CARPETA_A_TEAM = {
    "division_biblioteca_fabrica_bots": "fabrica_bots",
    "division_fondeo": "trading_core",
    "division_propfirms": "trading_core",
    "division_marketing": "ventas_captacion",
    "division_academia": "ventas_captacion",
    "division_operaciones": "operaciones_internas",
    "division_finanzas": "legal_finanzas",
    "division_legal": "legal_finanzas",
    "division_infraestructura": "infraestructura",
    "division_ia": "softwares_qh",
    "division_desarrollo": "softwares_qh",
}

# Agentes específicos que van a Infraestructura
AGENTES_INFRAESTRUCTURA = {
    "agente_seguridad": "infraestructura",
    "agente_render": "infraestructura",
}

# IDs de agentes para jerarquía (se obtendrán dinámicamente)
AGI_AGENTE_ID = None  # Se obtendrá después de registrar AGI Telegram

def detectar_puerto_paperclip() -> Optional[int]:
    """Detecta qué puerto está usando Paperclip"""
    for port in PAPERCLIP_PORTS:
        try:
            # Intentar endpoint de dashboard como health check
            response = requests.get(f"http://127.0.0.1:{port}/api/companies", timeout=2)
            if response.status_code == 200:
                return port
        except:
            continue
    return None

def obtener_company_id(puerto: int) -> Optional[str]:
    """Obtiene el ID de la compañía de Paperclip"""
    try:
        response = requests.get(f"http://127.0.0.1:{puerto}/api/companies", timeout=5)
        if response.status_code == 200:
            companies = response.json()
            if companies and len(companies) > 0:
                return companies[0].get("id")
    except Exception as e:
        print(f"Error obteniendo company ID: {e}")
    return None

def obtener_agente_id_por_nombre(puerto: int, company_id: str, nombre_agente: str) -> Optional[str]:
    """Obtiene el ID de un agente existente por su nombre"""
    try:
        url = f"http://127.0.0.1:{puerto}/api/companies/{company_id}/agents"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            agentes = response.json()
            for agente in agentes:
                if agente["name"] == nombre_agente:
                    return agente["id"]
        return None
    except Exception as e:
        print(f"Error obteniendo ID del agente {nombre_agente}: {e}")
        return None

def actualizar_reports_to_agente(puerto: int, company_id: str, agente_id: str, reports_to_id: str) -> bool:
    """Actualiza el campo reportsTo de un agente"""
    try:
        url = f"http://127.0.0.1:{puerto}/api/companies/{company_id}/agents/{agente_id}"
        payload = {"reportsTo": reports_to_id}
        response = requests.patch(url, json=payload, timeout=5)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error actualizando reportsTo: {e}")
        return False

def determinar_team_agente(file_name: str, carpeta: str) -> str:
    """Determina a qué Team pertenece un agente según su carpeta y nombre"""
    # Primero verificar si es un agente específico de infraestructura
    if file_name in AGENTES_INFRAESTRUCTURA:
        return AGENTES_INFRAESTRUCTURA[file_name]
    
    # Luego verificar por carpeta
    if carpeta in CARPETA_A_TEAM:
        return CARPETA_A_TEAM[carpeta]
    
    # Por defecto, asignar a Operaciones Internas
    return "operaciones_internas"

def escanear_agentes() -> List[Dict]:
    """Escanea todos los archivos agente_*.py"""
    agentes = []
    
    for root, dirs, files in os.walk(AGENTES_PATH):
        for file in files:
            if file.startswith("agente_") and file.endswith(".py"):
                ruta_completa = Path(root) / file
                ruta_relativa = ruta_completa.relative_to(AGENTES_PATH)
                
                # Determinar carpeta
                partes = ruta_relativa.parts
                carpeta = partes[0] if len(partes) > 1 else ""
                
                # Determinar rol según la carpeta
                rol = MACRODIVISIONES.get(carpeta, OTRAS_DIVISIONES.get(carpeta, "general"))
                
                # Determinar team según carpeta y nombre de archivo
                team_id = determinar_team_agente(file.replace(".py", ""), carpeta)
                
                # Nombre del agente (sin prefijo y extensión)
                nombre = file.replace("agente_", "").replace(".py", "").replace("_", " ").title()
                
                agentes.append({
                    "nombre": nombre,
                    "id": file.replace(".py", ""),
                    "ruta": str(ruta_relativa),
                    "macrodivision": rol,
                    "team_id": team_id
                })
    
    return agentes

def registrar_agente_en_paperclip(agente: Dict, puerto: int, company_id: str) -> Optional[str]:
    """Registra un agente en Paperclip vía API y retorna su ID"""
    url = f"http://127.0.0.1:{puerto}/api/companies/{company_id}/agents"
    
    payload = {
        "name": agente["nombre"],
        "id": agente["id"],
        "role": agente["macrodivision"],
        "description": f"Agente ubicado en {agente['ruta']} - Team: {agente['team_id']}"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code in [200, 201]:
            agente_data = response.json()
            return agente_data.get("id")
        else:
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error registrando {agente['nombre']}: {e}")
        return None

def main():
    print("="*60)
    print("SINCRONIZADOR DE COLMENA - AUTO-DISCOVERY JERÁRQUICO")
    print("="*60)
    
    # Detectar puerto de Paperclip
    puerto = detectar_puerto_paperclip()
    if not puerto:
        print("ERROR: No se detectó Paperclip corriendo en puertos 3100-3102")
        print("Asegúrate de que Paperclip esté iniciado antes de ejecutar este script.")
        return
    
    print(f"Paperclip detectado en puerto: {puerto}")
    
    # Obtener company ID
    company_id = obtener_company_id(puerto)
    if not company_id:
        print("ERROR: No se pudo obtener el ID de la compañía")
        return
    
    print(f"Company ID: {company_id}")
    
    # PASO 1: Escanear agentes
    print("\n" + "="*60)
    print("PASO 1: ESCANEANDO AGENTES")
    print("="*60)
    agentes = escanear_agentes()
    print(f"\nAgentes descubiertos: {len(agentes)}")
    
    if len(agentes) == 0:
        print("No se encontraron agentes para sincronizar.")
        return
    
    # Mostrar distribución por teams (metadata)
    print("\nDistribución por Teams (metadata):")
    team_counts = {}
    for agente in agentes:
        team_name = next((t["name"] for t in TEAMS_DEFINITION if t["id"] == agente["team_id"]), "Desconocido")
        team_counts[team_name] = team_counts.get(team_name, 0) + 1
    
    for team, count in sorted(team_counts.items()):
        print(f"  - {team}: {count} agentes")
    
    # PASO 2: Registrar agentes y obtener sus IDs
    print("\n" + "="*60)
    print("PASO 2: REGISTRANDO AGENTES")
    print("="*60)
    agentes_registrados = {}  # nombre -> id
    exitosos = 0
    fallidos = 0
    
    for agente in agentes:
        agente_id = registrar_agente_en_paperclip(agente, puerto, company_id)
        if agente_id:
            agentes_registrados[agente["nombre"]] = agente_id
            print(f"✓ {agente['nombre']} registrado (ID: {agente_id[:8]}...)")
            exitosos += 1
        else:
            print(f"✗ {agente['nombre']} falló")
            fallidos += 1
    
    # PASO 3: Configurar jerarquía (reportsTo)
    print("\n" + "="*60)
    print("PASO 3: CONFIGURANDO JERARQUÍA (reportsTo)")
    print("="*60)
    
    # Obtener ID de AGI Telegram (Llm Manager)
    agi_id = agentes_registrados.get("Llm Manager")
    if not agi_id:
        print("WARNING: No se encontró 'Llm Manager' (AGI Telegram). Buscando alternativo...")
        # Intentar con otros nombres posibles
        for nombre in ["Ai Town", "Render", "Seguridad"]:
            if nombre in agentes_registrados:
                agi_id = agentes_registrados[nombre]
                print(f"Usando {nombre} como agente principal")
                break
    
    if agi_id:
        print(f"Agente principal (CEO I): ID {agi_id[:8]}...")
        
        # Configurar reportsTo para todos los demás agentes
        jerarquia_exitosos = 0
        for nombre, agente_id in agentes_registrados.items():
            if agente_id != agi_id:  # No asignar reportsTo a sí mismo
                if actualizar_reports_to_agente(puerto, company_id, agente_id, agi_id):
                    print(f"✓ {nombre} -> reportsTo CEO I")
                    jerarquia_exitosos += 1
                else:
                    print(f"✗ {nombre} falló asignar reportsTo")
        
        print(f"\nJerarquía configurada: {jerarquia_exitosos}/{len(agentes_registrados)-1} agentes reportan a CEO I")
    else:
        print("ERROR: No se pudo identificar el agente principal para jerarquía")
    
    # Reporte final
    print("\n" + "="*60)
    print("REPORTE FINAL")
    print("="*60)
    print(f"Total agentes descubiertos: {len(agentes)}")
    print(f"Agentes registrados exitosamente: {exitosos}")
    print(f"Agentes fallidos: {fallidos}")
    print(f"\nJerarquía configurada:")
    print(f"  Sergio Palomba (CEO 0)")
    if agi_id:
        print(f"    └─ CEO I (ID: {agi_id[:8]}...)")
        print(f"       └─ {len(agentes_registrados)-1} agentes reportan a CEO I")
    print(f"\nDistribución por Teams (metadata):")
    for team, count in sorted(team_counts.items()):
        print(f"  - {team}: {count} agentes")
    print(f"\nPanel de Paperclip: http://127.0.0.1:{puerto}")
    print("="*60)

if __name__ == "__main__":
    main()

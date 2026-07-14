"""
Script para purga total de agentes en Paperclip
"""
import requests
import json

PAPERCLIP_PORTS = [3100, 3101, 3102]
COMPANY_ID = "4e83ada7-4b92-4c3d-bcef-21ebdd2a389e"

def detectar_puerto():
    for port in PAPERCLIP_PORTS:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/api/companies", timeout=2)
            if response.status_code == 200:
                return port
        except:
            continue
    return None

def obtener_agentes(puerto):
    try:
        url = f"http://127.0.0.1:{puerto}/api/companies/{COMPANY_ID}/agents"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error obteniendo agentes: {e}")
        return []

def eliminar_agente(puerto, agente_id):
    try:
        url = f"http://127.0.0.1:{puerto}/api/companies/{COMPANY_ID}/agents/{agente_id}"
        response = requests.delete(url, timeout=5)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error eliminando agente {agente_id}: {e}")
        return False

def main():
    print("="*60)
    print("PURGA TOTAL DE AGENTES - PAPERCLIP")
    print("="*60)
    
    puerto = detectar_puerto()
    if not puerto:
        print("ERROR: No se detectó Paperclip")
        return
    
    print(f"Paperclip detectado en puerto: {puerto}")
    
    agentes = obtener_agentes(puerto)
    print(f"Agentes encontrados: {len(agentes)}")
    
    if len(agentes) == 0:
        print("No hay agentes para eliminar")
        return
    
    confirmacion = input(f"¿Estás seguro de eliminar {len(agentes)} agentes? (s/N): ")
    if confirmacion.lower() != 's':
        print("Operación cancelada")
        return
    
    exitosos = 0
    fallidos = 0
    
    for agente in agentes:
        agente_id = agente["id"]
        nombre = agente["name"]
        if eliminar_agente(puerto, agente_id):
            print(f"✓ {nombre} eliminado")
            exitosos += 1
        else:
            print(f"✗ {nombre} falló")
            fallidos += 1
    
    print("\n" + "="*60)
    print("REPORTE FINAL")
    print("="*60)
    print(f"Agentes eliminados: {exitosos}")
    print(f"Agentes fallidos: {fallidos}")
    print("="*60)

if __name__ == "__main__":
    main()

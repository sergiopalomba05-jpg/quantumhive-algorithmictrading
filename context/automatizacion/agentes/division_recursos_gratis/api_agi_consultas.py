#!/usr/bin/env python3
"""
API AGI Consultas
================
API para que AGI consulte información sobre recursos, procesos, cuentas disponibles.
Endpoints para estado de recursos, procesos activos, cuentas disponibles.
Endpoints para solicitar asignación de recursos, inicio de procesos.
Endpoints para obtener informes de gestión, alertas.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIAGIConsultas:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def cargar_recursos_centralizados(self) -> Dict:
        """Carga datos centralizados del administrador."""
        recursos_file = self.output_dir / "recursos_centralizados.json"
        if recursos_file.exists():
            with open(recursos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def cargar_procesos_nubes(self) -> Dict:
        """Carga datos de procesos del gestor de nubes."""
        procesos_file = self.output_dir / "procesos_nubes.json"
        if procesos_file.exists():
            with open(procesos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def cargar_reportes(self) -> Dict:
        """Carga reportes generados."""
        reportes_dir = self.output_dir / "reportes"
        reportes = {}
        
        if reportes_dir.exists():
            for archivo in reportes_dir.glob("*.json"):
                with open(archivo, 'r', encoding='utf-8') as f:
                    reportes[archivo.stem] = json.load(f)
        
        return reportes
    
    # ENDPOINTS PARA CONSULTAR INFORMACIÓN
    
    def endpoint_estado_recursos(self) -> Dict:
        """Endpoint: Consultar estado de recursos."""
        datos = self.cargar_recursos_centralizados()
        
        return {
            "endpoint": "estado_recursos",
            "fecha_consulta": datetime.now().isoformat(),
            "total_recursos": datos.get("total_recursos", 0),
            "activos": len(datos.get("clasificacion_estado", {}).get("activos", [])),
            "caducados": len(datos.get("clasificacion_estado", {}).get("caducados", [])),
            "clasificacion_estado": datos.get("clasificacion_estado", {}),
            "alertas": datos.get("alertas", [])
        }
    
    def endpoint_procesos_activos(self) -> Dict:
        """Endpoint: Consultar procesos activos."""
        datos = self.cargar_procesos_nubes()
        
        return {
            "endpoint": "procesos_activos",
            "fecha_consulta": datetime.now().isoformat(),
            "total_procesos": datos.get("total_procesos", 0),
            "asignaciones": datos.get("asignaciones", []),
            "estado_procesos": datos.get("estado_procesos", [])
        }
    
    def endpoint_cuentas_disponibles(self) -> Dict:
        """Endpoint: Consultar cuentas disponibles."""
        datos = self.cargar_recursos_centralizados()
        
        cuentas = []
        for recurso in datos.get("recursos_centralizados", []):
            if recurso.get("tipo") in ["compute", "vps", "trial"]:
                cuentas.append({
                    "nombre": recurso.get("nombre"),
                    "proveedor": recurso.get("proveedor"),
                    "estado": recurso.get("estado"),
                    "duracion": recurso.get("duracion")
                })
        
        return {
            "endpoint": "cuentas_disponibles",
            "fecha_consulta": datetime.now().isoformat(),
            "total_cuentas": len(cuentas),
            "cuentas": cuentas
        }
    
    def endpoint_informes_gestion(self) -> Dict:
        """Endpoint: Obtener informes de gestión."""
        reportes = self.cargar_reportes()
        
        return {
            "endpoint": "informes_gestion",
            "fecha_consulta": datetime.now().isoformat(),
            "total_reportes": len(reportes),
            "reportes": reportes
        }
    
    # ENDPOINTS PARA SOLICITAR ACCIONES
    
    def endpoint_solicitar_recurso(self, tipo_carga: str = "entrenamiento_ml") -> Dict:
        """Endpoint: Solicitar asignación de recurso."""
        datos = self.cargar_recursos_centralizados()
        
        # Buscar recurso óptimo para el tipo de carga
        recursos_carga = datos.get("clasificacion_carga", {}).get(tipo_carga, [])
        recursos_activos = datos.get("clasificacion_estado", {}).get("activos", [])
        
        # Intersección
        disponibles = [r for r in recursos_carga if r in recursos_activos]
        
        if disponibles:
            recurso = disponibles[0]
            return {
                "endpoint": "solicitar_recurso",
                "fecha_solicitud": datetime.now().isoformat(),
                "tipo_carga": tipo_carga,
                "recurso_asignado": recurso,
                "estado": "asignado"
            }
        else:
            return {
                "endpoint": "solicitar_recurso",
                "fecha_solicitud": datetime.now().isoformat(),
                "tipo_carga": tipo_carga,
                "estado": "no_disponible",
                "mensaje": "No hay recursos disponibles para este tipo de carga"
            }
    
    def endpoint_iniciar_proceso(self, proceso: Dict) -> Dict:
        """Endpoint: Iniciar proceso en nube."""
        datos = self.cargar_procesos_nubes()
        
        # Simular inicio de proceso
        asignacion = {
            "endpoint": "iniciar_proceso",
            "fecha_inicio": datetime.now().isoformat(),
            "proceso": proceso.get("nombre"),
            "tipo_carga": proceso.get("tipo_carga"),
            "estado": "iniciado",
            "mensaje": "Proceso iniciado en nube seleccionada"
        }
        
        return asignacion
    
    # ENDPOINT GENERAL PARA CONSULTAS COMPLEJAS
    
    def endpoint_consulta_general(self, consulta: str) -> Dict:
        """Endpoint: Consulta general para AGI."""
        datos_recursos = self.cargar_recursos_centralizados()
        datos_procesos = self.cargar_procesos_nubes()
        
        respuesta = {
            "endpoint": "consulta_general",
            "fecha_consulta": datetime.now().isoformat(),
            "consulta": consulta,
            "resumen": {
                "total_recursos": datos_recursos.get("total_recursos", 0),
                "total_procesos": datos_procesos.get("total_procesos", 0),
                "alertas": len(datos_recursos.get("alertas", []))
            },
            "recursos_disponibles": datos_recursos.get("clasificacion_estado", {}).get("activos", []),
            "procesos_activos": datos_procesos.get("estado_procesos", []),
            "alertas": datos_recursos.get("alertas", [])
        }
        
        return respuesta
    
    def procesar_consulta_agi(self, endpoint: str, **kwargs) -> Dict:
        """Procesa consulta de AGI y devuelve respuesta."""
        logger.info(f"[API] Consulta AGI recibida: {endpoint}")
        
        if endpoint == "estado_recursos":
            return self.endpoint_estado_recursos()
        elif endpoint == "procesos_activos":
            return self.endpoint_procesos_activos()
        elif endpoint == "cuentas_disponibles":
            return self.endpoint_cuentas_disponibles()
        elif endpoint == "informes_gestion":
            return self.endpoint_informes_gestion()
        elif endpoint == "solicitar_recurso":
            return self.endpoint_solicitar_recurso(kwargs.get("tipo_carga", "entrenamiento_ml"))
        elif endpoint == "iniciar_proceso":
            return self.endpoint_iniciar_proceso(kwargs.get("proceso", {}))
        elif endpoint == "consulta_general":
            return self.endpoint_consulta_general(kwargs.get("consulta", ""))
        else:
            return {
                "endpoint": endpoint,
                "estado": "error",
                "mensaje": "Endpoint no reconocido"
            }

if __name__ == "__main__":
    api = APIAGIConsultas()
    
    # Ejemplo de uso
    print("=== ESTADO RECURSOS ===")
    print(json.dumps(api.endpoint_estado_recursos(), indent=2))
    
    print("\n=== PROCESOS ACTIVOS ===")
    print(json.dumps(api.endpoint_procesos_activos(), indent=2))
    
    print("\n=== CUENTAS DISPONIBLES ===")
    print(json.dumps(api.endpoint_cuentas_disponibles(), indent=2))

#!/usr/bin/env python3
"""
Agente Recolector de Nubes Gratis
=================================
Busca nubes gratuitas, VPS gratuitos, periodos de prueba gratuitos.
Clasifica por tipo, límites, duración, restricciones.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteRecolectorNubes:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.output_dir / "nubes_gratis.json"
        
    def buscar_nubes_gratis(self) -> List[Dict]:
        """Busca nubes gratuitas disponibles."""
        nubes = [
            {
                "nombre": "Google Cloud Free Tier",
                "proveedor": "Google",
                "tipo": "compute",
                "cpu": "e2-micro",
                "ram": "1GB",
                "storage": "30GB HDD",
                "duracion": "Siempre gratis (con límites)",
                "limite_uso": "1 instancia f1-micro por mes",
                "regiones": ["us-central1", "us-east1", "europe-west1"],
                "requisitos": "Cuenta Google válida, tarjeta de crédito",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "AWS Free Tier",
                "proveedor": "Amazon",
                "tipo": "compute",
                "cpu": "t2.micro",
                "ram": "1GB",
                "storage": "30GB SSD",
                "duracion": "12 meses",
                "limite_uso": "750 horas/mes",
                "regiones": ["us-east-1", "us-west-2", "eu-west-1"],
                "requisitos": "Cuenta AWS nueva, tarjeta de crédito",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Oracle Cloud Always Free",
                "proveedor": "Oracle",
                "tipo": "compute",
                "cpu": "4 OCPU",
                "ram": "24GB",
                "storage": "200GB",
                "duracion": "Siempre gratis",
                "limite_uso": "2 instancias ARM",
                "regiones": ["us-ashburn-1", "eu-frankfurt-1", "ap-tokyo-1"],
                "requisitos": "Cuenta Oracle Cloud gratuita",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Azure Free Tier",
                "proveedor": "Microsoft",
                "tipo": "compute",
                "cpu": "B1S",
                "ram": "1GB",
                "storage": "30GB SSD",
                "duracion": "12 meses",
                "limite_uso": "750 horas/mes",
                "regiones": ["eastus", "westeurope", "southeastasia"],
                "requisitos": "Cuenta Azure nueva, tarjeta de crédito",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[RECOLECTOR] {len(nubes)} nubes gratuitas encontradas")
        return nubes
    
    def buscar_vps_gratis(self) -> List[Dict]:
        """Busca VPS gratuitos."""
        vps = [
            {
                "nombre": "Oracle Cloud Free VPS",
                "proveedor": "Oracle",
                "tipo": "vps",
                "cpu": "4 OCPU ARM",
                "ram": "24GB",
                "storage": "200GB",
                "duracion": "Siempre gratis",
                "limite_uso": "2 instancias",
                "regiones": ["us-ashburn-1", "eu-frankfurt-1"],
                "requisitos": "Cuenta Oracle Cloud gratuita",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "AWS Lightsail Free Trial",
                "proveedor": "Amazon",
                "tipo": "vps",
                "cpu": "1 vCPU",
                "ram": "512MB",
                "storage": "20GB SSD",
                "duracion": "1 mes",
                "limite_uso": "1 instancia",
                "regiones": ["us-east-1", "us-west-2"],
                "requisitos": "Cuenta AWS nueva",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[RECOLECTOR] {len(vps)} VPS gratuitos encontrados")
        return vps
    
    def buscar_periodos_prueba(self) -> List[Dict]:
        """Busca periodos de prueba gratuitos."""
        trials = [
            {
                "nombre": "DigitalOcean Free Trial",
                "proveedor": "DigitalOcean",
                "tipo": "trial",
                "cpu": "1 vCPU",
                "ram": "1GB",
                "storage": "25GB SSD",
                "duracion": "60 días",
                "limite_uso": "$200 crédito",
                "regiones": ["nyc1", "sfo2", "ams3"],
                "requisitos": "Tarjeta de crédito válida",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Linode Free Trial",
                "proveedor": "Linode",
                "tipo": "trial",
                "cpu": "1 vCPU",
                "ram": "1GB",
                "storage": "25GB SSD",
                "duracion": "60 días",
                "limite_uso": "$100 crédito",
                "regiones": ["us-east", "eu-west", "ap-south"],
                "requisitos": "Tarjeta de crédito válida",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[RECOLECTOR] {len(trials)} periodos de prueba encontrados")
        return trials
    
    def clasificar_recursos(self, recursos: List[Dict]) -> Dict[str, List[Dict]]:
        """Clasifica recursos por tipo y estado."""
        clasificacion = {
            "compute": [],
            "vps": [],
            "trial": [],
            "activos": [],
            "caducados": []
        }
        
        for recurso in recursos:
            tipo = recurso.get("tipo", "unknown")
            estado = recurso.get("estado", "unknown")
            
            if tipo in clasificacion:
                clasificacion[tipo].append(recurso)
            
            if estado == "activo":
                clasificacion["activos"].append(recurso)
            elif estado == "caducado":
                clasificacion["caducados"].append(recurso)
        
        return clasificacion
    
    def guardar_datos(self, datos: Dict):
        """Guarda los datos recolectados."""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        logger.info(f"[RECOLECTOR] Datos guardados en {self.db_file}")
    
    def recolectar_todo(self):
        """Recolecta todos los recursos de nubes."""
        logger.info("[RECOLECTOR] Iniciando recolección de nubes gratuitas...")
        
        nubes = self.buscar_nubes_gratis()
        vps = self.buscar_vps_gratis()
        trials = self.buscar_periodos_prueba()
        
        todos_recursos = nubes + vps + trials
        clasificacion = self.clasificar_recursos(todos_recursos)
        
        datos = {
            "fecha_recoleccion": datetime.now().isoformat(),
            "total_recursos": len(todos_recursos),
            "recursos": todos_recursos,
            "clasificacion": clasificacion
        }
        
        self.guardar_datos(datos)
        
        logger.info(f"[RECOLECTOR] Recolección completada: {len(todos_recursos)} recursos")
        return datos

if __name__ == "__main__":
    recolector = AgenteRecolectorNubes()
    recolector.recolectar_todo()

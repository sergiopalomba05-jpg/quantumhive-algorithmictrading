#!/usr/bin/env python3
"""
Agente Recolector de Recursos Varios
=====================================
Busca otros recursos gratuitos: APIs, datasets, herramientas, frameworks.
Clasifica por tipo, límites, disponibilidad.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteRecolectorRecursosVarios:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.output_dir / "recursos_varios.json"
        
    def buscar_apis_gratis(self) -> List[Dict]:
        """Busca APIs gratuitas relevantes para trading."""
        apis = [
            {
                "nombre": "Alpha Vantage",
                "tipo": "api_financiera",
                "categoria": "datos_mercado",
                "limite_uso": "500 requests/día",
                "duracion": "Siempre gratis",
                "requisitos": "API Key gratuita",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Yahoo Finance API",
                "tipo": "api_financiera",
                "categoria": "datos_mercado",
                "limite_uso": "Sin límite oficial",
                "duracion": "Siempre gratis",
                "requisitos": "Ninguno",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Polygon.io",
                "tipo": "api_financiera",
                "categoria": "datos_mercado",
                "limite_uso": "5 requests/minuto",
                "duracion": "Siempre gratis",
                "requisitos": "API Key gratuita",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[RECOLECTOR] {len(apis)} APIs gratuitas encontradas")
        return apis
    
    def buscar_datasets_gratis(self) -> List[Dict]:
        """Busca datasets gratuitos para entrenamiento."""
        datasets = [
            {
                "nombre": "Kaggle Datasets",
                "tipo": "dataset",
                "categoria": "datos_financieros",
                "limite_uso": "Sin límite",
                "duracion": "Siempre gratis",
                "requisitos": "Cuenta Kaggle",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Yahoo Finance Historical Data",
                "tipo": "dataset",
                "categoria": "datos_financieros",
                "limite_uso": "Sin límite",
                "duracion": "Siempre gratis",
                "requisitos": "Ninguno",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[RECOLECTOR] {len(datasets)} datasets gratuitos encontrados")
        return datasets
    
    def buscar_herramientas_gratis(self) -> List[Dict]:
        """Busca herramientas gratuitas para desarrollo."""
        herramientas = [
            {
                "nombre": "GitHub Free",
                "tipo": "herramienta",
                "categoria": "versionado",
                "limite_uso": "Repositorios ilimitados públicos",
                "duracion": "Siempre gratis",
                "requisitos": "Cuenta GitHub",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "VS Code",
                "tipo": "herramienta",
                "categoria": "ide",
                "limite_uso": "Sin límite",
                "duracion": "Siempre gratis",
                "requisitos": "Ninguno",
                "estado": "activo",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[RECOLECTOR] {len(herramientas)} herramientas gratuitas encontradas")
        return herramientas
    
    def clasificar_recursos(self, recursos: List[Dict]) -> Dict[str, List[Dict]]:
        """Clasifica recursos por tipo y categoría."""
        clasificacion = {
            "api": [],
            "dataset": [],
            "herramienta": [],
            "datos_mercado": [],
            "datos_financieros": [],
            "versionado": [],
            "ide": []
        }
        
        for recurso in recursos:
            tipo = recurso.get("tipo", "unknown")
            categoria = recurso.get("categoria", "unknown")
            
            if tipo in clasificacion:
                clasificacion[tipo].append(recurso)
            if categoria in clasificacion:
                clasificacion[categoria].append(recurso)
        
        return clasificacion
    
    def guardar_datos(self, datos: Dict):
        """Guarda los datos recolectados."""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        logger.info(f"[RECOLECTOR] Datos guardados en {self.db_file}")
    
    def recolectar_todo(self):
        """Recolecta todos los recursos varios."""
        logger.info("[RECOLECTOR] Iniciando recolección de recursos varios...")
        
        apis = self.buscar_apis_gratis()
        datasets = self.buscar_datasets_gratis()
        herramientas = self.buscar_herramientas_gratis()
        
        todos_recursos = apis + datasets + herramientas
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
    recolector = AgenteRecolectorRecursosVarios()
    recolector.recolectar_todo()

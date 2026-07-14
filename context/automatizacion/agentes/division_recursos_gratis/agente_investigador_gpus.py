#!/usr/bin/env python3
"""
Agente Investigador de GPUs
===========================
Investiga GPUs gratuitas disponibles.
Clasifica por tipo, memoria VRAM, disponibilidad, restricciones.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteInvestigadorGPUs:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.output_dir / "gpus_gratis.json"
        
    def investigar_gpus_gratis(self) -> List[Dict]:
        """Investiga GPUs gratuitas disponibles."""
        gpus = [
            {
                "nombre": "Google Colab",
                "proveedor": "Google",
                "tipo_gpu": "T4 / V100 / A100 (aleatorio)",
                "vram": "16GB (T4), 32GB (V100), 40GB (A100)",
                "duracion_sesion": "12 horas",
                "limite_uso": "Sesiones ilimitadas con timeout",
                "requisitos": "Cuenta Google",
                "estado": "activo",
                "disponibilidad": "Alta",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Kaggle Kernels",
                "proveedor": "Kaggle",
                "tipo_gpu": "T4 / P100",
                "vram": "16GB (T4), 16GB (P100)",
                "duracion_sesion": "12 horas",
                "limite_uso": "30 horas/semana GPU",
                "requisitos": "Cuenta Kaggle",
                "estado": "activo",
                "disponibilidad": "Media",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Hugging Face Spaces",
                "proveedor": "Hugging Face",
                "tipo_gpu": "T4",
                "vram": "16GB",
                "duracion_sesion": "Siempre",
                "limite_uso": "1 espacio GPU gratuito",
                "requisitos": "Cuenta Hugging Face",
                "estado": "activo",
                "disponibilidad": "Alta",
                "fecha_registro": datetime.now().isoformat()
            },
            {
                "nombre": "Oracle Cloud GPU Always Free",
                "proveedor": "Oracle",
                "tipo_gpu": "No disponible en tier gratuito",
                "vram": "N/A",
                "duracion_sesion": "N/A",
                "limite_uso": "N/A",
                "requisitos": "N/A",
                "estado": "no_disponible",
                "disponibilidad": "Baja",
                "nota": "GPU requiere plan pago",
                "fecha_registro": datetime.now().isoformat()
            }
        ]
        
        logger.info(f"[INVESTIGADOR] {len(gpus)} GPUs investigadas")
        return gpus
    
    def clasificar_gpus(self, gpus: List[Dict]) -> Dict[str, List[Dict]]:
        """Clasifica GPUs por tipo y disponibilidad."""
        clasificacion = {
            "disponibles": [],
            "no_disponibles": [],
            "alta_disponibilidad": [],
            "media_disponibilidad": [],
            "baja_disponibilidad": []
        }
        
        for gpu in gpus:
            estado = gpu.get("estado", "unknown")
            disponibilidad = gpu.get("disponibilidad", "unknown")
            
            if estado == "activo":
                clasificacion["disponibles"].append(gpu)
            elif estado == "no_disponible":
                clasificacion["no_disponibles"].append(gpu)
            
            if disponibilidad == "Alta":
                clasificacion["alta_disponibilidad"].append(gpu)
            elif disponibilidad == "Media":
                clasificacion["media_disponibilidad"].append(gpu)
            elif disponibilidad == "Baja":
                clasificacion["baja_disponibilidad"].append(gpu)
        
        return clasificacion
    
    def guardar_datos(self, datos: Dict):
        """Guarda los datos investigados."""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        logger.info(f"[INVESTIGADOR] Datos guardados en {self.db_file}")
    
    def investigar_todo(self):
        """Investiga todos los recursos de GPUs."""
        logger.info("[INVESTIGADOR] Iniciando investigación de GPUs gratuitas...")
        
        gpus = self.investigar_gpus_gratis()
        clasificacion = self.clasificar_gpus(gpus)
        
        datos = {
            "fecha_investigacion": datetime.now().isoformat(),
            "total_gpus": len(gpus),
            "gpus": gpus,
            "clasificacion": clasificacion
        }
        
        self.guardar_datos(datos)
        
        logger.info(f"[INVESTIGADOR] Investigación completada: {len(gpus)} GPUs")
        return datos

if __name__ == "__main__":
    investigador = AgenteInvestigadorGPUs()
    investigador.investigar_todo()

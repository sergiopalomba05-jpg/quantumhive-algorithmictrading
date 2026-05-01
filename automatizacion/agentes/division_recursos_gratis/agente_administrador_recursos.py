#!/usr/bin/env python3
"""
Agente Administrador de Recursos
================================
Centraliza y gestiona información de TODOS los recolectores de la división.
Clasifica recursos por estado, prioridad, tipo de carga.
Gestiona cuentas/credenciales de nubes gratuitas.
Asigna recursos a procesos según disponibilidad.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteAdministradorRecursos:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.output_dir / "recursos_centralizados.json"
        self.cuentas_file = self.output_dir / "cuentas_nubes.json"
        
    def cargar_datos_recolectores(self) -> Dict:
        """Carga datos de todos los recolectores."""
        datos = {
            "nubes_gratis": {},
            "gpus_gratis": {},
            "recursos_varios": {}
        }
        
        # Cargar datos de nubes
        nubes_file = self.output_dir / "nubes_gratis.json"
        if nubes_file.exists():
            with open(nubes_file, 'r', encoding='utf-8') as f:
                datos["nubes_gratis"] = json.load(f)
        
        # Cargar datos de GPUs
        gpus_file = self.output_dir / "gpus_gratis.json"
        if gpus_file.exists():
            with open(gpus_file, 'r', encoding='utf-8') as f:
                datos["gpus_gratis"] = json.load(f)
        
        # Cargar datos de recursos varios
        recursos_file = self.output_dir / "recursos_varios.json"
        if recursos_file.exists():
            with open(recursos_file, 'r', encoding='utf-8') as f:
                datos["recursos_varios"] = json.load(f)
        
        logger.info("[ADMINISTRADOR] Datos de recolectores cargados")
        return datos
    
    def centralizar_recursos(self, datos_recolectores: Dict) -> Dict:
        """Centraliza todos los recursos de los recolectores."""
        recursos_centralizados = []
        
        # Extraer recursos de nubes
        if "recursos" in datos_recolectores.get("nubes_gratis", {}):
            recursos_centralizados.extend(datos_recolectores["nubes_gratis"]["recursos"])
        
        # Extraer recursos de GPUs
        if "gpus" in datos_recolectores.get("gpus_gratis", {}):
            recursos_centralizados.extend(datos_recolectores["gpus_gratis"]["gpus"])
        
        # Extraer recursos varios
        if "recursos" in datos_recolectores.get("recursos_varios", {}):
            recursos_centralizados.extend(datos_recolectores["recursos_varios"]["recursos"])
        
        logger.info(f"[ADMINISTRADOR] {len(recursos_centralizados)} recursos centralizados")
        return recursos_centralizados
    
    def clasificar_por_estado(self, recursos: List[Dict]) -> Dict[str, List[Dict]]:
        """Clasifica recursos por estado."""
        clasificacion = {
            "activos": [],
            "caducados": [],
            "no_disponibles": [],
            "pendientes": []
        }
        
        for recurso in recursos:
            estado = recurso.get("estado", "unknown")
            if estado in clasificacion:
                clasificacion[estado].append(recurso)
            else:
                clasificacion["pendientes"].append(recurso)
        
        return clasificacion
    
    def clasificar_por_prioridad(self, recursos: List[Dict]) -> Dict[str, List[Dict]]:
        """Clasifica recursos por prioridad de uso."""
        clasificacion = {
            "alta": [],
            "media": [],
            "baja": []
        }
        
        for recurso in recursos:
            tipo = recurso.get("tipo", "unknown")
            proveedor = recurso.get("proveedor", "unknown")
            
            # Asignar prioridad basada en tipo y proveedor
            if tipo in ["compute", "vps"] and proveedor in ["Oracle", "Google"]:
                clasificacion["alta"].append(recurso)
            elif tipo in ["trial"] or proveedor in ["AWS", "Azure"]:
                clasificacion["media"].append(recurso)
            else:
                clasificacion["baja"].append(recurso)
        
        return clasificacion
    
    def clasificar_por_tipo_carga(self, recursos: List[Dict]) -> Dict[str, List[Dict]]:
        """Clasifica recursos por tipo de carga que pueden soportar."""
        clasificacion = {
            "entrenamiento_ml": [],
            "backtesting": [],
            "almacenamiento": [],
            "api_requests": []
        }
        
        for recurso in recursos:
            tipo = recurso.get("tipo", "unknown")
            categoria = recurso.get("categoria", "unknown")
            
            if tipo in ["compute", "vps"] or categoria == "datos_financieros":
                clasificacion["entrenamiento_ml"].append(recurso)
            if tipo in ["compute", "vps"]:
                clasificacion["backtesting"].append(recurso)
            if "storage" in recurso:
                clasificacion["almacenamiento"].append(recurso)
            if tipo == "api":
                clasificacion["api_requests"].append(recurso)
        
        return clasificacion
    
    def generar_alertas_caducidad(self, recursos: List[Dict]) -> List[Dict]:
        """Genera alertas para recursos próximos a caducar."""
        alertas = []
        
        for recurso in recursos:
            duracion = recurso.get("duracion", "")
            if "mes" in duracion.lower() or "día" in duracion.lower():
                alertas.append({
                    "recurso": recurso.get("nombre"),
                    "tipo": recurso.get("tipo"),
                    "duracion": duracion,
                    "mensaje": f"Recurso {recurso.get('nombre')} tiene duración limitada: {duracion}",
                    "fecha_alerta": datetime.now().isoformat()
                })
        
        return alertas
    
    def guardar_centralizacion(self, datos: Dict):
        """Guarda los datos centralizados."""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        logger.info(f"[ADMINISTRADOR] Datos centralizados guardados en {self.db_file}")
    
    def administrar_todo(self):
        """Administra todos los recursos de la división."""
        logger.info("[ADMINISTRADOR] Iniciando administración de recursos...")
        
        datos_recolectores = self.cargar_datos_recolectores()
        recursos_centralizados = self.centralizar_recursos(datos_recolectores)
        
        clasificacion_estado = self.clasificar_por_estado(recursos_centralizados)
        clasificacion_prioridad = self.clasificar_por_prioridad(recursos_centralizados)
        clasificacion_carga = self.clasificar_por_tipo_carga(recursos_centralizados)
        alertas = self.generar_alertas_caducidad(recursos_centralizados)
        
        datos = {
            "fecha_actualizacion": datetime.now().isoformat(),
            "total_recursos": len(recursos_centralizados),
            "recursos_centralizados": recursos_centralizados,
            "clasificacion_estado": clasificacion_estado,
            "clasificacion_prioridad": clasificacion_prioridad,
            "clasificacion_carga": clasificacion_carga,
            "alertas": alertas,
            "datos_recolectores": datos_recolectores
        }
        
        self.guardar_centralizacion(datos)
        
        logger.info(f"[ADMINISTRADOR] Administración completada: {len(recursos_centralizados)} recursos, {len(alertas)} alertas")
        return datos

if __name__ == "__main__":
    administrador = AgenteAdministradorRecursos()
    administrador.administrar_todo()

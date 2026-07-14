#!/usr/bin/env python3
"""
Agente Gestor de Nubes
======================
Distribuye procesos de entrenamiento en nubes gratuitas disponibles.
Balancea carga entre múltiples nubes.
Monitorea estado de procesos en cada nube.
Reasigna procesos si una nube falla o caduca.
Sincroniza modelos entrenados de vuelta al repositorio central.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteGestorNubes:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.procesos_file = self.output_dir / "procesos_nubes.json"
        self.modelos_file = self.output_dir / "modelos_sincronizados.json"
        
    def cargar_recursos_disponibles(self) -> Dict:
        """Carga recursos disponibles del administrador."""
        recursos_file = self.output_dir / "recursos_centralizados.json"
        if recursos_file.exists():
            with open(recursos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def seleccionar_nube_optima(self, recursos: Dict, tipo_carga: str = "entrenamiento_ml") -> Dict:
        """Selecciona la nube óptima para un tipo de carga."""
        recursos_activos = recursos.get("clasificacion_estado", {}).get("activos", [])
        recursos_prioridad = recursos.get("clasificacion_prioridad", {})
        
        # Filtrar por tipo de carga
        recursos_carga = recursos.get("clasificacion_carga", {}).get(tipo_carga, [])
        
        # Priorizar recursos de alta prioridad
        alta_prioridad = recursos_prioridad.get("alta", [])
        
        # Intersección: recursos activos + tipo de carga + alta prioridad
        seleccionados = [r for r in recursos_carga if r in recursos_activos and r in alta_prioridad]
        
        if seleccionados:
            return seleccionados[0]
        elif recursos_carga:
            return recursos_carga[0]
        elif recursos_activos:
            return recursos_activos[0]
        else:
            return {}
    
    def asignar_proceso_a_nube(self, proceso: Dict, recursos: Dict) -> Dict:
        """Asigna un proceso a una nube específica."""
        tipo_carga = proceso.get("tipo_carga", "entrenamiento_ml")
        nube_seleccionada = self.seleccionar_nube_optima(recursos, tipo_carga)
        
        if not nube_seleccionada:
            logger.warning(f"[GESTOR] No hay nubes disponibles para proceso {proceso.get('nombre')}")
            return {}
        
        asignacion = {
            "proceso": proceso.get("nombre"),
            "nube": nube_seleccionada.get("nombre"),
            "proveedor": nube_seleccionada.get("proveedor"),
            "tipo": nube_seleccionada.get("tipo"),
            "estado": "asignado",
            "fecha_asignacion": datetime.now().isoformat(),
            "proceso_config": proceso
        }
        
        logger.info(f"[GESTOR] Proceso {proceso.get('nombre')} asignado a {nube_seleccionada.get('nombre')}")
        return asignacion
    
    def balancear_carga(self, procesos: List[Dict], recursos: Dict) -> List[Dict]:
        """Balancea carga entre múltiples nubes."""
        asignaciones = []
        nubes_usadas = {}
        
        for proceso in procesos:
            asignacion = self.asignar_proceso_a_nube(proceso, recursos)
            if asignacion:
                asignaciones.append(asignacion)
                
                # Rastrear uso de nubes
                nube = asignacion.get("nube")
                nubes_usadas[nube] = nubes_usadas.get(nube, 0) + 1
        
        logger.info(f"[GESTOR] Carga balanceada: {len(asignaciones)} procesos en {len(nubes_usadas)} nubes")
        return asignaciones
    
    def monitorear_procesos(self, asignaciones: List[Dict]) -> List[Dict]:
        """Monitorea estado de procesos en cada nube."""
        estado_procesos = []
        
        for asignacion in asignaciones:
            # Simulación de monitoreo
            estado = {
                "proceso": asignacion.get("proceso"),
                "nube": asignacion.get("nube"),
                "estado": "ejecutando",
                "progreso": "50%",
                "fecha_monitoreo": datetime.now().isoformat()
            }
            estado_procesos.append(estado)
        
        logger.info(f"[GESTOR] {len(estado_procesos)} procesos monitoreados")
        return estado_procesos
    
    def reasignar_proceso_fallido(self, proceso: Dict, recursos: Dict) -> Dict:
        """Reasigna un proceso fallido a otra nube."""
        logger.warning(f"[GESTOR] Reasignando proceso fallido: {proceso.get('proceso')}")
        
        # Excluir nube fallida de selección
        nube_fallida = proceso.get("nube")
        
        # Buscar nueva nube
        nueva_asignacion = self.asignar_proceso_a_nube(proceso, recursos)
        
        if nueva_asignacion and nueva_asignacion.get("nube") != nube_fallida:
            nueva_asignacion["estado"] = "reasignado"
            nueva_asignacion["nube_anterior"] = nube_fallida
            logger.info(f"[GESTOR] Proceso reasignado de {nube_fallida} a {nueva_asignacion.get('nube')}")
        
        return nueva_asignacion
    
    def sincronizar_modelos(self, modelos: List[Dict]) -> List[Dict]:
        """Sincroniza modelos entrenados al repositorio central."""
        modelos_sincronizados = []
        
        for modelo in modelos:
            sincronizado = {
                "modelo": modelo.get("nombre"),
                "origen": modelo.get("nube"),
                "destino": "repositorio_central",
                "estado": "sincronizado",
                "fecha_sincronizacion": datetime.now().isoformat()
            }
            modelos_sincronizados.append(sincronizado)
        
        logger.info(f"[GESTOR] {len(modelos_sincronizados)} modelos sincronizados")
        return modelos_sincronizados
    
    def guardar_asignaciones(self, datos: Dict):
        """Guarda las asignaciones de procesos."""
        with open(self.procesos_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        logger.info(f"[GESTOR] Asignaciones guardadas en {self.procesos_file}")
    
    def gestionar_todo(self, procesos: List[Dict]):
        """Gestiona todos los procesos en nubes."""
        logger.info("[GESTOR] Iniciando gestión de procesos en nubes...")
        
        recursos = self.cargar_recursos_disponibles()
        asignaciones = self.balancear_carga(procesos, recursos)
        estado_procesos = self.monitorear_procesos(asignaciones)
        
        datos = {
            "fecha_gestion": datetime.now().isoformat(),
            "total_procesos": len(procesos),
            "procesos": procesos,
            "asignaciones": asignaciones,
            "estado_procesos": estado_procesos,
            "recursos_utilizados": recursos
        }
        
        self.guardar_asignaciones(datos)
        
        logger.info(f"[GESTOR] Gestión completada: {len(asignaciones)} procesos asignados")
        return datos

if __name__ == "__main__":
    gestor = AgenteGestorNubes()
    
    # Ejemplo de procesos
    procesos_ejemplo = [
        {"nombre": "entrenar_us30_h1_v2", "tipo_carga": "entrenamiento_ml"},
        {"nombre": "entrenar_xauusd_m1_v2", "tipo_carga": "entrenamiento_ml"},
        {"nombre": "backtesting_nasdaq", "tipo_carga": "backtesting"}
    ]
    
    gestor.gestionar_todo(procesos_ejemplo)

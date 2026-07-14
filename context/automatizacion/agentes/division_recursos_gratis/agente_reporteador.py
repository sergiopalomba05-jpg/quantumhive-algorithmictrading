#!/usr/bin/env python3
"""
Agente Reporteador
==================
Genera informes de estado de recursos (disponibilidad, uso, caducidad).
Reporta progreso de procesos en cada nube.
Alerta sobre recursos próximos a caducar.
Consolida resultados de entrenamiento distribuido.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteReporteador:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / "automatizacion" / "agentes" / "division_recursos_gratis" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reportes_dir = self.output_dir / "reportes"
        self.reportes_dir.mkdir(exist_ok=True)
        
    def cargar_datos_centralizados(self) -> Dict:
        """Carga datos centralizados del administrador."""
        recursos_file = self.output_dir / "recursos_centralizados.json"
        if recursos_file.exists():
            with open(recursos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def cargar_datos_procesos(self) -> Dict:
        """Carga datos de procesos del gestor de nubes."""
        procesos_file = self.output_dir / "procesos_nubes.json"
        if procesos_file.exists():
            with open(procesos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def generar_reporte_recursos(self, datos: Dict) -> Dict:
        """Genera informe de estado de recursos."""
        recursos_centralizados = datos.get("recursos_centralizados", [])
        clasificacion_estado = datos.get("clasificacion_estado", {})
        clasificacion_prioridad = datos.get("clasificacion_prioridad", {})
        alertas = datos.get("alertas", [])
        
        reporte = {
            "tipo": "recursos",
            "fecha_generacion": datetime.now().isoformat(),
            "resumen": {
                "total_recursos": len(recursos_centralizados),
                "activos": len(clasificacion_estado.get("activos", [])),
                "caducados": len(clasificacion_estado.get("caducados", [])),
                "prioridad_alta": len(clasificacion_prioridad.get("alta", [])),
                "alertas": len(alertas)
            },
            "detalle_estado": clasificacion_estado,
            "detalle_prioridad": clasificacion_prioridad,
            "alertas": alertas
        }
        
        logger.info(f"[REPORTEADOR] Reporte de recursos generado: {reporte['resumen']}")
        return reporte
    
    def generar_reporte_procesos(self, datos: Dict) -> Dict:
        """Genera informe de progreso de procesos."""
        asignaciones = datos.get("asignaciones", [])
        estado_procesos = datos.get("estado_procesos", [])
        
        procesos_por_nube = {}
        for asignacion in asignaciones:
            nube = asignacion.get("nube")
            procesos_por_nube[nube] = procesos_por_nube.get(nube, 0) + 1
        
        reporte = {
            "tipo": "procesos",
            "fecha_generacion": datetime.now().isoformat(),
            "resumen": {
                "total_procesos": len(asignaciones),
                "ejecutando": len(estado_procesos),
                "nubes_utilizadas": len(procesos_por_nube)
            },
            "procesos_por_nube": procesos_por_nube,
            "estado_procesos": estado_procesos,
            "asignaciones": asignaciones
        }
        
        logger.info(f"[REPORTEADOR] Reporte de procesos generado: {reporte['resumen']}")
        return reporte
    
    def generar_reporte_alertas(self, datos: Dict) -> Dict:
        """Genera informe de alertas."""
        alertas = datos.get("alertas", [])
        
        reporte = {
            "tipo": "alertas",
            "fecha_generacion": datetime.now().isoformat(),
            "resumen": {
                "total_alertas": len(alertas),
                "alertas_criticas": 0
            },
            "alertas": alertas
        }
        
        # Clasificar alertas críticas
        for alerta in alertas:
            if "caducar" in alerta.get("mensaje", "").lower():
                reporte["resumen"]["alertas_criticas"] += 1
        
        logger.info(f"[REPORTEADOR] Reporte de alertas generado: {reporte['resumen']}")
        return reporte
    
    def generar_reporte_consolidado(self, datos_recursos: Dict, datos_procesos: Dict) -> Dict:
        """Genera informe consolidado de recursos y procesos."""
        reporte_recursos = self.generar_reporte_recursos(datos_recursos)
        reporte_procesos = self.generar_reporte_procesos(datos_procesos)
        reporte_alertas = self.generar_reporte_alertas(datos_recursos)
        
        reporte_consolidado = {
            "tipo": "consolidado",
            "fecha_generacion": datetime.now().isoformat(),
            "recursos": reporte_recursos,
            "procesos": reporte_procesos,
            "alertas": reporte_alertas
        }
        
        logger.info(f"[REPORTEADOR] Reporte consolidado generado")
        return reporte_consolidado
    
    def guardar_reporte(self, reporte: Dict, nombre_archivo: str):
        """Guarda un reporte en archivo."""
        archivo = self.reportes_dir / f"{nombre_archivo}.json"
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        logger.info(f"[REPORTEADOR] Reporte guardado: {archivo}")
    
    def generar_todos_los_reportes(self):
        """Genera todos los reportes disponibles."""
        logger.info("[REPORTEADOR] Iniciando generación de reportes...")
        
        datos_recursos = self.cargar_datos_centralizados()
        datos_procesos = self.cargar_datos_procesos()
        
        if not datos_recursos and not datos_procesos:
            logger.warning("[REPORTEADOR] No hay datos disponibles para generar reportes")
            return {}
        
        reportes = {}
        
        if datos_recursos:
            reportes["recursos"] = self.generar_reporte_recursos(datos_recursos)
            reportes["alertas"] = self.generar_reporte_alertas(datos_recursos)
        
        if datos_procesos:
            reportes["procesos"] = self.generar_reporte_procesos(datos_procesos)
        
        if datos_recursos and datos_procesos:
            reportes["consolidado"] = self.generar_reporte_consolidado(datos_recursos, datos_procesos)
        
        # Guardar reportes individuales
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        for tipo, reporte in reportes.items():
            self.guardar_reporte(reporte, f"reporte_{tipo}_{fecha}")
        
        logger.info(f"[REPORTEADOR] {len(reportes)} reportes generados y guardados")
        return reportes

if __name__ == "__main__":
    reporteador = AgenteReporteador()
    reporteador.generar_todos_los_reportes()

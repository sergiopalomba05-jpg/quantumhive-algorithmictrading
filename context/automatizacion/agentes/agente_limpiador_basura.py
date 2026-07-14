#!/usr/bin/env python3
"""
Agente Limpiador de Basura
==========================
Elimina datos basura de logs y archivos temporales.
Limpia archivos antiguos.
Optimiza almacenamiento.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import os
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteLimpiadorBasura:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reporte_file = self.output_dir / "reporte_limpieza.json"
        
    def limpiar_logs_antiguos(self, directorio_logs: str, dias: int = 7) -> Dict:
        """Limpia logs más antiguos que X días."""
        directorio = Path(directorio_logs)
        if not directorio.exists():
            return {"estado": "directorio_no_existe", "mensaje": f"Directorio {directorio} no existe"}
        
        fecha_limite = datetime.now() - timedelta(days=dias)
        archivos_eliminados = []
        espacio_liberado = 0
        
        for archivo in directorio.glob("*.log"):
            if archivo.stat().st_mtime < fecha_limite.timestamp():
                tamaño = archivo.stat().st_size
                archivo.unlink()
                archivos_eliminados.append(str(archivo))
                espacio_liberado += tamaño
        
        reporte = {
            "tipo": "limpieza_logs",
            "directorio": str(directorio),
            "dias_limite": dias,
            "archivos_eliminados": len(archivos_eliminados),
            "espacio_liberado_bytes": espacio_liberado,
            "espacio_liberado_mb": espacio_liberado / (1024 * 1024),
            "fecha_limpieza": datetime.now().isoformat()
        }
        
        logger.info(f"[LIMPIADOR] {len(archivos_eliminados)} logs eliminados, {reporte['espacio_liberado_mb']:.2f} MB liberados")
        return reporte
    
    def limpiar_archivos_temporales(self, directorio_temp: str) -> Dict:
        """Limpia archivos temporales."""
        directorio = Path(directorio_temp)
        if not directorio.exists():
            return {"estado": "directorio_no_existe", "mensaje": f"Directorio {directorio} no existe"}
        
        archivos_eliminados = []
        espacio_liberado = 0
        
        for archivo in directorio.glob("*"):
            if archivo.is_file():
                tamaño = archivo.stat().st_size
                archivo.unlink()
                archivos_eliminados.append(str(archivo))
                espacio_liberado += tamaño
        
        reporte = {
            "tipo": "limpieza_temporales",
            "directorio": str(directorio),
            "archivos_eliminados": len(archivos_eliminados),
            "espacio_liberado_bytes": espacio_liberado,
            "espacio_liberado_mb": espacio_liberado / (1024 * 1024),
            "fecha_limpieza": datetime.now().isoformat()
        }
        
        logger.info(f"[LIMPIADOR] {len(archivos_eliminados)} archivos temporales eliminados, {reporte['espacio_liberado_mb']:.2f} MB liberados")
        return reporte
    
    def limpiar_cache_pycache(self, directorio_base: str) -> Dict:
        """Limpia directorios __pycache__."""
        directorio = Path(directorio_base)
        if not directorio.exists():
            return {"estado": "directorio_no_existe", "mensaje": f"Directorio {directorio} no existe"}
        
        directorios_eliminados = []
        espacio_liberado = 0
        
        for pycache in directorio.rglob("__pycache__"):
            if pycache.is_dir():
                tamaño = sum(f.stat().st_size for f in pycache.rglob("*") if f.is_file())
                shutil.rmtree(pycache)
                directorios_eliminados.append(str(pycache))
                espacio_liberado += tamaño
        
        reporte = {
            "tipo": "limpieza_pycache",
            "directorio_base": str(directorio),
            "directorios_eliminados": len(directorios_eliminados),
            "espacio_liberado_bytes": espacio_liberado,
            "espacio_liberado_mb": espacio_liberado / (1024 * 1024),
            "fecha_limpieza": datetime.now().isoformat()
        }
        
        logger.info(f"[LIMPIADOR] {len(directorios_eliminados)} directorios __pycache__ eliminados, {reporte['espacio_liberado_mb']:.2f} MB liberados")
        return reporte
    
    def analizar_almacenamiento(self, directorio: str) -> Dict:
        """Analiza uso de almacenamiento de un directorio."""
        directorio_path = Path(directorio)
        if not directorio_path.exists():
            return {"estado": "directorio_no_existe", "mensaje": f"Directorio {directorio} no existe"}
        
        uso = {}
        total_size = 0
        
        for item in directorio_path.rglob("*"):
            if item.is_file():
                tamaño = item.stat().st_size
                extension = item.suffix
                uso[extension] = uso.get(extension, 0) + tamaño
                total_size += tamaño
        
        # Ordenar por tamaño
        uso_ordenado = sorted(uso.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "directorio": str(directorio),
            "tamaño_total_bytes": total_size,
            "tamaño_total_mb": total_size / (1024 * 1024),
            "uso_por_extension": dict(uso_ordenado),
            "fecha_analisis": datetime.now().isoformat()
        }
    
    def limpiar_todo(self, directorios: List[str]) -> Dict:
        """Ejecuta limpieza completa en múltiples directorios."""
        logger.info("[LIMPIADOR] Iniciando limpieza completa...")
        
        resultados = []
        total_espacio_liberado = 0
        
        for directorio in directorios:
            # Limpiar logs
            if "log" in directorio.lower():
                resultado = self.limpiar_logs_antiguos(directorio)
                resultados.append(resultado)
                total_espacio_liberado += resultado.get("espacio_liberado_bytes", 0)
            
            # Limpiar temporales
            elif "temp" in directorio.lower():
                resultado = self.limpiar_archivos_temporales(directorio)
                resultados.append(resultado)
                total_espacio_liberado += resultado.get("espacio_liberado_bytes", 0)
            
            # Limpiar pycache
            elif "agentes" in directorio.lower() or "nucleo" in directorio.lower():
                resultado = self.limpiar_cache_pycache(directorio)
                resultados.append(resultado)
                total_espacio_liberado += resultado.get("espacio_liberado_bytes", 0)
        
        reporte_completo = {
            "fecha_limpieza_completa": datetime.now().isoformat(),
            "resultados": resultados,
            "total_espacio_liberado_bytes": total_espacio_liberado,
            "total_espacio_liberado_mb": total_espacio_liberado / (1024 * 1024),
            "directorios_procesados": len(directorios)
        }
        
        self._guardar_reporte(reporte_completo)
        
        logger.info(f"[LIMPIADOR] Limpieza completada: {reporte_completo['total_espacio_liberado_mb']:.2f} MB liberados")
        return reporte_completo
    
    def _guardar_reporte(self, reporte: Dict):
        """Guarda reporte de limpieza."""
        with open(self.reporte_file, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        logger.info(f"[LIMPIADOR] Reporte guardado en {self.reporte_file}")

if __name__ == "__main__":
    limpiador = AgenteLimpiadorBasura()
    
    # Ejemplo de uso
    directorios = [
        "C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING/automatizacion/logs",
        "C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING/automatizacion/agentes",
        "C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING/nucleo"
    ]
    
    resultado = limpiador.limpiar_todo(directorios)
    print(json.dumps(resultado, indent=2))

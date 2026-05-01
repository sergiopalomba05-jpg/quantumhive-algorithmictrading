#!/usr/bin/env python3
"""
Agente de Informes de Logs
===========================
Genera informes de logs de todos los agentes.
Detecta patrones de errores recurrentes.
Alerta sobre problemas recurrentes.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging
import re
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteInformesLogs:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.informes_file = self.output_dir / "informes_logs.json"
        self.patrones_file = self.output_dir / "patrones_errores.json"
        
    def analizar_archivo_log(self, archivo_log: str) -> Dict:
        """Analiza un archivo de log específico."""
        archivo = Path(archivo_log)
        if not archivo.exists():
            return {"estado": "archivo_no_existe", "mensaje": f"Archivo {archivo} no existe"}
        
        errores = []
        warnings = []
        info = []
        
        with open(archivo, 'r', encoding='utf-8', errors='ignore') as f:
            for linea in f:
                if "ERROR" in linea.upper():
                    errores.append(linea.strip())
                elif "WARNING" in linea.upper():
                    warnings.append(linea.strip())
                elif "INFO" in linea.upper():
                    info.append(linea.strip())
        
        return {
            "archivo": str(archivo),
            "total_errores": len(errores),
            "total_warnings": len(warnings),
            "total_info": len(info),
            "errores": errores[:10],  # Primeros 10 errores
            "warnings": warnings[:10],  # Primeros 10 warnings
            "fecha_analisis": datetime.now().isoformat()
        }
    
    def detectar_patrones_errores(self, logs: List[Dict]) -> Dict:
        """Detecta patrones de errores recurrentes."""
        todos_errores = []
        
        for log in logs:
            todos_errores.extend(log.get("errores", []))
        
        # Extraer mensajes de error
        mensajes_error = []
        for error in todos_errores:
            # Intentar extraer el mensaje de error
            match = re.search(r'ERROR[:\s]+(.+)', error, re.IGNORECASE)
            if match:
                mensajes_error.append(match.group(1).strip())
        
        # Contar frecuencias
        contador = Counter(mensajes_error)
        
        patrones = []
        for mensaje, frecuencia in contador.most_common(10):
            if frecuencia > 1:
                patrones.append({
                    "mensaje": mensaje,
                    "frecuencia": frecuencia,
                    "tipo": "recurrente" if frecuencia > 3 else "ocasional"
                })
        
        return {
            "patrones_detectados": patrones,
            "total_patrones": len(patrones),
            "fecha_deteccion": datetime.now().isoformat()
        }
    
    def detectar_tareas_estorbo(self, logs: List[Dict]) -> Dict:
        """Detecta tareas que se estorban entre sí."""
        # Buscar patrones de timeout, bloqueo, espera
        patrones_estorbo = []
        
        for log in logs:
            errores = log.get("errores", [])
            for error in errores:
                if "timeout" in error.lower() or "blocked" in error.lower() or "waiting" in error.lower():
                    patrones_estorbo.append({
                        "error": error[:100],
                        "archivo": log.get("archivo"),
                        "tipo": "timeout" if "timeout" in error.lower() else "bloqueo" if "blocked" in error.lower() else "espera"
                    })
        
        return {
            "patrones_estorbo": patrones_estorbo,
            "total_estorbos": len(patrones_estorbo),
            "fecha_deteccion": datetime.now().isoformat()
        }
    
    def generar_informe_completo(self, directorio_logs: str) -> Dict:
        """Genera informe completo de todos los logs."""
        directorio = Path(directorio_logs)
        if not directorio.exists():
            return {"estado": "directorio_no_existe", "mensaje": f"Directorio {directorio} no existe"}
        
        logs_analizados = []
        
        for archivo_log in directorio.glob("*.log"):
            analisis = self.analizar_archivo_log(str(archivo_log))
            logs_analizados.append(analisis)
        
        patrones = self.detectar_patrones_errores(logs_analizados)
        estorbos = self.detectar_tareas_estorbo(logs_analizados)
        
        informe = {
            "fecha_informe": datetime.now().isoformat(),
            "directorio": str(directorio),
            "total_archivos_analizados": len(logs_analizados),
            "total_errores": sum(l.get("total_errores", 0) for l in logs_analizados),
            "total_warnings": sum(l.get("total_warnings", 0) for l in logs_analizados),
            "logs_analizados": logs_analizados,
            "patrones_errores": patrones,
            "tareas_estorbo": estorbos,
            "recomendaciones": self._generar_recomendaciones(patrones, estorbos)
        }
        
        self._guardar_informe(informe)
        
        logger.info(f"[INFORMES] Informe generado: {len(logs_analizados)} archivos, {informe['total_errores']} errores")
        return informe
    
    def _generar_recomendaciones(self, patrones: Dict, estorbos: Dict) -> List[str]:
        """Genera recomendaciones basadas en patrones detectados."""
        recomendaciones = []
        
        if len(patrones.get("patrones_detectados", [])) > 0:
            recomendaciones.append("Hay errores recurrentes que requieren atención inmediata")
        
        if len(estorbos.get("patrones_estorbo", [])) > 0:
            recomendaciones.append("Se detectaron tareas que se estorban entre sí, revisar concurrencia")
        
        if len(recomendaciones) == 0:
            recomendaciones.append("No se detectaron problemas graves, sistema operativo normalmente")
        
        return recomendaciones
    
    def _guardar_informe(self, informe: Dict):
        """Guarda informe de logs."""
        with open(self.informes_file, 'w', encoding='utf-8') as f:
            json.dump(informe, f, indent=2, ensure_ascii=False)
        logger.info(f"[INFORMES] Informe guardado en {self.informes_file}")
    
    def obtener_ultimo_informe(self) -> Dict:
        """Obtiene el último informe generado."""
        if not self.informes_file.exists():
            return {"estado": "no_hay_informe", "mensaje": "No hay informes generados"}
        
        with open(self.informes_file, 'r', encoding='utf-8') as f:
            return json.load(f)

if __name__ == "__main__":
    informes = AgenteInformesLogs()
    
    # Ejemplo de uso
    directorio_logs = "C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING/automatizacion/logs"
    resultado = informes.generar_informe_completo(directorio_logs)
    print(json.dumps(resultado, indent=2))

#!/usr/bin/env python3
"""
Agente Optimizador de Procesos
===============================
Detecta ineficiencias en agentes y procesos.
Optimiza flujos de trabajo.
Sugiere mejoras para aumentar eficiencia.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging
import psutil
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteOptimizadorProcesos:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mejoras_file = self.output_dir / "mejoras_propuestas.json"
        self.evaluaciones_file = self.output_dir / "evaluaciones_rendimiento.json"
        
    def analizar_rendimiento_agente(self, nombre_agente: str) -> Dict:
        """Analiza rendimiento de un agente específico."""
        try:
            proceso = None
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if nombre_agente.lower() in proc.info['name'].lower():
                    proceso = proc
                    break
            
            if not proceso:
                return {
                    "agente": nombre_agente,
                    "estado": "no_encontrado",
                    "mensaje": "Agente no está corriendo actualmente"
                }
            
            cpu = proceso.cpu_percent(interval=1)
            memoria = proceso.memory_percent()
            
            # Evaluar rendimiento
            rendimiento = "optimo"
            if cpu > 80:
                rendimiento = "alto_cpu"
            elif memoria > 80:
                rendimiento = "alta_memoria"
            elif cpu > 50 or memoria > 50:
                rendimiento = "medio"
            
            return {
                "agente": nombre_agente,
                "pid": proceso.pid,
                "cpu_percent": cpu,
                "memory_percent": memoria,
                "rendimiento": rendimiento,
                "fecha_analisis": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[OPTIMIZADOR] Error analizando {nombre_agente}: {e}")
            return {
                "agente": nombre_agente,
                "estado": "error",
                "mensaje": str(e)
            }
    
    def detectar_ineficiencias(self, agentes: List[str]) -> List[Dict]:
        """Detecta ineficiencias en múltiples agentes."""
        ineficiencias = []
        
        for agente in agentes:
            resultado = self.analizar_rendimiento_agente(agente)
            
            if resultado.get("rendimiento") in ["alto_cpu", "alta_memoria"]:
                ineficiencias.append({
                    "agente": agente,
                    "tipo": resultado["rendimiento"],
                    "valor": resultado.get("cpu_percent") if resultado["rendimiento"] == "alto_cpu" else resultado.get("memory_percent"),
                    "recomendacion": self._generar_recomendacion(resultado),
                    "fecha": datetime.now().isoformat()
                })
        
        logger.info(f"[OPTIMIZADOR] {len(ineficiencias)} ineficiencias detectadas")
        return ineficiencias
    
    def _generar_recomendacion(self, resultado: Dict) -> str:
        """Genera recomendación basada en el resultado."""
        if resultado["rendimiento"] == "alto_cpu":
            return "Considerar optimizar código o distribuir carga en múltiples procesos"
        elif resultado["rendimiento"] == "alta_memoria":
            return "Considerar optimizar uso de memoria o aumentar recursos disponibles"
        else:
            return "Monitorear rendimiento para detectar patrones"
    
    def proponer_mejora(self, agente: str, tipo_mejora: str, descripcion: str, 
                        impacto_esperado: str) -> Dict:
        """Propone una mejora para un agente."""
        mejora = {
            "id": int(datetime.now().timestamp()),
            "agente": agente,
            "tipo_mejora": tipo_mejora,
            "descripcion": descripcion,
            "impacto_esperado": impacto_esperado,
            "estado": "pendiente_aprobacion",
            "fecha_propuesta": datetime.now().isoformat(),
            "propuesto_por": "Agente Optimizador"
        }
        
        # Guardar en archivo
        self._guardar_mejora(mejora)
        
        logger.info(f"[OPTIMIZADOR] Mejora propuesta para {agente}: {tipo_mejora}")
        return mejora
    
    def _guardar_mejora(self, mejora: Dict):
        """Guarda una mejora propuesta."""
        mejoras = []
        if self.mejoras_file.exists():
            with open(self.mejoras_file, 'r', encoding='utf-8') as f:
                mejoras = json.load(f)
        
        mejoras.append(mejora)
        
        with open(self.mejoras_file, 'w', encoding='utf-8') as f:
            json.dump(mejoras, f, indent=2, ensure_ascii=False)
    
    def obtener_mejoras_pendientes(self) -> List[Dict]:
        """Obtiene mejoras pendientes de aprobación."""
        if not self.mejoras_file.exists():
            return []
        
        with open(self.mejoras_file, 'r', encoding='utf-8') as f:
            mejoras = json.load(f)
        
        return [m for m in mejoras if m["estado"] == "pendiente_aprobacion"]
    
    def evaluar_flujo_trabajo(self, flujo: List[str]) -> Dict:
        """Evalúa eficiencia de un flujo de trabajo."""
        tiempos = []
        
        for paso in flujo:
            inicio = time.time()
            # Simular ejecución del paso
            time.sleep(0.1)
            fin = time.time()
            tiempos.append({
                "paso": paso,
                "tiempo": fin - inicio
            })
        
        tiempo_total = sum(t["tiempo"] for t in tiempos)
        promedio = tiempo_total / len(tiempos)
        
        return {
            "flujo": flujo,
            "tiempos_por_paso": tiempos,
            "tiempo_total": tiempo_total,
            "tiempo_promedio": promedio,
            "evaluacion": self._evaluar_eficiencia(promedio),
            "fecha_evaluacion": datetime.now().isoformat()
        }
    
    def _evaluar_eficiencia(self, tiempo_promedio: float) -> str:
        """Evalúa eficiencia basada en tiempo promedio."""
        if tiempo_promedio < 0.5:
            return "alta_eficiencia"
        elif tiempo_promedio < 1.0:
            return "media_eficiencia"
        else:
            return "baja_eficiencia"
    
    def optimizar_todo(self, agentes: List[str]):
        """Ejecuta optimización completa."""
        logger.info("[OPTIMIZADOR] Iniciando optimización completa...")
        
        ineficiencias = self.detectar_ineficiencias(agentes)
        mejoras_pendientes = self.obtener_mejoras_pendientes()
        
        resultado = {
            "fecha_optimizacion": datetime.now().isoformat(),
            "ineficiencias_detectadas": ineficiencias,
            "mejoras_pendientes": mejoras_pendientes,
            "total_ineficiencias": len(ineficiencias),
            "total_mejoras_pendientes": len(mejoras_pendientes)
        }
        
        logger.info(f"[OPTIMIZADOR] Optimización completada: {len(ineficiencias)} ineficiencias, {len(mejoras_pendientes)} mejoras pendientes")
        return resultado

if __name__ == "__main__":
    optimizador = AgenteOptimizadorProcesos()
    
    # Ejemplo de uso
    agentes = ["python", "node"]
    resultado = optimizador.optimizar_todo(agentes)
    print(json.dumps(resultado, indent=2))

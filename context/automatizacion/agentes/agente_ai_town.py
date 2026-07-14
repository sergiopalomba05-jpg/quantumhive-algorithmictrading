#!/usr/bin/env python3
"""
Agente AI Town
==============
Detecta errores en el proyecto AI Town.
Clona AI Town desde GitHub.
Integra archivos creados en quantum_bridge.
Configura Convex.
Ejecuta el proyecto para visualizar el mundo virtual.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging
import subprocess
import shutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteAITown:
    def __init__(self):
        self.quantumhive_dir = Path(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING")
        self.cascade_projects_dir = Path(r"C:\Users\sergio\CascadeProjects")
        self.quantum_bridge_dir = self.quantumhive_dir / "quantum_bridge"
        self.ai_town_dir = self.cascade_projects_dir / "quantumhive-town"
        self.reporte_file = self.quantumhive_dir / "automatizacion" / "agentes" / "data" / "reporte_ai_town.json"
        
    def detectar_estado_actual(self) -> Dict:
        """Detecta el estado actual del proyecto AI Town."""
        logger.info("[AI TOWN] Detectando estado actual...")
        
        estado = {
            "quantum_bridge_existe": self.quantum_bridge_dir.exists(),
            "ai_town_clonado": self.ai_town_dir.exists(),
            "archivos_creados": [],
            "archivos_integrados": [],
            "convex_configurado": False,
            "proyecto_ejecutandose": False,
            "errores": [],
            "fecha_analisis": datetime.now().isoformat()
        }
        
        # Verificar archivos creados en quantum_bridge
        if estado["quantum_bridge_existe"]:
            archivos_esperados = [
                "convex/quantumBridge.ts",
                "convex/agentAnimation.ts",
                "convex/mapGenerator.ts",
                "convex/businessRules.ts",
                "components/QuantumCanvas.tsx",
                "package.json",
                "vercel.json"
            ]
            
            for archivo in archivos_esperados:
                ruta = self.quantum_bridge_dir / archivo
                if ruta.exists():
                    estado["archivos_creados"].append(archivo)
        
        # Verificar si AI Town está clonado
        if estado["ai_town_clonado"]:
            # Verificar archivos integrados
            for archivo in archivos_esperados:
                ruta = self.ai_town_dir / archivo
                if ruta.exists():
                    estado["archivos_integrados"].append(archivo)
        
        # Detectar errores
        if not estado["quantum_bridge_existe"]:
            estado["errores"].append("quantum_bridge NO existe")
        
        if not estado["ai_town_clonado"]:
            estado["errores"].append("AI Town NO está clonado")
        
        if len(estado["archivos_integrados"]) < len(estado["archivos_creados"]):
            estado["errores"].append(f"Solo {len(estado['archivos_integrados'])}/{len(estado['archivos_creados'])} archivos integrados")
        
        # Verificar si Convex está configurado
        if estado["ai_town_clonado"]:
            convex_dir = self.ai_town_dir / "convex"
            if convex_dir.exists():
                # Buscar archivos .convex o configuración
                for archivo in convex_dir.glob("*"):
                    if "convex" in archivo.name.lower():
                        estado["convex_configurado"] = True
                        break
        
        logger.info(f"[AI TOWN] Estado detectado: {len(estado['errores'])} errores")
        return estado
    
    def clonar_ai_town(self) -> Dict:
        """Clona AI Town desde GitHub."""
        logger.info("[AI TOWN] Clonando AI Town desde GitHub...")
        
        try:
            if self.ai_town_dir.exists():
                logger.warning(f"[AI TOWN] Directorio {self.ai_town_dir} ya existe, eliminando...")
                shutil.rmtree(self.ai_town_dir)
            
            # Crear directorio CascadeProjects si no existe
            self.cascade_projects_dir.mkdir(parents=True, exist_ok=True)
            
            # Clonar AI Town
            cmd = [
                "git",
                "clone",
                "https://github.com/a16z-infra/ai-town.git",
                str(self.ai_town_dir)
            ]
            
            resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if resultado.returncode == 0:
                logger.info(f"[AI TOWN] AI Town clonado exitosamente en {self.ai_town_dir}")
                return {
                    "estado": "exitoso",
                    "mensaje": "AI Town clonado exitosamente",
                    "directorio": str(self.ai_town_dir)
                }
            else:
                logger.error(f"[AI TOWN] Error clonando AI Town: {resultado.stderr}")
                return {
                    "estado": "error",
                    "mensaje": "Error clonando AI Town",
                    "error": resultado.stderr
                }
        except Exception as e:
            logger.error(f"[AI TOWN] Excepción clonando AI Town: {e}")
            return {
                "estado": "error",
                "mensaje": "Excepción clonando AI Town",
                "error": str(e)
            }
    
    def integrar_archivos(self) -> Dict:
        """Integra archivos creados en quantum_bridge a AI Town."""
        logger.info("[AI TOWN] Integrando archivos en AI Town...")
        
        if not self.ai_town_dir.exists():
            return {
                "estado": "error",
                "mensaje": "AI Town no está clonado"
            }
        
        archivos_a_copiar = [
            ("convex/quantumBridge.ts", "convex/quantumBridge.ts"),
            ("convex/agentAnimation.ts", "convex/agentAnimation.ts"),
            ("convex/mapGenerator.ts", "convex/mapGenerator.ts"),
            ("convex/businessRules.ts", "convex/businessRules.ts"),
            ("components/QuantumCanvas.tsx", "components/QuantumCanvas.tsx"),
            ("package.json", "package.json"),
            ("vercel.json", "vercel.json")
        ]
        
        archivos_copiados = []
        errores = []
        
        for origen, destino in archivos_a_copiar:
            ruta_origen = self.quantum_bridge_dir / origen
            ruta_destino = self.ai_town_dir / destino
            
            try:
                # Crear directorios si no existen
                ruta_destino.parent.mkdir(parents=True, exist_ok=True)
                
                # Copiar archivo
                if ruta_origen.exists():
                    shutil.copy2(ruta_origen, ruta_destino)
                    archivos_copiados.append(destino)
                    logger.info(f"[AI TOWN] Copiado: {origen} -> {destino}")
                else:
                    error_msg = f"Archivo origen no existe: {origen}"
                    errores.append(error_msg)
                    logger.warning(f"[AI TOWN] {error_msg}")
            except Exception as e:
                error_msg = f"Error copiando {origen}: {e}"
                errores.append(error_msg)
                logger.error(f"[AI TOWN] {error_msg}")
        
        # Copiar quantum_hierarchy.json a la raíz
        json_origen = self.quantumhive_dir / "quantum_hierarchy.json"
        json_destino = self.ai_town_dir / "quantum_hierarchy.json"
        
        if json_origen.exists():
            try:
                shutil.copy2(json_origen, json_destino)
                archivos_copiados.append("quantum_hierarchy.json")
                logger.info(f"[AI TOWN] Copiado: quantum_hierarchy.json")
            except Exception as e:
                error_msg = f"Error copiando quantum_hierarchy.json: {e}"
                errores.append(error_msg)
                logger.error(f"[AI TOWN] {error_msg}")
        
        return {
            "estado": "exitoso" if len(errores) == 0 else "parcial",
            "archivos_copiados": archivos_copiados,
            "total_copiados": len(archivos_copiados),
            "errores": errores
        }
    
    def instalar_dependencias(self) -> Dict:
        """Instala dependencias de npm en AI Town."""
        logger.info("[AI TOWN] Instalando dependencias...")
        
        if not self.ai_town_dir.exists():
            return {
                "estado": "error",
                "mensaje": "AI Town no está clonado"
            }
        
        try:
            # Instalar dependencias
            cmd = ["npm", "install"]
            resultado = subprocess.run(
                cmd,
                cwd=str(self.ai_town_dir),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if resultado.returncode == 0:
                logger.info("[AI TOWN] Dependencias instaladas exitosamente")
                
                # Instalar dependencia adicional
                cmd_extra = ["npm", "install", "@use-gesture/react"]
                resultado_extra = subprocess.run(
                    cmd_extra,
                    cwd=str(self.ai_town_dir),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                return {
                    "estado": "exitoso",
                    "mensaje": "Dependencias instaladas exitosamente"
                }
            else:
                logger.error(f"[AI TOWN] Error instalando dependencias: {resultado.stderr}")
                return {
                    "estado": "error",
                    "mensaje": "Error instalando dependencias",
                    "error": resultado.stderr
                }
        except Exception as e:
            logger.error(f"[AI TOWN] Excepción instalando dependencias: {e}")
            return {
                "estado": "error",
                "mensaje": "Excepción instalando dependencias",
                "error": str(e)
            }
    
    def configurar_convex(self) -> Dict:
        """Configura Convex para AI Town."""
        logger.info("[AI TOWN] Configurando Convex...")
        
        if not self.ai_town_dir.exists():
            return {
                "estado": "error",
                "mensaje": "AI Town no está clonado"
            }
        
        try:
            # Ejecutar npx convex dev
            cmd = ["npx", "convex", "dev"]
            
            # Nota: Esto requerirá interacción del usuario para crear proyecto en Convex
            logger.warning("[AI TOWN] La configuración de Convex requiere interacción manual")
            logger.warning("[AI TOWN] Ejecuta: cd " + str(self.ai_town_dir) + " && npx convex dev")
            
            return {
                "estado": "requiere_interaccion_manual",
                "mensaje": "Configuración de Convex requiere interacción manual",
                "comando": f"cd {self.ai_town_dir} && npx convex dev"
            }
        except Exception as e:
            logger.error(f"[AI TOWN] Excepción configurando Convex: {e}")
            return {
                "estado": "error",
                "mensaje": "Excepción configurando Convex",
                "error": str(e)
            }
    
    def ejecutar_proyecto(self) -> Dict:
        """Ejecuta el proyecto AI Town."""
        logger.info("[AI TOWN] Ejecutando proyecto AI Town...")
        
        if not self.ai_town_dir.exists():
            return {
                "estado": "error",
                "mensaje": "AI Town no está clonado"
            }
        
        try:
            # Ejecutar npm run dev
            cmd = ["npm", "run", "dev"]
            
            logger.warning("[AI TOWN] Ejecutando proyecto en background...")
            logger.warning(f"[AI TOWN] Comando: cd {self.ai_town_dir} && npm run dev")
            
            return {
                "estado": "requiere_ejecucion_manual",
                "mensaje": "Proyecto requiere ejecución manual",
                "comando": f"cd {self.ai_town_dir} && npm run dev",
                "url": "http://localhost:3000"
            }
        except Exception as e:
            logger.error(f"[AI TOWN] Excepción ejecutando proyecto: {e}")
            return {
                "estado": "error",
                "mensaje": "Excepción ejecutando proyecto",
                "error": str(e)
            }
    
    def generar_reporte_completo(self) -> Dict:
        """Genera reporte completo del estado y acciones necesarias."""
        logger.info("[AI TOWN] Generando reporte completo...")
        
        estado = self.detectar_estado_actual()
        acciones = []
        
        if not estado["ai_town_clonado"]:
            acciones.append({
                "accion": "clonar_ai_town",
                "descripcion": "Clonar AI Town desde GitHub",
                "prioridad": "ALTA",
                "estado": "pendiente"
            })
        
        if len(estado["archivos_integrados"]) < len(estado["archivos_creados"]):
            acciones.append({
                "accion": "integrar_archivos",
                "descripcion": "Integrar archivos creados en AI Town",
                "prioridad": "ALTA",
                "estado": "pendiente"
            })
        
        if not estado["convex_configurado"]:
            acciones.append({
                "accion": "configurar_convex",
                "descripcion": "Configurar Convex (requiere interacción manual)",
                "prioridad": "ALTA",
                "estado": "pendiente"
            })
        
        acciones.append({
            "accion": "instalar_dependencias",
            "descripcion": "Instalar dependencias npm",
            "prioridad": "MEDIA",
            "estado": "pendiente"
        })
        
        acciones.append({
            "accion": "ejecutar_proyecto",
            "descripcion": "Ejecutar proyecto AI Town",
            "prioridad": "MEDIA",
            "estado": "pendiente"
        })
        
        reporte = {
            "fecha_reporte": datetime.now().isoformat(),
            "estado_actual": estado,
            "acciones_necesarias": acciones,
            "total_acciones": len(acciones),
            "resumen": {
                "errores_detectados": len(estado["errores"]),
                "archivos_creados": len(estado["archivos_creados"]),
                "archivos_integrados": len(estado["archivos_integrados"]),
                "ai_town_clonado": estado["ai_town_clonado"],
                "convex_configurado": estado["convex_configurado"]
            }
        }
        
        # Guardar reporte
        self.reporte_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.reporte_file, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[AI TOWN] Reporte guardado en {self.reporte_file}")
        return reporte
    
    def ejecutar_reparacion_completa(self) -> Dict:
        """Ejecuta reparación completa automática."""
        logger.info("[AI TOWN] Iniciando reparación completa...")
        
        resultados = []
        
        # Paso 1: Clonar AI Town
        if not self.ai_town_dir.exists():
            resultado_clonar = self.clonar_ai_town()
            resultados.append(resultado_clonar)
            if resultado_clonar["estado"] != "exitoso":
                return {
                    "estado": "error",
                    "mensaje": "Error clonando AI Town",
                    "resultados": resultados
                }
        
        # Paso 2: Integrar archivos
        resultado_integrar = self.integrar_archivos()
        resultados.append(resultado_integrar)
        
        # Paso 3: Instalar dependencias
        resultado_dependencias = self.instalar_dependencias()
        resultados.append(resultado_dependencias)
        
        # Paso 4: Configurar Convex (requiere interacción manual)
        resultado_convex = self.configurar_convex()
        resultados.append(resultado_convex)
        
        # Paso 5: Ejecutar proyecto (requiere ejecución manual)
        resultado_ejecutar = self.ejecutar_proyecto()
        resultados.append(resultado_ejecutar)
        
        return {
            "estado": "completado_con_acciones_manuales",
            "mensaje": "Reparación completada. Algunos pasos requieren acción manual.",
            "resultados": resultados,
            "proximos_pasos": [
                f"cd {self.ai_town_dir}",
                "npx convex dev",
                "npm run dev",
                "Abrir http://localhost:3000"
            ]
        }

if __name__ == "__main__":
    agente = AgenteAITown()
    
    # Generar reporte completo
    reporte = agente.generar_reporte_completo()
    print(json.dumps(reporte, indent=2))
    
    # Ejecutar reparación automáticamente
    print("\nEjecutando reparación completa...")
    resultado = agente.ejecutar_reparacion_completa()
    print(json.dumps(resultado, indent=2))

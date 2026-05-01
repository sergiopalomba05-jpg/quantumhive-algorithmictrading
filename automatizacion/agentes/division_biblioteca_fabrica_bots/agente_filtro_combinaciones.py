#!/usr/bin/env python3
"""
Agente Filtro de Combinaciones
===============================
Detecta combinaciones de modelos ONNX que ya fueron probadas y erróneas.
Evita repetir backtesting de combinaciones fallidas.
Solo backtestea NUEVAS modificaciones sobre modelos rentables.
Protege modelos rentables originales (no se modifican, solo se crean clones).
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteFiltroCombinaciones:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "automatizacion" / "agentes" / "division_biblioteca_fabrica_bots" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.historial_file = self.output_dir / "historial_combinaciones.json"
        self.modelos_rentables_file = self.output_dir / "modelos_rentables_protegidos.json"
        
        # Cargar historial
        self.historial = self._cargar_historial()
        self.modelos_rentables = self._cargar_modelos_rentables()
        
    def _cargar_historial(self) -> Dict:
        """Carga historial de combinaciones probadas."""
        if self.historial_file.exists():
            with open(self.historial_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "combinaciones_erroneas": [],
            "combinaciones_exitosas": [],
            "clones_creados": []
        }
    
    def _cargar_modelos_rentables(self) -> Dict:
        """Carga modelos rentables protegidos."""
        if self.modelos_rentables_file.exists():
            with open(self.modelos_rentables_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _generar_hash_combinacion(self, config: Dict) -> str:
        """Genera hash único de una combinación de configuración."""
        # Ordenar diccionario para consistencia
        config_ordenado = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_ordenado.encode()).hexdigest()
    
    def _combinacion_ya_probada(self, hash_combinacion: str) -> Dict:
        """Verifica si una combinación ya fue probada."""
        # Buscar en combinaciones erróneas
        for comb in self.historial["combinaciones_erroneas"]:
            if comb["hash"] == hash_combinacion:
                return {"estado": "erronea", "resultado": comb}
        
        # Buscar en combinaciones exitosas
        for comb in self.historial["combinaciones_exitosas"]:
            if comb["hash"] == hash_combinacion:
                return {"estado": "exitosa", "resultado": comb}
        
        return {"estado": "no_probada"}
    
    def _obtener_diferencias_config(self, config_base: Dict, config_nueva: Dict) -> Dict:
        """Obtiene diferencias entre configuraciones."""
        diferencias = {}
        
        for key, value_nueva in config_nueva.items():
            if key not in config_base:
                diferencias[key] = {"tipo": "nuevo", "valor": value_nueva}
            elif config_base[key] != value_nueva:
                diferencias[key] = {
                    "tipo": "modificado",
                    "valor_anterior": config_base[key],
                    "valor_nuevo": value_nueva
                }
        
        return diferencias
    
    def registrar_modelo_rentable(self, nombre_bot: str, activo: str, temporalidad: str, config: Dict, ruta_modelo: str):
        """Registra un modelo rentable como protegido."""
        hash_config = self._generar_hash_combinacion(config)
        
        modelo_rentable = {
            "nombre": nombre_bot,
            "activo": activo,
            "temporalidad": temporalidad,
            "config": config,
            "hash_config": hash_config,
            "ruta_modelo": ruta_modelo,
            "fecha_registro": datetime.now().isoformat(),
            "estado": "protegido"
        }
        
        self.modelos_rentables[nombre_bot] = modelo_rentable
        self._guardar_modelos_rentables()
        
        logger.info(f"[FILTRO] Modelo rentable registrado y protegido: {nombre_bot}")
        return modelo_rentable
    
    def crear_clon_modelo(self, modelo_base: str, config_modificada: Dict, nombre_clon: str) -> Dict:
        """Crea un clon de un modelo rentable con modificaciones."""
        if modelo_base not in self.modelos_rentables:
            logger.error(f"[FILTRO] Modelo base no encontrado: {modelo_base}")
            return {"estado": "error", "mensaje": "Modelo base no encontrado"}
        
        modelo_rentable = self.modelos_rentables[modelo_base]
        config_base = modelo_rentable["config"]
        
        # Obtener diferencias
        diferencias = self._obtener_diferencias_config(config_base, config_modificada)
        
        # Generar hash de la configuración completa del clon
        hash_clon = self._generar_hash_combinacion(config_modificada)
        
        # Verificar si esta combinación ya fue probada
        estado_previo = self._combinacion_ya_probada(hash_clon)
        if estado_previo["estado"] == "erronea":
            logger.warning(f"[FILTRO] Combinación ya probada y errónea: {hash_clon}")
            return {
                "estado": "ya_probada_erronea",
                "mensaje": "Esta combinación ya fue probada y falló anteriormente",
                "resultado_previo": estado_previo["resultado"]
            }
        
        # Crear clon
        clon = {
            "nombre": nombre_clon,
            "modelo_base": modelo_base,
            "activo": modelo_rentable["activo"],
            "temporalidad": modelo_rentable["temporalidad"],
            "config_base": config_base,
            "config_modificada": config_modificada,
            "diferencias": diferencias,
            "hash_config": hash_clon,
            "fecha_creacion": datetime.now().isoformat(),
            "estado": "pendiente_backtesting"
        }
        
        # Registrar en historial
        self.historial["clones_creados"].append(clon)
        self._guardar_historial()
        
        logger.info(f"[FILTRO] Clon creado: {nombre_clon} basado en {modelo_base}")
        logger.info(f"[FILTRO] Diferencias: {len(diferencias)} modificaciones")
        
        return clon
    
    def obtener_diferencias_para_backtesting(self, nombre_clon: str) -> Dict:
        """Obtiene solo las diferencias que necesitan backtesting."""
        for clon in self.historial["clones_creados"]:
            if clon["nombre"] == nombre_clon:
                return {
                    "nombre_clon": nombre_clon,
                    "modelo_base": clon["modelo_base"],
                    "diferencias": clon["diferencias"],
                    "config_modificada": clon["config_modificada"],
                    "backtesting_solo_diferencias": True
                }
        
        return {"estado": "error", "mensaje": "Clon no encontrado"}
    
    def registrar_resultado_backtesting(self, nombre_clon: str, resultado: Dict):
        """Registra resultado de backtesting de un clon."""
        # Buscar clon
        clon_encontrado = None
        for clon in self.historial["clones_creados"]:
            if clon["nombre"] == nombre_clon:
                clon_encontrado = clon
                break
        
        if not clon_encontrado:
            logger.error(f"[FILTRO] Clon no encontrado: {nombre_clon}")
            return
        
        # Actualizar estado del clon
        clon_encontrado["resultado_backtesting"] = resultado
        clon_encontrado["fecha_resultado"] = datetime.now().isoformat()
        
        # Determinar si es exitoso o erróneo
        es_rentable = resultado.get("pnl_total", 0) > 1000 and resultado.get("profit_factor", 0) > 1.1
        
        if es_rentable:
            clon_encontrado["estado"] = "rentable"
            self.historial["combinaciones_exitosas"].append({
                "hash": clon_encontrado["hash_config"],
                "nombre": nombre_clon,
                "modelo_base": clon_encontrado["modelo_base"],
                "resultado": resultado,
                "fecha": datetime.now().isoformat()
            })
            logger.info(f"[FILTRO] Clon rentable: {nombre_clon}")
        else:
            clon_encontrado["estado"] = "no_rentable"
            self.historial["combinaciones_erroneas"].append({
                "hash": clon_encontrado["hash_config"],
                "nombre": nombre_clon,
                "modelo_base": clon_encontrado["modelo_base"],
                "resultado": resultado,
                "fecha": datetime.now().isoformat()
            })
            logger.info(f"[FILTRO] Clon no rentable: {nombre_clon}")
        
        self._guardar_historial()
    
    def obtener_modelos_rentables(self) -> List[Dict]:
        """Obtiene lista de modelos rentables protegidos."""
        return list(self.modelos_rentables.values())
    
    def obtener_combinaciones_erroneas(self) -> List[Dict]:
        """Obtiene lista de combinaciones erróneas para evitar repetir."""
        return self.historial["combinaciones_erroneas"]
    
    def _guardar_historial(self):
        """Guarda historial de combinaciones."""
        with open(self.historial_file, 'w', encoding='utf-8') as f:
            json.dump(self.historial, f, indent=2, ensure_ascii=False)
    
    def _guardar_modelos_rentables(self):
        """Guarda modelos rentables protegidos."""
        with open(self.modelos_rentables_file, 'w', encoding='utf-8') as f:
            json.dump(self.modelos_rentables, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    filtro = AgenteFiltroCombinaciones()
    
    # Ejemplo de uso
    config_atlas = {
        "bb_periodo": 30,
        "bb_desv": 2.5,
        "rsi_periodo": 7,
        "rsi_rev_long_max": 25.0,
        "rsi_rev_short_min": 75.0,
        "atr_sl_mult": 0.8
    }
    
    # Registrar modelo rentable
    filtro.registrar_modelo_rentable(
        "Atlas", "XAUUSD", "M5", config_atlas, 
        "modelos/xauusd_m5_atlas.zip"
    )
    
    # Crear clon con modificación
    config_modificada = config_atlas.copy()
    config_modificada["rsi_periodo"] = 5  # Modificación
    
    clon = filtro.crear_clon_modelo("Atlas", config_modificada, "Atlas_Clone_V1")
    print(f"Clon creado: {clon}")

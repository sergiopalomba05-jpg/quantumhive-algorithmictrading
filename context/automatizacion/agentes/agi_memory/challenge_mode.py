#!/usr/bin/env python3
"""
Challenge Mode — AGI UPGRADE v2.0
Permite que AGI cuestione decisiones de Sergio con datos.
Activable por Sergio cuando desea un debate informado.
"""

import json
from typing import Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChallengeMode:
    def __init__(self):
        self.activo = False
        self.contexto_qh_path = Path(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\automatizacion\agi_memoria\contexto_qh.md")
        self.vision_ceo_path = Path(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\automatizacion\agi_memoria\vision_ceo.md")
        self.limites_path = Path(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\automatizacion\agi_memoria\limites_conocimiento.json")
    
    def activar(self):
        """Activa el modo desafío."""
        self.activo = True
        logger.info("[CHALLENGE MODE] Modo desafío activado")
        return {"estado": "activo", "mensaje": "AGI cuestionará decisiones con datos"}
    
    def desactivar(self):
        """Desactiva el modo desafío."""
        self.activo = False
        logger.info("[CHALLENGE MODE] Modo desafío desactivado")
        return {"estado": "inactivo", "mensaje": "AGI operará en modo estándar"}
    
    def cuestionar_decision(self, decision: str) -> Optional[Dict]:
        """Cuestiona una decisión de Sergio con datos."""
        if not self.activo:
            return None
        
        # Cargar contexto actual
        contexto = self._cargar_contexto()
        vision = self._cargar_vision()
        limites = self._cargar_limites()
        
        # Generar desafío basado en datos
        desafio = {
            "decision_original": decision,
            "cuestionamiento": self._generar_cuestionamiento(decision, contexto, vision, limites),
            "datos_relevantes": self._extraer_datos_relevantes(contexto, vision, limites),
            "alternativas": self._proponer_alternativas(decision, contexto),
            "timestamp": self._get_timestamp()
        }
        
        logger.info(f"[CHALLENGE MODE] Desafío generado para: {decision}")
        return desafio
    
    def _cargar_contexto(self) -> Dict:
        """Carga el contexto actual de QuantumHive."""
        if not self.contexto_qh_path.exists():
            return {"estado": "no_disponible"}
        
        with open(self.contexto_qh_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Parse simple del markdown (en producción usaría un parser real)
        return {"contenido": contenido, "estado": "cargado"}
    
    def _cargar_vision(self) -> Dict:
        """Carga la visión del CEO."""
        if not self.vision_ceo_path.exists():
            return {"estado": "no_disponible"}
        
        with open(self.vision_ceo_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        return {"contenido": contenido, "estado": "cargado"}
    
    def _cargar_limites(self) -> Dict:
        """Carga los límites de conocimiento de AGI."""
        if not self.limites_path.exists():
            return {"estado": "no_disponible"}
        
        with open(self.limites_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _generar_cuestionamiento(self, decision: str, contexto: Dict, vision: Dict, limites: Dict) -> str:
        """Genera un cuestionamiento basado en datos."""
        cuestionamientos = [
            f"Considerando que {self._extraer_prioridad(vision)} es la prioridad actual, ¿esta decisión alinea con esa dirección?",
            f"Dado que las capacidades actuales son {self._extraer_capacidades(limites)}, ¿esta decisión es ejecutable ahora?",
            f"Basado en el contexto de {self._extraer_fase(contexto)}, ¿esta decisión es el próximo paso lógico?",
        ]
        
        # En producción, esto sería más sofisticado usando LLM
        return cuestionamientos[0] if cuestionamientos else "No hay suficiente contexto para cuestionar."
    
    def _extraer_datos_relevantes(self, contexto: Dict, vision: Dict, limites: Dict) -> Dict:
        """Extrae datos relevantes para el desafío."""
        return {
            "fase_actual": self._extraer_fase(contexto),
            "prioridades": self._extraer_prioridad(vision),
            "capacidades": self._extraer_capacidades(limites),
            "limitaciones": limites.get("limitaciones_actuales", []) if limites.get("limitaciones_actuales") else []
        }
    
    def _proponer_alternativas(self, decision: str, contexto: Dict) -> list:
        """Propone alternativas a la decisión."""
        alternativas = [
            "Considera implementar esto por fases para reducir riesgo",
            "Valida primero con un prototipo antes de escalar",
            "Sincroniza con el equipo antes de ejecutar"
        ]
        return alternativas
    
    def _extraer_fase(self, contexto: Dict) -> str:
        """Extrae la fase actual del contexto."""
        if contexto.get("estado") == "cargado":
            contenido = contexto.get("contenido", "")
            if "Fase 1" in contenido:
                return "Fase 1 - Infraestructura Base"
        return "Desconocida"
    
    def _extraer_prioridad(self, vision: Dict) -> str:
        """Extrae la prioridad actual de la visión."""
        if vision.get("estado") == "cargado":
            contenido = vision.get("contenido", "")
            if "AGI UPGRADE" in contenido:
                return "AGI UPGRADE v2.0"
        return "No especificada"
    
    def _extraer_capacidades(self, limites: Dict) -> str:
        """Extrae las capacidades actuales."""
        if limites.get("estado") == "cargado":
            capacidades = limites.get("capacidades_disponibles", {})
            activas = [k for k, v in capacidades.items() if v]
            return ", ".join(activas)
        return "No especificadas"
    
    def _get_timestamp(self) -> str:
        """Obtiene el timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()

if __name__ == "__main__":
    challenge = ChallengeMode()
    
    # Prueba
    challenge.activar()
    resultado = challenge.cuestionar_decision("Crear un nuevo bot para BTC sin validar primero")
    print(json.dumps(resultado, indent=2))

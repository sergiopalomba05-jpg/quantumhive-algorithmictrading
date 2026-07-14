#!/usr/bin/env python3
"""
Intent Classifier — AGI UPGRADE v2.0
Clasifica la intención del mensaje de Sergio antes de procesarlo.
Esto permite que el Memory Manager guarde en la categoría correcta
y que el Action Router sepa si activarse o no.
"""

import re
from typing import Dict, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TipoIntencion(Enum):
    IDEA_NUEVA = "idea_nueva"
    ORDEN_DIRECTA = "orden_directa"
    CONSULTA_ESTADO = "consulta_estado"
    CONVERSACION_ESTRATEGICA = "conversacion_estrategica"
    URGENCIA = "urgencia"
    APROBACION = "aprobacion"
    RECHAZO = "rechazo"

class IntentClassifier:
    def __init__(self):
        self.patrones = {
            TipoIntencion.IDEA_NUEVA: [
                r"(?i)^tengo una idea",
                r"(?i)^propongo",
                r"(?i)^qué te parece si",
                r"(?i)^podríamos",
                r"(?i)^idea:",
                r"(?i)^💡",
                r"(?i)^nuevo proyecto",
            ],
            TipoIntencion.ORDEN_DIRECTA: [
                r"(?i)^ejecuta",
                r"(?i)^haz",
                r"(?i)^crea",
                r"(?i)^inicia",
                r"(?i)^comienza",
                r"(?i)^corre",
                r"(?i)^lanza",
            ],
            TipoIntencion.CONSULTA_ESTADO: [
                r"(?i)^cómo está",
                r"(?i)^qué pasa con",
                r"(?i)^estado de",
                r"(?i)^reporte",
                r"(?i)^resumen",
                r"(?i)^situación",
                r"(?i)^status",
            ],
            TipoIntencion.CONVERSACION_ESTRATEGICA: [
                r"(?i)^qué piensas sobre",
                r"(?i)^tu opinión",
                r"(?i)^estrategia",
                r"(?i)^visión",
                r"(?i)^planificar",
                r"(?i)^analizar",
            ],
            TipoIntencion.URGENCIA: [
                r"(?i)^urgente",
                r"(?i)^ahora",
                r"(?i)^inmediato",
                r"(?i)^crítico",
                r"(?i)^⚠️",
                r"(?i)^🚨",
            ],
            TipoIntencion.APROBACION: [
                r"(?i)^sí",
                r"(?i)^ok",
                r"(?i)^confirmado",
                r"(?i)^adelante",
                r"(?i)^✓",
                r"(?i)^✅",
            ],
            TipoIntencion.RECHAZO: [
                r"(?i)^no",
                r"(?i)^cancelar",
                r"(?i)^rechazar",
                r"(?i)^detener",
                r"(?i)^❌",
            ],
        }
    
    def clasificar(self, mensaje: str) -> Dict:
        """Clasifica la intención del mensaje."""
        if not mensaje or not mensaje.strip():
            return {
                "tipo": TipoIntencion.CONVERSACION_ESTRATEGICA.value,
                "confianza": 0.0,
                "metadatos": {"error": "mensaje_vacio"}
            }
        
        mensaje = mensaje.strip()
        mejor_coincidencia = None
        mejor_confianza = 0.0
        
        for tipo, patrones in self.patrones.items():
            for patron in patrones:
                if re.search(patron, mensaje):
                    confianza = self._calcular_confianza(patron, mensaje)
                    if confianza > mejor_confianza:
                        mejor_coincidencia = tipo
                        mejor_confianza = confianza
        
        if mejor_coincidencia is None:
            mejor_coincidencia = TipoIntencion.CONVERSACION_ESTRATEGICA
            mejor_confianza = 0.3
        
        resultado = {
            "tipo": mejor_coincidencia.value,
            "confianza": mejor_confianza,
            "metadatos": {
                "longitud_mensaje": len(mensaje),
                "palabras_clave": self._extraer_palabras_clave(mensaje),
                "timestamp": self._get_timestamp()
            }
        }
        
        logger.info(f"[INTENT CLASSIFIER] Mensaje clasificado como: {mejor_coincidencia.value} (confianza: {mejor_confianza:.2f})")
        return resultado
    
    def _calcular_confianza(self, patron: str, mensaje: str) -> float:
        """Calcula la confianza de la coincidencia."""
        coincidencia = re.search(patron, mensaje)
        if coincidencia:
            # Coincidencia al inicio del mensaje = mayor confianza
            if coincidencia.start() < len(mensaje) * 0.3:
                return 0.9
            else:
                return 0.7
        return 0.0
    
    def _extraer_palabras_clave(self, mensaje: str) -> list:
        """Extrae palabras clave del mensaje."""
        # Palabras comunes en contexto QuantumHive
        palabras_clave = ["bot", "agente", "división", "dashboard", "agi", "trading", 
                         "backtesting", "fábrica", "recursos", "nube", "gpu", "api"]
        
        encontradas = []
        for palabra in palabras_clave:
            if palabra.lower() in mensaje.lower():
                encontradas.append(palabra)
        
        return encontradas
    
    def _get_timestamp(self) -> str:
        """Obtiene el timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()

if __name__ == "__main__":
    classifier = IntentClassifier()
    
    # Pruebas
    mensajes = [
        "Tengo una idea para mejorar el dashboard",
        "Ejecuta el análisis de rendimiento",
        "Cómo está el bot Atlas?",
        "Qué piensas sobre la nueva estrategia",
        "URGENTE: El bot está en drawdown",
        "Sí, adelante con el plan",
        "No, cancela esa acción",
    ]
    
    for msg in mensajes:
        resultado = classifier.clasificar(msg)
        print(f"Mensaje: {msg}")
        print(f"Clasificación: {resultado}")
        print("-" * 50)

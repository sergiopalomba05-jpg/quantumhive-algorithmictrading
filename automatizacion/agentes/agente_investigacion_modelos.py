"""
Agente Investigación de Modelos IA — QuantumHive
Investiga y mantiene un registro actualizado de modelos IA disponibles y descontinuados.
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AgenteInvestigacionModelos:
    """Agente para investigación y seguimiento de modelos IA disponibles."""
    
    def __init__(self):
        self.registro_path = "modelos_registro.json"
        self.cargar_registro()
        logger.info("AgenteInvestigacionModelos inicializado")
    
    def cargar_registro(self):
        """Carga el registro de modelos desde archivo."""
        try:
            with open(self.registro_path, 'r') as f:
                self.registro = json.load(f)
            logger.info(f"Registro cargado: {len(self.registro)} modelos")
        except FileNotFoundError:
            self.registro = {}
            logger.info("Registro nuevo creado")
    
    def guardar_registro(self):
        """Guarda el registro de modelos en archivo."""
        with open(self.registro_path, 'w') as f:
            json.dump(self.registro, f, indent=2)
        logger.info("Registro guardado")
    
    def investigar_modelos_groq(self) -> Dict:
        """Investiga modelos disponibles en Groq."""
        try:
            url = "https://api.groq.com/openai/v1/models"
            headers = {
                'Authorization': f'Bearer {os.getenv("GROQ_API_KEY", "")}',
                'Content-Type': 'application/json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                modelos = response.json()
                modelos_groq = []
                
                for modelo in modelos.get('data', []):
                    modelos_groq.append({
                        'id': modelo.get('id'),
                        'nombre': modelo.get('id'),
                        'proveedor': 'groq',
                        'estado': 'activo',
                        'ultima_verificacion': datetime.now().isoformat()
                    })
                
                logger.info(f"Modelos Groq investigados: {len(modelos_groq)}")
                return {'groq': modelos_groq}
            else:
                logger.error(f"Error investigando modelos Groq: {response.status_code}")
                return {'groq': []}
                
        except Exception as e:
            logger.error(f"Error investigando modelos Groq: {e}")
            return {'groq': []}
    
    def obtener_modelo_funcional_groq(self) -> Optional[str]:
        """
        Retorna el modelo funcional más actual de Groq.
        Prioriza modelos que no estén descontinuados.
        """
        modelos_disponibles = self.investigar_modelos_groq()
        
        if not modelos_disponibles.get('groq'):
            logger.error("No se encontraron modelos Groq disponibles")
            return None
        
        # Priorizar modelos Llama 3
        for modelo in modelos_disponibles['groq']:
            if 'llama' in modelo['id'].lower() and 'versatile' in modelo['id'].lower():
                logger.info(f"Modelo recomendado: {modelo['id']}")
                return modelo['id']
        
        # Fallback a cualquier modelo disponible
        for modelo in modelos_disponibles['groq']:
            logger.info(f"Modelo recomendado (fallback): {modelo['id']}")
            return modelo['id']
        
        return None
    
    def actualizar_registro(self):
        """Actualiza el registro con información de todos los proveedores."""
        logger.info("Actualizando registro de modelos...")
        
        # Investigar Groq
        modelos_groq = self.investigar_modelos_groq()
        self.registro['groq'] = modelos_groq.get('groq', [])
        
        # Guardar registro
        self.guardar_registro()
        logger.info("Registro actualizado")
    
    def obtener_modelos_descontinuados(self) -> List[str]:
        """Retorna lista de modelos descontinuados."""
        descontinuados = []
        
        for proveedor, modelos in self.registro.items():
            for modelo in modelos:
                if modelo.get('estado') == 'descontinuado':
                    descontinuados.append(modelo['id'])
        
        return descontinuados
    
    def obtener_modelos_activos(self) -> Dict[str, List[str]]:
        """Retorna diccionario de modelos activos por proveedor."""
        activos = {}
        
        for proveedor, modelos in self.registro.items():
            activos[proveedor] = [
                modelo['id'] for modelo in modelos 
                if modelo.get('estado') == 'activo'
            ]
        
        return activos


# Instancia global del agente
agente_investigacion = AgenteInvestigacionModelos()


if __name__ == "__main__":
    # Test del agente
    agente = AgenteInvestigacionModelos()
    agente.actualizar_registro()
    
    modelo_funcional = agente.obtener_modelo_funcional_groq()
    print(f"Modelo funcional recomendado: {modelo_funcional}")

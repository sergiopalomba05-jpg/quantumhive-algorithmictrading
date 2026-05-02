"""
Memory Loader por Capas — QuantumHive AGI
Carga memoria organizada en capas: Contexto → Estratégico → Operativo → Técnico.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryLoader:
    """Carga memoria organizada en capas jerárquicas."""
    
    def __init__(self, base_path: str = "CONTEXTOS_GENERALES"):
        self.base_path = Path(base_path)
        self.capas = {
            'contexto': [],
            'estrategico': [],
            'operativo': [],
            'tecnico': []
        }
        self.cargar_memoria()
    
    def cargar_memoria(self):
        """Carga archivos de memoria en sus capas correspondientes."""
        if not self.base_path.exists():
            logger.warning(f"Directorio de memoria no encontrado: {self.base_path}")
            return
        
        for archivo in self.base_path.glob("*.md"):
            nombre = archivo.name.lower()
            contenido = self._leer_archivo(archivo)
            
            if not contenido:
                continue
            
            # Clasificar por capa según nombre del archivo
            if 'contexto' in nombre or 'macro' in nombre:
                self.capas['contexto'].append({
                    'nombre': archivo.name,
                    'ruta': str(archivo),
                    'contenido': contenido,
                    'capa': 'contexto'
                })
            elif 'estrategia' in nombre or 'plan' in nombre:
                self.capas['estrategico'].append({
                    'nombre': archivo.name,
                    'ruta': str(archivo),
                    'contenido': contenido,
                    'capa': 'estrategico'
                })
            elif 'operativo' in nombre or 'proceso' in nombre or 'protocolo' in nombre:
                self.capas['operativo'].append({
                    'nombre': archivo.name,
                    'ruta': str(archivo),
                    'contenido': contenido,
                    'capa': 'operativo'
                })
            else:
                # Por defecto a técnico
                self.capas['tecnico'].append({
                    'nombre': archivo.name,
                    'ruta': str(archivo),
                    'contenido': contenido,
                    'capa': 'tecnico'
                })
        
        logger.info(f"Memoria cargada: {self._contar_total()} archivos")
        for capa, archivos in self.capas.items():
            logger.info(f"  Capa {capa}: {len(archivos)} archivos")
    
    def _leer_archivo(self, ruta: Path) -> Optional[str]:
        """Lee el contenido de un archivo."""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error leyendo {ruta}: {e}")
            return None
    
    def _contar_total(self) -> int:
        """Cuenta total de archivos en todas las capas."""
        return sum(len(archivos) for archivos in self.capas.values())
    
    def obtener_capa(self, capa: str) -> List[Dict]:
        """
        Obtiene todos los archivos de una capa específica.
        
        Args:
            capa: Nombre de la capa (contexto, estratégico, operativo, técnico)
        """
        return self.capas.get(capa, [])
    
    def obtener_contexto_completo(self, capas: Optional[List[str]] = None) -> str:
        """
        Obtiene contexto completo concatenando capas especificadas.
        
        Args:
            capas: Lista de capas a incluir (si es None, incluye todas en orden jerárquico)
        """
        if capas is None:
            capas = ['contexto', 'estrategico', 'operativo', 'tecnico']
        
        contexto = ""
        for capa in capas:
            archivos = self.capas.get(capa, [])
            for archivo in archivos:
                contexto += f"\n\n=== {archivo['nombre']} ({capa.upper()}) ===\n"
                contexto += archivo['contenido']
        
        return contexto
    
    def buscar_en_memoria(self, query: str, capas: Optional[List[str]] = None) -> List[Dict]:
        """
        Busca texto en los archivos de memoria.
        
        Args:
            query: Texto a buscar
            capas: Capas donde buscar (si es None, busca en todas)
        """
        if capas is None:
            capas = list(self.capas.keys())
        
        resultados = []
        query_lower = query.lower()
        
        for capa in capas:
            for archivo in self.capas.get(capa, []):
                if query_lower in archivo['contenido'].lower():
                    resultados.append({
                        'archivo': archivo['nombre'],
                        'capa': capa,
                        'ruta': archivo['ruta'],
                        'relevancia': archivo['contenido'].lower().count(query_lower)
                    })
        
        # Ordenar por relevancia
        resultados.sort(key=lambda x: x['relevancia'], reverse=True)
        return resultados
    
    def obtener_resumen_capas(self) -> Dict:
        """Obtiene resumen de todas las capas."""
        return {
            capa: {
                'cantidad': len(archivos),
                'archivos': [a['nombre'] for a in archivos]
            }
            for capa, archivos in self.capas.items()
        }


# Instancia global del memory loader
memory_loader = MemoryLoader()


if __name__ == "__main__":
    # Test del memory loader
    print("=== MEMORY LOADER - TEST ===\n")
    
    loader = MemoryLoader()
    
    # Resumen de capas
    print("Resumen de capas:")
    resumen = loader.obtener_resumen_capas()
    for capa, info in resumen.items():
        print(f"  {capa}: {info['cantidad']} archivos")
    
    # Buscar ejemplo
    print("\nBuscando 'estrategia' en memoria:")
    resultados = loader.buscar_en_memoria('estrategia')
    for r in resultados[:5]:
        print(f"  - {r['archivo']} ({r['capa']}) - Relevancia: {r['relevancia']}")

#!/usr/bin/env python3
"""
Agente Estructurador y Organizador de Estrategias
================================================
Limpia, filtra y organiza la información recolectada:

Funciones:
- Eliminar información duplicada
- Filtrar por calidad y relevancia
- Estructurar por categorías:
  * Tipo de estrategia (reversión, continuidad, breakout, scalping)
  * Tipo de activo (forex, índices, metales, criptos)
  * Temporalidad (M1, M5, M15, H1, H4, D1)
  * Nivel de complejidad (clásico, avanzado, profesional)
- Organizar por entorno aplicable
- Generar biblioteca limpia y funcional
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteEstructuradorEstrategias:
    def __init__(self, input_dir: str = None, output_dir: str = None):
        self.input_dir = Path(input_dir) if input_dir else Path(__file__).parent.parent.parent.parent / "biblioteca_fabrica" / "recolectado"
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "biblioteca_fabrica" / "estructurado"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estructura de biblioteca organizada
        self.estructura_biblioteca = {
            'por_tipo_estrategia': {},
            'por_activo': {},
            'por_temporalidad': {},
            'por_complejidad': {},
            'por_categoria': {}
        }
        
    def _generar_hash(self, item: Dict) -> str:
        """Genera hash único para detectar duplicados."""
        contenido = json.dumps(item, sort_keys=True)
        return hashlib.md5(contenido.encode()).hexdigest()
    
    def _cargar_recolectado(self) -> List[Dict]:
        """Carga todos los archivos recolectados."""
        items = []
        for archivo in self.input_dir.glob("*.json"):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        items.extend(data)
                    else:
                        items.append(data)
            except Exception as e:
                logger.error(f"Error leyendo {archivo}: {e}")
        return items
    
    def _eliminar_duplicados(self, items: List[Dict]) -> List[Dict]:
        """Elimina items duplicados basándose en hash."""
        hashes_vistos: Set[str] = set()
        items_unicos = []
        
        for item in items:
            hash_item = self._generar_hash(item)
            if hash_item not in hashes_vistos:
                hashes_vistos.add(hash_item)
                items_unicos.append(item)
        
        logger.info(f"Eliminados {len(items) - len(items_unicos)} duplicados")
        return items_unicos
    
    def _filtrar_por_calidad(self, items: List[Dict]) -> List[Dict]:
        """Filtra items por calidad y relevancia."""
        items_filtrados = []
        
        for item in items:
            # Criterios de calidad
            calidad = True
            
            # Debe tener nombre o descripción
            if not item.get('nombre') and not item.get('descripcion'):
                calidad = False
            
            # Si es de GitHub, debe tener mínimas estrellas o descripción
            if item.get('fuente') == 'GitHub':
                if item.get('estrellas', 0) < 5 and not item.get('descripcion'):
                    calidad = False
            
            # Debe tener contexto
            if not item.get('contexto'):
                calidad = False
            
            if calidad:
                items_filtrados.append(item)
        
        logger.info(f"Filtrados {len(items_filtrados)}/{len(items)} items por calidad")
        return items_filtrados
    
    def _clasificar_por_tipo_estrategia(self, item: Dict) -> str:
        """Clasifica el item por tipo de estrategia."""
        contexto = item.get('contexto', {})
        
        if contexto.get('tipo_estrategia'):
            return contexto['tipo_estrategia']
        
        # Inferir de descripción
        descripcion = item.get('descripcion', '').lower()
        if 'revers' in descripcion:
            return 'reversión'
        elif 'contin' in descripcion or 'trend' in descripcion:
            return 'continuidad'
        elif 'breakout' in descripcion or 'break' in descripcion:
            return 'breakout'
        elif 'scalp' in descripcion:
            return 'scalping'
        
        return 'general'
    
    def _clasificar_por_activo(self, item: Dict) -> List[str]:
        """Clasifica el item por tipo de activo."""
        contexto = item.get('contexto', {})
        
        if contexto.get('activos'):
            return contexto['activos']
        
        # Inferir de descripción
        descripcion = item.get('descripcion', '').lower()
        activos = []
        
        if 'forex' in descripcion or any(p in descripcion for p in ['eurusd', 'gbpusd', 'usdjpy']):
            activos.append('forex')
        if 'us30' in descripcion or 'nasdaq' in descripcion or 'sp500' in descripcion:
            activos.append('indices')
        if 'gold' in descripcion or 'xauusd' in descripcion or 'silver' in descripcion:
            activos.append('metales')
        if 'btc' in descripcion or 'bitcoin' in descripcion or 'eth' in descripcion:
            activos.append('criptos')
        
        return activos if activos else ['general']
    
    def _clasificar_por_temporalidad(self, item: Dict) -> List[str]:
        """Clasifica el item por temporalidad."""
        contexto = item.get('contexto', {})
        
        if contexto.get('temporalidades'):
            return contexto['temporalidades']
        
        # Inferir de descripción
        descripcion = item.get('descripcion', '').lower()
        temporalidades = []
        
        temps = ['m1', 'm5', 'm15', 'h1', 'h4', 'd1']
        for temp in temps:
            if temp in descripcion:
                temporalidades.append(temp)
        
        return temporalidades if temporalidades else ['general']
    
    def _clasificar_por_complejidad(self, item: Dict) -> str:
        """Clasifica el item por nivel de complejidad."""
        contexto = item.get('contexto', {})
        
        if contexto.get('nivel'):
            return contexto['nivel']
        
        if contexto.get('nivel_complejidad'):
            return contexto['nivel_complejidad']
        
        # Inferir de tipo
        if item.get('tipo') == 'avanzado':
            return 'avanzado'
        elif item.get('tipo') == 'clásico':
            return 'clásico'
        
        # Inferir de descripción
        descripcion = item.get('descripcion', '').lower()
        if 'footprint' in descripcion or 'order flow' in descripcion or 'delta' in descripcion:
            return 'profesional'
        elif 'advanced' in descripcion or 'professional' in descripcion:
            return 'avanzado'
        
        return 'clásico'
    
    def _clasificar_por_categoria(self, item: Dict) -> str:
        """Clasifica el item por categoría."""
        contexto = item.get('contexto', {})
        
        if contexto.get('categoria'):
            return contexto['categoria']
        
        # Inferir de tipo
        if item.get('categoria'):
            return item['categoria']
        
        return 'general'
    
    def _organizar_en_estructura(self, items: List[Dict]):
        """Organiza los items en la estructura de biblioteca."""
        for item in items:
            # Clasificaciones
            tipo_estrategia = self._clasificar_por_tipo_estrategia(item)
            activos = self._clasificar_por_activo(item)
            temporalidades = self._clasificar_por_temporalidad(item)
            complejidad = self._clasificar_por_complejidad(item)
            categoria = self._clasificar_por_categoria(item)
            
            # Agregar a estructura
            if tipo_estrategia not in self.estructura_biblioteca['por_tipo_estrategia']:
                self.estructura_biblioteca['por_tipo_estrategia'][tipo_estrategia] = []
            self.estructura_biblioteca['por_tipo_estrategia'][tipo_estrategia].append(item)
            
            for activo in activos:
                if activo not in self.estructura_biblioteca['por_activo']:
                    self.estructura_biblioteca['por_activo'][activo] = []
                self.estructura_biblioteca['por_activo'][activo].append(item)
            
            for temp in temporalidades:
                if temp not in self.estructura_biblioteca['por_temporalidad']:
                    self.estructura_biblioteca['por_temporalidad'][temp] = []
                self.estructura_biblioteca['por_temporalidad'][temp].append(item)
            
            if complejidad not in self.estructura_biblioteca['por_complejidad']:
                self.estructura_biblioteca['por_complejidad'][complejidad] = []
            self.estructura_biblioteca['por_complejidad'][complejidad].append(item)
            
            if categoria not in self.estructura_biblioteca['por_categoria']:
                self.estructura_biblioteca['por_categoria'][categoria] = []
            self.estructura_biblioteca['por_categoria'][categoria].append(item)
    
    def _guardar_estructura_organizada(self):
        """Guarda la estructura organizada en archivos."""
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Guardar por tipo de estrategia
        dir_tipo = self.output_dir / 'por_tipo_estrategia'
        dir_tipo.mkdir(parents=True, exist_ok=True)
        for tipo, items in self.estructura_biblioteca['por_tipo_estrategia'].items():
            archivo = dir_tipo / f"{tipo}_{fecha}.json"
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        
        # Guardar por activo
        dir_activo = self.output_dir / 'por_activo'
        dir_activo.mkdir(parents=True, exist_ok=True)
        for activo, items in self.estructura_biblioteca['por_activo'].items():
            archivo = dir_activo / f"{activo}_{fecha}.json"
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        
        # Guardar por complejidad
        dir_complejidad = self.output_dir / 'por_complejidad'
        dir_complejidad.mkdir(parents=True, exist_ok=True)
        for complejidad, items in self.estructura_biblioteca['por_complejidad'].items():
            archivo = dir_complejidad / f"{complejidad}_{fecha}.json"
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        
        # Guardar índice general
        indice = {
            'fecha_estructurado': datetime.now().isoformat(),
            'total_items': sum(len(v) for v in self.estructura_biblioteca['por_tipo_estrategia'].values()),
            'categorias': {
                'tipos_estrategia': list(self.estructura_biblioteca['por_tipo_estrategia'].keys()),
                'activos': list(self.estructura_biblioteca['por_activo'].keys()),
                'temporalidades': list(self.estructura_biblioteca['por_temporalidad'].keys()),
                'complejidades': list(self.estructura_biblioteca['por_complejidad'].keys()),
                'categorias': list(self.estructura_biblioteca['por_categoria'].keys())
            }
        }
        
        archivo_indice = self.output_dir / f"indice_{fecha}.json"
        with open(archivo_indice, 'w', encoding='utf-8') as f:
            json.dump(indice, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Estructura guardada en {self.output_dir}")
        logger.info(f"Total items organizados: {indice['total_items']}")
    
    def ejecutar_estructuracion(self):
        """Ejecuta el ciclo completo de estructuración."""
        logger.info("[INICIO] Ciclo de estructuración de estrategias")
        
        # Cargar recolectado
        logger.info("[ESTRUCTURADOR] Cargando datos recolectados...")
        items = self._cargar_recolectado()
        logger.info(f"[ESTRUCTURADOR] Cargados {len(items)} items")
        
        # Eliminar duplicados
        logger.info("[ESTRUCTURADOR] Eliminando duplicados...")
        items = self._eliminar_duplicados(items)
        
        # Filtrar por calidad
        logger.info("[ESTRUCTURADOR] Filtrando por calidad...")
        items = self._filtrar_por_calidad(items)
        
        # Organizar en estructura
        logger.info("[ESTRUCTURADOR] Organizando en estructura...")
        self._organizar_en_estructura(items)
        
        # Guardar estructura
        logger.info("[ESTRUCTURADOR] Guardando estructura organizada...")
        self._guardar_estructura_organizada()
        
        logger.info("[FIN] Ciclo de estructuración completado")

if __name__ == "__main__":
    estructurador = AgenteEstructuradorEstrategias()
    estructurador.ejecutar_estructuracion()

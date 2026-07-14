#!/usr/bin/env python3
"""
Agente Recolector de Estrategias
=================================
Recolecta información de la web sobre:
- Scripts de trading
- Indicadores técnicos (clásicos y avanzados)
- Order flow y footprint
- Estrategias rentables ya armadas
- Plantillas de configuración
- Herramientas profesionales

Cada dato incluye contexto:
- Fuente (URL, repositorio, autor)
- Tipo de activo (forex, índices, metales, criptos)
- Temporalidad (M1, M5, M15, H1, H4, D1)
- Mercado y entorno aplicable
- Naturaleza (reversión, continuidad, breakout, scalping)
"""

import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteRecolectorEstrategias:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "biblioteca_fabrica" / "recolectado"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def recolectar_github(self, query: str, max_results: int = 20) -> List[Dict]:
        """Recolecta scripts de GitHub relacionados con trading."""
        try:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={max_results}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                resultados = []
                for item in data.get('items', []):
                    resultado = {
                        'fuente': 'GitHub',
                        'url': item['html_url'],
                        'nombre': item['name'],
                        'descripcion': item.get('description', ''),
                        'estrellas': item['stargazers_count'],
                        'lenguaje': item.get('language', ''),
                        'fecha_recoleccion': datetime.now().isoformat(),
                        'tipo': 'repositorio',
                        'contexto': self._analizar_contexto(item.get('description', ''))
                    }
                    resultados.append(resultado)
                return resultados
        except Exception as e:
            logger.error(f"Error recolectando de GitHub: {e}")
        return []
    
    def _analizar_contexto(self, texto: str) -> Dict:
        """Analiza el contexto de una estrategia basado en su descripción."""
        texto_lower = texto.lower()
        contexto = {
            'tipo_estrategia': 'desconocido',
            'activos': [],
            'temporalidades': [],
            'indicadores': []
        }
        
        # Detectar tipo de estrategia
        if 'revers' in texto_lower:
            contexto['tipo_estrategia'] = 'reversión'
        elif 'contin' in texto_lower or 'trend' in texto_lower:
            contexto['tipo_estrategia'] = 'continuidad'
        elif 'breakout' in texto_lower or 'break' in texto_lower:
            contexto['tipo_estrategia'] = 'breakout'
        elif 'scalp' in texto_lower:
            contexto['tipo_estrategia'] = 'scalping'
        
        # Detectar activos
        activos_keywords = {
            'forex': ['forex', 'eurusd', 'gbpusd', 'usdjpy'],
            'indices': ['us30', 'nasdaq', 'sp500', 'dow'],
            'metales': ['gold', 'xauusd', 'silver', 'xagusd'],
            'criptos': ['btc', 'bitcoin', 'eth', 'xrp']
        }
        for categoria, keywords in activos_keywords.items():
            if any(kw in texto_lower for kw in keywords):
                contexto['activos'].append(categoria)
        
        # Detectar temporalidades
        temporalidades = ['m1', 'm5', 'm15', 'h1', 'h4', 'd1']
        for temp in temporalidades:
            if temp in texto_lower:
                contexto['temporalidades'].append(temp)
        
        # Detectar indicadores comunes
        indicadores = ['rsi', 'macd', 'bb', 'bollinger', 'ema', 'sma', 'atr', 'stochastic']
        for ind in indicadores:
            if ind in texto_lower:
                contexto['indicadores'].append(ind)
        
        return contexto
    
    def recolectar_tradingview(self, indicadores_avanzados: bool = True) -> List[Dict]:
        """Recolecta información sobre indicadores de TradingView."""
        # Simulación - en producción se usaría scraping de TradingView
        indicadores_base = [
            {'nombre': 'RSI', 'tipo': 'clásico', 'categoria': 'momentum'},
            {'nombre': 'MACD', 'tipo': 'clásico', 'categoria': 'trend'},
            {'nombre': 'Bollinger Bands', 'tipo': 'clásico', 'categoria': 'volatilidad'},
            {'nombre': 'ATR', 'tipo': 'clásico', 'categoria': 'volatilidad'},
        ]
        
        if indicadores_avanzados:
            indicadores_avz = [
                {'nombre': 'Footprint Chart', 'tipo': 'avanzado', 'categoria': 'order_flow'},
                {'nombre': 'Volume Profile', 'tipo': 'avanzado', 'categoria': 'volumen'},
                {'nombre': 'Cumulative Volume Delta', 'tipo': 'avanzado', 'categoria': 'order_flow'},
                {'nombre': 'Market Profile', 'tipo': 'avanzado', 'categoria': 'volumen'},
                {'nombre': 'Order Flow', 'tipo': 'avanzado', 'categoria': 'order_flow'},
            ]
            indicadores_base.extend(indicadores_avz)
        
        resultados = []
        for ind in indicadores_base:
            resultado = {
                'fuente': 'TradingView',
                'nombre': ind['nombre'],
                'tipo': ind['tipo'],
                'categoria': ind['categoria'],
                'fecha_recoleccion': datetime.now().isoformat(),
                'contexto': {
                    'tipo_herramienta': 'indicador',
                    'nivel_complejidad': ind['tipo']
                }
            }
            resultados.append(resultado)
        
        return resultados
    
    def recolectar_order_flow(self) -> List[Dict]:
        """Recolecta información específica sobre Order Flow."""
        estrategias_order_flow = [
            {
                'nombre': 'Footprint Reversal',
                'descripcion': 'Detección de reversión usando footprint charts',
                'indicadores': ['Footprint', 'CVD', 'Delta'],
                'contexto': {'tipo_estrategia': 'reversión', 'nivel': 'avanzado'}
            },
            {
                'nombre': 'Volume Profile Breakout',
                'descripcion': 'Breakout de niveles de volumen',
                'indicadores': ['Volume Profile', 'POC', 'VAH', 'VAL'],
                'contexto': {'tipo_estrategia': 'breakout', 'nivel': 'avanzado'}
            },
            {
                'nombre': 'Cumulative Delta Trend',
                'descripcion': 'Seguimiento de tendencia con delta acumulado',
                'indicadores': ['CVD', 'Delta', 'Volume'],
                'contexto': {'tipo_estrategia': 'continuidad', 'nivel': 'avanzado'}
            }
        ]
        
        resultados = []
        for estrategia in estrategias_order_flow:
            resultado = {
                'fuente': 'Repositorio Order Flow',
                'fecha_recoleccion': datetime.now().isoformat(),
                **estrategia
            }
            resultados.append(resultado)
        
        return resultados
    
    def guardar_resultados(self, resultados: List[Dict], categoria: str):
        """Guarda los resultados recolectados en archivos JSON."""
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo = self.output_dir / f"{categoria}_{fecha}.json"
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Guardados {len(resultados)} resultados en {archivo}")
    
    def ejecutar_recoleccion_completa(self):
        """Ejecuta el ciclo completo de recolección."""
        logger.info("[INICIO] Ciclo de recolección de estrategias")
        
        # Recolectar de GitHub
        logger.info("[RECOLECTOR] Buscando en GitHub...")
        queries = ['trading strategy', 'order flow', 'footprint', 'trading indicators', 'mt5 ea']
        for query in queries:
            resultados = self.recolectar_github(query)
            if resultados:
                self.guardar_resultados(resultados, f'github_{query.replace(" ", "_")}')
        
        # Recolectar indicadores TradingView
        logger.info("[RECOLECTOR] Recolectando indicadores TradingView...")
        resultados_tv = self.recolectar_tradingview(indicadores_avanzados=True)
        self.guardar_resultados(resultados_tv, 'tradingview_indicadores')
        
        # Recolectar Order Flow
        logger.info("[RECOLECTOR] Recolectando estrategias Order Flow...")
        resultados_of = self.recolectar_order_flow()
        self.guardar_resultados(resultados_of, 'order_flow')
        
        logger.info("[FIN] Ciclo de recolección completado")

if __name__ == "__main__":
    recolector = AgenteRecolectorEstrategias()
    recolector.ejecutar_recoleccion_completa()

#!/usr/bin/env python3
"""
Agente Marketing de Bots Rentables
==================================
Genera información de marketing para bots rentables:

Funciones:
- Extrae todas las características del bot
- Cómo fue creado (parámetros, indicadores, configuración)
- Resultados numéricos (WR, PF, PnL, Ops)
- Asigna nombre especial a cada bot rentable
- Genera personalidad percibida por clientes
- Estructura info para campañas de venta
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteMarketingBots:
    def __init__(self, output_dir: str = None):
        # UBICACIÓN SEGURA: bots_terminados/ para evitar pérdida de archivos
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "bots_terminados" / "bots_rentables"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Nombres especiales para bots rentables
        self.nombres_bot = [
            "Atlas", "Phoenix", "Titan", "Quantum", "Nova", 
            "Zenith", "Apex", "Vertex", "Nexus", "Prism",
            "Vortex", "Catalyst", "Matrix", "Pulse", "Flux"
        ]
        self.indice_nombre = 0
    
    def _generar_nombre_bot(self) -> str:
        """Genera un nombre especial para el bot."""
        nombre = self.nombres_bot[self.indice_nombre % len(self.nombres_bot)]
        self.indice_nombre += 1
        return nombre
    
    def _generar_personalidad(self, resultados: Dict) -> str:
        """Genera la personalidad percibida del bot."""
        wr = resultados.get('winrate', 0)
        pf = resultados.get('profit_factor', 0)
        ops = resultados.get('operaciones', 0)
        
        if wr > 55 and pf > 1.5:
            return "Conservador de alto rendimiento - Equilibrio perfecto entre precisión y rentabilidad"
        elif wr > 50 and pf > 1.5:
            return "Estratega equilibrado - Rentabilidad sólida con gestión de riesgo profesional"
        elif wr > 55 and pf > 1.2:
            return "Precisionista - Alta tasa de aciertos con rentabilidad consistente"
        elif ops > 200:
            return "Activo dinámico - Múltiples oportunidades con gestión agresiva"
        else:
            return "Analista calculador - Estrategia metódica y consistente"
    
    def _generar_puntos_venta(self, resultados: Dict, config: Dict) -> List[str]:
        """Genera puntos de venta destacados."""
        puntos = []
        
        wr = resultados.get('winrate', 0)
        pf = resultados.get('profit_factor', 0)
        pnl = resultados.get('pnl_total', 0)
        ops = resultados.get('operaciones', 0)
        
        if wr > 50:
            puntos.append(f"Tasa de aciertos del {wr:.1f}% - Superior al promedio del mercado")
        if pf > 1.3:
            puntos.append(f"Profit Factor de {pf:.2f} - Rentabilidad sostenible a largo plazo")
        if pnl > 2000:
            puntos.append(f"Profit acumulado de ${pnl:,.2f} - Resultados comprobados en backtesting")
        if ops > 100:
            puntos.append(f"{ops} operaciones validadas - Estrategia probada en múltiples escenarios")
        
        # Puntos basados en configuración
        if config.get('atr_sl_mult', 0) < 1.0:
            puntos.append("Stop Loss optimizado con ATR - Gestión de riesgo profesional")
        if config.get('rr_tp1', 0) > 1.5:
            puntos.append("Ratio Riesgo/Beneficio superior a 1.5 - Maximización de ganancias")
        
        return puntos
    
    def _generar_reporte_completo(self, nombre: str, activo: str, temporalidad: str, 
                                   resultados: Dict, config: Dict, periodo: str) -> Dict:
        """Genera reporte completo de marketing."""
        personalidad = self._generar_personalidad(resultados)
        puntos_venta = self._generar_puntos_venta(resultados, config)
        
        reporte = {
            'nombre_comercial': nombre,
            'activo': activo,
            'temporalidad': temporalidad,
            'periodo_backtesting': periodo,
            'personalidad': personalidad,
            'resultados': {
                'operaciones': resultados.get('operaciones', 0),
                'winrate': f"{resultados.get('winrate', 0):.1%}",
                'profit_factor': f"{resultados.get('profit_factor', 0):.2f}",
                'pnl_total': f"${resultados.get('pnl_total', 0):.2f}"
            },
            'configuracion': {
                'indicadores': ['Bollinger Bands', 'RSI', 'ATR'],
                'bb_periodo': config.get('bb_periodo', 0),
                'bb_desv': config.get('bb_desv', 0),
                'rsi_periodo': config.get('rsi_periodo', 0),
                'rsi_rangos': f"{config.get('rsi_rev_long_max', 0)}/{config.get('rsi_rev_short_min', 0)}",
                'sl_atr_mult': config.get('atr_sl_mult', 0),
                'tp_rr': f"{config.get('rr_tp1', 0)}/{config.get('rr_tp2', 0)}",
                'max_ops_dia': config.get('max_ops_dia', 0)
            },
            'puntos_venta': puntos_venta,
            'descripcion_marketing': f"{nombre} es un bot de trading especializado en {activo} ({temporalidad}). {personalidad}. {puntos_venta[0] if puntos_venta else ''}",
            'fecha_generacion': datetime.now().isoformat(),
            'estado': 'rentable'
        }
        
        return reporte
    
    def guardar_reporte(self, reporte: Dict):
        """Guarda el reporte en archivo JSON."""
        nombre_bot = reporte['nombre_comercial']
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo = self.output_dir / f"reporte_{nombre_bot}_{fecha}.json"
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[MARKETING] Reporte guardado: {nombre_bot}")
        
        # También guardar en resumen general
        resumen_archivo = self.output_dir / "resumen_bots_rentables.json"
        resumen = []
        if resumen_archivo.exists():
            with open(resumen_archivo, 'r', encoding='utf-8') as f:
                resumen = json.load(f)
        
        resumen.append({
            'nombre': nombre_bot,
            'activo': reporte['activo'],
            'temporalidad': reporte['temporalidad'],
            'winrate': reporte['resultados']['winrate'],
            'profit_factor': reporte['resultados']['profit_factor'],
            'pnl': reporte['resultados']['pnl_total'],
            'fecha': reporte['fecha_generacion']
        })
        
        with open(resumen_archivo, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False)
    
    def procesar_bot_rentable(self, activo: str, temporalidad: str, resultados: Dict, 
                              config: Dict, periodo: str):
        """Procesa un bot rentable y genera reporte de marketing."""
        logger.info(f"[MARKETING] Procesando bot rentable: {activo} {temporalidad}")
        
        nombre = self._generar_nombre_bot()
        reporte = self._generar_reporte_completo(nombre, activo, temporalidad, 
                                                  resultados, config, periodo)
        
        self.guardar_reporte(reporte)
        
        logger.info(f"[MARKETING] Bot '{nombre}' procesado y reporte generado")
        return reporte

if __name__ == "__main__":
    marketing = AgenteMarketingBots()
    
    # Ejemplo de uso
    resultados_ejemplo = {
        'operaciones': 139,
        'winrate': 0.532,
        'profit_factor': 1.53,
        'pnl_total': 3192.38
    }
    
    config_ejemplo = {
        'bb_periodo': 30,
        'bb_desv': 2.5,
        'rsi_periodo': 7,
        'rsi_rev_long_max': 25.0,
        'rsi_rev_short_min': 75.0,
        'atr_sl_mult': 0.8,
        'rr_tp1': 2.0,
        'rr_tp2': 2.5,
        'max_ops_dia': 4
    }
    
    marketing.procesar_bot_rentable('XAUUSD', 'M5', resultados_ejemplo, 
                                     config_ejemplo, '2025-01→2026-04')

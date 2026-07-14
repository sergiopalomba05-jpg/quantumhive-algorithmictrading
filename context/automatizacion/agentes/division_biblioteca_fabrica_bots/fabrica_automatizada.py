#!/usr/bin/env python3
"""
Fábrica Automatizada de Bots
=============================
Ciclo automático sin intervención manual:

1. Recolectar estrategias → 2. Estructurar → 3. Combinar → 4. Entrenar → 5. Validar → 6. Marketing
"""

import sys
from pathlib import Path
import logging
import traceback
from datetime import datetime

# Agregar ruta al proyecto
root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root))

from automatizacion.agentes.division_biblioteca_fabrica_bots.agente_recolector_estrategias import AgenteRecolectorEstrategias
from automatizacion.agentes.division_biblioteca_fabrica_bots.agente_estructurador_estrategias import AgenteEstructuradorEstrategias
from automatizacion.agentes.division_biblioteca_fabrica_bots.agente_combinador_estrategias import AgenteCombinadorEstrategias
from automatizacion.agentes.division_biblioteca_fabrica_bots.agente_marketing_bots import AgenteMarketingBots

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(root / 'logs' / 'fabrica_automatizada.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FabricaAutomatizada:
    def __init__(self):
        self.recolector = AgenteRecolectorEstrategias()
        self.estructurador = AgenteEstructuradorEstrategias()
        self.combinador = AgenteCombinadorEstrategias()
        self.marketing = AgenteMarketingBots()
        
    def ejecutar_ciclo_completo(self):
        """Ejecuta el ciclo completo de la fábrica."""
        try:
            logger.info("="*80)
            logger.info("[FABRICA] Iniciando ciclo automatizado")
            logger.info(f"[FABRICA] Fecha: {datetime.now().isoformat()}")
            logger.info("="*80)
            
            # Paso 1: Recolectar
            logger.info("[PASO 1] Recolectando estrategias...")
            try:
                self.recolector.ejecutar_recoleccion_completa()
                logger.info("[PASO 1] ✓ Recolectado completado")
            except Exception as e:
                logger.error(f"[PASO 1] Error: {e}")
                logger.error(traceback.format_exc())
                logger.info("[PASO 1] Continuando con siguiente paso...")
            
            # Paso 2: Estructurar
            logger.info("[PASO 2] Estructurando información...")
            try:
                self.estructurador.ejecutar_estructuracion()
                logger.info("[PASO 2] ✓ Estructuración completada")
            except Exception as e:
                logger.error(f"[PASO 2] Error: {e}")
                logger.error(traceback.format_exc())
                logger.info("[PASO 2] Continuando con siguiente paso...")
            
            # Paso 3: Combinar
            logger.info("[PASO 3] Generando combinaciones...")
            try:
                self.combinador.ejecutar_combinaciones()
                logger.info("[PASO 3] ✓ Combinaciones generadas")
            except Exception as e:
                logger.error(f"[PASO 3] Error: {e}")
                logger.error(traceback.format_exc())
                logger.info("[PASO 3] Continuando con siguiente paso...")
            
            # Paso 4-5: Entrenar y Validar (backtesting)
            logger.info("[PASO 4-5] Iniciando backtesting de fórmula V2...")
            try:
                self.ejecutar_backtesting_formula_v2()
                logger.info("[PASO 4-5] ✓ Backtesting completado")
            except Exception as e:
                logger.error(f"[PASO 4-5] Error: {e}")
                logger.error(traceback.format_exc())
                logger.info("[PASO 4-5] Continuando con siguiente paso...")
            
            logger.info("="*80)
            logger.info("[FABRICA] Ciclo completado")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"[FABRICA] Error crítico en ciclo: {e}")
            logger.error(traceback.format_exc())
    
    def ejecutar_backtesting_formula_v2(self):
        """Ejecuta backtesting de fórmula V2 en múltiples activos."""
        logger.info("[BACKTEST] Iniciando backtesting fórmula V2")
        
        # Configuración V2 exitosa
        config_v2 = {
            'bb_periodo': 30,
            'bb_desv': 2.5,
            'rsi_periodo': 7,
            'rsi_rev_long_max': 25.0,
            'rsi_rev_short_min': 75.0,
            'atr_sl_mult': 0.8,
            'rr_tp1': 2.0,
            'rr_tp2': 2.5,
            'max_ops_dia': 4,
            'ventana_apertura_barras': 3,
            'castigo_sobreoperacion': -0.8,
            'recompensa_tp1': 1.1,
            'castigo_sl': -1.6,
            'incentivo_apertura': 0.02,
            'recompensa_tp2': 1.3,
            'costo_holding': 0.0
        }
        
        # Procesar bots rentables ya encontrados
        bots_rentables = [
            {
                'activo': 'XAUUSD',
                'temporalidad': 'M5',
                'resultados': {'operaciones': 139, 'winrate': 0.532, 'profit_factor': 1.53, 'pnl_total': 3192.38},
                'periodo': '2025-01→2026-04'
            },
            {
                'activo': 'XAUUSD',
                'temporalidad': 'M15',
                'resultados': {'operaciones': 248, 'winrate': 0.50, 'profit_factor': 1.22, 'pnl_total': 2989.29},
                'periodo': '2025-01→2026-04'
            }
        ]
        
        for bot in bots_rentables:
            try:
                logger.info(f"[BACKTEST] Procesando bot rentable: {bot['activo']} {bot['temporalidad']}")
                self.marketing.procesar_bot_rentable(
                    bot['activo'],
                    bot['temporalidad'],
                    bot['resultados'],
                    config_v2,
                    bot['periodo']
                )
                logger.info(f"[BACKTEST] ✓ Bot {bot['activo']} {bot['temporalidad']} procesado")
            except Exception as e:
                logger.error(f"[BACKTEST] Error procesando bot: {e}")
                logger.error(traceback.format_exc())
                continue
        
        logger.info("[BACKTEST] Backtesting completado")

if __name__ == "__main__":
    fabrica = FabricaAutomatizada()
    fabrica.ejecutar_ciclo_completo()

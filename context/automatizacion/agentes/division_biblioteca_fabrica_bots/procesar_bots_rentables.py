#!/usr/bin/env python3
"""
Procesar Bots Rentables Existentes
==================================
Genera reportes de marketing para los bots rentables ya encontrados.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root))

from automatizacion.agentes.division_biblioteca_fabrica_bots.agente_marketing_bots import AgenteMarketingBots

marketing = AgenteMarketingBots()

# Bot 1: XAUUSD M5 V2
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

# Bot 1: Atlas (XAUUSD M5)
marketing.procesar_bot_rentable(
    'XAUUSD', 'M5',
    {'operaciones': 139, 'winrate': 0.532, 'profit_factor': 1.53, 'pnl_total': 3192.38},
    config_v2,
    '2025-01→2026-04'
)

# Bot 2: XAUUSD M15 V2
marketing.procesar_bot_rentable(
    'XAUUSD', 'M15',
    {'operaciones': 248, 'winrate': 0.50, 'profit_factor': 1.22, 'pnl_total': 2989.29},
    config_v2,
    '2025-01→2026-04'
)

print("Bots rentables procesados y reportes generados")

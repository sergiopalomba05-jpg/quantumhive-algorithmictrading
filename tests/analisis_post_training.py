#!/usr/bin/env python3
"""
analisis_post_training.py
Analiza métricas de los 4 bots ONNX tras descarga desde Kaggle.
Genera: equity curve, drawdown por régimen, PF por bot, heatmap de correlación.
"""
import json, sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

REPORTE_PATH = Path("C:/Users/sergio/BotsCuanticos/datos/reporte_kaggle.json")
HISTORIAL_PATH = Path("C:/Users/sergio/BotsCuanticos/datos/historial_trades_ea.csv")
OUTPUT_DIR = Path("C:/Users/sergio/BotsCuanticos/datos/analisis")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_reporte():
    if not REPORTE_PATH.exists():
        print(f"[WARN] No existe {REPORTE_PATH}")
        return None
    with open(REPORTE_PATH) as f:
        return json.load(f)

def equity_curve_from_pnl(pnl_series: pd.Series):
    equity = (1 + pnl_series).cumprod()
    peak = equity.expanding().max()
    drawdown = (equity - peak) / peak
    return equity, drawdown

def analyze_bot(name, stats):
    wr = stats.get('winrate', 0)
    pf = stats.get('profit_factor', 0)
    mr = stats.get('mean_reward', 0)
    trades = stats.get('trades', 0)
    ret = stats.get('total_return_pct', 0)
    
    score = 0
    if wr > 0.55: score += 1
    if pf > 1.3: score += 1
    if mr > 0: score += 1
    if trades > 100: score += 1
    
    verdict = "RENTABLE" if score >= 3 else "MARGINAL" if score == 2 else "DEBIL"
    
    return {
        'bot': name,
        'winrate': wr,
        'profit_factor': pf,
        'mean_reward': mr,
        'trades': trades,
        'total_return_pct': ret,
        'score': score,
        'verdict': verdict
    }

def plot_equity(equity, drawdown, title, save_path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(equity.index, equity.values, color='green', linewidth=1)
    ax1.set_title(f'{title} — Equity Curve')
    ax1.set_ylabel('Multiplicador de Capital')
    ax1.grid(True, alpha=0.3)
    
    ax2.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.5)
    ax2.set_title('Drawdown')
    ax2.set_ylabel('DD %')
    ax2.set_xlabel('Trade #')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[PLOT] {save_path}")

def main():
    reporte = load_reporte()
    if reporte is None:
        print("No hay reporte para analizar. Descargá reporte_kaggle.json de Kaggle.")
        sys.exit(1)
    
    bots = reporte.get('bots', {})
    rows = []
    
    print("\n" + "="*70)
    print("DIAGNOSTICO POST-ENTRENAMIENTO")
    print("="*70)
    print(f"Timestamp: {reporte.get('timestamp', 'N/A')}")
    print(f"Device:    {reporte.get('device', 'N/A')}")
    print(f"Filas:     {reporte.get('filas_dataset', 0):,}")
    print("-"*70)
    
    for name, stats in bots.items():
        analysis = analyze_bot(name, stats)
        rows.append(analysis)
        print(f"\n{name.upper()}")
        print(f"  WinRate:        {analysis['winrate']:.2%}")
        print(f"  Profit Factor:  {analysis['profit_factor']}")
        print(f"  Mean Reward:    {analysis['mean_reward']:.4f}")
        print(f"  Trades eval:    {analysis['trades']}")
        print(f"  Total Return:   {analysis['total_return_pct']:.2f}%")
        print(f"  Score:          {analysis['score']}/4")
        print(f"  VEREDICTO:      {analysis['verdict']}")
    
    df = pd.DataFrame(rows)
    csv_path = OUTPUT_DIR / "diagnostico_bots.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[OK] CSV guardado: {csv_path}")
    
    # Si hay historial de trades EA, analizar
    if HISTORIAL_PATH.exists():
        print("\n--- Analisis de trades EA ---")
        trades = pd.read_csv(HISTORIAL_PATH)
        print(f"Trades registrados: {len(trades)}")
        if 'pnl' in trades.columns:
            equity = (1 + trades['pnl'] / 100).cumprod()  # asume pnl en %
            peak = equity.expanding().max()
            dd = (equity - peak) / peak
            print(f"Max Drawdown: {dd.min():.2%}")
            print(f"Return total: {equity.iloc[-1] - 1:.2%}")
    
    print("\n" + "="*70)
    print("RECOMENDACIONES PARA V3:")
    print("="*70)
    weak = [r for r in rows if r['verdict'] == 'DEBIL']
    if weak:
        print(f"Bots DEBILES ({len(weak)}): {', '.join(r['bot'] for r in weak)}")
        print("  -> Aumentar horizon a 240 (4h), agregar costos reales, reentrenar.")
    else:
        print("Ningun bot marcado como DEBIL. Validar en backtest walk-forward.")
    
    marginal = [r for r in rows if r['verdict'] == 'MARGINAL']
    if marginal:
        print(f"Bots MARGINALES ({len(marginal)}): {', '.join(r['bot'] for r in marginal)}")
        print("  -> Optimizar hiperparametros (lr, batch_size), agregar regularizacion.")
    
    print("="*70)

if __name__ == '__main__':
    main()

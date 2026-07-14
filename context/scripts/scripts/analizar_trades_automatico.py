"""
Analisis automatico de trades_historial.csv
Detecta errores del bot y propone fixes.
Auto-ejecutado durante sesion nocturna.
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAIZ = Path("C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING")
CSV_PATH = RAIZ / "modelos" / "trades_historial.csv"
REPORT_PATH = RAIZ / "modelos" / "analisis_errores_bot.md"

if not CSV_PATH.exists():
    print("[SKIP] trades_historial.csv no existe. Backtest no ejecutado aun.")
    exit(0)

df = pd.read_csv(CSV_PATH)
print(f"[OK] Cargados {len(df)} trades desde {CSV_PATH}")

reporte = ["# Analisis Automatico de Trades — Errores del Bot", "", f"**Fecha:** {pd.Timestamp.now()}", f"**Total trades:** {len(df)}", ""]

# 1. Trades consecutivos perdedores (>3 seguidos)
if 'resultado' in df.columns:
    df['perdedor'] = df['resultado'].str.contains('loss|perdida|-', case=False, na=False)
    consecutivos = []
    count = 0
    for i, p in enumerate(df['perdedor']):
        if p:
            count += 1
        else:
            if count > 3:
                consecutivos.append((i-count, count))
            count = 0
    if consecutivos:
        reporte.append("## 1. Streaks Perdedores Consecutivos")
        reporte.append(f"Encontrados {len(consecutivos)} streaks de >3 perdidas consecutivas:")
        for start, length in consecutivos[:5]:
            reporte.append(f"- Desde trade #{start}: {length} perdidas seguidas")
        reporte.append("")
        reporte.append("**Fix propuesto:** Revisar entorno — posible sobre-optimizacion o falta de castigo por streaks.")
    else:
        reporte.append("## 1. Streaks Perdedores")
        reporte.append("No se detectaron streaks de >3 perdidas consecutivas. OK.")
    reporte.append("")

# 2. Trades por SL ajustado vs volatilidad
if all(c in df.columns for c in ['sl_pips', 'atr_14']):
    df['sl_vs_atr'] = df['sl_pips'] / df['atr_14']
    ajustados = df[df['sl_vs_atr'] < 1.0]
    reporte.append("## 2. SL vs ATR (Volatilidad)")
    reporte.append(f"Trades con SL < 1x ATR: {len(ajustados)} ({len(ajustados)/len(df)*100:.1f}%)")
    if len(ajustados) > len(df) * 0.3:
        reporte.append("**ALERTA:** Mas del 30% de trades tienen SL muy ajustado. Aumentar multiplicador ATR a 2.0-2.5.")
    else:
        reporte.append("SL apropiado para la mayoria de trades.")
    reporte.append("")

# 3. Distribucion horaria (horario NY)
if 'hora' in df.columns or 'timestamp' in df.columns:
    time_col = 'hora' if 'hora' in df.columns else 'timestamp'
    df['hora_num'] = pd.to_datetime(df[time_col], errors='coerce').dt.hour
    fuera_ny = df[(df['hora_num'] < 13) | (df['hora_num'] > 22)]  # UTC-4/EST
    reporte.append("## 3. Horario de Operacion (Sesion NY)")
    reporte.append(f"Trades fuera de sesion NY (13-22h UTC): {len(fuera_ny)} ({len(fuera_ny)/len(df)*100:.1f}%)")
    if len(fuera_ny) > 0:
        reporte.append("**Fix:** Reforzar filtro horario en entorno RL o EA MQL5.")
    reporte.append("")

# 4. Metricas globales
if 'resultado' in df.columns:
    wins = df[df['resultado'].str.contains('win|ganancia', case=False, na=False)]
    losses = df[df['resultado'].str.contains('loss|perdida', case=False, na=False)]
    winrate = len(wins) / len(df) * 100 if len(df) > 0 else 0
    reporte.append("## 4. Metricas Globales")
    reporte.append(f"- Winrate: {winrate:.1f}%")
    reporte.append(f"- Wins: {len(wins)} | Losses: {len(losses)}")
    if 'pnl' in df.columns:
        total_pnl = df['pnl'].sum()
        reporte.append(f"- PnL total: {total_pnl:.2f}")
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if len(df[df['pnl'] > 0]) > 0 else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if len(df[df['pnl'] < 0]) > 0 else 0
        reporte.append(f"- Avg win: {avg_win:.2f} | Avg loss: {avg_loss:.2f}")
        if avg_loss != 0:
            rr = abs(avg_win / avg_loss)
            reporte.append(f"- R:R promedio: 1:{rr:.2f}")
    reporte.append("")

# 5. Recomendaciones
reporte.append("## 5. Recomendaciones Automaticas")
reporte.append("1. Verificar entorno RL: castigo por streaks perdedores (< -0.05 por trade consecutivo)")
reporte.append("2. Ajustar SL: usar ATR(14) x 2.0 en vez de x 1.5 para mas tolerancia")
reporte.append("3. Filtro horario: solo operar 14:30-21:30 UTC (apertura NY + sesion)")
reporte.append("4. Revisar reward shaping: castigo por inactividad excesiva (-0.01/hora max)")
reporte.append("")

# Guardar
REPORT_PATH.write_text("\n".join(reporte), encoding="utf-8")
print(f"[OK] Reporte guardado en: {REPORT_PATH}")
print("\n--- RESUMEN ---")
for line in reporte[:20]:
    print(line)

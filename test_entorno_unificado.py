import sys
sys.path.insert(0, r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING")

import numpy as np
import pandas as pd
from nucleo.entornos.entorno_hibrido_unificado import EntornoHibridoUnificado, ConfigHibrido

# Datos sintéticos NY
n = 2000
idx = pd.date_range('2024-01-01 13:30', periods=n, freq='15min')
c = 35000 + np.cumsum(np.random.randn(n) * 5)
o = c + np.random.randn(n) * 2
h = np.maximum(np.maximum(c, o), np.maximum(c, o) + np.abs(np.random.randn(n)) * 3)
l = np.minimum(np.minimum(c, o), np.minimum(c, o) - np.abs(np.random.randn(n)) * 3)

df = pd.DataFrame({'open': o, 'high': h, 'low': l, 'close': c}, index=idx)
df['hora'] = df.index.hour + df.index.minute / 60.0
df = df[(df['hora'] >= 13.5) & (df['hora'] <= 21.0)].drop(columns=['hora'])

# Indicadores
from nucleo.indicadores import calcular_rsi, calcular_bollinger, calcular_atr
bb = calcular_bollinger(df)
df['bb_sup'] = bb['bb_superior']
df['bb_inf'] = bb['bb_inferior']
df['bb_media'] = bb['bb_media']
df['bbw'] = bb['bbw']
df['pb'] = bb['porcentaje_b']
df['rsi'] = calcular_rsi(df)
df['atr'] = calcular_atr(df)
df['ema50'] = df['close'].astype(float).ewm(span=50, adjust=False).mean()
df['pend_ema'] = df['ema50'].diff().fillna(0)
bbw = df['bbw'].astype(float)
p20 = bbw.rolling(200, min_periods=20).quantile(0.2)
p80 = bbw.rolling(200, min_periods=20).quantile(0.8)
df['bbw_estado'] = np.where(bbw < p20, -1.0, np.where(bbw > p80, 1.0, 0.0))
df['tendencia_h1'] = 0.0
df['conf_m5'] = 0.0
df['conf_m1'] = 0.0
for col in ['m5_bb_sup', 'm5_bb_inf', 'm5_rsi', 'm1_bb_sup', 'm1_bb_inf', 'm1_rsi']:
    df[col] = df.get(col, 0.0)
df = df.dropna()

# El entorno del nucleo computa internamente desde OHLCV
m15 = df[['open', 'high', 'low', 'close']].copy()

env = EntornoHibridoUnificado(m15, m15, m15, m15)
obs, _ = env.reset()
print(f"Obs shape: {obs.shape}, space: {env.observation_space.shape}")

# Simular 500 steps con accion random
for step in range(500):
    action = env.action_space.sample()
    obs, reward, done, trunc, info = env.step(action)
    if done:
        break

m = env.calcular_metricas()
print(f"\nMetricas: Ops={m['operaciones']} WR={m['winrate']:.1%} PF={m['profit_factor']:.2f} PnL={m['pnl_total']:.0f}")
print("TEST PASADO")

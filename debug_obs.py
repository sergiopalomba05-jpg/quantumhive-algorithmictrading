import sys, os
sys.path.insert(0, r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\notebooks")

import numpy as np
import pandas as pd
from pathlib import Path

# Copiar solo las funciones necesarias para testear
import importlib.util
spec = importlib.util.spec_from_file_location("kaggle", r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\notebooks\kaggle_unificado_v3.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("[DEBUG] Cargando datos...")
df_m15, df_m5, df_m1, df_h1 = mod.generar_dataset_unificado()
print(f"[DEBUG] M15: {len(df_m15)} filas, cols: {list(df_m15.columns)}")
print(f"[DEBUG] M15 index: {df_m15.index[0]} -> {df_m15.index[-1]}")
print(f"[DEBUG] M15 dtypes:\n{df_m15.dtypes}")
print(f"[DEBUG] M15 NaN count:\n{df_m15.isna().sum()}")

print("\n[DEBUG] Creando entorno con primeras 5000 filas...")
env = mod.EntornoHibridoUnificado(
    df_m15.iloc[:5000].copy(),
    df_m5.iloc[:5000].copy(),
    df_m1.iloc[:5000].copy(),
    df_h1.iloc[:5000].copy(),
)

obs, info = env.reset(seed=42)
print(f"[DEBUG] Obs inicial: {obs}")
print(f"[DEBUG] NaN en obs inicial: {np.isnan(obs).sum()}")

for step in range(200):
    obs, reward, done, truncated, info = env.step(0)
    if np.isnan(obs).any():
        print(f"[DEBUG] NaN detectado en step {step}: {obs}")
        break
    if done or truncated:
        print(f"[DEBUG] Episodio terminado en step {step}")
        break
else:
    print(f"[DEBUG] 200 steps sin NaN")

print("\n[DEBUG] Verificando precomputados del entorno:")
print(f"  bb media NaN: {mod.calcular_bollinger(df_m15['close'])['media'].isna().sum()}")
print(f"  rsi NaN: {mod.calcular_rsi(df_m15['close']).isna().sum()}")
print(f"  atr NaN: {mod.calcular_atr(df_m15).isna().sum()}")
print(f"  bbw estado NaN: {np.isnan(env.bbw_estado.values).sum()}")
print("[DEBUG] Fin")

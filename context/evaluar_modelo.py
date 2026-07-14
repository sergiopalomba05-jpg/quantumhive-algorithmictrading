import sys, os, random, json, warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

# Agregar path para importar el modulo
sys.path.insert(0, r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\notebooks")

import numpy as np
from stable_baselines3 import PPO

import kaggle_unificado_v3 as mod

print("[EVAL] Cargando datos...")
df_m15, df_m5, df_m1, df_h1 = mod.generar_dataset_unificado()
len_df = len(df_m15)
print(f"[EVAL] Dataset: {len_df:,} filas")

print("[EVAL] Cargando modelo...")
model_path = r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\modelos\modelo_final"
model = PPO.load(model_path)
print(f"[EVAL] Modelo cargado: {model_path}")

N_EVAL_EPISODIOS = 100
resultados = []
for ep in range(N_EVAL_EPISODIOS):
    start = random.randint(0, max(0, len_df - 5000))
    end = start + 5000
    env = mod.EntornoHibridoUnificado(
        df_m15.iloc[start:end].copy(),
        df_m5.iloc[start:end].copy(),
        df_m1.iloc[start:end].copy(),
        df_h1.iloc[start:end].copy(),
    )
    obs, info = env.reset(seed=ep)
    terminated, truncated = False, False
    while not (terminated or truncated):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
    
    metricas = env.calcular_metricas()
    resultados.append({
        "ep": ep,
        "pnl": metricas["pnl_total"],
        "ops": metricas["operaciones"],
        "wr": metricas["winrate"],
        "reward": reward,
    })
    if ep % 20 == 0:
        print(f"[EVAL] Ep={ep} | PnL={metricas['pnl_total']:.0f} | Ops={metricas['operaciones']} | WR={metricas['winrate']:.1%}")

wrs = [r["wr"] for r in resultados if r["ops"] > 0]
pnl_total = sum(r["pnl"] for r in resultados)
avg_ops = sum(r["ops"] for r in resultados) / len(resultados)
print(f"\n[EVAL FINAL] WR medio: {np.mean(wrs):.1%} | PnL total: {pnl_total:.0f} | Ops/ep: {avg_ops:.1f}")

# Reporte
reporte = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "eval_episodios": N_EVAL_EPISODIOS,
    "avg_winrate": float(np.mean(wrs)) if wrs else 0.0,
    "avg_ops": float(avg_ops),
    "total_pnl": float(pnl_total),
}
with open(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\reporte_evaluacion.json", "w") as f:
    json.dump(reporte, f, indent=2)
print("\n[OK] Reporte guardado en: reporte_evaluacion.json")

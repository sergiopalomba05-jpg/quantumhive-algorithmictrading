import sys, warnings, traceback, json
from datetime import datetime, timezone
warnings.filterwarnings("ignore")
sys.path.insert(0, r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\notebooks")

import numpy as np
from stable_baselines3 import PPO
import kaggle_unificado_v3 as mod

try:
    print("[EVAL] Cargando datos...")
    df_m15, df_m5, df_m1, df_h1 = mod.generar_dataset_unificado()
    len_df = len(df_m15)
    print(f"[EVAL] Dataset OK: {len_df:,} filas")

    print("[EVAL] Cargando modelo...")
    model_path = r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\modelos\modelo_final"
    model = PPO.load(model_path)
    print("[EVAL] Modelo cargado OK")

    N = 20  # Reducido para rapidez
    resultados = []
    for ep in range(N):
        start = ep * 5000 % max(1, len_df - 5000)
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
        resultados.append({"pnl": metricas["pnl_total"], "ops": metricas["operaciones"], "wr": metricas["winrate"]})
        if ep % 5 == 0:
            print(f"[EVAL] Ep={ep} | PnL={metricas['pnl_total']:.0f} | Ops={metricas['operaciones']} | WR={metricas['winrate']:.1%}")

    wrs = [r["wr"] for r in resultados if r["ops"] > 0]
    pnls = [r["pnl"] for r in resultados]
    ops = [r["ops"] for r in resultados]

    print("\n" + "="*50)
    print("RESULTADOS EVALUACION (20 episodios)")
    print(f"  WR medio:      {np.mean(wrs):.1%}" if wrs else "  WR medio: N/A (sin ops)")
    print(f"  PnL total:     {sum(pnls):.0f}")
    print(f"  PnL promedio:  {np.mean(pnls):.0f}")
    print(f"  Ops/ep:        {np.mean(ops):.1f}")
    print(f"  Ops totales:   {sum(ops)}")
    print("="*50)

    reporte = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "eval_episodios": N,
        "avg_winrate": float(np.mean(wrs)) if wrs else 0.0,
        "avg_ops": float(np.mean(ops)),
        "total_pnl": float(sum(pnls)),
        "avg_pnl": float(np.mean(pnls)),
    }
    with open(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\reporte_evaluacion.json", "w") as f:
        json.dump(reporte, f, indent=2)
    print("[OK] Reporte guardado: reporte_evaluacion.json")

except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    traceback.print_exc()

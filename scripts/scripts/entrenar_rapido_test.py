#!/usr/bin/env python3
"""
Entrenamiento Rapido de Validacion — Entorno Hibrido v3.1
===========================================================
Entrena PPO por 100K steps con el entorno corregido (anti-sobreoperacion)
para validar que no hay errores de runtime antes de Kaggle 2M steps.

Uso:
    python scripts/entrenar_rapido_test.py

Requiere:
    - datasets/US30_M15_2022_2024.csv
    - stable-baselines3, gymnasium, torch
"""

import sys, os, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from nucleo.entornos.entorno_hibrido_unificado import EntornoHibridoUnificado, ConfigHibrido

DATA = root / "datasets" / "US30_M15_2022_2024.csv"

def _cargar_csv():
    if not DATA.exists():
        raise FileNotFoundError(f"NO EXISTE: {DATA}")
    sep = ","
    with open(DATA, "r", encoding="utf-8") as fh:
        sample = fh.read(4096)
    for cand in [";", "\t"]:
        if cand in sample.split("\n")[0]:
            sep = cand
            break
    df = pd.read_csv(
        DATA, sep=sep, engine="c",
        low_memory=True,
    )
    # Normalizar nombres MetaTrader (<DATE>, <TIME>, <OPEN>...)
    df.columns = [c.lower().strip("<>") for c in df.columns]
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "date" in df.columns and "time" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce")
    elif "time" in df.columns:
        df["datetime"] = pd.to_datetime(df["time"], errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(df.index, errors="coerce")
    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.set_index("datetime").sort_index()
    for c in ("open", "high", "low", "close"):
        df[c] = df[c].astype(np.float32)
    return df

def main():
    print("[LOAD] Cargando datos M15...")
    df = _cargar_csv()
    # Filtrar NY sesion
    df["hora"] = df.index.hour
    df = df[(df["hora"] >= 14) & (df["hora"] <= 21)]
    print(f"[LOAD] {len(df):,} filas | {df.index[0]} -> {df.index[-1]}")

    cfg = ConfigHibrido()  # usa defaults v3.2 estrictos
    n_envs = 4
    def make_env():
        start = np.random.randint(0, max(1, len(df) - 5000))
        return EntornoHibridoUnificado(df.iloc[start:start + 5000].copy(), cfg=cfg)

    env = DummyVecEnv([make_env for _ in range(n_envs)])
    print("[TRAIN] Iniciando PPO 100K steps | Device=auto...")
    model = PPO("MlpPolicy", env, verbose=1, n_steps=2048, batch_size=64,
                learning_rate=3e-4, gamma=0.995, gae_lambda=0.95,
                ent_coef=0.01, vf_coef=0.5, max_grad_norm=0.5)
    model.learn(total_timesteps=100_000)
    model.save(str(root / "modelos" / "modelo_test_100k"))
    print("[OK] Entrenamiento 100K completado. Modelo guardado en modelos/modelo_test_100k")

    # Evaluacion rapida en ultimo env para ver metricas
    print("[EVAL] Evaluando entorno final...")
    e = make_env()
    obs, _ = e.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = e.step(int(action))
        done = terminated or truncated
    m = e.calcular_metricas()
    print(f"[EVAL] Ops={m['operaciones']} | WR={m['winrate']:.1%} | PF={m['profit_factor']:.2f} | PnL=${m['pnl_total']:.2f}")

if __name__ == "__main__":
    main()

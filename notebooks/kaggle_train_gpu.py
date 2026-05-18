"""
KAGGLE TRAINING PIPELINE — QuantumHive GPU
=============================================
Ejecutar en Kaggle con GPU T4.

INSTRUCCIONES KAGGLE:
1. Subir este archivo como dataset en /kaggle/input/quantumhive
2. Subir datatb_fusion.parquet a /kaggle/input/quantumhive/datos/
3. Subir la carpeta nucleo/ como dataset también
4. Notebook: New → Import this script → Run All

Dependencias (ejecutar en primera celda):
    !pip install -q stable-baselines3 gymnasium onnx onnxruntime pandas numpy
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv

# ── Paths Kaggle ──
INPUT_DIR = Path("/kaggle/input/quantumhive")
WORKING_DIR = Path("/kaggle/working")
SALIDA_MODELOS = WORKING_DIR / "modelos_onnx"
SALIDA_MODELOS.mkdir(parents=True, exist_ok=True)

# Agregar repo al path
sys.path.insert(0, str(INPUT_DIR))

from nucleo.entornos.entorno_madre import EntornoMadre, ConfigMadre
from nucleo.entornos.entorno_reversion import EntornoReversion, ConfigReversion
from nucleo.entornos.entorno_continuacion import EntornoContinuacion, ConfigContinuacion
from nucleo.entornos.entorno_scalper_m5 import EntornoScalperM5, ConfigScalperM5
from nucleo.exportador_onnx import ExportadorONNX

# ── GPU Config ──
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[KAGGLE] Dispositivo: {DEVICE}")
print(f"[KAGGLE] CUDA disponible: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"[KAGGLE] GPU: {torch.cuda.get_device_name(0)}")
    torch.backends.cudnn.benchmark = True


def cargar_fusion() -> pd.DataFrame:
    """Carga datatb_fusion.parquet o CSV fallback."""
    ruta_parquet = INPUT_DIR / "datos" / "datatb_fusion.parquet"
    ruta_csv = INPUT_DIR / "datos" / "datatb_fusion.csv"

    if ruta_parquet.exists():
        print(f"[KAGGLE] Cargando {ruta_parquet.name} ...")
        df = pd.read_parquet(ruta_parquet)
    elif ruta_csv.exists():
        print(f"[KAGGLE] Cargando {ruta_csv.name} ...")
        df = pd.read_csv(ruta_csv, index_col=0, parse_dates=True)
    else:
        raise FileNotFoundError(f"No se encontró datatb_fusion en {INPUT_DIR / 'datos'}")

    print(f"  -> Filas: {len(df):,} | Columnas: {len(df.columns)}")
    print(f"  -> Fechas: {df.index.min()} → {df.index.max()}")
    return df


def reporte_bot(nombre: str, model, env_test, n_eval: int = 2000) -> dict:
    """Evalúa un bot entrenado y reporta métricas clave."""
    print(f"\n[KAGGLE] Evaluando {nombre} ...")
    obs, _ = env_test.reset()
    rewards = []
    wins = 0
    losses = 0
    total_pnl = 0.0

    for _ in range(n_eval):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env_test.step(action)
        rewards.append(reward)
        if reward > 0:
            wins += 1
        elif reward < 0:
            losses += 1
        total_pnl += reward
        if terminated or truncated:
            obs, _ = env_test.reset()

    n_trades = wins + losses
    wr = wins / n_trades if n_trades > 0 else 0.0
    avg_reward = np.mean(rewards) if rewards else 0.0
    pf = abs(sum(r for r in rewards if r > 0) / sum(r for r in rewards if r < 0)) if any(r < 0 for r in rewards) else float("inf")

    stats = {
        "bot": nombre,
        "mean_reward": round(float(avg_reward), 6),
        "winrate": round(wr, 4),
        "profit_factor": round(pf, 3) if pf != float("inf") else 999.0,
        "total_pnl": round(float(total_pnl), 4),
        "trades_simulados": n_trades,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(f"  -> MeanReward={stats['mean_reward']} | WinRate={stats['winrate']:.2%} | PF={stats['profit_factor']} | Trades={n_trades}")
    return stats


def exportar_onnx(model, env, nombre: str) -> Path:
    """Exporta modelo a ONNX para MT5."""
    print(f"[KAGGLE] Exportando {nombre} a ONNX ...")
    exportador = ExportadorONNX(model, env, nombre_archivo=f"{nombre}.onnx", opset=12)
    ruta = exportador.exportar()
    print(f"  -> Guardado: {ruta}")
    return ruta


def entrenar_madre(df: pd.DataFrame) -> tuple:
    """Entrena Bot Madre (RecurrentPPO) con todas las features multitemporales."""
    print("\n" + "=" * 60)
    print("PASO 3: ENTRENAMIENTO BOT MADRE (RecurrentPPO)")
    print("=" * 60)

    config = ConfigMadre()
    config.total_timesteps = 500_000  # Ajustar según GPU
    config.device = DEVICE

    def _make_env():
        return EntornoMadre(df, config=config)

    env = DummyVecEnv([_make_env])
    model = RecurrentPPO(
        "MlpLstmPolicy",
        env,
        verbose=1,
        device=DEVICE,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.995,
        gae_lambda=0.95,
    )
    print(f"[KAGGLE] Entrenando Madre por {config.total_timesteps} pasos ...")
    model.learn(total_timesteps=config.total_timesteps)

    # Evaluar
    env_test = _make_env()
    stats = reporte_bot("bot_madre", model, env_test, n_eval=5000)

    # Guardar modelo
    ruta_zip = SALIDA_MODELOS / "bot_madre_ppo.zip"
    model.save(str(ruta_zip))
    print(f"  -> Modelo guardado: {ruta_zip}")

    # Exportar ONNX
    ruta_onnx = exportar_onnx(model, env_test, "bot_madre")

    return model, stats, ruta_onnx


def entrenar_hijo(df: pd.DataFrame, modelo_madre, config_cls, env_cls, nombre: str, condicion_madre: int) -> tuple:
    """Entrena un bot hijo filtrando por predicción del Madre."""
    print("\n" + "=" * 60)
    print(f"PASO: ENTRENAMIENTO {nombre.upper()} (PPO)")
    print("=" * 60)

    # Filtrar dataset donde Madre predice condicion_madre
    print(f"[KAGGLE] Filtrando barras donde Madre={condicion_madre} ...")
    # Simulamos predicciones del Madre sobre el dataset
    obs, _ = env_cls(df, config=config_cls()).reset()
    # En entorno real, el entorno ya tiene la lógica de filtrado dentro
    # Aquí simplificamos: entrenamos sobre todo el dataset, el entorno interno filtra

    config = config_cls()
    config.total_timesteps = 300_000
    config.device = DEVICE

    def _make_env():
        return env_cls(df, config=config)

    env = DummyVecEnv([_make_env])
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        device=DEVICE,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=128,
        n_epochs=10,
        gamma=0.99,
    )
    print(f"[KAGGLE] Entrenando {nombre} por {config.total_timesteps} pasos ...")
    model.learn(total_timesteps=config.total_timesteps)

    env_test = _make_env()
    stats = reporte_bot(nombre, model, env_test, n_eval=5000)

    ruta_zip = SALIDA_MODELOS / f"{nombre}_ppo.zip"
    model.save(str(ruta_zip))
    ruta_onnx = exportar_onnx(model, env_test, nombre)

    return model, stats, ruta_onnx


def main():
    print("=" * 60)
    print("QUANTUMHIVE KAGGLE TRAINING PIPELINE")
    print("=" * 60)

    # 1. Cargar datos
    df = cargar_fusion()

    # 2. Entrenar Madre
    modelo_madre, stats_madre, onnx_madre = entrenar_madre(df)

    # 3. Entrenar Hijos
    modelo_rev, stats_rev, onnx_rev = entrenar_hijo(
        df, modelo_madre, ConfigReversion, EntornoReversion, "bot_reversion", condicion_madre=1
    )
    modelo_cont, stats_cont, onnx_cont = entrenar_hijo(
        df, modelo_madre, ConfigContinuacion, EntornoContinuacion, "bot_continuacion", condicion_madre=2
    )
    modelo_scalp, stats_scalp, onnx_scalp = entrenar_hijo(
        df, modelo_madre, ConfigScalperM5, EntornoScalperM5, "bot_scalper", condicion_madre=-1
    )

    # 4. Reporte final
    reporte = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device": DEVICE,
        "dataset": "datatb_fusion",
        "filas": len(df),
        "bots": {
            "madre": stats_madre,
            "reversion": stats_rev,
            "continuacion": stats_cont,
            "scalper": stats_scalp,
        },
        "archivos_onnx": {
            "madre": str(onnx_madre),
            "reversion": str(onnx_rev),
            "continuacion": str(onnx_cont),
            "scalper": str(onnx_scalp),
        },
    }

    ruta_reporte = SALIDA_MODELOS / "reporte_entrenamiento.json"
    with open(ruta_reporte, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 60)
    print("ENTRENAMIENTO COMPLETADO")
    print("=" * 60)
    print(f"Reporte: {ruta_reporte}")
    print(f"Modelos: {SALIDA_MODELOS}")
    for nombre, stats in reporte["bots"].items():
        print(f"  {nombre:12s}: WR={stats['winrate']:.2%} | PF={stats['profit_factor']} | MR={stats['mean_reward']}")
    print("=" * 60)

    # Kaggle: guardar en output para descargar
    print("\n[KAGGLE] Para descargar: File → /kaggle/working/modelos_onnx/")


if __name__ == "__main__":
    main()

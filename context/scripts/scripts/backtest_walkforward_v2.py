"""
BACKTEST WALK-FORWARD v2 — EntornoHibridoUnificado nativo
QuantumHive — Elite Standard

Usa EntornoHibridoUnificado directamente, garantizando que el modelo
reciba EXACTAMENTE las mismas observaciones (10 features normalizadas)
que durante entrenamiento. Elimina el mismatch de entornos del v1.

Salida:
  - modelos/backtest_equity.csv   -> Curva equity minuto a minuto
  - modelos/trades_historial.csv  -> Cada trade con metadatos
  - modelos/backtest_resumen.json -> Metricas agregadas (Sharpe, DD, etc.)
"""

import os
import sys
import json
import math
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from stable_baselines3 import PPO

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_M15 = BASE_DIR / "datasets" / "US30_M15_2022_2024.csv"
CSV_M5  = BASE_DIR / "datasets" / "US30_M5_2022_2024.csv"
CSV_M1  = BASE_DIR / "datasets" / "US30_M1_2022_2024.csv"
CSV_H1  = BASE_DIR / "datasets" / "US30_H1_2022_2024.csv"
MODELO  = BASE_DIR / "modelos" / "modelo_unificado" / "modelo_final.zip"
OUT_DIR = BASE_DIR / "modelos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR))

from nucleo.entornos.entorno_hibrido_unificado import EntornoHibridoUnificado, ConfigHibrido


def _detectar_separador(ruta: Path) -> str:
    """Detecta separador CSV leyendo muestra."""
    with open(ruta, "r", encoding="utf-8") as fh:
        sample = fh.read(4096)
    for cand in ["\t", ";"]:
        if cand in sample.split("\n")[0]:
            return cand
    return ","


def _cargar_csv(ruta: Path, allow_fail: bool = False) -> pd.DataFrame | None:
    """Carga CSV optimizado: dtype float32, solo columnas necesarias."""
    if not ruta.exists():
        if allow_fail:
            print(f"  [SKIP] No existe: {ruta.name}")
            return None
        raise FileNotFoundError(f"NO EXISTE: {ruta}")

    print(f"  [OK] Leyendo {ruta.name} ...")
    cols_default = ["time", "open", "high", "low", "close", "volume"]
    sep = _detectar_separador(ruta)
    dtypes = {c: np.float32 for c in cols_default if c != "time"}

    try:
        df = pd.read_csv(
            ruta,
            sep=sep,
            engine="c",
            usecols=lambda x: x.lower() in [c.lower() for c in cols_default],
            dtype=dtypes,
            low_memory=True,
        )
    except Exception as e:
        if allow_fail:
            print(f"  [SKIP] Error cargando {ruta.name}: {e}")
            return None
        raise

    time_col = None
    for c in df.columns:
        if c.lower() in ("time", "datetime", "date"):
            time_col = c
            break
    if time_col:
        df["datetime"] = pd.to_datetime(df[time_col], errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(df.index, errors="coerce")

    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.set_index("datetime").sort_index()
    for c in ("open", "high", "low", "close"):
        if c in df.columns:
            df[c] = df[c].astype(np.float32)

    print(f"  [OK] {ruta.name}: {len(df):,} filas | {df.index[0]} -> {df.index[-1]}")
    return df


def _resample_desde_m15(df_m15: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Resample M15 a timeframe inferior como fallback."""
    print(f"  [FALLBACK] {freq} -> resample desde M15")
    return df_m15.resample(freq).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }).dropna().astype(np.float32)


def main() -> None:
    print("=" * 70)
    print("BACKTEST WALK-FORWARD v2 — EntornoHibridoUnificado nativo")
    print("=" * 70)

    if not MODELO.exists():
        print(f"[FATAL] Modelo no encontrado: {MODELO}")
        print("[INFO] Entrena primero: python entrenar_unificado.py")
        sys.exit(1)

    modelo = PPO.load(MODELO)
    print(f"[OK] Modelo cargado: {MODELO}")

    # ------------------------------------------------------------------
    # Cargar datos
    # ------------------------------------------------------------------
    print("\n[1/4] Cargando CSVs (optimizado memoria)...")
    df_m15 = _cargar_csv(CSV_M15)
    df_m5  = _cargar_csv(CSV_M5, allow_fail=True)  or _resample_desde_m15(df_m15, "5min")
    df_m1  = _cargar_csv(CSV_M1, allow_fail=True)  or _resample_desde_m15(df_m15, "1min")
    df_h1  = _cargar_csv(CSV_H1, allow_fail=True)  or _resample_desde_m15(df_m15, "1h")

    # ------------------------------------------------------------------
    # Crear entorno nativo
    # ------------------------------------------------------------------
    print("\n[2/4] Instanciando EntornoHibridoUnificado ...")
    cfg = ConfigHibrido()
    env = EntornoHibridoUnificado(
        datos_m15=df_m15,
        datos_m5=df_m5,
        datos_m1=df_m1,
        datos_h1=df_h1,
        cfg=cfg,
    )
    print(f"[OK] Entorno: {len(env.datos):,} velas | Action space: {env.action_space} | Obs shape: {env.observation_space.shape}")

    # ------------------------------------------------------------------
    # Walk-forward loop
    # ------------------------------------------------------------------
    print(f"\n[3/4] Iniciando walk-forward sobre {len(env.datos):,} velas M15 ...")
    print("-" * 70)

    obs, info = env.reset(seed=42)
    terminado = False
    total = len(env.datos)
    checkpoints = [int(total * p) for p in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
    next_checkpoint = 0

    while not terminado:
        action, _ = modelo.predict(obs, deterministic=True)
        obs, reward, terminado, truncado, info = env.step(int(action))

        if env.paso >= checkpoints[next_checkpoint]:
            pct = (next_checkpoint + 1) * 10
            print(f"  {pct:3d}% | Equity=${env.equity:,.2f} | Ops={len(env.historial)} | WR={env.calcular_metricas()['winrate']:.1f}%")
            next_checkpoint = min(next_checkpoint + 1, len(checkpoints) - 1)

    print("-" * 70)

    # ------------------------------------------------------------------
    # Exportar resultados
    # ------------------------------------------------------------------
    print("\n[4/4] Exportando resultados ...")
    equity_df, trades_df, metricas = env.exportar_resultados()

    equity_path = OUT_DIR / "backtest_equity.csv"
    equity_df.to_csv(equity_path, index=False)
    print(f"[OK] Curva equity: {equity_path} ({len(equity_df):,} filas)")

    trades_path = OUT_DIR / "trades_historial.csv"
    if not trades_df.empty:
        trades_df.to_csv(trades_path, index=False)
        print(f"[OK] Trades:       {trades_path} ({len(trades_df)} trades)")
    else:
        print(f"[WARN] Sin trades generados")

    # Resumen JSON
    resumen = {
        "timestamp": datetime.now().isoformat(),
        "modelo": str(MODELO),
        "dataset": {
            "inicio": str(env.datos.index[0]),
            "fin": str(env.datos.index[-1]),
            "velas": len(env.datos),
        },
        "resultados": {
            "balance_inicial": float(cfg.balance_inicial),
            "balance_final": float(env.balance),
            "equity_final": float(env.equity),
            "pnl_total": float(metricas["pnl_total"]),
            "trades_totales": int(metricas["operaciones"]),
            "winrate": float(metricas["winrate"]),
            "profit_factor": float(metricas["profit_factor"]),
            "drawdown_max": float(metricas["drawdown_max"]),
            "sharpe": float(metricas["sharpe"]),
        },
    }
    resumen_path = OUT_DIR / "backtest_resumen.json"
    resumen_path.write_text(json.dumps(resumen, indent=2, default=str), encoding="utf-8")
    print(f"[OK] Resumen JSON: {resumen_path}")

    # ------------------------------------------------------------------
    # Reporte consola
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("RESULTADOS FINALES — WALK-FORWARD v2")
    print("=" * 70)
    print(f"  Fechas:        {env.datos.index[0]} -> {env.datos.index[-1]}")
    print(f"  Velas:         {len(env.datos):,}")
    print(f"  Balance ini:   ${cfg.balance_inicial:,.2f}")
    print(f"  Balance fin:   ${env.balance:,.2f}")
    print(f"  PnL TOTAL:     ${metricas['pnl_total']:+,.2f}")
    print(f"  Retorno:       {metricas['pnl_total'] / cfg.balance_inicial * 100:+.2f}%")
    print(f"  Trades:        {metricas['operaciones']}")
    print(f"  Winrate:       {metricas['winrate']:.1f}%")
    print(f"  Profit factor: {metricas['profit_factor']:.2f}")
    print(f"  Max DD:        {metricas['drawdown_max']:.2f}")
    print(f"  Sharpe (ann):  {metricas['sharpe']:.2f}")
    print("=" * 70)

    # Veredicto
    if metricas["winrate"] > 0.55 and metricas["profit_factor"] > 1.3 and metricas["sharpe"] > 1.0:
        print("\n[PASS] Bot lista para exportar a ONNX y demo MT5.")
    else:
        print("\n[FAIL] Metricas debajo de umbrales. Reentrenar con entorno corregido.")
        print("       Umbrales: WR>55% | PF>1.3 | Sharpe>1.0")


if __name__ == "__main__":
    main()

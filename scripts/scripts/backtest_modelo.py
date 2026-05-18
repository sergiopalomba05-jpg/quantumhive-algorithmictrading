#!/usr/bin/env python3
"""
================================================================================
BACKTEST — Modelo PPO entrenado en Kaggle
================================================================================
Evalúa el modelo sobre datos locales. Versión simplificada y robusta.

Uso:
  cd C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING
  python scripts\backtest_modelo.py
================================================================================
"""
import os, sys, json, math, random, warnings
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE RUTAS
# ═══════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_M15 = BASE_DIR / "datasets" / "US30_M15_2022_2024.csv"
CSV_M5  = BASE_DIR / "datasets" / "US30_M5_2022_2024.csv"
CSV_M1  = BASE_DIR / "datasets" / "US30_M1_2022_2024.csv"
CSV_H1  = BASE_DIR / "datasets" / "US30_H1_2022_2024.csv"
MODELO  = BASE_DIR / "modelos" / "modelo_unificado" / "modelo_final.zip"
OUTPUT  = BASE_DIR / "modelos" / "modelo_unificado" / "backtest_resultados.json"

# ═══════════════════════════════════════════════════════════════════════════════
# INDICADORES
# ═══════════════════════════════════════════════════════════════════════════════
def calcular_rsi(serie: pd.Series, periodo: int = 7) -> pd.Series:
    c = serie.astype(float)
    cambios = c.diff()
    ganancia = cambios.clip(lower=0)
    perdida = (-cambios).clip(lower=0)
    mg = ganancia.ewm(alpha=1 / periodo, adjust=False).mean()
    mp = perdida.ewm(alpha=1 / periodo, adjust=False).mean()
    rs = mg / mp.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def calcular_bollinger(serie: pd.Series, periodo: int = 30, desv: float = 3.0) -> pd.DataFrame:
    c = serie.astype(float)
    media = c.rolling(periodo, min_periods=periodo).mean()
    std = c.rolling(periodo, min_periods=periodo).std(ddof=0)
    sup = media + desv * std
    inf = media - desv * std
    bbw = (sup - inf) / media.replace(0, np.nan)
    pb = (c - inf) / (sup - inf).replace(0, np.nan)
    return pd.DataFrame({"sup": sup, "inf": inf, "media": media, "bbw": bbw, "pb": pb}, index=serie.index)

def calcular_atr(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    c = df["close"].astype(float)
    cp = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - cp).abs(), (l - cp).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / periodo, adjust=False).mean()

def calcular_ema(serie: pd.Series, periodo: int = 50) -> pd.Series:
    return serie.astype(float).ewm(span=periodo, adjust=False).mean()

# ═══════════════════════════════════════════════════════════════════════════════
# PARSING CSV MT5
# ═══════════════════════════════════════════════════════════════════════════════
def _parsear_fecha(row):
    if "time" in row and pd.notna(row["time"]) and str(row["time"]).strip() != "":
        t = str(row["time"]).strip()
        if len(t) == 6 and t.isdigit():
            return f"{t[:2]}:{t[2:4]}:{t[4:]}"
    if "<TIME>" in row and pd.notna(row["<TIME>"]) and str(row["<TIME>"]).strip() != "":
        t = str(int(row["<TIME>"])).zfill(6)
        return f"{t[:2]}:{t[2:4]}:{t[4:]}"
    return "00:00:00"

def _cargar_csv(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        raise FileNotFoundError(f"NO EXISTE: {ruta}")
    print(f"  [OK] Leyendo {ruta.name} ...")
    df = pd.read_csv(ruta, sep=r"[,;\t]", engine="python")
    if "<DATE>" in df.columns:
        df["time"] = df.apply(_parsear_fecha, axis=1)
        df["datetime"] = pd.to_datetime(df["<DATE>"].astype(str) + " " + df["time"], errors="coerce")
        rename = {"<OPEN>": "open", "<HIGH>": "high", "<LOW>": "low", "<CLOSE>": "close", "<TICKVOL>": "volume", "<VOL>": "volume", "<SPREAD>": "spread"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    else:
        df["datetime"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.set_index("datetime").sort_index()
    print(f"  [OK] {ruta.name}: {len(df):,} filas | {df.index[0]} → {df.index[-1]}")
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# SCORE CONFLUENCIA
# ═══════════════════════════════════════════════════════════════════════════════
def score_confluencia(c, o, h, l, bb_sup, bb_inf, rsi):
    score = 0.0
    c = np.asarray(c, dtype=float)
    o = np.asarray(o, dtype=float)
    pb = np.asarray((c - bb_inf) / ((bb_sup - bb_inf) + 1e-9), dtype=float)
    rsi = np.asarray(rsi, dtype=float)
    bbw = np.asarray((bb_sup - bb_inf) / ((bb_sup + bb_inf) / 2 + 1e-9), dtype=float)
    ancho = (h - l) / (c + 1e-9)
    score += np.where(rsi < 30, 0.15, 0)
    score += np.where(rsi > 70, 0.15, 0)
    score += np.where(c > bb_sup, 0.15, 0)
    score += np.where(c < bb_inf, 0.15, 0)
    score += np.where((pb > 0.85) & (rsi > 60), 0.10, 0)
    score += np.where((pb < 0.15) & (rsi < 40), 0.10, 0)
    score += np.where((c > o) & (ancho > 0.001), 0.05, 0)
    score += np.where((c < o) & (ancho > 0.001), 0.05, 0)
    score += np.where(bbw > 0.008, 0.05, 0)
    return np.clip(score, 0.0, 1.0)

# ═══════════════════════════════════════════════════════════════════════════════
# DATASET UNIFICADO
# ═══════════════════════════════════════════════════════════════════════════════
def generar_dataset() -> pd.DataFrame:
    print("[1/3] Cargando CSVs ...")
    df_m15 = _cargar_csv(CSV_M15)
    df_m5  = _cargar_csv(CSV_M5)
    df_m1  = _cargar_csv(CSV_M1)
    df_h1  = _cargar_csv(CSV_H1)

    print("[2/3] Calculando indicadores ...")
    m15_bb = calcular_bollinger(df_m15["close"])
    df_m15["bbw"] = m15_bb["bbw"]
    df_m15["pb"] = m15_bb["pb"]
    df_m15["rsi"] = calcular_rsi(df_m15["close"])
    df_m15["atr"] = calcular_atr(df_m15)
    df_m15["ema50"] = calcular_ema(df_m15["close"])

    m5_bb = calcular_bollinger(df_m5["close"])
    df_m5["bbw"] = m5_bb["bbw"]
    df_m5["pb"] = m5_bb["pb"]
    df_m5["rsi"] = calcular_rsi(df_m5["close"])
    df_m5["ema50"] = calcular_ema(df_m5["close"])

    m1_bb = calcular_bollinger(df_m1["close"])
    df_m1["bb_sup"] = m1_bb["sup"]
    df_m1["bb_inf"] = m1_bb["inf"]
    df_m1["rsi"] = calcular_rsi(df_m1["close"])

    h1_bb = calcular_bollinger(df_h1["close"])
    df_h1["pb"] = h1_bb["pb"]
    df_h1["rsi"] = calcular_rsi(df_h1["close"])
    df_h1["ema50"] = calcular_ema(df_h1["close"])

    print("[3/3] Uniendo timeframes ...")
    df = df_m15[["open", "high", "low", "close", "bbw", "pb", "rsi", "atr", "ema50"]].copy()
    df["m5_close"] = df_m5["close"].reindex(df.index, method="ffill")
    df["m5_bbw"] = df_m5["bbw"].reindex(df.index, method="ffill")
    df["m5_rsi"] = df_m5["rsi"].reindex(df.index, method="ffill")
    df["m5_ema50"] = df_m5["ema50"].reindex(df.index, method="ffill")
    df["h1_pb"] = df_h1["pb"].reindex(df.index, method="ffill")
    df["h1_rsi"] = df_h1["rsi"].reindex(df.index, method="ffill")
    df["h1_ema50"] = df_h1["ema50"].reindex(df.index, method="ffill")
    df["m1_close"] = df_m1["close"].reindex(df.index, method="ffill")
    df["m1_open"] = df_m1["open"].reindex(df.index, method="ffill")
    df["m1_high"] = df_m1["high"].reindex(df.index, method="ffill")
    df["m1_low"] = df_m1["low"].reindex(df.index, method="ffill")
    df["m1_bb_sup"] = df_m1["bb_sup"].reindex(df.index, method="ffill")
    df["m1_bb_inf"] = df_m1["bb_inf"].reindex(df.index, method="ffill")
    df["m1_rsi"] = df_m1["rsi"].reindex(df.index, method="ffill")

    df["hora"] = df.index.hour
    df = df[(df["hora"] >= 14) & (df["hora"] <= 21)].copy()

    df["conf_m5"] = score_confluencia(
        df["m5_close"], df["m5_close"].shift(1),
        df["m5_close"], df["m5_close"],
        df["m5_close"], df["m5_close"],
        df["m5_rsi"]
    )
    df["conf_m1"] = score_confluencia(
        df["m1_close"], df["m1_open"],
        df["m1_high"], df["m1_low"],
        df["m1_bb_sup"], df["m1_bb_inf"],
        df["m1_rsi"]
    )

    df = df.dropna()
    print(f"\n[OK] Dataset final: {len(df):,} filas | Sesión NY (14-21h)")
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# ENTORNO HÍBRIDO
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class Config:
    balance_inicial: float = 10_000.0
    riesgo_pct: float = 0.01
    atr_sl_mult: float = 1.2
    ratio_tp: float = 2.0
    comision: float = 3.5
    spread: float = 2.0
    min_prob: float = 0.7
    castigo_contra_tendencia: float = 0.6
    castigo_inactividad: float = -0.01

class EntornoHibrido(gym.Env):
    def __init__(self, df: pd.DataFrame, cfg: Config = None):
        super().__init__()
        self.cfg = cfg or Config()
        self.df = df.reset_index(drop=True)
        self.n = len(self.df)
        self.features = ["close", "bbw", "pb", "rsi", "atr", "ema50", "m5_bbw", "m5_rsi", "m5_ema50", "h1_pb", "h1_rsi", "h1_ema50", "conf_m5", "conf_m1", "hora"]
        self.action_space = spaces.Discrete(7)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(len(self.features),), dtype=np.float32)
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.i = 0
        self.balance = self.cfg.balance_inicial
        self.pnl = 0.0
        self.posiciones = []
        self.num_ops = 0
        self.ganadas = 0
        self.perdidas = 0
        self.rewards = []
        self.ultima_accion = 0
        self.horas_sin_operar = 0
        return self._obs(), {}

    def _obs(self):
        row = self.df.iloc[self.i]
        return np.array([float(row.get(f, 0)) for f in self.features], dtype=np.float32)

    def _tp_sl(self, precio, direccion, atr):
        sl = self.cfg.atr_sl_mult * atr * (1 if direccion == 1 else -1)
        tp = sl * self.cfg.ratio_tp * (1 if direccion == 1 else -1)
        return precio + tp, precio - sl

    def _evaluar(self, action, precio, high, low):
        c = self.df.iloc[self.i]["close"]
        o = self.df.iloc[self.i]["open"]
        pb = self.df.iloc[self.i]["pb"]
        rsi = self.df.iloc[self.i]["rsi"]
        bbw = self.df.iloc[self.i]["bbw"]
        tend_h1 = self.df.iloc[self.i]["h1_rsi"] - 50
        pend = (self.df.iloc[self.i]["ema50"] - self.df.iloc[self.i - 5]["ema50"]) if self.i >= 5 else 0
        momentum_up = (c > o) and (c - o) > (high - low) * 0.3 and pend > 0
        momentum_down = (c < o) and (o - c) > (high - low) * 0.3 and pend < 0
        score = 0.5
        if action in [1, 3]:
            score += 0.1
            if (pb > 0.9 or pb < 0.1): score += 0.15
            if (rsi > 75 or rsi < 25): score += 0.15
            if bbw > 0.01: score += 0.1
            if action == 1 and momentum_up: score -= 0.6
            if action == 3 and momentum_down: score -= 0.6
            if abs(tend_h1) >= 0.5:
                if action == 1 and tend_h1 < 0: score += self.cfg.castigo_contra_tendencia
                if action == 3 and tend_h1 > 0: score += self.cfg.castigo_contra_tendencia
        elif action in [2, 4]:
            score += 0.1
            if (pb > 0.55 and pb < 0.85) or (pb < 0.45 and pb > 0.15): score += 0.15
            if abs(tend_h1) >= 0.5:
                if action == 2 and tend_h1 > 0: score += 0.15
                if action == 4 and tend_h1 < 0: score += 0.15
            if action == 2 and momentum_up: score += 0.1
            if action == 4 and momentum_down: score += 0.1
        elif action in [5, 6]:
            score += 0.05
            if bbw > 0.008: score += 0.1
            if abs(tend_h1) >= 0.5:
                if action == 5 and tend_h1 > 0: score += 0.1
                if action == 6 and tend_h1 < 0: score += 0.1
        prob = float(np.clip(score, 0.0, 1.0))
        ok = prob >= self.cfg.min_prob
        direccion = 1 if action in [1, 2, 5] else -1
        modo = "REV" if action in [1, 3] else ("CONT" if action in [2, 4] else "SCALP")
        return ok, modo, direccion, 0.0, prob

    def step(self, action):
        row = self.df.iloc[self.i]
        precio = float(row["close"])
        high = float(row["high"])
        low = float(row["low"])
        atr = float(row["atr"])
        hora = int(row["hora"])
        reward = 0.0

        if action != 0:
            self.horas_sin_operar = 0
        else:
            self.horas_sin_operar += 1
            if self.horas_sin_operar > 5 and hora >= 14:
                reward += self.cfg.castigo_inactividad

        if action != 0 and len(self.posiciones) < 3:
            ok, modo, direccion, castigo, prob = self._evaluar(action, precio, high, low)
            if ok:
                tp, sl = self._tp_sl(precio, direccion, atr)
                lote = (self.balance * self.cfg.riesgo_pct) / (abs(precio - sl) + 1e-9)
                lote = max(0.01, min(lote, 5.0))
                self.posiciones.append({"tipo": modo, "dir": direccion, "precio": precio, "tp": tp, "sl": sl, "lote": lote})
                self.num_ops += 1
                reward += 0.02 * prob
            else:
                reward += castigo - 0.05

        # Cerrar posiciones
        cerradas = []
        nuevas_pos = []
        for pos in self.posiciones:
            cerrada = False
            if pos["dir"] == 1 and precio >= pos["tp"]:
                pnl = (pos["tp"] - pos["precio"]) * pos["lote"]
                cerradas.append(pnl); cerrada = True
            elif pos["dir"] == -1 and precio <= pos["tp"]:
                pnl = (pos["precio"] - pos["tp"]) * pos["lote"]
                cerradas.append(pnl); cerrada = True
            elif pos["dir"] == 1 and precio <= pos["sl"]:
                pnl = (pos["sl"] - pos["precio"]) * pos["lote"]
                cerradas.append(pnl); cerrada = True
            elif pos["dir"] == -1 and precio >= pos["sl"]:
                pnl = (pos["precio"] - pos["sl"]) * pos["lote"]
                cerradas.append(pnl); cerrada = True
            if not cerrada:
                nuevas_pos.append(pos)
        self.posiciones = nuevas_pos

        for pnl in cerradas:
            neto = pnl - self.cfg.comision - self.cfg.spread
            self.pnl += neto
            self.balance += neto
            if neto > 0:
                self.ganadas += 1
                reward += 0.1 + min(neto / 100, 0.5)
            else:
                self.perdidas += 1
                reward -= 0.05 + min(abs(neto) / 100, 0.3)

        self.i += 1
        done = self.i >= self.n - 1
        self.rewards.append(reward)
        wr = self.ganadas / max(self.num_ops, 1) * 100
        info = {"pnl": self.pnl, "num_ops": self.num_ops, "winrate": wr, "reward_total": sum(self.rewards)}
        return self._obs(), reward, done, False, info

# ═══════════════════════════════════════════════════════════════════════════════
# BACKTEST
# ═══════════════════════════════════════════════════════════════════════════════
def backtest(ruta_modelo: str, n_episodios: int = 2000, velas_por_ep: int = 5000):
    if not Path(ruta_modelo).exists():
        raise FileNotFoundError(f"NO EXISTE EL MODELO: {ruta_modelo}\nDescomprimí el ZIP de Kaggle en modelos\\modelo_unificado\\")

    print("=" * 70)
    print("BACKTEST — Modelo Unificado PPO")
    print("=" * 70)

    modelo = PPO.load(ruta_modelo)
    print(f"[OK] Modelo cargado: {ruta_modelo}")

    df = generar_dataset()
    len_df = len(df)

    print(f"\n[OK] Iniciando backtest: {n_episodios} episodios x {velas_por_ep} velas ...")
    print("-" * 70)

    resultados = []
    for ep in range(n_episodios):
        start = random.randint(0, max(0, len_df - velas_por_ep))
        env = EntornoHibrido(df.iloc[start:start + velas_por_ep].reset_index(drop=True))
        obs, info = env.reset(seed=ep)
        done = False
        while not done:
            action, _ = modelo.predict(obs, deterministic=True)
            obs, reward, done, _, info = env.step(action)
        resultados.append({
            "ep": ep, "pnl": info["pnl"], "ops": info["num_ops"],
            "wr": info["winrate"], "reward": info["reward_total"],
        })
        if ep % 200 == 0 or ep == n_episodios - 1:
            print(f"  Ep={ep:4d} | PnL=${info['pnl']:+8.0f} | Ops={info['num_ops']:2d} | WR={info['winrate']:5.1f}%")

    # Resumen
    ops_positivos = [r for r in resultados if r["ops"] > 0]
    wrs = [r["wr"] for r in ops_positivos]
    pnl_total = sum(r["pnl"] for r in resultados)
    ops_total = sum(r["ops"] for r in resultados)
    pnl_pos = sum(r["pnl"] for r in resultados if r["pnl"] > 0)
    pnl_neg = sum(r["pnl"] for r in resultados if r["pnl"] < 0)
    mejores = sorted(resultados, key=lambda x: x["pnl"], reverse=True)[:5]
    peores = sorted(resultados, key=lambda x: x["pnl"])[:5]

    print("\n" + "=" * 70)
    print("RESULTADOS FINALES")
    print("=" * 70)
    print(f"  Episodios:        {n_episodios}")
    print(f"  PnL TOTAL:        ${pnl_total:+,.2f}")
    print(f"  WR medio:         {np.mean(wrs):.1f}%" if wrs else "  WR medio:         N/A")
    print(f"  Ops totales:      {ops_total}")
    print(f"  Ops/ep medio:     {ops_total / n_episodios:.1f}")
    print(f"  Ganancias:        ${pnl_pos:+,.2f}")
    print(f"  Pérdidas:         ${pnl_neg:+,.2f}")
    print(f"  Ratio G/P:        {abs(pnl_pos / pnl_neg):.2f}" if pnl_neg != 0 else "  Ratio G/P:        inf")
    print(f"  Mejor episodio:   ${mejores[0]['pnl']:+.0f} (WR {mejores[0]['wr']:.1f}%, {mejores[0]['ops']} ops)")
    print(f"  Peor episodio:    ${peores[0]['pnl']:+.0f} (WR {peores[0]['wr']:.1f}%, {peores[0]['ops']} ops)")
    print(f"  % episodios > $0:  {sum(1 for r in resultados if r['pnl'] > 0) / n_episodios * 100:.1f}%")
    print("=" * 70)

    # Guardar JSON
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "modelo": ruta_modelo,
            "episodios": n_episodios,
            "resumen": {
                "pnl_total": pnl_total,
                "wr_medio": float(np.mean(wrs)) if wrs else 0,
                "ops_totales": ops_total,
                "ops_por_ep": ops_total / n_episodios,
                "ganancias": pnl_pos,
                "perdidas": pnl_neg,
                "ratio_gp": abs(pnl_pos / pnl_neg) if pnl_neg else float('inf'),
                "pct_positivos": sum(1 for r in resultados if r["pnl"] > 0) / n_episodios,
            },
            "top_5": mejores,
            "bottom_5": peores,
            "detalle": resultados,
        }, f, indent=2, default=str)
    print(f"\n[OK] Resultados guardados en: {OUTPUT}")
    return resultados

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", type=str, default=str(MODELO))
    parser.add_argument("--episodios", type=int, default=2000)
    parser.add_argument("--velas", type=int, default=5000)
    args = parser.parse_args()
    backtest(args.modelo, args.episodios, args.velas)

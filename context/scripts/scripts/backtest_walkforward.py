#!/usr/bin/env python3
"""
BACKTEST WALK-FORWARD + EXPORTADOR MT5

Backtesting cronologico REAL sobre todo el dataset (no episodios aleatorios).
Exporta trades a CSV para analisis en MT5 Strategy Tester o Excel.

Uso:
  cd QUANTUMHIVE_ALGORITHMICTRADING
  python scripts/backtest_walkforward.py

Salida:
  - modelos/backtest_equity.csv   -> Curva de equity minuto a minuto
  - modelos/trades_historial.csv  -> Cada trade con entrada, SL, TP, salida, PnL
  - modelos/backtest_resumen.json -> Metricas agregadas (Sharpe, drawdown, etc.)
"""
import os, sys, json, math, random, warnings
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_M15 = BASE_DIR / "datasets" / "US30_M15_2022_2024.csv"
CSV_M5 = BASE_DIR / "datasets" / "US30_M5_2022_2024.csv"
CSV_M1 = BASE_DIR / "datasets" / "US30_M1_2022_2024.csv"
CSV_H1 = BASE_DIR / "datasets" / "US30_H1_2022_2024.csv"
MODELO = BASE_DIR / "modelos" / "modelo_unificado" / "modelo_final.zip"
OUT_DIR = BASE_DIR / "modelos"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def calcular_rsi(serie, periodo=7):
    c = serie.astype(float)
    cambios = c.diff()
    ganancia = cambios.clip(lower=0)
    perdida = (-cambios).clip(lower=0)
    mg = ganancia.ewm(alpha=1/periodo, adjust=False).mean()
    mp = perdida.ewm(alpha=1/periodo, adjust=False).mean()
    rs = mg / mp.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def calcular_bollinger(serie, periodo=30, desv=3.0):
    c = serie.astype(float)
    media = c.rolling(periodo, min_periods=periodo).mean()
    std = c.rolling(periodo, min_periods=periodo).std(ddof=0)
    sup = media + desv * std
    inf = media - desv * std
    bbw = (sup - inf) / media.replace(0, np.nan)
    pb = (c - inf) / (sup - inf).replace(0, np.nan)
    return pd.DataFrame({"sup": sup, "inf": inf, "media": media, "bbw": bbw, "pb": pb}, index=serie.index)


def calcular_atr(df, periodo=14):
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    c = df["close"].astype(float)
    cp = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - cp).abs(), (l - cp).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/periodo, adjust=False).mean()


def calcular_ema(serie, periodo=50):
    return serie.astype(float).ewm(span=periodo, adjust=False).mean()


def _parsear_fecha(row):
    if "time" in row and pd.notna(row["time"]) and str(row["time"]).strip() != "":
        t = str(row["time"]).strip()
        if len(t) == 6 and t.isdigit():
            return f"{t[:2]}:{t[2:4]}:{t[4:]}"
    if "<TIME>" in row and pd.notna(row["<TIME>"]) and str(row["<TIME>"]).strip() != "":
        t = str(int(row["<TIME>"])).zfill(6)
        return f"{t[:2]}:{t[2:4]}:{t[4:]}"
    return "00:00:00"


def _cargar_csv(ruta, cols_requeridas=None, allow_fail=False):
    """
    Carga CSV con memoria optimizada: dtype float32, solo columnas necesarias.
    Si allow_fail=True y hay MemoryError/Error, retorna None para fallback.
    """
    if not Path(ruta).exists():
        if allow_fail:
            print(f"  [SKIP] No existe: {ruta.name}")
            return None
        raise FileNotFoundError(f"NO EXISTE: {ruta}")
    print(f"  [OK] Leyendo {ruta.name} ...")
    cols_default = ["time", "open", "high", "low", "close", "volume"]
    cols = cols_requeridas or cols_default
    dtypes = {c: np.float32 for c in cols if c != "time"}
    try:
        # Detectar separador leyendo solo primeras lineas con engine python
        with open(ruta, "r", encoding="utf-8") as fh:
            sample = fh.read(2048)
        detected_sep = ","
        for sep_candidate in [";", "\t"]:
            if sep_candidate in sample.split("\n")[0]:
                detected_sep = sep_candidate
                break
        df = pd.read_csv(
            ruta,
            sep=detected_sep,
            engine="c",
            usecols=lambda x: x.lower() in [c.lower() for c in cols],
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


def generar_dataset():
    print("[1/4] Cargando CSVs (optimizado memoria)...")
    df_m15 = _cargar_csv(CSV_M15)
    df_m5 = _cargar_csv(CSV_M5, allow_fail=True)
    df_m1 = _cargar_csv(CSV_M1, allow_fail=True)
    df_h1 = _cargar_csv(CSV_H1, allow_fail=True)
    if df_m5 is None:
        print("  [FALLBACK] M5 -> resample desde M15")
        df_m5 = df_m15.resample("5min").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    if df_m1 is None:
        print("  [FALLBACK] M1 -> resample desde M15")
        df_m1 = df_m15.resample("1min").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    if df_h1 is None:
        print("  [FALLBACK] H1 -> resample desde M15")
        df_h1 = df_m15.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()

    print("[2/4] Calculando indicadores ...")
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

    print("[3/4] Uniendo timeframes ...")
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
    print(f"\n[OK] Dataset final: {len(df):,} filas | Sesion NY (14-21h)")
    return df


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


@dataclass
class Trade:
    id: int
    tipo: str
    dir: int
    open_time: datetime
    open_price: float
    sl: float
    tp: float
    lote: float
    close_time: Optional[datetime] = None
    close_price: Optional[float] = None
    pnl: float = 0.0
    resultado: str = "OPEN"


class EntornoBacktest(gym.Env):
    def __init__(self, df, cfg=None):
        super().__init__()
        self.cfg = cfg or Config()
        self.df = df.reset_index(drop=True)
        self.timestamps = df.index.tolist()
        self.n = len(self.df)
        self.features = 10
        self.action_space = spaces.Discrete(7)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.i = 0
        self.balance = self.cfg.balance_inicial
        self.equity = self.cfg.balance_inicial
        self.pnl = 0.0
        self.posiciones = []
        self.trades_historial = []
        self.trade_id = 0
        self.num_ops = 0
        self.ganadas = 0
        self.perdidas = 0
        self.equity_curve = [self.balance]
        self.pnl_curve = [0.0]
        self.timestamps_curve = [self.timestamps[0] if self.timestamps else datetime.now()]
        self.rewards = []
        self.horas_sin_operar = 0
        # Estado para observaciones normalizadas (10 features)
        self.pos_abierta_dir = 0  # 1=long, -1=short, 0=none
        self.pnl_dia = 0.0
        self.barras_dia = 0
        return self._obs(), {}

    def _obs(self):
        r = self.df.iloc[self.i]
        c = float(r["close"])
        pb = float(r.get("pb", 0.5))
        rsi = float(r.get("rsi", 50.0))
        bbw = float(r.get("bbw", 0.005))
        atr = float(r.get("atr", 0.0))
        ema50 = float(r.get("ema50", c))
        ema50_prev = float(self.df["ema50"].iloc[max(0, self.i - 5)]) if "ema50" in self.df.columns else c
        pend = (ema50 - ema50_prev) * 1000
        conf_m5 = float(r.get("conf_m5", 0.5))
        conf_m1 = float(r.get("conf_m1", 0.5))
        h1_rsi = float(r.get("h1_rsi", 50.0))
        tend_h1 = np.sign(h1_rsi - 50.0)
        # Heuristica bbw_estado: aproximar con percentiles fijos
        bbw_est = 0.0
        if bbw < 0.003:
            bbw_est = -1.0
        elif bbw > 0.008:
            bbw_est = 1.0
        pos_estado = float(self.pos_abierta_dir)
        pnl_norm = np.clip(self.pnl_dia / max(1e-12, self.cfg.balance_inicial) * 10, -1, 1)
        obs = np.array([
            np.clip(pb * 2 - 1, -1, 1),
            np.clip(rsi / 50 - 1, -1, 1),
            np.clip(bbw_est, -1, 1),
            np.clip(pend, -1, 1),
            float(conf_m5),
            float(conf_m1),
            np.clip(tend_h1, -1, 1),
            np.clip(atr / c * 100, -1, 1),
            pos_estado,
            pnl_norm,
        ], dtype=np.float32)
        return obs

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
        ts = self.timestamps[self.i] if self.i < len(self.timestamps) else None

        # Reset pnl_dia on new day (consistent with hybrid env)
        if ts is not None and hasattr(ts, 'date'):
            if not hasattr(self, '_last_date') or ts.date() != self._last_date:
                self.pnl_dia = 0.0
                self._last_date = ts.date()

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
                trade = Trade(
                    id=self.trade_id, tipo=modo, dir=direccion,
                    open_time=ts, open_price=precio, sl=sl, tp=tp, lote=lote,
                )
                self.posiciones.append(trade)
                self.trades_historial.append(trade)
                self.trade_id += 1
                self.num_ops += 1
                self.pos_abierta_dir = direccion
                reward += 0.02 * prob
            else:
                reward += castigo - 0.05

        pnl_cierre = 0.0
        for trade in self.posiciones[:]:
            cerrado = False
            if trade.dir == 1:
                if precio >= trade.tp:
                    trade.close_price = trade.tp; trade.resultado = "WIN"; cerrado = True
                elif precio <= trade.sl:
                    trade.close_price = trade.sl; trade.resultado = "LOSS"; cerrado = True
            else:
                if precio <= trade.tp:
                    trade.close_price = trade.tp; trade.resultado = "WIN"; cerrado = True
                elif precio >= trade.sl:
                    trade.close_price = trade.sl; trade.resultado = "LOSS"; cerrado = True

            if cerrado:
                trade.close_time = ts
                trade.pnl = (trade.close_price - trade.open_price) * trade.lote * trade.dir - self.cfg.comision - self.cfg.spread
                pnl_cierre += trade.pnl
                self.pnl_dia += trade.pnl
                self.posiciones.remove(trade)
                if len(self.posiciones) == 0:
                    self.pos_abierta_dir = 0
                if trade.pnl > 0:
                    self.ganadas += 1
                    reward += 0.1 + min(trade.pnl / 100, 0.5)
                else:
                    self.perdidas += 1
                    reward -= 0.05 + min(abs(trade.pnl) / 100, 0.3)

        pnl_flotante = 0.0
        for trade in self.posiciones:
            pnl_flotante += (precio - trade.open_price) * trade.lote * trade.dir
        self.equity = self.balance + pnl_cierre + pnl_flotante
        self.balance += pnl_cierre
        self.pnl += pnl_cierre
        self.equity_curve.append(self.equity)
        self.pnl_curve.append(self.pnl)
        self.timestamps_curve.append(ts)

        self.i += 1
        done = self.i >= self.n - 1
        self.rewards.append(reward)
        wr = self.ganadas / max(self.num_ops, 1) * 100
        info = {
            "pnl": self.pnl, "equity": self.equity, "num_ops": self.num_ops,
            "winrate": wr, "reward_total": sum(self.rewards),
            "trades_abiertos": len(self.posiciones),
        }
        return self._obs(), reward, done, False, info


def backtest_walkforward(ruta_modelo):
    if not Path(ruta_modelo).exists():
        raise FileNotFoundError(f"NO EXISTE EL MODELO: {ruta_modelo}")

    print("=" * 70)
    print("BACKTEST WALK-FORWARD — Modelo Unificado PPO")
    print("=" * 70)

    modelo = PPO.load(ruta_modelo)
    print(f"[OK] Modelo cargado: {ruta_modelo}")

    df = generar_dataset()

    print(f"\n[OK] Iniciando walk-forward sobre {len(df):,} velas M15 ...")
    print("-" * 70)

    env = EntornoBacktest(df)
    obs, info = env.reset(seed=42)
    done = False

    total = len(df)
    checkpoints = [int(total * p) for p in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]
    next_checkpoint = 0

    while not done:
        action, _ = modelo.predict(obs, deterministic=True)
        obs, reward, done, _, info = env.step(action)
        if env.i >= checkpoints[next_checkpoint]:
            pct = (next_checkpoint + 1) * 10
            print(f"  {pct:3d}% | Equity=${env.equity:,.2f} | PnL=${env.pnl:+,.2f} | Ops={env.num_ops} | WR={info['winrate']:.1f}%")
            next_checkpoint = min(next_checkpoint + 1, len(checkpoints) - 1)

    print("-" * 70)

    if env.posiciones:
        precio_final = float(df.iloc[-1]["close"])
        ts_final = env.timestamps[-1]
        for trade in env.posiciones:
            trade.close_time = ts_final
            trade.close_price = precio_final
            trade.pnl = (precio_final - trade.open_price) * trade.lote * trade.dir - env.cfg.comision - env.cfg.spread
            trade.resultado = "WIN" if trade.pnl > 0 else "LOSS"
            env.pnl += trade.pnl
            env.balance += trade.pnl
            if trade.pnl > 0:
                env.ganadas += 1
            else:
                env.perdidas += 1
        env.equity = env.balance
        env.posiciones = []

    equity_arr = np.array(env.equity_curve)
    pnl_arr = np.array(env.pnl_curve)
    returns = np.diff(equity_arr) / equity_arr[:-1]
    returns = returns[returns != 0]
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 4) if len(returns) > 1 and np.std(returns) > 0 else 0

    max_equity = np.maximum.accumulate(equity_arr)
    drawdowns = (max_equity - equity_arr) / max_equity
    max_dd = np.max(drawdowns) * 100 if len(drawdowns) > 0 else 0

    trades_cerrados = [t for t in env.trades_historial if t.resultado != "OPEN"]
    wins = [t for t in trades_cerrados if t.resultado == "WIN"]
    losses = [t for t in trades_cerrados if t.resultado == "LOSS"]
    pnl_total = sum(t.pnl for t in trades_cerrados)
    pnl_wins = sum(t.pnl for t in wins)
    pnl_losses = sum(t.pnl for t in losses)
    avg_win = np.mean([t.pnl for t in wins]) if wins else 0
    avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
    profit_factor = abs(pnl_wins / pnl_losses) if pnl_losses != 0 else float('inf')

    print("\n" + "=" * 70)
    print("RESULTADOS FINALES — WALK-FORWARD COMPLETO")
    print("=" * 70)
    print(f"  Fechas:           {df.index[0]} -> {df.index[-1]}")
    print(f"  Velas evaluadas:  {len(df):,}")
    print(f"  Balance inicial:  ${env.cfg.balance_inicial:,.2f}")
    print(f"  Balance final:    ${env.balance:,.2f}")
    print(f"  PnL TOTAL:        ${pnl_total:+,.2f}")
    print(f"  Retorno:          {pnl_total / env.cfg.balance_inicial * 100:+.2f}%")
    print(f"  Trades totales:   {len(trades_cerrados)}")
    print(f"  Wins:             {len(wins)} ({len(wins)/max(len(trades_cerrados),1)*100:.1f}%)")
    print(f"  Losses:           {len(losses)} ({len(losses)/max(len(trades_cerrados),1)*100:.1f}%)")
    print(f"  Winrate:          {len(wins)/max(len(trades_cerrados),1)*100:.1f}%")
    print(f"  Avg win:          ${avg_win:+.2f}")
    print(f"  Avg loss:         ${avg_loss:+.2f}")
    print(f"  Profit factor:    {profit_factor:.2f}")
    print(f"  Max drawdown:     {max_dd:.2f}%")
    print(f"  Sharpe (anual):   {sharpe:.2f}")
    print("=" * 70)

    equity_df = pd.DataFrame({
        "datetime": env.timestamps_curve,
        "equity": env.equity_curve,
        "pnl_acumulado": env.pnl_curve,
    })
    equity_path = OUT_DIR / "backtest_equity.csv"
    equity_df.to_csv(equity_path, index=False)
    print(f"\n[OK] Curva equity guardada: {equity_path}")

    trades_data = []
    for t in trades_cerrados:
        trades_data.append({
            "ticket": t.id, "tipo": t.tipo,
            "direccion": "BUY" if t.dir == 1 else "SELL",
            "open_time": t.open_time.strftime("%Y.%m.%d %H:%M") if t.open_time else "",
            "open_price": round(t.open_price, 2),
            "sl": round(t.sl, 2), "tp": round(t.tp, 2), "lote": round(t.lote, 2),
            "close_time": t.close_time.strftime("%Y.%m.%d %H:%M") if t.close_time else "",
            "close_price": round(t.close_price, 2) if t.close_price else None,
            "pnl": round(t.pnl, 2), "resultado": t.resultado,
            "duracion_barras": None,
        })
    trades_df = pd.DataFrame(trades_data)
    if not trades_df.empty:
        trades_df["duracion_barras"] = (
            pd.to_datetime(trades_df["close_time"], format="%Y.%m.%d %H:%M") -
            pd.to_datetime(trades_df["open_time"], format="%Y.%m.%d %H:%M")
        ).dt.total_seconds() / 900
        trades_df["duracion_barras"] = trades_df["duracion_barras"].round(0)

    trades_path = OUT_DIR / "trades_historial.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"[OK] Trades guardados: {trades_path}")

    resumen = {
        "timestamp": datetime.now().isoformat(),
        "modelo": ruta_modelo,
        "dataset": {"inicio": str(df.index[0]), "fin": str(df.index[-1]), "velas": len(df)},
        "resultados": {
            "balance_inicial": env.cfg.balance_inicial,
            "balance_final": env.balance,
            "pnl_total": pnl_total,
            "retorno_pct": pnl_total / env.cfg.balance_inicial * 100,
            "trades_totales": len(trades_cerrados),
            "wins": len(wins), "losses": len(losses),
            "winrate_pct": len(wins) / max(len(trades_cerrados), 1) * 100,
            "avg_win": avg_win, "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_dd,
            "sharpe_anual": sharpe,
        },
        "distribucion_tipos": {
            "REV": len([t for t in trades_cerrados if t.tipo == "REV"]),
            "CONT": len([t for t in trades_cerrados if t.tipo == "CONT"]),
            "SCALP": len([t for t in trades_cerrados if t.tipo == "SCALP"]),
        },
        "distribucion_direccion": {
            "BUY": len([t for t in trades_cerrados if t.dir == 1]),
            "SELL": len([t for t in trades_cerrados if t.dir == -1]),
        },
    }
    json_path = OUT_DIR / "backtest_resumen.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, default=str)
    print(f"[OK] Resumen JSON: {json_path}")

    print("\n" + "=" * 70)
    print("ARCHIVOS GENERADOS")
    print("=" * 70)
    print(f"  1. {trades_path.name}")
    print(f"     -> Abrir en Excel para analizar cada trade")
    print(f"     -> ticket, tipo, direccion, open_time, open_price, sl, tp,")
    print(f"        lote, close_time, close_price, pnl, resultado, duracion_barras")
    print(f"  2. {equity_path.name}")
    print(f"     -> Curva de equity para graficar")
    print(f"  3. {json_path.name}")
    print(f"     -> Metricas agregadas (Sharpe, drawdown, profit factor)")
    print("=" * 70)

    return resumen, trades_df, equity_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", type=str, default=str(MODELO))
    args = parser.parse_args()
    backtest_walkforward(args.modelo)

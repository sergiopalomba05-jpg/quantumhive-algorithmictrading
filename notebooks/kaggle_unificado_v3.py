#!/usr/bin/env python3
"""
Kaggle Notebook v3 — QuantumHive Unified PPO Trainer
=======================================================
Self-contained Kaggle script for training the unified RL bot.
Includes the EXACT EntornoHibridoUnificado used in production.

Run in Kaggle GPU (T4) notebook:
  1. Upload US30_M15/M5/M1/H1 CSVs as Kaggle datasets
  2. Run all cells
  3. Download modelo_final.zip and bot_unificado.onnx

Features:
  - Entorno hibrido nativo (10 features, 7 actions)
  - PPO with SB3 on GPU
  - Walk-forward evaluation
  - ONNX export (ActorNet wrapper, opset 14)
  - Auto-report generation
"""

import os, sys, random, json, warnings, math
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Install dependencies (uncomment in Kaggle first cell)
# ─────────────────────────────────────────────────────────────────────────────
# !pip install -q stable-baselines3[extra] onnx onnxruntime gymnasium torch

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
import torch
import torch.nn as nn

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class ConfigHibrido:
    balance_inicial: float = 10_000.0
    riesgo_pct: float = 0.01
    sl_atr_mult: float = 2.0
    tp1_atr_mult: float = 1.5
    tp2_atr_mult: float = 3.0
    fraccion_tp1: float = 0.5
    be_ratio: float = 0.5
    comision: float = 2.0
    spread: float = 1.5
    bb_periodo: int = 20
    bb_desv: float = 2.0
    rsi_periodo: int = 14
    atr_periodo: int = 14
    ventana_apertura_barras: int = 4
    min_probabilidad: float = 0.85
    castigo_sin_condiciones: float = -0.5
    castigo_inactividad_ventana: float = -0.15
    castigo_contra_tendencia_h1: float = -0.4
    costo_holding: float = -0.005
    incentivo_apertura: float = 0.02
    recompensa_tp1: float = 0.8
    recompensa_tp2: float = 1.0
    recompensa_be: float = 0.4
    castigo_sl: float = -1.2
    rsi_rev_long_max: float = 20.0
    rsi_rev_short_min: float = 80.0
    rsi_cont_long: tuple = (45.0, 75.0)
    rsi_cont_short: tuple = (25.0, 55.0)
    max_ops_dia: int = 2
    castigo_sobreoperacion: float = -0.5
    castigo_contra_momentum: float = -0.5
    castigo_streak_perdidas: float = -0.3
    streak_umbral: int = 3
    recompensa_no_operar: float = 0.05


# ═══════════════════════════════════════════════════════════════════════════════
# 3. INDICATORS
# ═══════════════════════════════════════════════════════════════════════════════
def calcular_rsi(serie: pd.Series, periodo: int = 14) -> pd.Series:
    delta = serie.diff()
    gan = delta.clip(lower=0)
    per = (-delta).clip(lower=0)
    avg_gan = gan.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    avg_per = per.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    rs = avg_gan / (avg_per + 1e-12)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def calcular_bollinger(serie: pd.Series, periodo: int = 20, desv: float = 2.0):
    media = serie.rolling(window=periodo, min_periods=1).mean().fillna(serie.mean())
    std = serie.rolling(window=periodo, min_periods=1).std(ddof=0).fillna(0.0)
    sup = media + desv * std
    inf = media - desv * std
    bbw = ((sup - inf) / (media + 1e-9)).fillna(0)
    pb = ((serie - inf) / (sup - inf + 1e-9)).fillna(0.5)
    return {"media": media, "bb_superior": sup, "bb_inferior": inf, "bbw": bbw, "pb": pb, "porcentaje_b": pb}

def calcular_atr(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / periodo, min_periods=1, adjust=False).mean()
    return atr.fillna(0.0)

def calcular_ema(serie: pd.Series, span: int = 50) -> pd.Series:
    return serie.ewm(span=span, adjust=False).mean()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DATASET BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
WORKING = Path("/kaggle/working" if os.path.exists("/kaggle") else ".")
DATA_PATH = Path(__file__).parent.parent / "datasets" if "__file__" in globals() else Path("../datasets")

def _cargar_csv(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        raise FileNotFoundError(f"NO EXISTE: {ruta}")
    sep = ","
    with open(ruta, "r", encoding="utf-8") as fh:
        sample = fh.read(4096)
    for cand in [";", "\t"]:
        if cand in sample.split("\n")[0]:
            sep = cand
            break
    df = pd.read_csv(
        ruta, sep=sep, engine="c",
        low_memory=True,
    )
    # 1. Parsear datetime desde columnas MT5 originales
    # Sin format estricto para soportar HH:MM y HH:MM:SS
    df['datetime'] = pd.to_datetime(
        df['<DATE>'].astype(str) + ' ' + df['<TIME>'].astype(str),
        errors='coerce'
    )

    # 2. Renombrar columnas MT5 a nombres limpios
    df.rename(columns={
        '<OPEN>': 'open',
        '<HIGH>': 'high',
        '<LOW>': 'low',
        '<CLOSE>': 'close',
        '<TICKVOL>': 'volume',
    }, inplace=True, errors='ignore')

    # 3. Eliminar columnas no usadas
    df.drop(columns=['<DATE>', '<TIME>', '<VOL>', '<SPREAD>',
                     '<REALVOL>'], inplace=True, errors='ignore')

    # 4. Asegurar que OHLC sean numéricos
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['datetime', 'open', 'high', 'low', 'close'])
    df = df.set_index('datetime').sort_index()
    for c in ('open', 'high', 'low', 'close'):
        df[c] = df[c].astype(np.float32)
    return df

def generar_dataset_unificado() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carga M15 + M5 + M1 + H1 y devuelve DataFrames separados para el entorno."""
    print("[DATA] Cargando CSVs...")
    df_m15 = _cargar_csv(DATA_PATH / "US30_M15_2022_2024.csv")
    df_m5  = _cargar_csv(DATA_PATH / "US30_M5_2022_2024.csv")  if (DATA_PATH / "US30_M5_2022_2024.csv").exists() else None
    df_m1  = _cargar_csv(DATA_PATH / "US30_M1_2022_2024.csv")  if (DATA_PATH / "US30_M1_2022_2024.csv").exists() else None
    df_h1  = _cargar_csv(DATA_PATH / "US30_H1_2022_2024.csv")  if (DATA_PATH / "US30_H1_2022_2024.csv").exists() else None

    if df_m5 is None:
        df_m5 = df_m15.resample("5min").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    if df_m1 is None:
        df_m1 = df_m15.resample("1min").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    if df_h1 is None:
        df_h1 = df_m15.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()

    # Alinear todos a índice M15 (forward-fill para M5/M1/H1)
    df_m5 = df_m5.reindex(df_m15.index, method="ffill")
    df_m1 = df_m1.reindex(df_m15.index, method="ffill")
    df_h1 = df_h1.reindex(df_m15.index, method="ffill")

    # Filtro sesion NY 14-21h sobre M15
    hora = df_m15.index.hour
    mask = (hora >= 14) & (hora <= 21)
    if mask.sum() == 0:
        print(f"[WARN] Filtro 14-21h dejo 0 filas. Horas presentes: {sorted(set(hora))[:10]}...")
        print(f"[WARN] Usando TODO el dataset sin filtrar hora.")
    else:
        df_m15 = df_m15[mask].copy()
        df_m5  = df_m5[mask].copy()
        df_m1  = df_m1[mask].copy()
        df_h1  = df_h1[mask].copy()

    df_m15 = df_m15.dropna(subset=["open","high","low","close"])
    df_m5  = df_m5.dropna(subset=["open","high","low","close"])
    df_m1  = df_m1.dropna(subset=["open","high","low","close"])
    df_h1  = df_h1.dropna(subset=["open","high","low","close"])

    if len(df_m15) == 0:
        raise ValueError("df_m15 vacio tras filtrado. Revisa el CSV y el formato de fechas.")
    print(f"[DATA] Dataset final: {len(df_m15):,} filas | {df_m15.index[0]} -> {df_m15.index[-1]}")
    return df_m15, df_m5, df_m1, df_h1


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ENTORNO HIBRIDO UNIFICADO (identico a produccion)
# ═══════════════════════════════════════════════════════════════════════════════
class EntornoHibridoUnificado(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        datos_m15: pd.DataFrame,
        datos_m5: pd.DataFrame | None = None,
        datos_m1: pd.DataFrame | None = None,
        datos_h1: pd.DataFrame | None = None,
        cfg: ConfigHibrido | None = None,
    ) -> None:
        super().__init__()
        self.datos = datos_m15.copy()
        if not isinstance(self.datos.index, pd.DatetimeIndex):
            raise ValueError("DataFrame requiere DatetimeIndex.")
        for c in ("open", "high", "low", "close"):
            if c not in self.datos.columns:
                raise ValueError(f"Falta columna: {c}")

        self.m5 = datos_m5.copy() if datos_m5 is not None else self.datos
        self.m1 = datos_m1.copy() if datos_m1 is not None else self.datos
        self.h1 = datos_h1.copy() if datos_h1 is not None else self.datos
        self.cfg = cfg or ConfigHibrido()

        self.balance = float(self.cfg.balance_inicial)
        self.equity = self.balance
        self.pico_equity = self.balance
        self.pico_equity_dia = self.balance
        self.fecha_equity_dia = None
        self.paso = 0
        self.precio_inicial = float(self.datos.iloc[0]["close"])

        self.pos_abierta = False
        self.dir = 0
        self.precio_entrada = 0.0
        self.sl = 0.0
        self.tp1 = 0.0
        self.tp2 = 0.0
        self.lote_total = 0.0
        self.lote_remanente = 0.0
        self.be_activado = False
        self.modo = ""
        self.ops_hoy = 0
        self.pnl_dia = 0.0
        self.barras_desde_inicio_dia = 0
        self.historial: list[dict] = []

        # Tracking para backtest
        self.equity_curve: list[float] = [self.balance]
        self.balance_curve: list[float] = [self.balance]
        self.timestamps_curve: list[pd.Timestamp] = [self.datos.index[0]]
        self.rewards_curve: list[float] = []

        self._precomputar()
        self.action_space = spaces.Discrete(7)
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(10,), dtype=np.float32)

    def _precomputar(self) -> None:
        self.bb = calcular_bollinger(self.datos["close"], self.cfg.bb_periodo, self.cfg.bb_desv)
        self.rsi = calcular_rsi(self.datos["close"], self.cfg.rsi_periodo)
        self.atr = calcular_atr(self.datos, self.cfg.atr_periodo)
        c = self.datos["close"].astype(float)
        self.ema50 = c.ewm(span=50, adjust=False).mean()
        self.pend_ema = self.ema50.diff().fillna(0)
        bbw_s = self.bb["bbw"].fillna(0)
        self.bbw_estado = pd.Series(np.where(bbw_s > bbw_s.quantile(0.80, interpolation="linear"), 1.0,
                                    np.where(bbw_s < bbw_s.quantile(0.20, interpolation="linear"), -1.0, 0.0)),
                                    index=self.datos.index)
        self.bb_m5 = calcular_bollinger(self.m5["close"])
        self.rsi_m5 = calcular_rsi(self.m5["close"])
        self.bb_m1 = calcular_bollinger(self.m1["close"])
        self.rsi_m1 = calcular_rsi(self.m1["close"])
        c_h1 = self.h1["close"].astype(float)
        ema50_h1 = c_h1.ewm(span=50, adjust=False).mean()
        self.tendencia_h1 = np.sign(c_h1 - ema50_h1).fillna(0)

    def _ts(self) -> pd.Timestamp:
        return self.datos.index[self.paso]

    def _close(self) -> float:
        return float(self.datos.iloc[self.paso]["close"])

    def _high(self) -> float:
        return float(self.datos.iloc[self.paso]["high"])

    def _low(self) -> float:
        return float(self.datos.iloc[self.paso]["low"])

    def _reset_posicion(self):
        self.pos_abierta = False
        self.dir = 0
        self.precio_entrada = 0.0
        self.sl = 0.0
        self.tp1 = 0.0
        self.tp2 = 0.0
        self.lote_total = 0.0
        self.lote_remanente = 0.0
        self.be_activado = False
        self.modo = ""

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        super().reset(seed=seed)
        self.balance = float(self.cfg.balance_inicial)
        self.equity = self.balance
        self.pico_equity = self.balance
        self.pico_equity_dia = self.balance
        self.fecha_equity_dia = None
        self.paso = 0
        self._reset_posicion()
        self.ops_hoy = 0
        self.pnl_dia = 0.0
        self.barras_desde_inicio_dia = 0
        self.historial = []
        self.historial: list[dict] = []
        self.streak_perdidas = 0
        self.equity_curve = [self.balance]
        self.balance_curve = [self.balance]
        self.timestamps_curve = [self.datos.index[0]]
        self.rewards_curve = []
        return self._obs(), {"balance": self.balance, "equity": self.equity}

    def step(self, action: int):
        if self.paso >= len(self.datos) - 1:
            if self.pos_abierta:
                self._cerrar_total(self._ts(), self._close(), "fin_datos")
            return self._obs(), 0.0, True, False, {"motivo": "fin_datos"}

        ts = self._ts()
        self._actualizar_picos(ts)
        precio = self._close()
        high = self._high()
        low = self._low()
        info: dict[str, Any] = {}
        reward = self.cfg.costo_holding if self.pos_abierta else 0.0

        # Castigo inactividad ventana apertura
        if not self.pos_abierta and self.ops_hoy == 0 and self.barras_desde_inicio_dia < self.cfg.ventana_apertura_barras:
            reward += self.cfg.castigo_inactividad_ventana
            info["inactividad"] = self.barras_desde_inicio_dia

        if self.pos_abierta:
            evt = self._gestionar_posicion(ts, high, low)
            if evt == "tp1":
                reward += self.cfg.recompensa_tp1
                info["evento"] = "tp1"
            elif evt == "tp2":
                reward += self.cfg.recompensa_tp2
                info["evento"] = "tp2"
            elif evt == "sl":
                reward += self.cfg.castigo_sl
                info["evento"] = "sl"
            elif evt == "be":
                reward += self.cfg.recompensa_be
                info["evento"] = "be"

        if action != 0 and not self.pos_abierta:
            if self.ops_hoy >= self.cfg.max_ops_dia:
                reward += self.cfg.castigo_sobreoperacion
                info["rechazo"] = {"castigo": self.cfg.castigo_sobreoperacion, "razon": "max_ops_dia"}
            else:
                ok, modo, direccion, castigo, prob = self._evaluar_apertura(action, precio, high, low)
                if ok:
                    self._abrir(modo, direccion, precio, ts)
                    reward += self.cfg.incentivo_apertura * prob
                    if self.streak_perdidas >= self.cfg.streak_umbral:
                        reward += self.cfg.castigo_streak_perdidas * self.streak_perdidas
                        info["streak_castigo"] = self.streak_perdidas
                    info["apertura"] = {"modo": modo, "dir": direccion, "prob": prob}
                else:
                    reward += castigo
                    info["rechazo"] = {"castigo": castigo, "razon": modo, "prob": prob}
        elif action == 0 and not self.pos_abierta and self.barras_desde_inicio_dia < self.cfg.ventana_apertura_barras:
            reward += self.cfg.recompensa_no_operar

        self.equity = self._equity(precio)
        self.pico_equity = max(self.pico_equity, self.equity)
        self.paso += 1
        terminado = self.paso >= len(self.datos) - 1

        # Tracking backtest
        self.equity_curve.append(float(self.equity))
        self.balance_curve.append(float(self.balance))
        self.timestamps_curve.append(ts)
        self.rewards_curve.append(float(reward))

        return self._obs(), float(reward), bool(terminado), False, info

    def _gestionar_posicion(self, ts: pd.Timestamp, high: float, low: float) -> str | None:
        if not self.pos_abierta:
            return None
        if self._toco(low, high, self.sl):
            res = "be" if (self.be_activado and abs(self.sl - self.precio_entrada) < 1e-9) else "sl"
            self._cerrar_total(ts, float(self.sl), res)
            return res
        if not self.be_activado and self._toco(low, high, self.tp1):
            self._cerrar_parcial(ts, float(self.tp1))
            return "tp1"
        if self._toco(low, high, self.tp2):
            self._cerrar_total(ts, float(self.tp2), "tp2")
            return "tp2"
        return None

    def _toco(self, low: float, high: float, nivel: float) -> bool:
        return bool(np.isfinite(nivel) and low <= nivel <= high)

    def _cerrar_parcial(self, ts: pd.Timestamp, precio: float) -> None:
        frac = self.cfg.fraccion_tp1
        lote_cerrar = min(self.lote_total * frac, self.lote_remanente)
        pnl = (precio - self.precio_entrada) * self.dir * lote_cerrar - self.cfg.comision - self.cfg.spread
        self.balance += float(pnl)
        self.lote_remanente -= lote_cerrar
        self.pnl_dia += pnl
        # BE: mover SL a precio de entrada
        self.sl = self.precio_entrada
        self.be_activado = True

    def _cerrar_total(self, ts: pd.Timestamp, precio: float, motivo: str) -> None:
        pnl = (precio - self.precio_entrada) * self.dir * self.lote_remanente - self.cfg.comision - self.cfg.spread
        self.balance += float(pnl)
        self.pnl_dia += pnl
        if pnl > 0:
            self.streak_perdidas = 0
        else:
            self.streak_perdidas += 1
        self.historial.append({
            "ts_entrada": ts, "ts_salida": ts, "dir": self.dir, "modo": self.modo,
            "precio_entrada": self.precio_entrada, "precio_salida": precio,
            "lote": self.lote_total, "pnl": pnl,
            "resultado": "WIN" if pnl > 0 else "LOSS", "motivo": motivo,
        })
        self._reset_posicion()

    def _abrir(self, modo: str, direccion: int, precio: float, ts: pd.Timestamp) -> None:
        if self.ops_hoy >= self.cfg.max_ops_dia:
            return
        atr = float(self.atr.iloc[self.paso])
        sl_offset = atr * self.cfg.sl_atr_mult
        tp1_offset = atr * self.cfg.tp1_atr_mult
        tp2_offset = atr * self.cfg.tp2_atr_mult
        if direccion == 1:
            self.sl = precio - sl_offset
            self.tp1 = precio + tp1_offset
            self.tp2 = precio + tp2_offset
        else:
            self.sl = precio + sl_offset
            self.tp1 = precio - tp1_offset
            self.tp2 = precio - tp2_offset
        self.lote_total = (self.balance * self.cfg.riesgo_pct) / (abs(precio - self.sl) + 1e-9)
        self.lote_total = max(0.01, min(self.lote_total, 5.0))
        self.lote_remanente = self.lote_total
        self.pos_abierta = True
        self.dir = direccion
        self.precio_entrada = precio
        self.be_activado = False
        self.modo = modo
        self.ops_hoy += 1

    def _evaluar_apertura(self, action: int, precio: float, high: float, low: float):
        """Evalúa si hay setup visual PERFECTO para abrir. Estricto: toque banda + RSI extremo + mecha."""
        i = self.paso
        c = precio
        o = float(self.datos.iloc[i]["open"])
        h = high
        l = low
        rsi = float(self.rsi.iloc[i])
        pend = float(self.pend_ema.iloc[i])
        sup = float(self.bb["bb_superior"].iloc[i])
        inf = float(self.bb["bb_inferior"].iloc[i])
        i_m5 = min(i, len(self.m5) - 1)
        i_m1 = min(i, len(self.m1) - 1)
        tend_h1 = float(self.tendencia_h1.iloc[min(i, len(self.tendencia_h1) - 1)])

        if action == 1: modo, direccion = "REV", 1
        elif action == 2: modo, direccion = "REV", -1
        elif action == 3: modo, direccion = "CONT", 1
        elif action == 4: modo, direccion = "CONT", -1
        elif action == 5: modo, direccion = "SCALP", 1
        else: modo, direccion = "SCALP", -1

        # Estrategia visual estricta: REVERSIÓN a la media en apertura NY
        conf = self._score_confluencia(c, o, h, l, sup, inf, rsi, direccion=direccion)

        # Confluencia en M5 y M1 solo si hay dirección
        if conf >= 0.35:
            c_m5 = float(self.m5["close"].iloc[i_m5])
            o_m5 = float(self.m5["open"].iloc[i_m5])
            h_m5 = float(self.m5["high"].iloc[i_m5])
            l_m5 = float(self.m5["low"].iloc[i_m5])
            sup_m5 = float(self.bb_m5["bb_superior"].iloc[i_m5])
            inf_m5 = float(self.bb_m5["bb_inferior"].iloc[i_m5])
            rsi_m5 = float(self.rsi_m5.iloc[i_m5])
            conf_m5 = self._score_confluencia(c_m5, o_m5, h_m5, l_m5, sup_m5, inf_m5, rsi_m5, direccion=direccion)
            c_m1 = float(self.m1["close"].iloc[i_m1])
            o_m1 = float(self.m1["open"].iloc[i_m1])
            h_m1 = float(self.m1["high"].iloc[i_m1])
            l_m1 = float(self.m1["low"].iloc[i_m1])
            sup_m1 = float(self.bb_m1["bb_superior"].iloc[i_m1])
            inf_m1 = float(self.bb_m1["bb_inferior"].iloc[i_m1])
            rsi_m1 = float(self.rsi_m1.iloc[i_m1])
            conf_m1 = self._score_confluencia(c_m1, o_m1, h_m1, l_m1, sup_m1, inf_m1, rsi_m1, direccion=direccion)
            bonus_m5 = 0.15 if conf_m5 >= 0.35 else 0.0
            bonus_m1 = 0.15 if conf_m1 >= 0.35 else 0.0
            conf = min(1.0, conf + bonus_m5 + bonus_m1)

        momentum = abs(pend) > 0.0002
        tend_favor = (direccion == 1 and tend_h1 >= 0) or (direccion == -1 and tend_h1 <= 0)

        if "REV" in modo:
            if conf < 0.5:
                castigo = self.cfg.castigo_sin_condiciones
                return False, modo, direccion, castigo, 0.0
            prob = conf * (1.2 if tend_favor else 0.9)
            prob = float(np.clip(prob, 0.0, 1.0))
            if prob < self.cfg.min_probabilidad:
                castigo = self.cfg.castigo_sin_condiciones
                return False, modo, direccion, castigo, prob
            return True, modo, direccion, 0.0, prob

        if "CONT" in modo:
            if direccion == 1:
                rsi_ok = self.cfg.rsi_cont_long[0] <= rsi <= self.cfg.rsi_cont_long[1]
            else:
                rsi_ok = self.cfg.rsi_cont_short[0] <= rsi <= self.cfg.rsi_cont_short[1]
            if not (rsi_ok and tend_favor and momentum):
                castigo = self.cfg.castigo_contra_momentum
                return False, modo, direccion, castigo, 0.0
            prob = 0.75 if tend_favor else 0.55
            return True, modo, direccion, 0.0, prob

        if "SCALP" in modo:
            if not (conf >= 0.5 and momentum):
                castigo = self.cfg.castigo_contra_momentum
                return False, modo, direccion, castigo, 0.0
            prob = 0.7 if tend_favor else 0.5
            return True, modo, direccion, 0.0, prob

        return False, modo, direccion, self.cfg.castigo_sin_condiciones, 0.0

    def _score_confluencia(self, c, o, h, l, bb_sup, bb_inf, rsi, direccion=0):
        score = 0.0
        rango = max(1e-12, h - l)
        if direccion == 1:  # Compra (reversión desde abajo)
            toca_inf = l <= bb_inf
            rsi_extremo = rsi < 20
            mecha_rev = (o - l) / rango > 0.35 if o > c else (c - l) / rango > 0.35
            if toca_inf and rsi_extremo and mecha_rev:
                score = 0.7
            elif toca_inf and rsi < 25:
                score = 0.35
            elif l <= bb_inf + (bb_sup - bb_inf) * 0.05 and rsi < 25:
                score = 0.2
        elif direccion == -1:  # Venta (reversión desde arriba)
            toca_sup = h >= bb_sup
            rsi_extremo = rsi > 80
            mecha_rev = (h - o) / rango > 0.35 if o < c else (h - c) / rango > 0.35
            if toca_sup and rsi_extremo and mecha_rev:
                score = 0.7
            elif toca_sup and rsi > 75:
                score = 0.35
            elif h >= bb_sup - (bb_sup - bb_inf) * 0.05 and rsi > 75:
                score = 0.2
        else:
            dist_sup = (bb_sup - c) / max(1e-12, bb_sup - bb_inf)
            dist_inf = (c - bb_inf) / max(1e-12, bb_sup - bb_inf)
            if dist_sup < 0.15 or dist_inf < 0.15:
                score = 0.3
            elif dist_sup < 0.3 or dist_inf < 0.3:
                score = 0.15
            if rsi > 80 or rsi < 20:
                score += 0.2
        return float(np.clip(score, 0.0, 1.0))

    def _obs(self) -> np.ndarray:
        i = self.paso
        c = self._close()
        pb = float(self.bb["porcentaje_b"].iloc[i])
        rsi = float(self.rsi.iloc[i])
        bbw_est = float(self.bbw_estado.iloc[i])
        pend = float(self.pend_ema.iloc[i])
        atr = float(self.atr.iloc[i])
        i_m5 = min(i, len(self.m5) - 1)
        i_m1 = min(i, len(self.m1) - 1)
        c_m5 = float(self.m5["close"].iloc[i_m5])
        o_m5 = float(self.m5["open"].iloc[i_m5])
        h_m5 = float(self.m5["high"].iloc[i_m5])
        l_m5 = float(self.m5["low"].iloc[i_m5])
        sup_m5 = float(self.bb_m5["bb_superior"].iloc[i_m5])
        inf_m5 = float(self.bb_m5["bb_inferior"].iloc[i_m5])
        rsi_m5 = float(self.rsi_m5.iloc[i_m5])
        conf_m5 = self._score_confluencia(c_m5, o_m5, h_m5, l_m5, sup_m5, inf_m5, rsi_m5, direccion=0)
        c_m1 = float(self.m1["close"].iloc[i_m1])
        o_m1 = float(self.m1["open"].iloc[i_m1])
        h_m1 = float(self.m1["high"].iloc[i_m1])
        l_m1 = float(self.m1["low"].iloc[i_m1])
        sup_m1 = float(self.bb_m1["bb_superior"].iloc[i_m1])
        inf_m1 = float(self.bb_m1["bb_inferior"].iloc[i_m1])
        rsi_m1 = float(self.rsi_m1.iloc[i_m1])
        conf_m1 = self._score_confluencia(c_m1, o_m1, h_m1, l_m1, sup_m1, inf_m1, rsi_m1, direccion=0)
        tend_h1 = float(self.tendencia_h1.iloc[min(i, len(self.tendencia_h1) - 1)])
        pos_estado = 1.0 if self.pos_abierta and self.dir == 1 else (-1.0 if self.pos_abierta and self.dir == -1 else 0.0)
        pnl_norm = np.clip(self.pnl_dia / max(1e-12, self.cfg.balance_inicial) * 10, -1, 1)
        return np.array([
            np.clip(pb * 2 - 1, -1, 1),
            np.clip(rsi / 50 - 1, -1, 1),
            np.clip(bbw_est, -1, 1),
            np.clip(pend * 1000, -1, 1),
            float(conf_m5),
            float(conf_m1),
            np.clip(tend_h1, -1, 1),
            np.clip(atr / c * 100, -1, 1),
            pos_estado,
            pnl_norm,
        ], dtype=np.float32)

    def calcular_metricas(self) -> dict[str, Any]:
        ops = self.historial
        if not ops:
            return {"operaciones": 0, "winrate": 0.0, "profit_factor": 0.0,
                    "drawdown_max": 0.0, "sharpe": 0.0, "pnl_total": 0.0}
        pnls = np.array([o["pnl"] for o in ops], dtype=float)
        gan = pnls[pnls > 0]
        per = pnls[pnls < 0]
        wr = float(gan.size / pnls.size) if pnls.size else 0.0
        pf = float(gan.sum() / abs(per.sum())) if per.size and abs(per.sum()) > 1e-12 else (np.inf if gan.size else 0.0)
        curva = np.cumsum(pnls)
        dd = float((curva - np.maximum.accumulate(curva)).min())
        ret = pnls
        sharpe = float(ret.mean() / ret.std(ddof=0) * np.sqrt(252)) if ret.std(ddof=0) > 1e-12 else 0.0
        return {"operaciones": int(pnls.size), "winrate": wr, "profit_factor": pf,
                "drawdown_max": dd, "sharpe": sharpe, "pnl_total": float(pnls.sum())}

    def exportar_resultados(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        equity_df = pd.DataFrame({
            "datetime": self.timestamps_curve,
            "equity": self.equity_curve,
            "balance": self.balance_curve,
            "reward": self.rewards_curve,
        })
        trades = []
        for o in self.historial:
            trades.append({
                "ticket": id(o),
                "tipo": o.get("modo", ""),
                "direccion": "BUY" if o.get("dir", 0) == 1 else "SELL",
                "open_time": o.get("ts_entrada", ""),
                "open_price": round(o.get("precio_entrada", 0), 2),
                "sl": round(o.get("sl", 0), 2) if "sl" in o else None,
                "tp": round(o.get("tp", 0), 2) if "tp" in o else None,
                "lote": round(o.get("lote", 0), 2) if "lote" in o else None,
                "close_time": o.get("ts_salida", ""),
                "close_price": round(o.get("precio_salida", 0), 2) if "precio_salida" in o else None,
                "pnl": round(o.get("pnl", 0), 2),
                "resultado": o.get("resultado", ""),
            })
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        metricas = self.calcular_metricas()
        return equity_df, trades_df, metricas

    def _equity(self, precio: float) -> float:
        if not self.pos_abierta:
            return float(self.balance)
        flotante = (precio - self.precio_entrada) * self.dir * self.lote_remanente
        return float(self.balance + flotante)

    def _actualizar_picos(self, ts) -> None:
        if hasattr(ts, 'normalize'):
            dia = ts.normalize()
        else:
            dia = self.paso // 26
        if self.fecha_equity_dia is None or dia != self.fecha_equity_dia:
            self.fecha_equity_dia = dia
            self.pico_equity_dia = self.equity
            self.ops_hoy = 0
            self.pnl_dia = 0.0
            self.barras_desde_inicio_dia = 0
        else:
            self.pico_equity_dia = max(self.pico_equity_dia, self.equity)
            self.barras_desde_inicio_dia += 1


# ═══════════════════════════════════════════════════════════════════════════════
# 6. HYPERPARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════
DEVICE = "cpu"  # Force CPU: CUDA kernel compatibility issue on Kaggle T4
TIMESTEPS = 100_000
N_EVAL_EPISODES = 100
N_STEPS = 2048
BATCH_SIZE = 64
LEARNING_RATE = 3e-4
GAMMA = 0.995
GAE_LAMBDA = 0.95
ENT_COEF = 0.01
VF_COEF = 0.5
MAX_GRAD_NORM = 0.5

MODELS = WORKING / "modelos"
MODELS.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. TRAIN
# ═══════════════════════════════════════════════════════════════════════════════
def entrenar():
    df_m15, df_m5, df_m1, df_h1 = generar_dataset_unificado()
    total = len(df_m15)
    min_len = min(total, 5000)

    def make_env():
        start = np.random.randint(0, max(1, total - min_len))
        end = start + min_len
        return EntornoHibridoUnificado(
            df_m15.iloc[start:end].copy(),
            df_m5.iloc[start:end].copy(),
            df_m1.iloc[start:end].copy(),
            df_h1.iloc[start:end].copy(),
        )

    env = DummyVecEnv([make_env])

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        device=DEVICE,
        n_steps=N_STEPS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        gamma=GAMMA,
        gae_lambda=GAE_LAMBDA,
        ent_coef=ENT_COEF,
        vf_coef=VF_COEF,
        max_grad_norm=MAX_GRAD_NORM,
        tensorboard_log=str(MODELS / "tb"),
    )

    checkpoint = CheckpointCallback(save_freq=100_000, save_path=str(MODELS), name_prefix="ppo_unificado")
    eval_env = DummyVecEnv([make_env])
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(MODELS),
        log_path=str(MODELS),
        eval_freq=50_000,
        deterministic=True,
        render=False,
        n_eval_episodes=50,
    )

    print(f"[TRAIN] Iniciando entrenamiento: {TIMESTEPS:,} steps | Device={DEVICE}")
    model.learn(total_timesteps=TIMESTEPS, callback=[checkpoint, eval_callback])
    model.save(str(MODELS / "modelo_final"))
    print("[TRAIN] Entrenamiento completado.")
    return model, env


# ═══════════════════════════════════════════════════════════════════════════════
# 8. EVAL
# ═══════════════════════════════════════════════════════════════════════════════
def evaluar(model, n_episodios=2000):
    df_m15, df_m5, df_m1, df_h1 = generar_dataset_unificado()
    len_df = len(df_m15)
    resultados = []
    for ep in range(n_episodios):
        start = random.randint(0, max(0, len_df - 5000))
        end = start + 5000
        env = EntornoHibridoUnificado(
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
        resultados.append({
            "ep": ep,
            "pnl": info.get("pnl", 0),
            "ops": info.get("num_ops", 0),
            "wr": info.get("winrate", 0),
            "reward": info.get("reward_total", 0),
        })
        if ep % 200 == 0:
            print(f"[EVAL] Ep={ep} | PnL={info.get('pnl',0):.0f} | Ops={info.get('num_ops',0)} | WR={info.get('winrate',0):.1f}%")
    wrs = [r["wr"] for r in resultados if r["ops"] > 0]
    pnl_total = sum(r["pnl"] for r in resultados)
    avg_ops = sum(r["ops"] for r in resultados) / len(resultados)
    print(f"\n[EVAL FINAL] WR medio: {np.mean(wrs):.1%} | PnL total: {pnl_total:.0f} | Ops/ep: {avg_ops:.1f}")
    return resultados


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ONNX EXPORT (ActorNet wrapper, opset 14)
# ═══════════════════════════════════════════════════════════════════════════════
class ActorNet(nn.Module):
    def __init__(self, policy):
        super().__init__()
        self.mlp_extractor = policy.mlp_extractor
        self.action_net = policy.action_net

    def forward(self, observations: torch.Tensor):
        latent_pi, _ = self.mlp_extractor(observations)
        return self.action_net(latent_pi)


def exportar_onnx(model, path_out: str):
    import onnx
    import onnxruntime as ort

    policy = model.policy.to("cpu")
    policy.eval()
    actor = ActorNet(policy)
    actor.eval()

    dummy_input = torch.randn(1, 10)
    torch.onnx.export(
        actor,
        dummy_input,
        path_out,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["obs"],
        output_names=["action_logits"],
        dynamic_axes={"obs": {0: "batch"}, "action_logits": {0: "batch"}},
    )

    onnx_model = onnx.load(path_out)
    onnx.checker.check_model(onnx_model)

    sess = ort.InferenceSession(path_out)
    test_input = np.random.randn(1, 10).astype(np.float32)
    ort_out = sess.run(None, {"obs": test_input})
    torch_out = actor(torch.from_numpy(test_input))
    diff = abs(float(torch_out.detach().numpy()[0][0]) - float(ort_out[0][0][0]))
    print(f"[ONNX] Exportado: {path_out} | Diff torch/onnx: {diff:.6f}")
    return path_out


# ═══════════════════════════════════════════════════════════════════════════════
# 10. MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    model, env = entrenar()
    resultados = evaluar(model, N_EVAL_EPISODES)
    ruta_onnx = str(MODELS / "bot_unificado.onnx")
    exportar_onnx(model, ruta_onnx)

    reporte = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timesteps": TIMESTEPS,
        "eval_episodes": N_EVAL_EPISODES,
        "avg_winrate": float(np.mean([r["wr"] for r in resultados if r["ops"] > 0])),
        "avg_ops": float(np.mean([r["ops"] for r in resultados])),
        "total_pnl": float(sum(r["pnl"] for r in resultados)),
        "onnx_path": ruta_onnx,
    }
    with open(WORKING / "reporte_unificado.json", "w") as f:
        json.dump(reporte, f, indent=2)
    print("\n[OK] Pipeline completado. Reporte:", WORKING / "reporte_unificado.json")

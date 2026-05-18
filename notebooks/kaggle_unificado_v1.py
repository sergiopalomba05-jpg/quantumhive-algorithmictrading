#!/usr/bin/env python3
"""
================================================================================
KAGGLE — ENTRENAMIENTO BOT HÍBRIDO UNIFICADO v1
================================================================================
1 cerebro: Reversión + Continuación + Scalper
Datos NY M15 pre-filtrados | 10 features | 7 acciones
Reward simplificado | Probabilidad suave ≥0.7 | 1M steps PPO
ONNX export opset 11 (compatible MT5)

Instrucciones Kaggle:
  1. Nuevo Notebook → GPU V100
  2. Add Dataset: sergiopalomba/quantumhive-fusion (o datos NY M15/M5/M1)
  3. Settings → Internet ON
  4. Run All
================================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 1: Dependencias
# ═══════════════════════════════════════════════════════════════════════════════
!pip install -q stable-baselines3 gymnasium onnx onnxruntime onnxscript pandas numpy pyarrow

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 2: Imports
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import os, sys, json, math, warnings
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback

warnings.filterwarnings('ignore')
print(f'[OK] Torch: {torch.__version__} | CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'[OK] GPU: {torch.cuda.get_device_name(0)}')
    torch.backends.cudnn.benchmark = True

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 3: Configuración
# ═══════════════════════════════════════════════════════════════════════════════
WORKING = Path('/kaggle/working')
MODELS = WORKING / 'modelo_unificado'
MODELS.mkdir(exist_ok=True)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

TIMESTEPS = 1_000_000
N_EVAL_EPISODES = 2000
BATCH_SIZE = 256
N_STEPS = 2048
LEARNING_RATE = 3e-4
GAMMA = 0.995
GAE_LAMBDA = 0.92
ENT_COEF = 0.01
VF_COEF = 0.5
MAX_GRAD_NORM = 0.5

print(f'[CONFIG] Device: {DEVICE} | Timesteps: {TIMESTEPS:,}')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 4: Indicadores inline (sin dependencias externas)
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

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 5: Generar Dataset Unificado desde CSVs de múltiples temporalidades
# ═══════════════════════════════════════════════════════════════════════════════
def buscar_csv(name_hint: str):
    for dp, _, fnames in os.walk('/kaggle/input'):
        for f in fnames:
            if f.lower().endswith('.csv') and name_hint.lower() in f.lower():
                return Path(dp) / f
    return None

def _parsear_fecha(row) -> datetime:
    """Parsea formato MT5: YYYY.MM.DD HH:MM:SS"""
    fecha_raw = str(row["<DATE>"])
    fecha = fecha_raw.replace(".", "").replace("-", "")
    hora_raw = str(row["<TIME>"])
    hora = hora_raw.replace(":", "")
    hora = hora.zfill(6)
    return datetime(
        year=int(fecha[0:4]), month=int(fecha[4:6]), day=int(fecha[6:8]),
        hour=int(hora[0:2]), minute=int(hora[2:4]), second=int(hora[4:6]),
    )

def _cargar_csv_kaggle(path: Path | None) -> pd.DataFrame:
    """Carga CSV de Kaggle input, maneja formato preparado (time) o MT5 crudo (<DATE>/<TIME>)."""
    if path is None:
        return pd.DataFrame()
    df = pd.read_csv(path, sep=None, engine="python")
    # Formato MT5 crudo
    if "<DATE>" in df.columns and "<TIME>" in df.columns:
        df["time"] = df.apply(_parsear_fecha, axis=1)
        df = df.rename(columns={
            "<OPEN>": "open", "<HIGH>": "high", "<LOW>": "low",
            "<CLOSE>": "close", "<TICKVOL>": "volume",
        })
    elif "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    else:
        raise ValueError(f"Formato desconocido en {path}. Columnas: {list(df.columns)}")
    return df[["time", "open", "high", "low", "close", "volume"]].copy().set_index("time").sort_index()

def generar_dataset_unificado(
    path_m15: Path | None = None,
    path_m5: Path | None = None,
    path_m1: Path | None = None,
    path_h1: Path | None = None,
    simbolo: str = "US30",
) -> pd.DataFrame:
    """Une M15 (base) con indicadores precomputados de M5/M1/H1."""
    if path_m15 is None:
        path_m15 = buscar_csv("us30") or buscar_csv("m15")
    df = _cargar_csv_kaggle(path_m15)
    if df.empty:
        raise ValueError(f"No se pudo cargar M15 desde {path_m15}")

    # Filtrar sesión NY
    df["hora"] = df.index.hour + df.index.minute / 60.0
    # Invierno 13:30-20:00 UTC, verano 14:30-21:00 (usamos rango amplio 13:00-21:00)
    df = df[(df["hora"] >= 13.5) & (df["hora"] <= 21.0)].copy()
    df = df.drop(columns=["hora"], errors="ignore")

    # Indicadores M15
    bb15 = calcular_bollinger(df["close"])
    df["bb_sup"] = bb15["sup"]
    df["bb_inf"] = bb15["inf"]
    df["bb_media"] = bb15["media"]
    df["bbw"] = bb15["bbw"]
    df["pb"] = bb15["pb"]
    df["rsi"] = calcular_rsi(df["close"])
    df["atr"] = calcular_atr(df)
    df["ema50"] = df["close"].astype(float).ewm(span=50, adjust=False).mean()
    df["pend_ema"] = df["ema50"].diff().fillna(0)

    # BBW estado
    bbw = df["bbw"].astype(float)
    p20 = bbw.rolling(200, min_periods=20).quantile(0.2)
    p80 = bbw.rolling(200, min_periods=20).quantile(0.8)
    df["bbw_estado"] = np.where(bbw < p20, -1.0, np.where(bbw > p80, 1.0, 0.0))

    # Tendencia H1 (forward-fill desde H1 si existe)
    if path_h1 is not None:
        df_h1 = _cargar_csv_kaggle(path_h1)
        c_h1 = df_h1["close"].astype(float)
        ema50_h1 = c_h1.ewm(span=50, adjust=False).mean()
        tend_h1 = pd.Series(np.sign(c_h1 - ema50_h1).fillna(0), index=df_h1.index)
        df["tendencia_h1"] = tend_h1.reindex(df.index, method="ffill").fillna(0)
    else:
        df["tendencia_h1"] = 0.0

    # Confluencias M5 (reindex forward-fill)
    if path_m5 is not None:
        df_m5 = _cargar_csv_kaggle(path_m5)
        bb5 = calcular_bollinger(df_m5["close"])
        df_m5["bb_sup"] = bb5["sup"]
        df_m5["bb_inf"] = bb5["inf"]
        df_m5["rsi"] = calcular_rsi(df_m5["close"])
        for col in ["open", "high", "low", "close", "bb_sup", "bb_inf", "rsi"]:
            df[f"m5_{col}"] = df_m5[col].reindex(df.index, method="ffill")
    else:
        for col in ["open", "high", "low", "close", "bb_sup", "bb_inf", "rsi"]:
            df[f"m5_{col}"] = df[col] if col in df.columns else df["close"]

    # Confluencias M1
    if path_m1 is not None:
        df_m1 = _cargar_csv_kaggle(path_m1)
        bb1 = calcular_bollinger(df_m1["close"])
        df_m1["bb_sup"] = bb1["sup"]
        df_m1["bb_inf"] = bb1["inf"]
        df_m1["rsi"] = calcular_rsi(df_m1["close"])
        for col in ["open", "high", "low", "close", "bb_sup", "bb_inf", "rsi"]:
            df[f"m1_{col}"] = df_m1[col].reindex(df.index, method="ffill")
    else:
        for col in ["open", "high", "low", "close", "bb_sup", "bb_inf", "rsi"]:
            df[f"m1_{col}"] = df[col] if col in df.columns else df["close"]

    # Confirmaciones M5/M1 como score continuo de confluencia
    def score_confluencia(c, o, h, l, sup, inf, rsi):
        score = 0.0
        rango = np.maximum(1e-12, sup - inf)
        cerca_banda = np.minimum((sup - c) / rango, (c - inf) / rango)
        cerca_banda = np.where((c <= sup) & (c >= inf), cerca_banda, 0.0)
        score += 0.3 * np.maximum(0.0, 1.0 - cerca_banda * 3.0)
        cuerpo = np.abs(c - o)
        rango_barra = np.maximum(1e-12, h - l)
        mecha_inf = np.where(c > o, o - l, c - l)
        mecha_sup = np.where(c > o, h - c, h - o)
        score += 0.35 * ((mecha_inf > cuerpo * 1.5) & (mecha_inf > rango_barra * 0.3)).astype(float)
        score += 0.35 * ((mecha_sup > cuerpo * 1.5) & (mecha_sup > rango_barra * 0.3)).astype(float)
        score += 0.2 * ((rsi < 30.0) | (rsi > 70.0)).astype(float)
        score += 0.1 * (((rsi >= 30.0) & (rsi < 40.0)) | ((rsi > 60.0) & (rsi <= 70.0))).astype(float)
        score += 0.15 * (((l <= inf) & (c > inf)) | ((h >= sup) & (c < sup))).astype(float)
        return np.clip(score, 0.0, 1.0)

    df["conf_m5"] = score_confluencia(
        df["m5_close"].astype(float), df["m5_open"].astype(float),
        df["m5_high"].astype(float), df["m5_low"].astype(float),
        df["m5_bb_sup"].astype(float), df["m5_bb_inf"].astype(float),
        df["m5_rsi"].astype(float)
    )
    df["conf_m1"] = score_confluencia(
        df["m1_close"].astype(float), df["m1_open"].astype(float),
        df["m1_high"].astype(float), df["m1_low"].astype(float),
        df["m1_bb_sup"].astype(float), df["m1_bb_inf"].astype(float),
        df["m1_rsi"].astype(float)
    )

    # Clean
    df = df.dropna()
    # print(f"[DATASET] Filas: {len(df)} | Desde: {df.index[0]} | Hasta: {df.index[-1]}")
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 6: Entorno Híbrido Unificado (inline para Kaggle)
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class ConfigHibrido:
    balance_inicial: float = 10_000.0
    riesgo_pct: float = 0.01
    bb_periodo: int = 30
    bb_desv: float = 3.0
    rsi_periodo: int = 7
    atr_periodo: int = 14
    atr_sl_mult: float = 1.5
    atr_sl_scalp: float = 1.2
    rr_tp1: float = 1.0
    rr_tp2: float = 2.0
    rr_scalp: float = 1.5
    fraccion_tp1: float = 0.5
    rsi_rev_long_max: float = 35.0
    rsi_rev_short_min: float = 65.0
    rsi_cont_long: Tuple[float, float] = (45.0, 75.0)
    rsi_cont_short: Tuple[float, float] = (25.0, 55.0)
    castigo_contra_momentum: float = -0.6
    castigo_sin_condiciones: float = -0.1
    castigo_inactividad_ventana: float = -0.15
    castigo_contra_tendencia_h1: float = -0.4
    recompensa_tp2: float = 1.0
    recompensa_tp1: float = 0.8
    recompensa_be: float = 0.4
    castigo_sl: float = -1.2
    costo_holding: float = -0.005
    incentivo_apertura: float = 0.15
    min_probabilidad: float = 0.7
    ventana_apertura_barras: int = 8

class EntornoHibridoUnificado(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, df: pd.DataFrame, cfg: ConfigHibrido | None = None) -> None:
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.cfg = cfg or ConfigHibrido()
        self.n = len(self.df)

        self.balance = float(self.cfg.balance_inicial)
        self.equity = self.balance
        self.pico_equity = self.balance
        self.pico_equity_dia = self.balance
        self.fecha_equity_dia = None
        self.paso = 0
        self.precio_inicial = float(self.df.iloc[0]["close"])

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
        self.historial: List[Dict] = []

        self.action_space = spaces.Discrete(7)
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(10,), dtype=np.float32)

    def _row(self):
        return self.df.iloc[self.paso]

    def _ts(self):
        return self.df.index[self.paso] if hasattr(self.df.index[self.paso], 'strftime') else self.paso

    def reset(self, *, seed=None, options=None):
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
        return self._obs(), {"balance": self.balance, "equity": self.equity}

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

    def _score_confluencia(self, c, o, h, l, sup, inf, rsi):
        score = 0.0
        rango = max(1e-12, sup - inf)
        cerca_banda = min((sup - c) / rango, (c - inf) / rango) if (c <= sup and c >= inf) else 0.0
        score += 0.3 * max(0.0, 1.0 - cerca_banda * 3.0)
        cuerpo = abs(c - o)
        rango_barra = max(1e-12, h - l)
        if c > o:
            mecha_inf = o - l
            mecha_sup = h - c
        else:
            mecha_inf = c - l
            mecha_sup = h - o
        if mecha_inf > cuerpo * 1.5 and mecha_inf > rango_barra * 0.3:
            score += 0.35
        elif mecha_sup > cuerpo * 1.5 and mecha_sup > rango_barra * 0.3:
            score += 0.35
        if rsi < 30.0 or rsi > 70.0:
            score += 0.2
        elif rsi < 40.0 or rsi > 60.0:
            score += 0.1
        if (l <= inf and c > inf) or (h >= sup and c < sup):
            score += 0.15
        return float(np.clip(score, 0.0, 1.0))

    def _obs(self):
        r = self._row()
        pb = float(r["pb"])
        rsi = float(r["rsi"])
        bbw_est = float(r["bbw_estado"])
        pend = float(r["pend_ema"])
        atr = float(r["atr"])
        c = float(r["close"])
        conf_m5 = float(r["conf_m5"])
        conf_m1 = float(r["conf_m1"])
        tend_h1 = float(r.get("tendencia_h1", 0))
        pos_estado = 1.0 if self.pos_abierta and self.dir == 1 else (-1.0 if self.pos_abierta and self.dir == -1 else 0.0)
        pnl_norm = np.clip(self.pnl_dia / max(1e-12, self.cfg.balance_inicial) * 10, -1, 1)
        return np.array([
            np.clip(pb * 2 - 1, -1, 1),
            np.clip(rsi / 50 - 1, -1, 1),
            np.clip(bbw_est, -1, 1),
            np.clip(pend * 1000, -1, 1),
            conf_m5,
            conf_m1,
            np.clip(tend_h1, -1, 1),
            np.clip(atr / c * 100, -1, 1),
            pos_estado,
            pnl_norm,
        ], dtype=np.float32)

    def step(self, action: int):
        if self.paso >= self.n - 1:
            if self.pos_abierta:
                self._cerrar_total(self.paso, float(self._row()["close"]), "fin_datos")
            return self._obs(), 0.0, True, False, {"motivo": "fin_datos"}

        r = self._row()
        ts = self._ts()
        self._actualizar_picos(ts)
        precio = float(r["close"])
        high = float(r["high"])
        low = float(r["low"])
        info: Dict[str, Any] = {}
        reward = self.cfg.costo_holding if self.pos_abierta else 0.0

        # Castigo por inactividad en ventana de apertura NY (primeras 120 min = 8 barras)
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
            ok, modo, direccion, castigo, prob = self._evaluar_apertura(action, precio, high, low, r)
            if ok:
                self._abrir(modo, direccion, precio, ts)
                reward += self.cfg.incentivo_apertura * prob
                info["apertura"] = {"modo": modo, "dir": direccion, "prob": prob}
            else:
                reward += castigo
                info["rechazo"] = {"castigo": castigo, "razon": modo, "prob": prob}

        self.equity = self._equity(precio)
        self.pico_equity = max(self.pico_equity, self.equity)
        self.paso += 1
        terminado = self.paso >= self.n - 1
        return self._obs(), float(reward), bool(terminado), False, info

    def _gestionar_posicion(self, ts, high, low):
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

    def _toco(self, low, high, nivel):
        return bool(np.isfinite(nivel) and low <= nivel <= high)

    def _cerrar_parcial(self, ts, precio):
        frac = self.cfg.fraccion_tp1
        lote_cerrar = min(self.lote_total * frac, self.lote_remanente)
        pnl = (precio - self.precio_entrada) * self.dir * lote_cerrar
        self.balance += float(pnl)
        self.lote_remanente -= lote_cerrar
        self.be_activado = True
        self.sl = float(self.precio_entrada)
        self.pnl_dia += float(pnl)
        self.historial.append({
            "ts_entrada": self._ts_entrada_val, "ts_salida": ts, "dir": self.dir,
            "modo": self.modo, "precio_entrada": self.precio_entrada,
            "precio_salida": precio, "lote": lote_cerrar, "pnl": float(pnl),
            "resultado": "tp1"
        })

    def _cerrar_total(self, ts, precio, resultado):
        if not self.pos_abierta:
            return
        lote = self.lote_remanente
        pnl = (precio - self.precio_entrada) * self.dir * lote
        self.balance += float(pnl)
        self.pnl_dia += float(pnl)
        self.historial.append({
            "ts_entrada": self._ts_entrada_val, "ts_salida": ts, "dir": self.dir,
            "modo": self.modo, "precio_entrada": self.precio_entrada,
            "precio_salida": precio, "lote": lote, "pnl": float(pnl),
            "resultado": resultado
        })
        self._reset_posicion()

    def _abrir(self, modo, direccion, precio, ts):
        self.pos_abierta = True
        self.dir = int(np.sign(direccion))
        self.modo = modo
        self.precio_entrada = float(precio)
        self._ts_entrada_val = ts
        atr = float(self._row()["atr"])
        sl_dist = atr * (self.cfg.atr_sl_scalp if "SCALP" in modo else self.cfg.atr_sl_mult)
        rr = self.cfg.rr_scalp if "SCALP" in modo else self.cfg.rr_tp2
        d = self.dir
        self.sl = precio - d * sl_dist
        self.tp1 = precio + d * sl_dist * self.cfg.rr_tp1
        self.tp2 = precio + d * sl_dist * rr
        riesgo = self.balance * self.cfg.riesgo_pct
        self.lote_total = self.lote_remanente = float(max(0.0, riesgo / max(sl_dist, 1e-12)))
        self.be_activado = False
        self.ops_hoy += 1

    def _equity(self, precio):
        if not self.pos_abierta:
            return float(self.balance)
        flotante = (precio - self.precio_entrada) * self.dir * self.lote_remanente
        return float(self.balance + flotante)

    def _actualizar_picos(self, ts):
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

    def _evaluar_apertura(self, action, precio, high, low, r):
        c = precio
        o = float(r["open"])
        sup = float(r["bb_sup"])
        inf = float(r["bb_inf"])
        media = float(r["bb_media"])
        rsi = float(r["rsi"])
        bbw_est = float(r["bbw_estado"])
        pend = float(r["pend_ema"])
        conf_m5 = float(r["conf_m5"])
        conf_m1 = float(r["conf_m1"])
        tend_h1 = float(r.get("tendencia_h1", 0))

        if action == 1:
            modo, direccion = "REV", 1
        elif action == 2:
            modo, direccion = "REV", -1
        elif action == 3:
            modo, direccion = "CONT", 1
        elif action == 4:
            modo, direccion = "CONT", -1
        elif action == 5:
            modo, direccion = "SCALP", 1
        else:
            modo, direccion = "SCALP", -1

        score = 0.0

        # Detectar momentum fuerte en M15
        momentum_up = (c > o) and (c - o) > (high - low) * 0.3 and pend > 0
        momentum_down = (c < o) and (o - c) > (high - low) * 0.3 and pend < 0

        if modo == "REV":
            if direccion == 1:
                score += 0.3 if (low <= inf and c > inf) else 0.0
                score += 0.25 if (rsi < self.cfg.rsi_rev_long_max) else max(0.0, 0.25 * (50 - rsi) / 15)
                # REV LONG contra momentum alcista = suicidio
                if momentum_up:
                    score -= 0.6
                    if bbw_est > 0:
                        score -= 0.4
            else:
                score += 0.3 if (high >= sup and c < sup) else 0.0
                score += 0.25 if (rsi > self.cfg.rsi_rev_short_min) else max(0.0, 0.25 * (rsi - 50) / 15)
                # REV SHORT contra momentum bajista = suicidio
                if momentum_down:
                    score -= 0.6
                    if bbw_est > 0:
                        score -= 0.4
            score += 0.15 * conf_m5 + 0.1 * conf_m1
            score += 0.1 if bbw_est < 0 else 0.0

        elif modo == "CONT":
            if direccion == 1:
                cuerpo = c > sup or (c - sup) / max(1e-12, sup - media) > 0.2
                score += 0.25 if cuerpo else max(0.0, (c - media) / max(1e-12, sup - media)) * 0.25
                score += 0.2 if (self.cfg.rsi_cont_long[0] <= rsi <= self.cfg.rsi_cont_long[1]) else 0.1
                score += 0.15 if (pend > 0 or tend_h1 >= 0) else 0.0
                # Boost extra si momentum confirmado
                if momentum_up and conf_m5 > 0.5 and conf_m1 > 0.5:
                    score += 0.25
            else:
                cuerpo = c < inf or (inf - c) / max(1e-12, media - inf) > 0.2
                score += 0.25 if cuerpo else max(0.0, (media - c) / max(1e-12, media - inf)) * 0.25
                score += 0.2 if (self.cfg.rsi_cont_short[0] <= rsi <= self.cfg.rsi_cont_short[1]) else 0.1
                score += 0.15 if (pend < 0 or tend_h1 <= 0) else 0.0
                # Boost extra si momentum confirmado
                if momentum_down and conf_m5 > 0.5 and conf_m1 > 0.5:
                    score += 0.25
            score += 0.15 * conf_m5 + 0.1 * conf_m1
            score += 0.1 if bbw_est > 0 else 0.0

        elif modo == "SCALP":
            score += 0.3 if conf_m5 else 0.0
            score += 0.3 if conf_m1 else 0.0
            score += 0.1 if bbw_est > 0 else (0.05 if bbw_est == 0 else 0.0)
            # Boost si momentum alineado
            if direccion == 1 and momentum_up:
                score += 0.2
            if direccion == -1 and momentum_down:
                score += 0.2
            if direccion == 1:
                score += 0.15 if (low <= media <= c) else 0.0
                score += 0.15 if (rsi > 40) else 0.0
            else:
                score += 0.15 if (high >= media >= c) else 0.0
                score += 0.15 if (rsi < 60) else 0.0

        # Castigo por operar contra tendencia H1 fuerte
        if abs(tend_h1) >= 0.5:
            if np.sign(direccion) != np.sign(tend_h1):
                if modo == "CONT":
                    score += self.cfg.castigo_contra_tendencia_h1
                elif modo == "SCALP":
                    score -= 0.15
                elif modo == "REV":
                    if (direccion == 1 and rsi > 30) or (direccion == -1 and rsi < 70):
                        score -= 0.2

        prob = float(np.clip(score, 0.0, 1.0))
        ok = prob >= self.cfg.min_probabilidad
        if ok:
            return True, modo, direccion, 0.0, prob
        else:
            return False, modo, direccion, self.cfg.castigo_sin_condiciones * (1.0 - prob), prob

    def calcular_metricas(self):
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
        sharpe = float(pnls.mean() / pnls.std(ddof=0) * np.sqrt(252)) if pnls.std(ddof=0) > 1e-12 else 0.0
        return {"operaciones": int(pnls.size), "winrate": wr, "profit_factor": pf,
                "drawdown_max": dd, "sharpe": sharpe, "pnl_total": float(pnls.sum())}

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 7: Entrenamiento PPO
# ═══════════════════════════════════════════════════════════════════════════════
def entrenar():
    # Cargar datos
    df = generar_dataset_unificado()

    # Entorno vectorizado (NO barajar - series temporal)
    def make_env():
        # Para entrenamiento: usar un slice aleatorio de días consecutivos
        total = len(df)
        min_len = min(total, 5000)
        start = np.random.randint(0, max(1, total - min_len))
        return EntornoHibridoUnificado(df.iloc[start:start + min_len].reset_index(drop=True))

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

    # Callbacks
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

    print(f"[TRAIN] Iniciando entrenamiento: {TIMESTEPS:,} steps...")
    model.learn(total_timesteps=TIMESTEPS, callback=[checkpoint, eval_callback])
    model.save(str(MODELS / "modelo_final"))
    print("[TRAIN] Entrenamiento completado.")
    return model, env

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 8: Evaluación
# ═══════════════════════════════════════════════════════════════════════════════
def evaluar(model, n_episodios=2000):
    df_eval = generar_dataset_unificado()
    len_df = len(df_eval)
    resultados = []
    for ep in range(n_episodios):
        start = random.randint(0, max(0, len_df - 5000))
        env = EntornoHibridoUnificado(df_eval.iloc[start:start + 5000].reset_index(drop=True))
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
# CELDA 9: Export ONNX
# ═══════════════════════════════════════════════════════════════════════════════
def exportar_onnx(model, path_out: str):
    import onnx
    policy = model.policy.to("cpu")
    policy.eval()

    dummy_input = torch.randn(1, 10)
    torch.onnx.export(
        policy,
        dummy_input,
        path_out,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=["obs"],
        output_names=["action", "value"],
        dynamic_axes={"obs": {0: "batch"}, "action": {0: "batch"}, "value": {0: "batch"}},
    )

    # Validar
    onnx_model = onnx.load(path_out)
    onnx.checker.check_model(onnx_model)

    # Verificar inferencia
    import onnxruntime as ort
    sess = ort.InferenceSession(path_out)
    test_input = np.random.randn(1, 10).astype(np.float32)
    ort_out = sess.run(None, {"obs": test_input})
    torch_out = policy(torch.from_numpy(test_input))
    diff = abs(float(torch_out[0].detach().numpy()[0][0]) - float(ort_out[0][0][0]))
    print(f"[ONNX] Exportado: {path_out} | Diff torch/onnx: {diff:.6f}")
    return path_out

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 10: Ejecutar pipeline
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    model, env = entrenar()
    resultados = evaluar(model, N_EVAL_EPISODES)
    ruta_onnx = str(MODELS / "bot_unificado.onnx")
    exportar_onnx(model, ruta_onnx)

    # Reporte
    reporte = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timesteps": TIMESTEPS,
        "eval_episodios": N_EVAL_EPISODES,
        "avg_winrate": float(np.mean([r["winrate"] for r in resultados if r["operaciones"] > 0])),
        "avg_ops": float(np.mean([r["operaciones"] for r in resultados])),
        "total_pnl": float(sum(r["pnl_total"] for r in resultados)),
        "onnx_path": ruta_onnx,
    }
    with open(WORKING / "reporte_unificado.json", "w") as f:
        json.dump(reporte, f, indent=2)
    print("\n[OK] Pipeline completado. Reporte:", WORKING / "reporte_unificado.json")

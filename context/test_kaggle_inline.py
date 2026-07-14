"""Test del entorno inline del notebook Kaggle."""
import sys, numpy as np, pandas as pd

# Simular las funciones inline del notebook
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
    tr = pd.concat([(h-l).abs(), (h-cp).abs(), (l-cp).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/periodo, adjust=False).mean()

# Datos sintéticos NY
n = 5000
idx = pd.date_range('2024-01-01 13:30', periods=n, freq='15min')
c = 35000 + np.cumsum(np.random.randn(n) * 5)
o = c + np.random.randn(n) * 2
h = np.maximum(np.maximum(c, o), np.maximum(c, o) + np.abs(np.random.randn(n)) * 3)
l = np.minimum(np.minimum(c, o), np.minimum(c, o) - np.abs(np.random.randn(n)) * 3)

df = pd.DataFrame({'open': o, 'high': h, 'low': l, 'close': c}, index=idx)
df["hora"] = df.index.hour + df.index.minute / 60.0
df = df[(df["hora"] >= 13.5) & (df["hora"] <= 21.0)].drop(columns=["hora"])

bb = calcular_bollinger(df["close"])
df["bb_sup"] = bb["sup"]
df["bb_inf"] = bb["inf"]
df["bb_media"] = bb["media"]
df["bbw"] = bb["bbw"]
df["pb"] = bb["pb"]
df["rsi"] = calcular_rsi(df["close"])
df["atr"] = calcular_atr(df)
df["ema50"] = df["close"].astype(float).ewm(span=50, adjust=False).mean()
df["pend_ema"] = df["ema50"].diff().fillna(0)
bbw = df["bbw"].astype(float)
p20 = bbw.rolling(200, min_periods=20).quantile(0.2)
p80 = bbw.rolling(200, min_periods=20).quantile(0.8)
df["bbw_estado"] = np.where(bbw < p20, -1.0, np.where(bbw > p80, 1.0, 0.0))
df["tendencia_h1"] = 0.0
df["m5_bb_sup"] = df["bb_sup"]
df["m5_bb_inf"] = df["bb_inf"]
df["m5_rsi"] = df["rsi"]
df["m1_bb_sup"] = df["bb_sup"]
df["m1_bb_inf"] = df["bb_inf"]
df["m1_rsi"] = df["rsi"]
df["conf_m5"] = (
    ((df["low"] <= df["m5_bb_inf"]) & (df["close"] > df["m5_bb_inf"])) |
    ((df["high"] >= df["m5_bb_sup"]) & (df["close"] < df["m5_bb_sup"]))
).astype(float)
df["conf_m1"] = (
    (df["low"] <= df["m1_bb_inf"]) |
    (df["high"] >= df["m1_bb_sup"])
).astype(float)
df = df.dropna().reset_index(drop=True)

import gymnasium as gym
from gymnasium import spaces
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class ConfigHibrido:
    balance_inicial = 10000.0
    riesgo_pct = 0.01
    atr_sl_mult = 1.5
    atr_sl_scalp = 1.2
    rr_tp1 = 1.0
    rr_tp2 = 2.0
    rr_scalp = 1.5
    fraccion_tp1 = 0.5
    rsi_rev_long_max = 35.0
    rsi_rev_short_min = 65.0
    rsi_cont_long = (45.0, 75.0)
    rsi_cont_short = (25.0, 55.0)
    castigo_contra_momentum = -0.3
    castigo_sin_condiciones = -0.1
    recompensa_tp2 = 1.0
    recompensa_tp1 = 0.8
    recompensa_be = 0.4
    castigo_sl = -1.2
    costo_holding = -0.005
    incentivo_apertura = 0.15
    min_probabilidad = 0.7

class EntornoHibridoUnificado(gym.Env):
    metadata = {"render_modes": []}
    def __init__(self, df, cfg=None):
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
            np.clip(pb * 2 - 1, -1, 1), np.clip(rsi / 50 - 1, -1, 1),
            np.clip(bbw_est, -1, 1), np.clip(pend * 1000, -1, 1),
            conf_m5, conf_m1, np.clip(tend_h1, -1, 1),
            np.clip(atr / c * 100, -1, 1), pos_estado, pnl_norm,
        ], dtype=np.float32)
    def step(self, action):
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
        info = {}
        reward = self.cfg.costo_holding if self.pos_abierta else 0.0
        if self.pos_abierta:
            evt = self._gestionar_posicion(ts, high, low)
            if evt == "tp1":
                reward += self.cfg.recompensa_tp1; info["evento"] = "tp1"
            elif evt == "tp2":
                reward += self.cfg.recompensa_tp2; info["evento"] = "tp2"
            elif evt == "sl":
                reward += self.cfg.castigo_sl; info["evento"] = "sl"
            elif evt == "be":
                reward += self.cfg.recompensa_be; info["evento"] = "be"
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
        if not self.pos_abierta: return None
        if self._toco(low, high, self.sl):
            res = "be" if (self.be_activado and abs(self.sl - self.precio_entrada) < 1e-9) else "sl"
            self._cerrar_total(ts, float(self.sl), res); return res
        if not self.be_activado and self._toco(low, high, self.tp1):
            self._cerrar_parcial(ts, float(self.tp1)); return "tp1"
        if self._toco(low, high, self.tp2):
            self._cerrar_total(ts, float(self.tp2), "tp2"); return "tp2"
        return None
    def _toco(self, low, high, nivel):
        return bool(np.isfinite(nivel) and low <= nivel <= high)
    def _cerrar_parcial(self, ts, precio):
        frac = self.cfg.fraccion_tp1
        lote_cerrar = min(self.lote_total * frac, self.lote_remanente)
        pnl = (precio - self.precio_entrada) * self.dir * lote_cerrar
        self.balance += float(pnl); self.lote_remanente -= lote_cerrar
        self.be_activado = True; self.sl = float(self.precio_entrada)
        self.pnl_dia += float(pnl)
        self.historial.append({"ts_entrada": self._ts_entrada_val, "ts_salida": ts, "dir": self.dir,
                               "modo": self.modo, "precio_entrada": self.precio_entrada,
                               "precio_salida": precio, "lote": lote_cerrar, "pnl": float(pnl), "resultado": "tp1"})
    def _cerrar_total(self, ts, precio, resultado):
        if not self.pos_abierta: return
        lote = self.lote_remanente
        pnl = (precio - self.precio_entrada) * self.dir * lote
        self.balance += float(pnl); self.pnl_dia += float(pnl)
        self.historial.append({"ts_entrada": self._ts_entrada_val, "ts_salida": ts, "dir": self.dir,
                               "modo": self.modo, "precio_entrada": self.precio_entrada,
                               "precio_salida": precio, "lote": lote, "pnl": float(pnl), "resultado": resultado})
        self._reset_posicion()
    def _abrir(self, modo, direccion, precio, ts):
        self.pos_abierta = True; self.dir = int(np.sign(direccion)); self.modo = modo
        self.precio_entrada = float(precio); self._ts_entrada_val = ts
        atr = float(self._row()["atr"])
        sl_dist = atr * (self.cfg.atr_sl_scalp if "SCALP" in modo else self.cfg.atr_sl_mult)
        rr = self.cfg.rr_scalp if "SCALP" in modo else self.cfg.rr_tp2
        d = self.dir
        self.sl = precio - d * sl_dist
        self.tp1 = precio + d * sl_dist * self.cfg.rr_tp1
        self.tp2 = precio + d * sl_dist * rr
        riesgo = self.balance * self.cfg.riesgo_pct
        self.lote_total = self.lote_remanente = float(max(0.0, riesgo / max(sl_dist, 1e-12)))
        self.be_activado = False; self.ops_hoy += 1
    def _equity(self, precio):
        if not self.pos_abierta: return float(self.balance)
        flotante = (precio - self.precio_entrada) * self.dir * self.lote_remanente
        return float(self.balance + flotante)
    def _actualizar_picos(self, ts):
        if hasattr(ts, 'normalize'):
            dia = ts.normalize()
        else:
            dia = self.paso // 26
        if self.fecha_equity_dia is None or dia != self.fecha_equity_dia:
            self.fecha_equity_dia = dia; self.pico_equity_dia = self.equity; self.ops_hoy = 0; self.pnl_dia = 0.0
        else:
            self.pico_equity_dia = max(self.pico_equity_dia, self.equity)
    def _evaluar_apertura(self, action, precio, high, low, r):
        c = precio; o = float(r["open"]); sup = float(r["bb_sup"]); inf = float(r["bb_inf"])
        media = float(r["bb_media"]); rsi = float(r["rsi"]); bbw_est = float(r["bbw_estado"])
        pend = float(r["pend_ema"]); conf_m5 = float(r["conf_m5"]); conf_m1 = float(r["conf_m1"])
        tend_h1 = float(r.get("tendencia_h1", 0))
        if action == 1: modo, direccion = "REV", 1
        elif action == 2: modo, direccion = "REV", -1
        elif action == 3: modo, direccion = "CONT", 1
        elif action == 4: modo, direccion = "CONT", -1
        elif action == 5: modo, direccion = "SCALP", 1
        else: modo, direccion = "SCALP", -1
        score = 0.0
        if modo == "REV":
            if direccion == 1:
                score += 0.3 if (low <= inf and c > inf) else 0.0
                score += 0.25 if (rsi < self.cfg.rsi_rev_long_max) else max(0.0, 0.25 * (50 - rsi) / 15)
                momentum_contra = (c > o) and (c - o) > (high - low) * 0.3
                if momentum_contra: score -= 0.3
            else:
                score += 0.3 if (high >= sup and c < sup) else 0.0
                score += 0.25 if (rsi > self.cfg.rsi_rev_short_min) else max(0.0, 0.25 * (rsi - 50) / 15)
                momentum_contra = (c < o) and (o - c) > (high - low) * 0.3
                if momentum_contra: score -= 0.3
            score += 0.15 * conf_m5 + 0.1 * conf_m1
            score += 0.1 if bbw_est < 0 else 0.0
        elif modo == "CONT":
            if direccion == 1:
                cuerpo = c > sup or (c - sup) / max(1e-12, sup - media) > 0.2
                score += 0.25 if cuerpo else max(0.0, (c - media) / max(1e-12, sup - media)) * 0.25
                score += 0.2 if (self.cfg.rsi_cont_long[0] <= rsi <= self.cfg.rsi_cont_long[1]) else 0.1
                score += 0.15 if (pend > 0 or tend_h1 >= 0) else 0.0
            else:
                cuerpo = c < inf or (inf - c) / max(1e-12, media - inf) > 0.2
                score += 0.25 if cuerpo else max(0.0, (media - c) / max(1e-12, media - inf)) * 0.25
                score += 0.2 if (self.cfg.rsi_cont_short[0] <= rsi <= self.cfg.rsi_cont_short[1]) else 0.1
                score += 0.15 if (pend < 0 or tend_h1 <= 0) else 0.0
            score += 0.15 * conf_m5 + 0.1 * conf_m1
            score += 0.1 if bbw_est > 0 else 0.0
        elif modo == "SCALP":
            score += 0.3 if conf_m5 else 0.0
            score += 0.3 if conf_m1 else 0.0
            score += 0.1 if bbw_est > 0 else (0.05 if bbw_est == 0 else 0.0)
            if direccion == 1:
                score += 0.15 if (low <= media <= c) else 0.0
                score += 0.15 if (rsi > 40) else 0.0
            else:
                score += 0.15 if (high >= media >= c) else 0.0
                score += 0.15 if (rsi < 60) else 0.0
        prob = float(np.clip(score, 0.0, 1.0))
        ok = prob >= self.cfg.min_probabilidad
        if ok: return True, modo, direccion, 0.0, prob
        else: return False, modo, direccion, self.cfg.castigo_sin_condiciones * (1.0 - prob), prob
    def calcular_metricas(self):
        ops = self.historial
        if not ops: return {"operaciones": 0, "winrate": 0.0, "profit_factor": 0.0,
                            "drawdown_max": 0.0, "sharpe": 0.0, "pnl_total": 0.0}
        pnls = np.array([o["pnl"] for o in ops], dtype=float)
        gan = pnls[pnls > 0]; per = pnls[pnls < 0]
        wr = float(gan.size / pnls.size) if pnls.size else 0.0
        pf = float(gan.sum() / abs(per.sum())) if per.size and abs(per.sum()) > 1e-12 else (np.inf if gan.size else 0.0)
        curva = np.cumsum(pnls)
        dd = float((curva - np.maximum.accumulate(curva)).min())
        sharpe = float(pnls.mean() / pnls.std(ddof=0) * np.sqrt(252)) if pnls.std(ddof=0) > 1e-12 else 0.0
        return {"operaciones": int(pnls.size), "winrate": wr, "profit_factor": pf,
                "drawdown_max": dd, "sharpe": sharpe, "pnl_total": float(pnls.sum())}

# TEST
env = EntornoHibridoUnificado(df)
obs, _ = env.reset()
print(f"Obs shape: {obs.shape}")
for _ in range(1000):
    a = env.action_space.sample()
    obs, r, done, trunc, info = env.step(a)
    if done: break
m = env.calcular_metricas()
print(f"Ops={m['operaciones']} WR={m['winrate']:.1%} PF={m['profit_factor']:.2f} PnL={m['pnl_total']:.0f}")
print("INLINE TEST PASADO")

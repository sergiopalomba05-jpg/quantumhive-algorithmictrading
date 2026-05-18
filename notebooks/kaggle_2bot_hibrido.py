#!/usr/bin/env python3
"""
================================================================================
KAGGLE — ENTRENAMIENTO 2-BOT HÍBRIDO v3
================================================================================
Bot A: REVERSIÓN (Mean Reversion) — Opera en BB% extremo + RSI extremo
Bot B: CONTINUACIÓN (Trend) — Opera en ADX>25 + MACD ruptura + momentum

Cambios críticos vs v2:
  ✓ Cada bot entrena en DATASET COMPLETO (no subsets)
  ✓ Reward shaping diferenciado por estrategia
  ✓ Trailing SL dinámico + BE después de TP1
  ✓ Horizon extendido a 240 barras (4h)
  ✓ Costos: spread 0.02% + comisión 0.01% + swap
  ✓ 2 posiciones por trade: TP1 1:2 (cierra 50%) + TP2 1:4 trailing
  ✓ Filtro horario NY: 14:00-21:00 UTC
  ✓ Export ONNX opset 12 para MT5

Instrucciones Kaggle:
  1. Nuevo Notebook → GPU V100
  2. Add Dataset: sergiopalomba/quantumhive-fusion
  3. Settings → Internet ON
  4. Copiar celda por celda, Run All
================================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 1: Dependencias
# ═══════════════════════════════════════════════════════════════════════════════
!pip install -q stable-baselines3 gymnasium onnx onnxruntime pandas numpy pyarrow

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 2: Imports
# ═══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import os, sys, json, math, random, warnings
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback

warnings.filterwarnings('ignore')
print(f'[OK] Torch: {torch.__version__} | CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'[OK] GPU: {torch.cuda.get_device_name(0)}')
    torch.backends.cudnn.benchmark = True

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 3: Configuración Global
# ═══════════════════════════════════════════════════════════════════════════════
WORKING = Path('/kaggle/working')
MODELS = WORKING / 'modelos_2bot'
MODELS.mkdir(exist_ok=True)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Parámetros de trading (alineados con EA MQL5)
HORIZON_MAX = 240          # 4 horas en M1
SL_ATR_MUL = 1.5           # Stop Loss = 1.5 × ATR
TP1_RATIO = 2.0            # Primer take profit 1:2
TP2_RATIO = 4.0            # Segundo TP trailing 1:4
COMISION_PCT = 0.0001      # 0.01% por lado
SPREAD_PCT = 0.0002        # 0.02% spread
SWAP_PER_BAR = 0.000005    # Swap despreciable por barra

NY_OPEN = 14               # 14:00 UTC = 09:00 ET
NY_CLOSE = 21              # 21:00 UTC = 16:00 ET

# Sizing discreto
LOT_MIN = 0.01
LOT_MED = 0.05
LOT_MAX = 0.10

TIMESTEPS_BOT = 500_000    # Steps por bot (ajustar según tiempo GPU)
N_EVAL_EPISODES = 2000

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 4: Carga CSVs Institucionales (robusta)
# ═══════════════════════════════════════════════════════════════════════════════
BASE = Path('/kaggle/input/datasets/sergiopalomba/quantumhive-fusion')

def cargar_csv(name_hint: str):
    """Busca archivo CSV por nombre parcial, robusto a diferencias de path."""
    for dp, _, fnames in os.walk('/kaggle/input'):
        for f in fnames:
            if f.lower().endswith('.csv') and name_hint.lower() in f.lower():
                p = Path(dp) / f
                print(f'[OK] {name_hint} → {p}')
                df = pd.read_csv(p, sep='\t', engine='python')
                df.columns = [c.strip().strip('<>') for c in df.columns]
                if 'TIME' in df.columns:
                    df['datetime'] = pd.to_datetime(
                        df['DATE'] + ' ' + df['TIME'],
                        format='%Y.%m.%d %H:%M:%S', errors='coerce')
                else:
                    df['datetime'] = pd.to_datetime(df['DATE'], format='%Y.%m.%d', errors='coerce')
                for col in ['OPEN','HIGH','LOW','CLOSE','TICKVOL','VOL','SPREAD']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce')
                df = df.dropna(subset=['datetime','CLOSE'])
                df['hour'] = df['datetime'].dt.hour
                return df.set_index('datetime').sort_index()
    raise FileNotFoundError(f'No se encontró CSV con hint: {name_hint}')

m1 = cargar_csv('datatb.csv')  # M1
print(f'\nM1 cargado: {len(m1):,} filas x {len(m1.columns)} cols')
print(f'Rango: {m1.index.min()} → {m1.index.max()}')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 5: Feature Engineering (14 features alineadas con EA)
# ═══════════════════════════════════════════════════════════════════════════════
def calcular_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    c, h, l = d['CLOSE'], d['HIGH'], d['LOW']
    vol = d.get('TICKVOL', d.get('VOL', pd.Series(1, index=d.index)))

    # RSI(14)
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    d['rsi'] = 100 - (100 / (1 + rs))

    # EMAs
    d['ema_fast'] = c.ewm(span=12, adjust=False).mean()
    d['ema_slow'] = c.ewm(span=26, adjust=False).mean()
    d['ema_200'] = c.ewm(span=200, adjust=False).mean()

    # Bollinger Bands (20, 2)
    sma20, std20 = c.rolling(20).mean(), c.rolling(20).std()
    d['bb_upper'] = sma20 + 2 * std20
    d['bb_lower'] = sma20 - 2 * std20
    d['bb_mid'] = sma20
    bw = d['bb_upper'] - d['bb_lower']
    d['bb_pct_b'] = (c - d['bb_lower']) / bw
    d['bbw'] = bw / d['bb_mid']

    # ATR(14)
    tr = pd.concat([h-l, abs(h-c.shift()), abs(l-c.shift())], axis=1).max(axis=1)
    d['atr'] = tr.rolling(14).mean()

    # ADX
    pdm = h.diff().where(h.diff() > l.diff(), 0)
    mdm = (-l.diff()).where(l.diff() > h.diff(), 0)
    atrs = tr.ewm(alpha=1/14, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1/14, adjust=False).mean() / (atrs + 1e-9)
    mdi = 100 * mdm.ewm(alpha=1/14, adjust=False).mean() / (atrs + 1e-9)
    dx = 100 * abs(pdi - mdi) / (pdi + mdi + 1e-9)
    d['adx'] = dx.ewm(alpha=1/14, adjust=False).mean()
    d['plus_di'] = pdi
    d['minus_di'] = mdi

    # MACD
    e12 = c.ewm(span=12, adjust=False).mean()
    e26 = c.ewm(span=26, adjust=False).mean()
    d['macd'] = e12 - e26
    d['macd_signal'] = d['macd'].ewm(span=9, adjust=False).mean()
    d['macd_hist'] = d['macd'] - d['macd_signal']
    d['macd_slope'] = d['macd_hist'].diff(3)

    # Volume
    d['volume_spike'] = vol / (vol.ewm(span=20, adjust=False).mean() + 1e-9)

    # Mechas (cuerpo vs mecha)
    body = abs(c - d['OPEN'])
    d['mecha_up'] = (h - c.where(c > d['OPEN'], d['OPEN'])) / (body + 1e-9)
    d['mecha_low'] = (c.where(c < d['OPEN'], d['OPEN']) - l) / (body + 1e-9)
    d['body_ratio'] = body / (h - l + 1e-9)

    # Retorno previo
    d['return_prev'] = c.pct_change()

    # Confluencia MACD
    d['macd_confluence'] = np.where(
        (d['macd'] > d['macd_signal']) & (d['macd_hist'] > d['macd_hist'].shift(1)), 1,
        np.where((d['macd'] < d['macd_signal']) & (d['macd_hist'] < d['macd_hist'].shift(1)), -1, 0)
    )

    # Filtro apertura NY
    d['es_apertura_ny'] = ((d['hour'] >= NY_OPEN) & (d['hour'] <= NY_CLOSE)).astype(float)

    return d

m1 = calcular_features(m1)
m1 = m1.dropna().reset_index(drop=True)
print(f'\nFeatures OK: {len(m1):,} filas después de dropna')
print(f'Features: {len([c for c in m1.columns if c not in ["OPEN","HIGH","LOW","CLOSE","TICKVOL","VOL","SPREAD","hour"]])} calculadas')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 6: Definir Features para Observación (14 inputs)
# ═══════════════════════════════════════════════════════════════════════════════
FEATURES = [
    'CLOSE', 'HIGH', 'LOW', 'OPEN',
    'rsi', 'ema_fast', 'ema_slow',
    'bb_upper', 'bb_lower', 'bb_pct_b', 'bbw',
    'atr', 'adx', 'macd', 'macd_signal',
    'volume_spike', 'mecha_up', 'mecha_low', 'body_ratio',
    'macd_confluence', 'es_apertura_ny'
]
# 20 features en total; obs = 20 + 3 (hour_norm, pos, size) = 23

def normalize(row, feat: str) -> float:
    """Normaliza una feature para la observación del agente."""
    close = row.get('CLOSE', 1.0)
    if close == 0 or pd.isna(close): close = 1.0
    v = row.get(feat, 0)

    if feat in ['CLOSE','HIGH','LOW','OPEN','bb_upper','bb_lower','ema_fast','ema_slow']:
        return v / close - 1.0
    elif feat == 'rsi': return v / 100.0
    elif feat == 'atr': return v / close
    elif feat in ['adx','bbw']: return min(v / 100.0, 5.0)
    elif feat == 'macd': return v / close
    elif feat == 'macd_signal': return v / close
    elif feat == 'volume_spike': return min(v, 10.0)
    elif feat in ['mecha_up','mecha_low']: return min(v, 5.0)
    elif feat == 'body_ratio': return v
    elif feat == 'macd_confluence': return v
    elif feat == 'es_apertura_ny': return v
    return float(v)

print(f'[OK] Features definidas: {len(FEATURES)}')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 7: Entorno Base — Gestion Profesional (Trailing SL + BE + Costos)
# ═══════════════════════════════════════════════════════════════════════════════
class EntornoTradingProfesional(gym.Env):
    """
    Entorno base con gestión profesional de trades.
    Acciones: 0=WAIT, 1=LONG_50%, 2=LONG_100%, 3=SHORT_50%, 4=SHORT_100%

    Cuando abre una posición:
      - SL = ATR × SL_ATR_MUL (150 pts aprox)
      - TP1 = SL × TP1_RATIO (1:2)
      - TP2 = SL × TP2_RATIO (1:4)
      - Al tocar TP1: cierra 50% del lote, mueve SL a BE (entry)
      - Trailing SL: después de BE, SL sigue a 1.5 ATR detrás del máx favor
      - Cierre por tiempo: horizon 240 barras
      - Costos: spread + comisión × 2 + swap por barra
    """
    metadata = {'render_modes': []}

    def __init__(self, df: pd.DataFrame, features: List[str],
                 reward_mode: str = 'neutral',  # 'reversion' o 'continuacion' o 'neutral'
                 horizon: int = HORIZON_MAX):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.features = [f for f in features if f in df.columns]
        self.reward_mode = reward_mode
        self.horizon = horizon

        self.action_space = gym.spaces.Discrete(5)
        obs_dim = len(self.features) + 3  # +hour_norm + pos + size
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        self._idx = 100
        self._pos = 0        # 0=none, 1=LONG, -1=SHORT
        self._size = 0.0     # lotaje actual
        self._entry = 0.0
        self._sl = 0.0
        self._tp1 = 0.0
        self._tp2 = 0.0
        self._max_fav = 0.0  # precio máximo favorable
        self._be = False     # break-even alcanzado
        self._hold = 0

    def _obs(self):
        row = self.df.iloc[self._idx]
        obs = [normalize(row, f) for f in self.features]
        hour = row.get('hour', 12)
        obs.append((hour - 12) / 12.0)  # -1 a 1
        obs.append(self._pos)
        obs.append(self._size)
        return np.array(obs, dtype=np.float32)

    def reset(self, seed=None, options=None):
        self._idx = random.randint(100, len(self.df) - self.horizon - 10)
        self._pos = 0
        self._size = 0.0
        self._entry = 0.0
        self._sl = 0.0
        self._tp1 = 0.0
        self._tp2 = 0.0
        self._max_fav = 0.0
        self._be = False
        self._hold = 0
        return self._obs(), {}

    def step(self, action):
        row = self.df.iloc[self._idx]
        price = row['CLOSE']
        atr = row.get('atr', price * 0.001)
        hour = row.get('hour', 12)
        in_ny = NY_OPEN <= hour <= NY_CLOSE
        reward = 0.0
        terminated = False
        info = {'event': 'none', 'mode': self.reward_mode}

        # Mapear acción
        action_dir = 0
        action_size = 0.0
        if action == 1: action_dir, action_size = 1, LOT_MED
        elif action == 2: action_dir, action_size = 1, LOT_MAX
        elif action == 3: action_dir, action_size = -1, LOT_MED
        elif action == 4: action_dir, action_size = -1, LOT_MAX

        cost_base = SPREAD_PCT + COMISION_PCT * 2

        # ── ABRIR POSICIÓN ──
        if self._pos == 0 and action_dir != 0 and in_ny:
            # Filtros específicos por modo (durante entrenamiento)
            if self.reward_mode == 'reversion':
                # Reversión: solo en BB% extremo + RSI extremo
                bb_pct = row.get('bb_pct_b', 0.5)
                rsi = row.get('rsi', 50)
                if not ((bb_pct < 0.05 and rsi < 30) or (bb_pct > 0.95 and rsi > 70)):
                    reward -= 2.0  # penaliza operar fuera de setup
            elif self.reward_mode == 'continuacion':
                # Continuación: solo en ADX alto + momentum
                adx = row.get('adx', 0)
                macd_conf = row.get('macd_confluence', 0)
                if not (adx > 25 and macd_conf != 0):
                    reward -= 2.0

            self._pos = action_dir
            self._size = action_size
            self._entry = price
            self._sl = price - self._pos * atr * SL_ATR_MUL
            self._tp1 = price + self._pos * atr * SL_ATR_MUL * TP1_RATIO
            self._tp2 = price + self._pos * atr * SL_ATR_MUL * TP2_RATIO
            self._max_fav = price
            self._be = False
            self._hold = 0
            info['event'] = 'open'
            reward -= cost_base * 10  # costo apertura

        # ── GESTIONAR POSICIÓN ABIERTA ──
        elif self._pos != 0:
            self._hold += 1
            self._max_fav = max(self._max_fav, price) if self._pos == 1 else min(self._max_fav, price)

            # PnL no realizado (para reward intermedia)
            unreal_pnl = self._pos * (price - self._entry) / self._entry
            cost = cost_base + SWAP_PER_BAR * self._hold

            # Checks
            hit_sl = (self._pos == 1 and price <= self._sl) or (self._pos == -1 and price >= self._sl)
            hit_tp1 = (self._pos == 1 and price >= self._tp1) or (self._pos == -1 and price <= self._tp1)
            hit_tp2 = (self._pos == 1 and price >= self._tp2) or (self._pos == -1 and price <= self._tp2)

            # BE: al tocar TP1, mover SL a entry, cierra 50% (simulado)
            if hit_tp1 and not self._be:
                self._sl = self._entry  # BE
                self._be = True
                partial_pnl = abs(self._tp1 - self._entry) / self._entry
                reward += partial_pnl * 30 * self._size  # reward parcial
                info['event'] = 'tp1_be'

            # Trailing SL después de BE
            if self._be and self._hold > 10:
                trail = self._max_fav - self._pos * atr * 1.5
                if self._pos == 1:
                    self._sl = max(self._sl, trail)
                else:
                    self._sl = min(self._sl, trail)

            # Resultado final
            if hit_sl:
                # Si fue BE, menos severo
                if self._be:
                    reward += (-abs(self._entry - self._sl) / self._entry - cost) * 50 * self._size
                else:
                    reward += (-abs(self._entry - self._sl) / self._entry - cost) * 100 * self._size
                self._pos = 0
                self._size = 0.0
                terminated = True
                info['event'] = 'sl'
            elif hit_tp2:
                final_pnl = abs(self._entry - self._tp2) / self._entry
                reward += (final_pnl - cost) * 100 * self._size
                self._pos = 0
                self._size = 0.0
                terminated = True
                info['event'] = 'tp2'
            elif self._hold >= self.horizon:
                final_pnl = self._pos * (price - self._entry) / self._entry
                reward += (final_pnl - cost) * 100 * self._size
                self._pos = 0
                self._size = 0.0
                terminated = True
                info['event'] = 'time_close'
            else:
                # Reward intermedia: incentiva ir hacia TP
                dist_to_tp = (self._tp2 - price) if self._pos == 1 else (price - self._tp2)
                dist_to_sl = (price - self._sl) if self._pos == 1 else (self._sl - price)
                if dist_to_tp > 0 and dist_to_sl > 0:
                    progress = dist_to_tp / (dist_to_tp + dist_to_sl)
                    reward += (progress - 0.5) * 0.5  # leve shaping
                reward -= cost * 5  # carrying cost
        else:
            # Sin posición y no abre
            reward -= 0.005

        self._idx += 1
        if self._idx >= len(self.df) - 5:
            terminated = True

        return self._obs(), float(reward), terminated, False, info

print('[OK] Entorno base definido')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 8: Funciones de Entrenamiento y Evaluación
# ═══════════════════════════════════════════════════════════════════════════════
def entrenar_bot(nombre: str, reward_mode: str, df_train, timesteps: int = TIMESTEPS_BOT):
    """Entrena un bot PPO con reward shaping específico."""
    print(f'\n{"="*60}')
    print(f'ENTRENAMIENTO: {nombre} | Modo: {reward_mode}')
    print(f'{"="*60}')

    env = DummyVecEnv([lambda: EntornoTradingProfesional(df_train, FEATURES, reward_mode=reward_mode)])

    model = PPO(
        'MlpPolicy', env,
        verbose=1, device=DEVICE,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        vf_coef=0.5,
        clip_range=0.2,
        policy_kwargs=dict(net_arch=[256, 256, 128])
    )

    print(f'Entrenando {timesteps:,} timesteps...')
    model.learn(total_timesteps=timesteps)

    ruta = MODELS / f'{nombre}_ppo'
    model.save(str(ruta))
    print(f'[OK] Modelo guardado: {ruta}')
    return model

def evaluar_bot(nombre: str, model, df_test, reward_mode: str, n_ep: int = N_EVAL_EPISODES):
    """Evalúa un bot entrenado y reporta métricas."""
    env = EntornoTradingProfesional(df_test, FEATURES, reward_mode=reward_mode)
    wins, tp1s, losses, timeouts, total_reward = 0, 0, 0, 0, 0.0
    pnl_list = []

    for _ in range(n_ep):
        obs, _ = env.reset()
        done = False
        ep_reward = 0.0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, trunc, info = env.step(int(action))
            ep_reward += reward
            if done:
                ev = info.get('event', '')
                if ev == 'tp2': wins += 1
                elif ev == 'tp1_be': tp1s += 1
                elif ev == 'sl': losses += 1
                elif ev == 'time_close': timeouts += 1
                total_reward += ep_reward
                pnl_list.append(ep_reward)

    total = wins + tp1s + losses + timeouts
    wr_tp2 = wins / total if total > 0 else 0
    wr_any = (wins + tp1s) / total if total > 0 else 0
    mean_r = np.mean(pnl_list) if pnl_list else 0

    print(f'\n--- {nombre} Evaluación ({n_ep} episodios) ---')
    print(f'  TP2 (ganancia completa): {wins}')
    print(f'  TP1 + BE (parcial):      {tp1s}')
    print(f'  SL (pérdida):            {losses}')
    print(f'  Timeout (cierre tiempo): {timeouts}')
    print(f'  WinRate TP2:  {wr_tp2:.2%}')
    print(f'  WinRate +BE:  {wr_any:.2%}')
    print(f'  Mean Reward:  {mean_r:.2f}')

    return {
        'bot': nombre, 'mode': reward_mode,
        'winrate_tp2': round(wr_tp2, 4),
        'winrate_be': round(wr_any, 4),
        'mean_reward': round(float(mean_r), 4),
        'tp2': wins, 'tp1_be': tp1s, 'sl': losses, 'timeout': timeouts,
        'total_episodes': n_ep
    }

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 9: ENTRENAMIENTO BOT A — REVERSIÓN
# ═══════════════════════════════════════════════════════════════════════════════
model_reversion = entrenar_bot('bot_reversion', 'reversion', m1, timesteps=TIMESTEPS_BOT)
stats_reversion = evaluar_bot('bot_reversion', model_reversion, m1, 'reversion')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 10: ENTRENAMIENTO BOT B — CONTINUACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
model_continuacion = entrenar_bot('bot_continuacion', 'continuacion', m1, timesteps=TIMESTEPS_BOT)
stats_continuacion = evaluar_bot('bot_continuacion', model_continuacion, m1, 'continuacion')

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 11: EXPORTAR ONNX (OpSet 12 para MT5)
# ═══════════════════════════════════════════════════════════════════════════════
import onnx

def exportar_onnx(model, nombre: str, obs_dim: int):
    """Exporta política PPO a ONNX compatible con MT5."""
    print(f'\n[ONNX] Exportando {nombre}...')

    class ONNXWrapper(torch.nn.Module):
        def __init__(self, policy):
            super().__init__()
            self.mlp_extractor = policy.mlp_extractor
            self.action_net = policy.action_net
        def forward(self, x):
            latent_pi, _ = self.mlp_extractor(x)
            logits = self.action_net(latent_pi)
            return torch.softmax(logits, dim=-1)

    model.policy.eval()
    wrapper = ONNXWrapper(model.policy).eval()

    dummy = torch.randn(1, obs_dim, dtype=torch.float32)
    if DEVICE == 'cuda':
        dummy = dummy.cuda()
        wrapper = wrapper.cuda()

    path_onnx = str(MODELS / f'{nombre}.onnx')
    try:
        torch.onnx.export(
            wrapper, dummy, path_onnx,
            export_params=True, opset_version=12,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
        )
        onnx.checker.check_model(onnx.load(path_onnx))
        kb = Path(path_onnx).stat().st_size / 1024
        print(f'[OK] {nombre}.onnx exportado ({kb:.0f} KB)')
        return True
    except Exception as e:
        print(f'[ERROR] ONNX {nombre}: {e}')
        import traceback
        traceback.print_exc()
        return False

obs_dim = len(FEATURES) + 3
exportar_onnx(model_reversion, 'bot_reversion', obs_dim)
exportar_onnx(model_continuacion, 'bot_continuacion', obs_dim)

# ═══════════════════════════════════════════════════════════════════════════════
# CELDA 12: REPORTE FINAL + ZIP
# ═══════════════════════════════════════════════════════════════════════════════
reporte = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'device': DEVICE,
    'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu',
    'dataset_rows': len(m1),
    'features_used': FEATURES,
    'config': {
        'horizon': HORIZON_MAX,
        'sl_atr_mul': SL_ATR_MUL,
        'tp1_ratio': TP1_RATIO,
        'tp2_ratio': TP2_RATIO,
        'timesteps_per_bot': TIMESTEPS_BOT,
        'comision_pct': COMISION_PCT,
        'spread_pct': SPREAD_PCT,
    },
    'bots': {
        'reversion': stats_reversion,
        'continuacion': stats_continuacion
    }
}

with open(WORKING / 'reporte_2bot.json', 'w', encoding='utf-8') as f:
    json.dump(reporte, f, indent=2, ensure_ascii=False)

import shutil
shutil.make_archive(str(WORKING / 'modelos_2bot'), 'zip', str(MODELS))

print(f'\n{"="*60}')
print('ENTRENAMIENTO COMPLETADO — 2-BOT HÍBRIDO v3')
print(f'{"="*60}')
print(f'Reporte:     /kaggle/working/reporte_2bot.json')
print(f'Modelos ZIP: /kaggle/working/modelos_2bot.zip')
print(f'\nContenido del ZIP:')
for f in sorted(MODELS.iterdir()):
    print(f'  {f.name} ({f.stat().st_size/1024:.0f} KB)')
print(f'\nPróximo paso: Descargar modelos_2bot.zip y subir ONNXs a MT5')
print(f'{"="*60}')

# Mostrar links de descarga
from IPython.display import FileLink, display
print('\nLinks de descarga:')
display(FileLink('/kaggle/working/modelos_2bot.zip'))
display(FileLink('/kaggle/working/reporte_2bot.json'))

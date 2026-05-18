#!/usr/bin/env python3
"""
KAGGLE — Reentrenamiento Bot Hibrido (Caballito de Batalla)
===========================================================
Entrena un solo modelo PPO para operar REVERSION en bandas de Bollinger
con gestion profesional: SL ATR×1.5, TP1 1:2, TP2 1:4, BE, cierre parcial.

Compatible con: PlantillaEAHibrido.mq5
Features: 14 (alineadas con EA MQL5)
Dataset: datatb_fusion institutional CSVs
"""
from __future__ import annotations
import os, sys, json, math, random
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# =============================================================================
# CONFIG
# =============================================================================
WORKING = Path('/kaggle/working')
MODELS = WORKING / 'modelos_hibrido'
MODELS.mkdir(exist_ok=True)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Riesgo / gestion (alineado con PlantillaEAHibrido.mq5)
SL_ATR_MUL = 1.5
TP1_RATIO = 2.0
TP2_RATIO = 4.0
COMISION_PCT = 0.0001   # 0.01%
SPREAD_PCT = 0.0002     # 0.02%
SWAP_PER_BAR = 0.000005
HORIZON_MAX = 240       # 4h max hold

# Filtro horario NY (simulado en entrenamiento)
NY_OPEN_HOUR = 14      # 14:00 UTC = 09:00 ET (aprox)
NY_CLOSE_HOUR = 21     # 21:00 UTC = 16:00 ET

print(f'[HIBRIDO] Device: {DEVICE}')
if torch.cuda.is_available():
    print(f'[HIBRIDO] GPU: {torch.cuda.get_device_name(0)}')
    torch.backends.cudnn.benchmark = True

# =============================================================================
# 1. CARGA CSVs (mismo path que v2)
# =============================================================================
BASE = Path('/kaggle/input/datasets/sergiopalomba/quantumhive-fusion')

def leer_csv(name: str):
    ruta = BASE / name
    if not ruta.exists():
        return None, f'No existe: {name}'
    print(f'[OK] {name}')
    df = pd.read_csv(ruta, sep='\t', engine='python')
    df.columns = [c.strip().strip('<>') for c in df.columns]
    if 'TIME' in df.columns:
        df['datetime'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'],
                                        format='%Y.%m.%d %H:%M:%S', errors='coerce')
    else:
        df['datetime'] = pd.to_datetime(df['DATE'], format='%Y.%m.%d', errors='coerce')
    for col in ['OPEN','HIGH','LOW','CLOSE','TICKVOL','VOL','SPREAD']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce')
    df = df.dropna(subset=['datetime','CLOSE'])
    df['hour'] = df['datetime'].dt.hour
    return df.set_index('datetime').sort_index(), None

m1, err = leer_csv('datatb.csv')
if err: raise ValueError(f'M1: {err}')
print(f'M1: {len(m1):,} filas')

# =============================================================================
# 2. INDICADORES (14 features alineadas con EA MQL5)
# =============================================================================
def calcular_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    close, high, low = d['CLOSE'], d['HIGH'], d['LOW']
    vol = d.get('TICKVOL', d.get('VOL', pd.Series(1, index=d.index)))

    # 1. RSI(14) — EA usa RSI(7) M15, pero usamos 14 en M1 como estandar
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    d['rsi'] = 100 - (100 / (1 + rs))

    # 2-3. EMAs
    d['ema_fast'] = close.ewm(span=12, adjust=False).mean()
    d['ema_slow'] = close.ewm(span=26, adjust=False).mean()

    # 4-7. Bollinger Bands (periodo 20, desv 2 — ajustable en EA)
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    d['bb_upper'] = sma20 + 2 * std20
    d['bb_lower'] = sma20 - 2 * std20
    d['bb_mid'] = sma20
    bw = d['bb_upper'] - d['bb_lower']
    d['bb_pct_b'] = (close - d['bb_lower']) / bw
    d['bbw'] = bw / d['bb_mid']

    # 8. ATR(14)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    d['atr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()

    # 9. ADX
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    plus_dm = high.diff().where(high.diff() > low.diff(), 0)
    minus_dm = (-low.diff()).where(low.diff() > high.diff(), 0)
    atr_s = tr.ewm(alpha=1/14, adjust=False).mean()
    pdi = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_s
    mdi = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_s
    dx = 100 * abs(pdi - mdi) / (pdi + mdi)
    d['adx'] = dx.ewm(alpha=1/14, adjust=False).mean()

    # 10-12. MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    d['macd'] = ema12 - ema26
    d['macd_signal'] = d['macd'].ewm(span=9, adjust=False).mean()
    d['macd_hist'] = d['macd'] - d['macd_signal']

    # 13. Volume spike
    d['volume_spike'] = vol / vol.ewm(span=20, adjust=False).mean()

    # 14. Retorno previo
    d['return_prev'] = close.pct_change()

    return d

m1 = calcular_features(m1)
print(f'Features calculadas. NaN: {m1.isna().mean().mean()*100:.2f}%')

# =============================================================================
# 3. ENV HIBRIDO (1 trade a la vez, gestion completa SL/TP1/TP2/BE)
# =============================================================================
FEATURES_HIBRIDO = [
    'CLOSE','HIGH','LOW','OPEN',
    'rsi','ema_fast','ema_slow',
    'bb_upper','bb_lower','bb_pct_b','bbw',
    'atr','adx','macd'
]

class EntornoHibrido(gym.Env):
    """
    Entorno para 1 bot hibrido de reversión.
    Acciones: 0=WAIT, 1=LONG, 2=SHORT
    Cuando abre, simula hasta SL, TP1, TP2, o BE.
    """
    metadata = {'render_modes': []}

    def __init__(self, df: pd.DataFrame, features: list[str],
                 sl_atr_mul=1.5, tp1_ratio=2.0, tp2_ratio=4.0):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.features = [f for f in features if f in df.columns]
        self.sl_atr_mul = sl_atr_mul
        self.tp1_ratio = tp1_ratio
        self.tp2_ratio = tp2_ratio
        self.horizon = HORIZON_MAX

        self.action_space = gym.spaces.Discrete(3)  # WAIT, LONG, SHORT
        obs_len = len(self.features) + 2  # +hour_norm + posicion_actual
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf,
                                                shape=(obs_len,), dtype=np.float32)
        self._idx = 200  # despues de indicadores
        self._pos = 0    # 0=sin pos, 1=LONG, -1=SHORT

    def _obs(self):
        row = self.df.iloc[self._idx]
        obs = []
        for f in self.features:
            v = row.get(f, 0)
            # Normalizacion simple
            if f in ['CLOSE','HIGH','LOW','OPEN','bb_upper','bb_lower','ema_fast','ema_slow']:
                v = v / row['CLOSE'] - 1.0  # retorno vs close
            elif f == 'rsi':
                v = v / 100.0
            elif f == 'atr':
                v = v / row['CLOSE']
            elif f in ['adx','bbw']:
                v = min(v / 100.0, 5.0)
            elif f == 'macd':
                v = v / row['CLOSE']
            obs.append(float(v))
        # Hora normalizada (filtro NY)
        hour = row.get('hour', 12)
        obs.append((hour - 12) / 12.0)  # -1 a 1
        obs.append(self._pos)  # posicion actual
        return np.array(obs, dtype=np.float32)

    def reset(self, seed=None, options=None):
        self._idx = random.randint(200, len(self.df) - self.horizon - 10)
        self._pos = 0
        return self._obs(), {}

    def step(self, action):
        row = self.df.iloc[self._idx]
        price = row['CLOSE']
        atr = row.get('atr', price * 0.001)
        hour = row.get('hour', 12)
        reward = 0.0
        terminated = False
        info = {'event': 'none'}

        # Filtro horario (NY session aprox)
        in_ny = NY_OPEN_HOUR <= hour <= NY_CLOSE_HOUR

        if self._pos == 0 and action != 0 and in_ny:
            # ABRIR POSICION
            self._pos = 1 if action == 1 else -1
            self._entry = price
            self._sl = price - self._pos * atr * self.sl_atr_mul
            self._tp1 = price + self._pos * atr * self.sl_atr_mul * self.tp1_ratio
            self._tp2 = price + self._pos * atr * self.sl_atr_mul * self.tp2_ratio
            self._be = False
            self._hold = 0
            self._max_fav = price  # max precio favorable
            info['event'] = 'open'

        elif self._pos != 0:
            # GESTIONAR POSICION ABIERTA
            self._hold += 1
            self._max_fav = max(self._max_fav, price) if self._pos == 1 else min(self._max_fav, price)

            pnl_pct = self._pos * (price - self._entry) / self._entry
            cost = SPREAD_PCT + COMISION_PCT * 2 + SWAP_PER_BAR * self._hold

            # SL
            hit_sl = (self._pos == 1 and price <= self._sl) or (self._pos == -1 and price >= self._sl)
            # TP1
            hit_tp1 = (self._pos == 1 and price >= self._tp1) or (self._pos == -1 and price <= self._tp1)
            # TP2
            hit_tp2 = (self._pos == 1 and price >= self._tp2) or (self._pos == -1 and price <= self._tp2)
            # BE (trailing simple: si toco TP1, SL se mueve a entry)
            if hit_tp1 and not self._be:
                self._sl = self._entry  # BE
                self._be = True
                reward += pnl_pct * 50  # recompensa parcial por TP1
                info['event'] = 'tp1_partial'

            if hit_sl:
                reward += (-abs(self._entry - self._sl) / self._entry - cost) * 100
                self._pos = 0
                terminated = True
                info['event'] = 'sl'
            elif hit_tp2:
                reward += (abs(self._entry - self._tp2) / self._entry - cost) * 100
                self._pos = 0
                terminated = True
                info['event'] = 'tp2_full'
            elif self._hold >= self.horizon:
                # Cierre por tiempo
                reward += (pnl_pct - cost) * 100
                self._pos = 0
                terminated = True
                info['event'] = 'time_close'
            else:
                # Penalizacion leve por hold (costo de oportunidad)
                reward -= cost * 10

        else:
            # Sin posicion y no abre
            reward -= 0.01  # penaliza inactividad leve

        self._idx += 1
        if self._idx >= len(self.df) - 5:
            terminated = True

        return self._obs(), float(reward), terminated, False, info

# =============================================================================
# 4. ENTRENAMIENTO
# =============================================================================
print('\n' + '='*60)
print('ENTRENAMIENTO BOT HIBRIDO — Reversion con Gestion Profesional')
print('='*60)

env = DummyVecEnv([lambda: EntornoHibrido(m1, FEATURES_HIBRIDO,
                                            sl_atr_mul=SL_ATR_MUL,
                                            tp1_ratio=TP1_RATIO,
                                            tp2_ratio=TP2_RATIO)])

model = PPO('MlpPolicy', env, verbose=1, device=DEVICE,
            learning_rate=3e-4, n_steps=2048, batch_size=256,
            n_epochs=10, gamma=0.99, gae_lambda=0.95,
            ent_coef=0.01, vf_coef=0.5)

TIMESTEPS = 500_000
print(f'Entrenando {TIMESTEPS:,} timesteps...')
model.learn(total_timesteps=TIMESTEPS)

# Guardar modelo PPO
model.save(str(MODELS / 'bot_hibrido_ppo'))
print(f'[OK] Modelo guardado: {MODELS / "bot_hibrido_ppo"}')

# =============================================================================
# 5. EVALUACION
# =============================================================================
def evaluar_hibrido(model, df, n_ep=1000):
    env_test = EntornoHibrido(df, FEATURES_HIBRIDO)
    wins, losses, tp1s, sls, timeouts = 0, 0, 0, 0, 0
    pnls = []
    for _ in range(n_ep):
        obs, _ = env_test.reset()
        done = False
        ep_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, trunc, info = env_test.step(int(action))
            ep_reward += reward
            if done:
                ev = info.get('event', '')
                if ev == 'tp2_full':
                    wins += 1
                    tp1s += 1
                elif ev == 'tp1_partial':
                    tp1s += 1
                elif ev == 'sl':
                    losses += 1
                    sls += 1
                elif ev == 'time_close':
                    timeouts += 1
                pnls.append(ep_reward)
    total = wins + losses + timeouts
    wr = wins / total if total > 0 else 0
    print(f'\nEvaluacion {n_ep} episodios:')
    print(f'  TP2 (ganancia completa): {wins}')
    print(f'  TP1 (parcial): {tp1s}')
    print(f'  SL (perdida): {losses}')
    print(f'  Timeout: {timeouts}')
    print(f'  WinRate: {wr:.2%}')
    print(f'  Mean Reward: {np.mean(pnls):.2f}')
    return {'winrate': wr, 'mean_reward': float(np.mean(pnls)), 'tp2': wins, 'sl': losses, 'timeout': timeouts}

stats = evaluar_hibrido(model, m1, n_ep=2000)

# =============================================================================
# 6. EXPORTAR ONNX (14 features)
# =============================================================================
import onnx
obs_sample, _ = EntornoHibrido(m1.head(1000), FEATURES_HIBRIDO).reset()
obs_t = torch.as_tensor(obs_sample, dtype=torch.float32).unsqueeze(0)
if DEVICE == 'cuda':
    obs_t = obs_t.cuda()

path_onnx = str(MODELS / 'bot_hibrido.onnx')
try:
    torch.onnx.export(model.policy, obs_t, path_onnx,
                      export_params=True, opset_version=12,
                      input_names=['obs'], output_names=['action_logits'],
                      dynamic_axes={'obs': {0: 'batch'}, 'action_logits': {0: 'batch'}})
    onnx.checker.check_model(onnx.load(path_onnx))
    kb = Path(path_onnx).stat().st_size / 1024
    print(f'\n[OK] ONNX exportado: {path_onnx} ({kb:.0f} KB)')
except Exception as e:
    print(f'\n[ERROR] ONNX: {e}')
    import traceback
    traceback.print_exc()

# =============================================================================
# 7. REPORTE + ZIP
# =============================================================================
reporte = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'device': DEVICE,
    'filas_dataset': len(m1),
    'bot_hibrido': stats,
    'config': {
        'sl_atr_mul': SL_ATR_MUL,
        'tp1_ratio': TP1_RATIO,
        'tp2_ratio': TP2_RATIO,
        'horizon_max': HORIZON_MAX,
        'timesteps': TIMESTEPS,
    }
}
with open(WORKING / 'reporte_hibrido.json', 'w') as f:
    json.dump(reporte, f, indent=2)

import shutil
shutil.make_archive(str(WORKING / 'modelos_hibrido'), 'zip', str(MODELS))
print(f'\nZIP: {WORKING / "modelos_hibrido.zip"}')
print('Descargar desde panel Output → /kaggle/working/modelos_hibrido.zip')
print('\n' + '='*60)
print('HIBRIDO LISTO — Subir bot_hibrido.onnx a MT5')
print('Features usadas (14):', FEATURES_HIBRIDO)
print('='*60)

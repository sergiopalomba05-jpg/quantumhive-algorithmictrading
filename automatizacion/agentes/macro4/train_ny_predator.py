#!/usr/bin/env python3
"""
Entrenamiento del Cerebro - NY PREDATOR v1
===========================================
Selector de Modos usando PPO (Proximal Policy Optimization).

MODO A (Reversión): Detectar mecha fuera de Banda (30, 3.0) con cierre de cuerpo dentro y volumen de rechazo.
MODO B (Continuidad): Detectar cierre de cuerpo sólido fuera de Banda (30, 3.0) con expansión de BBW y volumen creciente.

Gestión de Riesgo: ATR para Stop Loss y Take Profit dinámicos.

Autor: Cascade
Fecha: 4 de mayo de 2026
Proyecto: NY PREDATOR v1 - Bot especialista US30 (Apertura NY)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NYPredatorEnv(gym.Env):
    """Entorno de trading personalizado para NY Predator."""
    
    def __init__(self, df):
        super(NYPredatorEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.current_step = 0
        self.max_steps = len(self.df) - 1
        
        # Espacio de acción: 0 = MODO A (Reversión), 1 = MODO B (Continuidad), 2 = NO TRADE
        self.action_space = spaces.Discrete(3)
        
        # Espacio de observación: features técnicos
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(10,), dtype=np.float32
        )
        
        # Variables de estado
        self.balance = 100000
        self.position = 0
        self.entry_price = 0
        self.sl = 0
        self.tp = 0
        
    def reset(self, seed=None, options=None):
        """Resetea el entorno."""
        super().reset(seed=seed)
        self.current_step = 0
        self.balance = 100000
        self.position = 0
        self.entry_price = 0
        self.sl = 0
        self.tp = 0
        return self._get_observation(), {}
    
    def _get_observation(self):
        """Obtiene la observación actual."""
        if self.current_step >= len(self.df):
            return np.zeros(10, dtype=np.float32)
        
        row = self.df.iloc[self.current_step]
        
        # Features técnicos
        obs = np.array([
            row['close'] / row['bb_upper'],  # Posición relativa en BB
            row['bb_width'],  # Ancho de BB
            row['rsi'] / 100,  # RSI normalizado
            row['atr'] / row['close'],  # ATR normalizado
            row['volume'] / row['volume_ma'],  # Volumen relativo
            (row['close'] - row['open']) / row['close'],  # Tamaño del cuerpo
            (row['high'] - row['low']) / row['close'],  # Tamaño de la mecha
            (row['close'] - row['bb_lower']) / row['bb_width'],  # Distancia a banda inferior
            (row['bb_upper'] - row['close']) / row['bb_width'],  # Distancia a banda superior
            self.position  # Posición actual
        ], dtype=np.float32)
        
        return obs
    
    def _detectar_modo_a(self, row):
        """
        MODO A (Reversión): Detectar mecha fuera de Banda (30, 3.0) 
        con cierre de cuerpo dentro y volumen de rechazo.
        """
        # Mecha fuera de banda superior
        mecha_superior = row['high'] > row['bb_upper']
        # Cierre de cuerpo dentro de banda
        cierre_dentro = row['close'] < row['bb_upper'] and row['close'] > row['bb_lower']
        # Volumen de rechazo (mayor al promedio)
        volumen_rechazo = row['volume'] > row['volume_ma']
        
        return mecha_superior and cierre_dentro and volumen_rechazo
    
    def _detectar_modo_b(self, row):
        """
        MODO B (Continuidad): Detectar cierre de cuerpo sólido fuera de Banda (30, 3.0) 
        con expansión de BBW y volumen creciente.
        """
        # Cierre sólido fuera de banda superior
        cierre_fuera = row['close'] > row['bb_upper']
        # Expansión de BBW
        bbw_expansion = row['bb_width'] > row['bb_width'].shift(1)
        # Volumen creciente
        volumen_creciente = row['volume'] > row['volume'].shift(1)
        
        return cierre_fuera and bbw_expansion and volumen_creciente
    
    def _calcular_sl_tp(self, row):
        """
        Gestión de Riesgo: ATR para Stop Loss y Take Profit dinámicos.
        """
        atr = row['atr']
        close = row['close']
        
        # SL dinámico basado en ATR (2x ATR)
        sl = close - (atr * 2)
        
        # TP dinámico basado en ATR (3x ATR)
        tp = close + (atr * 3)
        
        return sl, tp
    
    def step(self, action):
        """Ejecuta un paso del entorno."""
        if self.current_step >= self.max_steps:
            return self._get_observation(), 0, True, False, {}
        
        row = self.df.iloc[self.current_step]
        reward = 0
        
        # Ejecutar acción
        if action == 0:  # MODO A (Reversión)
            if self._detectar_modo_a(row):
                sl, tp = self._calcular_sl_tp(row)
                self.position = -1  # Short
                self.entry_price = row['close']
                self.sl = sl
                self.tp = tp
                reward = 10  # Recompensa por detección correcta
            else:
                reward = -1  # Penalización por falso positivo
        
        elif action == 1:  # MODO B (Continuidad)
            if self._detectar_modo_b(row):
                sl, tp = self._calcular_sl_tp(row)
                self.position = 1  # Long
                self.entry_price = row['close']
                self.sl = sl
                self.tp = tp
                reward = 10  # Recompensa por detección correcta
            else:
                reward = -1  # Penalización por falso positivo
        
        elif action == 2:  # NO TRADE
            reward = 0
        
        # Calcular PnL si hay posición abierta
        if self.position != 0:
            pnl = 0
            if self.position == 1:  # Long
                pnl = (row['close'] - self.entry_price) / self.entry_price * 100
            elif self.position == -1:  # Short
                pnl = (self.entry_price - row['close']) / self.entry_price * 100
            
            # Cerrar posición si se alcanza SL o TP
            if row['close'] <= self.sl or row['close'] >= self.tp:
                self.position = 0
                reward += pnl
            else:
                reward += pnl * 0.1  # Recompensa parcial por PnL flotante
        
        self.current_step += 1
        
        # Episode termina al final del dataset
        done = self.current_step >= self.max_steps
        
        return self._get_observation(), reward, done, False, {}

class NYPredatorTrainer:
    """Entrenador del cerebro NY Predator."""
    
    def __init__(self):
        # Rutas relativas usando pathlib
        self.root = Path(__file__).resolve().parent.parent.parent.parent
        self.data_file = self.root / "datasets" / "historicos" / "US30_M15_PROCESSED.csv"
        self.model_file = self.root / "cerebros" / "ny_predator_v1.pkl"
        
        # Crear directorios si no existen
        self.model_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[TRAIN] Ruta raíz: {self.root}")
        logger.info(f"[TRAIN] Archivo datos: {self.data_file}")
        logger.info(f"[TRAIN] Archivo modelo: {self.model_file}")
    
    def cargar_datos(self) -> pd.DataFrame:
        """Carga los datos procesados."""
        logger.info("[TRAIN] Cargando datos procesados...")
        
        try:
            df = pd.read_csv(self.data_file, index_col=0, parse_dates=True)
            logger.info(f"[TRAIN] Datos cargados: {len(df)} filas")
            return df
        except Exception as e:
            logger.error(f"[TRAIN] Error cargando datos: {e}")
            raise
    
    def entrenar_modelo(self, df: pd.DataFrame):
        """Entrena el modelo PPO."""
        logger.info("="*80)
        logger.info("[TRAIN] INICIANDO ENTRENAMIENTO - NY PREDATOR v1")
        logger.info(f"[TRAIN] Fecha: {datetime.now().isoformat()}")
        logger.info("="*80)
        
        # Crear entorno
        env = NYPredatorEnv(df)
        
        # Crear modelo PPO
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1,
            tensorboard_log=self.root / "logs" / "tensorboard"
        )
        
        # Entrenar
        logger.info("[TRAIN] Iniciando entrenamiento...")
        model.learn(total_timesteps=100000)
        
        # Guardar modelo
        model.save(self.model_file)
        logger.info(f"[TRAIN] Modelo guardado en: {self.model_file}")
        
        logger.info("="*80)
        logger.info("[TRAIN] ENTRENAMIENTO COMPLETADO")
        logger.info("="*80)
        
        return model

if __name__ == "__main__":
    trainer = NYPredatorTrainer()
    df = trainer.cargar_datos()
    modelo = trainer.entrenar_modelo(df)
    
    print("\n[RESUMEN]")
    print(f"Modelo entrenado y guardado en: {trainer.model_file}")
    print(f"Total timesteps: 100000")

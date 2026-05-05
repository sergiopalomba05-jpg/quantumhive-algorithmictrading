#!/usr/bin/env python3
"""
Ingesta de Datos Maestros - NY PREDATOR v1
===========================================
Procesa el dataset maestro US30_M15_MASTER.csv para entrenamiento.

REGLA DE INTEGRIDAD T-1:
Obligatorio aplicar df['target'] = df['close'].shift(-1)
para asegurar que el entrenamiento se base solo en velas cerradas.
El bot no puede ver el futuro.

Autor: Cascade
Fecha: 4 de mayo de 2026
Proyecto: NY PREDATOR v1 - Bot especialista US30 (Apertura NY)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IngestaDatos:
    """Procesa datos maestros para entrenamiento de NY Predator."""
    
    def __init__(self, output_dir=None):
        # Rutas relativas usando pathlib
        self.root = Path(__file__).resolve().parent.parent.parent.parent
        self.input_file = self.root / "datasets" / "historicos" / "US30_M15_MASTER.csv"
        
        # Usar directorio de salida personalizado si se proporciona, por defecto entrenamientos_onnx/data
        if output_dir:
            self.output_file = Path(output_dir) / "US30_M15_PROCESSED.csv"
        else:
            self.output_file = self.root / "entrenamientos_onnx" / "data" / "US30_M15_PROCESSED.csv"
        
        # Crear directorios si no existen
        self.input_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[INGESTA] Ruta raíz: {self.root}")
        logger.info(f"[INGESTA] Archivo entrada: {self.input_file}")
        logger.info(f"[INGESTA] Archivo salida: {self.output_file}")
    
    def cargar_datos(self) -> pd.DataFrame:
        """Carga el dataset maestro."""
        logger.info("[INGESTA] Cargando dataset maestro...")
        
        try:
            # Leer CSV con espacios múltiples como separador
            df = pd.read_csv(self.input_file, sep='\s+')
            
            logger.info(f"[INGESTA] Dataset cargado: {len(df)} filas")
            logger.info(f"[INGESTA] Columnas: {df.columns.tolist()}")
            
            return df
        except Exception as e:
            logger.error(f"[INGESTA] Error cargando dataset: {e}")
            raise
    
    def limpiar_datos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y estructura los datos OHLCV + Spread."""
        logger.info("[INGESTA] Limpiando y estructurando datos...")
        
        # Renombrar columnas a formato estándar
        df.columns = df.columns.str.strip()
        column_mapping = {
            '<DATE>': 'date',
            '<TIME>': 'time',
            '<OPEN>': 'open',
            '<HIGH>': 'high',
            '<LOW>': 'low',
            '<CLOSE>': 'close',
            '<TICKVOL>': 'tickvol',
            '<VOL>': 'volume',
            '<SPREAD>': 'spread'
        }
        df = df.rename(columns=column_mapping)
        
        # Combinar fecha y hora en datetime
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.set_index('datetime')
        
        # Convertir tipos de datos
        numeric_columns = ['open', 'high', 'low', 'close', 'tickvol', 'volume', 'spread']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Eliminar filas con valores nulos
        df = df.dropna()
        
        logger.info(f"[INGESTA] Datos limpiados: {len(df)} filas")
        logger.info(f"[INGESTA] Rango de fechas: {df.index.min()} a {df.index.max()}")
        
        return df
    
    def calcular_indicadores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos para entrenamiento."""
        logger.info("[INGESTA] Calculando indicadores técnicos...")
        
        # Bollinger Bands (30, 3.0)
        df['bb_period'] = 30
        df['bb_std'] = 3.0
        df['bb_middle'] = df['close'].rolling(window=30).mean()
        df['bb_std_dev'] = df['close'].rolling(window=30).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std_dev'] * 3.0)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std_dev'] * 3.0)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # RSI (7)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Volumen promedio
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        logger.info("[INGESTA] Indicadores calculados")
        
        return df
    
    def aplicar_regla_integridad_t1(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        REGLA DE INTEGRIDAD T-1:
        Aplicar df['target'] = df['close'].shift(-1)
        para asegurar que el entrenamiento se base solo en velas cerradas.
        El bot no puede ver el futuro.
        """
        logger.info("[INGESTA] Aplicando REGLA DE INTEGRIDAD T-1...")
        
        # Target es el cierre de la siguiente vela (shift -1)
        df['target'] = df['close'].shift(-1)
        
        # Eliminar última fila (sin target)
        df = df[:-1]
        
        logger.info(f"[INGESTA] REGLA T-1 aplicada: {len(df)} filas con target")
        
        return df
    
    def guardar_datos(self, df: pd.DataFrame):
        """Guarda los datos procesados."""
        logger.info("[INGESTA] Guardando datos procesados...")
        
        try:
            df.to_csv(self.output_file)
            logger.info(f"[INGESTA] Datos guardados en: {self.output_file}")
            logger.info(f"[INGESTA] Total filas procesadas: {len(df)}")
        except Exception as e:
            logger.error(f"[INGESTA] Error guardando datos: {e}")
            raise
    
    def ejecutar_ingesta(self):
        """Ejecuta el ciclo completo de ingesta de datos."""
        logger.info("="*80)
        logger.info("[INGESTA] INICIANDO INGESTA DE DATOS MAESTROS - NY PREDATOR v1")
        logger.info(f"[INGESTA] Fecha: {datetime.now().isoformat()}")
        logger.info("="*80)
        
        # Paso 1: Cargar datos
        df = self.cargar_datos()
        
        # Paso 2: Limpiar datos
        df = self.limpiar_datos(df)
        
        # Paso 3: Calcular indicadores
        df = self.calcular_indicadores(df)
        
        # Paso 4: Aplicar REGLA DE INTEGRIDAD T-1
        df = self.aplicar_regla_integridad_t1(df)
        
        # Paso 5: Guardar datos
        self.guardar_datos(df)
        
        logger.info("="*80)
        logger.info("[INGESTA] INGESTA COMPLETADA EXITOSAMENTE")
        logger.info("="*80)
        
        return df

if __name__ == "__main__":
    ingesta = IngestaDatos()
    df_procesado = ingesta.ejecutar_ingesta()
    
    print("\n[RESUMEN]")
    print(f"Filas procesadas: {len(df_procesado)}")
    print(f"Columnas: {df_procesado.columns.tolist()}")
    print(f"Rango de fechas: {df_procesado.index.min()} a {df_procesado.index.max()}")

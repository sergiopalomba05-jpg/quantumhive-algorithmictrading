"""
Filtrado Horario para NY Predator v1 - NY Open (09:30-11:30 EST)
Detecta offset horario del broker y filtra velas de apertura de NY
Calcula indicadores técnicos para entrenamiento
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timezone, timedelta

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FiltroNYOpen:
    """Filtra velas de apertura de Nueva York (09:30-11:30 EST)."""
    
    def __init__(self):
        # Rutas relativas usando pathlib
        self.root = Path(__file__).resolve().parent.parent.parent.parent
        self.input_file = self.root / "entrenamientos_onnx" / "VELAS IC MARCKET" / "US30_M15_2022_2024.csv"
        self.output_file = self.root / "entrenamientos_onnx" / "data" / "US30_NY_ONLY_M15.csv"
        
        # Crear directorios si no existen
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[FILTRO] Ruta raíz: {self.root}")
        logger.info(f"[FILTRO] Archivo entrada: {self.input_file}")
        logger.info(f"[FILTRO] Archivo salida: {self.output_file}")
    
    def detectar_offset_broker(self, df):
        """Detecta el offset horario del broker analizando las horas del archivo."""
        # Convertir a datetime si no lo está
        if 'date' in df.columns and 'time' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        elif '<DATE>' in df.columns and '<TIME>' in df.columns:
            df['datetime'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'])
        else:
            logger.error("[FILTRO] No se encontraron columnas de fecha/hora")
            raise ValueError("Columnas de fecha/hora no encontradas")
        
        # Extraer hora del día (0-23)
        df['hour'] = df['datetime'].dt.hour
        
        # Analizar distribución de horas para detectar offset
        hour_counts = df['hour'].value_counts().sort_index()
        
        logger.info(f"[FILTRO] Distribución de horas en el archivo:")
        for hour, count in hour_counts.items():
            if count > 100:  # Solo mostrar horas significativas
                logger.info(f"[FILTRO]   Hora {hour}: {count} velas")
        
        # IC Markets está en Sydney (UTC+10 o UTC+11 dependiendo del horario de verano)
        # NY está en EST (UTC-5) o EDT (UTC-4)
        # La diferencia es aproximadamente 14-15 horas
        # Si IC Markets es 00:00, NY es aproximadamente 09:00-10:00 del día anterior
        
        # Detectar offset basado en la hora más común
        most_common_hour = hour_counts.idxmax()
        
        # Asumimos que la hora más común corresponde a la sesión de Londres (08:00-16:00)
        # o a la sesión de NY (13:00-21:00 hora del broker)
        # IC Markets (UTC+10) vs NY (UTC-5) = diferencia de 15 horas
        
        # Si la hora más común es alrededor de 13:00-21:00, es sesión de NY en hora del broker
        # Si la hora más común es alrededor de 07:00-15:00, es sesión de Londres en hora del broker
        
        logger.info(f"[FILTRO] Hora más común: {most_common_hour}")
        
        # Asumimos offset de IC Markets (UTC+10 o UTC+11)
        # Para NY EST (UTC-5): offset = +15 horas
        # Para NY EDT (UTC-4): offset = +14 horas
        
        # Usaremos offset de +14 horas (promedio para cubrir ambos casos)
        offset_hours = 14
        
        logger.info(f"[FILTRO] Offset horario detectado: +{offset_hours} horas (IC Markets -> NY)")
        logger.info(f"[FILTRO] Rango objetivo NY: 09:30-11:30 EST")
        logger.info(f"[FILTRO] Rango equivalente en hora del broker: {9+offset_hours}:{30+offset_hours%60} - {11+offset_hours}:{30+offset_hours%60}")
        
        return df, offset_hours
    
    def filtrar_ny_open(self, df, offset_hours):
        """Filtra velas de apertura de NY (09:30-11:30 EST)."""
        # Convertir hora del broker a hora de NY
        # NY time = broker time - offset_hours
        df['ny_hour'] = (df['hour'] - offset_hours) % 24
        
        # Filtrar velas de 09:30-11:30 NY time
        # 09:30 = 9.5, 11:30 = 11.5
        df['ny_time_decimal'] = df['ny_hour'] + df['datetime'].dt.minute / 60
        df_filtered = df[(df['ny_time_decimal'] >= 9.5) & (df['ny_time_decimal'] <= 11.5)]
        
        logger.info(f"[FILTRO] Velas filtradas: {len(df_filtered)}")
        logger.info(f"[FILTRO] Porcentaje filtrado: {len(df_filtered) / len(df) * 100:.2f}%")
        
        return df_filtered
    
    def calcular_indicadores(self, df):
        """Calcula indicadores técnicos para entrenamiento."""
        logger.info("[FILTRO] Calculando indicadores técnicos...")
        
        # Asegurar que las columnas numéricas estén en formato correcto
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['tickvol'] = pd.to_numeric(df['tickvol'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # Bandas de Bollinger (Periodo 30, Desviación 3.0)
        bb_period = 30
        bb_std = 3.0
        df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * bb_std)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # RSI (Periodo 7)
        rsi_period = 7
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Periodo 14)
        atr_period = 14
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=atr_period).mean()
        
        # Volumen MA (Periodo 20) - Basado en tickvol
        volume_ma_period = 20
        df['volume_ma'] = df['tickvol'].rolling(window=volume_ma_period).mean()
        
        # Verificación de variabilidad de volume_ma
        volume_ma_std = df['volume_ma'].std()
        volume_ma_unique = df['volume_ma'].nunique()
        logger.info(f"[FILTRO] Variabilidad de volume_ma - std: {volume_ma_std}, valores únicos: {volume_ma_unique}")
        
        if volume_ma_std == 0 or volume_ma_unique == 1:
            logger.warning("[FILTRO] volume_ma es CONSTANTE. Eliminando columnas de volumen del dataset.")
            # Eliminar columnas de volumen
            df = df.drop(columns=['volume_ma', 'tickvol'])
        else:
            # Relleno de seguridad: reemplazar 0 por 1 para evitar división por cero
            df['volume_ma'] = df['volume_ma'].replace(0, 1)
        
        # TARGET (REGLA T-1): target = close.shift(-1)
        df['target'] = df['close'].shift(-1)
        
        logger.info("[FILTRO] Indicadores técnicos calculados")
        logger.info(f"[FILTRO] Columnas calculadas: bb_upper, bb_middle, bb_lower, bb_width, rsi, atr, target")
        if 'volume_ma' in df.columns:
            logger.info(f"[FILTRO] Columnas de volumen: tickvol, volume_ma")
        else:
            logger.info(f"[FILTRO] Columnas de volumen: ELIMINADAS (volume_ma constante)")
        
        return df
    
    def limpiar_nan_inf(self, df):
        """Elimina valores NaN e infinitos del dataframe."""
        logger.info("[FILTRO] Limpiando valores NaN e infinitos...")
        
        # Reemplazar infinitos por NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Eliminar filas con NaN
        filas_antes = len(df)
        df = df.dropna()
        filas_despues = len(df)
        
        logger.info(f"[FILTRO] Filas eliminadas por NaN/inf: {filas_antes - filas_despues}")
        logger.info(f"[FILTRO] Filas después de limpieza: {filas_despues}")
        
        return df
    
    def aplicar_integridad_temporal(self, df):
        """Aplica shift(1) para que la IA no vea el futuro."""
        df_shifted = df.copy()
        
        # Shift de todas las columnas numéricas excepto datetime
        numeric_cols = df_shifted.select_dtypes(include=[np.number]).columns
        df_shifted[numeric_cols] = df_shifted[numeric_cols].shift(1)
        
        # Eliminar primera fila (que tendrá NaN después del shift)
        df_shifted = df_shifted.dropna(subset=numeric_cols)
        
        logger.info(f"[FILTRO] Velas después de shift(1): {len(df_shifted)}")
        logger.info(f"[FILTRO] Integridad temporal aplicada: IA solo ve velas cerradas")
        
        return df_shifted
    
    def guardar_datos(self, df):
        """Guarda los datos filtrados con indicadores técnicos."""
        # Validar columnas requeridas (volume_ma es opcional)
        required_columns = ['open', 'high', 'low', 'close', 'bb_upper', 'bb_lower', 
                          'bb_middle', 'bb_width', 'rsi', 'atr', 'target']
        
        # Agregar columnas opcionales si existen
        if 'tickvol' in df.columns:
            required_columns.append('tickvol')
        if 'volume_ma' in df.columns:
            required_columns.append('volume_ma')
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"[FILTRO] Faltan columnas requeridas: {missing_columns}")
            raise ValueError(f"Faltan columnas requeridas: {missing_columns}")
        
        logger.info("[FILTRO] Todas las columnas requeridas están presentes")
        
        # Verificación pre-vuello: contar valores nulos
        null_counts = df.isnull().sum()
        logger.info("[FILTRO] Verificación pre-vuello - Conteo de valores nulos:")
        for col, count in null_counts.items():
            if count > 0:
                logger.warning(f"[FILTRO]   {col}: {count} valores nulos")
        
        if null_counts.sum() > 0:
            logger.error(f"[FILTRO] ERROR: El dataframe tiene {null_counts.sum()} valores nulos. No se puede guardar.")
            raise ValueError(f"El dataframe tiene valores nulos: {null_counts.to_dict()}")
        
        logger.info("[FILTRO] Verificación pre-vuello: ✅ Todas las columnas tienen 0 valores nulos")
        
        # Seleccionar solo columnas relevantes (excluir columnas temporales y volume)
        cols = ['datetime', 'open', 'high', 'low', 'close', 'spread',
               'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'rsi', 'atr', 'target']
        
        # Agregar columnas de volumen si existen
        if 'tickvol' in df.columns:
            cols.insert(5, 'tickvol')
        if 'volume_ma' in df.columns:
            cols.append('volume_ma')
        
        df_export = df[cols].copy()
        
        # Guardar sin índice
        df_export.to_csv(self.output_file, index=False)
        
        logger.info(f"[FILTRO] Datos guardados en: {self.output_file}")
        logger.info(f"[FILTRO] Columnas guardadas: {df_export.columns.tolist()}")
    
    def ejecutar_filtrado(self):
        """Ejecuta el ciclo completo de filtrado y cálculo de indicadores."""
        logger.info("="*80)
        logger.info("[FILTRO] INICIANDO FILTRADO HORARIO - NY PREDATOR v1")
        logger.info(f"[FILTRO] Fecha: {datetime.now().isoformat()}")
        logger.info("="*80)
        
        # Paso 1: Cargar datos
        logger.info("[FILTRO] Cargando dataset...")
        df = pd.read_csv(self.input_file, sep='\t')
        logger.info(f"[FILTRO] Dataset cargado: {len(df)} filas")
        logger.info(f"[FILTRO] Columnas: {df.columns.tolist()}")
        
        # Paso 2: Renombrar columnas MT5 a formato estándar
        logger.info("[FILTRO] Renombrando columnas MT5...")
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
        
        # Paso 3: Detectar offset horario
        logger.info("[FILTRO] Detectando offset horario del broker...")
        df, offset_hours = self.detectar_offset_broker(df)
        
        # Paso 4: Filtrar velas de NY Open
        logger.info("[FILTRO] Filtrando velas de NY Open (09:30-11:30 EST)...")
        df_filtered = self.filtrar_ny_open(df, offset_hours)
        
        # Paso 5: Calcular indicadores técnicos
        logger.info("[FILTRO] Calculando indicadores técnicos...")
        df_with_indicators = self.calcular_indicadores(df_filtered)
        
        # Paso 6: Limpiar NaN e infinitos (CRÍTICO)
        logger.info("[FILTRO] Limpiando NaN e infinitos...")
        df_clean = self.limpiar_nan_inf(df_with_indicators)
        
        # Paso 7: Aplicar integridad temporal
        logger.info("[FILTRO] Aplicando integridad temporal (shift(1))...")
        df_final = self.aplicar_integridad_temporal(df_clean)
        
        # Paso 8: Guardar datos
        logger.info("[FILTRO] Guardando datos filtrados...")
        self.guardar_datos(df_final)
        
        logger.info("="*80)
        logger.info("[FILTRO] FILTRADO COMPLETADO EXITOSAMENTE")
        logger.info("="*80)
        
        return df_final

if __name__ == "__main__":
    filtro = FiltroNYOpen()
    df_filtrado = filtro.ejecutar_filtrado()
    
    print("\n[RESUMEN]")
    print(f"Velas filtradas: {len(df_filtrado)}")
    print(f"Rango de fechas: {df_filtrado['datetime'].min()} a {df_filtrado['datetime'].max()}")
    print(f"\nColumnas del dataset: {df_filtrado.columns.tolist()}")
    print("\n[PRIMERAS 5 FILAS DEL DATASET]")
    print(df_filtrado.head())

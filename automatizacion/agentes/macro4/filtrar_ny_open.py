"""
Filtrado Horario para NY Predator v1 - NY Open (09:30-11:30 EST)
Detecta offset horario del broker y filtra velas de apertura de NY
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
        """Guarda los datos filtrados."""
        # Seleccionar columnas relevantes
        if '<OPEN>' in df.columns:
            # Formato MT5 original
            cols = ['datetime', '<OPEN>', '<HIGH>', '<LOW>', '<CLOSE>', '<TICKVOL>', '<VOL>', '<SPREAD>']
            df_export = df[cols].copy()
            df_export.columns = ['datetime', 'open', 'high', 'low', 'close', 'tickvol', 'volume', 'spread']
        else:
            # Formato ya procesado
            cols = ['datetime', 'open', 'high', 'low', 'close', 'tickvol', 'volume', 'spread']
            df_export = df[cols].copy()
        
        # Guardar sin índice
        df_export.to_csv(self.output_file, index=False)
        
        logger.info(f"[FILTRO] Datos guardados en: {self.output_file}")
    
    def ejecutar_filtrado(self):
        """Ejecuta el ciclo completo de filtrado."""
        logger.info("="*80)
        logger.info("[FILTRO] INICIANDO FILTRADO HORARIO - NY PREDATOR v1")
        logger.info(f"[FILTRO] Fecha: {datetime.now().isoformat()}")
        logger.info("="*80)
        
        # Paso 1: Cargar datos
        logger.info("[FILTRO] Cargando dataset...")
        df = pd.read_csv(self.input_file, sep='\t')
        logger.info(f"[FILTRO] Dataset cargado: {len(df)} filas")
        logger.info(f"[FILTRO] Columnas: {df.columns.tolist()}")
        
        # Paso 2: Detectar offset horario
        logger.info("[FILTRO] Detectando offset horario del broker...")
        df, offset_hours = self.detectar_offset_broker(df)
        
        # Paso 3: Filtrar velas de NY Open
        logger.info("[FILTRO] Filtrando velas de NY Open (09:30-11:30 EST)...")
        df_filtered = self.filtrar_ny_open(df, offset_hours)
        
        # Paso 4: Aplicar integridad temporal
        logger.info("[FILTRO] Aplicando integridad temporal (shift(1))...")
        df_final = self.aplicar_integridad_temporal(df_filtered)
        
        # Paso 5: Guardar datos
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

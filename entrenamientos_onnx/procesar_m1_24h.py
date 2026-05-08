"""
Procesamiento M1 24H - Global Hunter
Genera US30_M1_PROCESSED_FINAL.csv con sensores completos sin filtro horario
"""

import pandas as pd
import numpy as np
from pathlib import Path

def calculate_bollinger_bands(df, period=30, std_dev=3.0):
    """Calcula Bollinger Bands, BB Width y BB%"""
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    df['bb_std'] = df['close'].rolling(window=period).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_dev)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_dev)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    return df

def calculate_atr(df, period=20):
    """Calcula ATR"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(window=period).mean()
    return df

def calculate_volume_ma(df, period=20):
    """Calcula Volume MA sobre tickvol"""
    df['volume_ma'] = df['tickvol'].rolling(window=period).mean()
    return df

def process_m1_24h(input_path, output_path):
    """Procesa archivo M1 con sensores completos sin filtro horario"""
    print(f"Procesando: {input_path}")
    
    # Cargar datos (formato MT5 con tabuladores)
    df = pd.read_csv(input_path, sep='\t')
    print(f"Filas originales: {len(df)}")
    
    # Renombrar columnas MT5 a formato estándar
    column_mapping = {
        '<DATE>': 'date',
        '<TIME>': 'time',
        '<OPEN>': 'open',
        '<HIGH>': 'high',
        '<LOW>': 'low',
        '<CLOSE>': 'close',
        '<TICKVOL>': 'tickvol',
        '<VOL>': 'vol',
        '<SPREAD>': 'spread'
    }
    df = df.rename(columns=column_mapping)
    
    # Aplicar sensores
    df = calculate_bollinger_bands(df, period=30, std_dev=3.0)
    df = calculate_atr(df, period=20)
    df = calculate_volume_ma(df, period=20)
    
    # Target: close.shift(-1)
    df['target'] = df['close'].shift(-1)
    
    # Limpieza de NaN
    df = df.dropna()
    print(f"Filas después de limpieza: {len(df)}")
    
    # Guardar
    df.to_csv(output_path, index=False)
    print(f"Guardado: {output_path}")
    return len(df)

def main():
    base_path = Path(__file__).parent
    input_folder = base_path / "VELAS IC MARCKET"
    output_folder = base_path / "data"
    output_folder.mkdir(exist_ok=True)
    
    # Procesar M1 24H
    m1_input = input_folder / "US30_M1_2024_2025.csv"
    m1_output = output_folder / "US30_M1_PROCESSED_FINAL.csv"
    
    total_filas = process_m1_24h(m1_input, m1_output)
    
    print(f"\n{'='*60}")
    print(f"PROCESAMIENTO M1 24H COMPLETADO")
    print(f"Total de filas procesadas: {total_filas}")
    print(f"Archivo generado: {m1_output}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

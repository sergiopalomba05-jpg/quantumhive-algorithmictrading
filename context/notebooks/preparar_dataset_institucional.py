"""
PREPARAR DATASET INSTITUCIONAL COMPLETO — QuantumHive
======================================================
Lee los CSV multitemporales exportados desde MT5 (ICMarkets demo),
los alinea, calcula indicadores y confluencias, y genera un dataset
maestro en formato Parquet (rápido) + CSV (fallback).

Entrada:
  C:\Users\sergio\Documents\datatb.csv          (M1)
  C:\Users\sergio\Documents\datatb_m5.csv      (M5)
  C:\Users\sergio\Documents\datatb_m15.csv     (M15)
  C:\Users\sergio\Documents\datatb_H1.csv     (H1)
  C:\Users\sergio\Documents\datatb_H4.csv     (H4)
  C:\Users\sergio\Documents\datatb_daily.csv  (Daily)

Salida:
  datos/datatb_fusion.parquet
  datos/datatb_fusion.csv     (fallback)
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ── Paths ──
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RUTA_DOCS = Path("C:/Users/sergio/Documents")
RUTA_SALIDA = ROOT / "datos"


def leer_csv_mt5(nombre_archivo: str) -> pd.DataFrame | None:
    """Lee un CSV de MT5 con tabulaciones y headers tipo <DATE>, <TIME>."""
    ruta = RUTA_DOCS / nombre_archivo
    if not ruta.exists():
        print(f"[PREPARAR] No encontrado: {ruta}")
        return None

    print(f"[PREPARAR] Leyendo {nombre_archivo} ...")
    df = pd.read_csv(
        ruta,
        sep="\t",
        engine="python",
        na_values="",
        keep_default_na=False,
    )

    # Limpiar nombres de columnas quitando < >
    df.columns = [c.strip().strip("<>") for c in df.columns]

    # Crear datetime unificado
    if "DATE" in df.columns and "TIME" in df.columns:
        df["datetime"] = pd.to_datetime(df["DATE"] + " " + df["TIME"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    elif "datetime" not in df.columns:
        print(f"[PREPARAR] WARN: No se encontró DATE/TIME en {nombre_archivo}")
        return None

    # Convertir columnas numéricas
    for col in ["OPEN", "HIGH", "LOW", "CLOSE", "TICKVOL", "VOL", "SPREAD"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

    df = df.dropna(subset=["datetime", "CLOSE"]).set_index("datetime").sort_index()
    print(f"  -> {len(df):,} filas | {df.index.min()} -> {df.index.max()}")
    return df


def calcular_indicadores_m1(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores técnicos sobre el dataframe M1."""
    print("[PREPARAR] Calculando indicadores técnicos en M1 ...")
    close = df["CLOSE"]
    high = df["HIGH"]
    low = df["LOW"]
    vol = df.get("TICKVOL", df.get("VOL", pd.Series(1, index=df.index)))

    # RSI 14
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # EMAs
    df["ema_fast"] = close.ewm(span=12, adjust=False).mean()
    df["ema_slow"] = close.ewm(span=26, adjust=False).mean()
    df["ema_200"] = close.ewm(span=200, adjust=False).mean()

    # Bollinger Bands 20
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_mid"] = sma20
    df["bb_lower"] = sma20 - 2 * std20

    # BB% (Bollinger Band %B) y BBW (Bollinger Band Width)
    band_width = df["bb_upper"] - df["bb_lower"]
    df["bb_pct_b"] = (close - df["bb_lower"]) / band_width
    df["bbw"] = band_width / df["bb_mid"]

    # ATR 14
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()

    # ADX (simplificado Wilder)
    plus_dm = high.diff().where(high.diff() > low.diff(), 0)
    minus_dm = (-low.diff()).where(low.diff() > high.diff(), 0)
    atr_smooth = tr.ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_smooth
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_smooth
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df["adx"] = dx.ewm(alpha=1/14, adjust=False).mean()
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Volume spike (volumen vs EMA20 volumen)
    vol_ema = vol.ewm(span=20, adjust=False).mean()
    df["volume_spike"] = vol / vol_ema

    # Volumen como feature separada
    df["volume_ema20"] = vol_ema

    print("  -> Indicadores M1 calculados.")
    return df


def alinear_timeframes(df_m1: pd.DataFrame, tf_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Para cada fila M1, busca la última barra cerrada en cada timeframe superior.
    Agrega columnas OHLC + spread del TF superior como features.
    """
    print("[PREPARAR] Alineando timeframes superiores a M1 ...")
    df = df_m1.copy()

    for tf_name, tf_df in tf_data.items():
        if tf_df is None or tf_df.empty:
            continue

        print(f"  -> Fusionando {tf_name} ({len(tf_df):,} barras) ...")

        # merge_asof busca la última barra TF <= cada timestamp M1
        tf_cols = tf_df[["OPEN", "HIGH", "LOW", "CLOSE", "SPREAD"]].copy()
        tf_cols.columns = [f"{c.lower()}_{tf_name.lower()}" for c in tf_cols.columns]
        tf_cols = tf_cols.reset_index()

        df = df.reset_index()
        df = pd.merge_asof(
            df.sort_values("datetime"),
            tf_cols.sort_values("datetime"),
            on="datetime",
            direction="backward",
        )
        df = df.set_index("datetime").sort_index()

    print(f"  -> M1 + TF fusionado: {len(df)} filas x {len(df.columns)} columnas")
    return df


def calcular_confluencias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula señales de confluencia multitemporal para facilitar el entrenamiento.
    """
    print("[PREPARAR] Calculando confluencias multitemporales ...")

    # EMA trend direction: -1 (bajista), 0 (flat), +1 (alcista)
    for tf in ["m1", "m5", "m15", "h1", "h4", "daily"]:
        col = f"close_{tf}"
        if col in df.columns:
            ema = df[col].ewm(span=20, adjust=False).mean()
            df[f"ema_trend_{tf}"] = np.where(df[col] > ema * 1.0002, 1,
                                             np.where(df[col] < ema * 0.9998, -1, 0))

    # RSI confluence: suma de señales (-1 sobrevendido, 0 neutral, +1 sobrecomprado)
    rsi_cols = [c for c in df.columns if c.startswith("rsi") or c.endswith("_rsi")]
    if "rsi" in df.columns:
        df["rsi_signal"] = np.where(df["rsi"] > 70, -1,
                                   np.where(df["rsi"] < 30, 1, 0))
        rsi_cols.append("rsi_signal")

    # Bollinger position: -1 (tocando lower), 0 (middle), +1 (tocando upper)
    df["bb_position_m1"] = np.where(df["CLOSE"] <= df["bb_lower"] * 1.0001, -1,
                                    np.where(df["CLOSE"] >= df["bb_upper"] * 0.9999, 1, 0))

    # Trend strength confluence (ADX > 25 = tendencia fuerte)
    df["trend_strength"] = np.where(df["adx"] > 25, 1, 0)

    # DI confluence
    df["di_confluence"] = np.where(df["plus_di"] > df["minus_di"], 1,
                                   np.where(df["plus_di"] < df["minus_di"], -1, 0))

    # MACD confluence
    df["macd_confluence"] = np.where(
        (df["macd"] > df["macd_signal"]) & (df["macd_hist"] > df["macd_hist"].shift(1)), 1,
        np.where(
            (df["macd"] < df["macd_signal"]) & (df["macd_hist"] < df["macd_hist"].shift(1)), -1, 0
        )
    )

    # EMA alignment confluence (cuántos TFs están alineados)
    ema_trend_cols = [c for c in df.columns if c.startswith("ema_trend_")]
    if ema_trend_cols:
        df["ema_alignment_score"] = df[ema_trend_cols].sum(axis=1)
        df["ema_alignment_pct"] = df[ema_trend_cols].mean(axis=1)  # promedio de tendencias

    print(f"  -> Confluencias calculadas. Columnas totales: {len(df.columns)}")
    return df


def generar_targets(df: pd.DataFrame, horizon: int = 60, tp_sl_ratio: float = 2.0) -> pd.DataFrame:
    """
    Genera targets para RL: regresión del retorno futuro y clasificación de dirección.
    horizon: minutos hacia adelante para evaluar.
    """
    print(f"[PREPARAR] Generando targets (horizon={horizon} min) ...")

    future_close = df["CLOSE"].shift(-horizon)
    df["return_future"] = (future_close - df["CLOSE"]) / df["CLOSE"]

    # Target dirección: 0=SHORT, 1=FLAT, 2=LONG
    threshold = 0.001  # 0.1%
    df["target_direction"] = np.where(
        df["return_future"] > threshold, 2,
        np.where(df["return_future"] < -threshold, 0, 1)
    )

    # Target regresión: retorno normalizado por ATR (reward shaping)
    df["target_reward"] = df["return_future"] / (df["atr"] / df["CLOSE"])

    # Volatilidad futura (útil para tamaño de posición)
    df["future_volatility"] = df["CLOSE"].shift(-horizon).rolling(horizon).std() / df["CLOSE"]

    print("  -> Targets generados.")
    return df


def validar_dataset(df: pd.DataFrame) -> None:
    """Valida que el dataset sea apto para entrenamiento."""
    print("[PREPARAR] Validando dataset ...")
    assert len(df) > 1000, "Dataset muy pequeño"
    assert df["CLOSE"].var() > 0, "Precio sin varianza — datos corruptos"

    # Check NaN
    nan_pct = df.isna().mean().mean() * 100
    print(f"  -> NaN global: {nan_pct:.2f}%")
    if nan_pct > 10:
        print(f"[PREPARAR] WARNING: {nan_pct:.1f}% NaN — considerar adelantar ventana de entrenamiento")

    # Features criticas para Bot Madre
    features_criticas = ["rsi", "ema_fast", "ema_slow", "bb_upper", "bb_lower",
                         "atr", "adx", "macd", "macd_signal"]
    faltantes = [f for f in features_criticas if f not in df.columns]
    assert not faltantes, f"Features críticas faltantes: {faltantes}"

    print("  -> Dataset validado OK.")


def main() -> None:
    RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

    # 1. Cargar timeframes
    print("=" * 60)
    print("FASE 1: CARGA DE DATOS MULTITEMPORALES")
    print("=" * 60)

    m1 = leer_csv_mt5("datatb.csv")
    if m1 is None:
        raise RuntimeError("No se pudo cargar datatb.csv (M1). Verificar que el archivo exista.")

    tf_data = {
        "M5": leer_csv_mt5("datatb_m5.csv"),
        "M15": leer_csv_mt5("datatb_m15.csv"),
        "H1": leer_csv_mt5("datatb_H1.csv"),
        "H4": leer_csv_mt5("datatb_H4.csv"),
        "D1": leer_csv_mt5("datatb_daily.csv"),
    }

    # 2. Calcular indicadores en M1
    print("\n" + "=" * 60)
    print("FASE 2: INDICADORES TÉCNICOS M1")
    print("=" * 60)
    m1 = calcular_indicadores_m1(m1)

    # 3. Alinear timeframes
    print("\n" + "=" * 60)
    print("FASE 3: ALINEACIÓN MULTITEMPORAL")
    print("=" * 60)
    df = alinear_timeframes(m1, tf_data)

    # 4. Confluencias
    print("\n" + "=" * 60)
    print("FASE 4: CONFLUENCIAS")
    print("=" * 60)
    df = calcular_confluencias(df)

    # 5. Targets
    print("\n" + "=" * 60)
    print("FASE 5: TARGETS PARA RL")
    print("=" * 60)
    df = generar_targets(df, horizon=60, tp_sl_ratio=2.0)

    # 6. Limpiar filas con demasiados NaN
    print("\n" + "=" * 60)
    print("FASE 6: LIMPIEZA Y VALIDACIÓN")
    print("=" * 60)

    # Requiere al menos 200 barras previas (warmup EMA200 + targets)
    min_idx = df["ema_200"].first_valid_index()
    if min_idx is not None:
        df = df.loc[min_idx:]

    # Eliminar filas donde target es NaN (últimas N del dataset)
    df = df.dropna(subset=["target_direction"])

    validar_dataset(df)

    # 7. Guardar
    print("\n" + "=" * 60)
    print("FASE 7: EXPORTACIÓN")
    print("=" * 60)

    # Parquet (rápido, comprimido)
    ruta_parquet = RUTA_SALIDA / "datatb_fusion.parquet"
    df.to_parquet(ruta_parquet, compression="zstd")
    print(f"  -> Parquet: {ruta_parquet} ({ruta_parquet.stat().st_size / 1024 / 1024:.1f} MB)")

    # CSV (fallback, legible)
    ruta_csv = RUTA_SALIDA / "datatb_fusion.csv"
    df.to_csv(ruta_csv)
    print(f"  -> CSV:     {ruta_csv} ({ruta_csv.stat().st_size / 1024 / 1024:.1f} MB)")

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DATASET INSTITUCIONAL")
    print("=" * 60)
    print(f"Filas:        {len(df):,}")
    print(f"Columnas:     {len(df.columns)}")
    print(f"Desde:        {df.index.min()}")
    print(f"Hasta:        {df.index.max()}")
    print(f"NaN:          {df.isna().mean().mean()*100:.2f}%")
    print(f"Target LONG:  {(df['target_direction']==2).mean()*100:.1f}%")
    print(f"Target FLAT:  {(df['target_direction']==1).mean()*100:.1f}%")
    print(f"Target SHORT: {(df['target_direction']==0).mean()*100:.1f}%")
    print(f"\nListo para entrenar los 4 bots.")
    print("=" * 60)


if __name__ == "__main__":
    main()

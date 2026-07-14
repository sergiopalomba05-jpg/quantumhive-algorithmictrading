"""preparar_datos_mt5.py — Convierte export CSV de MT5 al formato del notebook Kaggle.

Uso:
    python preparar_datos_mt5.py --input-dir "C:/Users/.../Downloads" --output-dir "C:/Users/.../datasets" --desde 2022-01-01 --hasta 2024-12-31

MT5 exporta columnas:
    <DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<TICKVOL>;<VOL>;<SPREAD>
"""
import argparse
import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd


def detectar_delimitador(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        primera = f.readline()
        if ";" in primera:
            return ";"
        return ","


def parsear_fecha(row) -> pd.Timestamp:
    """MT5 exporta DATE como YYYY.MM.DD y TIME como HH:MM:SS."""
    fecha_raw = str(row["<DATE>"])
    # Quitar puntos si existen: 2022.01.03 → 20220103
    fecha = fecha_raw.replace(".", "").replace("-", "")
    hora_raw = str(row["<TIME>"])
    # Quitar dos puntos si existen: 01:05:00 → 010500
    hora = hora_raw.replace(":", "")
    # Asegurar 6 dígitos
    hora = hora.zfill(6)
    return pd.Timestamp(
        year=int(fecha[0:4]),
        month=int(fecha[4:6]),
        day=int(fecha[6:8]),
        hour=int(hora[0:2]),
        minute=int(hora[2:4]),
        second=int(hora[4:6]),
    )


def procesar_csv(path: Path, desde: pd.Timestamp | None, hasta: pd.Timestamp | None) -> pd.DataFrame:
    sep = detectar_delimitador(path)
    try:
        df = pd.read_csv(path, sep=sep, engine="python")
    except Exception:
        df = pd.read_csv(path, sep="\t", engine="python")

    # Si pandas leyó todo como una sola columna, reintentar explícito
    if len(df.columns) == 1 and "\t" in str(df.columns[0]):
        df = pd.read_csv(path, sep="\t", engine="python")

    # MT5 usa <DATE> y <TIME> como columnas
    if "<DATE>" in df.columns and "<TIME>" in df.columns:
        df["time"] = df.apply(parsear_fecha, axis=1)
        df = df.rename(columns={
            "<OPEN>": "open",
            "<HIGH>": "high",
            "<LOW>": "low",
            "<CLOSE>": "close",
            "<TICKVOL>": "volume",
        })
    elif "time" in df.columns:
        # Ya tiene formato correcto
        df["time"] = pd.to_datetime(df["time"])
    else:
        raise ValueError(f"No sé cómo parsear: {path}. Columnas: {list(df.columns)}")

    df = df[["time", "open", "high", "low", "close", "volume"]].copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").set_index("time")

    if desde is not None:
        df = df[df.index >= desde]
    if hasta is not None:
        df = df[df.index <= hasta]

    # Eliminar duplicados y ordenar
    df = df[~df.index.duplicated(keep="first")]
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, help="Carpeta con CSVs exportados de MT5")
    parser.add_argument("--output-dir", required=True, help="Carpeta de salida")
    parser.add_argument("--desde", default="2022-01-01", help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--hasta", default="2024-12-31", help="Fecha fin (YYYY-MM-DD)")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    desde = pd.Timestamp(args.desde) if args.desde else None
    hasta = pd.Timestamp(args.hasta) if args.hasta else None

    # Buscar archivos por temporalidad
    temporalidades = {
        "M1": ["*M1*", "*1m*", "*1min*"],
        "M5": ["*M5*", "*5m*", "*5min*"],
        "M15": ["*M15*", "*15m*", "*15min*"],
        "H1": ["*H1*", "*1h*", "*60m*"],
    }

    for tf, patterns in temporalidades.items():
        found = False
        for pat in patterns:
            matches = list(input_dir.glob(pat + ".csv")) + list(input_dir.glob(pat + ".CSV"))
            if matches:
                path = matches[0]
                print(f"[{tf}] Procesando: {path.name}")
                df = procesar_csv(path, desde, hasta)
                out_path = output_dir / f"US30_{tf}_2022_2024.csv"
                df.to_csv(out_path)
                print(f"  → {out_path} | Filas: {len(df)} | Desde: {df.index[0]} | Hasta: {df.index[-1]}")
                found = True
                break
        if not found:
            print(f"[{tf}] ⚠️ No encontré CSV. Patrones buscados: {patterns}")

    print("\n✅ Listo. Subí los CSVs de salida a Kaggle como dataset.")


if __name__ == "__main__":
    main()

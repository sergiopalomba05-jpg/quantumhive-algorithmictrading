#!/usr/bin/env python3
"""
Descarga automática de outputs de Kaggle notebook.

Requiere: kaggle API instalada y credentials (~/.kaggle/kaggle.json)

Uso:
    python scripts/descargar_kaggle.py --kernel sergio/quantumhive-us30-unified --output-dir modelos/

Esto descarga:
    - modelo_final.zip
    - bot_unificado.onnx
    - reporte_unificado.json
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> bool:
    print(f"[KAGGLE] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e}")
        return False


def check_kaggle():
    try:
        subprocess.run(["kaggle", "--version"], check=True, capture_output=True)
        return True
    except FileNotFoundError:
        print("[ERROR] kaggle CLI no instalada.")
        print("  pip install kaggle")
        print("  mkdir ~/.kaggle && cp kaggle.json ~/.kaggle/")
        return False


def main():
    parser = argparse.ArgumentParser(description="Descargar outputs de Kaggle")
    parser.add_argument("--kernel", required=True, help="Kernel path (usuario/slug)")
    parser.add_argument("--output-dir", type=Path, default=Path("modelos"))
    args = parser.parse_args()

    if not check_kaggle():
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Descargar outputs
    ok = run([
        "kaggle", "kernels", "output",
        args.kernel,
        "-p", str(args.output_dir),
    ])

    if ok:
        print(f"\n✅ Descargado en: {args.output_dir}")
        for f in args.output_dir.iterdir():
            print(f"   {f.name}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

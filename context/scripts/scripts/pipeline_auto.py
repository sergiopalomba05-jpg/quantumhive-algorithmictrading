#!/usr/bin/env python3
"""
Pipeline automático QuantumHive:
    Entrenar → Validar → Exportar ONNX → Deploy MT5

Uso:
    python scripts/pipeline_auto.py --stage all
    python scripts/pipeline_auto.py --stage validate --model path/to/model.zip
    python scripts/pipeline_auto.py --stage deploy --onnx path/to/bot.onnx
"""
import argparse
import json
import subprocess
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
MODELS_DIR = BASE / "modelos"
ONNX_DIR = BASE / "onnx"
MT5_FILES = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal"  # Windows default
DASHBOARD = BASE / "dashboard" / "progress.json"


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    log(" ".join(cmd))
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        log(f"ERROR: {e}")
        return False


def update_progress(category: str, key: str, status: str):
    try:
        subprocess.run(
            [sys.executable, str(BASE / "scripts" / "save_progress.py"), category, key, status],
            check=True,
        )
    except Exception as e:
        log(f"No se pudo actualizar progreso: {e}")


def stage_train():
    """Fase 1: Entrenar en Kaggle (notebook)."""
    log("=== STAGE: Entrenamiento ===")
    log("Instrucciones manuales para Kaggle:")
    log("  1. Subir notebooks/kaggle_unificado_v1.py a nuevo notebook")
    log("  2. Adjuntar dataset 'us30-ny-session-2022-2024'")
    log("  3. Activar GPU V100, Internet ON")
    log("  4. Run All → esperar ~40 min")
    log("  5. Descargar modelo_final.zip y bot_unificado.onnx")
    log("Este script continuará automáticamente cuando detecte los archivos.")
    update_progress("pipeline", "entrenamiento", "wip")
    return True


def stage_validate(model_path: Path):
    """Fase 2: Validar modelo con backtest walk-forward."""
    log("=== STAGE: Validación ===")
    if not model_path.exists():
        log(f"Modelo no encontrado: {model_path}")
        return False

    update_progress("pipeline", "validacion", "wip")

    # Ejecutar test del entorno (backtest local rápido)
    test_script = BASE / "test_entorno_unificado.py"
    if test_script.exists():
        log("Ejecutando test_entorno_unificado.py...")
        ok = run([sys.executable, str(test_script)], cwd=BASE)
        if not ok:
            update_progress("pipeline", "validacion", "warn")
            return False

    # TODO: Agregar backtest walk-forward 2024 con métricas WR/PF/DD
    log("Validación manual requerida: revisar WR > 35%, PF > 1.2, DD < 20%")
    log("Si pasa: marcar como ok")

    # Por ahora marcamos pendiente a espera de métricas reales
    update_progress("pipeline", "validacion", "warn")
    return True


def stage_export(model_path: Path, onnx_path: Path):
    """Fase 3: Exportar modelo a ONNX opset 11."""
    log("=== STAGE: Export ONNX ===")
    if not model_path.exists():
        log(f"Modelo no encontrado: {model_path}")
        return False

    update_progress("pipeline", "onnx_export", "wip")

    # El notebook Kaggle ya exporta ONNX inline
    # Este stage es para export local si es necesario
    export_script = BASE / "scripts" / "exportar_onnx.py"
    if export_script.exists():
        ok = run([sys.executable, str(export_script), str(model_path), str(onnx_path)])
    else:
        log("exportar_onnx.py no encontrado. Asumiendo export desde Kaggle.")
        ok = True

    if ok and onnx_path.exists():
        log(f"ONNX exportado: {onnx_path}")
        update_progress("pipeline", "onnx_export", "ok")
        update_progress("metrics", "ultimo_modelo", str(model_path.name))
        return True
    else:
        update_progress("pipeline", "onnx_export", "warn")
        return False


def stage_deploy(onnx_path: Path):
    """Fase 4: Copiar ONNX a MT5 /MQL5/Files/ y compilar EA."""
    log("=== STAGE: Deploy MT5 ===")
    if not onnx_path.exists():
        log(f"ONNX no encontrado: {onnx_path}")
        return False

    update_progress("pipeline", "deploy_mt5", "wip")

    # Buscar carpeta MQL5/Files del terminal MT5
    mt5_dirs = list(MT5_FILES.glob("*/MQL5/Files"))
    if not mt5_dirs:
        log("Carpeta MT5 MQL5/Files no encontrada.")
        log(f"  Buscado en: {MT5_FILES}")
        log("  Copiar manualmente a: <Terminal>/MQL5/Files/")
        update_progress("pipeline", "deploy_mt5", "warn")
        return False

    target = mt5_dirs[0] / "bot_unificado.onnx"
    shutil.copy2(onnx_path, target)
    log(f"Copiado a MT5: {target}")

    # Verificar EA
    ea_path = BASE / "mt5" / "QuantumHive_EA.mq5"
    if ea_path.exists():
        log(f"EA encontrado: {ea_path}")
        log("Acción manual: abrir MetaEditor → F5 (Compilar) → Attach to chart US30 M15")
        update_progress("pipeline", "deploy_mt5", "ok")
        return True
    else:
        log("QuantumHive_EA.mq5 no encontrado. Crear antes de deploy.")
        update_progress("pipeline", "deploy_mt5", "warn")
        return False


def main():
    parser = argparse.ArgumentParser(description="Pipeline QuantumHive")
    parser.add_argument("--stage", choices=["all", "train", "validate", "export", "deploy"], default="all")
    parser.add_argument("--model", type=Path, default=MODELS_DIR / "modelo_final.zip")
    parser.add_argument("--onnx", type=Path, default=ONNX_DIR / "bot_unificado.onnx")
    args = parser.parse_args()

    MODELS_DIR.mkdir(exist_ok=True)
    ONNX_DIR.mkdir(exist_ok=True)

    ok = True
    if args.stage in ("all", "train"):
        ok = stage_train() and ok
    if args.stage in ("all", "validate"):
        ok = stage_validate(args.model) and ok
    if args.stage in ("all", "export"):
        ok = stage_export(args.model, args.onnx) and ok
    if args.stage in ("all", "deploy"):
        ok = stage_deploy(args.onnx) and ok

    if ok:
        log("=== Pipeline completado ===")
    else:
        log("=== Pipeline con advertencias / errores ===")
        sys.exit(1)


if __name__ == "__main__":
    main()

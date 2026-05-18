#!/usr/bin/env python3
"""
Versionado automático de modelos con Git.

Uso:
    python scripts/versionar_modelo.py --tag v1.0-us30 --onnx onnx/bot_unificado.onnx --note "WR 42% PF 1.8"

Esto hace:
    1. git add del modelo y notas
    2. git commit con mensaje estructurado
    3. git tag con metadatos
    4. Actualiza progress.json
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
GIT_DIR = BASE / ".git"
PROGRESS = BASE / "scripts" / "progress.json"
METADATA_DIR = BASE / "modelos" / "metadata"


def run(cmd: list[str], cwd: Path = BASE) -> bool:
    print(f"[GIT] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e}")
        return False


def ensure_git():
    if not GIT_DIR.exists():
        print("Inicializando repositorio git...")
        run(["git", "init"])
        # Crear .gitignore básico
        gitignore = BASE / ".gitignore"
        gitignore.write_text("__pycache__/\n*.pyc\n*.egg-info/\n.pytest_cache/\n", encoding="utf-8")
        run(["git", "add", ".gitignore"])
        run(["git", "commit", "-m", "init: .gitignore"])


def save_metadata(tag: str, note: str, onnx_path: Path | None):
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "tag": tag,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": note,
        "onnx_file": str(onnx_path) if onnx_path else None,
    }
    meta_file = METADATA_DIR / f"{tag}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    return meta_file


def update_progress(tag: str, note: str):
    if not PROGRESS.exists():
        return
    with open(PROGRESS, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["metrics"]["ultimo_modelo"] = tag
    data["updated"] = datetime.now(timezone.utc).isoformat()
    with open(PROGRESS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[PROGRESS] Último modelo: {tag}")


def main():
    parser = argparse.ArgumentParser(description="Versionar modelo QuantumHive")
    parser.add_argument("--tag", required=True, help="Tag del modelo (ej: v1.0-us30)")
    parser.add_argument("--onnx", type=Path, help="Ruta al archivo ONNX")
    parser.add_argument("--note", default="", help="Nota sobre el modelo")
    args = parser.parse_args()

    ensure_git()

    # Guardar metadata
    meta_file = save_metadata(args.tag, args.note, args.onnx)
    files_to_add = [str(meta_file)]

    if args.onnx and args.onnx.exists():
        # Copiar a carpeta versionada para tracking
        versioned_dir = BASE / "modelos" / args.tag
        versioned_dir.mkdir(parents=True, exist_ok=True)
        dest = versioned_dir / args.onnx.name
        import shutil
        shutil.copy2(args.onnx, dest)
        files_to_add.append(str(dest))
        print(f"[COPY] {args.onnx} → {dest}")

    # Git add + commit
    run(["git", "add"] + files_to_add)
    commit_msg = f"modelo: {args.tag}\n\nNota: {args.note}"
    run(["git", "commit", "-m", commit_msg])

    # Tag
    tag_msg = f"{args.tag}: {args.note}"
    run(["git", "tag", "-a", args.tag, "-m", tag_msg])

    print(f"\n✅ Modelo versionado: {args.tag}")
    print(f"   git log --oneline")
    print(f"   git show {args.tag}")

    update_progress(args.tag, args.note)


if __name__ == "__main__":
    main()

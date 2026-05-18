#!/usr/bin/env python3
"""
================================================================================
AGENTE DE MANTENIMIENTO — QUANTUMHIVE
================================================================================
Limpia archivos basura, duplicados, caches y proyectos abandonados.
Modo seguro: borra solo con confirmación (default dry-run).

Uso:
    python agente_mantenimiento.py --path .. --dry-run
    python agente_mantenimiento.py --path .. --execute   # BORRA DE VERDAD
================================================================================
"""
import os, sys, hashlib, json, argparse, shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
EXTENSIONES_BASURA = [
    '.pyc', '.pyo', '.pyd', '.so', '.o', '.obj',
    '.log', '.tmp', '.temp', '.swp', '.swo', '.bak', '.orig',
    '.DS_Store', '.Thumbs.db', '.coverage', '.egg-info',
    '.ipynb_checkpoints', '.pytest_cache',
]

NOMBRES_BASURA = [
    '__pycache__', '.pytest_cache', '.mypy_cache', '.tox', '.venv',
    'venv', 'env', 'node_modules', '.ipynb_checkpoints',
    'dist', 'build', '.eggs', '*.egg-info',
    'debug.log', 'npm-debug.log', 'yarn-error.log',
]

ARCHIVOS_VIEJOS_DIAS = 30  # logs y temporales con más de X días

# ═══════════════════════════════════════════════════════════════════════════════
# AGENTE
# ═══════════════════════════════════════════════════════════════════════════════
class AgenteMantenimiento:
    def __init__(self, root: Path, dry_run: bool = True):
        self.root = root.resolve()
        self.dry_run = dry_run
        self.reporte: Dict = {
            'timestamp': datetime.now().isoformat(),
            'root': str(self.root),
            'dry_run': dry_run,
            'basura': [],
            'duplicados': [],
            'viejos': [],
            'total_borrado_mb': 0.0,
            'errores': [],
        }

    # ─── Escaneo de basura ───
    def escanear_basura(self) -> List[Path]:
        basura: List[Path] = []
        for dp, dirs, files in os.walk(self.root):
            dpath = Path(dp)
            # Carpetas basura
            for d in list(dirs):
                if d in NOMBRES_BASURA or any(d.endswith(ext) for ext in ['.egg-info']):
                    basura.append(dpath / d)
                    dirs.remove(d)  # No recursar
            # Archivos basura
            for f in files:
                p = dpath / f
                if any(f.endswith(ext) for ext in EXTENSIONES_BASURA):
                    basura.append(p)
                elif f in ['debug.log', 'npm-debug.log', 'yarn-error.log', 'error.log']:
                    basura.append(p)
        return sorted(set(basura))

    # ─── Duplicados por hash ───
    def escanear_duplicados(self) -> List[List[Path]]:
        hashes: Dict[str, List[Path]] = {}
        for dp, _, files in os.walk(self.root):
            dpath = Path(dp)
            if any(part in NOMBRES_BASURA for part in dpath.parts):
                continue
            for f in files:
                p = dpath / f
                if p.stat().st_size < 1024:  # ignorar archivos < 1KB
                    continue
                try:
                    h = self._hash_file(p)
                    hashes.setdefault(h, []).append(p)
                except Exception as e:
                    self.reporte['errores'].append(f"hash {p}: {e}")
        return [grupo for grupo in hashes.values() if len(grupo) > 1]

    def _hash_file(self, p: Path, chunksize: int = 8192) -> str:
        h = hashlib.blake2b(digest_size=16)
        with open(p, 'rb') as f:
            while chunk := f.read(chunksize):
                h.update(chunk)
        return h.hexdigest()

    # ─── Archivos viejos ───
    def escanear_viejos(self) -> List[Path]:
        viejos: List[Path] = []
        cutoff = datetime.now() - timedelta(days=ARCHIVOS_VIEJOS_DIAS)
        for dp, _, files in os.walk(self.root):
            dpath = Path(dp)
            for f in files:
                p = dpath / f
                if not any(f.endswith(ext) for ext in ['.log', '.tmp', '.temp', '.bak', '.old']):
                    continue
                try:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime)
                    if mtime < cutoff:
                        viejos.append(p)
                except Exception:
                    pass
        return sorted(viejos)

    # ─── Ejecución ───
    def limpiar(self):
        print("=" * 70)
        print(f"  AGENTE DE MANTENIMIENTO — {'DRY-RUN' if self.dry_run else 'EJECUCIÓN REAL'}")
        print(f"  Raíz: {self.root}")
        print("=" * 70)

        # 1. Basura
        basura = self.escanear_basura()
        print(f"\n[1] Basura encontrada: {len(basura)} elementos")
        for p in basura:
            size = self._tamaño(p)
            self.reporte['basura'].append({'path': str(p.relative_to(self.root)), 'size_mb': size})
            self.reporte['total_borrado_mb'] += size
            accion = "[BORRARÍA]" if self.dry_run else "[BORRADO]"
            tipo = "DIR" if p.is_dir() else "FILE"
            print(f"  {accion} ({tipo}) {str(p.relative_to(self.root)):<50} {size:.2f} MB")
            if not self.dry_run:
                self._borrar(p)

        # 2. Duplicados
        dups = self.escanear_duplicados()
        print(f"\n[2] Grupos duplicados: {len(dups)}")
        for grupo in dups:
            size = grupo[0].stat().st_size / (1024 * 1024)
            grupo_rel = [str(p.relative_to(self.root)) for p in grupo]
            self.reporte['duplicados'].append({
                'hash_prefix': self._hash_file(grupo[0])[:8],
                'size_mb': size,
                'paths': grupo_rel,
            })
            print(f"  [DUP] {size:.2f} MB — {len(grupo)} copias")
            for p in grupo_rel:
                print(f"        └─ {p}")

        # 3. Viejos
        viejos = self.escanear_viejos()
        print(f"\n[3] Logs/temp viejos (>{ARCHIVOS_VIEJOS_DIAS} días): {len(viejos)}")
        for p in viejos:
            size = self._tamaño(p)
            self.reporte['viejos'].append({'path': str(p.relative_to(self.root)), 'size_mb': size})
            self.reporte['total_borrado_mb'] += size
            accion = "[BORRARÍA]" if self.dry_run else "[BORRADO]"
            print(f"  {accion} {str(p.relative_to(self.root)):<50} {size:.2f} MB")
            if not self.dry_run:
                self._borrar(p)

        # Resumen
        print(f"\n{'=' * 70}")
        print(f"  Total espacio recuperado: {self.reporte['total_borrado_mb']:.2f} MB")
        print(f"  {'NO se borró nada (dry-run)' if self.dry_run else 'BORRADO COMPLETADO'}")
        print(f"{'=' * 70}\n")

        # Guardar reporte
        reporte_path = self.root / 'scripts' / 'reporte_mantenimiento.json'
        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(self.reporte, f, indent=2, ensure_ascii=False)
        print(f"Reporte guardado: {reporte_path}")

    def _tamaño(self, p: Path) -> float:
        try:
            if p.is_dir():
                total = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
                return total / (1024 * 1024)
            return p.stat().st_size / (1024 * 1024)
        except Exception:
            return 0.0

    def _borrar(self, p: Path):
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        except Exception as e:
            self.reporte['errores'].append(f"borrar {p}: {e}")
            print(f"  ERROR borrando {p}: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Agente de mantenimiento QUANTUMHIVE")
    parser.add_argument("--path", default="..", help="Ruta raíz del proyecto")
    parser.add_argument("--execute", action="store_true", help="Borrar DE VERDAD (default: dry-run)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Ruta no existe: {root}")
        sys.exit(1)

    agente = AgenteMantenimiento(root, dry_run=not args.execute)
    agente.limpiar()

if __name__ == "__main__":
    main()

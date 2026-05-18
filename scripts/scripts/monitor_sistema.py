#!/usr/bin/env python3
"""
Monitor de Salud QuantumHive v3.1
=================================
Verifica archivos criticos, integridad de modelos y estado del sistema.
Ejecutar: python scripts/monitor_sistema.py
"""
import sys, json, hashlib, time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "logs" / "health_check.json"
REPORT.parent.mkdir(parents=True, exist_ok=True)

checks = []
def ok(msg): checks.append({"status":"OK","msg":msg})
def warn(msg): checks.append({"status":"WARN","msg":msg})
def fail(msg): checks.append({"status":"FAIL","msg":msg})

# Archivos criticos
criticos = [
    "nucleo/entornos/entorno_hibrido_unificado.py",
    "notebooks/kaggle_unificado_v3.py",
    "scripts/exportar_onnx.py",
    "scripts/backtest_walkforward_v2.py",
    "ea_mql5/QuantumHive_EA_v3.mq5",
]
for p in criticos:
    fp = ROOT / p
    if fp.exists():
        ok(f"{p} ({fp.stat().st_size/1024:.1f} KB)")
    else:
        fail(f"{p} NO EXISTE")

# Modelo ONNX
onnx = ROOT / "modelos" / "bot_unificado.onnx"
if onnx.exists():
    ok(f"ONNX modelo: {onnx.stat().st_size/1024:.1f} KB")
else:
    warn("ONNX no existe. Ejecutar exportar_onnx.py")

# Modelo PPO
ppo = ROOT / "modelos" / "modelo_unificado" / "modelo_final.zip"
if ppo.exists():
    ok(f"PPO modelo: {ppo.stat().st_size/1024:.1f} KB")
else:
    warn("Modelo PPO no encontrado")

# Resultados backtest
for f in ("backtest_equity.csv","trades_historial.csv","backtest_resumen.json"):
    fp = ROOT / "modelos" / f
    if fp.exists():
        ok(f"Backtest output: {f}")
    else:
        warn(f"Backtest output faltante: {f}")

# Write report
report = {"timestamp": datetime.now().isoformat(), "checks": checks,
          "total": len(checks), "ok": sum(1 for c in checks if c["status"]=="OK")}
with open(REPORT, "w") as f:
    json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
if any(c["status"]=="FAIL" for c in checks):
    sys.exit(1)

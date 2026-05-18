#!/usr/bin/env python3
"""
Actualiza progress.json desde código o línea de comandos.

Ejemplo:
    python scripts/save_progress.py D1_Trading_IA "Cerebro Unificado US30" ok "Listo"
    python scripts/save_progress.py pipeline entrenamiento wip
    python scripts/save_progress.py metrics win_rate 42.5
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROGRESS_PATH = Path(__file__).parent.parent / "scripts" / "progress.json"


def load() -> dict:
    if not PROGRESS_PATH.exists():
        raise FileNotFoundError(f"No existe {PROGRESS_PATH}")
    with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data: dict):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def recalc_progress(data: dict) -> int:
    """Recalcula porcentaje global basado en items completados."""
    total = 0
    done = 0
    for div in data.get("divisiones", {}).values():
        for item in div.get("items", {}).values():
            total += 1
            if item.get("status") == "ok":
                done += 1
    if total == 0:
        return 0
    return round(done / total * 100)


def update_division_item(data: dict, division: str, item_name: str, status: str, badge: str | None = None):
    div = data["divisiones"].get(division)
    if not div:
        raise KeyError(f"División no encontrada: {division}")
    item = div["items"].get(item_name)
    if not item:
        raise KeyError(f"Item no encontrado: {item_name} en {division}")
    item["status"] = status
    if badge:
        item["badge"] = badge
    else:
        mapping = {"ok": "Listo", "wip": "En progreso", "warn": "Pendiente", "pend": "Futuro"}
        item["badge"] = mapping.get(status, status)
    data["progreso_pct"] = recalc_progress(data)
    data["updated"] = datetime.now(timezone.utc).isoformat()
    return data


def update_pipeline(data: dict, stage: str, status: str):
    if stage not in data["pipeline"]:
        raise KeyError(f"Stage no encontrado: {stage}")
    data["pipeline"][stage]["status"] = status
    now = datetime.now(timezone.utc).isoformat()
    if status == "wip":
        data["pipeline"][stage]["started_at"] = now
    elif status in ("ok", "warn", "pend"):
        data["pipeline"][stage]["ended_at"] = now
    data["updated"] = now
    return data


def update_metrics(data: dict, key: str, value):
    data["metrics"][key] = value
    data["updated"] = datetime.now(timezone.utc).isoformat()
    return data


def main():
    if len(sys.argv) < 4:
        print("Uso:")
        print("  python save_progress.py <division> <item> <status> [badge_texto]")
        print("  python save_progress.py pipeline <stage> <status>")
        print("  python save_progress.py metrics <key> <valor>")
        print("  python save_progress.py recalc")
        sys.exit(1)

    data = load()
    category = sys.argv[1]

    if category == "recalc":
        data["progreso_pct"] = recalc_progress(data)
        data["updated"] = datetime.now(timezone.utc).isoformat()
        save(data)
        print(f"Progreso recalculado: {data['progreso_pct']}%")
        return

    if category == "pipeline":
        stage = sys.argv[2]
        status = sys.argv[3]
        data = update_pipeline(data, stage, status)
        save(data)
        print(f"Pipeline {stage} → {status}")
        return

    if category == "metrics":
        key = sys.argv[2]
        # intentar convertir a número
        val = sys.argv[3]
        try:
            val = float(val) if "." in val else int(val)
        except ValueError:
            pass
        data = update_metrics(data, key, val)
        save(data)
        print(f"Metric {key} = {val}")
        return

    # Default: division item update
    division = category
    item_name = sys.argv[2]
    status = sys.argv[3]
    badge = sys.argv[4] if len(sys.argv) > 4 else None
    data = update_division_item(data, division, item_name, status, badge)
    save(data)
    print(f"{division} / {item_name} → {status} ({data['progreso_pct']}%)")


if __name__ == "__main__":
    main()

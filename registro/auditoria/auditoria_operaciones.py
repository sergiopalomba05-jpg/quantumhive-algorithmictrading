"""AuditoriaOperaciones: log inmutable de toda operación."""
from __future__ import annotations
import hashlib, json, os
from datetime import datetime
from pathlib import Path
from typing import Any
import pandas as pd


class AuditoriaOperaciones:
    """Registro append-only con hash SHA256 por entrada."""

    def __init__(self, ruta: str | os.PathLike = "registro/auditoria/auditoria_operaciones.jsonl") -> None:
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, operacion: dict[str, Any]) -> None:
        """Registra operación con hash SHA256 inmutable."""
        entrada = {
            "timestamp": operacion.get("timestamp", datetime.now().isoformat()),
            "cuenta": operacion.get("cuenta", ""),
            "cliente_id": operacion.get("cliente_id", ""),
            "bot": operacion.get("bot", ""),
            "activo": operacion.get("activo", ""),
            "direccion": operacion.get("direccion", ""),
            "score_entrada": operacion.get("score_entrada", 0),
            "skills_activos": operacion.get("skills_activos", []),
            "resultado_pips": operacion.get("resultado_pips", 0.0),
            "resultado_usd": operacion.get("resultado_usd", 0.0),
            "clasificacion": operacion.get("clasificacion", ""),  # A/B/C/D
            "timestamp_cierre": operacion.get("timestamp_cierre", ""),
        }
        payload = json.dumps(entrada, ensure_ascii=False, sort_keys=True)
        entrada["hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

    def verificar_integridad(self) -> list[dict]:
        """Verifica que ningún registro fue modificado comparando hashes."""
        if not self.ruta.exists():
            return []
        invalidos = []
        for i, linea in enumerate(self.ruta.read_text(encoding="utf-8").splitlines(), 1):
            try:
                reg = json.loads(linea)
                hash_guardado = reg.pop("hash", "")
                payload = json.dumps(reg, ensure_ascii=False, sort_keys=True)
                hash_calc = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                if hash_calc != hash_guardado:
                    invalidos.append({"linea": i, "hash_guardado": hash_guardado, "hash_calculado": hash_calc})
            except Exception:
                continue
        return invalidos

    def exportar_para_cliente(self, cliente_id: str, mes: int, año: int) -> pd.DataFrame:
        """Exporta operaciones del cliente en el período como DataFrame."""
        if not self.ruta.exists():
            return pd.DataFrame()
        ops = []
        for linea in self.ruta.read_text(encoding="utf-8").splitlines():
            try:
                op = json.loads(linea)
                if op.get("cliente_id") == cliente_id:
                    ts = op.get("timestamp", "")
                    if ts:
                        d = datetime.fromisoformat(ts)
                        if d.month == mes and d.year == año:
                            ops.append(op)
            except Exception:
                continue
        return pd.DataFrame(ops)

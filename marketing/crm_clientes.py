"""CRMClientes: pipeline de ventas para el servicio BotsCuanticos."""
from __future__ import annotations
import json, os, uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import yaml


class CRMClientes:
    """Gestiona leads, estados de pipeline y propuestas personalizadas."""

    ESTADOS = ["LEAD", "CONTACTADO", "INTERESADO", "PROPUESTA_ENVIADA", "CLIENTE", "PERDIDO"]

    def __init__(self, ruta_leads: str | os.PathLike = "registro/clientes/leads.yaml",
                 ruta_propuestas: str | os.PathLike = "registro/clientes/propuestas") -> None:
        self.ruta_leads = Path(ruta_leads)
        self.ruta_leads.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_propuestas = Path(ruta_propuestas)
        self.ruta_propuestas.mkdir(parents=True, exist_ok=True)
        self.leads: list[dict] = self._cargar()

    def _cargar(self) -> list[dict]:
        if not self.ruta_leads.exists():
            return []
        return yaml.safe_load(self.ruta_leads.read_text(encoding="utf-8")) or []

    def _guardar(self) -> None:
        self.ruta_leads.write_text(yaml.dump(self.leads, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def agregar_lead(self, nombre: str, instagram: str, capital: float,
                     tipo_interes: str, origen: str = "Instagram DM") -> str:
        """Registra nuevo lead."""
        lead_id = str(uuid.uuid4())[:8]
        lead = {
            "id": lead_id,
            "nombre": nombre,
            "instagram": instagram,
            "capital": float(capital),
            "tipo_interes": tipo_interes,
            "origen": origen,
            "estado": "LEAD",
            "fecha_primer_contacto": datetime.now().isoformat(),
            "fecha_ultimo_contacto": datetime.now().isoformat(),
            "notas": "",
            "propuestas_enviadas": [],
        }
        self.leads.append(lead)
        self._guardar()
        return lead_id

    def actualizar_estado(self, lead_id: str, nuevo_estado: str, notas: str = "") -> bool:
        if nuevo_estado not in self.ESTADOS:
            return False
        for l in self.leads:
            if l["id"] == lead_id:
                l["estado"] = nuevo_estado
                l["fecha_ultimo_contacto"] = datetime.now().isoformat()
                l["notas"] = (l.get("notas", "") + "\n" + notas).strip()
                self._guardar()
                return True
        return False

    def leads_para_seguimiento_hoy(self) -> list[dict]:
        """Retorna leads que necesitan seguimiento hoy."""
        hoy = datetime.now()
        seguimiento = []
        for l in self.leads:
            if l.get("estado") in ("PERDIDO", "CLIENTE"):
                continue
            ult = datetime.fromisoformat(l.get("fecha_ultimo_contacto", hoy.isoformat()))
            dias = (hoy - ult).days
            if dias >= 3:
                seguimiento.append({**l, "dias_sin_contacto": dias})
        return seguimiento

    def calcular_conversion(self) -> dict[str, Any]:
        total = len(self.leads)
        estados = {e: sum(1 for l in self.leads if l["estado"] == e) for e in self.ESTADOS}
        clientes = estados.get("CLIENTE", 0)
        propuestas = estados.get("PROPUESTA_ENVIADA", 0)
        tasa = clientes / max(1, total)
        capital_gestionado = sum(l["capital"] for l in self.leads if l["estado"] == "CLIENTE")
        return {
            "total_leads": total,
            "por_estado": estados,
            "tasa_conversion": round(tasa, 4),
            "capital_gestionado_usd": round(capital_gestionado, 2),
        }

    def generar_propuesta(self, lead_id: str) -> Path | None:
        """Genera texto de propuesta personalizada y la guarda."""
        for l in self.leads:
            if l["id"] != lead_id:
                continue
            capital = float(l.get("capital", 0))
            tipo = l.get("tipo_interes", "challenge")
            fee = capital * 0.30 if tipo == "challenge" else capital * 0.25
            texto = (
                f"Hola {l['nombre']},\n\n"
                f"Gracias por tu interés en BotsCuanticos.\n"
                f"Basado en tu capital de ${capital:,.0f} y tu interés en {tipo},\n"
                f"te propongo un fee del {30 if 'challenge' in tipo else 25}% sobre ganancias.\n\n"
                f"Beneficios incluidos:\n"
                f"- Bot especializado en tu activo preferido\n"
                f"- Monitoreo 24/7 del enjambre\n"
                f"- Reporte mensual de auditoría\n"
                f"- Soporte directo por Telegram\n\n"
                f"¿Te gustaría agendar una llamada?\n\n"
                f"Sergio | BotsCuanticos"
            )
            ruta = self.ruta_propuestas / f"propuesta_{lead_id}_{datetime.now().strftime('%Y%m%d')}.txt"
            ruta.write_text(texto, encoding="utf-8")
            l["propuestas_enviadas"].append(str(ruta))
            self._guardar()
            return ruta
        return None

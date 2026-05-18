"""Genera reporte PDF mensual para inversores."""
from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt
import pandas as pd


def generar_reporte_pdf(cliente_id: str, mes: int, año: int,
                        ruta_auditoria: str | os.PathLike = "registro/auditoria/auditoria_operaciones.jsonl",
                        ruta_salida: str | os.PathLike = "registro/reportes") -> Path:
    """Genera reporte PDF profesional mensual para el inversor.

    Requiere ``reportlab`` o ``fpdf2``. Si no están instalados,
    genera un HTML intermedio como fallback.
    """
    ruta_aud = Path(ruta_auditoria)
    if not ruta_aud.exists():
        raise FileNotFoundError(str(ruta_aud))

    ops = []
    for linea in ruta_aud.read_text(encoding="utf-8").splitlines():
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

    df = pd.DataFrame(ops)
    if df.empty:
        raise ValueError("Sin operaciones para el período solicitado")

    # Métricas
    total_ops = len(df)
    gan = df[df["resultado_usd"] > 0]
    per = df[df["resultado_usd"] <= 0]
    winrate = len(gan) / total_ops if total_ops > 0 else 0.0
    pf = gan["resultado_usd"].sum() / abs(per["resultado_usd"].sum()) if not per.empty and per["resultado_usd"].sum() != 0 else 0.0
    pnl_total = df["resultado_usd"].sum()
    dd_max = (df["resultado_usd"].cumsum() - df["resultado_usd"].cumsum().cummax()).min()

    # Gráfico equity
    fig, ax = plt.subplots(figsize=(8, 4))
    equity = df["resultado_usd"].cumsum()
    ax.plot(equity, color="#2ecc71")
    ax.axhline(dd_max, color="#e74c3c", linestyle="--", label=f"DD máx: {dd_max:.2f}")
    ax.set_title(f"Equity Curve - {cliente_id} {mes}/{año}")
    ax.legend()
    fig.tight_layout()

    dir_salida = Path(ruta_salida) / cliente_id
    dir_salida.mkdir(parents=True, exist_ok=True)
    ruta_img = dir_salida / f"equity_{mes}_{año}.png"
    fig.savefig(ruta_img, dpi=150)
    plt.close(fig)

    # Intentar PDF, fallback a HTML
    nombre = f"reporte_{mes}_{año}"
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"REPORTE MENSUAL {mes}/{año} - {cliente_id}", ln=True, align="C")
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Operaciones: {total_ops}  |  Winrate: {winrate:.1%}  |  PF: {pf:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"PnL: ${pnl_total:,.2f}  |  DD Máx: ${dd_max:,.2f}", ln=True)
        pdf.image(str(ruta_img), x=10, y=None, w=190)
        ruta_pdf = dir_salida / f"{nombre}.pdf"
        pdf.output(str(ruta_pdf))
        return ruta_pdf
    except ImportError:
        html = f"""<html><head><meta charset='utf-8'><title>Reporte {mes}/{año}</title></head>
<body><h1>Reporte {mes}/{año} - {cliente_id}</h1>
<p>Operaciones: {total_ops} | Winrate: {winrate:.1%} | PF: {pf:.2f}</p>
<p>PnL: ${pnl_total:,.2f} | DD Máx: ${dd_max:,.2f}</p>
<img src='{ruta_img.name}'></body></html>"""
        ruta_html = dir_salida / f"{nombre}.html"
        ruta_html.write_text(html, encoding="utf-8")
        return ruta_html

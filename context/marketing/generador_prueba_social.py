"""Generador de imágenes de prueba social para Instagram."""
from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _crear_fondo(tamano: tuple[int, int] = (1080, 1080)) -> Image.Image:
    """Fondo degradado oscuro azul/negro."""
    img = Image.new("RGB", tamano, (0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(tamano[1]):
        r = int(5 + (15 - 5) * y / tamano[1])
        g = int(10 + (25 - 10) * y / tamano[1])
        b = int(30 + (60 - 30) * y / tamano[1])
        draw.line([(0, y), (tamano[0], y)], fill=(r, g, b))
    return img


def _texto_centro(draw: ImageDraw.ImageDraw, texto: str, y: int, tamano: int = 40,
                  color: tuple[int, int, int] = (255, 255, 255)) -> None:
    try:
        fuente = ImageFont.truetype("arial.ttf", tamano)
    except Exception:
        fuente = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), texto, font=fuente)
    ancho = bbox[2] - bbox[0]
    x = (1080 - ancho) // 2
    draw.text((x, y), texto, fill=color, font=fuente)


def generar_imagen_challenge_superado(datos: dict[str, Any]) -> Path:
    """Genera imagen cuando se supera un challenge."""
    img = _crear_fondo()
    draw = ImageDraw.Draw(img)
    _texto_centro(draw, "BotsCuanticos", 60, 35, (100, 200, 255))
    _texto_centro(draw, "CHALLENGE SUPERADO ✅", 160, 70, (46, 204, 113))
    firma = datos.get("firma_fondeo", "FTMO")
    _texto_centro(draw, f"Firma: {firma}", 280, 30)
    bal_ini = float(datos.get("balance_inicial", 0))
    bal_fin = float(datos.get("balance_final", 0))
    pct = (bal_fin - bal_ini) / max(1e-12, bal_ini) * 100
    _texto_centro(draw, f"${bal_ini:,.0f}  →  ${bal_fin:,.0f}", 360, 35)
    _texto_centro(draw, f"+{pct:.1f}%", 430, 60, (46, 204, 113))
    dias = int(datos.get("dias_tardados", 0))
    _texto_centro(draw, f"Completado en {dias} días", 520, 30)

    # Equity mini
    equity = datos.get("equity_curve", [])
    if equity:
        fig, ax = plt.subplots(figsize=(6, 2), facecolor="none")
        ax.plot(equity, color="#2ecc71", linewidth=1.5)
        ax.axis("off")
        fig.tight_layout(pad=0)
        tmp = Path("_tmp_eq.png")
        fig.savefig(tmp, dpi=150, transparent=True)
        plt.close(fig)
        eq_img = Image.open(tmp).convert("RGBA")
        eq_img = eq_img.resize((900, 200))
        img.paste(eq_img, (90, 650), eq_img)
        tmp.unlink(missing_ok=True)

    # Watermark
    try:
        wm_font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        wm_font = ImageFont.load_default()
    draw.text((800, 1040), "BotsCuánticos™", fill=(255, 255, 255, 80), font=wm_font)

    salida = Path("marketing/contenido/challenges")
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"challenge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(ruta, quality=95)
    return ruta


def generar_imagen_resultado_semanal(metricas: dict[str, Any]) -> Path:
    """Genera imagen de resultados semanales del enjambre."""
    img = _crear_fondo()
    draw = ImageDraw.Draw(img)
    _texto_centro(draw, "RESULTADOS SEMANALES", 80, 50, (100, 200, 255))
    semana = metricas.get("semana", "")
    _texto_centro(draw, semana, 150, 30)
    pnl = float(metricas.get("pnl_pct", 0))
    wr = float(metricas.get("winrate", 0))
    ops = int(metricas.get("operaciones", 0))
    _texto_centro(draw, f"PnL: {pnl:+.2f}%", 220, 45, (46, 204, 113) if pnl >= 0 else (231, 76, 60))
    _texto_centro(draw, f"Winrate: {wr:.1%}  |  Ops: {ops}", 300, 30)
    mejor = metricas.get("mejor_operacion", "")
    if mejor:
        _texto_centro(draw, f"Mejor: {mejor}", 370, 25)

    # Gráfico barras por día
    dias = metricas.get("pnl_por_dia", [])
    if dias:
        fig, ax = plt.subplots(figsize=(7, 2.5), facecolor="none")
        colores = ["#2ecc71" if d >= 0 else "#e74c3c" for d in dias]
        ax.bar(range(len(dias)), dias, color=colores)
        ax.set_xticks(range(len(dias)))
        ax.set_xticklabels(["L", "M", "X", "J", "V"][:len(dias)])
        ax.axis("off")
        fig.tight_layout(pad=0)
        tmp = Path("_tmp_bar.png")
        fig.savefig(tmp, dpi=150, transparent=True)
        plt.close(fig)
        bar_img = Image.open(tmp).convert("RGBA")
        bar_img = bar_img.resize((900, 280))
        img.paste(bar_img, (90, 500), bar_img)
        tmp.unlink(missing_ok=True)

    salida = Path("marketing/contenido/semanales")
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"semana_{datetime.now().strftime('%Y%m%d')}.png"
    img.save(ruta, quality=95)
    return ruta


def generar_imagen_estadisticas_bot(bot_nombre: str, metricas: dict[str, Any]) -> Path:
    """Genera imagen con estadísticas históricas de un bot."""
    img = _crear_fondo()
    draw = ImageDraw.Draw(img)
    _texto_centro(draw, bot_nombre, 60, 45, (100, 200, 255))
    activo = metricas.get("activo", "US30")
    _texto_centro(draw, f"Activo: {activo}", 130, 25)
    wr = float(metricas.get("winrate", 0))
    pf = float(metricas.get("profit_factor", 0))
    dd = float(metricas.get("drawdown_max", 0))
    total_ops = int(metricas.get("total_operaciones", 0))
    _texto_centro(draw, f"Winrate: {wr:.1%}", 200, 30)
    _texto_centro(draw, f"Profit Factor: {pf:.2f}", 250, 30)
    _texto_centro(draw, f"DD Máx: {dd:.2f}%", 300, 30)
    _texto_centro(draw, f"Total Ops: {total_ops}", 350, 30)

    equity = metricas.get("equity_historica", [])
    if equity:
        fig, ax = plt.subplots(figsize=(7, 2.5), facecolor="none")
        ax.plot(equity, color="#3498db", linewidth=1.5)
        ax.fill_between(range(len(equity)), equity, alpha=0.2, color="#3498db")
        ax.axis("off")
        fig.tight_layout(pad=0)
        tmp = Path("_tmp_eq_bot.png")
        fig.savefig(tmp, dpi=150, transparent=True)
        plt.close(fig)
        eq_img = Image.open(tmp).convert("RGBA")
        eq_img = eq_img.resize((900, 280))
        img.paste(eq_img, (90, 450), eq_img)
        tmp.unlink(missing_ok=True)

    salida = Path("marketing/contenido/estadisticas")
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"stats_{bot_nombre}_{datetime.now().strftime('%Y%m%d')}.png"
    img.save(ruta, quality=95)
    return ruta

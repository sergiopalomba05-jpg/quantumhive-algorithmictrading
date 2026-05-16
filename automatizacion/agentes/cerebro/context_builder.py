"""
Context Builder — Construye el bloque de contexto que se inyecta en AGI.
"""

import logging
from datetime import datetime
from typing import Optional

from .estado_global import EstadoGlobal, determinar_horario_operativo

logger = logging.getLogger(__name__)


def _obtener_emoji_precio(precio: float, cambio_24h: float) -> str:
    if cambio_24h > 0.5:
        return "🟢"
    elif cambio_24h < -0.5:
        return "🔴"
    return "⚪"


def _formatear_posicion(pos) -> str:
    if pos is None:
        return "  └── Sin posición abierta"
    emoji = "🟢" if pos.side == "LONG" else "🔴"
    diff = pos.pnl_actual
    emoji_pnl = "✅" if diff >= 0 else "📉"
    return (
        f"  └── Posición abierta: {emoji} {pos.side} desde ${pos.entry_price:,.0f}\n"
        f"      SL: ${pos.sl:,.0f} | TP: ${pos.tp:,.0f}\n"
        f"      {emoji_pnl} P&L actual: ${diff:+.2f}"
    )


def construir_contexto_completo(estado: EstadoGlobal) -> str:
    ahora = datetime.now()
    emoji_precio = _obtener_emoji_precio(estado.btc_precio_actual, estado.btc_cambio_24h)

    # Estado goat_btc
    goat_activo = "✅ ACTIVO" if estado.goat_btc_activo else "❌ INACTIVO"
    if estado.goat_btc_ultimo_heartbeat:
        goat_activo += f" (último heartbeat: {estado.goat_btc_ultimo_heartbeat[:19]})"

    # Posición
    pos_texto = _formatear_posicion(estado.btc_posicion_activa)

    # Performance
    winrate = estado.btc_winrate_semana * 100
    perf = (
        f"  Trades: {estado.btc_trades_hoy} | Señales: {estado.btc_senales_hoy}\n"
        f"  P&L del día: ${estado.btc_pnl_hoy:+.2f}\n"
        f"  Winrate semana: {winrate:.0f}%"
    )

    # Horario Sergio
    en_horario = determinar_horario_operativo()
    if en_horario:
        sergio_status = "✅ En horario operativo (10:30-13:00 AR)"
    else:
        sergio_status = "⏳ Fuera del horario operativo (próxima sesión: mañana 10:30)"
    if estado.sergio_ultimo_mensaje:
        sergio_status += f"\n  Último mensaje: {estado.sergio_ultimo_mensaje[:19]}"

    # Eventos recientes
    eventos_str = "\n".join([
        f"  {ev.timestamp[:16]} — {ev.tipo}: {str(ev.payload)[:60]}"
        for ev in estado.ultimos_eventos[:5]
    ]) if estado.ultimos_eventos else "  Sin eventos recientes"

    # Alertas
    alertas_str = "\n".join([
        f"  {'🔴' if a.severidad == 'CRITICA' else '⚠️'} {a.mensaje}"
        for a in estado.alertas_pendientes
    ]) if estado.alertas_pendientes else "  ✅ Ninguna"

    return f"""
═══ ESTADO ACTUAL DEL SISTEMA — {ahora.strftime('%H:%M')} ═══

📊 BTC/USD: {emoji_precio} ${estado.btc_precio_actual:,.0f}{f' | Cambio 24h: {estado.btc_cambio_24h:+.1f}%' if estado.btc_cambio_24h else ''}

🤖 goat_btc: {goat_activo}
{pos_texto}

📈 Performance hoy:
{perf}

👤 Sergio:
└── {sergio_status}

⚡ Eventos recientes:
{eventos_str}

⚠️ Alertas activas:
{alertas_str}
═══════════════════════════════════════════"""


def construir_contexto_minimo(estado: EstadoGlobal) -> str:
    precio = f"${estado.btc_precio_actual:,.0f}" if estado.btc_precio_actual else "N/A"
    pos = "Sin posición" if not estado.btc_posicion_activa else \
        f"{estado.btc_posicion_activa.side} @ ${estado.btc_posicion_activa.entry_price:,.0f}"
    return f"📊 BTC: {precio} | goat_btc: {'✅' if estado.goat_btc_activo else '❌'} | Posición: {pos} | P&L hoy: ${estado.btc_pnl_hoy:+.2f}"

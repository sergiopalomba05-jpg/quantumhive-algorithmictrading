#!/usr/bin/env python3
"""
terminal_ui.py — Terminal UI for GOAT BTC Trading Agent
Rich-based dark theme visual terminal designed for YouTube recording.
"""

import threading
import random
import datetime

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.live import Live


class TerminalUI:
    """Visual terminal for GOAT BTC trading agent using rich library."""

    def __init__(self, nombre_agente="G.O.A.T PROTOCOL"):
        self.nombre_agente = nombre_agente
        self.layout = None
        self.console = Console()
        self.live = None
        self.mensajes_conversacion = []
        self.ultima_senal = None
        self.historial_senales = []
        self.ultimo_mensaje = ""
        self.stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Helper decorativo
    # ------------------------------------------------------------------

    @staticmethod
    def _hex_encriptado():
        """Genera una línea de datos encriptados decorativa que cambia cada frame."""
        bytes_ = [f"{random.randint(0, 255):02X}" for _ in range(8)]
        return " ".join(bytes_)

    @staticmethod
    def _barra(valor_abs, max_chars, escala):
        """Genera barra proporcional █/░."""
        proporcion = min(1.0, valor_abs / escala)
        filled = int(proporcion * max_chars)
        return "█" * filled + "░" * (max_chars - filled)

    # ------------------------------------------------------------------
    # Inicio / detención
    # ------------------------------------------------------------------

    def iniciar(self):
        """Construye el layout e inicia la visualización en vivo."""
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="cuerpo"),
            Layout(name="senales", size=8),
        )
        self.layout["cuerpo"].split_row(
            Layout(name="macro", ratio=30),
            Layout(name="regimen", ratio=40),
            Layout(name="flujo", ratio=30),
        )

        vacio = lambda: {"ultimas_5_velas": []}
        self.layout["header"].update(self.render_header())
        self.layout["macro"].update(self.render_macro_h1({}))
        self.layout["regimen"].update(self.render_regimen_m15({}))
        self.layout["flujo"].update(self.render_flujo_m1({}))
        self.layout["senales"].update(self.render_senales())

        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=1 / 3,
            screen=True,
        )
        with self.live:
            self.stop_event.wait()

    def detener(self):
        """Detiene la terminal en vivo."""
        self.stop_event.set()
        if self.live is not None:
            try:
                self.live.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Renderers
    # ------------------------------------------------------------------

    def render_header(self) -> Panel:
        """Panel superior — nombre del agente, hora, BTC placeholder y línea encriptada."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        hex_line = self._hex_encriptado()

        texto = Text.assemble(
            (" \u26a1 ", "bold magenta"),
            (f"{self.nombre_agente}", "bold cyan"),
            (" | QUANTUMHIVE ", "white"),
            ("| ", "dim"),
            (f"{now}", "bold green"),
            (" UTC", "dim"),
            "\n",
            ("BTC: ", "white"),
            ("$XX,XXX.XX", "bold yellow"),
            (" | Cambio 24h: ", "dim"),
            ("+0.00%", "green"),
            ("  \u25cf ONLINE", "bold green"),
            "\n",
            (f"0x{hex_line}", "dark_sea_green"),
        )
        return Panel(
            texto,
            border_style="bright_blue",
            padding=(0, 1),
        )

    def render_macro_h1(self, data: dict) -> Panel:
        """Panel de análisis macro en H1 con BB, CVD y BBW."""
        precio = data.get("precio", 0)
        bb_sup = data.get("bb_sup", 0)
        bb_media = data.get("bb_media", 0)
        bb_inf = data.get("bb_inf", 0)
        dist_sup = data.get("distancia_sup_pct", 0)
        dist_inf = data.get("distancia_inf_pct", 0)
        cvd = data.get("cvd_largo", 0)
        bbw = data.get("bbw", 0)
        regimen = data.get("regimen", "\u2014")

        _fmt_precio = lambda v: f"${v:,.0f}" if v else "$--"

        cvd_abs = abs(cvd) if cvd else 0
        cvd_bar = self._barra(cvd_abs, 10, 2000)
        cvd_color = "green" if cvd >= 0 else "red"
        cvd_label = "COMPRADORES" if cvd >= 0 else "VENDEDORES"

        if bbw < 0.03:
            bbw_color = "green"
            bbw_label = "RANGO"
        elif bbw < 0.05:
            bbw_color = "yellow"
            bbw_label = "TRANSICI\u00d3N"
        else:
            bbw_color = "red"
            bbw_label = "TENDENCIA"

        texto = Text.assemble(
            ("[ AN\u00c1LISIS MACRO \u2014 H1 ]\n", "bold cyan"),
            ("BB 30/3.0\n", "dim"),
            ("Sup: ", "white"),
            (_fmt_precio(bb_sup), "yellow"),
            ("  Med: ", "white"),
            (_fmt_precio(bb_media), "white"),
            ("  Inf: ", "white"),
            (_fmt_precio(bb_inf), "yellow"),
            "\n",
            ("Distancia a Sup: ", "white"),
            (f"{dist_sup:+.2f}%   ", "white"),
            ("a Inf: ", "white"),
            (f"{dist_inf:+.2f}%\n", "white"),
            ("CVD: ", "white"),
            (f"{cvd_bar} ", "bold"),
            (f"{cvd:+,.0f} ", cvd_color),
            (f"{cvd_label}\n", cvd_color),
            ("BBW: ", "white"),
            (f"{bbw:.3f} \u2014 ", "white"),
            (f"{bbw_label}\n", bbw_color),
            ("R\u00e9gimen: ", "white"),
            (f"{regimen}", "bold"),
        )
        return Panel(texto, title="MACRO H1", border_style="blue", padding=(0, 1))

    def render_regimen_m15(self, data: dict) -> Panel:
        """Panel de régimen operativo M15 con ADX, BBW, CVD y clasificación."""
        bb_sup = data.get("bb_sup", 0)
        bb_media = data.get("bb_media", 0)
        bb_inf = data.get("bb_inf", 0)
        adx = data.get("adx", 0)
        bbw = data.get("bbw", 0)
        cvd = data.get("cvd_medio", 0)
        clasificacion = data.get("clasificacion", "\u2014")
        senal_bloqueada = data.get("senal_bloqueada", False)

        _fmt_p = lambda v: f"${v:,.0f}" if v else "$--"

        # ADX
        adx_filled = min(16, int(adx / 50 * 16))
        adx_bar = "\u2588" * adx_filled + "\u2591" * (16 - adx_filled)
        if adx < 20:
            adx_label = "SIN TENDENCIA"
            adx_color = "yellow"
        elif adx < 25:
            adx_label = "TENDENCIA D\u00c9BIL"
            adx_color = "cyan"
        else:
            adx_label = "TENDENCIA FUERTE"
            adx_color = "green"

        # BBW
        bbw_filled = min(12, int(bbw / 0.05 * 12))
        bbw_bar = "\u2588" * bbw_filled + "\u2591" * (12 - bbw_filled)
        if bbw < 0.03:
            bbw_color = "green"
            bbw_label = "RANGO"
        elif bbw < 0.05:
            bbw_color = "yellow"
            bbw_label = "TRANSICI\u00d3N"
        else:
            bbw_color = "red"
            bbw_label = "TENDENCIA"

        # CVD
        cvd_abs = abs(cvd) if cvd else 0
        cvd_bar = self._barra(cvd_abs, 10, 2000)
        cvd_color = "green" if cvd >= 0 else "red"
        cvd_label = "COMPRADORES" if cvd >= 0 else "VENDEDORES"

        # Clasificación
        if "RANGO" in clasificacion.upper():
            reg_icon = "\U0001f7e2"
            reg_color = "green"
        elif "TRANSICI" in clasificacion.upper():
            reg_icon = "\U0001f7e1"
            reg_color = "yellow"
        else:
            reg_icon = "\U0001f534"
            reg_color = "red"

        bloqueo = " [BLOQUEADA \U0001f512]" if senal_bloqueada else ""

        texto = Text.assemble(
            ("[ R\u00c9GIMEN OPERATIVO \u2014 M15 ]\n", "bold cyan"),
            ("BB 30/3.0: ", "dim"),
            ("Sup=", "white"),
            (_fmt_p(bb_sup), "yellow"),
            (" | Med=", "white"),
            (_fmt_p(bb_media), "white"),
            (" | Inf=", "white"),
            (_fmt_p(bb_inf), "yellow"),
            "\n",
            ("ADX: ", "white"),
            (f"{adx:.1f} ", "white"),
            (f"{adx_bar} ", "bold"),
            (f"[{adx:.1f}] ", "white"),
            (f"{adx_label}\n", adx_color),
            ("BBW: ", "white"),
            (f"{bbw:.3f} ", "white"),
            (f"{bbw_bar} ", "bold"),
            (f"[{bbw:.3f}] ", "white"),
            (f"{bbw_label}\n", bbw_color),
            ("CVD: ", "white"),
            (f"{cvd_bar} ", "bold"),
            (f"{cvd:+,.0f} ", cvd_color),
            (f"{cvd_label}\n", cvd_color),
            ("R\u00e9gimen: ", "bold"),
            (f"{reg_icon} ", "bold"),
            (f"{clasificacion}", reg_color),
            (f"{bloqueo}", "bold red"),
        )
        return Panel(
            texto, title="R\u00c9GIMEN M15", border_style="cyan", padding=(0, 1)
        )

    def render_flujo_m1(self, data: dict) -> Panel:
        """Panel de flujo en tiempo real M1 — velas, CVD corto, imbalance."""
        velas = data.get("ultimas_5_velas", [])
        cvd_corto = data.get("cvd_corto", 0)
        imbalance = data.get("imbalance", 0)
        vol_relativo = data.get("vol_relativo", 0)

        lines = [("[ FLUJO EN TIEMPO REAL \u2014 M1 ]\n", "bold cyan")]
        lines.append(("\u00daltimas 5 velas:\n", "dim"))

        if velas:
            max_delta = max((abs(v.get("delta", 0)) for v in velas), default=1)
            for vela in velas:
                t = vela.get("time", "")
                delta = vela.get("delta", 0)
                arrow = "\u25b2" if delta >= 0 else "\u25bc"
                color = "green" if delta >= 0 else "red"
                filled = min(14, int(abs(delta) / max_delta * 14))
                bar = "\u2588" * filled + "\u2591" * (14 - filled)
                lines.append((f"{t} ", "dim"))
                lines.append((f"{arrow} ", color))
                lines.append((f"{delta:+,.0f}  ", color))
                lines.append((f"{bar}\n", "bold"))
        else:
            lines.append(("  Sin datos a\u00fan...\n", "dim italic"))

        # CVD corto
        cvd_abs = abs(cvd_corto) if cvd_corto else 0
        cvd_bar = self._barra(cvd_abs, 10, 500)
        cvd_color = "green" if cvd_corto >= 0 else "red"
        cvd_label = "COMPRADOR" if cvd_corto >= 0 else "VENDEDOR"
        lines.append(("CVD corto: ", "white"))
        lines.append((f"{cvd_corto:+,.0f} ", "white"))
        lines.append((f"{cvd_bar} ", "bold"))
        lines.append((f"{cvd_label}\n", cvd_color))

        # Imbalance
        if imbalance > 0.2:
            im_color = "green"
            im_label = "\u25b6 PRESI\u00d3N COMPRA"
        elif imbalance < -0.2:
            im_color = "red"
            im_label = "\u25c0 PRESI\u00d3N VENTA"
        else:
            im_color = "yellow"
            im_label = "\u27fe NEUTRAL"
        lines.append(("Imbalance: ", "white"))
        lines.append((f"{imbalance:+.2f} ", "white"))
        lines.append((f"{im_label}\n", im_color))

        # Vol relativo
        if vol_relativo > 1.5:
            vol_color = "green"
        elif vol_relativo > 1.0:
            vol_color = "yellow"
        else:
            vol_color = "dim"
        lines.append(("Vol relativo: ", "white"))
        lines.append((f"{vol_relativo:.2f}", vol_color))

        return Panel(
            Text.assemble(*lines),
            title="FLUJO M1",
            border_style="green",
            padding=(0, 1),
        )

    def render_senales(self) -> Panel:
        """Panel inferior — última señal, historial y conversación."""
        lines = []

        # -- Última señal --
        lines.append(("\u2550" * 3 + " \u00daLTIMA SE\u00d1AL " + "\u2550" * 3 + "\n", "bold yellow"))
        if self.ultima_senal:
            s = self.ultima_senal
            tipo = s.get("tipo", "\u2014")
            score = s.get("score", 0)
            precio = s.get("precio", 0)
            bb_inf = s.get("bb_inf", 0)
            confluencias = s.get("confluencias", [])
            clasificacion = s.get("clasificacion", "\u2014")

            tipo_color = "green" if tipo == "LONG" else "red"
            if score >= 70:
                score_color = "green"
                score_icon = "\U0001f7e2"
            elif score >= 50:
                score_color = "yellow"
                score_icon = "\U0001f7e1"
            else:
                score_color = "red"
                score_icon = "\U0001f534"

            lines.append((f" {tipo} ", tipo_color + " bold"))
            lines.append((f"| Score: {score}/100 ", score_color))
            lines.append((f"{score_icon}\n", score_color))
            lines.append(("Precio: ", "white"))
            lines.append((f"${precio:,.0f} ", "bold yellow"))
            lines.append(("| BB Inf: ", "white"))
            lines.append((f"${bb_inf:,.0f}\n", "bold yellow"))

            if confluencias:
                for c in confluencias:
                    lines.append(("\u2705 ", "green"))
                    lines.append((f"{c}\n", "green"))
            lines.append(("Clasificaci\u00f3n: ", "white"))
            lines.append((f"{clasificacion}\n", "bold cyan"))
        else:
            lines.append(("  Sin se\u00f1ales a\u00fan...\n", "dim italic"))

        # -- Historial --
        lines.append(("\u2500" * 3 + " \u00daltimas se\u00f1ales " + "\u2500" * 3 + "\n", "bold yellow"))
        if self.historial_senales:
            for senal in self.historial_senales:
                ts = senal.get("timestamp", "\u2014")
                tipo = senal.get("tipo", "\u2014")
                score = senal.get("score", 0)
                estado = senal.get("estado", "\u2014")
                tipo_color = "green" if tipo == "LONG" else "red"
                estado_icon = "\u2705" if "CONFIRMADA" in estado.upper() else "\u23ed"
                lines.append((f"[{ts}] ", "dim"))
                lines.append((f"{tipo:<5} ", tipo_color + " bold"))
                lines.append((f"{score:<3} ", "white"))
                lines.append((f"{estado_icon} {estado}\n", "white"))
        else:
            lines.append(("  Sin historial\n", "dim italic"))

        # -- Conversación --
        lines.append(("\u2500" * 3 + " \u00daltimo mensaje " + "\u2500" * 3 + "\n", "bold yellow"))
        if self.mensajes_conversacion:
            pregunta, respuesta = self.mensajes_conversacion[-1]
            lines.append((f"> {pregunta}\n", "bold white"))
            lines.append((f"\u258e{respuesta}\n", "italic white"))
        else:
            lines.append(("  Sin conversaci\u00f3n\n", "dim italic"))

        return Panel(
            Text.assemble(*lines),
            border_style="bright_magenta",
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def actualizar(self, macro_data, regimen_data, flujo_data):
        """Actualiza todos los paneles con nueva información (llamar cada ~3s)."""
        try:
            self.layout["header"].update(self.render_header())
            self.layout["macro"].update(self.render_macro_h1(macro_data))
            self.layout["regimen"].update(self.render_regimen_m15(regimen_data))
            self.layout["flujo"].update(self.render_flujo_m1(flujo_data))
            self.layout["senales"].update(self.render_senales())
            self.live.update(self.layout)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Señales y conversación
    # ------------------------------------------------------------------

    def mostrar_senal(self, senal: dict):
        """Registra una nueva señal en el historial."""
        self.ultima_senal = senal
        self.historial_senales.insert(0, senal)
        if len(self.historial_senales) > 5:
            self.historial_senales.pop()
        tipo = senal.get("tipo", "\u2014")
        self.console.log(
            f"[bold magenta]\u26a1 SE\u00d1AL: {tipo} "
            f"Score: {senal.get('score', 0)}[/]"
        )

    def agregar_mensaje(self, pregunta: str, respuesta: str):
        """Agrega un par pregunta/respuesta a la conversación."""
        self.mensajes_conversacion.append((pregunta, respuesta))
        if len(self.mensajes_conversacion) > 5:
            self.mensajes_conversacion.pop(0)
        self.ultimo_mensaje = respuesta

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def esperar_input(self) -> str:
        """Espera entrada del usuario con prompt estilizado."""
        try:
            return self.console.input("[bold magenta]\u26a1 GOAT> [/]")
        except (KeyboardInterrupt, EOFError):
            self.detener()
            return ""

    @staticmethod
    def limpiar_input():
        """No-op para completitud de API."""
        return

import threading
import random
import datetime
import time
from collections import deque

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

# Paleta QuantumHive
G = "#00FF41"
R = "#FF0000"
Y = "#FFD700"
C = "#00FFFF"
W = "#FFFFFF"

class TerminalUI:
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

        self.raz_lines = deque(maxlen=8)
        self._raz_lock = threading.Lock()

        self._pulse_counter = 0
        self._start_time = time.time()
        self._last_price = None
        self._last_score = None
        self._last_signal = None
        self._update_counter = 0

    @staticmethod
    def _hex_encriptado():
        bytes_ = [f"{random.randint(0, 255):02X}" for _ in range(12)]
        return "0x" + " ".join(bytes_)

    @staticmethod
    def _barra(valor_abs, max_chars, escala):
        proporcion = min(1.0, valor_abs / escala) if escala else 0
        filled = int(proporcion * max_chars)
        return "\u2588" * filled + "\u2591" * (max_chars - filled)

    def agregar_razonamiento(self, linea: str):
        with self._raz_lock:
            self.raz_lines.append(linea)

    def _get_raz_lines(self):
        with self._raz_lock:
            return list(self.raz_lines)

    def iniciar(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="cuerpo"),
            Layout(name="razonamiento", size=6),
            Layout(name="senales", size=6),
            Layout(name="status_bar", size=1),
        )
        self.layout["cuerpo"].split_row(
            Layout(name="macro", ratio=30),
            Layout(name="regimen", ratio=40),
            Layout(name="flujo", ratio=30),
        )

        self.layout["header"].update(self.render_header({}))
        self.layout["macro"].update(self.render_macro_h1({}))
        self.layout["regimen"].update(self.render_regimen_m15({}))
        self.layout["flujo"].update(self.render_flujo_m1({}))
        self.layout["razonamiento"].update(self.render_razonamiento())
        self.layout["senales"].update(self.render_senales())
        self.layout["status_bar"].update(self.render_status_bar({}))

        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=1,
            screen=True,
        )
        with self.live:
            self.stop_event.wait()

    def detener(self):
        self.stop_event.set()
        if self.live is not None:
            try:
                self.live.stop()
            except Exception:
                pass

    def render_header(self, data: dict) -> Panel:
        tz = datetime.timezone(datetime.timedelta(hours=-3))
        now = datetime.datetime.now(tz).strftime("%H:%M:%S")
        precio = data.get("precio", 0)
        cambio_24h = data.get("cambio_24h", 0)
        regimen = data.get("regimen", "RANGO").upper()

        self._pulse_counter += 1
        pulsating = "\u25cf" if (self._pulse_counter // 2) % 2 == 0 else "\u25cb"

        if regimen == "RANGO":
            pulse_color = G
            estado = "OPERANDO"
        elif regimen == "TENDENCIA":
            pulse_color = G
            estado = "OPERANDO"
        else:
            pulse_color = Y
            estado = "OPERANDO"

        precio_str = f"${precio:,.2f}" if precio else "$--,---.--"

        texto = Text.assemble(
            (f" {pulsating}  {self.nombre_agente}  ", f"bold {C}"),
            ("| QUANTUMHIVE ", "dim white"),
            (f"{now}", f"bold {G}"),
            (" UTC", "dim white"),
            ("\n", ""),
            ("  ", "white"),
            (f"{precio_str}", f"bold {Y}"),
            ("  ", ""),
            (f"{pulsating}", f"bold {pulse_color}"),
            (f" {estado}", f"bold {pulse_color}"),
            ("  |  Cambio 24h: ", "dim white"),
            (f"{cambio_24h:+.2f}%", G if cambio_24h >= 0 else R),
        )
        return Panel(texto, border_style=C, padding=(0, 1))

    def render_macro_h1(self, data: dict) -> Panel:
        precio = data.get("precio", 0)
        bb_sup = data.get("bb_sup", 0)
        bb_media = data.get("bb_media", 0)
        bb_inf = data.get("bb_inf", 0)
        dist_sup = data.get("distancia_sup_pct", 0)
        dist_inf = data.get("distancia_inf_pct", 0)
        cvd = data.get("cvd_largo", 0)
        bbw = data.get("bbw", 0)
        regimen = data.get("regimen", "\u2014")

        _fmt = lambda v: f"${v:,.0f}" if v else "$--"

        cvd_abs = abs(cvd) if cvd else 0
        cvd_bar = self._barra(cvd_abs, 10, 2000)
        cvd_color = G if cvd >= 0 else R
        cvd_label = "COMPRADORES" if cvd >= 0 else "VENDEDORES"

        bbw_color = G if bbw < 0.025 else (Y if bbw < 0.035 else R)
        bbw_label = "RANGO" if bbw < 0.025 else ("TRANSICI\u00d3N" if bbw < 0.035 else "TENDENCIA")

        texto = Text.assemble(
            ("[ AN\u00c1LISIS MACRO \u2014 H1 ]\n", f"bold {C}"),
            ("BB 30/3.0\n", "dim white"),
            ("Sup: ", "white"), (_fmt(bb_sup), Y),
            ("  Med: ", "white"), (_fmt(bb_media), "white"),
            ("  Inf: ", "white"), (_fmt(bb_inf), Y), "\n",
            ("Distancia a Sup: ", "white"), (f"{dist_sup:+.2f}%   ", "white"),
            ("a Inf: ", "white"), (f"{dist_inf:+.2f}%\n", "white"),
            ("CVD: ", "white"), (f"{cvd_bar} ", "bold"), (f"{cvd:+,.0f} ", cvd_color), (f"{cvd_label}\n", cvd_color),
            ("BBW: ", "white"), (f"{bbw:.3f} \u2014 ", "white"), (f"{bbw_label}\n", bbw_color),
            ("R\u00e9gimen: ", "white"), (f"{regimen}", "bold"),
        )
        return Panel(texto, title="MACRO H1", border_style=C, padding=(0, 1))

    def render_regimen_m15(self, data: dict) -> Panel:
        bb_sup = data.get("bb_sup", 0)
        bb_media = data.get("bb_media", 0)
        bb_inf = data.get("bb_inf", 0)
        adx = data.get("adx", 0)
        bbw = data.get("bbw", 0)
        cvd = data.get("cvd_medio", 0)
        clasificacion = data.get("clasificacion", "\u2014")
        senal_bloqueada = data.get("senal_bloqueada", False)

        _fmt = lambda v: f"${v:,.0f}" if v else "$--"

        adx_filled = min(16, int(adx / 50 * 16))
        adx_bar = "\u2588" * adx_filled + "\u2591" * (16 - adx_filled)
        adx_label = "SIN TENDENCIA" if adx < 20 else ("TEND. D\u00c9BIL" if adx < 25 else "TEND. FUERTE")
        adx_color = Y if adx < 20 else (C if adx < 25 else G)

        bbw_filled = min(12, int(bbw / 0.05 * 12))
        bbw_bar = "\u2588" * bbw_filled + "\u2591" * (12 - bbw_filled)
        bbw_color = G if bbw < 0.025 else (Y if bbw < 0.035 else R)
        bbw_label = "RANGO" if bbw < 0.025 else ("TRANSICI\u00d3N" if bbw < 0.035 else "TENDENCIA")

        cvd_abs = abs(cvd) if cvd else 0
        cvd_bar = self._barra(cvd_abs, 10, 2000)
        cvd_color = G if cvd >= 0 else R
        cvd_label = "COMPRADORES" if cvd >= 0 else "VENDEDORES"

        if "RANGO" in clasificacion.upper():
            reg_icon = "\U0001f7e2"
            reg_color = G
        elif "TRANSICI" in clasificacion.upper():
            reg_icon = "\U0001f7e1"
            reg_color = Y
        else:
            reg_icon = "\U0001f534"
            reg_color = R

        bloqueo = " [BLOQUEADA \U0001f512]" if senal_bloqueada else ""

        texto = Text.assemble(
            ("[ R\u00c9GIMEN OPERATIVO \u2014 M15 ]\n", f"bold {C}"),
            ("BB 30/3.0: ", "dim white"), ("Sup=", "white"), (_fmt(bb_sup), Y),
            (" | Med=", "white"), (_fmt(bb_media), "white"),
            (" | Inf=", "white"), (_fmt(bb_inf), Y), "\n",
            ("ADX: ", "white"), (f"{adx:.1f} ", "white"),
            (f"{adx_bar} ", "bold"), (f"[{adx:.1f}] ", "white"), (f"{adx_label}\n", adx_color),
            ("BBW: ", "white"), (f"{bbw:.3f} ", "white"),
            (f"{bbw_bar} ", "bold"), (f"[{bbw:.3f}] ", "white"), (f"{bbw_label}\n", bbw_color),
            ("CVD: ", "white"), (f"{cvd_bar} ", "bold"),
            (f"{cvd:+,.0f} ", cvd_color), (f"{cvd_label}\n", cvd_color),
            ("R\u00e9gimen: ", "bold"),
            (f"{reg_icon} ", "bold"), (f"{clasificacion}", reg_color),
            (f"{bloqueo}", f"bold {R}"),
        )
        return Panel(texto, title="R\u00c9GIMEN M15", border_style=C, padding=(0, 1))

    def render_flujo_m1(self, data: dict) -> Panel:
        velas = data.get("ultimas_5_velas", [])
        cvd_corto = data.get("cvd_corto", 0)
        imbalance = data.get("imbalance", 0)
        vol_relativo = data.get("vol_relativo", 0)
        bbw_m1 = data.get("bbw_m1", 0)

        lines = [("[ FLUJO EN TIEMPO REAL \u2014 M1 ]\n", f"bold {C}")]
        lines.append(("\u00daltimas 5 velas:\n", "dim white"))

        if velas:
            max_delta = max((abs(v.get("delta", 0)) for v in velas), default=1)
            for vela in velas:
                t = vela.get("time", "")
                delta = vela.get("delta", 0)
                arrow = "\u25b2" if delta >= 0 else "\u25bc"
                color = G if delta >= 0 else R
                filled = min(14, int(abs(delta) / max_delta * 14))
                bar = "\u2588" * filled + "\u2591" * (14 - filled)
                lines.append((f"{t} ", "dim white"))
                lines.append((f"{arrow} ", color))
                lines.append((f"{delta:+,.0f}  ", color))
                lines.append((f"{bar}\n", "bold"))
        else:
            lines.append(("  Sin datos a\u00fan...\n", "dim italic"))

        cvd_abs = abs(cvd_corto) if cvd_corto else 0
        cvd_bar = self._barra(cvd_abs, 10, 500)
        cvd_color = G if cvd_corto >= 0 else R
        cvd_label = "COMPRADOR" if cvd_corto >= 0 else "VENDEDOR"
        lines.append(("CVD corto: ", "white"))
        lines.append((f"{cvd_corto:+,.0f} ", "white"))
        lines.append((f"{cvd_bar} ", "bold"))
        lines.append((f"{cvd_label}\n", cvd_color))

        if imbalance > 0.2:
            im_color, im_label = G, "\u25b6 PRESI\u00d3N COMPRA"
        elif imbalance < -0.2:
            im_color, im_label = R, "\u25c0 PRESI\u00d3N VENTA"
        else:
            im_color, im_label = Y, "\u27fe NEUTRAL"
        lines.append(("Imbalance: ", "white"))
        lines.append((f"{imbalance:+.2f} ", "white"))
        lines.append((f"{im_label}\n", im_color))

        vol_color = G if vol_relativo > 1.5 else (Y if vol_relativo > 1.0 else "dim white")
        lines.append(("Vol relativo: ", "white"))
        lines.append((f"{vol_relativo:.2f}\n", vol_color))

        bbw_m1_filled = min(12, int(bbw_m1 / 0.005 * 12))
        bbw_m1_bar = "\u2588" * bbw_m1_filled + "\u2591" * (12 - bbw_m1_filled)
        bbw_m1_color = G if bbw_m1 < 0.003 else (Y if bbw_m1 < 0.005 else R)
        lines.append(("BBW M1: ", "white"))
        lines.append((f"{bbw_m1:.4f} ", "white"))
        lines.append((f"{bbw_m1_bar}", bbw_m1_color))

        return Panel(Text.assemble(*lines), title="FLUJO M1", border_style=G, padding=(0, 1))

    def render_razonamiento(self) -> Panel:
        lines = self._get_raz_lines()
        if not lines:
            return Panel(
                "  \u25b6 INICIALIZANDO SENSORES...\n  \u25b6 CONECTANDO BINANCE FEED...\n  \u25b6 CALIBRANDO BOLLINGER 30/3.0...",
                title="RAZONAMIENTO EN VIVO",
                border_style=C,
                padding=(0, 1),
            )
        texto = Text("\n".join(f" \u25b6 {l}" for l in lines), style=f"bold {G}")
        return Panel(texto, title="RAZONAMIENTO EN VIVO", border_style=C, padding=(0, 1))

    def render_senales(self) -> Panel:
        lines = []
        lines.append(("\u2550" * 3 + " \u00daLTIMA SE\u00d1AL " + "\u2550" * 3 + "\n", f"bold {Y}"))
        if self.ultima_senal:
            s = self.ultima_senal
            tipo = s.get("tipo", "\u2014")
            score = s.get("score", 0)
            precio = s.get("precio", 0)
            bb_inf = s.get("bb_inf", 0)
            confluencias = s.get("confluencias", [])
            clasificacion = s.get("clasificacion", "\u2014")

            tipo_color = G if tipo == "LONG" else R
            score_color = G if score >= 70 else (Y if score >= 50 else R)
            score_icon = "\U0001f7e2" if score >= 70 else ("\U0001f7e1" if score >= 50 else "\U0001f534")

            lines.append((f" {tipo} ", f"bold {tipo_color}"))
            lines.append((f"| Score: {score}/100 ", score_color))
            lines.append((f"{score_icon}\n", score_color))
            lines.append(("Precio: ", "white"))
            lines.append((f"${precio:,.0f} ", f"bold {Y}"))
            lines.append(("| BB Inf: ", "white"))
            lines.append((f"${bb_inf:,.0f}\n", f"bold {Y}"))

            if confluencias:
                for c in confluencias:
                    lines.append(("\u2705 ", G))
                    lines.append((f"{c}\n", G))
            lines.append(("Clasificaci\u00f3n: ", "white"))
            lines.append((f"{clasificacion}\n", f"bold {C}"))
        else:
            lines.append(("  Sin se\u00f1ales a\u00fan...\n", "dim italic"))

        lines.append(("\u2500" * 3 + " \u00daltimas se\u00f1ales " + "\u2500" * 3 + "\n", f"bold {Y}"))
        if self.historial_senales:
            for senal in self.historial_senales:
                ts = senal.get("timestamp", "\u2014")
                tipo = senal.get("tipo", "\u2014")
                score = senal.get("score", 0)
                estado = senal.get("estado", "\u2014")
                tipo_color = G if tipo == "LONG" else R
                estado_icon = "\u2705" if "CONFIRMADA" in estado.upper() else "\u23ed"
                lines.append((f"[{ts}] ", "dim white"))
                lines.append((f"{tipo:<5} ", f"bold {tipo_color}"))
                lines.append((f"{score:<3} ", "white"))
                lines.append((f"{estado_icon} {estado}\n", "white"))
        else:
            lines.append(("  Sin historial\n", "dim italic"))

        lines.append(("\u2500" * 3 + " \u00daltimo mensaje " + "\u2500" * 3 + "\n", f"bold {Y}"))
        if self.mensajes_conversacion:
            pregunta, respuesta = self.mensajes_conversacion[-1]
            lines.append((f"> {pregunta}\n", "bold white"))
            lines.append((f"\u258e{respuesta}\n", f"italic {G}"))
        else:
            lines.append(("  Sin conversaci\u00f3n\n", "dim italic"))

        return Panel(Text.assemble(*lines), border_style=Y, padding=(0, 1))

    def render_status_bar(self, data: dict) -> Panel:
        precio = data.get("precio", 0)
        cvd = data.get("cvd_largo", 0)
        adx = data.get("adx", 0)
        regimen = data.get("regimen", "\u2014")
        senales_hoy = data.get("senales_hoy", 0)
        trades_hoy = data.get("trades_hoy", 0)
        pnl_diario = data.get("pnl_diario", 0)
        cooldown = data.get("cooldown", 0)
        rsi = data.get("rsi_7", 50)
        modo = data.get("modo_entrada", "")
        uptime_secs = int(time.time() - self._start_time)
        uptime_str = f"{uptime_secs // 3600:02d}:{(uptime_secs % 3600) // 60:02d}:{uptime_secs % 60:02d}"

        precio_str = f"${precio:,.0f}" if precio else "$--"
        cvd_str = f"{cvd:+,.0f}" if cvd else "--"
        adx_str = f"{adx:.1f}" if adx else "--"
        rsi_color = G if 40 <= rsi <= 60 else (Y if 30 <= rsi <= 70 else R)
        modo_str = f"| Modo: {modo.upper()} " if modo else ""

        texto = Text.assemble(
            ("BTCUSDT ", "bold white"),
            (f"{precio_str} ", Y),
            ("| CVD:", "dim white"), (f"{cvd_str} ", G if (cvd or 0) >= 0 else R),
            ("| ADX:", "dim white"), (f"{adx_str} ", "white"),
            ("| RSI(7):", "dim white"), (f"{rsi:.0f} ", rsi_color),
            modo_str if modo else ("", ""),
            ("| ", "dim white"),
            (f"{regimen.upper()}", G if regimen.upper() == "RANGO" else (Y if regimen.upper() == "TRANSICION" else G)),
            ("| Trades: ", "dim white"), (f"{trades_hoy} ", Y),
            ("| P&L: ", "dim white"), (f"${pnl_diario:+.2f} ", G if pnl_diario >= 0 else R),
            ("| CD: ", "dim white"), (f"{cooldown}s", Y if cooldown > 0 else G),
            ("| Uptime: ", "dim white"), (f"{uptime_str}", G),
        )
        return Panel(texto, border_style="dim white", padding=(0, 0))

    def actualizar(self, macro_data, regimen_data, flujo_data, status_data=None, header_data=None):
        try:
            hd = header_data or {}
            hd["precio"] = hd.get("precio") or macro_data.get("precio")
            hd["regimen"] = hd.get("regimen") or regimen_data.get("clasificacion", "")

            sd = status_data or {}
            sd["precio"] = sd.get("precio") or macro_data.get("precio")
            sd["cvd_largo"] = sd.get("cvd_largo") or macro_data.get("cvd_largo")
            sd["adx"] = sd.get("adx") or regimen_data.get("adx")
            sd["regimen"] = sd.get("regimen") or regimen_data.get("clasificacion", "\u2014")
            sd["rsi_7"] = sd.get("rsi_7", 50)
            sd["modo_entrada"] = sd.get("modo_entrada", "")

            precio_actual = sd.get("precio", 0)
            score_actual = status_data.get("score", 0) if status_data else 0
            signal_actual = self.ultima_senal

            precio_changed = precio_actual != self._last_price
            score_changed = score_actual != self._last_score
            signal_changed = signal_actual != self._last_signal
            time_changed = self._update_counter % 10 == 0

            if not (precio_changed or score_changed or signal_changed or time_changed):
                return

            self._last_price = precio_actual
            self._last_score = score_actual
            self._last_signal = signal_actual
            self._update_counter += 1

            if precio_changed or time_changed:
                self.layout["header"].update(self.render_header(hd))
                self.layout["macro"].update(self.render_macro_h1(macro_data))
                self.layout["status_bar"].update(self.render_status_bar(sd))
            if score_changed or time_changed:
                self.layout["regimen"].update(self.render_regimen_m15(regimen_data))
                self.layout["flujo"].update(self.render_flujo_m1(flujo_data))
            self.layout["razonamiento"].update(self.render_razonamiento())
            if signal_changed:
                self.layout["senales"].update(self.render_senales())
            self.live.update(self.layout)
        except Exception:
            pass

    def mostrar_senal(self, senal: dict):
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
        self.mensajes_conversacion.append((pregunta, respuesta))
        if len(self.mensajes_conversacion) > 5:
            self.mensajes_conversacion.pop(0)
        self.ultimo_mensaje = respuesta

    def esperar_input(self) -> str:
        try:
            return self.console.input(f"[bold {C}]\u26a1 GOAT> [/]")
        except (KeyboardInterrupt, EOFError):
            self.detener()
            return ""

    @staticmethod
    def limpiar_input():
        pass

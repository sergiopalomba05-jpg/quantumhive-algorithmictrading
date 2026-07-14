"""
Estado Global — Estado completo del sistema mantenido por el Cerebro.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Posicion:
    senal_id: int
    side: str
    entry_price: float
    sl: float
    tp: float
    cantidad: float
    timestamp_entrada: str
    pnl_actual: float = 0.0


@dataclass
class Senal:
    id: int
    direccion: str
    score: int
    precio: float
    timestamp: str
    clasificacion: str = ""
    confluencias: list = field(default_factory=list)
    resultado: str = ""


@dataclass
class Alerta:
    nombre: str
    severidad: str
    mensaje: str
    timestamp: str
    resuelta: bool = False


@dataclass
class Evento:
    id: int
    tipo: str
    origen: str
    payload: dict
    timestamp: str


@dataclass
class Decision:
    descripcion: str
    timestamp: str
    tipo: str = ""


@dataclass
class EstadoGlobal:
    # Trading
    btc_precio_actual: float = 0.0
    btc_cambio_24h: float = 0.0
    btc_posicion_activa: Optional[Posicion] = None
    btc_ultima_senal: Optional[Senal] = None
    btc_pnl_hoy: float = 0.0
    btc_trades_hoy: int = 0
    btc_winrate_semana: float = 0.0
    btc_senales_hoy: int = 0

    # Sistema
    goat_btc_activo: bool = False
    goat_btc_ultimo_heartbeat: Optional[str] = None
    agi_ultimo_mensaje: Optional[str] = None
    render_dormido: bool = True

    # Contexto Sergio
    sergio_en_horario_operativo: bool = False
    sergio_ultimo_mensaje: Optional[str] = None
    us30_sesion_activa: bool = False

    # Alertas y anomalías
    alertas_pendientes: List[Alerta] = field(default_factory=list)
    anomalias_detectadas: List[Alerta] = field(default_factory=list)

    # Historial
    ultimas_senales: List[Senal] = field(default_factory=list)
    ultimos_eventos: List[Evento] = field(default_factory=list)


def determinar_horario_operativo() -> bool:
    """10:30-13:00 Argentina (UTC-3)."""
    ahora = datetime.now()
    hora, minuto = ahora.hour, ahora.minute
    return (hora == 10 and minuto >= 30) or (11 <= hora <= 12)

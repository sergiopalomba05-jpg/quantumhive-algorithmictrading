#!/usr/bin/env python3
"""
================================================================================
QUANTUMHIVE — Imperial Trading Floor (Parte 1: Mapa Base)
================================================================================
Motor isométrico estilo Habbo / pixel-art de lujo.
Resolución: 1400x900 | Tiles isométricos 64x32

Partes:
  1. Mapa base — piso mármol negro/dorado, paredes hexagonales, zonas
  2. Abeja robótica central + partículas  ← siguiente
  3. Agentes con sprites únicos            ← siguiente
  4. Pantallas trading con datos animados  ← siguiente
================================================================================
"""
import math, random, sys, os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional

# ─── Pygame init ───
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
pygame.init()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
SCREEN_W, SCREEN_H = 1400, 900
FPS = 60
TILE_W, TILE_H = 64, 32
MAP_COLS, MAP_ROWS = 24, 20
ZOOM_MIN, ZOOM_MAX = 0.6, 2.0

# ═══════════════════════════════════════════════════════════════════════════════
# PALETA DE COLORES — Imperial Black/Gold/White
# ═══════════════════════════════════════════════════════════════════════════════
C_VOID              = (12, 10, 14)
C_MARBLE_BLACK      = (18, 16, 22)
C_MARBLE_DARK       = (28, 24, 32)
C_MARBLE_MID        = (40, 36, 48)
C_MARBLE_LIGHT      = (55, 50, 65)
C_VEIN_GOLD_DARK   = (120, 95, 40)
C_VEIN_GOLD_MID    = (180, 145, 60)
C_VEIN_GOLD_LIGHT  = (230, 195, 90)
C_GOLD_PURE        = (255, 215, 0)
C_GOLD_SOFT        = (210, 175, 70)

C_WALL_WHITE       = (245, 243, 240)
C_WALL_CREAM       = (235, 232, 225)
C_WALL_SHADOW      = (210, 205, 198)
C_HEX_GOLD         = (200, 165, 70)
C_HEX_GOLD_DIM     = (160, 130, 50)

C_CRYSTAL_BASE     = (60, 90, 110)
C_CRYSTAL_GLOW     = (80, 180, 220)
C_CRYSTAL_DARK     = (30, 55, 70)

C_GLASS            = (200, 220, 235)
C_GLASS_ALPHA      = (200, 220, 235, 80)

C_LEATHER_BROWN    = (100, 60, 35)
C_LEATHER_DARK     = (70, 42, 24)
C_WOOD_DARK        = (55, 40, 30)
C_WOOD_MID         = (80, 58, 42)

C_TEXT_DARK        = (30, 28, 35)
C_TEXT_LIGHT       = (240, 238, 235)
C_TEXT_GOLD        = (230, 195, 90)

# ═══════════════════════════════════════════════════════════════════════════════
# TILE TYPES
# ═══════════════════════════════════════════════════════════════════════════════
class TT(Enum):
    VOID        = auto()
    MARBLE_BLACK= auto()   # piso principal — mármol negro con vetas doradas
    MARBLE_GOLD = auto()   # piso CEO / zonas VIP — más dorado
    MARBLE_WHITE= auto()   # piso lounge / pasillos
    HEX_PATTERN = auto()   # pared/piso decorativo hexagonal
    SERVER_GRILL= auto()   # piso zona servers (rejilla metálica)
    ELEVATED    = auto()   # plataforma elevada (cristal/CEO)
    SIGNAGE     = auto()   # área del cartel de pared

# ═══════════════════════════════════════════════════════════════════════════════
# ZONAS DEL MAPA (definen qué tile va en cada celda)
# ═══════════════════════════════════════════════════════════════════════════════
# Layout conceptual (cols x rows = 24x20):
#   [S][S][S][S][S][S][.][.][.][.][.][.][.][C][C][C][C][C][C][.][.][.][.][.]
#   [S][S][S][S][S][S][.][.][.][.][.][.][.][C][C][C][C][C][C][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [T][T][T][T][T][T][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [T][T][T][T][T][T][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [T][T][T][T][T][T][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [T][T][T][T][T][T][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][X][X][X][.][.][.][.][.][.][.][.][.][.][.][.][.]   <- Abeja
#   [.][.][.][.][.][.][.][.][X][X][X][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][X][X][X][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [V][V][V][V][V][V][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [V][V][V][V][V][V][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [V][V][V][V][V][V][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#   [.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.][.]
#
# S = Servers (fondo arriba-izquierda)
# T = Trading Floor (izquierda media)
# C = CEO Suite (derecha arriba)
# V = VIP Lounge (abajo izquierda)
# X = Zona central Abeja

# Máscara de zonas: cada celda tiene una zona string o None
ZONES: List[List[Optional[str]]] = [[None] * MAP_COLS for _ in range(MAP_ROWS)]

def _fill_zone(x0, y0, w, h, name):
    for r in range(y0, min(y0+h, MAP_ROWS)):
        for c in range(x0, min(x0+w, MAP_COLS)):
            ZONES[r][c] = name

# Servidores: fondo arriba-izquierda
_fill_zone(0, 0, 6, 3, "servers")
# Trading Floor: izquierda media
_fill_zone(0, 4, 6, 6, "trading")
# CEO Suite: derecha arriba
_fill_zone(14, 0, 6, 3, "ceo")
# VIP Lounge: abajo izquierda
_fill_zone(0, 16, 6, 3, "vip")
# Zona central (abeja): centro del mapa
_fill_zone(9, 8, 6, 4, "core")
# Pasillos conectores (piso blanco)
_fill_zone(6, 1, 2, 2, "corridor")
_fill_zone(6, 16, 2, 2, "corridor")
_fill_zone(6, 5, 3, 4, "corridor")

# Bordes exteriores: paredes
for c in range(MAP_COLS):
    ZONES[0][c] = "wall_top"
    ZONES[MAP_ROWS-1][c] = "wall_bottom"
for r in range(MAP_ROWS):
    ZONES[r][0] = "wall_left"
    ZONES[r][MAP_COLS-1] = "wall_right"

# ═══════════════════════════════════════════════════════════════════════════════
# TILE RENDERER — Piso de mármol y estructuras
# ═══════════════════════════════════════════════════════════════════════════════
class TileRenderer:
    """Renderiza cada tile individual con detalle premium."""

    @staticmethod
    def iso_polygon(surf, color, cx, cy, zoom):
        """Dibuja un rombo isométrico centrado en (cx,cy)."""
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        pts = [
            (cx, cy - hh),      # top
            (cx + hw, cy),      # right
            (cx, cy + hh),      # bottom
            (cx - hw, cy),      # left
        ]
        pygame.draw.polygon(surf, color, pts)
        # borde sutil
        pygame.draw.polygon(surf, (color[0]+8, color[1]+6, color[2]+10), pts, 1)

    @classmethod
    def draw_marble_black(cls, surf, cx, cy, zoom, seed_val):
        """Mármol negro profundo con vetas doradas irregulares."""
        base = C_MARBLE_BLACK
        cls.iso_polygon(surf, base, cx, cy, zoom)
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        # vetas doradas — 2-3 líneas curvas por tile
        random.seed(seed_val)
        n_veins = random.randint(2, 4)
        for i in range(n_veins):
            y_off = random.randint(-hh//2, hh//2)
            gold = random.choice([C_VEIN_GOLD_DARK, C_VEIN_GOLD_MID, C_VEIN_GOLD_LIGHT])
            width = max(1, int(random.choice([0.5, 1, 1.5]) * zoom))
            # veta en zigzag horizontal
            x_start = -hw + random.randint(0, hw//3)
            x_end = hw - random.randint(0, hw//3)
            seg_len = (x_end - x_start) // 4
            prev = (cx + x_start, cy + y_off)
            for seg in range(4):
                nx = cx + x_start + seg_len * (seg+1)
                ny = cy + y_off + random.randint(-int(3*zoom), int(3*zoom))
                pygame.draw.line(surf, gold, prev, (nx, ny), width)
                prev = (nx, ny)
        random.seed()

    @classmethod
    def draw_marble_gold(cls, surf, cx, cy, zoom, seed_val):
        """Mármol negro con vetas doradas más densas (zona VIP/CEO)."""
        cls.draw_marble_black(surf, cx, cy, zoom, seed_val)
        # brillo adicional dorado
        random.seed(seed_val + 1000)
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        for _ in range(3):
            px = cx + random.randint(-hw+4, hw-4)
            py = cy + random.randint(-hh+2, hh-2)
            r = max(1, int(random.randint(1, 3) * zoom))
            pygame.draw.circle(surf, C_VEIN_GOLD_LIGHT, (px, py), r)
        random.seed()

    @classmethod
    def draw_marble_white(cls, surf, cx, cy, zoom, seed_val):
        """Mármol blanco crema con vetas doradas sutiles (pasillos/lounge)."""
        base = C_WALL_CREAM
        cls.iso_polygon(surf, base, cx, cy, zoom)
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        random.seed(seed_val + 2000)
        # vetas sutiles doradas
        for _ in range(2):
            y_off = random.randint(-hh//2, hh//2)
            gold = C_HEX_GOLD_DIM
            w = max(1, int(0.5 * zoom))
            x0 = -hw + random.randint(5, hw//2)
            x1 = hw - random.randint(5, hw//2)
            pygame.draw.line(surf, gold, (cx+x0, cy+y_off), (cx+x1, cy+y_off+random.randint(-2,2)), w)
        # borde más claro
        pts = [
            (cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy),
        ]
        pygame.draw.polygon(surf, C_WALL_WHITE, pts, max(1, int(zoom)))
        random.seed()

    @classmethod
    def draw_hex_pattern(cls, surf, cx, cy, zoom, seed_val):
        """Patrón hexagonal dorado sobre piso blanco (decoración)."""
        cls.draw_marble_white(surf, cx, cy, zoom, seed_val)
        # dibujar hexágono dorado pequeño en el centro
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        radius = int(min(hw, hh) * 0.35)
        pts = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 2
            px = cx + int(radius * math.cos(angle))
            py = cy + int(radius * 0.5 * math.sin(angle))
            pts.append((px, py))
        pygame.draw.polygon(surf, C_HEX_GOLD, pts, max(1, int(1.5*zoom)))

    @classmethod
    def draw_server_grill(cls, surf, cx, cy, zoom, seed_val):
        """Rejilla metálica oscura con luces verdes/rojas (zona servers)."""
        base = (25, 28, 32)
        cls.iso_polygon(surf, base, cx, cy, zoom)
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        # líneas de rejilla
        step_x = max(4, int(6 * zoom))
        for ox in range(-hw + step_x, hw, step_x):
            pygame.draw.line(surf, (45, 50, 55), (cx+ox, cy-hh//2), (cx+ox, cy+hh//2), max(1, int(0.5*zoom)))
        # luces parpadeantes (seed-based)
        random.seed(seed_val + 3000)
        for _ in range(random.randint(1, 3)):
            lx = cx + random.randint(-hw+4, hw-4)
            ly = cy + random.randint(-hh+2, hh-2)
            color = random.choice([(40, 200, 60), (200, 40, 40), (40, 120, 220)])
            r = max(1, int(random.randint(1, 2) * zoom))
            pygame.draw.circle(surf, color, (lx, ly), r)
            # halo suave
            pygame.draw.circle(surf, (color[0]//2, color[1]//2, color[2]//2), (lx, ly), r+1)
        random.seed()

    @classmethod
    def draw_elevated(cls, surf, cx, cy, zoom, seed_val):
        """Plataforma elevada de cristal (zona central / CEO)."""
        # borde azul cristal
        base = C_CRYSTAL_DARK
        cls.iso_polygon(surf, base, cx, cy, zoom)
        # brillo interior
        hw = int(TILE_W * zoom * 0.5)
        hh = int(TILE_H * zoom * 0.5)
        inner_pts = [
            (cx, cy - hh + int(3*zoom)),
            (cx + hw - int(3*zoom), cy),
            (cx, cy + hh - int(3*zoom)),
            (cx - hw + int(3*zoom), cy),
        ]
        pygame.draw.polygon(surf, C_CRYSTAL_BASE, inner_pts)
        # borde luminoso
        pygame.draw.polygon(surf, C_CRYSTAL_GLOW, [
            (cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy),
        ], max(1, int(1.5*zoom)))

    @classmethod
    def draw_signage_zone(cls, surf, cx, cy, zoom, seed_val):
        """Zona del cartel en pared — fondo blanco con marco dorado."""
        cls.draw_marble_white(surf, cx, cy, zoom, seed_val)

    @classmethod
    def render(cls, surf, tile_type: TT, cx, cy, zoom, seed_val=0):
        if tile_type == TT.VOID:
            return
        elif tile_type == TT.MARBLE_BLACK:
            cls.draw_marble_black(surf, cx, cy, zoom, seed_val)
        elif tile_type == TT.MARBLE_GOLD:
            cls.draw_marble_gold(surf, cx, cy, zoom, seed_val)
        elif tile_type == TT.MARBLE_WHITE:
            cls.draw_marble_white(surf, cx, cy, zoom, seed_val)
        elif tile_type == TT.HEX_PATTERN:
            cls.draw_hex_pattern(surf, cx, cy, zoom, seed_val)
        elif tile_type == TT.SERVER_GRILL:
            cls.draw_server_grill(surf, cx, cy, zoom, seed_val)
        elif tile_type == TT.ELEVATED:
            cls.draw_elevated(surf, cx, cy, zoom, seed_val)
        elif tile_type == TT.SIGNAGE:
            cls.draw_signage_zone(surf, cx, cy, zoom, seed_val)

# ═══════════════════════════════════════════════════════════════════════════════
# ESTRUCTURAS — Muebles, racks, escritorios, paredes
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class Structure:
    x: float   # coord tile (iso)
    y: float
    kind: str
    height: float = 0.0   # elevación en píxeles (para z-sorting)

class StructureRenderer:
    """Dibuja muebles, racks, escritorios, muros."""

    @classmethod
    def to_screen(cls, x, y, offset, zoom):
        """Proyección isométrica con offset y zoom."""
        iso_x = (x - y) * TILE_W * zoom * 0.5
        iso_y = (x + y) * TILE_H * zoom * 0.5
        return iso_x + offset[0], iso_y + offset[1]

    @classmethod
    def draw_desk_glass(cls, surf, x, y, offset, zoom, facing="right"):
        """Escritorio de cristal con marco dorado."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(18 * zoom)  # altura base
        w = int(28 * zoom)
        h = int(14 * zoom)
        d = int(10 * zoom)
        # tapa cristal
        pts = [
            (sx, sy - h),
            (sx + w, sy - h//2),
            (sx, sy),
            (sx - w, sy - h//2),
        ]
        pygame.draw.polygon(surf, (200, 220, 235, 120), pts)
        pygame.draw.polygon(surf, C_VEIN_GOLD_MID, pts, max(1, int(zoom)))
        # patas
        for dx in (-w+4, w-4):
            leg_top = (sx + dx, sy - h//2)
            leg_bot = (sx + dx, sy + int(10*zoom))
            pygame.draw.line(surf, C_VEIN_GOLD_DARK, leg_top, leg_bot, max(1, int(1.5*zoom)))

    @classmethod
    def draw_chair_leather(cls, surf, x, y, offset, zoom):
        """Sillón de cuero oscuro."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(12 * zoom)
        w = int(10 * zoom)
        h = int(12 * zoom)
        # respaldo
        pts_back = [
            (sx - w, sy - h),
            (sx + w, sy - h),
            (sx + w, sy),
            (sx - w, sy),
        ]
        pygame.draw.polygon(surf, C_LEATHER_DARK, pts_back)
        # asiento
        pts_seat = [
            (sx - w, sy),
            (sx + w, sy),
            (sx + w//2, sy + int(4*zoom)),
            (sx - w//2, sy + int(4*zoom)),
        ]
        pygame.draw.polygon(surf, C_LEATHER_BROWN, pts_seat)

    @classmethod
    def draw_server_rack(cls, surf, x, y, offset, zoom, blink_frame=0):
        """Rack de servidores con luces parpadeantes."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(40 * zoom)
        w = int(12 * zoom)
        h = int(40 * zoom)
        # caja metálica
        pts = [
            (sx - w, sy),
            (sx + w, sy),
            (sx + w, sy + h),
            (sx - w, sy + h),
        ]
        pygame.draw.polygon(surf, (35, 38, 42), pts)
        pygame.draw.polygon(surf, (60, 65, 72), pts, max(1, int(zoom)))
        # luces LED
        for i in range(5):
            ly = sy + int((6 + i*7) * zoom)
            # alternancia parpadeante
            on = ((blink_frame // 15) + i) % 3 != 0
            color = (40, 200, 60) if on else (20, 40, 20)
            pygame.draw.circle(surf, color, (sx - w//2, ly), max(1, int(1.5*zoom)))
            pygame.draw.circle(surf, color, (sx + w//2, ly), max(1, int(1.5*zoom)))

    @classmethod
    def draw_ceo_desk(cls, surf, x, y, offset, zoom):
        """Escritorio CEO grande de madera oscura con dorado."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(22 * zoom)
        w = int(50 * zoom)
        h = int(18 * zoom)
        pts = [
            (sx, sy - h),
            (sx + w, sy - h//2),
            (sx, sy),
            (sx - w, sy - h//2),
        ]
        pygame.draw.polygon(surf, C_WOOD_DARK, pts)
        pygame.draw.polygon(surf, C_VEIN_GOLD_MID, pts, max(1, int(1.2*zoom)))
        # patas robustas
        for dx in (-w+6, w-6):
            pygame.draw.line(surf, C_WOOD_MID,
                (sx+dx, sy-h//2), (sx+dx, sy+int(12*zoom)), max(1, int(2*zoom)))

    @classmethod
    def draw_ceo_chair(cls, surf, x, y, offset, zoom):
        """Sillón CEO de cuero con respaldo alto."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(18 * zoom)
        w = int(14 * zoom)
        h = int(22 * zoom)
        # respaldo alto
        pts = [
            (sx - w, sy - h),
            (sx + w, sy - h),
            (sx + w, sy),
            (sx - w, sy),
        ]
        pygame.draw.polygon(surf, C_LEATHER_DARK, pts)
        # bordes dorados
        pygame.draw.polygon(surf, C_VEIN_GOLD_DARK, pts, max(1, int(zoom)))
        # asiento
        pygame.draw.ellipse(surf, C_LEATHER_BROWN,
            (sx - w, sy, w*2, int(6*zoom)))

    @classmethod
    def draw_vip_sofa(cls, surf, x, y, offset, zoom, facing="left"):
        """Sofá lounge de cuero grande."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(14 * zoom)
        w = int(30 * zoom)
        h = int(10 * zoom)
        pts = [
            (sx - w, sy - h),
            (sx + w, sy - h),
            (sx + w, sy),
            (sx - w, sy),
        ]
        pygame.draw.polygon(surf, C_LEATHER_BROWN, pts)
        # brazos
        for dx in (-w+4, w-4):
            pygame.draw.ellipse(surf, C_LEATHER_DARK,
                (sx+dx-int(4*zoom), sy-int(10*zoom), int(8*zoom), int(12*zoom)))

    @classmethod
    def draw_vip_table(cls, surf, x, y, offset, zoom):
        """Mesa de centro lounge — madera con dorado."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(10 * zoom)
        w = int(18 * zoom)
        h = int(6 * zoom)
        pts = [
            (sx, sy - h),
            (sx + w, sy - h//2),
            (sx, sy),
            (sx - w, sy - h//2),
        ]
        pygame.draw.polygon(surf, C_WOOD_MID, pts)
        pygame.draw.polygon(surf, C_VEIN_GOLD_MID, pts, max(1, int(zoom)))

    @classmethod
    def draw_wall_signage(cls, surf, x, y, offset, zoom, text_lines=None):
        """Cartel en pared — QUANTUMHIVE | IMPERIAL TRADING FLOOR..."""
        if text_lines is None:
            text_lines = ["QUANTUMHIVE", "IMPERIAL TRADING FLOOR", "MAX TRADING CAPACITY"]
        sx, sy = cls.to_screen(x, y, offset, zoom)
        sy -= int(35 * zoom)
        w = int(80 * zoom)
        h = int(30 * zoom)
        # placa dorada con marco
        rect = pygame.Rect(sx - w//2, sy - h, w, h)
        pygame.draw.rect(surf, C_VEIN_GOLD_DARK, rect, border_radius=max(2, int(2*zoom)))
        pygame.draw.rect(surf, C_GOLD_SOFT, rect.inflate(-int(3*zoom), -int(3*zoom)), border_radius=max(2, int(2*zoom)))
        # texto (fallback a sysfont si no hay fuente)
        font_size = max(8, int(10 * zoom))
        try:
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.SysFont("consolas", font_size)
        for i, line in enumerate(text_lines):
            color = C_TEXT_DARK if i < 2 else (100, 85, 50)
            ts = font.render(line, True, color)
            tr = ts.get_rect(center=(sx, sy - h//2 + i*font_size - font_size//2))
            surf.blit(ts, tr)

    @classmethod
    def draw_hex_wall_tile(cls, surf, x, y, offset, zoom, is_top=False):
        """Baldosa de pared con patrón hexagonal dorado."""
        sx, sy = cls.to_screen(x, y, offset, zoom)
        if is_top:
            sy -= int(16 * zoom)
        h = int(16 * zoom)
        w = int(TILE_W * zoom * 0.5)
        # pared blanca
        pts = [
            (sx - w, sy - h), (sx + w, sy - h),
            (sx + w, sy), (sx - w, sy),
        ]
        pygame.draw.polygon(surf, C_WALL_WHITE, pts)
        pygame.draw.polygon(surf, C_WALL_SHADOW, pts, max(1, int(zoom)))
        # hexágonos dorados
        hex_r = int(6 * zoom)
        for ox in (-w//2, 0, w//2):
            for oy in (-h//2, 0):
                hpx, hpy = sx + ox, sy + oy - h//2
                hex_pts = []
                for i in range(6):
                    angle = math.pi/3 * i - math.pi/2
                    hx = hpx + int(hex_r * math.cos(angle))
                    hy = hpy + int(hex_r * 0.5 * math.sin(angle))
                    hex_pts.append((hx, hy))
                pygame.draw.polygon(surf, C_HEX_GOLD, hex_pts, max(1, int(0.8*zoom)))

    @classmethod
    def draw(cls, surf, st: Structure, offset, zoom, frame=0):
        if st.kind == "desk_glass":
            cls.draw_desk_glass(surf, st.x, st.y, offset, zoom)
        elif st.kind == "chair_leather":
            cls.draw_chair_leather(surf, st.x, st.y, offset, zoom)
        elif st.kind == "server_rack":
            cls.draw_server_rack(surf, st.x, st.y, offset, zoom, frame)
        elif st.kind == "ceo_desk":
            cls.draw_ceo_desk(surf, st.x, st.y, offset, zoom)
        elif st.kind == "ceo_chair":
            cls.draw_ceo_chair(surf, st.x, st.y, offset, zoom)
        elif st.kind == "vip_sofa":
            cls.draw_vip_sofa(surf, st.x, st.y, offset, zoom)
        elif st.kind == "vip_table":
            cls.draw_vip_table(surf, st.x, st.y, offset, zoom)
        elif st.kind == "signage":
            cls.draw_wall_signage(surf, st.x, st.y, offset, zoom)
        elif st.kind == "hex_wall":
            cls.draw_hex_wall_tile(surf, st.x, st.y, offset, zoom)

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA — Genera la grid de tiles y estructuras
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class Tile:
    col: int
    row: int
    ttype: TT
    elevation: float = 0.0  # 0 = piso normal, 1 = plataforma elevada

class ImperialMap:
    def __init__(self):
        self.tiles: List[Tile] = []
        self.structures: List[Structure] = []
        self._build()
        self._place_structures()

    def _build(self):
        """Construye la grid de tiles según zonas."""
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                zone = ZONES[r][c]
                if zone is None:
                    ttype = TT.MARBLE_BLACK
                    elev = 0.0
                elif zone == "servers":
                    ttype = TT.SERVER_GRILL
                    elev = 0.0
                elif zone == "trading":
                    ttype = TT.MARBLE_BLACK
                    elev = 0.0
                elif zone == "ceo":
                    ttype = TT.MARBLE_GOLD
                    elev = 0.3  # plataforma elevada
                elif zone == "vip":
                    ttype = TT.MARBLE_WHITE
                    elev = 0.0
                elif zone == "core":
                    ttype = TT.ELEVATED
                    elev = 0.5  # más elevada
                elif zone == "corridor":
                    ttype = TT.MARBLE_WHITE
                    elev = 0.0
                elif zone in ("wall_top", "wall_bottom", "wall_left", "wall_right"):
                    ttype = TT.SIGNAGE if zone == "wall_top" and 6 < c < 18 else TT.HEX_PATTERN
                    elev = 0.0
                else:
                    ttype = TT.MARBLE_BLACK
                    elev = 0.0
                self.tiles.append(Tile(c, r, ttype, elev))

    def _place_structures(self):
        """Coloca muebles y estructuras en cada zona."""
        # --- SERVERS ---
        for r in range(1, 3):
            for c in range(1, 5, 2):
                self.structures.append(Structure(c, r, "server_rack", height=40))

        # --- TRADING FLOOR ---
        # Escritorios de cristal en formación 2x3
        desk_positions = [
            (1, 5), (3, 5), (1, 7), (3, 7), (1, 9), (3, 9),
        ]
        for c, r in desk_positions:
            self.structures.append(Structure(c, r, "desk_glass", height=18))
            # silla frente a cada escritorio
            self.structures.append(Structure(c+0.3, r+0.3, "chair_leather", height=12))

        # --- CEO SUITE ---
        self.structures.append(Structure(16, 1, "ceo_desk", height=22))
        self.structures.append(Structure(16, 1.8, "ceo_chair", height=18))
        # monitor grande (placeholder — reemplazar en parte 4)
        self.structures.append(Structure(15, 1, "desk_glass", height=18))
        self.structures.append(Structure(17, 1, "desk_glass", height=18))

        # --- VIP LOUNGE ---
        self.structures.append(Structure(2, 17, "vip_sofa", height=14))
        self.structures.append(Structure(4, 17, "vip_table", height=10))

        # --- CARTEL ---
        self.structures.append(Structure(12, 0.5, "signage", height=35))

        # --- PAREDES HEXAGONALES ---
        # Fondo superior
        for c in range(1, MAP_COLS-1):
            if ZONES[0][c] in ("wall_top", None):
                self.structures.append(Structure(c, -0.4, "hex_wall", height=16))

    def get_tile(self, c, r):
        for t in self.tiles:
            if t.col == c and t.row == r:
                return t
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# MOTOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
class ImperialEngine:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("QUANTUMHIVE — Imperial Trading Floor [Parte 1/4]")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 16)

        self.map = ImperialMap()
        self.offset = [SCREEN_W // 2, SCREEN_H // 3]
        self.zoom = 1.0
        self.dragging = False
        self.drag_start = (0, 0)
        self.frame = 0

    def iso_to_screen(self, c, r, elevation=0.0):
        """Convierte coordenadas de tile a pantalla."""
        iso_x = (c - r) * TILE_W * self.zoom * 0.5
        iso_y = (c + r) * TILE_H * self.zoom * 0.5
        iso_y -= int(elevation * 30 * self.zoom)
        return self.offset[0] + iso_x, self.offset[1] + iso_y

    def draw(self):
        self.screen.fill(C_VOID)

        # 1. Tiles (ordenados de arriba-izquierda a abajo-derecha)
        sorted_tiles = sorted(self.map.tiles, key=lambda t: (t.row + t.col))
        for tile in sorted_tiles:
            sx, sy = self.iso_to_screen(tile.col, tile.row, tile.elevation)
            seed = tile.col * 1000 + tile.row * 17
            TileRenderer.render(self.screen, tile.ttype, int(sx), int(sy), self.zoom, seed)

        # 2. Estructuras (z-sort por posición isométrica Y)
        sorted_structs = sorted(self.map.structures, key=lambda s: (s.y + s.x))
        for st in sorted_structs:
            sx, sy = self.iso_to_screen(st.x, st.y, st.height / 40.0)
            StructureRenderer.draw(self.screen, st, self.offset, self.zoom, self.frame)

        # 3. UI Overlay
        self._draw_ui()

        pygame.display.flip()

    def _draw_ui(self):
        # Título
        title = self.font.render("QUANTUMHIVE — Imperial Trading Floor", True, C_TEXT_GOLD)
        tr = title.get_rect(topleft=(14, 10))
        # fondo oscuro semitransparente para legibilidad
        bg = pygame.Surface((tr.width + 16, tr.height + 8), pygame.SRCALPHA)
        bg.fill((12, 10, 14, 180))
        self.screen.blit(bg, (tr.x - 8, tr.y - 4))
        self.screen.blit(title, tr)

        # Hints
        hints = [
            "Controls: Drag = pan | Scroll = zoom | R = reset | ESC = exit",
            "Parte 1/4: Mapa base — piso, paredes, zonas, muebles",
        ]
        for i, h in enumerate(hints):
            s = self.font_small.render(h, True, C_TEXT_LIGHT)
            self.screen.blit(s, (14, 36 + i * 16))

        # Zoom info
        zs = self.font_small.render(f"Zoom: {self.zoom:.1f}x", True, C_TEXT_LIGHT)
        self.screen.blit(zs, (SCREEN_W - 120, 10))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.frame += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.zoom = 1.0
                        self.offset = [SCREEN_W // 2, SCREEN_H // 3]
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.dragging = True
                        self.drag_start = event.pos
                    elif event.button == 4:  # scroll up
                        self.zoom = min(ZOOM_MAX, self.zoom + 0.1)
                    elif event.button == 5:  # scroll down
                        self.zoom = max(ZOOM_MIN, self.zoom - 0.1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    dx = event.pos[0] - self.drag_start[0]
                    dy = event.pos[1] - self.drag_start[1]
                    self.offset[0] += dx
                    self.offset[1] += dy
                    self.drag_start = event.pos

            self.draw()

        pygame.quit()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  QUANTUMHIVE — Imperial Trading Floor")
    print("  Parte 1/4: Mapa base (piso, paredes, zonas, muebles)")
    print("=" * 60)
    print("  Controls: Drag = pan  |  Scroll = zoom  |  R = reset  |  ESC = exit")
    print()
    engine = ImperialEngine()
    engine.run()

if __name__ == "__main__":
    main()

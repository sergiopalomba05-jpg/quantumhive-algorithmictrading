#!/usr/bin/env python3
"""
QuantumHive Town — Generador completo de assets cyberpunk
Genera: tileset, sprites de agentes, mapa JS, spritesheet data TS
"""
from PIL import Image, ImageDraw, ImageFont
import os, json, math

OUT = os.path.dirname(os.path.abspath(__file__))
T = 32  # tile size

# === PALETTA CYBERPUNK (MUCHO MAS CLARA) ===
C = {
    # Backgrounds
    "bg":        (15, 15, 35),
    # Floors - MUCHO mas claros
    "floor1":    (35, 40, 70),      # suelo base
    "floor2":    (50, 55, 90),      # lineas de grid
    "floor3":    (65, 70, 110),     # centro de celda
    "floor_glow":(80, 85, 130),     # glow sutil
    # Walls
    "wall_d":    (25, 25, 60),      # pared oscura
    "wall_m":    (45, 45, 85),      # pared media
    "wall_l":    (65, 65, 105),     # pared clara
    "wall_top":  (75, 75, 115),     # tope de pared
    # Neon colors - BRILLANTES
    "neon":      (0, 220, 255),     # azul cyan
    "neon_d":    (0, 160, 220),     # azul medio
    "neon_g":    (0, 100, 180),     # azul oscuro glow
    "gold":      (255, 220, 30),    # dorado brillante
    "gold_d":    (200, 160, 20),    # dorado oscuro
    "green":     (50, 255, 100),    # verde brillante
    "green_d":   (30, 180, 60),     # verde oscuro
    "red":       (255, 50, 50),     # rojo alerta
    "red_d":     (180, 30, 30),     # rojo oscuro
    "blue":      (30, 150, 255),    # azul
    "purple":    (180, 100, 255),   # violeta
    "cyan":      (30, 255, 240),    # cian
    "orange":    (255, 160, 30),    # naranja
    # Server/tech
    "srv1":      (50, 50, 95),
    "srv2":      (65, 65, 110),
    "srv_led":   (100, 255, 120),
    "screen_bg": (15, 35, 70),
    "screen_l1": (0, 200, 255),
    "screen_l2": (0, 255, 120),
    "screen_l3": (255, 200, 0),
    # Furniture
    "desk":      (65, 55, 90),
    "desk_t":    (80, 70, 105),
    "desk_edge": (95, 85, 120),
    "chair":     (55, 45, 80),
    "chair_t":   (70, 60, 95),
    # Cables
    "cable1":    (0, 180, 220),
    "cable2":    (0, 140, 180),
    "cable3":    (80, 80, 140),
    # Misc
    "white":     (230, 230, 240),
    "black":     (5, 5, 15),
    "shadow":    (8, 8, 20),
    "plant1":    (20, 160, 60),
    "plant2":    (40, 200, 80),
    "plant3":    (30, 130, 50),
    "pot":       (120, 90, 60),
    "pot_t":     (140, 110, 75),
    # Department wall colors (brighter!)
    "dept_blue": (0, 180, 255),
    "dept_green":(50, 255, 100),
    "dept_gold": (255, 210, 40),
    "dept_cyan": (30, 240, 230),
    "dept_purple":(160, 90, 255),
    "dept_red":  (255, 60, 80),
}

def r(d, x1,y1,x2,y2,c): d.rectangle([x1,y1,x2,y2], fill=c)
def p(d, x,y,c): d.point((x,y), fill=c)
def l(d, x1,y1,x2,y2,c): d.line([x1,y1,x2,y2], fill=c, width=1)

# ================================================================
# TILESET: 16 columnas x 4 filas = 64 tiles de 32x32
# Fila 0 (y=0):  suelos y paredes basicas
# Fila 1 (y=32): objetos (servidor, pantalla, escritorio, silla, etc)
# Fila 2 (y=64): paredes de departamento (colores neon)
# Fila 3 (y=96): decoracion y mobiliario especial
# ================================================================

def tile_floor(d, ox, oy):
    """Suelo base con grid tech - CLARO y visible"""
    r(d, ox,oy,ox+31,oy+31, C["floor1"])
    # Grid lines
    for i in range(0,32,8):
        l(d, ox,oy+i,ox+31,oy+i, C["floor2"])
        l(d, ox+i,oy,ox+i,oy+31, C["floor2"])
    # Center glow point
    r(d, ox+15,oy+15,ox+16,oy+16, C["floor3"])
    # Corner highlights
    p(d, ox,oy, C["floor_glow"])
    p(d, ox+31,oy, C["floor_glow"])
    p(d, ox,oy+31, C["floor_glow"])
    p(d, ox+31,oy+31, C["floor_glow"])

def tile_floor_neon(d, ox, oy):
    """Suelo con glow neon central"""
    tile_floor(d, ox, oy)
    # Central neon glow
    r(d, ox+13,oy+13,ox+18,oy+18, C["neon"])
    r(d, ox+14,oy+14,ox+17,oy+17, C["white"])
    # Glow rays
    for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        p(d, ox+15+dx*2, oy+15+dy*2, C["neon_d"])
    for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]:
        p(d, ox+15+dx, oy+15+dy, C["neon_g"])

def tile_floor_gold(d, ox, oy):
    """Suelo con glow dorado"""
    tile_floor(d, ox, oy)
    r(d, ox+13,oy+13,ox+18,oy+18, C["gold"])
    r(d, ox+14,oy+14,ox+17,oy+17, C["white"])

def tile_wall(d, ox, oy):
    """Pared basica con strip neon"""
    r(d, ox,oy,ox+31,oy+31, C["wall_d"])
    # Top highlight
    r(d, ox,oy,ox+31,oy+3, C["wall_m"])
    r(d, ox,oy+1,ox+31,oy+1, C["wall_top"])
    # Neon strip
    r(d, ox,oy+2,ox+31,oy+2, C["neon"])
    # Bottom shadow
    r(d, ox,oy+28,ox+31,oy+31, C["shadow"])
    # Side highlights
    r(d, ox,oy,ox+1,oy+31, C["wall_m"])
    r(d, ox+30,oy,ox+31,oy+31, C["wall_m"])

def tile_wall_gold(d, ox, oy):
    """Pared con panel dorado"""
    tile_wall(d, ox, oy)
    # Gold panel
    r(d, ox+10,oy+7,ox+21,oy+24, C["wall_m"])
    r(d, ox+11,oy+8,ox+20,oy+23, C["gold_d"])
    r(d, ox+12,oy+9,ox+19,oy+22, C["gold"])
    # Shine
    p(d, ox+13,oy+10, C["white"])

def tile_wall_window(d, ox, oy):
    """Pared con ventana/pantalla"""
    tile_wall(d, ox, oy)
    # Window frame
    r(d, ox+6,oy+6,ox+25,oy+22, C["wall_l"])
    # Window glass
    r(d, ox+7,oy+7,ox+24,oy+21, C["screen_bg"])
    # Window lines
    for i in range(4):
        y = oy+9+i*3
        w = 10 + (i%3)*3
        r(d, ox+9,y,ox+9+w,y+1, C["screen_l1"])

# === Fila 1: OBJETOS ===

def tile_server(d, ox, oy):
    """Rack de servidores con LEDs"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Rack body
    r(d, ox+4,oy+1,ox+27,oy+30, C["srv1"])
    r(d, ox+5,oy+2,ox+26,oy+29, C["srv2"])
    # Server bays
    for i in range(5):
        y = oy+3+i*5
        r(d, ox+6,y,ox+25,y+4, C["srv1"])
        r(d, ox+7,y+1,ox+24,y+3, C["srv2"])
        # LEDs
        leds = [C["green"], C["blue"], C["red"], C["cyan"], C["orange"]]
        p(d, ox+24,y+2, leds[i])
        p(d, ox+22,y+2, C["srv_led"])
        # Vent lines
        l(d, ox+9,y+2,ox+14,y+2, C["wall_l"])
    # Side rails
    r(d, ox+4,oy+1,ox+4,oy+30, C["wall_l"])
    r(d, ox+27,oy+1,ox+27,oy+30, C["wall_l"])

def tile_screen(d, ox, oy):
    """Pantalla con codigo de barras"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Monitor frame
    r(d, ox+2,oy+3,ox+29,oy+24, C["wall_l"])
    # Screen
    r(d, ox+3,oy+4,ox+28,oy+23, C["screen_bg"])
    # Code lines
    lines = [C["screen_l1"], C["screen_l2"], C["screen_l3"], C["screen_l1"]]
    for i, col in enumerate(lines):
        y = oy+6+i*4
        w = 8 + (i%3)*5
        r(d, ox+5,y,ox+5+w,y+1, col)
        r(d, ox+5+w+2,y,ox+5+w+6,y+1, C["white"])
    # Stand
    r(d, ox+13,oy+25,ox+18,oy+27, C["wall_l"])
    r(d, ox+10,oy+28,ox+21,oy+29, C["wall_m"])

def tile_screen_graph(d, ox, oy):
    """Pantalla con grafico de barras"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+2,oy+3,ox+29,oy+24, C["wall_l"])
    r(d, ox+3,oy+4,ox+28,oy+23, C["screen_bg"])
    # Bar chart
    heights = [6, 10, 8, 14, 11, 7, 12]
    colors = [C["green"], C["neon"], C["gold"], C["red"], C["cyan"], C["purple"], C["blue"]]
    for i, (h, col) in enumerate(zip(heights, colors)):
        x = ox+5+i*3
        y = oy+22-h
        r(d, x,y,x+2,oy+22, col)
    # Stand
    r(d, ox+13,oy+25,ox+18,oy+27, C["wall_l"])
    r(d, ox+10,oy+28,ox+21,oy+29, C["wall_m"])

def tile_desk(d, ox, oy):
    """Escritorio con monitor"""
    # Desk surface
    r(d, ox+2,oy+16,ox+29,oy+20, C["desk_t"])
    r(d, ox+3,oy+17,ox+28,oy+19, C["desk_edge"])
    # Desk legs
    r(d, ox+3,oy+21,ox+5,oy+30, C["desk"])
    r(d, ox+26,oy+21,ox+28,oy+30, C["desk"])
    # Monitor on desk
    r(d, ox+10,oy+6,ox+22,oy+15, C["wall_l"])
    r(d, ox+11,oy+7,ox+21,oy+14, C["screen_bg"])
    # Monitor stand
    r(d, ox+14,oy+15,ox+18,oy+16, C["wall_l"])
    # Code on screen
    l(d, ox+13,oy+9,ox+17,oy+9, C["screen_l1"])
    l(d, ox+13,oy+11,ox+19,oy+11, C["screen_l2"])
    l(d, ox+13,oy+13,ox+15,oy+13, C["screen_l3"])

def tile_chair(d, ox, oy):
    """Silla de oficina"""
    # Seat
    r(d, ox+8,oy+14,ox+23,oy+18, C["chair_t"])
    r(d, ox+9,oy+15,ox+22,oy+17, C["chair"])
    # Backrest
    r(d, ox+9,oy+4,ox+22,oy+13, C["chair_t"])
    r(d, ox+10,oy+5,ox+21,oy+12, C["chair"])
    # Legs
    r(d, ox+10,oy+19,ox+12,oy+28, C["wall_m"])
    r(d, ox+19,oy+19,ox+21,oy+28, C["wall_m"])
    # Wheels
    p(d, ox+9,oy+29, C["wall_l"])
    p(d, ox+22,oy+29, C["wall_l"])

def tile_cables(d, ox, oy):
    """Bundle de cables"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Cable bundle
    for i, col in enumerate([C["cable1"], C["cable2"], C["cable3"]]):
        x = ox+8+i*5
        l(d, x,oy+2,x,oy+29, col)
        # Connectors
        r(d, x-1,oy+14,x+1,oy+16, C["wall_l"])

def tile_plant(d, ox, oy):
    """Planta decorativa"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Pot
    r(d, ox+10,oy+20,ox+21,oy+28, C["pot"])
    r(d, ox+11,oy+21,ox+20,oy+27, C["pot_t"])
    # Soil
    r(d, ox+11,oy+20,ox+20,oy+21, C["desk"])
    # Leaves
    r(d, ox+14,oy+8,ox+17,oy+19, C["plant3"])
    # Leaf clusters
    for dx,dy in [(-3,-4),(3,-4),(-2,-6),(2,-6),(0,-7)]:
        cx, cy = ox+15+dx, oy+12+dy
        r(d, cx,cy,cx+2,cy+2, C["plant1"])
        p(d, cx+1,cy-1, C["plant2"])

def tile_quantum(d, ox, oy):
    """Quantum core hexagonal central"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Outer glow
    for dx in range(-2,3):
        for dy in range(-2,3):
            if abs(dx)+abs(dy) <= 3:
                p(d, ox+15+dx, oy+15+dy, C["neon_g"])
    # Hexagon body
    hex_pts = [(15,2),(22,6),(22,12),(15,16),(8,12),(8,6)]
    hex_pts = [(ox+x,oy+y) for x,y in hex_pts]
    d.polygon(hex_pts, fill=C["neon_d"])
    # Inner hex
    hex_in = [(15,4),(20,7),(20,11),(15,14),(10,11),(10,7)]
    hex_in = [(ox+x,oy+y) for x,y in hex_in]
    d.polygon(hex_in, fill=C["neon"])
    # Center
    r(d, ox+13,oy+7,ox+18,oy+10, C["white"])

def tile_portal(d, ox, oy):
    """Portal / Energy core"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Outer rings
    for r_size in [14, 11, 8]:
        for angle in range(0, 360, 15):
            x = ox+15 + int(r_size * math.cos(math.radians(angle)))
            y = oy+15 + int(r_size * math.sin(math.radians(angle)))
            if 0 <= x-ox <= 31 and 0 <= y-oy <= 31:
                p(d, x, y, C["gold"])
    # Inner glow
    r(d, ox+12,oy+12,ox+19,oy+19, C["gold_d"])
    r(d, ox+13,oy+13,ox+18,oy+18, C["gold"])
    r(d, ox+14,oy+14,ox+17,oy+17, C["white"])

# === Fila 2: PAREDES DE DEPARTAMENTO (con color neon) ===

def _dept_wall(d, ox, oy, color, label_char):
    """Pared de departamento con color y label"""
    r(d, ox,oy,ox+31,oy+31, C["wall_d"])
    # Colored top strip
    r(d, ox,oy,ox+31,oy+5, C["wall_m"])
    r(d, ox,oy+1,ox+31,oy+1, color)
    r(d, ox,oy+2,ox+31,oy+2, color)
    # Bottom shadow
    r(d, ox,oy+28,ox+31,oy+31, C["shadow"])
    # Side highlights
    r(d, ox,oy,ox+1,oy+31, C["wall_m"])
    r(d, ox+30,oy,ox+31,oy+31, C["wall_m"])
    # Label area
    r(d, ox+6,oy+10,ox+25,oy+22, C["wall_m"])
    r(d, ox+7,oy+11,ox+24,oy+21, color)
    # Letter/number indicator
    r(d, ox+12,oy+13,ox+19,oy+19, C["white"])

def tile_dept_orchestration(d, ox, oy):
    """Agent Orchestration Center - AZUL"""
    _dept_wall(d, ox, oy, C["dept_blue"], "AOC")
    # Blue accent dots
    p(d, ox+8, oy+24, C["dept_blue"])
    p(d, ox+23, oy+24, C["dept_blue"])

def tile_dept_factory(d, ox, oy):
    """App Factory - VERDE"""
    _dept_wall(d, ox, oy, C["dept_green"], "FAC")
    p(d, ox+8, oy+24, C["dept_green"])
    p(d, ox+23, oy+24, C["dept_green"])

def tile_dept_data(d, ox, oy):
    """Data & Analytics Lab - DORADO"""
    _dept_wall(d, ox, oy, C["dept_gold"], "DAL")
    p(d, ox+8, oy+24, C["dept_gold"])
    p(d, ox+23, oy+24, C["dept_gold"])

def tile_dept_comm(d, ox, oy):
    """Communication Hub - CYAN"""
    _dept_wall(d, ox, oy, C["dept_cyan"], "CHB")
    p(d, ox+8, oy+24, C["dept_cyan"])
    p(d, ox+23, oy+24, C["dept_cyan"])

def tile_dept_server(d, ox, oy):
    """Server Farm - AZUL OSCURO"""
    _dept_wall(d, ox, oy, C["blue"], "SRV")
    p(d, ox+8, oy+24, C["blue"])
    p(d, ox+23, oy+24, C["blue"])

def tile_dept_learning(d, ox, oy):
    """Learning & Upgrade Hub - PURPURA"""
    _dept_wall(d, ox, oy, C["dept_purple"], "LUH")
    p(d, ox+8, oy+24, C["dept_purple"])
    p(d, ox+23, oy+24, C["dept_purple"])

def tile_dept_portal(d, ox, oy):
    """Portal / Energy Core - DORADO"""
    _dept_wall(d, ox, oy, C["dept_gold"], "PEC")
    p(d, ox+8, oy+24, C["dept_gold"])
    p(d, ox+23, oy+24, C["dept_gold"])

def tile_dept_meeting(d, ox, oy):
    """Meeting & Strategy Room - ROJO"""
    _dept_wall(d, ox, oy, C["dept_red"], "MSR")
    p(d, ox+8, oy+24, C["dept_red"])
    p(d, ox+23, oy+24, C["dept_red"])

# === Fila 3: DECORACION ESPECIAL ===

def tile_floor_hallway(d, ox, oy):
    """Pasillo con guias neon"""
    tile_floor(d, ox, oy)
    # Guide lines
    l(d, ox+2,oy+15,ox+29,oy+15, C["neon_g"])
    l(d, ox+2,oy+16,ox+29,oy+16, C["neon_g"])
    # Arrow markers
    r(d, ox+14,oy+12,ox+17,oy+14, C["neon"])
    r(d, ox+15,oy+10,ox+16,oy+12, C["neon"])

def tile_floor_carpet(d, ox, oy):
    """Alfombra de meeting room"""
    r(d, ox,oy,ox+31,oy+31, C["floor1"])
    # Border
    r(d, ox,oy,ox+31,oy+1, C["dept_red"])
    r(d, ox,oy+30,ox+31,oy+31, C["dept_red"])
    r(d, ox,oy,ox+1,oy+31, C["dept_red"])
    r(d, ox+30,oy,ox+31,oy+31, C["dept_red"])
    # Center pattern
    r(d, ox+12,oy+12,ox+19,oy+19, C["dept_gold"])

def tile_floor_lab(d, ox, oy):
    """Suelo de laboratorio con grid especial"""
    tile_floor(d, ox, oy)
    # Lab grid accent
    r(d, ox+8,oy,ox+8,oy+31, C["neon_g"])
    r(d, ox+24,oy,ox+24,oy+31, C["neon_g"])
    r(d, ox,oy+8,ox+31,oy+8, C["neon_g"])
    r(d, ox,oy+24,ox+31,oy+24, C["neon_g"])

def tile_floor_energy(d, ox, oy):
    """Suelo con patrones de energia"""
    tile_floor(d, ox, oy)
    # Energy rings
    for r_size in [6, 10, 14]:
        angle_step = max(10, r_size)
        for angle in range(0, 360, angle_step):
            x = ox+15 + int(r_size * math.cos(math.radians(angle)))
            y = oy+15 + int(r_size * math.sin(math.radians(angle)))
            if 0 <= x-ox <= 31 and 0 <= y-oy <= 31:
                p(d, x, y, C["gold_d"])

def tile_whiteboard(d, ox, oy):
    """Pizarra blanca"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Board frame
    r(d, ox+3,oy+3,ox+28,oy+24, C["wall_l"])
    # Board surface
    r(d, ox+4,oy+4,ox+27,oy+23, C["white"])
    # Writing
    l(d, ox+6,oy+8,ox+15,oy+8, C["red"])
    l(d, ox+6,oy+12,ox+20,oy+12, C["blue"])
    l(d, ox+6,oy+16,ox+18,oy+16, C["green"])
    # Tray
    r(d, ox+10,oy+25,ox+21,oy+26, C["wall_m"])
    # Markers
    r(d, ox+12,oy+25,ox+13,oy+26, C["red"])
    r(d, ox+15,oy+25,ox+16,oy+26, C["blue"])
    r(d, ox+18,oy+25,ox+19,oy+26, C["green"])

def tile_coffee(d, ox, oy):
    """Estacion de cafe"""
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    # Machine
    r(d, ox+8,oy+4,ox+23,oy+20, C["srv1"])
    r(d, ox+9,oy+5,ox+22,oy+19, C["srv2"])
    # Dispenser
    r(d, ox+12,oy+10,ox+19,oy+17, C["wall_d"])
    # Cup
    r(d, ox+13,oy+22,ox+18,oy+28, C["white"])
    r(d, ox+14,oy+23,ox+17,oy+27, C["desk"])
    # Steam
    p(d, ox+14,oy+21, C["white"])
    p(d, ox+16,oy+20, C["white"])

# ================================================================
# BUILD TILESET
# ================================================================

def build_tileset():
    img = Image.new("RGBA", (16*T, 4*T), (0,0,0,0))
    d = ImageDraw.Draw(img)

    # === Fila 0: Suelos y paredes ===
    y0 = 0
    # Col 0: Suelo base
    tile_floor(d, 0*T, y0)
    # Col 1: Suelo neon
    tile_floor_neon(d, 1*T, y0)
    # Col 2: Pared basica
    tile_wall(d, 2*T, y0)
    # Col 3: Pared con panel dorado
    tile_wall_gold(d, 3*T, y0)
    # Col 4: Pared con ventana
    tile_wall_window(d, 4*T, y0)
    # Col 5-15: Mas suelos y paredes variadas
    tile_floor_gold(d, 5*T, y0)
    tile_floor(d, 6*T, y0)
    tile_floor_neon(d, 7*T, y0)
    tile_wall(d, 8*T, y0)
    tile_wall_gold(d, 9*T, y0)
    tile_wall_window(d, 10*T, y0)
    tile_floor(d, 11*T, y0)
    tile_floor_neon(d, 12*T, y0)
    tile_wall(d, 13*T, y0)
    tile_wall_gold(d, 14*T, y0)
    tile_wall(d, 15*T, y0)

    # === Fila 1: Objetos ===
    y1 = T
    tile_server(d, 0*T, y1)
    tile_screen(d, 1*T, y1)
    tile_screen_graph(d, 2*T, y1)
    tile_desk(d, 3*T, y1)
    tile_chair(d, 4*T, y1)
    tile_cables(d, 5*T, y1)
    tile_plant(d, 6*T, y1)
    tile_quantum(d, 7*T, y1)
    tile_portal(d, 8*T, y1)
    tile_server(d, 9*T, y1)
    tile_screen(d, 10*T, y1)
    tile_screen_graph(d, 11*T, y1)
    tile_desk(d, 12*T, y1)
    tile_chair(d, 13*T, y1)
    tile_plant(d, 14*T, y1)
    tile_quantum(d, 15*T, y1)

    # === Fila 2: Paredes de departamento ===
    y2 = 2*T
    tile_dept_orchestration(d, 0*T, y2)  # Agent Orchestration Center
    tile_dept_factory(d, 1*T, y2)        # App Factory
    tile_dept_data(d, 2*T, y2)           # Data & Analytics Lab
    tile_dept_comm(d, 3*T, y2)           # Communication Hub
    tile_dept_server(d, 4*T, y2)         # Server Farm
    tile_dept_learning(d, 5*T, y2)       # Learning & Upgrade Hub
    tile_dept_portal(d, 6*T, y2)         # Portal / Energy Core
    tile_dept_meeting(d, 7*T, y2)        # Meeting & Strategy Room
    # Duplicates for variety
    tile_dept_orchestration(d, 8*T, y2)
    tile_dept_factory(d, 9*T, y2)
    tile_dept_data(d, 10*T, y2)
    tile_dept_comm(d, 11*T, y2)
    tile_dept_server(d, 12*T, y2)
    tile_dept_learning(d, 13*T, y2)
    tile_dept_portal(d, 14*T, y2)
    tile_dept_meeting(d, 15*T, y2)

    # === Fila 3: Decoracion especial ===
    y3 = 3*T
    tile_floor_hallway(d, 0*T, y3)
    tile_floor_carpet(d, 1*T, y3)
    tile_floor_lab(d, 2*T, y3)
    tile_floor_energy(d, 3*T, y3)
    tile_whiteboard(d, 4*T, y3)
    tile_coffee(d, 5*T, y3)
    tile_floor(d, 6*T, y3)
    tile_floor_neon(d, 7*T, y3)
    tile_floor_hallway(d, 8*T, y3)
    tile_floor_carpet(d, 9*T, y3)
    tile_floor_lab(d, 10*T, y3)
    tile_floor_energy(d, 11*T, y3)
    tile_whiteboard(d, 12*T, y3)
    tile_coffee(d, 13*T, y3)
    tile_floor(d, 14*T, y3)
    tile_floor_neon(d, 15*T, y3)

    path = os.path.join(OUT, "public", "assets", "quantumhive-tileset.png")
    img.save(path)
    print(f"Tileset saved: {path}")
    return img

# ================================================================
# SPRITES DE AGENTES
# ================================================================

def draw_agent(d, ox, oy, body_c, accent_c, hair_c, skin_c, outline_c):
    """Dibuja un agente cyberpunk de 32x32 (un frame facing down)"""
    # Shadow
    r(d, ox+10,oy+28,ox+21,oy+30, (0,0,0,60))
    # Body
    r(d, ox+11,oy+14,ox+20,oy+27, body_c)
    r(d, ox+12,oy+15,ox+19,oy+26, body_c)
    # Head
    r(d, ox+12,oy+4,ox+19,oy+13, skin_c)
    r(d, ox+13,oy+5,ox+18,oy+12, skin_c)
    # Hair
    r(d, ox+11,oy+3,ox+20,oy+7, hair_c)
    # Eyes
    p(d, ox+14, oy+8, outline_c)
    p(d, ox+17, oy+8, outline_c)
    # Mouth
    l(d, ox+14,oy+11,ox+17,oy+11, outline_c)
    # Accent stripe on body
    r(d, ox+11,oy+18,ox+20,oy+19, accent_c)
    # Arms
    r(d, ox+8,oy+15,ox+10,oy+24, body_c)
    r(d, ox+21,oy+15,ox+23,oy+24, body_c)
    # Hands
    r(d, ox+8,oy+24,ox+10,oy+25, skin_c)
    r(d, ox+21,oy+24,ox+23,oy+25, skin_c)
    # Legs
    r(d, ox+12,oy+27,ox+14,oy+31, body_c)
    r(d, ox+17,oy+27,ox+19,oy+31, body_c)
    # Boots
    r(d, ox+11,oy+30,ox+15,oy+31, outline_c)
    r(d, ox+16,oy+30,ox+20,oy+31, outline_c)

def draw_agent_left(d, ox, oy, body_c, accent_c, hair_c, skin_c, outline_c):
    """Agente mirando a la izquierda"""
    r(d, ox+10,oy+28,ox+21,oy+30, (0,0,0,60))
    r(d, ox+12,oy+14,ox+20,oy+27, body_c)
    r(d, ox+12,oy+4,ox+19,oy+13, skin_c)
    r(d, ox+11,oy+3,ox+20,oy+7, hair_c)
    p(d, ox+13, oy+8, outline_c)
    p(d, ox+15, oy+8, outline_c)
    l(d, ox+13,oy+11,ox+16,oy+11, outline_c)
    r(d, ox+12,oy+18,ox+20,oy+19, accent_c)
    r(d, ox+9,oy+15,ox+11,oy+24, body_c)
    r(d, ox+21,oy+16,ox+23,oy+25, body_c)
    r(d, ox+9,oy+24,ox+11,oy+25, skin_c)
    r(d, ox+12,oy+27,ox+14,oy+31, body_c)
    r(d, ox+17,oy+27,ox+19,oy+31, body_c)
    r(d, ox+11,oy+30,ox+15,oy+31, outline_c)
    r(d, ox+16,oy+30,ox+20,oy+31, outline_c)

def draw_agent_right(d, ox, oy, body_c, accent_c, hair_c, skin_c, outline_c):
    """Agente mirando a la derecha"""
    r(d, ox+10,oy+28,ox+21,oy+30, (0,0,0,60))
    r(d, ox+11,oy+14,ox+19,oy+27, body_c)
    r(d, ox+12,oy+4,ox+19,oy+13, skin_c)
    r(d, ox+11,oy+3,ox+20,oy+7, hair_c)
    p(d, ox+16, oy+8, outline_c)
    p(d, ox+18, oy+8, outline_c)
    l(d, ox+15,oy+11,ox+18,oy+11, outline_c)
    r(d, ox+11,oy+18,ox+19,oy+19, accent_c)
    r(d, ox+9,oy+16,ox+11,oy+25, body_c)
    r(d, ox+20,oy+15,ox+22,oy+24, body_c)
    r(d, ox+20,oy+24,ox+22,oy+25, skin_c)
    r(d, ox+12,oy+27,ox+14,oy+31, body_c)
    r(d, ox+17,oy+27,ox+19,oy+31, body_c)
    r(d, ox+11,oy+30,ox+15,oy+31, outline_c)
    r(d, ox+16,oy+30,ox+20,oy+31, outline_c)

def draw_agent_up(d, ox, oy, body_c, accent_c, hair_c, skin_c, outline_c):
    """Agente mirando hacia arriba"""
    r(d, ox+10,oy+28,ox+21,oy+30, (0,0,0,60))
    r(d, ox+11,oy+14,ox+20,oy+27, body_c)
    r(d, ox+12,oy+4,ox+19,oy+13, skin_c)
    r(d, ox+11,oy+3,ox+20,oy+7, hair_c)
    r(d, ox+12,oy+18,ox+19,oy+19, accent_c)
    r(d, ox+8,oy+15,ox+10,oy+24, body_c)
    r(d, ox+21,oy+15,ox+23,oy+24, body_c)
    r(d, ox+8,oy+24,ox+10,oy+25, skin_c)
    r(d, ox+21,oy+24,ox+23,oy+25, skin_c)
    r(d, ox+12,oy+27,ox+14,oy+31, body_c)
    r(d, ox+17,oy+27,ox+19,oy+31, body_c)
    r(d, ox+11,oy+30,ox+15,oy+31, outline_c)
    r(d, ox+16,oy+30,ox+20,oy+31, outline_c)

# Agent color schemes
AGENT_COLORS = [
    # (body, accent, hair, skin, outline) — Hermes
    ((0, 180, 230), (255, 220, 30), (40, 30, 60), (200, 170, 140), (10, 10, 30)),
    # Dev_01
    ((30, 180, 80), (0, 220, 255), (60, 40, 30), (190, 160, 130), (10, 10, 30)),
    # Marketing_01
    ((220, 60, 120), (255, 150, 200), (80, 50, 40), (210, 175, 145), (10, 10, 30)),
    # Design_01
    ((150, 70, 220), (200, 130, 255), (50, 30, 60), (195, 165, 135), (10, 10, 30)),
    # Investigador
    ((200, 170, 30), (255, 220, 50), (70, 50, 30), (205, 170, 140), (10, 10, 30)),
    # OpenClaw_Bot
    ((80, 80, 120), (0, 200, 255), (30, 30, 50), (150, 140, 130), (10, 10, 30)),
]

def build_sprites():
    """Genera spritesheet de 6 agentes, 3 frames x 4 direcciones = 12 frames"""
    # 6 agents, each 96px wide (3 frames x 32px), 128px tall (4 dirs x 32px)
    img = Image.new("RGBA", (6*96, 128), (0,0,0,0))
    d = ImageDraw.Draw(img)

    draw_fns = [
        (draw_agent, 0),      # down
        (draw_agent_left, 32), # left
        (draw_agent_right, 64),# right
        (draw_agent_up, 96),   # up
    ]

    for agent_i, colors in enumerate(AGENT_COLORS):
        base_x = agent_i * 96
        for fn, y_off in draw_fns:
            for frame in range(3):
                # Slight variation per frame (arm position)
                ox = base_x + frame * 32
                oy = y_off
                fn(d, ox, oy, *colors)
                # Subtle frame variation
                if frame == 1:
                    # Slightly shifted arms
                    pass

    path = os.path.join(OUT, "public", "assets", "agent-sprites.png")
    img.save(path)
    print(f"Sprites saved: {path}")
    return img

# ================================================================
# MAPA DEL HQ
# ================================================================

def build_map():
    """
    Mapa 45x36 tiles con 8 departamentos alrededor del quantum core.
    Formato column-major: bgtiles[layer][x][y], objmap[layer][x][y]
    """
    W, H = 45, 36
    bg = [[-1]*H for _ in range(W)]
    obj = [[-1]*H for _ in range(W)]

    # Background: fill all with tile 0 (dark floor)
    for x in range(W):
        for y in range(H):
            bg[x][y] = 0

    # Neon floor corridors (tile 1)
    # Horizontal corridors
    for x in range(W):
        bg[x][17] = 1
        bg[x][18] = 1
    # Vertical corridors
    for y in range(H):
        bg[22][y] = 1

    # Department walls (tile 20-27) — outer ring + department borders
    # Outer walls
    for x in range(3, 42):
        obj[x][3] = 2    # top wall
        obj[x][32] = 2   # bottom wall
    for y in range(3, 33):
        obj[3][y] = 2    # left wall
        obj[41][y] = 2   # right wall

    # Top-left: Agent Orchestration (tile 20)
    for y in range(4, 12):
        obj[9][y] = 20
    for x in range(4, 10):
        obj[x][4] = 20

    # Top-center: Meeting Room (tile 27)
    for y in range(4, 12):
        obj[20][y] = 27
        obj[35][y] = 27
    for x in range(20, 36):
        obj[x][4] = 27

    # Top-right: Portal (tile 26)
    for y in range(4, 12):
        obj[36][y] = 26
    for x in range(36, 41):
        obj[x][4] = 26

    # Mid-left top: App Factory (tile 21)
    for y in range(12, 24):
        obj[9][y] = 21
    for x in range(4, 10):
        obj[x][12] = 21

    # Mid-right top: Learning Hub (tile 25)
    for y in range(12, 24):
        obj[36][y] = 25
    for x in range(36, 41):
        obj[x][12] = 25

    # Mid-left bottom: Data & Analytics (tile 22)
    for y in range(24, 32):
        obj[9][y] = 22
    for x in range(4, 10):
        obj[x][31] = 22

    # Mid-right bottom: Server Farm (tile 24)
    for y in range(24, 32):
        obj[36][y] = 24
    for x in range(36, 41):
        obj[x][31] = 24

    # Bottom-center: Communication Hub (tile 23)
    for y in range(24, 32):
        obj[20][y] = 23
        obj[35][y] = 23
    for x in range(20, 36):
        obj[x][31] = 23

    # Central quantum core area — special floor
    for x in range(18, 27):
        for y in range(14, 22):
            bg[x][y] = 1  # neon floor
    # Quantum core markers
    obj[22][17] = 7   # quantum hex (tile index 7 in row 1)
    obj[22][18] = 7

    # Hallway floors (tile 12 in row 3)
    for x in range(10, 20):
        bg[x][17] = 12
        bg[x][18] = 12
    for x in range(26, 36):
        bg[x][17] = 12
        bg[x][18] = 12

    # Department furniture — servers in Server Farm
    for y in range(25, 31):
        obj[37][y] = 4  # server rack
        obj[40][y] = 4

    # Screens in Agent Orchestration
    for y in range(5, 11):
        obj[5][y] = 5  # screen
        obj[8][y] = 5

    # Desks in Meeting Room
    for x in range(22, 34):
        obj[x][7] = 6   # screen graph
        obj[x][10] = 3   # desk

    # Plants decoration
    obj[4][4] = 10
    obj[40][4] = 10
    obj[4][31] = 10
    obj[40][31] = 10
    obj[18][14] = 10
    obj[26][14] = 10
    obj[18][21] = 10
    obj[26][21] = 10

    # Coffee station
    obj[15][5] = 8  # portal/coffee
    obj[30][5] = 8

    path = os.path.join(OUT, "data", "quantumhive.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write("// QuantumHive HQ Map — Auto-generated\n")
        f.write('export const tilesetpath = "/ai-town/assets/quantumhive-tileset.png";\n')
        f.write(f"export const tiledim = {T};\n")
        f.write(f"export const screenxtiles = {W};\n")
        f.write(f"export const screenytiles = {H};\n")
        f.write(f"export const tilesetpxw = {16*T};\n")
        f.write(f"export const tilesetpxh = {4*T};\n\n")

        def write_array(name, arr):
            f.write(f"export const {name} = [\n")
            for i, layer in enumerate(arr):
                f.write("  [\n")
                for row in layer:
                    f.write("   " + str(row) + ",\n")
                f.write("  ],\n")
            f.write("];\n\n")

        write_array("bgtiles", [bg])
        write_array("objmap", [obj])

        f.write("export const animatedsprites = [];\n\n")
        f.write(f"export const mapwidth = bgtiles[0].length;\n")
        f.write(f"export const mapheight = bgtiles[0][0].length;\n")

    print(f"Map saved: {path}")

# ================================================================
# SPRITESHEET DATA (.ts files)
# ================================================================

def build_spritesheet_data():
    """Genera archivos f1.ts a f6.ts con frame data"""
    names = ["Hermes", "Dev_01", "Marketing_01", "Design_01", "Investigador", "OpenClaw_Bot"]
    emojis = ["⚡", "💻", "📣", "🎨", "🔬", "🤖"]

    for i in range(6):
        base_x = i * 96
        path = os.path.join(OUT, "data", "spritesheets", f"f{i+1}.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write('import { SpritesheetData } from "./types";\n\n')
            f.write(f'// {names[i]} ({emojis[i]}) — QuantumHive Agent\n')
            f.write(f'export const spritesheetData: SpritesheetData = {{\n')
            f.write(f'  "meta": {{ "image": "/ai-town/assets/agent-sprites.png", "size": {{ "w": 576, "h": 128 }} }},\n')
            f.write(f'  "frames": {{\n')
            for direction, y_off in [("down", 0), ("left", 32), ("right", 64), ("up", 96)]:
                for frame in range(3):
                    name = direction if frame == 0 else f"{direction}{frame+1}"
                    fx = base_x + frame * 32
                    fy = y_off
                    f.write(f'    "{name}": {{ "frame": {{"x":{fx},"y":{fy},"w":32,"h":32}} }},\n')
            f.write(f'  }},\n')
            f.write(f'  "animations": {{\n')
            for direction in ["down", "left", "right", "up"]:
                frames = [direction] + [f"{direction}{j}" for j in range(2, 4)]
                f.write(f'    "{direction}": {frames},\n')
            f.write(f'  }},\n')
            f.write(f'}};\n')
        print(f"Spritesheet data saved: {path}")

# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":
    print("=== QuantumHive Town Asset Generator ===")
    build_tileset()
    build_sprites()
    build_map()
    build_spritesheet_data()
    print("=== All assets generated! ===")

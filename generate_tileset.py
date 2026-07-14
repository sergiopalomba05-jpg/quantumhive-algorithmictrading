#!/usr/bin/env python3
"""
QuantumHive Town — Generador completo de assets cyberpunk
Genera: tileset, sprites de agentes, mapa JS, spritesheet data TS
"""
from PIL import Image, ImageDraw, ImageFont
import os, json, math

OUT = os.path.dirname(os.path.abspath(__file__))
T = 32  # tile size

# === PALETTA CYBERPUNK ===
C = {
    "bg":        (10, 10, 26),
    "floor1":    (18, 18, 38),
    "floor2":    (22, 22, 45),
    "floor3":    (26, 26, 52),
    "floor_line":(30, 30, 58),
    "wall_d":    (12, 12, 30),
    "wall_m":    (20, 20, 42),
    "wall_l":    (30, 30, 55),
    "neon":      (0, 212, 255),
    "neon_d":    (0, 150, 200),
    "gold":      (255, 215, 0),
    "gold_d":    (180, 140, 0),
    "green":     (0, 255, 80),
    "red":       (255, 40, 40),
    "blue":      (0, 150, 255),
    "purple":    (180, 100, 255),
    "cyan":      (0, 255, 230),
    "srv1":      (25, 25, 50),
    "srv2":      (30, 30, 60),
    "screen_bg": (5, 15, 35),
    "desk":      (35, 30, 50),
    "desk_t":    (45, 40, 60),
    "white":     (220, 220, 230),
    "skin":      (200, 170, 140),
    "shadow":    (5, 5, 15),
}

def r(d, x1,y1,x2,y2,c): d.rectangle([x1,y1,x2,y2], fill=c)
def p(d, x,y,c): d.point((x,y), fill=c)
def l(d, x1,y1,x2,y2,c): d.line([x1,y1,x2,y2], fill=c, width=1)

# ================================================================
# TILESET: 16 columnas x 4 filas = 64 tiles de 32x32
# Fila 0: suelos y paredes basicas
# Fila 1: objetos (servidor, pantalla, escritorio, silla, etc)
# Fila 2: paredes de departamento (colores)
# Fila 3: variantes y decoracion
# ================================================================

def tile_floor(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["floor1"])
    for i in range(0,32,8):
        l(d, ox,oy+i,ox+31,oy+i, C["floor2"])
        l(d, ox+i,oy,ox+i,oy+31, C["floor2"])

def tile_floor_neon(d, ox, oy):
    tile_floor(d, ox, oy)
    r(d, ox+14,oy+14,ox+17,oy+17, C["neon"])
    for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        p(d, ox+15+dx, oy+15+dy, C["neon_d"])

def tile_wall(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["wall_d"])
    r(d, ox,oy,ox+31,oy+3, C["wall_m"])
    r(d, ox,oy+1,ox+31,oy+1, C["neon"])
    r(d, ox,oy+29,ox+31,oy+31, C["shadow"])

def tile_wall_gold(d, ox, oy):
    tile_wall(d, ox, oy)
    r(d, ox+10,oy+8,ox+21,oy+24, C["wall_m"])
    r(d, ox+11,oy+9,ox+20,oy+23, C["gold_d"])
    r(d, ox+12,oy+10,ox+19,oy+22, C["gold"])

def tile_server(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+4,oy+2,ox+27,oy+29, C["srv1"])
    r(d, ox+5,oy+3,ox+26,oy+28, C["srv2"])
    for i in range(4):
        y = oy+4+i*6
        r(d, ox+6,y,ox+25,y+4, C["srv1"])
        r(d, ox+7,y+1,ox+24,y+3, C["srv2"])
        colors = [C["green"],C["blue"],C["red"],C["green"]]
        p(d, ox+24,y+2, colors[i])
        p(d, ox+22,y+2, C["green"])
    r(d, ox+4,oy+2,ox+4,oy+29, C["wall_l"])
    r(d, ox+27,oy+2,ox+27,oy+29, C["wall_l"])

def tile_screen(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+2,oy+4,ox+29,oy+26, C["wall_l"])
    r(d, ox+3,oy+5,ox+28,oy+25, C["screen_bg"])
    for i in range(5):
        y = oy+7+i*4
        w = 12+(i%3)*4
        r(d, ox+5,y,ox+5+w,y+1, C["neon"])
    r(d, ox+3,oy+5,ox+28,oy+5, C["neon"])

def tile_screen_chart(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+1,oy+2,ox+30,oy+28, C["wall_l"])
    r(d, ox+2,oy+3,ox+29,oy+27, C["screen_bg"])
    bars = [8,14,10,18,12,20,15]
    for i,h in enumerate(bars):
        x = ox+4+i*3
        r(d, x,oy+27-h,x+2,oy+27, C["neon"])
    r(d, ox+2,oy+3,ox+29,oy+3, C["gold"])

def tile_desk(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+2,oy+12,ox+29,oy+18, C["desk_t"])
    r(d, ox+2,oy+18,ox+29,oy+22, C["desk"])
    r(d, ox+3,oy+22,ox+5,oy+28, C["desk"])
    r(d, ox+26,oy+22,ox+28,oy+28, C["desk"])
    r(d, ox+10,oy+5,ox+22,oy+12, C["screen_bg"])
    r(d, ox+11,oy+6,ox+21,oy+11, C["neon"])
    r(d, ox+14,oy+12,ox+18,oy+14, C["wall_l"])

def tile_chair(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+8,oy+14,ox+23,oy+20, (30,25,45))
    r(d, ox+9,oy+15,ox+22,oy+19, C["wall_m"])
    r(d, ox+9,oy+8,ox+22,oy+14, (30,25,45))
    r(d, ox+10,oy+9,ox+21,oy+13, C["wall_m"])
    r(d, ox+10,oy+20,ox+11,oy+26, (30,25,45))
    r(d, ox+20,oy+20,ox+21,oy+26, (30,25,45))

def tile_cable(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    for i in range(3):
        y = oy+8+i*6
        for x in range(ox+2,ox+30,2):
            p(d, x,y, (15,15,35))
            glow = C["neon_d"] if (x+oy)%8<3 else (15,15,35)
            p(d, x+1,y, glow)

def tile_plant(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    r(d, ox+10,oy+20,ox+21,oy+28, (40,30,20))
    r(d, ox+9,oy+20,ox+22,oy+21, (40,30,20))
    for dx,dy in [(-2,-4),(0,-6),(2,-4),(3,-2),(-3,-2),(-1,-7),(1,-7)]:
        p(d, ox+15+dx, oy+20+dy, (0,80,40))

def tile_quantum(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    cx,cy = ox+16,oy+16
    for rad,color in [(12,C["gold"]),(10,C["neon"]),(7,C["gold"]),(4,C["neon"])]:
        for a in range(0,360,15):
            x = int(cx+rad*math.cos(math.radians(a)))
            y = int(cy+rad*math.sin(math.radians(a)))
            p(d, x,y, color)
    r(d, cx-2,cy-2,cx+2,cy+2, C["gold"])
    r(d, cx-1,cy-1,cx+1,cy+1, C["cyan"])

def tile_portal(d, ox, oy):
    r(d, ox,oy,ox+31,oy+31, C["bg"])
    cx,cy = ox+16,oy+16
    for rad in [12,10,7,4]:
        color = C["neon"] if rad%4==0 else C["gold"]
        for a in range(0,360,10):
            x = int(cx+rad*math.cos(math.radians(a)))
            y = int(cy+rad*math.sin(math.radians(a)))
            p(d, x,y, color)
    r(d, cx-1,cy-1,cx+1,cy+1, C["cyan"])

# Dept wall tiles (fila 2)
DEPT_COLORS = {
    "orchestration": C["neon"],
    "appfactory":    C["green"],
    "analytics":     C["gold"],
    "comms":         C["cyan"],
    "server":        C["blue"],
    "learning":      C["purple"],
    "portal":        C["gold"],
    "meeting":       C["red"],
}

def tile_dept_wall(d, ox, oy, color):
    r(d, ox,oy,ox+31,oy+31, C["wall_d"])
    r(d, ox,oy,ox+31,oy+3, C["wall_m"])
    r(d, ox,oy+1,ox+31,oy+1, color)
    r(d, ox,oy+29,ox+31,oy+31, C["shadow"])
    r(d, ox+14,oy+12,ox+17,oy+19, color)

# ================================================================
# SPRITESHEET: 6 agentes, cada uno 4 dirs x 3 frames = 12 frames
# Layout: 6 columns (1 agent per column), 4 rows (dirs)
# Each agent: 3 frames wide x 4 dirs tall = 96x128 px
# Total: 6*96=576 x 128 px
# ================================================================

AGENT_COLORS = {
    "Hermes":       {"body":(0,180,220),  "acc":(255,215,0),  "hair":(200,200,220)},
    "Dev_01":       {"body":(0,150,80),   "acc":(0,255,180),  "hair":(40,40,60)},
    "Marketing_01": {"body":(180,40,130), "acc":(255,100,200), "hair":(60,30,50)},
    "Design_01":    {"body":(150,80,220), "acc":(200,140,255), "hair":(30,20,50)},
    "Investigador": {"body":(220,180,0),  "acc":(255,255,100), "hair":(50,40,30)},
    "OpenClaw_Bot": {"body":(80,80,100),  "acc":(0,212,255),  "hair":(20,20,35)},
}

def draw_agent_frame(d, ox, oy, direction, frame, colors):
    """Dibuja un frame de 32x32 de un agente"""
    body, acc, hair = colors["body"], colors["acc"], colors["hair"]
    
    # Walking offset
    wo = 0
    if frame == 1: wo = -1
    if frame == 2: wo = 1
    
    # Head (centered)
    r(d, ox+11,oy+4,ox+20,oy+12, C["skin"])
    r(d, ox+11,oy+3,ox+20,oy+6, hair)
    
    # Eyes based on direction
    if direction == "down":
        p(d, ox+13,oy+8, C["white"]); p(d, ox+17,oy+8, C["white"])
        p(d, ox+13,oy+9, acc); p(d, ox+17,oy+9, acc)
    elif direction == "up":
        r(d, ox+12,oy+5,ox+19,oy+7, hair)
    elif direction == "left":
        p(d, ox+12,oy+8, C["white"]); p(d, ox+12,oy+9, acc)
    elif direction == "right":
        p(d, ox+18,oy+8, C["white"]); p(d, ox+18,oy+9, acc)
    
    # Body
    r(d, ox+10,oy+13,ox+21,oy+26, body)
    # Neon belt
    r(d, ox+10,oy+20,ox+21,oy+21, acc)
    
    # Arms
    if direction == "left":
        r(d, ox+7,oy+14,ox+10,oy+20, body)
    elif direction == "right":
        r(d, ox+21,oy+14,ox+24,oy+20, body)
    
    # Legs with walk cycle
    if direction in ["down","up"]:
        r(d, ox+12+wo,oy+26,ox+14+wo,oy+30, body)
        r(d, ox+17-wo,oy+26,ox+19-wo,oy+30, body)
    else:
        r(d, ox+12,oy+26,ox+14,oy+30, body)
        r(d, ox+17,oy+26,ox+19,oy+30, body)
    
    # Shoes glow
    r(d, ox+12+wo,oy+30,ox+14+wo,oy+31, acc)
    r(d, ox+17-wo,oy+30,ox+19-wo,oy+31, acc)

def gen_spritesheet():
    agents = list(AGENT_COLORS.keys())
    n = len(agents)
    img = Image.new("RGBA", (n*3*T, 4*T), (0,0,0,0))
    d = ImageDraw.Draw(img)
    
    dirs = ["down","left","right","up"]
    for ai, name in enumerate(agents):
        colors = AGENT_COLORS[name]
        for di, direction in enumerate(dirs):
            for frame in range(3):
                ox = ai*3*T + frame*T
                oy = di*T
                draw_agent_frame(d, ox, oy, direction, frame, colors)
    return img

# ================================================================
# MAP DATA: Genera gentle.js compatible
# ================================================================
def gen_map_js(path, w, h):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w") as f:
        f.write('// QuantumHive HQ Map — Auto-generated\n')
        f.write('export const tilesetpath = "/ai-town/assets/quantumhive-tileset.png";\n')
        f.write('export const tiledim = 32;\n')
        f.write(f'export const screenxtiles = {w};\n')
        f.write(f'export const screenytiles = {h};\n')
        f.write(f'export const tilesetpxw = {16*T};\n')
        f.write(f'export const tilesetpxh = {4*T};\n\n')
        
        # Column-major format: bgtiles[layer][x][y]
        # BG layer 0: floor
        f.write('export const bgtiles = [\n')
        f.write('  [\n')
        for x in range(w):
            col = []
            for y in range(h):
                if x in [22,23] or y in [17,18]:
                    col.append(1)
                else:
                    col.append(0)
            f.write('   [' + ','.join(str(v) for v in col) + '],\n')
        f.write('  ],\n')
        # Layer 1: empty
        f.write('  [\n')
        for x in range(w):
            f.write('   [' + ','.join(['-1']*h) + '],\n')
        f.write('  ],\n')
        f.write('];\n\n')
        
        # objmap - column-major
        f.write('export const objmap = [\n')
        f.write('  [\n')
        for x in range(w):
            col = []
            for y in range(h):
                val = -1
                if y <= 3 or y >= h-4 or x <= 3 or x >= w-4:
                    val = 2
                elif y <= 5:
                    if x < 13: val = 20
                    elif x < 28: val = 21
                    else: val = 22
                elif y >= h-6:
                    if x < 13: val = 26
                    elif x < 28: val = 25
                    else: val = 24
                elif x <= 5 and 10 <= y <= 20:
                    val = 27
                elif x >= w-6 and 10 <= y <= 20:
                    val = 23
                col.append(val)
            f.write('   [' + ','.join(str(v) for v in col) + '],\n')
        f.write('  ],\n')
        # Layer 2: empty
        f.write('  [\n')
        for x in range(w):
            f.write('   [' + ','.join(['-1']*h) + '],\n')
        f.write('  ],\n')
        f.write('];\n\n')
        
        f.write('export const animatedsprites = [];\n\n')
        f.write(f'export const mapwidth = bgtiles[0].length;\n')
        f.write(f'export const mapheight = bgtiles[0][0].length;\n')

# ================================================================
# SPRITESHEET DATA TS files
# ================================================================
def gen_spritesheet_ts(name, col_idx):
    """Generate a .ts file with spritesheet data for one agent"""
    # Each agent is at column col_idx in the spritesheet
    # 3 frames per direction, 4 directions
    # Frame positions: x = col_idx*96 + frame*32, y = dir*32
    frames = {}
    animations = {}
    
    dirs = [("down",0),("left",1),("right",2),("up",3)]
    for dir_name, dir_y in dirs:
        dir_frames = []
        for fi in range(3):
            fname = f"{dir_name}{fi+1}" if fi > 0 else dir_name
            x = col_idx * 96 + fi * 32
            y = dir_y * 32
            frames[fname] = {
                "frame": {"x": x, "y": y, "w": 32, "h": 32},
                "sourceSize": {"w": 32, "h": 32},
                "spriteSourceSize": {"x": 0, "y": 0}
            }
            dir_frames.append(fname)
        animations[dir_name] = dir_frames
    
    return f'''import {{ SpritesheetData }} from './types';

export const data: SpritesheetData = {{
  frames: {json.dumps(frames, indent=4)},
  meta: {{
    scale: '1',
  }},
  animations: {json.dumps(animations, indent=4)},
}};
'''

# ================================================================
# MAIN
# ================================================================
def main():
    print("=== QuantumHive Town — Generador Cyberpunk v2 ===\n")
    
    # 1. TILESET
    print("[1/4] Generando tileset...")
    tileset = Image.new("RGBA", (16*T, 4*T), (0,0,0,0))
    td = ImageDraw.Draw(tileset)
    
    # Fila 0: suelos y paredes
    tile_floor(td, 0*T, 0)        # 0
    tile_floor_neon(td, 1*T, 0)   # 1
    tile_wall(td, 2*T, 0)         # 2
    tile_wall_gold(td, 3*T, 0)    # 3
    tile_server(td, 4*T, 0)       # 4
    tile_screen(td, 5*T, 0)       # 5
    tile_screen_chart(td, 6*T, 0) # 6
    tile_desk(td, 7*T, 0)         # 7
    tile_chair(td, 8*T, 0)        # 8
    tile_cable(td, 9*T, 0)        # 9
    tile_plant(td, 10*T, 0)       # 10
    tile_quantum(td, 11*T, 0)     # 11
    tile_portal(td, 12*T, 0)      # 12
    # Fila 0, cols 13-15: variaciones
    tile_floor(td, 13*T, 0)
    tile_floor_neon(td, 14*T, 0)
    tile_wall(td, 15*T, 0)
    
    # Fila 1: mas objetos
    tile_server(td, 0*T, T)      # 16
    tile_screen(td, 1*T, T)      # 17
    tile_screen_chart(td, 2*T, T)# 18
    tile_desk(td, 3*T, T)        # 19
    tile_chair(td, 4*T, T)       # 20
    tile_cable(td, 5*T, T)       # 21
    tile_plant(td, 6*T, T)       # 22
    tile_quantum(td, 7*T, T)     # 23
    tile_portal(td, 8*T, T)      # 24
    tile_floor(td, 9*T, T)
    tile_floor_neon(td, 10*T, T)
    tile_wall(td, 11*T, T)
    tile_wall_gold(td, 12*T, T)
    tile_server(td, 13*T, T)
    tile_screen(td, 14*T, T)
    tile_desk(td, 15*T, T)
    
    # Fila 2: paredes de departamento
    dept_list = ["orchestration","appfactory","analytics","comms","server","learning","portal","meeting"]
    for i, dept in enumerate(dept_list):
        tile_dept_wall(td, i*T, 2*T, DEPT_COLORS[dept])
    # Rest of fila 2
    for i in range(8, 16):
        tile_floor(td, i*T, 2*T)
    
    # Fila 3: variaciones
    for i in range(16):
        tile_floor(td, i*T, 3*T)
    
    ts_path = os.path.join(OUT, "public", "assets", "quantumhive-tileset.png")
    os.makedirs(os.path.dirname(ts_path), exist_ok=True)
    tileset.save(ts_path)
    print(f"   -> {ts_path} ({tileset.size[0]}x{tileset.size[1]})")
    
    # 2. SPRITES DE AGENTES
    print("[2/4] Generando sprites de agentes...")
    spritesheet = gen_spritesheet()
    sp_path = os.path.join(OUT, "public", "assets", "agent-sprites.png")
    spritesheet.save(sp_path)
    print(f"   -> {sp_path} ({spritesheet.size[0]}x{spritesheet.size[1]})")
    
    # 3. SPRITESHEET DATA TS
    print("[3/4] Generando spritesheet data...")
    agents = list(AGENT_COLORS.keys())
    ss_dir = os.path.join(OUT, "data", "spritesheets")
    os.makedirs(ss_dir, exist_ok=True)
    
    agent_chars = ["f1","f2","f3","f4","f5","f6"]  # 6 agents
    for i, (agent_name, char_name) in enumerate(zip(agents, agent_chars)):
        ts_content = gen_spritesheet_ts(agent_name, i)
        ts_file = os.path.join(ss_dir, f"{char_name}.ts")
        with open(ts_file, "w") as f:
            f.write(ts_content)
        print(f"   -> {ts_file}")
    
    # 4. MAPA JS
    print("[4/4] Generando mapa...")
    MAP_W, MAP_H = 45, 36
    map_path = os.path.join(OUT, "data", "quantumhive.js")
    gen_map_js(map_path, MAP_W, MAP_H)
    print(f"   -> {map_path}")
    
    # 5. MAPA VISUAL (preview PNG)
    print("   Generando preview del mapa...")
    map_img = Image.new("RGBA", (MAP_W*T, MAP_H*T), C["bg"])
    md = ImageDraw.Draw(map_img)
    
    # Fondo
    r(md, 0,0,MAP_W*T-1,MAP_H*T-1, C["bg"])
    
    # Suelo
    for y in range(MAP_H):
        for x in range(MAP_W):
            tile_floor(md, x*T, y*T)
    
    # Neon paths
    for x in range(MAP_W):
        tile_floor_neon(md, x*T, 17*T)
        tile_floor_neon(md, x*T, 18*T)
    for y in range(MAP_H):
        tile_floor_neon(md, 22*T, y*T)
        tile_floor_neon(md, 23*T, y*T)
    
    # Quantum core centro
    for dx in range(-4,5):
        for dy in range(-4,5):
            if abs(dx)+abs(dy) <= 5:
                tile_quantum(md, (22+dx)*T, (18+dy)*T)
    
    # Dept walls
    for x in range(2,13):
        tile_dept_wall(md, x*T, 2*T, C["neon"])
        tile_dept_wall(md, x*T, 3*T, C["neon"])
    for y in range(2,10):
        tile_dept_wall(md, 2*T, y*T, C["neon"])
    
    for x in range(16,28):
        tile_dept_wall(md, x*T, 2*T, C["green"])
        tile_dept_wall(md, x*T, 3*T, C["green"])
    
    for x in range(32,43):
        tile_dept_wall(md, x*T, 2*T, C["gold"])
        tile_dept_wall(md, x*T, 3*T, C["gold"])
    
    for y in range(10,20):
        tile_dept_wall(md, 42*T, y*T, C["cyan"])
        tile_dept_wall(md, 43*T, y*T, C["cyan"])
    
    for x in range(35,43):
        tile_dept_wall(md, x*T, 30*T, C["blue"])
        tile_dept_wall(md, x*T, 31*T, C["blue"])
    for y in range(26,32):
        tile_dept_wall(md, 42*T, y*T, C["blue"])
        tile_dept_wall(md, 43*T, y*T, C["blue"])
    
    for x in range(16,28):
        tile_dept_wall(md, x*T, 32*T, C["purple"])
        tile_dept_wall(md, x*T, 33*T, C["purple"])
    
    for x in range(2,12):
        tile_dept_wall(md, x*T, 32*T, C["gold"])
        tile_dept_wall(md, x*T, 33*T, C["gold"])
    for y in range(24,34):
        tile_dept_wall(md, 2*T, y*T, C["gold"])
        tile_dept_wall(md, 3*T, y*T, C["gold"])
    
    for y in range(10,20):
        tile_dept_wall(md, 2*T, y*T, C["red"])
        tile_dept_wall(md, 3*T, y*T, C["red"])
    
    # Muebles
    for x in range(36,42):
        for y in range(27,30):
            tile_server(md, x*T, y*T)
    for x in range(33,42,3):
        tile_screen_chart(md, x*T, 4*T)
    for x in range(17,27,3):
        tile_desk(md, x*T, 5*T)
        tile_chair(md, (x+1)*T, 5*T)
    for x in range(4,10,3):
        tile_portal(md, x*T, 28*T)
    tile_screen(md, 4*T, 12*T)
    tile_screen(md, 8*T, 12*T)
    for x in range(5,40,4):
        tile_cable(md, x*T, 17*T)
    for pos in [(5,6),(10,6),(35,6),(40,6),(5,28),(10,28),(35,28),(40,28)]:
        tile_plant(md, pos[0]*T, pos[1]*T)
    
    # Labels
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    labels = [
        (5,1,"AGENT ORCHESTRATION CENTER",C["neon"]),
        (20,1,"APP FACTORY",C["green"]),
        (35,1,"DATA & ANALYTICS LAB",C["gold"]),
        (41,9,"COMMUNICATION HUB",C["cyan"]),
        (36,25,"SERVER FARM",C["blue"]),
        (20,31,"LEARNING & UPGRADE HUB",C["purple"]),
        (4,31,"PORTAL / ENERGY CORE",C["gold"]),
        (3,9,"MEETING & STRATEGY ROOM",C["red"]),
    ]
    for lx,ly,label,color in labels:
        md.text((lx*T, ly*T), label, fill=color, font=font)
    
    cx,cy = 22*T, 18*T
    md.text((cx-50, cy-20), "QUANTUMHIVE", fill=C["gold"], font=font)
    md.text((cx-40, cy), "AI ORCHESTRATION", fill=C["neon"], font=font)
    md.text((cx-20, cy+20), "IA TOWN", fill=C["cyan"], font=font)
    
    preview_path = os.path.join(OUT, "public", "assets", "quantumhive-hq-preview.png")
    map_img.save(preview_path)
    print(f"   -> {preview_path}")
    
    print("\n=== COMPLETADO ===")
    print(f"Tileset: 16x4 tiles (64 tiles de 32x32)")
    print(f"Agentes: {len(agents)} sprites ({spritesheet.size[0]}x{spritesheet.size[1]})")
    print(f"Mapa: {MAP_W}x{MAP_H} tiles ({MAP_W*T}x{MAP_H*T} px)")
    print(f"\nArchivos generados:")
    print(f"  - public/assets/quantumhive-tileset.png")
    print(f"  - public/assets/agent-sprites.png")
    print(f"  - data/quantumhive.js")
    print(f"  - data/spritesheets/f1-f6.ts (nuevos)")
    print(f"  - public/assets/quantumhive-hq-preview.png")

if __name__ == "__main__":
    main()

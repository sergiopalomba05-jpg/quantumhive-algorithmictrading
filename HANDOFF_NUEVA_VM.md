# HANDOFF COMPLETO — QuantumHive Town
## Para nueva VM / nuevo agente

---

## 1. QUÉ ES QUANTUMHIVE

QuantumHive es una empresa de algorithmic trading. Tiene 11 divisiones macro con ~193 agentes de IA que ejecutan micro-tareas. El CEO es Sergio Palomba.

### Divisiones
1. **Trading Core** — Bots de trading, señales, backtesting
2. **Operaciones** — Ejecución, gestión de cuentas, prop firms
3. **Marketing** — Contenido, redes, copy, métricas
4. **Fábrica** — Desarrollo de bots, código, deploy
5. **Legal** — Compliance, contratos
6. **Colmena** — Comunicación interna, Telegram bots
7. **Apps** — Desarrollo de aplicaciones (catálogo, admin)
8. **Universidad** — Capacitación, cursos, investigación
9. **Comunicaciones** — Notificaciones, alertas
10. **Innovación** — I+D, nuevos productos
11. **Infraestructura** — Servidores, VPS, cloud

### Documentos de contexto (en el repo, carpeta `context/`)
- `CONTEXTO_MAESTRO.md` — Identidad completa de QuantumHive
- `ESTRUCTURA_ORGANIZACIONAL.md` — Las 11 divisiones y ~193 agentes
- `CONTEXTO_AGENTES.md` — Lista completa de agentes con micro-tareas
- `QUANTUMHIVE_ARQUITECTURA.md` — Arquitectura técnica
- `vision_ceo.md` — Visión del CEO

---

## 2. QUÉ ES QUANTUMHIVE TOWN

Es un **dashboard visual cyberpunk** tipo HQ isométrico (inspirado en a16z AI Town). Los agentes de QuantumHive aparecen como sprites pixel art caminando por un edificio futuristic. Cada división tiene su oficina. El CEO puede interactuar con los agentes.

### Referencia visual
El usuario mandó imágenes de un HQ isométrico cyberpunk con:
- Centro hexagonal "QUANTUMHIVE AI ORCHESTRATION CORE"
- 8 departamentos alrededor con nombres
- Estilo dark + neon azul/dorado
- Agentes pixel art en sus puestos de trabajo
- Pantallas con gráficos, servidores, cables

### Stack
- **Frontend**: Vite 4 + React 18 + TypeScript + Tailwind CSS
- **Rendering 2D**: PIXI.js via @pixi/react (canvas, sprites, tilemap)
- **Backend**: Convex (database realtime + serverless functions + A* pathfinding)
- **LLM**: Vertex AI (Google Cloud) — Gemini 2.5 Flash
- **Sprites**: Generados con Python/PIL (Pillow)
- **Tilemap**: Formato column-major `[x][y]`, tiles de 32x32px

---

## 3. REPOSITORIOS

| Repo | URL | Estado |
|------|-----|--------|
| **PRINCIPAL** | `https://github.com/sergiopalomba05-jpg/quantumhive-algorithmictrading` | USAR ESTE |
| quantumhive (viejo) | `https://github.com/sergiopalomba05-jpg/quantumhive` | NO USAR |

- **Rama principal**: `main`
- **Identity git**: `Sergio Palomba <sergio@quantumhive.com>`

---

## 4. ESTRUCTURA DEL PROYECTO

```
quantumhive-algorithmictrading/          ← repo root en GitHub
├── context/                             ← documentación QuantumHive (193 agentes, etc.)
│   ├── CONTEXTO_MAESTRO.md
│   ├── ESTRUCTURA_ORGANIZACIONAL.md
│   ├── CONTEXTO_AGENTES.md
│   └── ... (archivos .md, .py, .json)
│
└── quantumhive-town/                    ← AI Town (EL PROYECTO)
    ├── quantumhive-town/                ← código del juego
    │   ├── convex/                      ← backend Convex (serverless)
    │   │   ├── init.ts                  ← INICIALIZACIÓN del mundo (importa quantumhive.js)
    │   │   ├── aiTown/                  ← lógica del juego
    │   │   │   ├── movement.ts          ← A* pathfinding
    │   │   │   ├── player.ts            ← tick, pathfinding, posición
    │   │   │   ├── worldMap.ts          ← clase WorldMap (formato de datos)
    │   │   │   └── ...
    │   │   ├── util/llm.ts             ← Vertex AI provider (MODIFICADO)
    │   │   └── schema.ts
    │   │
    │   ├── src/                         ← React + PIXI frontend
    │   │   ├── App.tsx                  ← raíz (help modal + Game)
    │   │   ├── components/
    │   │   │   ├── Game.tsx             ← shell UI, panel lateral, botones
    │   │   │   ├── PixiGame.tsx         ← game loop, viewport, click-to-move
    │   │   │   ├── PixiStaticMap.tsx    ← RENDERER DE TILES (lee layer[x][y])
    │   │   │   ├── PixiViewport.tsx     ← cámara, drag, zoom, pinch
    │   │   │   ├── Character.tsx        ← renderiza sprite animado por dirección
    │   │   │   ├── Player.tsx           ← wrapper de Character (posición histórica)
    │   │   │   ├── PlayerDetails.tsx    ← panel derecho con info del agente
    │   │   │   └── buttons/             ← InteractButton, Button, etc.
    │   │   ├── hooks/
    │   │   │   ├── useHistoricalTime.ts ← sincronización de tiempo con servidor
    │   │   │   ├── useHistoricalValue.ts← interpolación de posición
    │   │   │   ├── serverGame.ts        ← hook que parsea estado del juego
    │   │   │   └── sendInput.ts         ← enviar inputs al servidor
    │   │   └── index.css
    │   │
    │   ├── data/                        ← DATOS DEL JUEGO
    │   │   ├── characters.ts            ← DEFINICIÓN DE 6 AGENTES (MODIFICADO)
    │   │   ├── quantumhive.js           ← MAPA DEL HQ (NUEVO, reemplaza gentle.js)
    │   │   ├── gentle.js                ← mapa original a16z (NO SE USA)
    │   │   └── spritesheets/
    │   │       ├── f1.ts - f6.ts        ← FRAME DATA de cada agente (NUEVOS)
    │   │       ├── f7.ts - f8.ts        ← viejos (NO SE USAN)
    │   │       └── types.ts             ← tipo SpritesheetData
    │   │
    │   ├── public/assets/               ← IMÁGENES
    │   │   ├── quantumhive-tileset.png  ← TILESET CYBERPUNK (NUEVO, 512x128)
    │   │   ├── agent-sprites.png        ← SPRITES 6 AGENTES (NUEVO, 576x128)
    │   │   ├── 32x32folk.png            ← sprites originales a16z (NO SE USA)
    │   │   ├── gentle-obj.png           ← tileset original a16z (NO SE USA)
    │   │   └── fonts/                   ← VCR OSD Mono, Upheaval Pro
    │   │
    │   ├── generate_tileset.py          ← SCRIPT PYTHON generador de assets (NUEVO)
    │   ├── package.json
    │   ├── vite.config.ts               ← base: '/ai-town'
    │   ├── .env.local                   ← config (NO commitear)
    │   ├── tsconfig.json
    │   ├── tailwind.config.js
    │   └── index.html
    │
    ├── HANDOFF_NUEVA_VM.md              ← ESTE ARCHIVO
    ├── WORKFLOW.md                       ← instrucciones de setup
    ├── AGENTS.md                         ← contexto rápido
    └── PLAN_QUANTUMHIVE_TOWN.md         ← plan de implementación
```

---

## 5. QUÉ SE MODIFICÓ vs EL ORIGINAL

### Archivos NUEVOS creados
| Archivo | Qué es |
|---------|--------|
| `generate_tileset.py` | Script Python (~600 líneas) que genera todo el tileset cyberpunk |
| `data/quantumhive.js` | Mapa del HQ (45x36 tiles, column-major format) |
| `data/spritesheets/f1.ts` a `f6.ts` | Frame data de los 6 agentes cyberpunk |
| `public/assets/quantumhive-tileset.png` | Tileset 16x4 tiles de 32px |
| `public/assets/agent-sprites.png` | Sprites de 6 agentes |
| `public/assets/quantumhive-hq.png` | Preview visual del mapa |
| `HANDOFF_NUEVA_VM.md` | Este handoff |
| `WORKFLOW.md` | Instrucciones de setup |
| `AGENTS.md` | Contexto rápido para el siguiente agente |
| `PLAN_QUANTUMHIVE_TOWN.md` | Plan de implementación |

### Archivos MODIFICADOS
| Archivo | Qué cambió |
|---------|-----------|
| `data/characters.ts` | De 8 agentes (a16z folk) a 6 agentes cyberpunk. `textureUrl` apunta a `agent-sprites.png` |
| `convex/init.ts` | `import * as map from '../data/quantumhive'` (antes era `gentle`) |
| `convex/util/llm.ts` | Agregado provider Vertex AI con `getLLMConfig()` y `chatCompletion()` |
| `.env.local` | Config Vertex AI + Convex local |
| `.gitignore` | Agregado `__pycache__/`, `convex/_generated/`, preview PNG |

### Archivos NO TOCADOS (intactos del a16z)
- `src/components/PixiStaticMap.tsx` — el renderer de tiles
- `src/components/PixiGame.tsx` — el game loop
- `src/components/Character.tsx` — renderizado de sprites
- `src/components/PixiViewport.tsx` — cámara/viewport
- `convex/aiTown/movement.ts` — pathfinding A*
- `convex/aiTown/player.ts` — lógica de movimiento
- Todo el schema de Convex

---

## 6. CONFIGURACIÓN DEL ENTORNO

### .env.local (en quantumhive-town/)
```bash
# Vertex AI (Google Cloud)
LLM_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=project-aa5fb956-b08a-4e13-869
GOOGLE_CLOUD_LOCATION=us-central1
LLM_MODEL=gemini-2.5-flash
LLM_EMBEDDING_MODEL=text-embedding-004

# Convex local
CONVEX_DEPLOYMENT=anonymous:anonymous-quantumhive
VITE_CONVEX_URL=http://127.0.0.1:3210
VITE_CONVEX_SITE_URL=http://127.0.0.1:3211
```

### Variables de Convex (server-side, via CLI)
```bash
npx convex env set LLM_PROVIDER vertex
npx convex env set GOOGLE_CLOUD_PROJECT project-aa5fb956-b08a-4e13-869
npx convex env set GOOGLE_CLOUD_LOCATION us-central1
npx convex env set LLM_MODEL gemini-2.5-flash
npx convex env set LLM_EMBEDDING_MODEL text-embedding-004
```

### Credenciales (NO commitear, NO exponer)
```
GCP Project:           project-aa5fb956-b08a-4e13-869
GCP Service Account:   557866434489-compute@developer.gserviceaccount.com
Supabase URL:          https://gbngjsulhqcwgkqoxozy.supabase.co
Telegram Bot:          @vm1openclaw_bot
Telegram Token:        8900188300:AAFhsZpOLR8TYbbdqChqkUTX28dH-FC2l5Y
Telegram User ID:      7787265794
Telegram Group ID:     -1004435575714
Hermes:                v0.18.2 en %LOCALAPPDATA%\hermes\hermes-agent\
OpenClaw:              v2026.6.11 en %LOCALAPPDATA%\OpenClaw\
```

---

## 7. PIPELINE DE ARRANQUE EN NUEVA VM

### Paso 1: Instalar dependencias del sistema
```bash
# Node.js 18+ y npm
# Python 3.12+ con Pillow
pip install Pillow
# Git
```

### Paso 2: Clonar e instalar
```bash
git clone https://github.com/sergiopalomba05-jpg/quantumhive-algorithmictrading.git
cd quantumhive-algorithmictrading/quantumhive-town/quantumhive-town
npm install --legacy-peer-deps
```

### Paso 3: Generar assets cyberpunk
```bash
python generate_tileset.py
```
Esto genera automáticamente:
- `public/assets/quantumhive-tileset.png` — tileset con 64 tiles
- `public/assets/agent-sprites.png` — sprites de 6 agentes
- `data/quantumhive.js` — mapa del HQ
- `data/spritesheets/f1-f6.ts` — data de frames

### Paso 4: Setear variables de Convex
```bash
npx convex env set LLM_PROVIDER vertex
npx convex env set GOOGLE_CLOUD_PROJECT project-aa5fb956-b08a-4e13-869
npx convex env set GOOGLE_CLOUD_LOCATION us-central1
npx convex env set LLM_MODEL gemini-2.5-flash
npx convex env set LLM_EMBEDDING_MODEL text-embedding-004
```

### Paso 5: Arrancar el desarrollo
```bash
# Terminal 1: Convex (serverless backend)
npx convex dev

# Terminal 2: Vite (frontend dev server)
npx vite --host
```

### Paso 6: Abrir el juego
- URL: `http://localhost:5173/ai-town/`
- Convex dashboard: `http://localhost:3210`
- Si está gris: `Ctrl+F5` (hard refresh)

---

## 8. FORMATO DE DATOS TÉCNICO

### Tilemap (column-major)
El renderer `PixiStaticMap.tsx` espera:
```javascript
bgtiles[layer][x][y]   // tile index o -1 si vacío
objmap[layer][x][y]    // tile index de objetos o -1
```

### Dimensiones del mapa
```
width (screenxtiles):  45 tiles
height (screenytiles): 36 tiles
tileDim:               32 px
total:                 1440 x 1152 px
```

### Tileset
```
Imagen:      512 x 128 px
Tiles:       16 columnas x 4 filas = 64 tiles
Tamaño:      32 x 32 px cada tile
Formato:     RGBA con fondo transparente
```

### Tile indices usados
| Índice | Tile |
|--------|------|
| 0 | Suelo tech (oscuro con grid) |
| 1 | Suelo con glow neon azul |
| 2 | Pared oscura con strip neon |
| 3 | Pared con panel dorado |
| 4 | Servidor rack |
| 5 | Pantalla holográfica |
| 6 | Pantalla con gráfico de barras |
| 7 | Escritorio con monitor |
| 8 | Silla |
| 9 | Cables bundle |
| 10 | Planta decorativa |
| 11 | Quantum core (hexágono) |
| 12 | Portal / Energy core |
| 20 | Dept wall: Agent Orchestration (neon azul) |
| 21 | Dept wall: App Factory (verde) |
| 22 | Dept wall: Data & Analytics (dorado) |
| 23 | Dept wall: Communication Hub (cyan) |
| 24 | Dept wall: Server Farm (azul) |
| 25 | Dept wall: Learning Hub (púrpura) |
| 26 | Dept wall: Portal / Energy (dorado) |
| 27 | Dept wall: Meeting Room (rojo) |

### Sprites de agentes
```
Imagen:        576 x 128 px
Por agente:    96 x 128 px (3 frames x 4 direcciones)
Frame size:    32 x 32 px
Direcciones:   down, left, right, up
Animaciones:   3 frames por dirección
```

### Layout del spritesheet
```
Columna 0 (f1): Hermes       → x: 0-95
Columna 1 (f2): Dev_01       → x: 96-191
Columna 2 (f3): Marketing_01 → x: 192-287
Columna 3 (f4): Design_01    → x: 288-383
Columna 4 (f5): Investigador → x: 384-479
Columna 5 (f6): OpenClaw_Bot → x: 480-575
```

### Frame data (f1.ts ejemplo)
```typescript
frames: {
  down:  { frame: { x: 0,   y: 0,  w: 32, h: 32 } },
  down2: { frame: { x: 32,  y: 0,  w: 32, h: 32 } },
  down3: { frame: { x: 64,  y: 0,  w: 32, h: 32 } },
  left:  { frame: { x: 0,   y: 32, w: 32, h: 32 } },
  // ...
}
animations: {
  down:  ["down", "down2", "down3"],
  left:  ["left", "left2", "left3"],
  right: ["right", "right2", "right3"],
  up:    ["up", "up2", "up3"],
}
```

---

## 9. AGENTES DEL AI TOWN

### Definición (data/characters.ts)
| # | Nombre | Sprite | Color | Rol |
|---|--------|--------|-------|-----|
| 0 | Hermes | f1 | Azul + Dorado | Orquestador central, responde solo a Sergio |
| 1 | Dev_01 | f2 | Verde + Cyan | Desarrollador senior, código y deploy |
| 2 | Marketing_01 | f3 | Rosa + Rosa claro | Marketing digital, contenido y métricas |
| 3 | Design_01 | f4 | Púrpura + Lila | Diseñador UI/UX, mockups, branding |
| 4 | Investigador | f5 | Dorado + Amarillo | Research, datos, competidores |
| 5 | OpenClaw_Bot | f6 | Gris + Azul neon | Notificador por Telegram |

### Identidades (system prompts en characters.ts)
Cada agente tiene un `identity` con:
- Nombre y rol
- Idioma: español rioplatense
- Emoji característico
- Responsabilidades específicas
- A qué.división pertenece

### Movimiento
- Velocidad: 0.75 tiles/segundo
- Pathfinding: A* en Convex server
- Click-to-move en el mapa
- Animaciones: 3 frames por dirección

---

## 10. EL SCRIPT GENERADOR (generate_tileset.py)

### Qué hace
Script Python (~600 líneas) que genera TODOS los assets cyberpunk de una vez:
1. **Tileset** — 64 tiles de 32x32px con paleta cyberpunk
2. **Sprites** — 6 agentes con 12 frames cada uno
3. **Mapa** — Archivo .compatible con el engine de tiles
4. **Spritesheet data** — Archivos .ts con posiciones de frames

### Paleta de colores cyberpunk
```
Fondo:        (10, 10, 26)    — casi negro
Suelo:        (30, 30, 60)    — azul oscuro
Suelo neon:   (0, 212, 255)   — azul brillante
Pared:        (20, 20, 50)    — gris azulado
Dorado:       (255, 215, 0)   — dorado brillante
Verde neon:   (0, 255, 80)    — verde brillante
Rojo:         (255, 40, 40)   — rojo alerta
Púrpura:      (180, 100, 255) — violeta
Cyan:         (0, 255, 230)   — cian brillante
```

### Para regenerar
```bash
python generate_tileset.py
```

### Para modificar
Editar las funciones `tile_*()` en el script. Cada función dibuja un tile de 32x32 usando PIL:
- `tile_floor()` — suelo base con grid
- `tile_floor_neon()` — suelo con centro glow
- `tile_wall()` — pared con strip neon
- `tile_server()` — rack de servidores con LEDs
- `tile_screen()` — pantalla con líneas de código
- `tile_quantum()` — hexágono cuántico central
- `tile_portal()` — portal con anillos

---

## 11. PIPELINE DE RENDERIZADO

### Cómo se dibuja el mapa
```
1. PixiStaticMap recibe `map: WorldMap` desde Convex
2. Carga tileset PNG como BaseTexture (NEAREST scaling)
3. Corta en tiles individuales: tiles[x + y * numxtiles]
4. Itera sobre el mapa: for i in range(screenxtiles * screenytiles)
5. Para cada celda (x,y), busca tileIndex en layer[x][y]
6. Crea PIXI.Sprite con el tile correspondiente
7. Posiciona: xPx = x * tileDim, yPx = y * tileDim
```

### Cómo se renderizan los agentes
```
1. Player.tsx busca posición histórica del jugador
2. Convierte tile-space a pixel-space: x = pos.x * tileDim + tileDim/2
3. Character.tsx crea PIXI.Spritesheet desde la imagen
4. Determina dirección del orientation angle
5. Crea AnimatedSprite con la animación de esa dirección
6. Agrega bubbles (thinking 💭, speaking 💬) y activity emoji
```

### Cómo funciona el pathfinding
```
1. Usuario hace click en el mapa
2. PixiGame convierte coordenadas screen → world → tiles
3. Envía input 'moveTo' al servidor Convex
4. Convex ejecuta A* (movement.ts) contra el objmap
5. Retorna path como array de waypoints
6. Player se mueve interpolando posición en cada tick
```

---

## 12. ESTADO ACTUAL Y PROBLEMAS CONOCIDOS

### Lo que FUNCIONA
- Convex local corre en puerto 3210
- Vite corre en puerto 5173
- 6 agentes se crean en la DB
- Agentes se mueven con pathfinding A*
- Tileset cyberpunk se genera con Python
- Mapa del HQ con 8 departamentos
- Sprites de agentes con colores distintos

### Lo que NO funciona / pendiente
1. **VISUAL GRIS**: El juego puede mostrar gris al cargar. Soluciones:
   - Ctrl+F5 (hard refresh)
   - Verificar F12 → Console si hay errores
   - El tileset es muy oscuro — necesita más contraste
   - Puede ser que Convex no esté corriendo (verificar puerto 3210)

2. **CONVEX NO CLOUD**: Solo funciona local. Para producción:
   - `npx convex login` → linking a project en convex.dev
   - `npx convex deploy` → deploy a cloud

3. **AGENTES NO FUNCIONALES**: Se mueven pero no ejecutan tareas reales. Solo socializan y tienen "activities" aleatorias (daydreaming, reading a book, gardening).

4. **TILESET CALIDAD**: Generado con PIL es funcional pero básico. Necesita:
   - Más tiles de detalle
   - Mejor pixel art
   - Animaciones en tiles (agua, luces parpadeantes)

5. **DASHBOARD PANEL**: Panel derecho muestra info básica. Falta:
   - Stats en tiempo real
   - Log de acciones
   - Indicadores de estado (idle/working/error)
   - Gráficos de productividad

6. **VOZ**: No está integrado Vertex AI Live para control por voz

7. **DEPLOY**: No está deployado a producción

### Errores TypeScript (pre-existentes del a16z, no bloqueantes)
```
Game.tsx:77-80 — Type 'number | undefined' (useElementSize puede devolver undefined)
PixiViewport.tsx:26 — 'events' does not exist in IViewportOptions
```
Estos no bloquean el funcionamiento. Vite los ignora.

---

## 13. SHORTCUTS Y HERRAMIENTAS

### Atajos de teclado en el juego
- **Click + Drag**: Mover cámara
- **Scroll**: Zoom in/out
- **Click en agente**: Seleccionar y ver info
- **Click en mapa**: Mover tu personaje (si estás "interacting")

### Botones de la UI
- **Interact**: Unirse al mundo como jugador humano
- **Pantalla Completa**: Fullscreen
- **Ocultar/Mostrar Panel**: Toggle panel derecho
- **Help**: Modal de ayuda

### Convex CLI
```bash
npx convex dev              # Iniciar dev server local
npx convex dev --once       # Push code una vez
npx convex run init         # Inicializar mundo con agentes
npx convex run <function>   # Ejecutar función
npx convex env set KEY VAL  # Setear variable de entorno
npx convex login            # Login a Convex cloud
npx convex deploy           # Deploy a cloud
```

---

## 14. PRÓXIMOS PASOS RECOMENDADOS

### Prioridad ALTA
1. **Resolver visual gris** — Verificar que el tileset carga, mejorar contraste
2. **Conectar Convex cloud** — `npx convex login` para persistencia
3. **Mejorar tileset** — Más tiles, mejor pixel art, más detalle

### Prioridad MEDIA
4. **Agentes funcionales** — Que cada agente ejecute su micro-tarea real
5. **Dashboard stats** — Panel lateral con métricas en tiempo real
6. **Deploy a producción** — Vercel/Railway + Convex cloud

### Prioridad BAJA
7. **Voz** — Vertex AI Live para control por voz
8. **Animaciones** — Tiles animados (agua, luces, humo)
9. **Sonido** — Ambientación sonora cyberpunk
10. **Más agentes** — Expandir de 6 a los 193 originales

---

## 15. CONTACTO Y RECURSOS

- **CEO**: Sergio Palomba
- **Telegram**: @vm1openclaw_bot
- **GitHub**: sergiopalomba05-jpg
- **Convex Dashboard**: https://dashboard.convex.dev
- **GCP Console**: https://console.cloud.google.com/project/aa5fb956-b08a-4e13-869
- **Supabase**: https://gbngjsulhqcwgkqoxozy.supabase.co

---

*Documento generado el 14 de julio de 2026. Última sesión de trabajo.*
*Repo: https://github.com/sergiopalomba05-jpg/quantumhive-algorithmictrading*
*Rama: main*

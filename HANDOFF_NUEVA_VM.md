# QuantumHive Town — Handoff Completo para Nueva VM

## Contexto General
QuantumHive es una empresa de algorithmic trading con 11 divisiones y ~193 agentes. El AI Town es un dashboard visual cyberpunk donde los agentes aparecen como sprites pixel art en un HQ isométrico.

## Stack Tecnológico
- **Frontend**: Vite + React + TypeScript + Tailwind CSS
- **Rendering**: PIXI.js (via @pixi/react) — canvas 2D con viewport drag/zoom
- **Backend**: Convex (realtime DB + serverless functions)
- **LLM**: Vertex AI (Google Cloud) — Gemini 2.5 Flash
- **Assets**: Python/PIL para generar tileset, sprites y mapa

## Repositorios en GitHub
1. **repo principal**: `https://github.com/sergiopalomba05-jpg/quantumhive-algorithmictrading`
   - Rama: `main`
   - Contiene TODO el proyecto incluyendo AI Town
2. **repo viejo (NO usar)**: `https://github.com/sergiopalomba05-jpg/quantumhive` (puede no existir)

## Ubicación del Proyecto
```
quantumhive-algorithmictrading/     ← repo root
└── quantumhive-town/               ← AI Town (subcarpeta del repo)
    ├── quantumhive-town/           ← código del juego (dentro del subrepo)
    │   ├── convex/                 ← backend Convex
    │   ├── src/                    ← React + PIXI frontend
    │   ├── data/                   ← mapa, characters, spritesheets
    │   ├── public/assets/          ← tileset, sprites PNG
    │   └── generate_tileset.py     ← script generador de assets
    └── context/                    ← documentación QuantumHive (CONTEXTO_MAESTRO.md, etc.)
```

**NOTA**: En la VM anterior el proyecto estaba en `D:\quantumhive\` (se copió ahí por falta de espacio en C:). El repo original está en `C:\Users\sergio\Desktop\boveda-obsidian\agencia\motor madre\quantumhive-town\quantumhive-town\`.

## Dependencias del Sistema
- **Node.js** v18+ con npm
- **Python 3.12+** con Pillow (`pip install Pillow`)
- **Git**

## Configuración de Entorno

### .env.local (en quantumhive-town/)
```bash
# Vertex AI (Google Cloud)
LLM_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=project-aa5fb956-b08a-4e13-869
GOOGLE_CLOUD_LOCATION=us-central1
LLM_MODEL=gemini-2.5-flash
LLM_EMBEDDING_MODEL=text-embedding-004

# Convex (se configura con npx convex dev)
CONVEX_DEPLOYMENT=anonymous:anonymous-quantumhive

# URLs locales
VITE_CONVEX_URL=http://127.0.0.1:3210
VITE_CONVEX_SITE_URL=http://127.0.0.1:3211
```

### Variables de entorno en Convex (server-side)
```bash
npx convex env set LLM_PROVIDER vertex
npx convex env set GOOGLE_CLOUD_PROJECT project-aa5fb956-b08a-4e13-869
npx convex env set GOOGLE_CLOUD_LOCATION us-central1
npx convex env set LLM_MODEL gemini-2.5-flash
npx convex env set LLM_EMBEDDING_MODEL text-embedding-004
```

### Credenciales importantes (NO commitear)
- **GCP Project**: `project-aa5fb956-b08a-4e13-869`
- **GCP Service Account**: `557866434489-compute@developer.gserviceaccount.com`
- **Supabase**: `https://gbngjsulhqcwgkqoxozy.supabase.co`
- **Telegram Bot**: `@vm1openclaw_bot` (token: `8900188300:AAFhsZpOLR8TYbbdqChqkUTX28dH-FC2l5Y`)
- **Telegram User ID**: `7787265794`
- **Telegram Group ID**: `-1004435575714`

## Pipeline de Arranque (en nueva VM)

### 1. Clonar e instalar
```bash
git clone https://github.com/sergiopalomba05-jpg/quantumhive-algorithmictrading.git
cd quantumhive-algorithmictrading/quantumhive-town
npm install --legacy-peer-deps
pip install Pillow
```

### 2. Generar assets cyberpunk
```bash
cd quantumhive-town
python generate_tileset.py
```
Esto genera:
- `public/assets/quantumhive-tileset.png` (512x128, 16x4 tiles de 32px)
- `public/assets/agent-sprites.png` (576x128, 6 agentes x 3 frames x 4 dirs)
- `data/quantumhive.js` (mapa 45x36 tiles, column-major)
- `data/spritesheets/f1-f6.ts` (frame data para cada agente)

### 3. Configurar Convex env vars server-side
```bash
npx convex env set LLM_PROVIDER vertex
npx convex env set GOOGLE_CLOUD_PROJECT project-aa5fb956-b08a-4e13-869
npx convex env set GOOGLE_CLOUD_LOCATION us-central1
npx convex env set LLM_MODEL gemini-2.5-flash
npx convex env set LLM_EMBEDDING_MODEL text-embedding-004
```

### 4. Arrancar desarrollo
```bash
# Terminal 1: Convex
npx convex dev

# Terminal 2: Vite
npx vite --host
```
- Convex: `http://localhost:3210`
- Juego: `http://localhost:5173/ai-town/`

### 5. Inicializar mundo
Abrir `http://localhost:5173/ai-town/` — el init crea 6 agentes automáticamente.

## Archivos Clave Modificados

### Archivos NUEVOS creados
| Archivo | Descripción |
|---------|-------------|
| `generate_tileset.py` | Script Python que genera tileset, sprites y mapa |
| `data/quantumhive.js` | Mapa del HQ cyberpunk (reemplaza gentle.js) |
| `public/assets/quantumhive-tileset.png` | Tileset cyberpunk 16x4 tiles |
| `public/assets/agent-sprites.png` | Sprites 6 agentes cyberpunk |
| `public/assets/quantumhive-hq.png` | Preview visual del mapa |
| `WORKFLOW.md` | Instrucciones de setup |
| `AGENTS.md` | Contexto para siguiente agente |
| `PLAN_QUANTUMHIVE_TOWN.md` | Plan de implementación |

### Archivos MODIFICADOS
| Archivo | Cambio |
|---------|--------|
| `data/characters.ts` | 6 agentes (antes 8), textureUrl apunta a agent-sprites.png |
| `data/spritesheets/f1.ts-f6.ts` | Nuevas posiciones de frames en spritesheet cyberpunk |
| `convex/init.ts` | Importa `quantumhive` en vez de `gentle` |
| `convex/util/llm.ts` | Agregado Vertex AI provider |
| `.gitignore` | Agregado __pycache__, convex/_generated |
| `.env.local` | Config Vertex AI + Convex |

### Archivos NO modificados (intactos del a16z)
- `src/components/PixiStaticMap.tsx` — renderer de tiles (usa `layer[x][y]`)
- `src/components/PixiGame.tsx` — game loop y viewport
- `src/components/Game.tsx` — shell UI con panel lateral
- `src/components/Character.tsx` — renderizado de sprites
- `convex/aiTown/` — toda la lógica del juego

## Arquitectura del Rendering

### Formato de datos del mapa (column-major)
```
bgtiles[layer][x][y]   → tile index o -1 si vacío
objmap[layer][x][y]    → tile index de objetos/colisión o -1
```
- `bgtiles[0][x][y]`: suelo (0=floor, 1=floor_neon)
- `objmap[0][x][y]`: paredes y objetos (2=wall, 20-27=dept walls, -1=vacío)
- `objmap[1][x][y]`: mobiliario (servidores, escritorios, etc.)

### Tileset layout (16x4 tiles, 32px cada uno)
```
Fila 0: floor, floor_neon, wall, wall_gold, server, screen, screen_chart, desk, chair, cable, plant, quantum, portal
Fila 1: server, screen, screen_chart, desk, chair, cable, plant, quantum, portal, floor, floor_neon, wall, wall_gold, server, screen, desk
Fila 2: dept walls (orchestration=neon, appfactory=green, analytics=gold, comms=cyan, server=blue, learning=purple, portal=gold, meeting=red)
Fila 3: floor variations
```

### Sprites de agentes (576x128 px)
- 6 columnas (1 por agente) x 4 filas (direcciones)
- Cada agente: 3 frames de 32x32px = 96x128px
- Layout: `[down, down2, down3] [left, left2, left3] [right, right2, right3] [up, up2, up3]`

### Colores de agentes
| Agente | Color Body | Color Accent |
|--------|-----------|--------------|
| Hermes | Azul (0,180,220) | Dorado (255,215,0) |
| Dev_01 | Verde (0,150,80) | Cyan (0,255,180) |
| Marketing_01 | Rosa (180,40,130) | Rosa claro (255,100,200) |
| Design_01 | Púrpura (150,80,220) | Lila (200,140,255) |
| Investigador | Dorado (220,180,0) | Amarillo (255,255,100) |
| OpenClaw_Bot | Gris (80,80,100) | Azul neon (0,212,255) |

## Estado del Proyecto (14 Jul 2026)

### Completado
- [x] Tileset cyberpunk generado (dark + neon azul/dorado)
- [x] 6 sprites de agentes cyberpunk
- [x] Mapa HQ con 8 departamentos + hexagonal central
- [x] Characters.ts actualizado
- [x] Init.ts apuntando a quantumhive.js
- [x] Convex local funcionando
- [x] Agentes creándose y moviéndose en la DB
- [x] Push a GitHub

### Pendiente / Known Issues
- [ ] **VISUAL**: El juego muestra gris — necesita Ctrl+F5 (hard refresh) o verificar que el tileset se carga. El problema es que el tileset es muy oscuro contra el fondo 0x1a1a2e. Los floor tiles usan (30,30,60) que es casi invisible. Verificar con F12 → Console si hay errores.
- [ ] **Convex cloud**: No está linkeado a cloud, solo funciona local. Para production: `npx convex login` → link project.
- [ ] **Agentes funcionales**: Se mueven pero no ejecutan tareas reales. Solo socializan.
- [ ] **Dashboard panel**: Panel lateral muestra info básica. Falta stats en tiempo real.
- [ ] **Voz**: No está integrado Vertex AI Live.
- [ ] **Tileset calidad**: Generado con PIL, es funcional pero básico. Necesita mejor pixel art.
- [ ] **Repo deploy**: El repo `quantumhive-algorithmictrading` es el correcto. NO confundir con `quantumhive`.

### Errores conocidos (no bloqueantes)
- TypeScript: `Type 'number | undefined'` en Game.tsx:77-80 (pre-existente del a16z)
- TypeScript: `'events' does not exist` en PixiViewport.tsx:26 (pre-existente)
- Node assertion: `UV_HANDLE_CLOSING` en Convex CLI (warning, no bloquea)

## Dashboard Visual (Referencia)
La imagen de referencia del dashboard cyberpunk muestra:
- Centro hexagonal "QUANTUMHIVE AI ORCHESTRATION CORE"
- 8 departamentos alrededor:
  1. Agent Orchestration Center (arriba izq)
  2. App Factory (arriba centro)
  3. Data & Analytics Lab (arriba der)
  4. Communication Hub (der)
  5. Server Farm (abajo der)
  6. Learning & Upgrade Hub (abajo centro)
  7. Portal / Energy Core (abajo izq)
  8. Meeting & Strategy Room (izq)
- Estilo: dark + neon azul/dorado, pixel art isométrico
- Agentes en sus oficinas ejecutando tareas

## Herramientas Instaladas
- **Hermes**: v0.18.2 en `%LOCALAPPDATA%\hermes\hermes-agent\`
- **OpenClaw**: v2026.6.11 en `%LOCALAPPDATA%\OpenClaw\`
- **Shortcuts**: `C:\Users\sergio\Desktop\QuantumHive Town.bat`

## Próximos Pasos Recomendados
1. **Resolver visual gris** — Verificar tileset loading, mejorar contraste
2. **Mejorar pixel art** — Tileset más detallado, más tiles
3. **Agentes funcionales** — Conectar a tareas reales de cada división
4. **Dashboard stats** — Panel lateral con métricas en tiempo real
5. **Deploy a producción** — Vercel/Railway + Convex cloud
6. **Voz** — Vertex AI Live para control por voz

# QuantumHive Town — Plan de Implementación

## Visión
Dashboard visual isométrico cyberpunk estilo HQ de empresa tech futuristic.
Dark background + neon azul/dorado. Agentes en oficinas ejecutando tareas reales.

## Estilo Visual (de las imágenes)
- **Paleta**: Negro oscuro (#0a0a1a), azul neon (#00d4ff), dorado (#ffd700), gris oscuro (#1a1a2e)
- **Estilo**: Isométrico, pixel art premium, glow effects
- **Layout**: Hexágono central "QUANTUMHIVE" rodeado de 8 departamentos

## Departamentos (8 áreas)
1. **Agent Orchestration Center** (arriba izq) — Control central de agentes
2. **App Factory** (arriba centro) — Desarrollo de apps
3. **Data & Analytics Lab** (arriba der) — Análisis de datos
4. **Communication Hub** (der) — Comunicaciones
5. **Server Farm** (abajo der) — Infraestructura
6. **Learning & Upgrade Hub** (abajo centro) — Capacitación
7. **Portal / Energy Core** (abajo izq) — Energía/conexiones
8. **Meeting & Strategy Room** (izq) — Reuniones

## Cambios Requeridos

### FASE 1: Tileset Cyberpunk (Archivos a crear/modificar)
- Crear `public/assets/quantumhive-tileset.png` — tileset 32x32 dark/neon
- Crear `public/assets/quantumhive-objects.png` — objetos de oficina
- Modificar `data/gentle.js` → `data/quantumhive.js` — nuevo mapa
- **Herramienta**: Generar tileset con código Python/Canvas o descargar asset pack cyberpunk

### FASE 2: Mapa del HQ
- Diseñar layout isométrico con 8 departamentos + centro hexagonal
- Cada departamento = sala con muebles, pantallas, agentes
- Paredes, suelo tech, cables, servidores, pantallas holográficas
- **Archivo**: `data/quantumhive.js` (reemplaza gentle.js)

### FASE 3: Sprites de Agentes Cyberpunk
- Crear spritesheet de personajes cyberpunk (pixel art 32x32)
- 6 agentes: Hermes, Dev_01, Marketing_01, Design_01, Investigador, OpenClaw_Bot
- Cada uno con color/style distinto
- **Archivos**: `data/spritesheets/` + `public/assets/agent-sprites.png`

### FASE 4: UI Dashboard
- Panel lateral con stats de agentes en tiempo real
- Indicadores de actividad (idle, working, error)
- Log de acciones recientes
- **Archivos**: `src/components/Game.tsx`, `src/components/PlayerDetails.tsx`

### FASE 5: Agentes Funcionales
- Conectar cada agente a su división real
- Mostrar tarea actual en bubble sobre el personaje
- Ejecutar micro-tasks reales (no solo socializar)
- **Archivos**: `data/characters.ts`, `convex/aiTown/`

## Archivos Clave del Pipeline Actual
| Archivo | Función |
|---------|---------|
| `data/gentle.js` | Mapa actual (reemplazar) |
| `public/assets/gentle-obj.png` | Tileset actual (reemplazar) |
| `public/assets/32x32folk.png` | Sprites agentes (reemplazar) |
| `src/components/PixiStaticMap.tsx` | Renderiza mapa |
| `src/components/Character.tsx` | Renderiza personajes |
| `src/components/Game.tsx` | Canvas principal |
| `src/components/PixiViewport.tsx` | Cámara/zoom |
| `data/characters.ts` | Definición agentes |

## Orden de Ejecución
1. ~~Analizar código actual~~ ✅
2. Generar tileset cyberpunk (Python/PIL o asset pack)
3. Crear mapa del HQ con departamentos
4. Crear sprites de agentes cyberpunk
5. Actualizar gentle.js → quantumhive.js
6. Probar renderizado
7. Agregar dashboard panel
8. Conectar agentes a tareas reales

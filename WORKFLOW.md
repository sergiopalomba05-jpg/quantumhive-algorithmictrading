# QuantumHive Town — Workflow de Continuación

## Estado Actual (14 Jul 2026)
- **Tileset cyberpunk generado**: `public/assets/quantumhive-tileset.png` (512x128, 64 tiles)
- **Sprites de agentes**: `public/assets/agent-sprites.png` (576x128, 6 agentes cyberpunk)
- **Mapa HQ**: `data/quantumhive.js` (45x36 tiles, 8 departamentos + centro hexagonal)
- **Characters.ts**: Apunta a nuevos sprites (f1-f6)
- **init.ts**: Carga mapa quantumhive en vez de gentle
- **Convex**: Local en puerto 3210 (no linkeado a cloud)
- **Vite**: Corre en puerto 5173

## Para Arrancar en una Nueva Instancia

### 1. Clonar el repo
```bash
git clone https://github.com/sergiopalomba05-jpg/quantumhive-algorithmictrading.git
cd quantumhive-algorithmictrading/quantumhive-town
```

### 2. Instalar dependencias
```bash
npm install --legacy-peer-deps
```
**NOTA**: Si `hnswlib-node` falla, ya está removido del package.json. Si hay errores de peer deps, usar `--legacy-peer-deps`.

### 3. Configurar entorno
```bash
# Copiar .env.local.example a .env.local y configurar:
# - LLM_PROVIDER=vertex
# - GOOGLE_CLOUD_PROJECT=project-aa5fb956-b08a-4e13-869
# - GOOGLE_CLOUD_LOCATION=us-central1
# - LLM_MODEL=gemini-2.5-flash
```

### 4. Arrancar desarrollo
```bash
npm run dev
```
Esto arranca:
- Convex local en `http://localhost:3210`
- Vite en `http://localhost:5173/ai-town/`

### 5. Inicializar base de datos
Abrir `http://localhost:5173/ai-town/` y hacer click en "Interact" para crear los agentes.

## Regenerar Assets
Si querés modificar el tileset o mapa:
```bash
python generate_tileset.py
```
Esto regenera:
- `public/assets/quantumhive-tileset.png`
- `public/assets/agent-sprites.png`
- `data/quantumhive.js`
- `data/spritesheets/f1-f6.ts`

## Estructura del Proyecto
```
quantumhive-town/
├── public/assets/          # Imágenes estáticas
│   ├── quantumhive-tileset.png  # Tileset cyberpunk (16x4 tiles)
│   ├── agent-sprites.png        # Sprites 6 agentes (3 dirs x 3 frames)
│   └── quantumhive-hq.png       # Preview del mapa
├── data/
│   ├── quantumhive.js      # Mapa del HQ (reemplaza gentle.js)
│   ├── characters.ts       # Definición de agentes
│   └── spritesheets/       # Data de frames por agente (f1-f6.ts)
├── convex/
│   ├── init.ts             # Inicialización (usa quantumhive.js)
│   └── aiTown/             # Lógica del juego
├── src/components/         # UI React + PIXI
├── generate_tileset.py     # Script generador de assets
└── .env.local              # Config (no commitear)
```

## Próximos Pasos
1. **Mejorar tileset**: Agregar más tiles, mejor pixel art
2. **Conectar agentes a Convex cloud**: `npx convex login` + deploy
3. **Agentes funcionales**: Que ejecuten tareas reales
4. **Dashboard panel**: Panel lateral con stats en tiempo real
5. **Voz**: Integrar Vertex AI Live para control por voz

## Credenciales (NO commitear)
- **GCP Project**: project-aa5fb956-b08a-4e13-869
- **Supabase**: https://gbngjsulhqcwgkqoxozy.supabase.co
- **Telegram Bot**: @vm1openclaw_bot (token en .env)
- **Hermes**: v0.18.2 en %LOCALAPPDATA%\hermes\hermes-agent\
- **OpenClaw**: v2026.6.11 en %LOCALAPPDATA%\OpenClaw\

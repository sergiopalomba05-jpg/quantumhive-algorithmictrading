# AGENTS.md — QuantumHive Town

## Contexto Rápido
QuantumHive es una empresa de algorithmic trading con 11 divisiones y ~193 agentes.
Este proyecto es el **AI Town** — un dashboard visual cyberpunk donde los agentes aparecen como sprites pixel art en un HQ isométrico.

## Estado del Proyecto
- **Última sesión**: 14 Jul 2026
- **Stack**: Vite + React + PIXI.js + Convex (local) + TypeScript
- **Tileset**: Cyberpunk generado con Python/PIL (`generate_tileset.py`)
- **Mapa**: HQ con 8 departamentos + hexágono central cuántico
- **Agentes**: 6 sprites cyberpunk (Hermes, Dev_01, Marketing_01, Design_01, Investigador, OpenClaw_Bot)
- **Rama**: `main` en `sergiopalomba05-jpg/quantumhive-algorithmictrading`

## Para Continuar
1. Leer `WORKFLOW.md` para instrucciones de setup
2. Leer `PLAN_QUANTUMHIVE_TOWN.md` para el plan de implementación
3. El tileset es funcional pero básico — mejorar pixel art
4. Los agentes se mueven pero no ejecutan tareas reales aún
5. Falta conectar a Convex cloud (solo funciona local)

## Archivos Clave
| Archivo | Qué hace |
|---------|----------|
| `generate_tileset.py` | Genera tileset, sprites, mapa |
| `data/quantumhive.js` | Mapa del HQ |
| `data/characters.ts` | Definición de agentes |
| `convex/init.ts` | Inicialización del mundo |
| `convex/util/llm.ts` | Vertex AI provider |
| `.env.local` | Config (no commitear) |

## Credenciales (en .env.local)
- GCP: `project-aa5fb956-b08a-4e13-869`
- Model: `gemini-2.5-flash`
- Convex: local (no linkeado a cloud)

## Known Issues
- TypeScript errors pre-existentes en Game.tsx y PixiViewport.tsx (no bloquean)
- Convex cloud no está linkeado — solo funciona local
- Los agentes no ejecutan tareas reales, solo se mueven
- El tileset es básico — necesita mejor pixel art

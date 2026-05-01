/**
 * MapGenerator - Motor de Generación Dinámica de Mapas
 * Genera tiles y colisiones basándose en quantum_hierarchy.json
 */

import { v } from 'convex/values';
import { mutation, query } from './_generated/server';
import { api } from './_generated/api';

// Schema de tile
export const tileSchema = {
  x: v.number(),
  y: v.number(),
  width: v.number(),
  height: v.number(),
  tileType: v.string(),
  collision: v.boolean(),
  divisionId: v.optional(v.string()),
  macroId: v.optional(v.string()),
  sprite: v.optional(v.string()),
};

// Tabla de tiles del mapa
export const mapTiles = defineTable({
  ...tileSchema,
  worldId: v.id('worlds'),
});

/**
 * Generar mapa completo desde quantum_hierarchy.json
 */
export const generateMapFromHierarchy = mutation({
  args: {
    worldId: v.id('worlds'),
    hierarchy: v.any(), // quantum_hierarchy.json
  },
  handler: async (ctx, args) => {
    const { worldId, hierarchy } = args;

    // Limpiar tiles existentes
    const existingTiles = await ctx.db
      .query('mapTiles')
      .withIndex('worldId', (q) => q.eq('worldId', worldId))
      .collect();

    for (const tile of existingTiles) {
      await ctx.db.delete(tile._id);
    }

    // Generar tiles desde macrodivisions
    for (const [key, macro] of Object.entries(hierarchy.macrodivisions)) {
      const tile = {
        x: macro.location.x,
        y: macro.location.y,
        width: macro.location.width,
        height: macro.location.height,
        tileType: macro.tileType,
        collision: macro.collision,
        macroId: macro.id,
        divisionId: macro.divisionId,
        sprite: `${macro.tileType}_floor.png`,
        worldId,
      };

      await ctx.db.insert('mapTiles', tile);
    }

    // Generar tiles desde divisions (sobrescribiendo macrodivisions donde corresponda)
    for (const [key, division] of Object.entries(hierarchy.divisions)) {
      const tile = {
        x: division.location.x,
        y: division.location.y,
        width: division.location.width,
        height: division.location.height,
        tileType: division.tileType,
        collision: division.collision,
        divisionId: division.id,
        macroId: division.macroId,
        sprite: `${division.tileType}_floor.png`,
        worldId,
      };

      await ctx.db.insert('mapTiles', tile);
    }

    return { success: true, tilesGenerated: Object.keys(hierarchy.divisions).length };
  },
});

/**
 * Obtener todos los tiles del mapa
 */
export const getMapTiles = query({
  args: {
    worldId: v.id('worlds'),
  },
  handler: async (ctx, args) => {
    const tiles = await ctx.db
      .query('mapTiles')
      .withIndex('worldId', (q) => q.eq('worldId', args.worldId))
      .collect();

    return tiles;
  },
});

/**
 * Obtener tiles de una división específica
 */
export const getDivisionTiles = query({
  args: {
    worldId: v.id('worlds'),
    divisionId: v.string(),
  },
  handler: async (ctx, args) => {
    const tiles = await ctx.db
      .query('mapTiles')
      .withIndex('worldId', (q) => q.eq('worldId', args.worldId))
      .filter((q) => q.eq(q.field('divisionId'), args.divisionId))
      .collect();

    return tiles;
  },
});

/**
 * Obtener tiles de una macrodivisión específica
 */
export const getMacroTiles = query({
  args: {
    worldId: v.id('worlds'),
    macroId: v.string(),
  },
  handler: async (ctx, args) => {
    const tiles = await ctx.db
      .query('mapTiles')
      .withIndex('worldId', (q) => q.eq('worldId', args.worldId))
      .filter((q) => q.eq(q.field('macroId'), args.macroId))
      .collect();

    return tiles;
  },
});

/**
 * Verificar colisión en posición específica
 */
export const checkCollision = query({
  args: {
    worldId: v.id('worlds'),
    x: v.number(),
    y: v.number(),
  },
  handler: async (ctx, args) => {
    const tiles = await ctx.db
      .query('mapTiles')
      .withIndex('worldId', (q) => q.eq('worldId', args.worldId))
      .collect();

    for (const tile of tiles) {
      if (tile.collision) {
        if (
          args.x >= tile.x &&
          args.x <= tile.x + tile.width &&
          args.y >= tile.y &&
          args.y <= tile.y + tile.height
        ) {
          return { collision: true, tile };
        }
      }
    }

    return { collision: false };
  },
});

/**
 * Actualizar tile específico (para reconfiguración dinámica)
 */
export const updateTile = mutation({
  args: {
    tileId: v.id('mapTiles'),
    updates: v.object({
      x: v.optional(v.number()),
      y: v.optional(v.number()),
      width: v.optional(v.number()),
      height: v.optional(v.number()),
      tileType: v.optional(v.string()),
      collision: v.optional(v.boolean()),
      sprite: v.optional(v.string()),
    }),
  },
  handler: async (ctx, args) => {
    const { tileId, updates } = args;

    await ctx.db.patch(tileId, updates);

    return { success: true };
  },
});

/**
 * Agregar nueva división al mapa (Future-Proof)
 */
export const addDivisionToMap = mutation({
  args: {
    worldId: v.id('worlds'),
    division: v.object({
      id: v.string(),
      name: v.string(),
      macroId: v.string(),
      location: v.object({
        x: v.number(),
        y: v.number(),
        width: v.number(),
        height: v.number(),
      }),
      tileType: v.string(),
      collision: v.boolean(),
    }),
  },
  handler: async (ctx, args) => {
    const { worldId, division } = args;

    const tile = {
      x: division.location.x,
      y: division.location.y,
      width: division.location.width,
      height: division.location.height,
      tileType: division.tileType,
      collision: division.collision,
      divisionId: division.id,
      macroId: division.macroId,
      sprite: `${division.tileType}_floor.png`,
      worldId,
    };

    await ctx.db.insert('mapTiles', tile);

    return { success: true };
  },
});

/**
 * Obtener dimensiones totales del mapa
 */
export const getMapDimensions = query({
  args: {
    worldId: v.id('worlds'),
  },
  handler: async (ctx, args) => {
    const tiles = await ctx.db
      .query('mapTiles')
      .withIndex('worldId', (q) => q.eq('worldId', args.worldId))
      .collect();

    if (tiles.length === 0) {
      return { width: 0, height: 0 };
    }

    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;

    for (const tile of tiles) {
      minX = Math.min(minX, tile.x);
      minY = Math.min(minY, tile.y);
      maxX = Math.max(maxX, tile.x + tile.width);
      maxY = Math.max(maxY, tile.y + tile.height);
    }

    return {
      width: maxX - minX,
      height: maxY - minY,
      minX, minY, maxX, maxY,
    };
  },
});

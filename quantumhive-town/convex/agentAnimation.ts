/**
 * Sistema de Animación de Agentes
 * Estados: IDLE, WORKING, ALERT, MEETING
 */

import { v } from 'convex/values';

export const animationState = v.union(
  v.literal('IDLE'),
  v.literal('WORKING'),
  v.literal('ALERT'),
  v.literal('MEETING')
);

export const agentAnimationSchema = {
  agentId: v.string(),
  currentState: animationState,
  targetState: v.optional(animationState),
  transitionAt: v.number(),
  speed: v.number(),
  behavior: v.string(),
  position: v.object({
    x: v.number(),
    y: v.number(),
  }),
  targetPosition: v.optional(v.object({
    x: v.number(),
    y: v.number(),
  })),
};

// Tabla de estados de animación de agentes
export const agentAnimations = defineTable({
  ...agentAnimationSchema,
  lastUpdated: v.number(),
});

/**
 * Configuración de estados de animación
 */
export const animationStates = {
  IDLE: {
    description: 'Agente en reposo, esperando tareas',
    speed: 0,
    behavior: 'static',
    sprite: 'agent_idle',
  },
  WORKING: {
    description: 'Agente trabajando en su escritorio/estación',
    speed: 1,
    behavior: 'stationary_animation',
    sprite: 'agent_working',
  },
  ALERT: {
    description: 'Movimiento rápido a zona de compliance',
    speed: 3,
    behavior: 'emergency_movement',
    sprite: 'agent_alert',
  },
  MEETING: {
    description: 'Agrupación de agentes para colaboración',
    speed: 0.5,
    behavior: 'group_gathering',
    sprite: 'agent_meeting',
  },
};

/**
 * Transición de estado de animación
 */
export const transitionAgentState = mutation({
  args: {
    agentId: v.string(),
    newState: animationState,
    targetPosition: v.optional(v.object({
      x: v.number(),
      y: v.number(),
    })),
  },
  handler: async (ctx, args) => {
    const { agentId, newState, targetPosition } = args;

    const currentState = await ctx.db
      .query('agentAnimations')
      .withIndex('agentId', (q) => q.eq('agentId', agentId))
      .first();

    const stateConfig = animationStates[newState];

    const updateData = {
      agentId,
      currentState: newState,
      targetState: undefined,
      transitionAt: Date.now(),
      speed: stateConfig.speed,
      behavior: stateConfig.behavior,
      position: currentState?.position || { x: 0, y: 0 },
      targetPosition: targetPosition,
      lastUpdated: Date.now(),
    };

    if (currentState) {
      await ctx.db.patch(currentState._id, updateData);
    } else {
      await ctx.db.insert('agentAnimations', updateData);
    }

    return { success: true };
  },
});

/**
 * Obtener estado de animación de un agente
 */
export const getAgentAnimationState = query({
  args: {
    agentId: v.string(),
  },
  handler: async (ctx, args) => {
    const animation = await ctx.db
      .query('agentAnimations')
      .withIndex('agentId', (q) => q.eq('agentId', args.agentId))
      .first();

    return animation;
  },
});

/**
 * Obtener todos los agentes con estado ALERT
 */
export const getAlertAgents = query({
  handler: async (ctx) => {
    const alertAgents = await ctx.db
      .query('agentAnimations')
      .filter((q) => q.eq(q.field('currentState'), 'ALERT'))
      .collect();

    return alertAgents;
  },
});

/**
 * Resetear todos los agentes a IDLE
 */
export const resetAllAgentsToIdle = mutation({
  handler: async (ctx) => {
    const allAnimations = await ctx.db.query('agentAnimations').collect();

    for (const animation of allAnimations) {
      await ctx.db.patch(animation._id, {
        currentState: 'IDLE',
        targetState: undefined,
        transitionAt: Date.now(),
        speed: 0,
        behavior: 'static',
        lastUpdated: Date.now(),
      });
    }

    return { success: true, count: allAnimations.length };
  },
});

/**
 * Agrupar agentes de una división para MEETING
 */
export const gatherDivisionAgents = mutation({
  args: {
    divisionId: v.string(),
    meetingPoint: v.object({
      x: v.number(),
      y: v.number(),
    }),
  },
  handler: async (ctx, args) => {
    const { divisionId, meetingPoint } = args;

    // Obtener agentes de la división (desde quantum_hierarchy)
    const world = await ctx.db.query('worlds').first();
    if (!world) return { success: false };

    const divisionAgents = world.agents.filter((agent) =>
      agent.description.includes(divisionId)
    );

    // Transicionar todos a MEETING
    for (const agent of divisionAgents) {
      await ctx.db.runMutation(api.agentAnimation.transitionAgentState, {
        agentId: agent.id,
        newState: 'MEETING',
        targetPosition: meetingPoint,
      });
    }

    return { success: true, count: divisionAgents.length };
  },
});

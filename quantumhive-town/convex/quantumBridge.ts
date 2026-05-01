/**
 * QuantumBridge - Endpoint para recibir eventos externos de Python/MT5
 * Traduce señales de trading en movimientos de avatares en AI Town
 */

import { v } from 'convex/values';
import { mutation, query } from './_generated/server';
import { api } from './_generated/api';

// Definición de tipos de eventos
export const eventType = v.union(
  v.literal('COMPLIANCE_ALARM'),
  v.literal('D2B_TRIGGER'),
  v.literal('SPLIT_PAYMENT'),
  v.literal('BACKTEST_COMPLETE'),
  v.literal('TRADING_SIGNAL'),
  v.literal('AGENT_STATUS')
);

export const severityLevel = v.union(
  v.literal('CRITICAL'),
  v.literal('HIGH'),
  v.literal('INFO'),
  v.literal('LOW')
);

export const animationState = v.union(
  v.literal('IDLE'),
  v.literal('WORKING'),
  v.literal('ALERT'),
  v.literal('MEETING')
);

// Schema de evento externo
export const externalEventSchema = {
  eventType: eventType,
  severity: severityLevel,
  divisionId: v.string(),
  agentId: v.optional(v.string()),
  timestamp: v.number(),
  data: v.optional(v.any()),
  metadata: v.optional(v.any()),
};

// Tabla de eventos recibidos
export const receivedEvents = defineTable({
  ...externalEventSchema,
  processed: v.boolean(),
  processedAt: v.optional(v.number()),
});

/**
 * Endpoint HTTP para recibir eventos desde Python/MT5
 * Este es el QuantumBridge principal
 */
export const receiveEvent = mutation({
  args: externalEventSchema,
  handler: async (ctx, args) => {
    const { eventType, severity, divisionId, agentId, timestamp, data, metadata } = args;

    // 1. Validar evento contra reglas de negocio
    const validationResult = await ctx.db.runMutation(
      api.quantumBridge.validateBusinessRules,
      { eventType, divisionId, data }
    );

    if (!validationResult.valid) {
      console.error(`Evento rechazado por reglas de negocio: ${validationResult.reason}`);
      return { success: false, reason: validationResult.reason };
    }

    // 2. Determinar acción de animación según evento
    const animationAction = determineAnimationAction(eventType, severity);

    // 3. Guardar evento en base de datos
    const eventId = await ctx.db.insert('receivedEvents', {
      eventType,
      severity,
      divisionId,
      agentId,
      timestamp,
      data,
      metadata,
      processed: false,
    });

    // 4. Ejecutar acción en el mundo (movimiento de agentes)
    if (animationAction) {
      await ctx.db.runMutation(
        api.quantumBridge.executeAgentAction,
        {
          eventId,
          animationState: animationAction.state,
          targetDivision: divisionId,
          targetAgent: agentId,
          speed: animationAction.speed,
          behavior: animationAction.behavior,
        }
      );
    }

    // 5. Enviar notificación push si es CRÍTICO
    if (severity === 'CRITICAL') {
      await ctx.db.runMutation(
        api.quantumBridge.sendCriticalNotification,
        {
          eventType,
          divisionId,
          severity,
          message: generateCriticalMessage(eventType, divisionId, data),
        }
      );
    }

    // 6. Marcar como procesado
    await ctx.db.patch(eventId, { processed: true, processedAt: Date.now() });

    return { success: true, eventId };
  },
});

/**
 * Valida evento contra reglas de negocio (D2B, Compliance 80%, etc.)
 */
export const validateBusinessRules = mutation({
  args: {
    eventType: eventType,
    divisionId: v.string(),
    data: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const { eventType, divisionId, data } = args;

    // Regla de Compliance 80%
    if (eventType === 'COMPLIANCE_ALARM') {
      if (data?.drawdownPercent >= 80) {
        return { valid: true };
      } else {
        return { valid: false, reason: 'Drawdown no alcanza umbral crítico (80%)' };
      }
    }

    // Regla D2B (Drawdown to Breakeven)
    if (eventType === 'D2B_TRIGGER') {
      if (divisionId === 'D1' && data?.breakevenReached) {
        return { valid: true };
      } else {
        return { valid: false, reason: 'Condiciones D2B no cumplidas' };
      }
    }

    // Regla de Split 40/40/20
    if (eventType === 'SPLIT_PAYMENT') {
      if (divisionId === 'D2' || divisionId === 'D16') {
        return { valid: true };
      } else {
        return { valid: false, reason: 'División no aplica split rule' };
      }
    }

    // Eventos válidos por defecto
    return { valid: true };
  },
});

/**
 * Ejecuta acción de animación en agentes
 */
export const executeAgentAction = mutation({
  args: {
    eventId: v.id('receivedEvents'),
    animationState: animationState,
    targetDivision: v.string(),
    targetAgent: v.optional(v.string()),
    speed: v.number(),
    behavior: v.string(),
  },
  handler: async (ctx, args) => {
    const { animationState, targetDivision, targetAgent, speed, behavior } = args;

    // Obtener mundo actual
    const world = await ctx.db.query('worlds').first();
    if (!world) {
      console.error('No hay mundo activo');
      return { success: false };
    }

    // Si se especificó un agente específico
    if (targetAgent) {
      const agent = world.agents.find((a) => a.id === targetAgent);
      if (agent) {
        // Actualizar estado del agente
        await ctx.db.patch(world._id, {
          agents: world.agents.map((a) =>
            a.id === targetAgent
              ? { ...a, animationState, speed, behavior }
              : a
          ),
        });
      }
    } else {
      // Si no se especificó, afectar todos los agentes de la división
      const divisionAgents = world.agents.filter((a) =>
        a.description.includes(targetDivision)
      );

      await ctx.db.patch(world._id, {
        agents: world.agents.map((a) =>
          divisionAgents.find((da) => da.id === a.id)
            ? { ...a, animationState, speed, behavior }
            : a
        ),
      });
    }

    return { success: true };
  },
});

/**
 * Envía notificación push para eventos críticos
 */
export const sendCriticalNotification = mutation({
  args: {
    eventType: eventType,
    divisionId: v.string(),
    severity: severityLevel,
    message: v.string(),
  },
  handler: async (ctx, args) => {
    const { eventType, divisionId, severity, message } = args;

    // Aquí se integraría con servicio de push notifications
    // Por ahora, guardamos en tabla de notificaciones
    await ctx.db.insert('criticalNotifications', {
      eventType,
      divisionId,
      severity,
      message,
      timestamp: Date.now(),
      sent: false,
    });

    return { success: true };
  },
});

/**
 * Query para obtener eventos recientes
 */
export const getRecentEvents = query({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;
    const events = await ctx.db
      .query('receivedEvents')
      .order('desc')
      .take(limit);
    return events;
  },
});

/**
 * Query para obtener estado actual de agentes
 */
export const getAgentsStatus = query({
  handler: async (ctx) => {
    const world = await ctx.db.query('worlds').first();
    if (!world) return [];

    return world.agents.map((agent) => ({
      id: agent.id,
      name: agent.name,
      animationState: agent.animationState,
      speed: agent.speed,
      behavior: agent.behavior,
      position: agent.position,
    }));
  },
});

// Funciones auxiliares

function determineAnimationAction(
  eventType: string,
  severity: string
): { state: string; speed: number; behavior: string } | null {
  const eventTriggers = {
    COMPLIANCE_ALARM: {
      state: 'ALERT',
      speed: 3,
      behavior: 'emergency_movement',
    },
    D2B_TRIGGER: {
      state: 'WORKING',
      speed: 1,
      behavior: 'stationary_animation',
    },
    SPLIT_PAYMENT: {
      state: 'MEETING',
      speed: 0.5,
      behavior: 'group_gathering',
    },
    BACKTEST_COMPLETE: {
      state: 'WORKING',
      speed: 1,
      behavior: 'stationary_animation',
    },
    TRADING_SIGNAL: {
      state: 'WORKING',
      speed: 1.5,
      behavior: 'quick_action',
    },
    AGENT_STATUS: {
      state: 'IDLE',
      speed: 0,
      behavior: 'static',
    },
  };

  return eventTriggers[eventType] || null;
}

function generateCriticalMessage(
  eventType: string,
  divisionId: string,
  data: any
): string {
  const messages = {
    COMPLIANCE_ALARM: `🚨 ALARMA CRÍTICA: Drawdown ${data?.drawdownPercent}% en división ${divisionId}`,
    D2B_TRIGGER: `⚠️ D2B activado en división ${divisionId}`,
    BACKTEST_COMPLETE: `✅ Backtesting completado en división ${divisionId}`,
  };

  return messages[eventType] || `Evento ${eventType} en división ${divisionId}`;
}

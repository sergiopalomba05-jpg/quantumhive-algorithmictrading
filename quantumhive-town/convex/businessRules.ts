/**
 * Reglas de Negocio de QuantumHive
 * Inyecta Regla de Oro D2B y Compliance 80% en sistema de eventos
 */

import { v } from 'convex/values';
import { mutation, query } from './_generated/server';

// Schema de regla de negocio
export const businessRuleSchema = {
  ruleId: v.string(),
  name: v.string(),
  description: v.string(),
  appliesTo: v.array(v.string()),
  conditions: v.array(v.object({
    field: v.string(),
    operator: v.string(),
    value: v.any(),
  })),
  actions: v.array(v.object({
    type: v.string(),
    target: v.string(),
    parameters: v.optional(v.any()),
  })),
  severity: v.union(v.literal('CRITICAL'), v.literal('HIGH'), v.literal('INFO')),
  active: v.boolean(),
};

// Tabla de reglas de negocio
export const businessRules = defineTable({
  ...businessRuleSchema,
  createdAt: v.number(),
  lastTriggered: v.optional(v.number()),
  triggerCount: v.number(),
});

/**
 * Reglas de Oro de QuantumHive
 */
export const quantumBusinessRules = {
  // Regla de Split 40/40/20
  splitRule: {
    ruleId: 'split_40_40_20',
    name: 'Regla de Split 40/40/20',
    description: 'División de ganancias: 40% QuantumHive, 40% Cliente, 20% PropFirm',
    appliesTo: ['D2', 'D16'],
    conditions: [
      { field: 'eventType', operator: 'equals', value: 'SPLIT_PAYMENT' },
      { field: 'totalProfit', operator: 'greaterThan', value: 0 },
    ],
    actions: [
      {
        type: 'CALCULATE_SPLIT',
        target: 'division',
        parameters: { quantumShare: 0.4, clientShare: 0.4, propFirmShare: 0.2 },
      },
      { type: 'ANIMATION_STATE', target: 'agents', parameters: { state: 'MEETING' } },
      { type: 'NOTIFICATION', target: 'mobile', parameters: { severity: 'INFO' } },
    ],
    severity: 'INFO',
    active: true,
  },

  // Regla de Oro D2B (Drawdown to Breakeven)
  d2bRule: {
    ruleId: 'd2b_golden_rule',
    name: 'Regla de Oro D2B',
    description: 'Drawdown to Breakeven - Protección de capital automática',
    appliesTo: ['D1'],
    conditions: [
      { field: 'eventType', operator: 'equals', value: 'D2B_TRIGGER' },
      { field: 'breakevenReached', operator: 'equals', value: true },
      { field: 'currentDrawdown', operator: 'greaterThan', value: 0 },
    ],
    actions: [
      {
        type: 'PROTECT_CAPITAL',
        target: 'trading',
        parameters: { action: 'move_to_breakeven' },
      },
      { type: 'ANIMATION_STATE', target: 'agents', parameters: { state: 'WORKING' } },
      { type: 'NOTIFICATION', target: 'mobile', parameters: { severity: 'HIGH' } },
    ],
    severity: 'HIGH',
    active: true,
  },

  // Regla de Compliance 80%
  complianceRule: {
    ruleId: 'compliance_80_percent',
    name: 'Regla de Compliance 80%',
    description: 'Alerta crítica al 80% de drawdown en challenges/live',
    appliesTo: ['D1', 'D2'],
    conditions: [
      { field: 'eventType', operator: 'equals', value: 'COMPLIANCE_ALARM' },
      { field: 'drawdownPercent', operator: 'greaterThanOrEqual', value: 80 },
    ],
    actions: [
      {
        type: 'EMERGENCY_STOP',
        target: 'trading',
        parameters: { action: 'immediate_halt' },
      },
      { type: 'ANIMATION_STATE', target: 'agents', parameters: { state: 'ALERT' } },
      { type: 'NOTIFICATION', target: 'mobile', parameters: { severity: 'CRITICAL' } },
      {
        type: 'AGENT_MOVEMENT',
        target: 'agents',
        parameters: { destination: 'compliance_zone', speed: 3 },
      },
    ],
    severity: 'CRITICAL',
    active: true,
  },
};

/**
 * Inicializar reglas de negocio en Convex
 */
export const initializeBusinessRules = mutation({
  handler: async (ctx) => {
    const rules = Object.values(quantumBusinessRules);

    for (const rule of rules) {
      const existing = await ctx.db
        .query('businessRules')
        .withIndex('ruleId', (q) => q.eq('ruleId', rule.ruleId))
        .first();

      if (!existing) {
        await ctx.db.insert('businessRules', {
          ...rule,
          createdAt: Date.now(),
          triggerCount: 0,
        });
      }
    }

    return { success: true, rulesInitialized: rules.length };
  },
});

/**
 * Evaluar evento contra reglas de negocio
 */
export const evaluateEventAgainstRules = mutation({
  args: {
    eventType: v.string(),
    divisionId: v.string(),
    data: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const { eventType, divisionId, data } = args;

    // Obtener reglas aplicables a la división
    const applicableRules = await ctx.db
      .query('businessRules')
      .filter((q) =>
        q.and(
          q.eq(q.field('active'), true),
          q.eq(q.field('appliesTo'), divisionId)
        )
      )
      .collect();

    const triggeredRules = [];

    for (const rule of applicableRules) {
      // Verificar condiciones
      const conditionsMet = rule.conditions.every((condition) => {
        const fieldValue = data?.[condition.field];
        return evaluateCondition(fieldValue, condition.operator, condition.value);
      });

      if (conditionsMet) {
        // Ejecutar acciones
        for (const action of rule.actions) {
          await executeAction(ctx, action, data, divisionId);
        }

        // Actualizar estadísticas de la regla
        await ctx.db.patch(rule._id, {
          lastTriggered: Date.now(),
          triggerCount: rule.triggerCount + 1,
        });

        triggeredRules.push(rule);
      }
    }

    return {
      triggered: triggeredRules.length > 0,
      rules: triggeredRules.map((r) => ({ id: r.ruleId, name: r.name })),
    };
  },
});

/**
 * Ejecutar acción específica
 */
async function executeAction(ctx, action, data, divisionId) {
  switch (action.type) {
    case 'ANIMATION_STATE':
      await ctx.db.runMutation(api.agentAnimation.transitionAgentState, {
        agentId: data?.agentId || 'all',
        newState: action.parameters.state,
      });
      break;

    case 'NOTIFICATION':
      if (action.parameters.severity === 'CRITICAL') {
        await ctx.db.runMutation(api.quantumBridge.sendCriticalNotification, {
          eventType: data?.eventType,
          divisionId,
          severity: action.parameters.severity,
          message: generateRuleMessage(action, data),
        });
      }
      break;

    case 'AGENT_MOVEMENT':
      // Implementar movimiento de agentes a zona específica
      break;

    case 'EMERGENCY_STOP':
    case 'PROTECT_CAPITAL':
    case 'CALCULATE_SPLIT':
      // Estas acciones se manejan en el backend de Python/MT5
      // Aquí solo registramos el evento
      break;
  }
}

/**
 * Evaluar condición individual
 */
function evaluateCondition(fieldValue, operator, expectedValue) {
  switch (operator) {
    case 'equals':
      return fieldValue === expectedValue;
    case 'notEquals':
      return fieldValue !== expectedValue;
    case 'greaterThan':
      return fieldValue > expectedValue;
    case 'greaterThanOrEqual':
      return fieldValue >= expectedValue;
    case 'lessThan':
      return fieldValue < expectedValue;
    case 'lessThanOrEqual':
      return fieldValue <= expectedValue;
    default:
      return false;
  }
}

/**
 * Generar mensaje de notificación basado en regla
 */
function generateRuleMessage(action, data) {
  const messages = {
    COMPLIANCE_ALARM: `🚨 ALARMA CRÍTICA: Drawdown ${data?.drawdownPercent}% - Trading detenido por seguridad`,
    D2B_TRIGGER: `⚠️ D2B activado: Capital protegido moviéndose a breakeven`,
    SPLIT_PAYMENT: `💰 Split 40/40/20 ejecutado: Ganancias distribuidas correctamente`,
  };

  return messages[data?.eventType] || `Regla activada: ${action.type}`;
}

/**
 * Obtener estadísticas de reglas
 */
export const getRuleStatistics = query({
  handler: async (ctx) => {
    const rules = await ctx.db.query('businessRules').collect();

    return rules.map((rule) => ({
      ruleId: rule.ruleId,
      name: rule.name,
      triggerCount: rule.triggerCount,
      lastTriggered: rule.lastTriggered,
      active: rule.active,
    }));
  },
});

/**
 * Activar/desactivar regla
 */
export const toggleRule = mutation({
  args: {
    ruleId: v.string(),
    active: v.boolean(),
  },
  handler: async (ctx, args) => {
    const rule = await ctx.db
      .query('businessRules')
      .withIndex('ruleId', (q) => q.eq('ruleId', args.ruleId))
      .first();

    if (!rule) {
      return { success: false, reason: 'Rule not found' };
    }

    await ctx.db.patch(rule._id, { active: args.active });

    return { success: true };
  },
});

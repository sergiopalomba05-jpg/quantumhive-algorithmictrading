# Banco de Decisiones - QuantumHive

## Decisiones Recientes

### 2026-05-01 - Implementación Memoria Persistente GitHub
**Decisión**: Implementar sistema de memoria persistente usando GitHub como backend
**Razón**: Render free plan resetea filesystem cada 24h, pierde memoria de sesiones
**Estado**: Implementado y en testing
**Impacto**: AGI podrá recordar contexto entre sesiones
**Score**: 95/100

### 2026-05-01 - Integración AI Town
**Decisión**: Integrar proyecto AI Town como capa visual de trading
**Razón**: Necesidad de interfaz visual para monitoreo de estrategias
**Estado**: En desarrollo
**Impacto**: Mejor visibilidad de operaciones en tiempo real
**Score**: 80/100

### 2026-05-01 - Fix GitHub Memory Timing
**Decisión**: Hacer guardado de memoria síncrono ANTES de Claude API
**Razón**: Bug donde Claude leía memoria de sesión anterior
**Estado**: Implementado
**Impacto**: Memoria en tiempo real, sin lag
**Score**: 100/100 (crítico)

## Decisiones Pendientes

### Integración de Exchanges
**Tema**: Integrar múltiples exchanges (Binance, Bybit, OKX)
**Prioridad**: Alta
**Proximo Paso**: Investigar APIs y limitaciones de rate
**Fecha Decisión**: 2026-05-15

### Estrategias de Trading
**Tema**: Definir estrategias iniciales (momentum, mean reversion, arbitraje)
**Prioridad**: Alta
**Proximo Paso**: Backtesting en datos históricos
**Fecha Decisión**: 2026-05-20

## Criterios de Decisión
- Impacto en ROI
- Riesgo de implementación
- Tiempo de desarrollo
- Escalabilidad
- Mantenibilidad

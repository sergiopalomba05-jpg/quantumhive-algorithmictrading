# Analisis Automatico de Trades — Errores del Bot

**Fecha:** 2026-04-27 06:42:02.333921
**Total trades:** 29388

## 1. Streaks Perdedores Consecutivos
Encontrados 958 streaks de >3 perdidas consecutivas:
- Desde trade #0: 11 perdidas seguidas
- Desde trade #28: 4 perdidas seguidas
- Desde trade #39: 25 perdidas seguidas
- Desde trade #89: 5 perdidas seguidas
- Desde trade #114: 19 perdidas seguidas

**Fix propuesto:** Revisar entorno — posible sobre-optimizacion o falta de castigo por streaks.

## 4. Metricas Globales
- Winrate: 64.5%
- Wins: 18953 | Losses: 10435
- PnL total: -179091.07
- Avg win: 56.65 | Avg loss: -6.12
- R:R promedio: 1:9.25

## 5. Recomendaciones Automaticas
1. Verificar entorno RL: castigo por streaks perdedores (< -0.05 por trade consecutivo)
2. Ajustar SL: usar ATR(14) x 2.0 en vez de x 1.5 para mas tolerancia
3. Filtro horario: solo operar 14:30-21:30 UTC (apertura NY + sesion)
4. Revisar reward shaping: castigo por inactividad excesiva (-0.01/hora max)

# CONTEXTO MACRO 1 — TRADING CORE

## D1 — Enjambre CFDs/US30

**Estado:** Bot híbrido unificado en entrenamiento activo v3.3.

**Arquitectura 3+1 modelos:**
1. **EntornoMadre** — 14 features (macro H1/H4/D1/W1 + estado). Clasifica QUÉ operar (REVERSIÓN / CONTINUACIÓN / SCALPER). Sin opción "no operar". NY obligatorio.
2. **EntornoReversión** — 15 features, activado por Madre. SL ~150 pts, TP 300-600.
3. **EntornoContinuación** — 17 features, activado por Madre. SL ~150 pts, TP 300-600.
4. **EntornoScalperM5** — 19 features (6 M5 + 7 M1 + 6 estado). AUTÓNOMO. SL ~50 pts (ATR×1.2), TP ~100 pts (ratio 1:2). Trailing stop. Secuencia interés compuesto 3-5 trades, max 2 secuencias/día.

**Pipeline ONNX:** entrenamiento RL → export ONNX opset 14 → EA MQL5 carga modelo → MT5 ejecución en vivo.

**Bot actual (v3.3 — scoring estricto):**
- RSI extremo: <20 compra / >80 venta
- Toque de banda Bollinger obligatorio
- Mecha de reversión >35% del rango de vela
- Máx 1-2 operaciones por día
- Ventana apertura: 4 barras (1h) post apertura NY
- `min_probabilidad=0.85`, `castigo_sin_condiciones=-0.5`

**Archivos clave:**
- `nucleo/entornos/entorno_hibrido_unificado.py` — entorno unificado actual (reemplaza a Madre+Hijos durante fase de simplificación)
- `notebooks/kaggle_unificado_v3.py` — script Kaggle completo para entrenamiento
- `nucleo/indicadores.py`, `nucleo/skills_trading.py` — indicadores y scoring
- `ea_mql5/PlantillaEAHibrido.mq5` — EA MQL5 base

---

## D2 — Gestión de Fondeo y Challenges

**Modelo:** Challenge cliente → cuenta live → split 40/40/20 (QH/Cliente/PropFirm).

**Agentes existentes:**
- `agente_challenge.py` — gestión pase challenge por cliente
- `agente_cuentas_fondeadas.py` — registro, balance, DD, cobro QH
- `agente_cobro_fondeo.py` — cobro cuando PropFirm paga
- `agente_afiliaciones.py` — acuerdos con PropFirms, cupones, comisiones
- `agente_onboarding_cliente.py` — alta de nuevo cliente, asigna bot challenge

---

## D2B — PropFirms y Dispersión de Cuentas

**Infraestructura multi-cuenta:** FTMO, FundingPips, Apex, MyFundedFX.

**Agentes:**
- **Selector de cuenta** — asigna por servidor MT5, firma, riesgo residual
- **Dispersor** — delay/variación únicos por cuenta para evitar detección
- **Monitor DD** — alerta contra límites de firma
- **GestorEnjambreDisperso.mqh** — EA MQL5 de dispersión

**Reglas operativas:**
- Rotación de cuentas (congelamiento por racha perdedora)
- Scheduling diario de asignación
- Retiros sistemáticos post-pago

---

## D7 — PropFirm Propia (Fase 5)

**Objetivo:** Capital de 8 cifras para fondear traders con bots propios.

**Estado:** Planeamiento. Se activa cuando el track record de D1/D2 sea sólido (≥12 meses, PF>1.5, WR>55%).

---

## D16 — Sala de Inversión Colmena

**Concepto:** Hedge fund gamificado. Bots operando cuentas reales visibles en tiempo real.

**Modelo:** Cliente deposita capital → bots trabajan → PnL en vivo → retiro cuando quiere. Comisión 20% QH / 80% cliente.

**Alerta crítica:** Requiere habilitación legal (Macro 6) antes de lanzamiento masivo. Beta cerrada: 5-10 personas.

**Agentes:**
- `agente_pool_capital.py` — tracking capital por cliente, porcentaje pool, PnL proporcional
- `agente_distribucion_ganancias.py` — cálculo 80/20 por sesión, comprobantes
- `agente_sala_visual.py` — métricas en vivo: PnL día, capital total, ops abiertas, equity curve
- `agente_retiros.py` — gestión solicitudes, verificación fondos, transferencia vía API
- `agente_ceo_sala.py` — kill-switch si DD>5% pool, reporte a dashboard ejecutivo

---

## D-NEW Crypto

**Ecosistema crypto para inversores largo plazo.**

- ClaudeCode entrenado en DeFi y análisis on-chain
- Foco: staking, farming, análisis de protocolos, diversificación portafolio
- Separado del enjambre CFDs: distinto riesgo, distinta liquidez, distinta infraestructura
- Estado: Fase 1 — investigación y definición de estrategia. No operativo aún.

---

## D-NEW Sintéticos

**Fase futura.** Binarias y sintéticos como expansión de productos.

- Evaluar viabilidad regulatoria por jurisdicción
- No prioritario hasta consolidar CFDs + Crypto

---

## D-NEW Futuros

**Evaluación e integración futura junto a CFDs.**

- Recomendación actual: arrancar con CFDs (más líquidos, mejor spreads)
- Futuros: Fase 3, cuando capital y regulación lo permitan
- Ventajas: centralización, clearing, menor riesgo contraparte

---

## D-NEW GVCA — Gestión de VPS, Cuentas y Ambientes

**Regla de oro:** 1 bot = 1 grupo de cuentas = 1 VPS distinto = 1 PropFirm distinta.

**Agentes:**
- **Bot-Manager** — por cada bot activo, monitorea estado, logs, métricas, reinicio automático
- **VPS Manager** — provisioning, escalado, rotación, costos
- **Anti-Detección** — fingerprint único por instancia, proxies rotativos, huella mínima
- **Compliance PropFirm** — verifica TOS de cada firma, detecta cambios, ajusta comportamiento bot
- **Cloud e Infraestructura** — orquestación containers, balanceo, failover

**Stack VPS gratuito (Fase 1):**
- Oracle Free Tier — VM perpetua, 2 CPU, 1GB RAM
- GitHub Actions — CI/CD, jobs schedulados
- Google Colab — notebooks de entrenamiento/ backtest
- Replit — prototipado rápido

**Stack VPS pago (escala futura):**
- Contabo — precio/beneficio, VPS dedos desde $6/mes
- Hetzner — Cloud alemana, precios competitivos, GDPR-friendly

---

## Nota Operativa Crítica

**Mientras el bot RL está en desarrollo, el sistema opera con:**
1. EAs mecánicos (reglas duras, sin ML) para sesiones NY
2. Trading manual de Sergio para setups de alta probabilidad
3. Esto construye track record desde YA — no esperamos al bot perfecto para empezar

El bot ONNX cuando esté listo es un **upgrade**, no el punto de partida.

---

*Sistema auto-administrado. QuantumHive v3.0*

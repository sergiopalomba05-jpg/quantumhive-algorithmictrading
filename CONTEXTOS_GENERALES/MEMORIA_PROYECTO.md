# MEMORIA PROYECTO — QUANTUMHIVE ALGORITHMIC TRADING

> **Proposito**: Documento de reanudacion para cualquier IA (Cascade, Claude, GPT-4, Gemini) que entre a trabajar en el proyecto. Resume TODO el estado actual, decisiones arquitecturales, errores conocidos, y proximos pasos. **ACTUALIZAR despues de cada sesion.**

---

## 1. IDENTIDAD DEL PROYECTO

- **Nombre**: QuantumHive Algorithmic Trading
- **Tipo**: Hedge fund gamificado + fabrica de bots de trading algoritmico
- **Activo principal**: US30 (Dow Jones CFD via IC Markets)
- **Estrategia**: Multi-timeframe (M1/M5/M15/H1) con RL (PPO) + ONNX export a MT5
- **Framework**: 11 Macrodivisiones, 186 agentes autonomos (46 activos, 122 planificados, 18 futuro), pipeline end-to-end

---

## 2. ARQUITECTURA — LAS 19 DIVISIONES

| D | Nombre | Estado | Agentes clave |
|---|--------|--------|---------------|
| D1 | Enjambre de Trading | **ENTRENANDO** | Bot hibrido PPO+ONNX, 4 modos (Madre, Reversion, Continuacion, Scalper) |
| D2 | Gestion Fondeo | PLAN | Challenge → live → split 40/40/20 |
| D3 | Grupo Senales | PLAN | Embudo 3 dias gratis → suscripcion |
| D4 | Marketing | PLAN | Contenido auto con resultados reales |
| D5 | Infoproductos | PLAN | Cursos + EAs + datasets + modelos ONNX |
| D6 | High Ticket | PLAN | Venta framework a hedge funds (SaaS) |
| D7 | PropFirm/Broker | **FASE 5** | Fondear traders con bots propios. Target: 8 cifras |
| D8 | Fabrica Bots | PLAN | EAs mecanicos/asistidos/hibridos + tienda |
| D9 | Limpieza | PLAN | Limpieza datos/modelos/logs cada domingo |
| D10 | Web/SEO | PLAN | quantumhive.io + dashboard + A/B testing |
| D11 | Atencion/Ventas | PLAN | Pipeline Lead→Bot→Especialista→Closer |
| D12 | Crecimiento | PLAN | CEO meta, Scout, Clasificador, Entrenadores |
| D13 | Legal | PLAN | Terminos, GDPR, compliance propfirm |
| D14 | Infraestructura | PLAN | Monitoreo, backup, performance |
| D15 | Business Intelligence | PLAN | Dashboard ejecutivo, alertas negocio |
| D16 | Sala Inversion Colmena | **LISTO** | Pool, distribucion, visual, retiros, CEO sala |
| D17 | Ecosistema Partners | **FUTURO** | Partners con salas propias |
| D18 | UCI (Conocimiento IA) | **LISTO** | Video, PDF, CNN, KB vectorial (ChromaDB) |
| D19 | Localizacion Multinacional | **LISTO** | Coordinador, Traductor, Marketing, Soporte, Legal |

---

## 3. ESTADO TECNICO CRITICO

### 3.1 Entrenamiento Bot Hibrido (D1) — ACTUAL
- **Notebook**: `notebooks/kaggle_unificado_v1.py`
- **Dataset**: US30 M1/M5/M15/H1 2022-2024 (IC Markets)
- **Timesteps entrenados**: 1,000,000 (PPO en Kaggle GPU P100)
- **Modelo guardado**: `modelos/modelo_unificado/modelo_final.zip` (+ checkpoints cada 100k)
- **Problema**: EvalCallback en Kaggle **spammeaba** el dataset 2000 veces → 4+ horas sin terminar
- **Fix aplicado**: `evaluar()` ahora carga dataset una sola vez + slices aleatorios de 5000 velas
- **Status**: Fix en local, Kaggle necesita reiniciar sesion para usar codigo nuevo

### 3.2 Backtest Local (scripts/backtest_walkforward.py)
- NUEVO: Backtest cronologico REAL sobre todo el dataset
- Exporta: `trades_historial.csv`, `backtest_equity.csv`, `backtest_resumen.json`
- Objetivo: Ver que errores comete el bot, corregir castigos/recompensas, reentrenar

### 3.3 Errores conocidos (FIXED)
- `z` → `zoom` en `quantumhive_wallstreet.py` (NameError)
- `C_VEIN_GOLD_DIM` → `C_VEIN_GOLD_MID` en `oficina_imperial.py`
- WindowsPath en f-string de `agente_mantenimiento.py`
- `ValueError` parsing fechas en `kaggle_unificado_v1.py` (raw MT5 CSV)
- `low_memory=False` no compatible con `engine="python"` en pandas (evaluar_modelo_local.py)

---

## 4. PIPELINE DE DATOS

```
MT5 Export (CSV raw)
    ↓
preparar_datos.py (parsea <DATE> <TIME> <OPEN>...)
    ↓
datasets/US30_M1_2022_2024.csv
    ↓
Kaggle Dataset (sergiopalomba/quantumhive-fusion)
    ↓
kaggle_unificado_v1.py (entrena PPO 1M steps)
    ↓
modelo_final.zip (+ checkpoints)
    ↓
evaluar_modelo_local.py / backtest_walkforward.py
    ↓
trades_historial.csv (para analisis en MT5 Strategy Tester)
```

---

## 5. GLOSARIO TECNICO CRITICO

- **Entorno Hibrido**: Framework RL que combina multi-timeframe + 4 modos
- **PPO**: Proximal Policy Optimization (algoritmo RL)
- **ONNX**: formato export para MT5 (EA MQL5 carga el modelo)
- **Walk-forward**: backtest cronologico sin look-ahead bias
- **Confluencia**: score 0-160 que valida señales con RSI + Bollinger multi-TF
- **Kill Switch**: apagado de emergencia si drawdown > 3%
- **BBW**: Bollinger Band Width (volatilidad)
- **PB**: Position within Band (posicion relativa en bandas)

---

## 6. PROXIMAS TAREAS (orden prioritario)

### CRITICO (Hoy)
1. [ ] Correr backtest_walkforward.py → obtener trades_historial.csv
2. [ ] Analizar trades: ver por que bot pierde/gana, patrones de error
3. [ ] Corregir entorno: ajustar castigos/recompensas segun analisis
4. [ ] Reentrenar en Kaggle con entorno corregido (2M steps?)

### ALTA (Esta semana)
5. [ ] Implementar ONNX export robusto (stable-baselines3 → onnx)
6. [ ] Crear EA MQL5 que cargue ONNX y opere en MT5 demo
7. [ ] Oficina Imperial Pygame — Parte 2 (abeja central + particulas)
8. [ ] Dashboard v3: agregar metricas de backtest en tiempo real

### MEDIA (Proximas 2 semanas)
9. [ ] D19: Generar landing pages EN/PT/DE para testing
10. [ ] D18: Pipeline end-to-end (video → transcripcion → embeddings)
11. [ ] D13: Generar disclaimers legales por jurisdiccion (USA, DEU, BRA)
12. [ ] D16: Sala Inversion — conectar con datos reales de demo MT5

---

## 7. EQUIPO IA (Sugerido)

| IA | Rol | Memoria | Uso |
|----|-----|---------|-----|
| **Cascade** (Windsurf) | Desarrollo IDE, edicion codigo | Sesion actual + MEMORIA_PROYECTO.md | Coding rapido, debugging, arquitectura |
| **Claude** (Anthropic) | Arquitecto / Socio estrategico | Claude Projects (repo completo subido) | Decisiones estrategicas, revision codigo, documentacion |
| **GPT-4o** (OpenAI) | Research / Marketing / Traducciones | Assistants API + File Search | Research mercados, copy marketing, traducciones D19 |
| **Memoria Vector** (ChromaDB) | KB del proyecto | Embeddings de todo el codigo + docs | Busqueda semantica, "donde esta X?", contexto para IAs |

**Recomendacion**: Crear Claude Project en https://console.anthropic.com/ → subir carpeta QUANTUMHIVE_ALGORITHMICTRADING completa.

---

## 8. DECISIONES ARQUITECTURALES CLAVE

1. **Espanol como idioma base del codigo**: Variables, funciones, clases, comentarios, docstrings. Excepcion: nombres de tecnologias (PPO, ONNX, MT5).
2. **No hardcodear credenciales**: Todo en `.env` (no pusheado a git).
3. **SQLite para persistencia**: Datos estructurados (pool, trades, decisiones CEO). JSON para config/metricas. CSV para datos raw.
4. **Kaggle para GPU**: Entrenamiento PPO gratis. Local para backtest/evaluacion (CPU suficiente).
5. **ONNX como puente**: Entrena en Python/Kaggle → exporta ONNX → EA MQL5 carga en MT5. No dependencia de Python en produccion.
6. **Horario NY obligatorio**: Entorno solo opera 14:00-21:00 UTC (sesion NY). Castigo severo fuera de ventana.
7. **Risk management hardcoded**: Sizing 1%, SL ATRx1.5, max 3 posiciones simultaneas, kill switch DD 3%.

---

## 9. METRICAS OBJETIVO

| Metrica | Target | Actual (1M steps) |
|---------|--------|-------------------|
| Winrate | > 55% | ? (pendiente backtest) |
| Profit Factor | > 1.3 | ? (pendiente backtest) |
| Max Drawdown | < 10% | ? (pendiente backtest) |
| Sharpe (anual) | > 1.0 | ? (pendiente backtest) |
| Ops/dia | 2-5 | ? (pendiente backtest) |

---

## 10. NOTAS DE LA ULTIMA SESION

- **Fecha**: 2026-04-27
- **Sergio descargo modelo ZIP de Kaggle** (modelo_unificado_backup.zip)
- **Descomprimio en**: `modelos/modelo_unificado/`
- **Fixes aplicados**: spam en evaluar(), paths CSV, pandas engine
- **Nuevo**: D19 completo (5 agentes), backtest_walkforward.py, MEMORIA_PROYECTO.md
- **Proximo**: Correr backtest local, analizar errores, reentrenar

---

*Ultima actualizacion: 2026-04-27 | Version memoria: 1.0*
*QuantumHive Algorithmic Trading — Colmena Digital*

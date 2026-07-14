# QUANTUMHIVE — Reporte de Avances 26 Abril 2026

## Resumen Ejecutivo
Pipeline de entrenamiento PPO en ejecución (Kaggle GPU T4). Oficina isométrica Pygame creada con estándar visual "Wall Street del Futuro". Agente de mantenimiento operativo para limpieza de basura.

---

## 1. Entrenamiento Kaggle — En Progreso

| Parámetro | Valor |
|-----------|-------|
| Notebook | `kaggle_unificado_v1.py` |
| GPU | Tesla T4 |
| Timesteps | 1,000,000 |
| Iteraciones completadas | 489 |
| Tiempo transcurrido | ~2 horas |
| Dataset | US30 NY Session 2022-2024 (347,017 filas) |
| Temporalidades | M15 (base) + M5/M1 (confluencia) + H1 (tendencia) |

### Castigos implementados (reward shaping):
- ✅ Castigo inactividad en ventana NY (-0.1/candle)
- ✅ Castigo SEVERO REV contra momentum M1/M5 (-1.5)
- ✅ Boost CONT/SCALP con momentum confirmado (+0.5)
- ✅ Castigo contra tendencia H1 (-0.8)

### Resultado intermedio:
- WR: 50.7% | PnL: -3,019 (Ep 0 eval)
- Estado: evaluación final en curso (celda aún cargando)

---

## 2. Oficina Isométrica Pygame — COMPLETADA

**Archivo:** `visualizador/quantumhive_wallstreet.py` (516 líneas)

### Características:
- Motor isométrico completo con zoom/pan
- Pisos: mármol negro veteado oro + mármol blanco CEO + plata técnica
- Macro-Oficina CEO: plataforma elevada, paredes cristal alpha
- 6 Trading Pods: celdas hexagonales plata/cristal
- Muros de Datos: 3 paneles con candlesticks dinámicos (actualización c/30 frames)
- Núcleo Cuántico Central: emisor de energía + partículas + avispa tecnológica
- 9 Avatares: toro dorado REV, oso plateado CONT, grifón CEO, fénix QA, lobo DevOps, búho Data, avispa núcleo
- Controles: drag pan, scroll zoom, R reset, ESC salir

---

## 3. Agente de Mantenimiento — OPERATIVO

**Archivo:** `scripts/agente_mantenimiento.py`

- Modo dry-run por default (seguro)
- `--execute` para borrado real
- Detecta: `__pycache__`, logs, temporales, duplicados por hash
- Reporte JSON: `scripts/reporte_mantenimiento.json`
- Primer scan: 9 carpetas basura encontradas (~0.19 MB), 2 grupos duplicados detectados (incl. 57MB datasets con mismo hash — revisar)

---

## 4. Dashboard v2 — FINAL (no se toca más)

- Mini mapa con 6 nodos principales
- Emojis para las 15 divisiones
- Badges con animación pulse
- Persistencia `progress.json`

---

## 5. Scripts de Automatización — LISTOS

| Script | Estado |
|--------|--------|
| `pipeline_auto.py` (entrenar→validar→ONNX→MT5) | ✅ |
| `versionar_modelo.py` (Git tags) | ✅ |
| `descargar_kaggle.py` | ✅ |
| `exportar_onnx.py` | ✅ |
| `save_progress.py` | ✅ |
| `agente_mantenimiento.py` | ✅ |

---

## Próximos Pasos

1. Esperar finalización Kaggle → descargar `modelo_final.zip` + `bot_unificado.onnx` + `reporte_unificado.json`
2. Evaluar WR final. Si < 55% → ajustar reward shaping / arquitectura red / timesteps
3. Ejecutar pipeline: `pipeline_auto.py --stage validate`
4. Versionar modelo con tag: `versionar_modelo.py --tag v1.0-us30`
5. Revisar duplicados de datasets (57MB mismos hashes detectados por agente)
6. Ejecutar `--execute` en agente de mantenimiento para limpiar `__pycache__`

---

## Nota para Claude
Kaggle training notebook ya tiene fix para CSVs con formato MT5 crudo (`<DATE>`, `<TIME>`, `<OPEN>`, etc.) vía función `_cargar_csv_kaggle()` que auto-detecta el formato.

Si WR final sigue ~50%, sugerir:
- Red PPO más grande: `net_arch=[256,256,128]`
- 2M timesteps
- Revisar balance de castigos (REV contra momentum puede ser excesivo)
- Añadir bonus por streaks de trades ganadores

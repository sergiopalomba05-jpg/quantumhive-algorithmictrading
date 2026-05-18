# CONTEXTO MACRO 4 — FÁBRICA DE BOTS E INFOPRODUCTOS

## D8 — Fábrica de Bots y Mercado Interno

**Responsabilidad:** Producción, control de calidad, pricing, catálogo y distribución de todos los bots, EAs, indicadores y herramientas de trading generadas por QuantumHive.

### Tipos de Bots

| Tipo | Descripción | Audiencia | Precio referencial |
|------|-------------|-----------|-------------------|
| **Mecánico** | Reglas duras, sin ML. Bollinger + RSI + mecha. Setup visual puro. | Traders manuales que quieren automatizar | $47-$97 |
| **Asistido** | Indicador + alerta visual. El trader decide si ejecuta. | Traders que quieren confirmación | $27-$67 |
| **Híbrido** | RL + CNN + reglas mecánicas. ONNX runtime. | Traders avanzados, propfirms | $197-$497 |
| **Enterprise** | Suite completa Madre+Hijos+Scalper+CNN. | Hedge funds, propfirms, family offices | Licencia SaaS |

### Control de Calidad

- **Backtest automático** obligatorio antes de release: 3 años datos, walk-forward, out-of-sample
- **Aprobación/rechazo** con métricas mínimas: WR>50%, PF>1.3, DD<15% en backtest
- **Staging** en cuenta demo 30 días antes de venta pública
- **Versionado semántico:** MAJOR (cambio arquitectura), MINOR (nueva feature), PATCH (fix)

### Tienda y Distribución

- **Mercado interno:** tienda dentro de la App Colmena (Fase 2)
- **Comunidad Telegram:** acceso anticipado, descuentos, soporte directo
- **Marketplaces externos:** MQL5 Market, TradingView (futuro)

### Agentes Existentes

- `agente_control_calidad.py` — backtest automático, aprobación/rechazo
- `agente_pricing.py` — análisis mercado EAs, precio óptimo
- `agente_catalogo.py` — catálogo productos, descripciones, métricas

---

## D18 — UCI — Unidad de Conocimiento e Inteligencia

**Responsabilidad:** Fábrica de datos de entrenamiento para todos los bots. Automatiza recolección, procesamiento y estructurado de conocimiento desde videos, PDFs y capturas de pantalla.

### Subdivisiones

#### 18A — Recolector Video
- Recibe URLs de YouTube
- Descarga audio con yt-dlp
- Transcribe con Whisper
- Extrae conocimiento estructurado (setups, reglas, gestión)

#### 18B — Procesador PDFs
- Procesa PDFs de `documentos/estrategias/`
- Extrae patrones de entrada, reglas de gestión, ejemplos de setups
- Guarda JSON estructurado con metadatos

#### 18C — Generador CNN
- Captura pantallazos desde MT5 en momentos de señal
- Etiqueta automáticamente según resultado (ganó/perdió)
- Guarda en `datos/imagenes_entrenamiento/validas/` e `invalidas/`

#### 18D — Base de Conocimiento Vectorial
- Indexa todo conocimiento procesado en ChromaDB (Fase 1) o FAISS/Pinecone (escala)
- Responde consultas de otros agentes
- Actualiza base cuando llega material nuevo
- Embeddings semánticos con sentence-transformers

#### 18E — Recolector Traders
- Descarga contenido público de traders con acuerdo CERRADO
- Transcribe con Whisper
- Extrae patrones estructurados
- Indexa en base vectorial
- **Verificación legal previa obligatoria** (Macro 6)

### Dependencias

- `yt-dlp>=2024.1.0`
- `openai-whisper>=20231117`
- `chromadb>=0.4.0`
- `faiss-cpu>=1.7.4`
- `sentence-transformers>=2.2.0`

### Arquitectura de Entrenamiento Visual

- **CNN ResNet18** como capa adicional de confirmación sobre score numérico
- **Generación offline:** `generador_imagenes_entrenamiento.py` produce PNG 224×224 de setups perfectos históricos (score ≥ 80 + ganadores)
- **Entrenamiento Kaggle:** GPU T4, 50 epochs, batch 32, early stopping (5 epochs sin mejora)
- **Exporta a ONNX** igual que modelos RL
- **Integración:** si CNN probabilidad > 0.70 Y score numérico ≥ 60 → operar. Si CNN < 0.50 aunque score ≥ 80 → NO operar (override visual)
- **No bloquea sistema actual:** se activa cuando haya 500+ imágenes

### Agentes Existentes

- `agente_recolector_videos.py` — yt-dlp + Whisper
- `agente_procesador_pdfs.py` — pdfplumber + extracción estructurada
- `agente_generador_cnn.py` — captura + etiquetado automático
- `agente_base_conocimiento.py` — ChromaDB/FAISS + consultas

---

## Responsabilidad Adicional: Cursos Genéricos para Academia

Hasta que Sergio arme su curso personal, la Fábrica de Bots (D8 + D18) es responsable de crear los **cursos genéricos** para la Academia (Macro 9).

**Cursos iniciales a producir:**
1. **Introducción a Bollinger Bands** — teoría, configuración, estrategias básicas
2. **EAs Mecánicos paso a paso** — cómo crear un bot simple en MQL5
3. **Backtesting manual** — lectura de charts, identificación de setups, journaling
4. **Gestión de riesgo para principiantes** — sizing, drawdown, psicología del riesgo
5. **Automatización básica con Python** — scripts simples para trading

**Formato:** Video + PDF + quiz + certificado básico.
**Calidad mínima:** Aprobado por Control de Calidad de D8 (mismos estándares que bots).
**Deadline:** 1 curso por semana durante Fase 1.

---

*Sistema auto-administrado. QuantumHive v3.0*

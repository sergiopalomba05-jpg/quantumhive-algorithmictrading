# CONTEXTO MACRO 4 — FÁBRICA DE BOTS E INFOPRODUCTOS

## FÁBRICA DE CEREBROS — Arquitectura Completa

### Concepto Central

Un cerebro ONNX bien entrenado en UNA estrategia sólida genera docenas de productos. La fábrica se autoalimenta continuamente.

---

### Cerebro Base BB (Bollinger Bands)

Aprende UNA sola cosa excepcionalmente bien:
- Detectar si el precio va a surfear la banda
- Detectar si el precio va a rebotar
- Entrenado visualmente con imágenes reales de setups clasificados por Sergio
- Retroalimentado con errores marcados visualmente por Sergio en backtesting

#### Proceso de Entrenamiento Visual

1. **Sergio recolecta imágenes de setups reales** de MT5
2. **Clasifica manualmente:** surfear / rebotar / inválido
3. **Agente Profesor CNN recibe las imágenes** (ver MACRO 10 Universidad)
4. **Entrena el modelo CNN con esos patrones visuales**
5. **Backtesting visual:** Sergio marca errores con fotos + explicación escrita
6. **Reentrenamiento sobre los errores marcados**
7. **Ciclo hasta que WR > umbral definido**

#### Clones del Cerebro BB

| Cerebro Clon | Activo | Sesión | Descripción |
|--------------|--------|--------|-------------|
| BB_NY_US30_v1 | US30 | Apertura NY | Base original, cerebro BB entrenado en apertura NY |
| BB_NY_NQ100_v1 | NQ100 | Apertura NY | Misma lógica, distinta base de datos NQ100 |
| BB_NY_SP500_v1 | SP500 | Apertura NY | Misma lógica, distinta base de datos SP500 |
| BB_Asia_US30_v1 | US30 | Sesión Asia | Mismo proceso, parámetros BB ajustados a volatilidad Asia |
| BB_Asia_NQ100_v1 | NQ100 | Sesión Asia | Misma lógica, distinta base de datos Asia |
| BB_EU_GER40_v1 | GER40 | Apertura EU | Mismo proceso, entrenado en mercado europeo |

**Cada clon:** misma lógica de surfear/rebotar bandas, distinta base de datos, parámetros ajustados por volatilidad del activo.

---

#### Fuentes Prioritarias para Cerebro BB

**Base de conocimiento permanente:** `universidad/biblioteca/bollinger/`

**Fuentes:**

1. **"Bollinger on Bollinger Bands" — John Bollinger**
   - PDF → Conversor Universal → curriculum BB
   - Libro oficial del creador de Bollinger Bands
   - Fuente primaria de conocimiento

2. **Videos de John Bollinger en YouTube**
   - Recolector → Whisper → PDF → curriculum BB
   - Contenido directo del creador
   - Actualizaciones y técnicas avanzadas

3. **Imágenes de setups reales clasificados por Sergio**
   - Profesor CNN → entrenamiento visual
   - Clasificación: surfear / rebotar / inválido
   - Entrenamiento con datos reales del mercado

4. **Errores marcados en backtesting por Sergio**
   - Retroalimentación continua
   - Fotos + explicación escrita
   - Reentrenamiento sobre errores marcados

**Todo queda en:** `universidad/biblioteca/bollinger/` como base permanente para todos los clones del Cerebro BB actuales y futuros.

---

### Cerebro Base SMC (Smart Money Concepts)

Aprende conceptos avanzados de Smart Money:
- **BOS** (Break of Structure)
- **CHoCH** (Change of Character)
- **FVG** (Fair Value Gap)
- **Liquidity Pools**

#### Estrategias Base Recolectadas por Universidad

- Sensei Trading
- Capital Trading
- ICT Concepts
- Otros frameworks recolectados por Agente Recolector de Conocimiento (MACRO 10)

#### Clones del Cerebro SMC

Aplicable a:
- EURUSD
- GBPUSD
- XAUUSD (Gold)
- Otros pares forex

**Misma lógica de clonación que BB:** cada activo tiene su propia base de datos, parámetros ajustados a volatilidad del par.

---

### Cerebro Base [Estrategia Siguiente]

Mismo proceso para cada nueva estrategia:
1. Universidad provee el conocimiento (videos, PDFs, frameworks)
2. Agente Conversor Universal procesa a PDF estructurado
3. Agente Profesor General extrae conceptos clave
4. Entrenamiento visual con setups clasificados por Sergio
5. Generación de clones por activo y horario
6. Pipeline automático de backtesting y publicación

---

### Pipeline Automático por Cerebro

```
Cerebro sólido aprobado (WR > umbral)
    ↓
Agente Clonador: genera variantes activo/horario
    ↓
Agente Backtester Automático: corre en DB correspondiente
    ↓
Si WR > umbral → aprobado
Si WR < umbral → descartado o ajustar parámetros
    ↓
Agente Publisher: sube a MQL5 Market y otras plataformas
    ↓
Agente Screen Capture: genera posts del backtesting
    ↓
Marketing: publica el contenido en redes
    ↓
Ventas: ingreso pasivo automatizado
```

**Métricas mínimas de aprobación:**
- WR > 50% (umbral a validar con datos reales)
- Drawdown máximo < 20%
- Factor de beneficio > 1.3
- Mínimo 200 trades en backtest

**Test obligatorio antes de publicar:**
- Backtest walk-forward mínimo 2 años
- Test en datos out-of-sample
- Verificación anti-sobreoperación: máximo 3 operaciones por día
- Aprobación final del Agente QA Fábrica

---

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

## D-NUEVA — División de Frameworks Genéricos

### Concepto

El framework de QuantumHive es la base. Extraemos el núcleo reutilizable y lo adaptamos a otros nichos como producto independiente vendible.

### Agente Extractor de Núcleo

**Responsabilidad:** Identifica qué es específico de trading y qué es infraestructura genérica.

**Funciones:**
- Identifica componentes específicos de trading (indicadores, estrategias, MT5)
- Identifica infraestructura genérica reutilizable:
  - Sistema multiagente
  - Orquestador y bus de comunicación
  - Sistema de reputación de agentes
  - Persistencia de contexto
  - Dashboard CEO
  - Sistema de cobros
  - Sistema de afiliados
  - Universidad de agentes
  - Comunicaciones multicanal
- Genera mapa de dependencias entre componentes
- Clasifica componentes: específico vs genérico

**Output:** Lista de componentes genéricos con sus interfaces y dependencias.

---

### Agente Generalizador

**Responsabilidad:** Remueve toda lógica específica de trading y mantiene el núcleo reutilizable.

**Funciones:**
- Remueve lógica específica de trading del código base
- Mantiene el núcleo reutilizable limpio
- Genera `framework_base/` con:
  - Sistema multiagente genérico
  - Bus de comunicación genérico
  - Sistema de reputación genérico
  - Persistencia de contexto genérica
  - Dashboard genérico
  - Sistema de cobros genérico
  - Sistema de afiliados genérico
  - Universidad de agentes genérica
  - Comunicaciones multicanal genéricas
- Documenta interfaces y APIs del framework
- Genera ejemplos de uso

**Output:** `framework_base/` limpio y documentado, listo para adaptación.

---

### Agente Adaptador de Nicho

**Responsabilidad:** Toma framework_base y agrega lógica del nicho específico.

**Funciones:**
- Toma `framework_base/` como punto de partida
- Agrega lógica específica del nicho
- Nichos prioritarios:

**Inmobiliario:**
- Captación de propiedades
- Valuación automática
- Matching comprador-vendedor
- Gestión de visitas
- Contratos digitales

**Recruiting:**
- Screening de candidatos
- Matching candidato-puesto
- Seguimiento de entrevistas
- Gestión de ofertas
- Onboarding automatizado

**E-commerce:**
- Gestión de stock
- Pricing dinámico
- Atención al cliente automatizada
- Gestión de pedidos
- Logística y envíos

**Legal:**
- Gestión de casos
- Generación de documentos
- Gestión de clientes
- Agenda de audiencias
- Facturación por horas

**Salud:**
- Gestión de turnos
- Seguimiento de pacientes
- Recordatorios automáticos
- Historia clínica digital
- Facturación a obras sociales

- Cada adaptación genera un producto nuevo completo
- Documenta customizaciones específicas del nicho

**Output:** Producto completo por nicho, listo para venta.

---

### Agente Empaquetador

**Responsabilidad:** Genera documentación completa y materiales de venta.

**Funciones:**
- Genera documentación completa del producto
- Manual de uso en español e inglés
- Guía de instalación paso a paso
- Ejemplos de configuración
- Demo funcional del nicho
- Videos de demostración
- FAQ común
- Soporte técnico documentado

**Pricing sugerido:** $500-$5000 por licencia según nicho y complejidad.

---

### Agente Publisher Frameworks

**Responsabilidad:** Sube productos a marketplaces y gestiona contacto directo con empresas.

**Funciones:**
- Sube a marketplaces:
  - Gumroad
  - AppSumo
  - GitHub Marketplace
  - Otros marketplaces SaaS
- Gestiona contacto directo con empresas interesadas
- Genera landing pages por producto
- Configura pagos y licencias
- Reporta ventas a MACRO 6B Finanzas
- Gestiona renovaciones de licencias
- Soporte post-venta automatizado

**Integración:** Conectado con MACRO 3 Marketing para promoción y MACRO 6B Finanzas para facturación.

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

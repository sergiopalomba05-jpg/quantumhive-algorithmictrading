# QuantumHive — Trading Algorítmico Enterprise

QuantumHive es una empresa de trading algorítmico de alto nivel que gestiona grandes capitales de inversores institucionales y privados. Cada línea de código está a la altura de ese estándar: cero errores, cero placeholders, documentación de nivel enterprise.

## 7 Divisiones QuantumHive

### DIVISION 1 — Enjambre de Trading (AHORA)
- **Bot Madre** (14 features, macro H1/H4/D1/W1): clasifica QUÉ operar — Reversión, Continuación o Scalper. SIEMPRE opera en sesión NY.
- **Bot Reversión** (SL ~150 pts, TP 300-600): entradas en bandas, RSI extremo.
- **Bot Continuación** (SL ~150 pts, TP 300-600): surfeo de tendencia, BBW expansión.
- **Bot Scalper M5+M1** (SL ~50 pts, TP ~100 pts, ratio 1:2): interés compuesto 3-5 trades, trailing stop, max 2 secuencias/día.
- **Agentes**: Risk Manager · Compliance · Recolector (todos los TF: M1/M5/M15/H1/H4/D1/W1) · Entrenador · Auditoría · Reportero · Optimizador.

### DIVISION 2 — Gestión de Fondeo (FASE 2)
- **Modelo**: Challenge GRATIS → cuenta live → split 50/50 con inversor.
- **Agentes**: Gestor cuentas · Asignador bots · Reportero cliente · Compliance FTMO · Auditoría inmutable de operaciones.

### DIVISION 3 — Grupo de Señales (FASE 2)
- **Embudo**: señales gratis 7 días → suscripción semanal → Colmena (acceso a bots).
- **Agentes**: Publicador señales Telegram · Conversor · Gestor suscripciones (Stripe/MercadoPago) · Embudo hacia División 2.

### DIVISION 4 — Marketing y Captación (FASE 2)
- Contenido automático con resultados reales del enjambre.
- **Agentes**: Contenido Instagram · Viral/SEO · Captación DMs · Cierre ventas automático · CRM con pipeline de conversión completo.

### DIVISION 5 — Productos y Afiliados (FASE 3)
- **5A — Infoproductos**: Cursos creados por agentes IA (Claude API): "Crear bots IA para trading", "Sistema Bollinger profesional", "Pasar challenges de fondeo", "Trading algorítmico desde cero". Publicados en Hotmart/Udemy/Teachable. Red de afiliados con comisiones automáticas.
- **5B — Software**: EAs híbridos (EA+ONNX) entrenados listos para usar, EAs 100% IA por activo, EAs clásicos Bollinger, scripts MQL5, datasets etiquetados, modelos ONNX pre-entrenados, herramientas de backtesting. Marketplace propio + MQL5 Market.
- **Agentes**: Creador infoproductos · Publicador Hotmart · Marketplace productos · Afiliados (tracking + comisiones) · Soporte productos.

### DIVISION 6 — High Ticket Enterprise (FASE 4)
- Venta del framework QuantumHive completo a empresas.
- Licencia mensual SaaS del framework, bots custom para hedge funds y prop firms, consultoría de automatización de trading, soporte técnico dedicado.
- **Agentes**: Enterprise sales · Gestor licencias · Soporte técnico · Facturación · Legal.

### DIVISION 7 — PropFirm y Broker (FASE 5)
- QuantumHive PropFirm: fondea traders con los propios bots.
- Después: broker regulado con infraestructura completa.
- Capital objetivo: gestión de 8 cifras.
- Requiere regulación financiera internacional (Seychelles/Vanuatu).

## Stack Técnico

- **Python 3.13**
- **gymnasium** + **stable-baselines3** (RL)
- **torch** + **torchvision** (CNN visual)
- **pandas**, **numpy**, **pyyaml**, **pytz**
- **onnx** + **onnxruntime** (export a MT5)
- **MetaTrader5** Python API
- **APScheduler** (scheduler de agentes)
- **CrewAI** (orquestación de agentes)
- **matplotlib** + **Pillow** + **fpdf2** (reportes)
- **pdfplumber** / **PyPDF2** (lectura de PDFs estrategia)

## Estructura de Carpetas

- `nucleo/`: indicadores, entornos RL (Madre/Reversión/Continuación/Scalper), utilidades, config global, estructura de mercado, analizador M1, orquestador, entrenamiento visual, lector PDFs.
- `bots/`: configuraciones por tipo (challenge/live/enjambre) y por estrategia.
- `automatizacion/`: agentes (auditoría, compliance, optimizador, recolector), orquestación, scheduler.
- `ea_mql5/`: plantillas y EAs híbridos ONNX para MetaTrader 5.
- `registro/`: logs append-only SHA256, auditoría, reportes mensuales.
- `marketing/`: contenido, publicación, campañas, CRM.
- `documentos/`: PDFs de estrategia para Bot Madre y CrewAI.
- `datos/`: históricos y en vivo descargados desde MT5.

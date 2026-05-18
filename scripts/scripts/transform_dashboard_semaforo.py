"""
Transforma quantumhive_dashboard_v2.html para agregar:
  - Semaforo de eficiencia (rojo/naranja/verde) en cada agente/item
  - Descripcion expandible al hacer click en cada item
  - Division header dot refleja estado agregado
"""

import re
from pathlib import Path

RAIZ = Path("C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING")
HTML = RAIZ / "dashboard" / "quantumhive_dashboard_v2.html"

# Descripciones por item (basado en conocimiento del proyecto)
DESCRIPCIONES = {
    # D1
    "Cerebro Unificado US30": "Agente principal de trading RL. Toma decisiones de compra/venta basado en modelos entrenados con PPO. Es el cerebro operativo que ejecuta en MT5 via ONNX.",
    "Entorno REV+CONT+SCALP": "Entorno de entrenamiento reinforcement learning con 3 modos: Reversion, Continuacion y Scalping. Define rewards, castigos y espacio de acciones.",
    "Dataset US30 M1–H1 (3 años)": "Dataset historico de US30 con timeframes M1 a H1, 3 años de datos. Alimenta el entrenamiento y backtesting.",
    "EA MT5 ONNX loader": "Expert Advisor en MQL5 que carga el modelo ONNX exportado desde Python y opera en cuenta demo/real de MetaTrader 5.",
    "Kill-switch STOP.txt": "Mecanismo de seguridad: si existe archivo STOP.txt, el bot detiene todas las operaciones inmediatamente. Proteccion manual de emergencia.",
    # D2
    "Agente afiliaciones": "Gestiona afiliados de prop firms. Registra referrals, tracking de comisiones y conversiones.",
    "Gestor challenges": "Administra cuentas de challenge/fondeo: monitorea reglas, drawdown, plazos y objetivos.",
    "Cuentas fondeadas": "Tracker de cuentas ya aprobadas por prop firms. Estado, balance, restricciones.",
    "Agente cobro comisiones": "Calcula y factura comisiones de afiliados y partners. Automatiza pagos.",
    "D2B — PropFirms Dispersión": "Division 2B: Estrategia de dispersion de riesgo usando multiples prop firms simultaneamente.",
    "reglas_propfirms.yaml": "Archivo de configuracion con reglas de 4 firmas principales. Limites de drawdown, objetivos, restricciones.",
    "Agente selector cuenta (MT5)": "Selecciona automaticamente la cuenta MT5 optima para operar segun reglas de la prop firm.",
    "Agente dispersor": "Ejecuta operaciones con delay y variacion en diferentes cuentas para evitar deteccion de copytrading.",
    "Agente monitor PropFirm": "Monitorea drawdown en tiempo real: alerta al 60%, 80% y 95% del limite permitido.",
    "GestorEnjambreDisperso.mqh": "Codigo MQL5 del sistema de dispersion. Coordina multiples EAs en paralelo.",
    "Agente gestor rotación cuentas": "Rota capital entre cuentas: congela cuentas perdedoras y activa las ganadoras.",
    # D3
    "Formateador señales": "Formatea señales de trading para envio automatico a grupos de Telegram (Free y VIP).",
    "Gestor grupos Free/VIP": "Administra suscriptores, cobros automaticos y contenido diferenciado por tier.",
    "Cobro suscripción auto": "Procesa pagos recurrentes de suscripciones via Stripe/MercadoPago.",
    "Retención + A/B testing": "Testea diferentes formatos de señales y precios para maximizar retencion de suscriptores.",
    # D4
    "Instagram por división": "Crea y publica contenido de Instagram segmentado por cada division del proyecto.",
    "Generador contenido (IA)": "Usa LLMs (Groq/Gemini) para generar posts, carruseles y captions de marketing.",
    "Publicador auto (Buffer)": "Automatiza publicaciones en redes sociales via API de Buffer o similar.",
    "CRM clientes": "Base de datos de clientes, leads y seguimiento de ventas.",
    "D4 Expandido — Partnerships GTM": "Estrategia Go-To-Market para partnerships con traders y comunidades.",
    "Agente partnerships traders": "Identifica y gestiona partnerships con traders influyentes para co-marketing.",
    "Agente captación seguidores": "Objetivo: adquirir 50 nuevos seguidores calificados por dia via automatizacion.",
    "Agente naming bots": "Genera nombres tecnicos para bots sin infringir marcas ajenas.",
    # D5
    "Creador contenido edu": "Genera cursos, guias y material educativo sobre trading algoritmico.",
    "Publicador Hotmart/Gumroad": "Gestiona productos digitales en plataformas de venta online.",
    "Gestor afiliados": "Programa de afiliados para infoproductos: tracking, comisiones, pagos.",
    "Licencias EA por activo": "Sistema de licenciamiento de EAs por instrumento (US30, XAUUSD, etc.).",
    # D6
    "Licencias framework completo": "Venta de licencias enterprise del framework QuantumHive completo a instituciones.",
    "Contratos institucionales": "Genera y gestiona contratos para clientes enterprise y hedge funds.",
    "White label bots": "Servicio de bots con branding del cliente para brokers y prop firms.",
    # D7
    "PropFirm propia (Fase 5)": "Plan a largo plazo: crear prop firm propia de QuantumHive. Fase 5 del roadmap.",
    "Broker propio (Fase 7)": "Plan a largo plazo: obtener licencia de broker. Fase 7 del roadmap.",
    # D8
    "Control de calidad ONNX": "Valida que modelos ONNX exportados funcionen correctamente y den outputs consistentes.",
    "Catálogo por activo + RR": "Catalogo de bots disponibles clasificados por activo y ratio riesgo/beneficio.",
    "Pricing dinámico": "Ajusta precios de EAs segun demanda, complejidad y rendimiento historico.",
    "Soporte post-venta": "Sistema de tickets y FAQ para clientes de EAs e infoproductos.",
    "Ecosistemas por bot": "Paquete completo por bot: EA ejecutable + PDF de manual + video tutorial.",
    # D9
    "Agente Mantenimiento (script)": "Script automatizado de limpieza de archivos temporales, cache y logs.",
    "Limpieza __pycache__ / logs / temp": "Elimina archivos compilados Python, logs viejos y temporales.",
    "Detección duplicados por hash": "Encuentra archivos duplicados comparando hashes MD5.",
    "Rotación logs": "Archiva y elimina logs antiguos segun politicas de retencion (7/30/90 dias).",
    "Limpieza modelos ONNX viejos": "Elimina versiones obsoletas de modelos ONNX manteniendo las N mas recientes.",
    "Limpieza prompts obsoletos": "Revisa y archiva prompts de LLM que ya no se usan.",
    # D10
    "Analytics web (GA4)": "Implementa Google Analytics 4 para tracking de trafico web.",
    "SEO técnico + contenido": "Optimiza landing pages para motores de busqueda. Keywords, meta tags, velocidad.",
    "A/B testing landing pages": "Testea variantes de landing pages para maximizar conversion.",
    "Diseño contenido (Canva API)": "Genera imagenes de marketing via API de Canva o alternativas.",
    "Next.js dashboard público": "Dashboard publico para clientes y suscriptores. Proyeccion futura.",
    # D11
    "Bot bienvenida + qualifying": "Chatbot de bienvenida que califica leads antes de pasarlos a un humano.",
    "Especialistas por área": "Deriva consultas al especialista correcto segun el tema (trading, tech, billing).",
    "Closer / cobro": "Agente encargado de cerrar ventas y procesar cobros.",
    "Onboarding ventas": "Proceso de induccion para nuevos clientes: configuracion, primeros pasos.",
    "Retención + win-back": "Campanas para recuperar clientes inactivos y retener los activos.",
    # D12
    "CEO estratégico (GPT-4)": "Agente de alto nivel que toma decisiones estrategicas basadas en metricas del negocio.",
    "Agente Entrenador": "Ajusta automaticamente parametros de scripted agents para optimizar rendimiento.",
    "Agente Curriculum": "Genera 5 niveles de escenarios RL progresivos para entrenar el cerebro de trading.",
    "Prompts versionados LLM-assistidos": "Sistema de versionado de prompts con ayuda de LLM para iterar y mejorar.",
    "Scout GitHub / estrategias": "Busca repositorios y papers relevantes para mejorar estrategias de trading.",
    "Clasificador equity curves": "CNN que clasifica curvas de equity como buenas/malas para filtrar estrategias.",
    "Sistema premios / gamificación": "Gamificacion para incentivar usuarios: logros, leaderboards, recompensas.",
    # D13
    "Términos de servicio": "Documento legal base que regula el uso de los servicios de QuantumHive.",
    "Contratos PDF auto-generados": "Genera contratos personalizados automaticamente en formato PDF.",
    "Regulaciones por jurisdicción": "Monitorea y adapta a regulaciones de diferentes paises (USA, UE, Latam).",
    "Compliance PropFirms": "Asegura que las operaciones cumplan reglas de cada prop firm partner.",
    "Privacidad GDPR / CCPA": "Cumplimiento de leyes de privacidad de datos en UE y California.",
    # D14
    "Monitoreo sistema (Uptime)": "Monitorea disponibilidad de servicios y alerta si algo esta caido.",
    "Backup diario automático": "Backup automatico diario de bases de datos y archivos criticos.",
    "Actualizaciones auto-rollback": "Sistema de deployment con rollback automatico si algo falla.",
    "Performance alerts": "Alertas cuando rendimiento de servidores o scripts cae por debajo de umbrales.",
    "Alertas 5 niveles": "Sistema de escalacion de alertas: info, warning, critical, emergency, disaster.",
    # D15
    "Dashboard ejecutivo": "Este panel. Centraliza metricas y estado de todas las divisiones.",
    "Agente Dashboard Central": "Monitorea archivos, detecta eventos y notifica a Sergio (sonido + log).",
    "Métricas trading en vivo": "Muestra PnL, drawdown, winrate y otras metricas en tiempo real.",
    "Métricas negocio (LTV, CAC)": "Metricas de negocio: Lifetime Value, Costo de Adquisicion, churn rate.",
    "Alertas KPIs automáticas": "Alerta cuando KPIs clave se desvian de objetivos.",
    "Reporte inversores": "Reportes periodicos para inversores y stakeholders. Fase 4.",
    "Agente Orquestador LLM": "Selecciona LLM gratuito, genera planes detallados con memoria persistente.",
    "Agente Analizador Tareas": "Evalua pipeline de tareas: dependencias, bloqueos, score ejecutabilidad.",
    "Agente Ejecutor Coordinador": "Coordina ejecucion de tareas aprobadas. Pausa decisiones criticas para aprobacion de Sergio.",
    # D16
    "Agente Pool Capital": "Gestiona pool de capital compartido entre inversores de la sala de inversión.",
    "Agente Distribución 80/20": "Distribuye ganancias: 80% a inversores, 20% a operadores/gestion.",
    "Agente Sala Visual (PnL vivo)": "Dashboard visual en tiempo real con PnL de todas las operaciones del pool.",
    "Agente Retiros (MP/Stripe)": "Procesa retiros de inversores via MercadoPago o Stripe.",
    "Agente CEO Sala (kill-switch 5%)": "CEO de la sala que detiene operaciones si drawdown supera 5%.",
    "Integración MT5 cuenta real": "Conecta la sala de inversion a cuenta real de MetaTrader 5.",
    "Habilitación legal": "Tramites legales para operar sala de inversion colectiva.",
    # D17
    "Infraestructura multi-sala": "Arquitectura para replicar la sala de inversion en otras regiones/paises.",
    "API partner (white-label)": "API para que partners integren QuantumHive en sus plataformas.",
    "Branding por partner": "Personalizacion de marca y colores para cada partner white-label.",
    "Revenue share automático": "Calcula y distribuye revenue share con partners automaticamente.",
    "Track record requerido": "Verifica track record minimo requerido para convertirse en partner.",
    # D18
    "18A — Recolector Videos": "Descarga videos de YouTube educativos sobre trading y los transcribe con Whisper.",
    "18B — Procesador PDFs": "Extrae patrones, reglas y ejemplos de PDFs de estrategias de trading.",
    "18C — Generador CNN": "Genera dataset de imagenes de charts para entrenar CNN clasificadoras.",
    "18D — Base Conocimiento": "Vector database (ChromaDB/FAISS) con embeddings de todo el conocimiento recolectado.",
    "Pipeline end-to-end": "Flujo completo: video → transcripcion → embeddings → consulta.",
    "Dataset ≥500 imágenes CNN": "Dataset minimo de 500 imagenes etiquetadas para entrenar CNNs.",
    "Documentos estrategia en carpeta": "Organiza documentos de estrategia recolectados en estructura de carpetas.",
    # D19
    "19A — Coordinador Idiomas": "Gestiona traducciones a 10 idiomas: ES, EN, PT, DE, FR, ZH, JA, RU, AR.",
    "19B — Traductor Técnico": "Traduce documentacion tecnica, codigo y notebooks manteniendo precision.",
    "19C — Marketing Local": "Adapta campañas de marketing a cultura e idioma de cada mercado.",
    "19D — Soporte Comunitario": "Moderacion y soporte en comunidades de diferentes idiomas.",
    "19E — Legal Compliance": "Adapta terminos legales y disclaimers a cada jurisdiccion.",
    "Idiomas: ZH, JA, RU, AR": "Idiomas adicionales planificados para fase 2 de internacionalizacion.",
    "Landing pages localizadas": "Landing pages especificas para cada mercado geografico.",
    "Disclaimers regulatorios": "Avisos legales adaptados a regulaciones de USA, UE, Latam, Asia.",
    # D20
    "20A — Escritor Manual": "Genera manual de usuario didactico con emojis, ejemplos y FAQ usando Groq LLM.",
    "20B — FAQ Bot": "Chatbot con memoria SQLite que responde dudas sobre QuantumHive usando el manual.",
    "Quick-start guides": "Guías rapidas de 1 pagina por cada division para nuevos usuarios.",
    "Glosario términos trading": "Diccionario simple de terminos tecnicos de trading en lenguaje no tecnico.",
    "Auto-actualización": "Detecta cambios en divisiones/agentes y regenera documentacion automaticamente.",
    "Manual v2.0": "Manual completo del sistema en docs/manual_usuario.md.",
}


def _default_desc(nombre: str) -> str:
    return f"Agente '{nombre}' del ecosistema QuantumHive. Opera autonomamente con supervision humana. Click para ver detalles."


def _badge_a_semaforo(html_item: str) -> str:
    """Extrae clase de badge y retorna clase CSS de semaforo."""
    if 'b-ok' in html_item:
        return 'ef-green'
    if 'b-wip' in html_item:
        return 'ef-yellow'
    if 'b-warn' in html_item:
        return 'ef-orange'
    if 'b-pend' in html_item:
        return 'ef-red'
    return 'ef-yellow'


def _estado_division(items_html: list) -> str:
    """Determina color del semaforo agregado de una division."""
    has_red = any('ef-red' in it for it in items_html)
    has_orange = any('ef-orange' in it for it in items_html)
    has_yellow = any('ef-yellow' in it for it in items_html)
    all_green = all('ef-green' in it for it in items_html)
    if has_red:
        return 'ef-red'
    if has_orange:
        return 'ef-orange'
    if has_yellow:
        return 'ef-yellow'
    if all_green:
        return 'ef-green'
    return 'ef-yellow'


def transformar():
    texto = HTML.read_text(encoding="utf-8")

    # 1. Insertar CSS de semaforos y descripciones (antes del cierre </style>)
    css_extra = """
  /* ===== SEMAFOROS DE EFICIENCIA ===== */
  .ef-dot {
    width: 8px; height: 8px; border-radius: 50%;
    display: inline-block; flex-shrink: 0;
    box-shadow: 0 0 4px currentColor;
    transition: all .3s ease;
  }
  .ef-green  { background: #22c55e; color: #22c55e; }
  .ef-yellow { background: #eab308; color: #eab308; }
  .ef-orange { background: #f97316; color: #f97316; }
  .ef-red    { background: #ef4444; color: #ef4444; }
  .ef-dot.pulse { animation: efPulse 2s infinite; }
  @keyframes efPulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 4px currentColor; }
    50% { opacity: .5; box-shadow: 0 0 12px currentColor; }
  }

  /* Descripcion expandible */
  .item-row {
    display: flex; align-items: flex-start; gap: 8px;
    padding: 7px 0; border-bottom: 1px solid var(--border);
    cursor: pointer; transition: background .15s;
    border-radius: 6px; padding-left: 4px; padding-right: 4px;
  }
  .item-row:hover { background: var(--bg2); }
  .item-row:last-child { border-bottom: 0; }
  .item-main {
    display: flex; align-items: center; justify-content: space-between;
    flex: 1; gap: 8px;
  }
  .item-name { display: flex; align-items: center; gap: 8px; }
  .item-desc {
    max-height: 0; overflow: hidden;
    transition: max-height .3s ease, padding .3s ease, opacity .3s ease;
    opacity: 0; font-size: 11px; color: var(--text2);
    line-height: 1.45; padding: 0 8px 0 20px;
  }
  .item-desc.open {
    max-height: 200px; opacity: 1;
    padding: 6px 8px 8px 20px;
  }
  .item-chevron {
    font-size: 10px; color: var(--text2); transition: transform .2s;
    margin-left: 4px;
  }
  .item-row.open .item-chevron { transform: rotate(90deg); }

  /* Division header semaforo */
  .div-header {
    display: flex; align-items: center; gap: 8px;
    cursor: pointer; user-select: none;
  }
  .div-desc {
    max-height: 0; overflow: hidden;
    transition: max-height .3s ease, opacity .3s ease, padding .3s ease;
    opacity: 0; font-size: 11.5px; color: var(--text2);
    line-height: 1.5; padding: 0 4px;
  }
  .div-desc.open { max-height: 300px; opacity: 1; padding: 8px 4px 4px; }
  .card { transition: border-color .2s; }
  .card:has(.ef-red) { border-left: 3px solid #ef4444; }
  .card:has(.ef-orange) { border-left: 3px solid #f97316; }
  .card:has(.ef-yellow) { border-left: 3px solid #eab308; }
  .card:has(.ef-green):not(:has(.ef-red)):not(:has(.ef-orange)):not(:has(.ef-yellow)) { border-left: 3px solid #22c55e; }
"""
    # Insertar CSS
    texto = texto.replace("</style>", css_extra + "\n</style>")

    # 2. Insertar JS de toggle (antes del cierre del ultimo script)
    js_extra = """
// ── Semaforos & Descripciones Expandibles ─────────────────────────────
document.querySelectorAll('.item-row').forEach(row => {
  row.addEventListener('click', () => {
    const desc = row.querySelector('.item-desc');
    if (desc) {
      desc.classList.toggle('open');
      row.classList.toggle('open');
    }
  });
});
document.querySelectorAll('.div-header').forEach(h => {
  h.addEventListener('click', (e) => {
    const card = h.closest('.card');
    const desc = card.querySelector('.div-desc');
    if (desc) {
      desc.classList.toggle('open');
      h.classList.toggle('open');
    }
  });
});
"""
    # Encontrar el ultimo </script> antes de </body> y insertar
    # Buscaremos el patron del chatbot o el final del script principal
    if "// ── Chatbot Widget" in texto:
        texto = texto.replace("// ── Chatbot Widget", js_extra + "\n// ── Chatbot Widget")
    else:
        texto = texto.replace("</script>\n\n</body>", js_extra + "\n</script>\n\n</body>")

    # 3. Transformar cada .item dentro de cada card
    # Patron: <div class="item">...<div class="item-name">TEXTO</div>...badge...</div>
    def reemplazar_item(match):
        html = match.group(0)
        # Extraer nombre del item
        name_match = re.search(r'<div class="item-name">(.*?)</div>', html, re.DOTALL)
        if not name_match:
            return html
        nombre_raw = re.sub(r'<.*?>', '', name_match.group(1)).strip()
        nombre = nombre_raw.split('—')[-1].strip() if '—' in nombre_raw else nombre_raw

        # Determinar semaforo
        semaforo = _badge_a_semaforo(html)

        # Descripcion
        desc = DESCRIPCIONES.get(nombre, _default_desc(nombre))
        # Si tiene style especial en item-name, preservarlo
        style_match = re.search(r'style="([^"]+)"', name_match.group(1))
        style_attr = f' style="{style_match.group(1)}"' if style_match else ''

        # Reconstruir item con chevron
        # Mantener el badge original
        badge_match = re.search(r'<span class="badge[^"]*">.*?</span>', html)
        badge_html = badge_match.group(0) if badge_match else ''

        nuevo = f'''<div class="item-row" onclick="this.classList.toggle('open');this.querySelector('.item-desc').classList.toggle('open');">
      <span class="ef-dot {semaforo} pulse"></span>
      <div style="flex:1;">
        <div class="item-main">
          <div class="item-name"{style_attr}>{nombre_raw}<span class="item-chevron">▶</span></div>
          {badge_html}
        </div>
        <div class="item-desc">{desc}</div>
      </div>
    </div>'''
        return nuevo

    # Reemplazar todos los items
    texto = re.sub(
        r'<div class="item"[^>]*>.*?</div>\s*(?=<div class="item"|</div>\s*<!--|\Z)',
        reemplazar_item,
        texto,
        flags=re.DOTALL
    )

    # 4. Transformar headers de division para que sean clickeables
    def reemplazar_header(match):
        h3 = match.group(0)
        # Extraer contenido dentro del h3
        inner = re.search(r'<h3>(.*?)</h3>', h3, re.DOTALL)
        if not inner:
            return h3
        contenido = inner.group(1)
        # Determinar semaforo agregado (usar el mismo dot existente)
        dot_match = re.search(r'<span class="dot"[^>]*></span>', contenido)
        dot_html = dot_match.group(0) if dot_match else '<span class="dot" style="background:var(--warn)"></span>'
        # Quitar el dot del contenido
        contenido_sin_dot = re.sub(r'<span class="dot"[^>]*></span>', '', contenido, count=1).strip()

        # Descripcion de la division (extraer de comentario anterior)
        return f'''<h3 class="div-header" onclick="this.classList.toggle('open');this.closest('.card').querySelector('.div-desc').classList.toggle('open');">
        <span class="ef-dot ef-yellow pulse" id="div-dot-{contenido_sin_dot.split()[0]}"></span>{dot_html} {contenido_sin_dot}
      </h3>
      <div class="div-desc">Division del ecosistema QuantumHive. Click en cualquier agente para ver su funcion, rol y estado de eficiencia. <span style="color:var(--text2);font-size:10px;">🔴 Necesita acción · 🟠 Atención · 🟡 En progreso · 🟢 Optimo</span></div>'''

    texto = re.sub(
        r'<h3>\s*<span class="dot"[^>]*>\s*</span>.*?</h3>',
        reemplazar_header,
        texto,
        flags=re.DOTALL
    )

    # 5. Guardar
    HTML.write_text(texto, encoding="utf-8")
    print(f"[OK] Dashboard transformado: {HTML}")


if __name__ == "__main__":
    transformar()

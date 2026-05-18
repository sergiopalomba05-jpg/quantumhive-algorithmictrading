<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QuantumHive — Dashboard Jerárquico</title>
<style>
  :root {
    --bg: #0f172a; --bg2: #1e293b; --bg3: #334155;
    --card: #1e293b; --text: #f8fafc; --text2: #94a3b8; --border: #334155;
    --accent: #534AB7; --accent-hover: #423A9e; --accent-light: #7B73D9;
    --accent2: #00D4AA; --accent2-light: #4DEBC9;
    --ok: #22c55e; --warn: #f59e0b; --danger: #ef4444;
    --info: #3b82f6;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Inter, system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 20px; min-height: 100vh; }
  header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; }
  h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .version { font-size: 12px; color: var(--text2); background: var(--bg2); padding: 4px 12px; border-radius: 12px; border: 1px solid var(--border); }

  /* Progress bar */
  .progress-wrap { margin-bottom: 16px; }
  .progress-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; color: var(--text2); }
  .progress-label strong { color: var(--accent); }
  .progress-bar { height: 8px; background: var(--bg2); border-radius: 4px; overflow: hidden; border: 1px solid var(--border); }
  .progress-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width .4s ease; }
  .progress-legend { display: flex; gap: 14px; margin-top: 6px; font-size: 11px; flex-wrap: wrap; color: var(--text2); }
  .progress-legend span { display: flex; align-items: center; gap: 4px; }

  /* Navegación Jerárquica */
  .nav-level { display: none; animation: slideIn 0.3s ease; }
  .nav-level.active { display: block; }
  @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }

  .breadcrumb { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; font-size: 13px; color: var(--text2); }
  .breadcrumb-item { cursor: pointer; transition: color 0.15s; }
  .breadcrumb-item:hover { color: var(--accent); }
  .breadcrumb-item.active { color: var(--text); font-weight: 600; }
  .breadcrumb-separator { color: var(--border); }

  .btn-back { font-size: 12px; padding: 6px 12px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg2); color: var(--text2); cursor: pointer; transition: .15s; display: inline-flex; align-items: center; gap: 6px; margin-bottom: 16px; }
  .btn-back:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

  /* NIVEL 0: Vista CEO - 9 Macro Burbujas */
  .macro-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
  .macro-card { background: var(--card); border: 1.5px solid var(--border); border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; }
  .macro-card:hover { transform: translateY(-4px); border-color: var(--accent); box-shadow: 0 12px 24px rgba(83, 74, 183, 0.15); }
  .macro-card.critico { border-color: var(--danger); }
  .macro-card.critico::before { content: '🚨'; position: absolute; top: 12px; right: 12px; font-size: 16px; }
  .macro-icon { font-size: 32px; margin-bottom: 12px; display: block; }
  .macro-name { font-size: 16px; font-weight: 700; margin-bottom: 8px; color: var(--text); }
  .macro-desc { font-size: 12px; color: var(--text2); margin-bottom: 12px; line-height: 1.5; }
  .macro-stats { display: flex; gap: 12px; font-size: 11px; color: var(--text2); }
  .macro-stat { display: flex; align-items: center; gap: 4px; }
  .macro-status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
  .macro-status.ok { background: var(--ok); }
  .macro-status.warn { background: var(--warn); }
  .macro-status.danger { background: var(--danger); }

  /* NIVEL 1: Vista Macrodivisión - Tarjetas Divisiones */
  .division-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
  .division-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.2s ease; }
  .division-card:hover { border-color: var(--accent); transform: translateX(4px); }
  .division-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
  .division-name { font-size: 14px; font-weight: 600; color: var(--text); }
  .division-badge { font-size: 10px; padding: 2px 8px; border-radius: 6px; background: var(--bg3); color: var(--text2); }
  .division-desc { font-size: 11px; color: var(--text2); margin-bottom: 12px; line-height: 1.4; }
  .division-meta { display: flex; gap: 16px; font-size: 11px; color: var(--text2); }
  .division-meta span { display: flex; align-items: center; gap: 4px; }

  /* NIVEL 2: Vista División - Descripción y Agentes */
  .division-detail { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
  .division-detail-header { margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
  .division-detail-title { font-size: 20px; font-weight: 700; margin-bottom: 8px; color: var(--text); }
  .division-detail-desc { font-size: 14px; color: var(--text2); line-height: 1.6; }
  .division-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .metric-box { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 12px; text-align: center; }
  .metric-value { font-size: 20px; font-weight: 700; color: var(--accent); }
  .metric-label { font-size: 11px; color: var(--text2); margin-top: 4px; }

  .agents-list { display: flex; flex-direction: column; gap: 10px; }
  .agent-row { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 14px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; justify-content: space-between; }
  .agent-row:hover { border-color: var(--accent); transform: translateX(4px); }
  .agent-info { display: flex; align-items: center; gap: 12px; }
  .agent-avatar { width: 40px; height: 40px; border-radius: 10px; background: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 18px; }
  .agent-name { font-size: 14px; font-weight: 600; color: var(--text); }
  .agent-role { font-size: 11px; color: var(--text2); margin-top: 2px; }
  .agent-status-mini { font-size: 10px; padding: 3px 8px; border-radius: 6px; background: var(--bg3); color: var(--text2); }
  .agent-score-mini { font-size: 12px; font-weight: 600; color: var(--accent); }

  /* NIVEL 3: Vista Agente - Panel Completo */
  .agent-panel { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }
  .agent-panel-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
  .agent-avatar-large { width: 64px; height: 64px; border-radius: 16px; background: linear-gradient(135deg, var(--accent), var(--accent2)); display: flex; align-items: center; justify-content: center; font-size: 28px; }
  .agent-title-group { flex: 1; }
  .agent-name-large { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
  .agent-role-large { font-size: 14px; color: var(--text2); }
  .agent-status-badge { font-size: 12px; padding: 6px 14px; border-radius: 8px; font-weight: 600; text-transform: uppercase; }
  .agent-status-badge.active { background: rgba(34, 197, 94, 0.2); color: var(--ok); }
  .agent-status-badge.inactivo { background: rgba(148, 163, 184, 0.2); color: var(--text2); }
  .agent-status-badge.cuarentena { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

  .score-section { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
  .score-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .score-title { font-size: 14px; font-weight: 600; }
  .score-value { font-size: 24px; font-weight: 700; color: var(--accent); }
  .score-bar { height: 12px; background: var(--bg3); border-radius: 6px; overflow: hidden; }
  .score-fill { height: 100%; border-radius: 6px; transition: width 0.5s ease, background 0.3s ease; }
  .score-fill.rojo { background: var(--danger); }
  .score-fill.naranja { background: var(--warn); }
  .score-fill.azul { background: var(--accent); }
  .score-fill.dorado { background: linear-gradient(90deg, var(--warn), var(--accent2)); }

  .agent-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .agent-metric { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 12px; text-align: center; }
  .agent-metric-value { font-size: 18px; font-weight: 700; color: var(--text); }
  .agent-metric-label { font-size: 11px; color: var(--text2); margin-top: 4px; }

  .agent-description { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
  .agent-description h4 { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--text); }
  .agent-description p { font-size: 13px; color: var(--text2); line-height: 1.6; }

  .agent-actions { display: flex; gap: 10px; flex-wrap: wrap; }
  .btn-action { font-size: 13px; padding: 10px 18px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg2); color: var(--text); cursor: pointer; transition: .15s; font-weight: 500; }
  .btn-action:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
  .btn-action.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
  .btn-action.primary:hover { background: var(--accent-hover); }
  .btn-action.danger { border-color: var(--danger); color: var(--danger); }
  .btn-action.danger:hover { background: var(--danger); color: #fff; }

  /* Responsive */
  @media (max-width: 768px) {
    .macro-grid { grid-template-columns: 1fr; }
    .division-grid { grid-template-columns: 1fr; }
    .agent-panel-header { flex-direction: column; text-align: center; }
    .agent-actions { flex-direction: column; }
    .btn-action { width: 100%; }
  }
</style>
</head>
<body>

<header>
  <div>
    <h1>QuantumHive — Dashboard Jerárquico</h1>
    <p style="font-size:13px;color:var(--text2);margin-top:2px;">9 Macrodivisiones — 25+ Divisiones — Navegación Inteligente</p>
  </div>
  <span class="version">v3.0 — Sistema Jerárquico</span>
</header>

<!-- NIVEL 0: Vista CEO -->
<div class="nav-level active" id="nivel-0">
  <div class="section-title" style="font-size:18px;font-weight:700;margin-bottom:20px;color:var(--accent);">🏢 Vista CEO — 9 Macrodivisiones</div>
  <div class="macro-grid" id="macro-grid">
    <!-- Macro 1: Trading -->
    <div class="macro-card" onclick="irNivel1('MACRO1')">
      <span class="macro-icon">🤖</span>
      <div class="macro-name">MACRO1 — Trading</div>
      <div class="macro-desc">Enjambre CFDs/US30, Fondeo, PropFirms, Crypto</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status ok"></span> 5 divisiones</span>
        <span class="macro-stat">Estado: Activo</span>
      </div>
    </div>
    <!-- Macro 2: Operaciones -->
    <div class="macro-card" onclick="irNivel1('MACRO2')">
      <span class="macro-icon">⚙️</span>
      <div class="macro-name">MACRO2 — Operaciones</div>
      <div class="macro-desc">Limpieza, Crecimiento, Legal, DevOps, BI</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status ok"></span> 4 divisiones</span>
        <span class="macro-stat">Estado: Activo</span>
      </div>
    </div>
    <!-- Macro 3: Marketing -->
    <div class="macro-card" onclick="irNivel1('MACRO3')">
      <span class="macro-icon">📢</span>
      <div class="macro-name">MACRO3 — Marketing</div>
      <div class="macro-desc">Señales, Marketing, Infoproductos, High Ticket, Atención</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status warn"></span> 5 divisiones</span>
        <span class="macro-stat">Estado: Parcial</span>
      </div>
    </div>
    <!-- Macro 4: Fábrica -->
    <div class="macro-card" onclick="irNivel1('MACRO4')">
      <span class="macro-icon">🏭</span>
      <div class="macro-name">MACRO4 — Fábrica</div>
      <div class="macro-desc">Fábrica de Bots, UCI Conocimiento IA</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status ok"></span> 2 divisiones</span>
        <span class="macro-stat">Estado: Activo</span>
      </div>
    </div>
    <!-- Macro 5: Innovación -->
    <div class="macro-card" onclick="irNivel1('MACRO5')">
      <span class="macro-icon">🚀</span>
      <div class="macro-name">MACRO5 — Innovación</div>
      <div class="macro-desc">Ecosistema Partners, Proyectos Futuros</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status warn"></span> 1 división</span>
        <span class="macro-stat">Estado: Futuro</span>
      </div>
    </div>
    <!-- Macro 6: Legal -->
    <div class="macro-card" onclick="irNivel1('MACRO6')">
      <span class="macro-icon">⚖️</span>
      <div class="macro-name">MACRO6 — Legal</div>
      <div class="macro-desc">Compliance, Contratos, Regulación, Habilitaciones</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status warn"></span> 1 división</span>
        <span class="macro-stat">Estado: Pendiente</span>
      </div>
    </div>
    <!-- Macro 7: Colmena -->
    <div class="macro-card critico" onclick="irNivel1('MACRO7')">
      <span class="macro-icon">🐝</span>
      <div class="macro-name">MACRO7 — Colmena</div>
      <div class="macro-desc">Sala Inversión, Comunidad, Jerarquías, Afiliados</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status danger"></span> 1 división</span>
        <span class="macro-stat">Estado: Crítico</span>
      </div>
    </div>
    <!-- Macro 8: Apps -->
    <div class="macro-card" onclick="irNivel1('MACRO8')">
      <span class="macro-icon">📱</span>
      <div class="macro-name">MACRO8 — Apps</div>
      <div class="macro-desc">App CEO, App Colmena, Visual Intelligence</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status warn"></span> 1 división</span>
        <span class="macro-stat">Estado: Futuro</span>
      </div>
    </div>
    <!-- Macro 9: Academia -->
    <div class="macro-card" onclick="irNivel1('MACRO9')">
      <span class="macro-icon">🎓</span>
      <div class="macro-name">MACRO9 — Academia</div>
      <div class="macro-desc">Cursos, Certificaciones, Pipeline Talento</div>
      <div class="macro-stats">
        <span class="macro-stat"><span class="macro-status warn"></span> 1 división</span>
        <span class="macro-stat">Estado: Futuro</span>
      </div>
    </div>
  </div>
</div>

<!-- NIVEL 1: Vista Macrodivisión -->
<div class="nav-level" id="nivel-1">
  <button class="btn-back" onclick="irNivel0()">← Volver a Vista CEO</button>
  <div class="breadcrumb">
    <span class="breadcrumb-item" onclick="irNivel0()">CEO</span>
    <span class="breadcrumb-separator">/</span>
    <span class="breadcrumb-item active" id="breadcrumb-macro">Macro</span>
  </div>
  <div class="section-title" id="titulo-macro" style="font-size:20px;font-weight:700;margin-bottom:20px;color:var(--accent);"></div>
  <div class="division-grid" id="division-grid">
    <!-- Divisiones cargadas dinámicamente -->
  </div>
</div>

<!-- NIVEL 2: Vista División -->
<div class="nav-level" id="nivel-2">
  <button class="btn-back" onclick="irNivel1()">← Volver a Macrodivisión</button>
  <div class="breadcrumb">
    <span class="breadcrumb-item" onclick="irNivel0()">CEO</span>
    <span class="breadcrumb-separator">/</span>
    <span class="breadcrumb-item" onclick="irNivel1()" id="breadcrumb-macro-n2">Macro</span>
    <span class="breadcrumb-separator">/</span>
    <span class="breadcrumb-item active" id="breadcrumb-division">División</span>
  </div>
  <div class="division-detail" id="division-detail">
    <!-- Contenido cargado dinámicamente -->
  </div>
</div>

<!-- NIVEL 3: Vista Agente -->
<div class="nav-level" id="nivel-3">
  <button class="btn-back" onclick="irNivel2()">← Volver a División</button>
  <div class="breadcrumb">
    <span class="breadcrumb-item" onclick="irNivel0()">CEO</span>
    <span class="breadcrumb-separator">/</span>
    <span class="breadcrumb-item" onclick="irNivel1()" id="breadcrumb-macro-n3">Macro</span>
    <span class="breadcrumb-separator">/</span>
    <span class="breadcrumb-item" onclick="irNivel2()" id="breadcrumb-division-n3">División</span>
    <span class="breadcrumb-separator">/</span>
    <span class="breadcrumb-item active" id="breadcrumb-agente">Agente</span>
  </div>
  <div class="agent-panel" id="agent-panel">
    <!-- Contenido cargado dinámicamente -->
  </div>
</div>

<script>
// Datos de las Macrodivisiones
const MACROS = {
  MACRO1: {
    nombre: 'MACRO1 — Trading',
    descripcion: 'Gestión de trading algorítmico, fondeo y prop firms',
    divisiones: [
      { id: 'D1', nombre: 'D1 — Trading IA', desc: 'Enjambre CFDs/US30, bot híbrido unificado', agentes: 8, estado: 'Activo' },
      { id: 'D2', nombre: 'D2 — Fondeo/Challenges', desc: 'Gestión de challenges y cuentas fondeadas', agentes: 4, estado: 'Futuro' },
      { id: 'D2B', nombre: 'D2B — PropFirms Dispersión', desc: 'Gestión dispersa de prop firms', agentes: 3, estado: 'Futuro' },
      { id: 'D7', nombre: 'D7 — PropFirm Propia', desc: 'PropFirm propia (Fase 5)', agentes: 2, estado: 'Futuro' },
      { id: 'D16', nombre: 'D16 — Sala Colmena', desc: 'Capital en vivo, gestión 20/80', agentes: 6, estado: 'Crítico' }
    ]
  },
  MACRO2: {
    nombre: 'MACRO2 — Operaciones',
    descripcion: 'Infraestructura técnica, optimización y mantenimiento',
    divisiones: [
      { id: 'D9', nombre: 'D9 — Limpieza/Mantenimiento', desc: 'The Cleaner, The Optimizer', agentes: 3, estado: 'Activo' },
      { id: 'D12', nombre: 'D12 — Crecimiento/Optimización', desc: 'Sistema de reputación DGCR', agentes: 5, estado: 'Activo' },
      { id: 'D13', nombre: 'D13 — Legal/Compliance', desc: 'Compliance regulatorio', agentes: 2, estado: 'Pendiente' },
      { id: 'D14', nombre: 'D14 — DevOps/Infraestructura', desc: 'Monitoreo, backups, actualizaciones', agentes: 3, estado: 'Pendiente' }
    ]
  },
  MACRO3: {
    nombre: 'MACRO3 — Marketing',
    descripcion: 'Captación, conversión y retención de clientes',
    divisiones: [
      { id: 'D3', nombre: 'D3 — Señales/Telegram', desc: 'Gestión de señales y grupos', agentes: 4, estado: 'Futuro' },
      { id: 'D4', nombre: 'D4 — Marketing/Captación', desc: 'Instagram, contenido, CRM', agentes: 5, estado: 'Futuro' },
      { id: 'D5', nombre: 'D5 — Infoproductos/EAs', desc: 'Cursos, EAs, licencias', agentes: 4, estado: 'Futuro' },
      { id: 'D6', nombre: 'D6 — Enterprise/High Ticket', desc: 'Contratos institucionales', agentes: 2, estado: 'Futuro' },
      { id: 'D11', nombre: 'D11 — Ventas/Atención', desc: 'Soporte, closers, onboarding', agentes: 5, estado: 'Futuro' }
    ]
  },
  MACRO4: {
    nombre: 'MACRO4 — Fábrica',
    descripcion: 'Producción y QA de bots de trading',
    divisiones: [
      { id: 'D8', nombre: 'D8 — Fábrica de Bots', desc: 'Catálogo, QA, tienda', agentes: 4, estado: 'Activo' },
      { id: 'D18', nombre: 'D18 — UCI Conocimiento IA', desc: 'Whisper, base vectorial, recolector', agentes: 5, estado: 'Activo' }
    ]
  },
  MACRO5: {
    nombre: 'MACRO5 — Innovación',
    descripcion: 'Proyectos futuros y ecosistema de partners',
    divisiones: [
      { id: 'D17', nombre: 'D17 — Ecosistema Partners', desc: 'White label, partnerships', agentes: 2, estado: 'Futuro' }
    ]
  },
  MACRO6: {
    nombre: 'MACRO6 — Legal',
    descripcion: 'Marco legal y regulatorio',
    divisiones: [
      { id: 'D13_LEGAL', nombre: 'D13 — Legal/Compliance', desc: 'Contratos, regulaciones, compliance', agentes: 3, estado: 'Pendiente' }
    ]
  },
  MACRO7: {
    nombre: 'MACRO7 — Colmena',
    descripcion: 'Comunidad de inversión y gestión de capital',
    divisiones: [
      { id: 'D16_COLMENA', nombre: 'D16 — Sala Colmena', desc: 'Gestión capital en vivo, comunidad', agentes: 6, estado: 'Crítico' }
    ]
  },
  MACRO8: {
    nombre: 'MACRO8 — Apps',
    descripcion: 'Aplicaciones móviles y visual intelligence',
    divisiones: [
      { id: 'D15', nombre: 'D15 — BI/Dashboard CEO', desc: 'Métricas en vivo, reportes', agentes: 4, estado: 'Activo' },
      { id: 'D19', nombre: 'D19 — Localización/Multinacional', desc: 'Landing pages, disclaimers', agentes: 5, estado: 'Activo' }
    ]
  },
  MACRO9: {
    nombre: 'MACRO9 — Academia',
    descripcion: 'Educación y certificación de traders',
    divisiones: [
      { id: 'D9_ACADEMIA', nombre: 'D9 — Academia Trading', desc: 'Cursos, certificaciones, mentorship', agentes: 4, estado: 'Futuro' }
    ]
  }
};

// Datos de Agentes (ejemplo)
const AGENTES = {
  'D1': [
    { id: 'ag_1', nombre: 'Data Engineer', rol: 'Limpieza + Features', score: 85, estado: 'Activo', modelo: 'claude-sonnet-4-6', tareas_exitosas: 12, tareas_fallidas: 1, ultima_tarea: 'Procesamiento dataset US30' },
    { id: 'ag_2', nombre: 'Strategist', rol: 'Reglas → Reward Shaping', score: 92, estado: 'Activo', modelo: 'claude-opus-4-6', tareas_exitosas: 8, tareas_fallidas: 0, ultima_tarea: 'Optimización reward function' },
    { id: 'ag_3', nombre: 'Trainer PPO', rol: 'Entrena + Exporta ONNX', score: 78, estado: 'Activo', modelo: 'claude-sonnet-4-6', tareas_exitosas: 5, tareas_fallidas: 2, ultima_tarea: 'Entrenamiento 1M steps' },
    { id: 'ag_4', nombre: 'Validator', rol: 'Backtest + GO/NO-GO', score: 70, estado: 'Inactivo', modelo: 'claude-sonnet-4-6', tareas_exitosas: 3, tareas_fallidas: 0, ultima_tarea: 'Validación walk-forward' },
    { id: 'ag_5', nombre: 'Deployer', rol: 'EA MT5 + Live', score: 75, estado: 'Activo', modelo: 'claude-sonnet-4-6', tareas_exitosas: 4, tareas_fallidas: 1, ultima_tarea: 'Deploy EA demo' }
  ]
};

let macroActual = '';
let divisionActual = '';
let agenteActual = '';

// Navegación entre niveles
function irNivel0() {
  ocultarTodosNiveles();
  document.getElementById('nivel-0').classList.add('active');
}

function irNivel1(macroId) {
  macroActual = macroId;
  const macro = MACROS[macroId];
  
  document.getElementById('breadcrumb-macro').textContent = macro.nombre;
  document.getElementById('titulo-macro').textContent = macro.nombre;
  
  // Cargar divisiones
  const grid = document.getElementById('division-grid');
  grid.innerHTML = macro.divisiones.map(div => `
    <div class="division-card" onclick="irNivel2('${div.id}', '${div.nombre}')">
      <div class="division-header">
        <div class="division-name">${div.nombre}</div>
        <span class="division-badge">${div.estado}</span>
      </div>
      <div class="division-desc">${div.desc}</div>
      <div class="division-meta">
        <span>👥 ${div.agentes} agentes</span>
        <span>📊 Score: ${div.estado === 'Activo' ? '85' : '0'}</span>
      </div>
    </div>
  `).join('');
  
  ocultarTodosNiveles();
  document.getElementById('nivel-1').classList.add('active');
}

function irNivel2(divisionId, divisionNombre) {
  divisionActual = divisionId;
  
  document.getElementById('breadcrumb-macro-n2').textContent = MACROS[macroActual].nombre;
  document.getElementById('breadcrumb-division').textContent = divisionNombre;
  
  // Cargar detalle división
  const detalle = document.getElementById('division-detail');
  const agentes = AGENTES[divisionId] || [];
  
  detalle.innerHTML = `
    <div class="division-detail-header">
      <div class="division-detail-title">${divisionNombre}</div>
      <div class="division-detail-desc">Gestión de operaciones, métricas y agentes especializados.</div>
    </div>
    <div class="division-metrics">
      <div class="metric-box">
        <div class="metric-value">${agentes.length}</div>
        <div class="metric-label">Agentes Activos</div>
      </div>
      <div class="metric-box">
        <div class="metric-value">${agentes.filter(a => a.score >= 80).length}</div>
        <div class="metric-label">Score ≥ 80</div>
      </div>
      <div class="metric-box">
        <div class="metric-value">${agentes.filter(a => a.estado === 'Activo').length}</div>
        <div class="metric-label">Operativos</div>
      </div>
      <div class="metric-box">
        <div class="metric-value">85%</div>
        <div class="metric-label">Eficiencia</div>
      </div>
    </div>
    <div class="section-title" style="font-size:16px;font-weight:600;margin:16px 0 12px;">Agentes de la División</div>
    <div class="agents-list">
      ${agentes.map(ag => `
        <div class="agent-row" onclick="irNivel3('${ag.id}', '${ag.nombre}')">
          <div class="agent-info">
            <div class="agent-avatar">🤖</div>
            <div>
              <div class="agent-name">${ag.nombre}</div>
              <div class="agent-role">${ag.rol}</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="agent-status-mini">${ag.estado}</span>
            <span class="agent-score-mini">${ag.score}/100</span>
          </div>
        </div>
      `).join('')}
    </div>
  `;
  
  ocultarTodosNiveles();
  document.getElementById('nivel-2').classList.add('active');
}

function irNivel3(agenteId, agenteNombre) {
  agenteActual = agenteId;
  
  document.getElementById('breadcrumb-macro-n3').textContent = MACROS[macroActual].nombre;
  document.getElementById('breadcrumb-division-n3').textContent = document.getElementById('breadcrumb-division').textContent;
  document.getElementById('breadcrumb-agente').textContent = agenteNombre;
  
  // Buscar agente
  const agentes = AGENTES[divisionActual] || [];
  const agente = agentes.find(a => a.id === agenteId);
  
  if (!agente) return;
  
  const scoreColor = agente.score < 40 ? 'rojo' : agente.score < 60 ? 'naranja' : agente.score < 90 ? 'azul' : 'dorado';
  const estadoClass = agente.estado === 'Activo' ? 'active' : agente.estado === 'Inactivo' ? 'inactivo' : 'cuarentena';
  
  const panel = document.getElementById('agent-panel');
  panel.innerHTML = `
    <div class="agent-panel-header">
      <div class="agent-avatar-large">🤖</div>
      <div class="agent-title-group">
        <div class="agent-name-large">${agente.nombre}</div>
        <div class="agent-role-large">${agente.rol}</div>
      </div>
      <span class="agent-status-badge ${estadoClass}">${agente.estado}</span>
    </div>
    
    <div class="score-section">
      <div class="score-header">
        <span class="score-title">Score de Reputación</span>
        <span class="score-value">${agente.score}/100</span>
      </div>
      <div class="score-bar">
        <div class="score-fill ${scoreColor}" style="width: ${agente.score}%"></div>
      </div>
      <div style="font-size:11px;color:var(--text2);margin-top:8px;">
        ${agente.score < 40 ? 'Nivel: Cuarentena' : agente.score < 60 ? 'Nivel: Bronce' : agente.score < 90 ? 'Nivel: Operativo' : 'Nivel: Élite'}
      </div>
    </div>
    
    <div class="agent-metrics">
      <div class="agent-metric">
        <div class="agent-metric-value">${agente.tareas_exitosas}</div>
        <div class="agent-metric-label">Exitosas</div>
      </div>
      <div class="agent-metric">
        <div class="agent-metric-value">${agente.tareas_fallidas}</div>
        <div class="agent-metric-label">Fallidas</div>
      </div>
      <div class="agent-metric">
        <div class="agent-metric-value">${agente.modelo}</div>
        <div class="agent-metric-label">Modelo IA</div>
      </div>
      <div class="agent-metric">
        <div class="agent-metric-value">85%</div>
        <div class="agent-metric-label">Uptime</div>
      </div>
    </div>
    
    <div class="agent-description">
      <h4>Descripción del Agente</h4>
      <p>Agente especializado en ${agente.rol}. Utiliza modelo ${agente.modelo} para ejecutar tareas de manera autónoma. Última tarea ejecutada: ${agente.ultima_tarea}.</p>
    </div>
    
    <div class="agent-actions">
      <button class="btn-action primary">Ver Logs</button>
      <button class="btn-action">Pausar</button>
      <button class="btn-action danger">Reiniciar</button>
      <button class="btn-action">Configurar</button>
    </div>
  `;
  
  ocultarTodosNiveles();
  document.getElementById('nivel-3').classList.add('active');
}

function ocultarTodosNiveles() {
  document.querySelectorAll('.nav-level').forEach(nivel => nivel.classList.remove('active'));
}
</script>

</body>
</html>

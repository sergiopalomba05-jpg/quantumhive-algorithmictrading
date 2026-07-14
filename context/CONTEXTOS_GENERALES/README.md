# QuantumHive - Sistema de Trading Algorítmico Autónomo

**⚠️ CONFIDENCIAL - REPOSITORIO PRIVADO**

QuantumHive es un sistema de trading algorítmico autónomo basado en inteligencia artificial, diseñado para operar en mercados financieros con mínima intervención humana. El sistema utiliza aprendizaje por refuerzo (Reinforcement Learning), procesamiento de lenguaje natural y arquitectura de agentes autónomos para tomar decisiones de trading en tiempo real.

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Estructura de Carpetas](#estructura-de-carpetas)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Inicio del Sistema](#inicio-del-sistema)
- [Estado Actual](#estado-actual)
- [Próximos Pasos](#próximos-pasos)

## 🎯 Descripción

QuantumHive es un ecosistema completo de trading algorítmico que incluye:

- **Enjambre de Bots IA**: Múltiples agentes autónomos que operan en diferentes activos y timeframes
- **Sistema de Reputación**: Gestión dinámica del rendimiento de cada agente con asignación de modelos según score
- **Logística de Recursos**: Distribución inteligente de APIs y recursos por departamento
- **Persistencia de Contexto**: Gestión de memoria y estado de agentes para continuidad
- **Seguridad Avanzada**: Monitoreo de anomalías, modo emergencia y guardrails de output
- **Bus de Comunicación**: Sistema de mensajes centralizado para coordinación entre agentes
- **Gestión de VPS y Cuentas**: Control de infraestructura y cuentas de trading con anti-detección
- **Monetización Inteligente**: Sistema de oportunidades de monetización Low y High Ticket
- **Visual Intelligence**: Sistema de diseño y QA para dashboards
- **Inteligencia Infinita del CEO**: Sistema de gestión de ideas y visión estratégica
- **Agentes Operativos**: Compliance, recolección de datos y scheduling

## 🏗️ Arquitectura

QuantumHive está organizado en 11 Macrodivisiones:

### Macrodivisiones Principales

1. **MACRO1 — Trading**
   - D1: Trading IA (Enjambre CFDs/US30, bot híbrido unificado)
   - D2: Fondeo/Challenges
   - D2B: PropFirms Dispersión
   - D7: PropFirm Propia
   - D16: Sala Colmena

2. **MACRO2 — Operaciones**
   - D9: Limpieza/Mantenimiento
   - D12: Crecimiento/Optimización
   - D13: Legal/Compliance
   - D14: DevOps/Infraestructura

3. **MACRO3 — Marketing**
   - D3: Señales/Telegram
   - D4: Marketing/Captación
   - D5: Infoproductos/EAs
   - D6: Enterprise/High Ticket
   - D11: Ventas/Atención

4. **MACRO4 — Fábrica**
   - D8: Fábrica de Bots
   - D18: UCI Conocimiento IA

5. **MACRO5 — Innovación**
   - D17: Ecosistema Partners

6. **MACRO6 — Legal**
   - D13: Legal/Compliance

7. **MACRO7 — Colmena**
   - D16: Sala Colmena

8. **MACRO8 — Apps**
   - D15: BI/Dashboard CEO
   - D19: Localización/Multinacional

9. **MACRO9 — Academia**
   - D9: Academia Trading

## 📁 Estructura de Carpetas

```
QUANTUMHIVE_ALGORITHMICTRADING/
├── nucleo/                          # Sistemas nucleares (Sistemas 1-7)
│   ├── governance/                  # Sistema 1: DGCR Reputación
│   │   ├── governance_manager.py
│   │   └── config_reputation.json
│   ├── dlri/                        # Sistema 2: DLRI Logística de Recursos
│   │   ├── keys_vault.py
│   │   ├── resource_distributor.py
│   │   └── intelligence_report.md
│   ├── persistencia/                # Sistema 3: CPC Persistencia de Contexto
│   │   └── context_manager.py
│   ├── ugcc/                        # Sistema 4: UGCC Gestión de Contexto
│   │   └── context_controller.py
│   ├── seguridad/                   # Sistema 5: USEC Seguridad
│   │   └── security_manager.py
│   ├── bus_comunicacion.py          # Sistema 6: Bus de Comunicación
│   ├── gvca/                        # Sistema 7: GVCA VPS y Cuentas
│   │   ├── vps_manager.py
│   │   ├── bot_account_registry.py
│   │   └── anti_deteccion.py
│   ├── inteligencia_infinita/       # Sistema 11: Inteligencia Infinita
│   │   ├── ceo_ii.py
│   │   ├── analizador_viabilidad.py
│   │   └── vision_manager.py
│   ├── uvid/                        # Sistema 9: UVID Visual Intelligence
│   │   ├── design_system.json
│   │   ├── dashboard_optimizer.py
│   │   └── qa_visual.py
│   └── quantumhive_core.py         # Punto de entrada principal
├── automatizacion/                  # Agentes automatizados
│   └── agentes/
│       ├── umi/                     # Sistema 8: UMI Monetización
│       │   ├── director_umi.py
│       │   ├── explorador_lt.py
│       │   ├── explorador_ht.py
│       │   ├── optimizador_division.py
│       │   └── afiliados_externos.py
│       └── iniciales/               # Sistema 12: Agentes Iniciales
│           ├── agente_compliance.py
│           ├── agente_recolector.py
│           └── scheduler.py
├── dashboard/                       # Dashboards HTML
│   ├── quantumhive_dashboard_v3.html
│   └── oficina_virtual.html
├── config/                         # Configuración centralizada
│   └── quantumhive_config.py
├── tests/                          # Tests unitarios
│   ├── test_imports.md
│   └── test_core.py
├── logs/                           # Logs del sistema
├── datasets/                       # Datasets de trading
├── reportes/                       # Reportes generados
├── .env.template                   # Template de variables de entorno
├── .gitignore                      # Archivos ignorados por Git
├── requirements.txt                # Dependencias Python
└── README.md                       # Este archivo
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.11 o superior
- MetaTrader 5 (para trading en vivo)
- Cuenta en IC Markets u otro broker compatible

### Pasos de Instalación

1. **Clonar el repositorio** (privado)
   ```bash
   git clone <url-repo-privado>
   cd QUANTUMHIVE_ALGORITHMICTRADING
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.template .env
   # Editar .env con tus credenciales reales
   ```

5. **Crear directorios necesarios**
   ```bash
   python config/quantumhive_config.py
   ```

## ⚙️ Configuración

### Variables de Entorno

Editar el archivo `.env` con las siguientes variables:

```env
# API Keys de LLM
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AI...
OPENROUTER_API_KEY=sk-or-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID_SERGIO=123456789
TELEGRAM_CHAT_ID_ALERTAS=123456789

# WhatsApp
WHATSAPP_TOKEN=EAAG...
WHATSAPP_PHONE_ID=123456789

# MetaTrader 5
MT5_LOGIN=12345678
MT5_PASSWORD=tu_password
MT5_SERVER=ICMarketsSC-Demo
```

### Configuración del Sistema

El archivo `config/quantumhive_config.py` contiene toda la configuración centralizada del sistema, incluyendo:

- Rutas de archivos y directorios
- Parámetros del sistema de reputación
- Límites de operaciones por día
- Horarios operativos
- Umbrales de alertas
- Parámetros de backtesting
- Parámetros de entrenamiento RL

## 🎮 Inicio del Sistema

### Inicio Manual

```bash
python nucleo/quantumhive_core.py
```

Esto iniciará todos los módulos en orden:
1. SecurityManager (primero siempre)
2. GestorReputacion
3. KeysVault + ResourceDistributor
4. GestorContexto
5. ContextController
6. BusComunicacion
7. VPSManager + BotAccountRegistry

### Inicio de Agentes Operativos

Los 3 agentes iniciales se pueden activar hoy sin infraestructura completa:

1. **Agente Compliance**
   ```bash
   python automatizacion/agentes/iniciales/agente_compliance.py
   ```

2. **Agente Recolector**
   ```bash
   python automatizacion/agentes/iniciales/agente_recolector.py
   ```

3. **Scheduler**
   ```bash
   python automatizacion/agentes/iniciales/scheduler.py
   ```

## 📊 Estado Actual

### Sistemas Implementados (Sistemas 1-12)

| Sistema | Estado | Archivos |
|---------|--------|----------|
| Sistema 1 - DGCR Reputación | ✅ Completo | governance_manager.py |
| Sistema 2 - DLRI Recursos | ✅ Completo | keys_vault.py, resource_distributor.py |
| Sistema 3 - CPC Persistencia | ✅ Completo | context_manager.py |
| Sistema 4 - UGCC Contexto | ✅ Completo | context_controller.py |
| Sistema 5 - USEC Seguridad | ✅ Completo | security_manager.py |
| Sistema 6 - Bus Comunicación | ✅ Completo | bus_comunicacion.py |
| Sistema 7 - GVCA VPS/Cuentas | ✅ Completo | vps_manager.py, bot_account_registry.py, anti_deteccion.py |
| Sistema 8 - UMI Monetización | ✅ Completo | director_umi.py, explorador_lt.py, explorador_ht.py, optimizador_division.py, afiliados_externos.py |
| Sistema 9 - UVID Visual Intelligence | ✅ Completo | design_system.json, dashboard_optimizer.py, qa_visual.py |
| Sistema 10 - Dashboard Jerárquico | ✅ Completo | quantumhive_dashboard_v3.html |
| Sistema 11 - Inteligencia Infinita | ✅ Completo | ceo_ii.py, analizador_viabilidad.py, vision_manager.py |
| Sistema 12 - Agentes Iniciales | ✅ Completo | agente_compliance.py, agente_recolector.py, scheduler.py |

### Tests de Importación

- Total módulos probados: 10/37
- Módulos OK: 9
- Módulos con error: 1 (cache pendiente)
- Módulos pendientes: 27

### Tests Unitarios

- Total tests: 17
- Exitosos: 2
- Fallidos: 1
- Errores: 14

Los tests unitarios requieren corrección de firmas de métodos para coincidir con las implementaciones reales.

## 🔮 Próximos Pasos

### Inmediatos (Esta Semana)

1. **Corregir tests unitarios** - Ajustar firmas de métodos en tests/test_core.py
2. **Activar agentes iniciales** - Poner en producción compliance, recolector y scheduler
3. **Configurar credenciales** - Llenar .env con API keys reales
4. **Probar integración** - Verificar que todos los módulos funcionen juntos

### Corto Plazo (Próximas 2 Semanas)

1. **Entrenamiento RL** - Entrenar bot unificado US30 con PPO
2. **Exportar ONNX** - Exportar modelo a formato ONNX
3. **Crear EA MT5** - Implementar Expert Advisor que cargue ONNX
4. **Testing en demo** - Probar EA en cuenta demo IC Markets

### Mediano Plazo (Próximo Mes)

1. **Live Trading** - Mover a cuenta real pequeña
2. **Dashboard en vivo** - Conectar dashboard a métricas reales
3. **Sistema de señales** - Implementar bot de señales Telegram
4. **Fábrica de bots** - Catálogo de bots por activo

## ⚠️ Seguridad y Confidencialidad

- Este repositorio es **PRIVADO** y no debe ser compartido públicamente
- Nunca subir el archivo `.env` al repositorio
- Las credenciales de APIs deben mantenerse seguras
- El sistema incluye guardrails de seguridad para prevenir operaciones no autorizadas

## 📞 Soporte

Para preguntas o soporte interno, contactar a:
- Sergio (CEO)
- Canal de Slack #quantumhive-dev

## 📄 Licencia

Propiedad intelectual de QuantumHive. Todos los derechos reservados.

---

**Última actualización:** 28 de abril de 2026  
**Versión:** 0.1.0 - Alpha

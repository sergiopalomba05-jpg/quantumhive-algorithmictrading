# CONTEXTO MACRO 13 — SOFTWARES QUANTUMHIVE

## Identidad

**Nombre:** MACRO 13 — Softwares QuantumHive
**Propósito:** Desarrollo y gestión de productos de software propios de QuantumHive.

---

## Software 1: PropFirm Shield

**Descripción:** Software de anti-detección y gestión multi-cuenta para PropFirms.

**Funcionalidades:**
- **Anti-detección:** Evita patrones de detección por parte de PropFirms
- **Gestión multi-cuenta:** Gestiona múltiples cuentas simultáneamente
- **Delay management:** Calcula y aplica delays óptimos por PropFirm
- **Organizador de cuentas:** Distribuye cuentas por carga y servidor
- **Gestor de lotaje:** Aplica variación de lotaje para evitar patrones
- **Monitor de drawdown:** Monitorea drawdown en tiempo real
- **Rotación de cuentas:** Rota cuentas automáticamente por racha perdedora
- **Selector de cuenta:** Selecciona cuenta por servidor MT5

**Estado:** En desarrollo (módulos dispersos en Colmena)

**Agentes:**
- `selector_cuenta.py` - Selector por servidor MT5
- `dispersor_cuentas.py` - Distribuye señales con delay
- `monitor_dd_prop.py` - Monitorea drawdown
- `gestor_rotacion.py` - Rotación de cuentas
- `anti_deteccion.py` - Monitorea patrones sospechosos
- `vps_manager.py` - Gestión de VPS
- `compliance_prop.py` - Compliance de PropFirms

**Macrounidad Filtro Detección:**
- `macrounidad_filtro_deteccion/delay_manager.py` - Controla delay entre operaciones
- `macrounidad_filtro_deteccion/organizador_cuentas.py` - Organiza cuentas entre empresas
- `macrounidad_filtro_deteccion/gestor_lotaje.py` - Aplica variación de lotaje
- `macrounidad_filtro_deteccion/anti_deteccion_propfirm.py` - Monitorea patrones sospechosos
- `macrounidad_filtro_deteccion/integrador_d2b.py` - Conecta agentes D2B con macrounidad

---

## Software 2: Bot Factory Pro

**Descripción:** Fábrica de bots ONNX completa para trading algorítmico.

**Funcionalidades:**
- **Entrenamiento de modelos:** Entrena modelos RL (PPO) y CNN
- **Exportación ONNX:** Exporta modelos a formato ONNX
- **Backtesting:** Sistema de backtesting completo
- **Publisher:** Publica bots en tienda interna
- **Pipeline clonador:** Clona bots exitosos
- **Optimización:** Optimiza hiperparámetros automáticamente
- **QA:** Sistema de calidad para bots
- **Catálogo:** Catálogo de bots disponibles

**Estado:** En desarrollo (4 bots rentables en Python)

**Agentes:**
- Todos los agentes de `division_biblioteca_fabrica_bots`
- `pipeline_clonador.py` - Clona bots exitosos
- `backtester.py` - Sistema de backtesting
- `publisher.py` - Publica bots en tienda
- `optimizador.py` - Optimiza hiperparámetros
- `qa_bots.py` - Sistema de calidad

---

## Software 3+: Próximos a definir

**Estado:** Pendiente de definición

**Posibles futuros softwares:**
- **QuantumHive Dashboard Pro:** Dashboard avanzado de trading
- **Signal Processor Pro:** Procesador de señales avanzado
- **Risk Manager Pro:** Gestor de riesgo avanzado
- **Portfolio Manager Pro:** Gestor de portafolio

---

## Flujo de Desarrollo

```
Idea de Software
    ↓
Diseño y Arquitectura
    ↓
Desarrollo de Agentes
    ↓
Integración y Testing
    ↓
Deploy en Producción
    ↓
Monitoreo y Mantenimiento
```

---

## Estado Actual

**Fase 1 — ACTIVA.**

- PropFirm Shield: Módulos dispersos en desarrollo
- Bot Factory Pro: 4 bots rentables en Python
- Pipeline de integración: En desarrollo

---

## Próximos Pasos

1. **Completar PropFirm Shield:**
   - Integrar módulos dispersos
   - Probar anti-detección
   - Deploy en producción

2. **Completar Bot Factory Pro:**
   - Implementar pipeline clonador
   - Implementar backtester
   - Implementar publisher

3. **Definir Software 3+:**
   - Identificar necesidades del mercado
   - Diseñar arquitectura
   - Iniciar desarrollo

---

## Métricas Clave

| Métrica | Target Fase 1 | Target Fase 2 |
|---------|---------------|---------------|
| Softwares en producción | 1 | 3+ |
| Usuarios activos | 50 | 500 |
| Uptime de software | >95% | >99% |
| Tiempo de desarrollo | 3 meses | 2 meses |
| Satisfacción usuario | >70% | >85% |

---

*Softwares QuantumHive v3.0*

# CONTEXTO MACRO 12 — INFRAESTRUCTURA Y PLATAFORMA

## Identidad

**Nombre:** MACRO 12 — Infraestructura y Plataforma
**Propósito:** Base técnica sobre la que opera todo QuantumHive. Gestión de cloud, datos, seguridad, monitoreo e integraciones.

---

## División Cloud y Deploy

**Responsabilidad:** Gestión de servidores, contenedores y despliegues.

**Componentes:**
- **Render:** Hosting principal de AGI Telegram y servicios web
- **VPS Oracle:** Servidores para trading bots y MT5
- **Contenedores Docker:** Despliegue de microservicios
- **CI/CD:** Pipeline automatizado de despliegue
- **Agente Render:** Automatización de deploys en Render

**Agentes:**
- `agente_render.py` - Gestión de deploys en Render
- `vps_manager.py` - Gestión de servidores VPS
- `deploy_automation.py` - CI/CD automatizado

---

## División Datos y Persistencia

**Responsabilidad:** Gestión de bases de datos y almacenamiento.

**Componentes:**
- **SQLite:** Base de datos local para historial y caché
- **Supabase:** Base de datos en la nube para persistencia global
- **GitHub Memory:** Almacenamiento de contexto en repositorio
- **Backups:** Sistema de backups automáticos
- **Migración:** Sistema de migración entre bases de datos

**Agentes:**
- `agente_backup.py` - Backups automáticos
- `migrador_datos.py` - Migración entre bases de datos
- `limpieza_datos.py` - Limpieza de datos obsoletos

---

## División Seguridad

**Responsabilidad:** Gestión de credenciales y seguridad.

**Componentes:**
- **KeysVault:** Almacenamiento seguro de credenciales
- **Agente Seguridad:** Gestión de accesos y permisos
- **Credenciales:** API keys, tokens, certificados
- **Encriptación:** Encriptación de datos sensibles
- **Auditoría:** Logs de accesos y cambios

**Agentes:**
- `agente_seguridad.py` - Gestión de seguridad
- `keys_vault.py` - Almacenamiento de credenciales
- `auditor_accesos.py` - Auditoría de accesos

---

## División Monitoreo

**Responsabilidad:** Monitoreo de sistema y alertas.

**Componentes:**
- **Logs:** Centralización de logs de todos los servicios
- **Heartbeat:** Monitoreo de heartbeat de agentes
- **Alertas:** Sistema de alertas críticas
- **Métricas:** Métricas de rendimiento y uso
- **Dashboard:** Dashboard de monitoreo en tiempo real

**Agentes:**
- `heartbeat_monitor.py` - Monitoreo de heartbeat
- `agente_alertas_criticas.py` - Alertas críticas
- `monitoreo_sistema.py` - Monitoreo general del sistema
- `agente_dashboard_central.py` - Dashboard de métricas

---

## División Integración

**Responsabilidad:** Integración con APIs externas y conectores.

**Componentes:**
- **APIs Externas:** Integración con Telegram, WhatsApp, MT5, etc.
- **Webhooks:** Recepción y envío de webhooks
- **Conectores:** Adaptadores para servicios externos
- **Event Bus:** Sistema de eventos internos
- **Rate Limiting:** Gestión de límites de API

**Agentes:**
- `integrador_apis.py` - Integración de APIs externas
- `gestor_webhooks.py` - Gestión de webhooks
- `event_bus.py` - Sistema de eventos internos
- `rate_limiter.py` - Gestión de límites de API

---

## Estado Actual

**Fase 1 — ACTIVA.**

- Render configurado para AGI Telegram
- Supabase conectado para persistencia
- GitHub Memory operativo
- Sistema de heartbeat implementado
- Event Bus funcional con 13+ agentes conectados
- Agente Render automatizado
- Sistema de alertas críticas activo

---

## Próximos Pasos

1. **Implementar sistema de backups automáticos** para todas las bases de datos
2. **Centralizar logs** en un servicio de logging (Elasticsearch o similar)
3. **Implementar dashboard de monitoreo** en tiempo real
4. **Agregar más conectores** para servicios externos (Stripe, PayPal, etc.)
5. **Implementar sistema de encriptación** para datos sensibles

---

## Métricas Clave

| Métrica | Target Fase 1 | Target Fase 2 |
|---------|---------------|---------------|
| Uptime de servicios | >99% | >99.9% |
| Tiempo de respuesta | <500ms | <200ms |
| Retención de logs | 30 días | 90 días |
| Frecuencia de backups | Diario | Cada 6 horas |
| Alertas respondidas | <5 minutos | <1 minuto |

---

*Infraestructura base de QuantumHive v3.0*

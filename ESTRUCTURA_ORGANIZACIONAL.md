# Estructura Organizacional QuantumHive - Análisis Completo

## División 1 — Enjambre de Trading
**Función:** Bots híbridos EA MQL5 + ONNX ejecutando en MT5
**Agentes existentes:**
- `agente_auditoria.py` - audita operaciones 24hs
- `agente_compliance.py` - verifica FTMO challenge/live
- `agente_optimizador.py` - análisis skills, ajuste automático
- `agente_recolector.py` - descarga datos de MT5

**Agentes creados hoy (posibles duplicados):**
- `iniciales/agente_compliance.py` - DUPLICADO de `agente_compliance.py`
- `iniciales/agente_recolector.py` - DUPLICADO de `agente_recolector.py`

---

## División 2 — Gestión de Fondeo y Challenges
**Función:** challenge cliente → cuenta live → split 40/40/20
**Agentes existentes:**
- `division_fondeo/agente_challenge.py` - gestión de pase de challenge
- `division_fondeo/agente_cuentas_fondeadas.py` - registro cuentas fondeadas
- `division_fondeo/agente_cobro_fondeo.py` - cobro parte QH

---

## División 2B — PropFirms y Dispersión de Cuentas
**Función:** gestión multi-cuenta en PropFirms con delay/variación
**Agentes existentes:** Ninguno en estructura actual
**Macrounidad creada hoy:**
- `macrounidad_filtro_deteccion/` - **NUEVA MACROUNIDAD**
  - `delay_manager.py` - controla delay entre operaciones
  - `organizador_cuentas.py` - organiza cuentas entre empresas
  - `gestor_lotaje.py` - aplica cambio de lotes mínimo
  - `anti_deteccion_propfirm.py` - monitorea patrones sospechosos

**Estado:** ✅ CORRECTO - No hay duplicados, esta macrounidad es NUEVA

---

## División 3 — Grupo de Señales
**Función:** embudo señales gratis → suscripción → Colmena
**Agentes existentes:**
- `division_senales/agente_formateador_senales.py`
- `division_senales/agente_gestor_grupos.py`
- `division_senales/agente_cobro_senales.py`
- `division_senales/agente_retencion.py`
- `division_senales/agente_captacion_senales.py`

---

## División 4 — Marketing y Captación
**Función:** contenido automático con resultados reales
**Agentes existentes:**
- `division_marketing/agente_partnerships_traders.py`
- `division_marketing/agente_captacion_seguidores.py`
- `division_marketing/agente_naming_bots.py`

---

## División 5 — Infoproductos y Afiliados
**Función:** infoproductos digitales + software
**Agentes existentes:**
- `division_infoproductos/agente_creador_infoproductos.py`
- `division_infoproductos/agente_analista_tendencias_infoproductos.py`
- `division_infoproductos/agente_entrenador_ventas_infoproductos.py`

---

## División 6 — High Ticket Enterprise
**Función:** venta del framework a hedge funds y prop firms
**Agentes existentes:** Ninguno específico

---

## División 7 — PropFirm y Broker (FASE 5)
**Función:** fondea traders con los propios bots
**Agentes existentes:** Ninguno específico

---

## División 8 — Fábrica de Bots y Mercado Interno
**Función:** EAs mecánicos/asistidos/híbridos + tienda
**Agentes existentes:**
- `division_fabrica/agente_control_calidad.py`
- `division_fabrica/agente_pricing.py`
- `division_fabrica/agente_catalogo.py`

---

## División 9 — Limpieza y Mantenimiento
**Función:** limpieza datos/modelos/logs/prompts
**Agentes existentes:**
- `division_limpieza/agente_limpieza_datos.py`
- `division_limpieza/agente_limpieza_modelos.py`
- `division_limpieza/agente_limpieza_logs.py`

---

## División 10 — Diseño y Optimización Web
**Función:** quantumhive.io + dashboard + SEO
**Agentes existentes:**
- `division_web/agente_dashboard_manager.py`
- `division_web/agente_seo.py`
- `division_web/agente_ab_testing.py`

**Agentes creados hoy (posibles duplicados):**
- `iniciales/agente_dashboard.py` - DUPLICADO de `division_web/agente_dashboard_manager.py`

---

## División 11 — Atención al Cliente y Ventas
**Función:** pipeline Lead→Bot→Especialista→Closer
**Agentes existentes:**
- `division_ventas/agente_pipeline_ventas.py`
- `division_ventas/agente_bot_bienvenida.py`
- `division_ventas/agente_especialista.py`
- `division_ventas/agente_closer.py`
- `division_ventas/agente_onboarding.py`

---

## División 12 — Crecimiento y Optimización (meta-división)
**Función:** CEO estratégico, Scout, Clasificador, Entrenadores
**Agentes existentes:**
- `division_crecimiento/agente_ceo_estrategico.py`
- `division_crecimiento/agente_entrenador_bots.py`
- `division_crecimiento/agente_supervisor_global.py`

---

## División 13 — Legal y Compliance
**Función:** términos, contratos, regulaciones
**Agentes existentes:**
- `division_legal/agente_coordinador_legal.py`
- `division_legal/agente_legal_marketing.py`
- `division_legal/agente_legal_propfirms.py`
- `division_legal/agente_legal_sala_inversion.py`
- `division_legal/agente_legal_senales.py`
- `division_legal/agente_legal_uci.py`

---

## División 14 — Infraestructura y DevOps
**Función:** monitoreo, backup, actualizaciones
**Agentes existentes:**
- `division_infra/agente_monitoreo_sistema.py`
- `division_infra/agente_backup.py`
- `division_infra/agente_alertas_criticas.py`

---

## División 15 — Business Intelligence
**Función:** dashboard ejecutivo, métricas trading/negocio
**Agentes existentes:**
- `division_bi/agente_dashboard_central.py`
- `division_bi/agente_dashboard_ejecutivo.py`
- `division_bi/agente_metricas_trading.py`
- `division_bi/agente_metricas_negocio.py`
- `division_bi/agente_chatbot_dashboard.py`
- `division_bi/agente_chatbot_arquitecto.py`
- `division_bi/agente_analizador_tareas.py`
- `division_bi/agente_ejecutor_coordinador.py`

**Agentes creados hoy (posibles duplicados):**
- `iniciales/agente_tareas.py` - DUPLICADO de `division_bi/agente_analizador_tareas.py`

---

## División 16 — Sala de Inversión Colmena
**Función:** hedge fund gamificado
**Agentes existentes:**
- `division_sala_inversion/agente_gestor_sala.py`
- `division_sala_inversion/agente_visualizador.py`

---

## División 17 — Ecosistema de Partners
**Función:** empresas de fondeo, traders independientes
**Agentes existentes:** Ninguno específico

---

## División 18 — Unidad de Conocimiento e Inteligencia (UCI)
**Función:** fábrica de datos de entrenamiento para bots
**Agentes existentes:**
- `division_uci/agente_recolector_video.py`
- `division_uci/agente_procesador_pdfs.py`
- `division_uci/agente_generador_cnn.py`
- `division_uci/agente_base_conocimiento.py`
- `division_uci/agente_recolector_traders.py`

**Agentes creados hoy (posibles duplicados):**
- `iniciales/agente_entrenador_cnn.py` - DUPLICADO de `division_uci/agente_generador_cnn.py`
- `iniciales/agente_profesor.py` - DUPLICADO de `division_uci/agente_procesador_pdfs.py`

---

## División 19 — Localización y Expansión Multinacional
**Función:** adaptación cultural, legal y lingüística
**Agentes existentes:**
- `division_multinacional/agente_coordinador_idiomas.py`
- `division_multinacional/agente_traductor_tecnico.py`
- `division_multinacional/agente_marketing_local.py`
- `division_multinacional/agente_soporte_comunitario.py`
- `division_multinacional/agente_legal_compliance_jurisdiccion.py`

---

## Agentes Creados Hoy - Análisis de Duplicados

### ✅ NUEVOS (sin duplicados):
1. `macrounidad_filtro_deteccion/delay_manager.py` - NUEVO
2. `macrounidad_filtro_deteccion/organizador_cuentas.py` - NUEVO
3. `macrounidad_filtro_deteccion/gestor_lotaje.py` - NUEVO
4. `macrounidad_filtro_deteccion/anti_deteccion_propfirm.py` - NUEVO
5. `iniciales/agente_wa_asistente.py` - NUEVO (WhatsApp asistente personal)

### ❌ DUPLICADOS (ya existían):
1. `iniciales/agente_compliance.py` - DUPLICADO de `agente_compliance.py` (División 1)
2. `iniciales/agente_recolector.py` - DUPLICADO de `agente_recolector.py` (División 1)
3. `iniciales/agente_dashboard.py` - DUPLICADO de `division_web/agente_dashboard_manager.py` (División 10)
4. `iniciales/agente_tareas.py` - DUPLICADO de `division_bi/agente_analizador_tareas.py` (División 15)
5. `iniciales/agente_entrenador_cnn.py` - DUPLICADO de `division_uci/agente_generador_cnn.py` (División 18)
6. `iniciales/agente_profesor.py` - DUPLICADO de `division_uci/agente_procesador_pdfs.py` (División 18)

---

## Conclusión

**Hay 6 agentes duplicados** que creé hoy en `automatizacion/agentes/iniciales/` que ya existían en otras divisiones.

**Recomendación:**
1. **Eliminar duplicados** en `automatizacion/agentes/iniciales/`
2. **Mantener macrounidad** `macrounidad_filtro_deteccion/` - es NUEVA y correcta
3. **Mantener agente_wa_asistente.py** - es NUEVO y correcto
4. **Integrar macrounidad** con `division_propfirms/` (División 2B)

**Agente Dashboard:**
- Ya existe en `division_bi/agente_dashboard_central.py` y `division_web/agente_dashboard_manager.py`
- El nuevo `iniciales/agente_dashboard.py` es un duplicado
- Debería usar los existentes y hacer que actualicen automáticamente con los cambios

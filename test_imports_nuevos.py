import sys
sys.path.insert(0, r'C:\Users\sergio\BotsCuanticos')

resultados = []

modulos = [
    ("monitoreo_sistema", "automatizacion.agentes.division_infra.agente_monitoreo_sistema", "AgenteMonitoreoSistema"),
    ("alertas_criticas", "automatizacion.agentes.division_infra.agente_alertas_criticas", "AgenteAlertasCriticas"),
    ("backup", "automatizacion.agentes.division_infra.agente_backup", "AgenteBackup"),
    ("dashboard_ejecutivo", "automatizacion.agentes.division_bi.agente_dashboard_ejecutivo", "AgenteDashboardEjecutivo"),
    ("metricas_negocio", "automatizacion.agentes.division_bi.agente_metricas_negocio", "AgenteMetricasNegocio"),
    ("supervisor_global", "automatizacion.agentes.division_crecimiento.agente_supervisor_global", "AgenteSupervisorGlobal"),
    ("bienvenida", "automatizacion.agentes.division_ventas.agente_bienvenida", "AgenteBienvenida"),
    ("closer", "automatizacion.agentes.division_ventas.agente_closer", "AgenteCloser"),
    ("formateador_senales", "automatizacion.agentes.division_senales.agente_formateador_senales", "AgenteFormateadorSenales"),
    ("gestor_grupos", "automatizacion.agentes.division_senales.agente_gestor_grupos", "AgenteGestorGrupos"),
    ("challenge", "automatizacion.agentes.division_fondeo.agente_challenge", "AgenteChallenge"),
    ("cuentas_fondeadas", "automatizacion.agentes.division_fondeo.agente_cuentas_fondeadas", "AgenteCuentasFondeadas"),
]

for nombre, modulo, clase in modulos:
    try:
        mod = __import__(modulo, fromlist=[clase])
        getattr(mod, clase)
        resultados.append(f"OK  {nombre}")
    except Exception as e:
        resultados.append(f"ERR {nombre}: {type(e).__name__}: {e}")

print("\n".join(resultados))
print(f"\nTotal: {len(resultados)} modulos probados")

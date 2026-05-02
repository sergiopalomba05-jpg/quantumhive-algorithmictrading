from agente_render import AgenteRender

agente = AgenteRender()
logs = agente.obtener_logs(limit=200)
print('Logs obtenidos:', len(logs))
errores = agente.obtener_errores_logs()
print('Errores encontrados:', len(errores))
if errores:
    print('Primeros 5 errores:')
    for e in errores[:5]:
        print(' ', e)

# SKILL: Consultar Errores Conocidos
Antes de implementar cualquier proceso, consultar la base de
errores conocidos del proyecto.

CÓMO USAR:
from automatizacion.agentes.agente_optimizador_procesos import AgenteOptimizadorProcesos
optimizador = AgenteOptimizadorProcesos()
resultado = optimizador.consultar_errores_similares(proceso="nombre_proceso")
if resultado:
    print("Errores conocidos para este proceso:")
    for error in resultado:
        print(f"- {error['tipo_error']}: {error['solucion_aplicada']}")

CUÁNDO USAR:
- Antes de implementar deploy a Render
- Antes de modificar llm_wrapper.py
- Antes de trabajar con agente_render.py
- Antes de cualquier integración con API externa
- Antes de modificar archivos de configuración

---
auto_execution_mode: 0
description: Deploy completo a Render con verificación de errores
---
Ejecutar deploy completo a Render siguiendo este orden exacto:

PASO 1 — Verificar modelo Groq activo:
cd automatizacion/agentes
python agente_investigacion_modelos.py
Confirmar que llm_wrapper.py usa ese modelo exacto.

PASO 2 — Verificar variables de entorno:
Listar todas las variables del .env local.
Verificar que cada una existe en Render via agente_render.py.
Si falta alguna → agregarla antes de continuar.

PASO 3 — Push del código:
git add [archivos modificados — nunca git add .]
git commit -m "descripción clara del cambio"
git push
Confirmar push exitoso con número de commit.

PASO 4 — Trigger deploy en Render:
python agente_render.py → hacer_deploy_manual()
Esperar status = 'live' (máximo 5 minutos).

PASO 5 — Verificar logs:
Obtener logs de Render.
Buscar errores en las primeras 50 líneas.
Si hay errores → diagnosticar y corregir antes de reportar completado.

PASO 6 — Confirmar funcionamiento:
Reportar: commit, estado deploy, errores encontrados (si hay), solución aplicada.

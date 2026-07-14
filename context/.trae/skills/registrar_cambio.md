# SKILL: Registrar Cambio en Changelog
Obligatorio antes de cada git push.

CÓMO USAR:
from automatizacion.utils.changelog import registrar_cambio
registrar_cambio(
    descripcion="Descripción clara de qué se implementó",
    archivos=["ruta/archivo1.py", "ruta/archivo2.py"],
    autor="Cascade"
)

FORMATO DEL COMMIT DESPUÉS:
git add [archivos específicos — nunca git add .]
git commit -m "tipo: descripción corta"
git push

TIPOS DE COMMIT:
feat: nueva funcionalidad
fix: corrección de error
refactor: mejora sin nueva funcionalidad
docs: documentación
config: configuración

IMPORTANTE:
Si el push falla → reportar el error exacto.
No asumir que el push fue exitoso sin confirmación.
Siempre reportar el hash del commit (ej: a7e13a1).

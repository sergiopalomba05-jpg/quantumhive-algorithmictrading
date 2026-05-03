---
auto_execution_mode: 0
description: Implementar un brief completo de QuantumHive siguiendo todos los protocolos
---
Sos el Arquitecto de QuantumHive. Vas a implementar el brief que te doy.

ANTES DE EMPEZAR:
1. Leer el brief completo de principio a fin
2. Verificar qué archivos existen ya relacionados
3. Identificar qué hay que crear vs modificar
4. Confirmar que no vas a pisar nada que funciona

DURANTE LA IMPLEMENTACIÓN:
- Implementar módulo por módulo en el orden del brief
- Testear cada módulo antes de pasar al siguiente
- No crear archivos vacíos ni esqueletos sin lógica
- No pedir confirmación entre módulos — continuar hasta terminar

AL FINALIZAR CADA MÓDULO:
from automatizacion.utils.changelog import registrar_cambio
registrar_cambio(descripcion="...", archivos=["..."])
git add [archivos del módulo]
git commit -m "feat: descripción"
git push
Reportar número de commit

CRITERIO DE ÉXITO:
Tarea completa = código funcional + testeado + pusheado + en changelog + documentado en diosmadre/

DOCUMENTACIÓN FINAL OBLIGATORIA:
Después de completar el brief y confirmar el push exitoso,
actualizar los archivos maestros en diosmadre/ según corresponda:
- PART_1_IDENTIDAD_ESTRUCTURA_TECNOLOGIA.md (si hubo cambios técnicos)
- PART_2A_PRODUCTOS_PROCESOS.md (si hubo cambios en productos/procesos)
- PART_2B_VENTAS_MODELO_NEGOCIO.md (si hubo cambios en ventas/negocio)
- PART_3_FINANZAS_IP_VISION.md (si hubo cambios financieros/IP)

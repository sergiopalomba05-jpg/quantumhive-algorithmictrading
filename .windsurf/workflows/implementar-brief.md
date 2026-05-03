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
Tarea completa = código funcional + testeado + pusheado + en changelog

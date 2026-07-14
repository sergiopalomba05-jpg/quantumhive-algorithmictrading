"""
SWE-1.6 Memory Manager — QuantumHive
Gestor de memoria persistente para el arquitecto SWE-1.6 (Cascade)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class SWE16MemoryManager:
    """Gestiona la memoria persistente de SWE-1.6."""

    def __init__(self, memory_path: str = None):
        if memory_path is None:
            # Ruta por defecto: .windsurf/swe-1-6-memory.json
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_path = os.path.join(base_dir, '.trae', 'memory', 'trae-memory.json')
        
        self.memory_path = memory_path
        self.memory = self._cargar_memoria()

    def _cargar_memoria(self) -> Dict[str, Any]:
        """Carga la memoria desde el archivo JSON."""
        if not os.path.exists(self.memory_path):
            return self._crear_memoria_inicial()
        
        try:
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                memoria = json.load(f)
            return memoria
        except Exception as e:
            print(f"Error cargando memoria SWE-1.6: {e}")
            return self._crear_memoria_inicial()

    def _crear_memoria_inicial(self) -> Dict[str, Any]:
        """Crea la estructura inicial de memoria."""
        return {
            "contexto_empresa": {
                "vision_ceo": "",
                "objetivos_actuales": [],
                "proyectos_en_curso": []
            },
            "memoria_codigo": {
                "archivos_clave": {},
                "patrones_arquitectura": [],
                "decisiones_tecnicas": [],
                "estructura_bd": {}
            },
            "estado_actual": {
                "ultima_tarea": "",
                "bloqueos": [],
                "proximos_pasos": []
            },
            "metadatos": {
                "ultima_actualizacion": datetime.now().isoformat(),
                "total_sesiones": 0,
                "version": "1.0.0"
            }
        }

    def guardar_memoria(self):
        """Guarda la memoria en el archivo JSON."""
        try:
            # Actualizar metadatos
            self.memory["metadatos"]["ultima_actualizacion"] = datetime.now().isoformat()
            self.memory["metadatos"]["total_sesiones"] = self.memory["metadatos"].get("total_sesiones", 0) + 1
            
            # Guardar
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando memoria SWE-1.6: {e}")
            return False

    def actualizar_vision_ceo(self, vision: str):
        """Actualiza la visión del CEO."""
        self.memory["contexto_empresa"]["vision_ceo"] = vision
        self.guardar_memoria()

    def agregar_objetivo(self, objetivo: str):
        """Agrega un objetivo actual."""
        if objetivo not in self.memory["contexto_empresa"]["objetivos_actuales"]:
            self.memory["contexto_empresa"]["objetivos_actuales"].append(objetivo)
            self.guardar_memoria()

    def eliminar_objetivo(self, objetivo: str):
        """Elimina un objetivo actual."""
        if objetivo in self.memory["contexto_empresa"]["objetivos_actuales"]:
            self.memory["contexto_empresa"]["objetivos_actuales"].remove(objetivo)
            self.guardar_memoria()

    def actualizar_proyecto(self, nombre: str, estado: str, descripcion: str = "", commit: str = ""):
        """Actualiza o agrega un proyecto en curso."""
        proyectos = self.memory["contexto_empresa"]["proyectos_en_curso"]
        
        # Buscar si ya existe
        for i, proyecto in enumerate(proyectos):
            if proyecto["nombre"] == nombre:
                proyectos[i]["estado"] = estado
                proyectos[i]["descripcion"] = descripcion
                if commit:
                    proyectos[i]["commit"] = commit
                self.guardar_memoria()
                return
        
        # Agregar nuevo proyecto
        proyectos.append({
            "nombre": nombre,
            "estado": estado,
            "descripcion": descripcion,
            "commit": commit
        })
        self.guardar_memoria()

    def registrar_archivo_clave(self, nombre: str, descripcion: str):
        """Registra un archivo clave del código."""
        self.memory["memoria_codigo"]["archivos_clave"][nombre] = descripcion
        self.guardar_memoria()

    def registrar_patron_arquitectura(self, patron: str):
        """Registra un patrón de arquitectura."""
        if patron not in self.memory["memoria_codigo"]["patrones_arquitectura"]:
            self.memory["memoria_codigo"]["patrones_arquitectura"].append(patron)
            self.guardar_memoria()

    def registrar_decision_tecnica(self, decision: str):
        """Registra una decisión técnica."""
        if decision not in self.memory["memoria_codigo"]["decisiones_tecnicas"]:
            self.memory["memoria_codigo"]["decisiones_tecnicas"].append(decision)
            self.guardar_memoria()

    def actualizar_ultima_tarea(self, tarea: str):
        """Actualiza la última tarea realizada."""
        self.memory["estado_actual"]["ultima_tarea"] = tarea
        self.guardar_memoria()

    def agregar_bloqueo(self, bloqueo: str):
        """Agrega un bloqueo actual."""
        if bloqueo not in self.memory["estado_actual"]["bloqueos"]:
            self.memory["estado_actual"]["bloqueos"].append(bloqueo)
            self.guardar_memoria()

    def eliminar_bloqueo(self, bloqueo: str):
        """Elimina un bloqueo actual."""
        if bloqueo in self.memory["estado_actual"]["bloqueos"]:
            self.memory["estado_actual"]["bloqueos"].remove(bloqueo)
            self.guardar_memoria()

    def agregar_paso_siguiente(self, paso: str):
        """Agrega un siguiente paso."""
        if paso not in self.memory["estado_actual"]["proximos_pasos"]:
            self.memory["estado_actual"]["proximos_pasos"].append(paso)
            self.guardar_memoria()

    def eliminar_paso_siguiente(self, paso: str):
        """Elimina un siguiente paso."""
        if paso in self.memory["estado_actual"]["proximos_pasos"]:
            self.memory["estado_actual"]["proximos_pasos"].remove(paso)
            self.guardar_memoria()

    def obtener_contexto_completo(self) -> str:
        """Retorna el contexto completo como string para inyectar en System Prompt."""
        contexto = f"""
=== MEMORIA SWE-1.6 (CASCADE) ===

VISIÓN CEO:
{self.memory['contexto_empresa']['vision_ceo']}

OBJETIVOS ACTUALES:
{chr(10).join(f"- {obj}" for obj in self.memory['contexto_empresa']['objetivos_actuales'])}

PROYECTOS EN CURSO:
{chr(10).join(f"- {p['nombre']}: {p['estado']}" for p in self.memory['contexto_empresa']['proyectos_en_curso'])}

ÚLTIMA TAREA:
{self.memory['estado_actual']['ultima_tarea']}

BLOQUEOS ACTUALES:
{chr(10).join(f"- {b}" for b in self.memory['estado_actual']['bloqueos'])}

PRÓXIMOS PASOS:
{chr(10).join(f"- {p}" for p in self.memory['estado_actual']['proximos_pasos'])}

ARCHIVOS CLAVE:
{chr(10).join(f"- {k}: {v}" for k, v in self.memory['memoria_codigo']['archivos_clave'].items())}

PATRONES DE ARQUITECTURA:
{chr(10).join(f"- {p}" for p in self.memory['memoria_codigo']['patrones_arquitectura'])}

DECISIONES TÉCNICAS:
{chr(10).join(f"- {d}" for d in self.memory['memoria_codigo']['decisiones_tecnicas'])}

=== FIN MEMORIA SWE-1.6 ===
"""
        return contexto


# Instancia global
swe_memory = SWE16MemoryManager()

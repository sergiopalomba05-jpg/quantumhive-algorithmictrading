#!/usr/bin/env python3
"""
Memory Manager — AGI UPGRADE v2.0
Gestiona la memoria persistente en JSON para AGI.
Carga y guarda contexto, perfil, ideas, decisiones.
"""

import json
from typing import Dict, Optional
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.base_path = Path(r"C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING\automatizacion\agi_memoria")
        self.agi_memory_path = self.base_path / "agi_memory.json"
        self.sergio_profile_path = self.base_path / "sergio_profile.json"
        self.active_context_path = self.base_path / "active_context.json"
        self.contexto_qh_path = self.base_path / "contexto_qh.md"
        self.vision_ceo_path = self.base_path / "vision_ceo.md"
        self.banco_decisiones_path = self.base_path / "banco_decisiones.md"
    
    def cargar_memoria_completa(self) -> Dict:
        """Carga toda la memoria persistente de AGI."""
        memoria = {
            "agi_memory": self._cargar_json(self.agi_memory_path),
            "sergio_profile": self._cargar_json(self.sergio_profile_path),
            "active_context": self._cargar_json(self.active_context_path),
            "contexto_qh": self._cargar_markdown(self.contexto_qh_path),
            "vision_ceo": self._cargar_markdown(self.vision_ceo_path),
            "banco_decisiones": self._cargar_markdown(self.banco_decisiones_path)
        }
        logger.info("Memoria persistente cargada completamente")
        return memoria
    
    def guardar_idea(self, titulo: str, descripcion: str, categoria: str, score: int, notas: str = ""):
        """Guarda una idea en vision_ceo.md y actualiza agi_memory.json."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Agregar a vision_ceo.md
        entrada = f"""
## {fecha} — {titulo}
**Score:** {score}/100
**Categoría:** {categoria}
**Estado:** registrada

**Descripción:**
{descripcion}

**Notas:**
{notas}

**Brief para Colmena:** pendiente

---
"""
        contenido = self._cargar_markdown(self.vision_ceo_path)
        with open(self.vision_ceo_path, 'a', encoding='utf-8') as f:
            f.write(entrada)
        
        # Actualizar agi_memory.json
        agi_memory = self._cargar_json(self.agi_memory_path)
        agi_memory["ideas"].append({
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "score": score,
            "fecha": fecha,
            "estado": "registrada"
        })
        self._guardar_json(self.agi_memory_path, agi_memory)
        
        logger.info(f"Idea guardada: {titulo}")
    
    def guardar_decision(self, descripcion: str, tipo: str, impacto: str, ejecutada_por: str):
        """Guarda una decisión en banco_decisiones.md y actualiza agi_memory.json."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Agregar a banco_decisiones.md
        entrada = f"""
## {fecha} — {tipo}
**Ejecutada por:** {ejecutada_por}
**Impacto:** {impacto}

**Descripción:**
{descripcion}

---
"""
        contenido = self._cargar_markdown(self.banco_decisiones_path)
        with open(self.banco_decisiones_path, 'a', encoding='utf-8') as f:
            f.write(entrada)
        
        # Actualizar agi_memory.json
        agi_memory = self._cargar_json(self.agi_memory_path)
        agi_memory["decisiones"].append({
            "descripcion": descripcion,
            "tipo": tipo,
            "impacto": impacto,
            "ejecutada_por": ejecutada_por,
            "fecha": fecha
        })
        self._guardar_json(self.agi_memory_path, agi_memory)
        
        logger.info(f"Decisión guardada: {tipo}")
    
    def actualizar_perfil_sergio(self, campo: str, valor):
        """Actualiza un campo específico del perfil de Sergio."""
        perfil = self._cargar_json(self.sergio_profile_path)
        perfil[campo] = valor
        perfil["ultima_actualizacion"] = datetime.now().isoformat()
        self._guardar_json(self.sergio_profile_path, perfil)
        logger.info(f"Perfil Sergio actualizado: {campo}")
    
    def agregar_hilo_activo(self, tema: str, proximo_paso: str):
        """Agrega un hilo activo al contexto."""
        active_context = self._cargar_json(self.active_context_path)
        active_context["hilos_abiertos_sin_resolucion"].append({
            "tema": tema,
            "proximo_paso": proximo_paso,
            "fecha": datetime.now().isoformat()
        })
        self._guardar_json(self.active_context_path, active_context)
        logger.info(f"Hilo activo agregado: {tema}")
    
    def obtener_contexto_para_claude(self) -> str:
        """Genera string de contexto completo para Claude API."""
        memoria = self.cargar_memoria_completa()
        
        contexto_parts = []
        
        # Contexto QuantumHive
        if memoria["contexto_qh"]:
            contexto_parts.append(f"## CONTEXTO QUANTUMHIVE\n{memoria['contexto_qh']}\n")
        
        # Perfil Sergio
        if memoria["sergio_profile"]:
            perfil = memoria["sergio_profile"]
            contexto_parts.append(f"## PERFIL DE SERGIO\n")
            contexto_parts.append(f"Patrones de decisión: {perfil.get('patrones_decision', 'N/A')}")
            contexto_parts.append(f"Horas de actividad: {perfil.get('horas_actividad', 'N/A')}")
            contexto_parts.append(f"Keywords prioritarios: {perfil.get('keywords_prioritarios', 'N/A')}")
            contexto_parts.append(f"Nivel de riesgo actual: {perfil.get('nivel_riesgo', 'N/A')}\n")
        
        # Ideas activas
        if memoria["vision_ceo"]:
            contexto_parts.append(f"## IDEAS ACTIVAS (vision_ceo.md)\n{memoria['vision_ceo']}\n")
        
        # Decisiones recientes
        if memoria["banco_decisiones"]:
            contexto_parts.append(f"## DECISIONES RECIENTES (banco_decisiones.md)\n{memoria['banco_decisiones']}\n")
        
        # Hilos abiertos
        if memoria["active_context"]:
            hilos = memoria["active_context"].get("hilos_abiertos_sin_resolucion", [])
            if hilos:
                contexto_parts.append("## HILOS ABIERTOS SIN RESOLUCIÓN\n")
                for hilo in hilos[-5:]:  # Últimos 5
                    contexto_parts.append(f"- {hilo['tema']}: {hilo['proximo_paso']}")
                contexto_parts.append("\n")
        
        return "\n".join(contexto_parts)
    
    def _cargar_json(self, path: Path) -> Dict:
        """Carga archivo JSON."""
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando JSON {path}: {e}")
            return {}
    
    def _guardar_json(self, path: Path, data: Dict):
        """Guarda archivo JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _cargar_markdown(self, path: Path) -> str:
        """Carga archivo Markdown."""
        if not path.exists():
            return ""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error cargando Markdown {path}: {e}")
            return ""

if __name__ == "__main__":
    manager = MemoryManager()
    
    # Prueba
    memoria = manager.cargar_memoria_completa()
    print("=== Memoria Cargada ===")
    print(json.dumps(memoria, indent=2, ensure_ascii=False))
    
    print("\n=== Contexto para Claude ===")
    contexto = manager.obtener_contexto_para_claude()
    print(contexto)

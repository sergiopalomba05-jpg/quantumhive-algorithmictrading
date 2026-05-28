"""
GitHub Memory Manager — QuantumHive AGI
Persiste la memoria de AGI en GitHub entre sesiones de Render.
Sin costo adicional, funciona en plan Free de Render.
"""

import os
import json
import base64
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'sergiopalomba05-jpg/quantumhive-algorithmictrading')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main')
MEMORIA_DIR = 'agi_memoria_github'

ARCHIVOS_JSON = [
    'agi_memory.json',
    'sergio_profile.json',
    'active_context.json',
    'agi_learning.json',
    'estado_sistema.json',
]

ARCHIVOS_MARKDOWN = [
    'vision_ceo.md',
    'banco_decisiones.md',
    'contexto_qh.md',
    'perfil_sergio.md',
]


class GitHubMemoryManager:
    """
    Gestiona la memoria persistente de AGI usando GitHub como storage.
    """

    def __init__(self):
        self.token = GITHUB_TOKEN
        self.repo = GITHUB_REPO
        self.branch = GITHUB_BRANCH
        self.headers = {
            'Authorization': f'token {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/repos/{self.repo}/contents'
        self._inicializar_archivos()
        logger.info("GitHubMemoryManager inicializado")

    def _inicializar_archivos(self):
        """Crea los archivos de memoria en GitHub si no existen."""
        for archivo in ARCHIVOS_JSON:
            path = f"{MEMORIA_DIR}/{archivo}"
            if not self._get_file(path):
                self._put_file(path, '{}', None, f'AGI: inicializar {archivo}')

        for archivo in ARCHIVOS_MARKDOWN:
            path = f"{MEMORIA_DIR}/{archivo}"
            if not self._get_file(path):
                nombre = archivo.replace('.md', '').replace('_', ' ').title()
                self._put_file(path, f'# {nombre}\n', None, f'AGI: inicializar {archivo}')

    def _get_file(self, path: str) -> Optional[Dict]:
        """Lee un archivo desde GitHub público (sin token). Retorna contenido y SHA."""
        try:
            url = f"{self.base_url}/{path}?ref={self.branch}"
            headers_publicos = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(url, headers=headers_publicos, timeout=10)
            if response.status_code == 200:
                data = response.json()
                contenido = base64.b64decode(data['content']).decode('utf-8')
                return {'contenido': contenido, 'sha': data['sha']}
            logger.warning(f"Error leyendo {path}: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error leyendo {path}: {e}")
            return None

    def _put_file(self, path: str, contenido: str, sha: Optional[str] = None,
                  mensaje: str = None) -> bool:
        """Crea o actualiza un archivo en GitHub."""
        try:
            url = f"{self.base_url}/{path}"
            contenido_b64 = base64.b64encode(contenido.encode('utf-8')).decode('utf-8')

            payload = {
                'message': mensaje or f'AGI: actualizar {path} — {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'content': contenido_b64,
                'branch': self.branch
            }

            if sha:
                payload['sha'] = sha

            response = requests.put(url, headers=self.headers, json=payload, timeout=15)

            if response.status_code in [200, 201]:
                logger.info(f"GitHub Memory: guardado {path}")
                return True
            else:
                logger.error(f"Error guardando {path}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Excepción guardando {path}: {e}")
            return False

    def cargar_memoria_completa(self) -> Dict[str, Any]:
        """Carga todos los archivos de memoria desde GitHub."""
        memoria = {}

        for archivo in ARCHIVOS_JSON:
            resultado = self._get_file(f"{MEMORIA_DIR}/{archivo}")
            if resultado:
                try:
                    memoria[archivo] = json.loads(resultado['contenido'])
                except:
                    memoria[archivo] = {}
            else:
                memoria[archivo] = {}

        for archivo in ARCHIVOS_MARKDOWN:
            resultado = self._get_file(f"{MEMORIA_DIR}/{archivo}")
            memoria[archivo] = resultado['contenido'] if resultado else ''

        return memoria

    def guardar_memoria(self, clave: str, datos: Any) -> bool:
        """Actualiza un archivo de memoria específico en GitHub."""
        path = f"{MEMORIA_DIR}/{clave}"
        resultado_actual = self._get_file(path)
        sha = resultado_actual['sha'] if resultado_actual else None

        if clave.endswith('.json'):
            contenido = json.dumps(datos, ensure_ascii=False, indent=2)
        else:
            contenido = datos

        return self._put_file(path, contenido, sha)

    def actualizar_perfil_sergio(self, mensaje: str, tipo: str = 'interaccion'):
        """Actualiza el perfil dinámico de Sergio en GitHub (síncrono)."""
        resultado = self._get_file(f"{MEMORIA_DIR}/sergio_profile.json")
        try:
            perfil = json.loads(resultado['contenido']) if resultado else {}
        except:
            perfil = {}

        perfil['ultima_interaccion'] = {
            'fecha': datetime.now().isoformat(),
            'tipo': tipo,
            'contenido': mensaje[:200]
        }
        perfil['total_interacciones'] = perfil.get('total_interacciones', 0) + 1
        self.guardar_memoria('sergio_profile.json', perfil)

    def registrar_idea_aprobada(self, titulo: str, descripcion: str,
                                 score: int, categoria: str, proximo_paso: str):
        """Registra una idea aprobada en vision_ceo.md en GitHub."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        entrada = f"""
## {fecha} — {titulo}
**Score:** {score}/100
**Categoría:** {categoria}
**Estado:** aprobada

**Descripción:**
{descripcion}

**Próximo paso:**
{proximo_paso}

---
"""
        resultado = self._get_file(f"{MEMORIA_DIR}/vision_ceo.md")
        contenido_actual = resultado['contenido'] if resultado else ''
        sha = resultado['sha'] if resultado else None
        self._put_file(f"{MEMORIA_DIR}/vision_ceo.md",
                       contenido_actual + entrada, sha,
                       f'AGI: nueva idea — {titulo}')

    def registrar_decision(self, decision: str, tipo: str, impacto: str, contexto: str):
        """Registra una decisión en banco_decisiones.md en GitHub."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        entrada = f"""
## {fecha} — {decision}
**Tipo:** {tipo}
**Impacto:** {impacto}
**Contexto:** {contexto}

---
"""
        resultado = self._get_file(f"{MEMORIA_DIR}/banco_decisiones.md")
        contenido_actual = resultado['contenido'] if resultado else ''
        sha = resultado['sha'] if resultado else None
        self._put_file(f"{MEMORIA_DIR}/banco_decisiones.md",
                       contenido_actual + entrada, sha,
                       f'AGI: decisión — {decision}')

    def obtener_contexto_para_claude(self) -> str:
        """Genera el bloque de contexto para inyectar en el system prompt."""
        try:
            memoria = self.cargar_memoria_completa()
            bloques = []

            perfil = memoria.get('sergio_profile.json', {})
            if perfil:
                bloques.append(f"PERFIL SERGIO: {json.dumps(perfil, ensure_ascii=False)[:500]}")

            activo = memoria.get('active_context.json', {})
            if activo:
                bloques.append(f"CONTEXTO ACTIVO: {json.dumps(activo, ensure_ascii=False)[:500]}")

            vision = memoria.get('vision_ceo.md', '')
            if vision and len(vision) > 10:
                bloques.append(f"VISION CEO (ideas recientes):\n{vision[-1000:]}")

            decisiones = memoria.get('banco_decisiones.md', '')
            if decisiones and len(decisiones) > 10:
                bloques.append(f"DECISIONES RECIENTES:\n{decisiones[-500:]}")

            return "\n\n".join(bloques) if bloques else ""

        except Exception as e:
            logger.error(f"Error cargando contexto GitHub: {e}")
            return ""


# Instancia global
try:
    github_memory = GitHubMemoryManager()
    logger.info("GitHub Memory Manager activo")
except Exception as e:
    logger.error(f"Error iniciando GitHub Memory: {e}")
    github_memory = None

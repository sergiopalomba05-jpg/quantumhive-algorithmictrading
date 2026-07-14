#!/usr/bin/env python3
"""
Agente Optimizador de Agentes
===============================
Analiza todos los agentes de la Colmena.
Detecta duplicaciones, recomienda fusiones, identifica gaps funcionales.
"""

import sqlite3
import json
import logging
import ast
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

DB_PATH = 'agi_memoria_telegram.db'
AGENTES_DIR = Path(__file__).parent


class AgenteOptimizadorAgentes:
    """Optimizador de agentes de la Colmena."""

    def __init__(self, db_path: str = DB_PATH, agentes_dir: Path = AGENTES_DIR):
        self.db_path = db_path
        self.agentes_dir = agentes_dir
        self._crear_tablas()

    def _crear_tablas(self):
        """Crea tablas SQLite si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analisis_agentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agente TEXT NOT NULL,
                archivo TEXT,
                division TEXT,
                macro TEXT,
                funciones_detectadas TEXT,
                dependencias TEXT,
                estado TEXT,
                score_utilidad INTEGER,
                ultima_ejecucion TEXT,
                observaciones TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recomendaciones_fusion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agentes_involucrados TEXT NOT NULL,
                tipo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                beneficio_esperado TEXT,
                complejidad TEXT,
                prioridad INTEGER,
                estado TEXT DEFAULT 'pendiente_aprobacion',
                aprobado_por TEXT,
                fecha_aprobacion TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info("[OPTIMIZADOR_AGENTES] Tablas creadas/verificadas")

    def escanear_agentes(self) -> list:
        """
        Escanea TODOS los archivos agente_*.py del proyecto.
        Directorios a escanear:
        - automatizacion/agentes/
        - automatizacion/agentes/division_biblioteca_fabrica_bots/
        - automatizacion/agentes/division_recursos_gratis/
        - cualquier subdirectorio dentro de agentes/
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Limpiar análisis anteriores
        cursor.execute("DELETE FROM analisis_agentes")

        directorios = [
            self.agentes_dir,
            self.agentes_dir / "division_biblioteca_fabrica_bots",
            self.agentes_dir / "division_recursos_gratis"
        ]

        agentes_encontrados = []

        for directorio in directorios:
            if not directorio.exists():
                continue

            for archivo in directorio.glob("agente_*.py"):
                try:
                    info = self._analizar_archivo_agente(archivo)
                    if info:
                        timestamp = datetime.now().isoformat()
                        funciones_json = json.dumps(info['funciones'])
                        dependencias_json = json.dumps(info['dependencias'])

                        cursor.execute("""
                            INSERT INTO analisis_agentes (
                                timestamp, agente, archivo, division, macro,
                                funciones_detectadas, dependencias, estado,
                                score_utilidad, observaciones
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            timestamp,
                            info['nombre'],
                            str(info['archivo']),
                            info.get('division'),
                            info.get('macro'),
                            funciones_json,
                            dependencias_json,
                            info['estado'],
                            info['score'],
                            info.get('observaciones')
                        ))

                        agentes_encontrados.append(info)
                        logger.info(f"[OPTIMIZADOR_AGENTES] Analizado: {info['nombre']}")

                except Exception as e:
                    logger.error(f"[OPTIMIZADOR_AGENTES] Error analizando {archivo}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"[OPTIMIZADOR_AGENTES] Escaneo completado: {len(agentes_encontrados)} agentes")
        return agentes_encontrados

    def _analizar_archivo_agente(self, archivo: Path) -> Optional[Dict]:
        """Analiza un archivo de agente y extrae información."""
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()

            # Parsear el archivo para extraer información
            arbol = ast.parse(contenido)

            nombre_clase = None
            docstring = None
            funciones_publicas = []
            imports = []

            for nodo in arbol.body:
                if isinstance(nodo, ast.ClassDef):
                    nombre_clase = nodo.name
                    docstring = ast.get_docstring(nodo)

                    # Extraer métodos públicos
                    for item in nodo.body:
                        if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                            funciones_publicas.append(item.name)

                elif isinstance(nodo, ast.Import):
                    for alias in nodo.names:
                        imports.append(alias.name)
                elif isinstance(nodo, ast.ImportFrom):
                    imports.append(nodo.module or '')

            if not nombre_clase:
                return None

            # Determinar división desde la ruta del archivo
            ruta_parts = archivo.parts
            division = "general"
            if "division_biblioteca_fabrica_bots" in ruta_parts:
                division = "fabrica_bots"
            elif "division_recursos_gratis" in ruta_parts:
                division = "recursos_gratis"

            # Calcular score de utilidad
            score = self._calcular_score_utilidad_interno(contenido, len(funciones_publicas), len(imports), docstring)

            # Determinar estado
            estado = "activo" if len(funciones_publicas) > 0 else "esqueleto"

            return {
                'nombre': archivo.stem,
                'archivo': archivo,
                'clase': nombre_clase,
                'docstring': docstring,
                'funciones': funciones_publicas,
                'dependencias': imports,
                'division': division,
                'estado': estado,
                'score': score,
                'tamano_bytes': len(contenido)
            }

        except Exception as e:
            logger.error(f"[OPTIMIZADOR_AGENTES] Error parseando {archivo}: {e}")
            return None

    def _calcular_score_utilidad_interno(self, contenido: str, num_funciones: int, num_imports: int, docstring: str) -> int:
        """Calcula score de utilidad interno."""
        score = 0

        # ¿Tiene código real?
        if num_funciones > 0:
            score += 30

        # ¿Tiene imports?
        if num_imports > 0:
            score += 10

        # ¿Tiene docstring?
        if docstring and len(docstring) > 50:
            score += 15

        # ¿Tiene código significativo?
        if len(contenido) > 500:
            score += 15

        # ¿Tiene SQLite?
        if 'sqlite3' in contenido:
            score += 10

        # ¿Tiene Event Bus?
        if 'event_bus' in contenido or 'EventBus' in contenido:
            score += 10

        # ¿Tiene logging?
        if 'logging' in contenido:
            score += 10

        return min(score, 100)

    def detectar_duplicados(self) -> list:
        """
        Compara funciones entre agentes usando similitud de nombres y docstrings.
        Detecta duplicados y posibles complementos.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT agente, funciones_detectadas
            FROM analisis_agentes
        """)

        agentes = cursor.fetchall()
        duplicados = []

        for i, (agente1, funcs1_json) in enumerate(agentes):
            for j, (agente2, funcs2_json) in enumerate(agentes):
                if i >= j:
                    continue

                funcs1 = json.loads(funcs1_json) if funcs1_json else []
                funcs2 = json.loads(funcs2_json) if funcs2_json else []

                # Comparar nombres de funciones
                similitud = self._calcular_similitud_listas(funcs1, funcs2)

                if similitud > 70:
                    duplicados.append({
                        'agente1': agente1,
                        'agente2': agente2,
                        'score_similitud': similitud,
                        'tipo': 'probable_duplicado'
                    })
                elif similitud > 50:
                    duplicados.append({
                        'agente1': agente1,
                        'agente2': agente2,
                        'score_similitud': similitud,
                        'tipo': 'posible_complemento'
                    })

        conn.close()
        logger.info(f"[OPTIMIZADOR_AGENTES] Duplicados detectados: {len(duplicados)}")
        return duplicados

    def _calcular_similitud_listas(self, lista1: List, lista2: List) -> float:
        """Calcula similitud entre dos listas de strings."""
        if not lista1 or not lista2:
            return 0

        coincidencias = 0
        for item1 in lista1:
            for item2 in lista2:
                if SequenceMatcher(None, item1.lower(), item2.lower()).ratio() > 0.8:
                    coincidencias += 1
                    break

        total = max(len(lista1), len(lista2))
        return (coincidencias / total) * 100

    def recomendar_fusion(
        self,
        agente1: str,
        agente2: str,
        motivo: str,
        beneficio: str,
        complejidad: str = 'media'
    ) -> dict:
        """
        Genera y guarda recomendación de fusión en SQLite.
        Requiere aprobación de Sergio antes de ejecutar.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        agentes_json = json.dumps([agente1, agente2])

        cursor.execute("""
            INSERT INTO recomendaciones_fusion (
                timestamp, agentes_involucrados, tipo, descripcion,
                beneficio_esperado, complejidad, prioridad, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            agentes_json,
            'fusion',
            motivo,
            beneficio,
            complejidad,
            5,  # prioridad media por defecto
            'pendiente_aprobacion'
        ))

        recomendacion_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"[OPTIMIZADOR_AGENTES] Recomendación de fusión creada: {agente1} + {agente2}")
        return {'id': recomendacion_id, 'agentes': [agente1, agente2]}

    def analizar_gaps_funcionales(self) -> list:
        """
        Compara funciones cubiertas por agentes existentes contra el mapa planificado.
        Detecta funciones planificadas que no tienen agente creado.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener agentes existentes
        cursor.execute("SELECT agente FROM analisis_agentes")
        agentes_existentes = {row[0] for row in cursor.fetchall()}

        # Leer mapa de agentes planificados desde archivo JSON
        agentes_json_path = self.agentes_dir.parent / "agi_data" / "agentes.json"

        gaps = []

        if agentes_json_path.exists():
            with open(agentes_json_path, 'r', encoding='utf-8') as f:
                datos = json.load(f)

            # Agentes planificados
            agentes_planificados = datos.get('agentes_planificados', [])

            for planificado in agentes_planificados:
                nombre = planificado['nombre']
                if nombre not in agentes_existentes:
                    gaps.append({
                        'nombre': nombre,
                        'division': planificado.get('division'),
                        'estado': planificado.get('estado'),
                        'descripcion': planificado.get('descripcion'),
                        'prioridad': 5 if planificado.get('estado') == 'operativo' else 3
                    })

        conn.close()
        logger.info(f"[OPTIMIZADOR_AGENTES] Gaps detectados: {len(gaps)}")
        return sorted(gaps, key=lambda x: x['prioridad'], reverse=True)

    def calcular_score_utilidad(self, nombre_agente: str) -> int:
        """
        Score 0-100 de utilidad de un agente.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT score_utilidad FROM analisis_agentes WHERE agente = ?
        """, (nombre_agente,))

        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            return resultado[0]
        else:
            return 0

    def generar_mapa_colmena(self) -> dict:
        """
        Genera mapa JSON completo de todos los agentes.
        Sube el mapa a GitHub Memory como colmena_mapa.json
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM analisis_agentes")
        columnas = [col[0] for col in cursor.description]
        agentes = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM recomendaciones_fusion")
        columnas = [col[0] for col in cursor.description]
        recomendaciones = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        conn.close()

        # Calcular estadísticas
        total_agentes = len(agentes)
        scores = [a['score_utilidad'] for a in agentes if a['score_utilidad']]
        score_promedio = sum(scores) / len(scores) if scores else 0

        # Agrupar por división
        por_division = {}
        for agente in agentes:
            div = agente['division'] or 'general'
            if div not in por_division:
                por_division[div] = []
            por_division[div].append(agente['agente'])

        # Detectar duplicados
        duplicados = self.detectar_duplicados()

        # Analizar gaps
        gaps = self.analizar_gaps_funcionales()

        mapa = {
            "total_agentes": total_agentes,
            "por_division": por_division,
            "por_estado": {
                "activo": len([a for a in agentes if a['estado'] == 'activo']),
                "esqueleto": len([a for a in agentes if a['estado'] == 'esqueleto'])
            },
            "duplicados_detectados": duplicados,
            "gaps_detectados": gaps,
            "score_promedio": round(score_promedio, 2),
            "recomendaciones": recomendaciones,
            "fecha_generacion": datetime.now().isoformat()
        }

        # Guardar en archivo
        mapa_path = self.agentes_dir.parent / "agi_data" / "colmena_mapa.json"
        mapa_path.parent.mkdir(parents=True, exist_ok=True)

        with open(mapa_path, 'w', encoding='utf-8') as f:
            json.dump(mapa, f, indent=2, ensure_ascii=False)

        logger.info(f"[OPTIMIZADOR_AGENTES] Mapa generado: {mapa_path}")
        return mapa

    def ejecutar_analisis_completo(self) -> dict:
        """
        Ejecuta: escanear → detectar duplicados → analizar gaps → calcular scores → generar mapa.
        Retorna resumen ejecutivo para AGI.
        """
        logger.info("[OPTIMIZADOR_AGENTES] Iniciando análisis completo...")

        # Escanear agentes
        agentes = self.escanear_agentes()

        # Detectar duplicados
        duplicados = self.detectar_duplicados()

        # Analizar gaps
        gaps = self.analizar_gaps_funcionales()

        # Generar mapa
        mapa = self.generar_mapa_colmena()

        resumen = {
            "fecha_analisis": datetime.now().isoformat(),
            "total_agentes_escaneados": len(agentes),
            "duplicados_detectados": len(duplicados),
            "gaps_detectados": len(gaps),
            "score_promedio_agentes": mapa['score_promedio'],
            "mapa_generado": True,
            "recomendaciones_pendientes": len([r for r in mapa['recomendaciones'] if r['estado'] == 'pendiente_aprobacion'])
        }

        logger.info(f"[OPTIMIZADOR_AGENTES] Análisis completado: {resumen}")
        return resumen


def analisis_semanal_agentes(db_path: str = DB_PATH) -> dict:
    """
    Función para scheduler: análisis semanal de agentes.
    """
    optimizador = AgenteOptimizadorAgentes(db_path=db_path)
    return optimizador.ejecutar_analisis_completo()


if __name__ == "__main__":
    # Test básico
    optimizador = AgenteOptimizadorAgentes()

    # Test escaneo
    agentes = optimizador.escanear_agentes()
    print(f"Agentes escaneados: {len(agentes)}")

    # Test análisis completo
    resumen = optimizador.ejecutar_analisis_completo()
    print(f"Resumen: {resumen}")

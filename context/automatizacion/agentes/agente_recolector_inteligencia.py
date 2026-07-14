#!/usr/bin/env python3
"""
Agente Recolector Inteligente
===============================
Centraliza y coordina todos los recolectores existentes del proyecto.
Normaliza, deduplica y distribuye inteligencia a la Colmena.
"""

import sqlite3
import json
import logging
import importlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

DB_PATH = 'agi_memoria_telegram.db'
AGENTES_DIR = Path(__file__).parent

RECOLECTORES = {
    "nubes": "division_recursos_gratis.agente_recolector_nubes.AgenteRecolectorNubes",
    "estrategias": "division_biblioteca_fabrica_bots.agente_recolector_estrategias.AgenteRecolectorEstrategias",
    "recursos_varios": "division_recursos_gratis.agente_recolector_recursos_varios.AgenteRecolectorRecursosVarios"
}


class AgenteRecolectorInteligencia:
    """Recolector inteligente centralizado."""

    def __init__(self, db_path: str = DB_PATH, agentes_dir: Path = AGENTES_DIR):
        self.db_path = db_path
        self.agentes_dir = agentes_dir
        self._crear_tablas()

    def _crear_tablas(self):
        """Crea tablas SQLite si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inteligencia_recolectada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                fuente TEXT NOT NULL,
                recolector TEXT NOT NULL,
                categoria TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                url TEXT,
                datos_raw TEXT,
                relevancia_score INTEGER DEFAULT 50,
                procesado INTEGER DEFAULT 0,
                aplicado INTEGER DEFAULT 0,
                aplicado_en TEXT,
                fecha_expiracion TEXT,
                tags TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recolectores_estado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recolector TEXT UNIQUE NOT NULL,
                ultima_ejecucion TEXT,
                estado TEXT,
                items_recolectados INTEGER DEFAULT 0,
                errores_consecutivos INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1
            )
        """)

        conn.commit()
        conn.close()
        logger.info("[RECOLECTOR_INTELIGENTE] Tablas creadas/verificadas")

    def ejecutar_recolector(self, nombre_recolector: str) -> dict:
        """
        Ejecuta un recolector específico de forma segura.
        Captura errores sin que afecten a los demás recolectores.
        """
        if nombre_recolector not in RECOLECTORES:
            return {'error': f'Recolector {nombre_recolector} no existe', 'items': 0}

        ruta_modulo = RECOLECTORES[nombre_recolector]
        timestamp = datetime.now().isoformat()

        try:
            # Importar dinámicamente el recolector
            partes = ruta_modulo.split('.')
            nombre_clase = partes[-1]
            modulo_path = '.'.join(partes[:-1])

            # Añadir directorio padre al sys.path para imports relativos
            import sys
            sys.path.insert(0, str(self.agentes_dir))

            modulo = importlib.import_module(modulo_path)
            clase = getattr(modulo, nombre_clase)
            instancia = clase()

            # Ejecutar método principal si existe
            if hasattr(instancia, 'recolectar_todos'):
                resultado = instancia.recolectar_todos()
            elif hasattr(instancia, 'recolectar'):
                resultado = instancia.recolectar()
            else:
                resultado = {'items': []}

            items = resultado if isinstance(resultado, list) else resultado.get('items', [])
            items_count = len(items)

            # Actualizar estado del recolector
            self._actualizar_estado_recolector(nombre_recolector, 'exitoso', items_count, 0)

            logger.info(f"[RECOLECTOR_INTELIGENTE] {nombre_recolector}: {items_count} items recolectados")
            return {'recolector': nombre_recolector, 'items': items, 'estado': 'exitoso'}

        except Exception as e:
            logger.error(f"[RECOLECTOR_INTELIGENTE] Error en {nombre_recolector}: {e}")
            self._actualizar_estado_recolector(nombre_recolector, 'error', 0, 1)
            return {'recolector': nombre_recolector, 'error': str(e), 'items': 0}

    def _actualizar_estado_recolector(self, nombre: str, estado: str, items: int, errores: int):
        """Actualiza el estado de un recolector en SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT errores_consecutivos FROM recolectores_estado WHERE recolector = ?
        """, (nombre,))
        resultado = cursor.fetchone()

        if resultado:
            errores_actuales = resultado[0]
            nuevos_errores = errores_actuales + errores if estado == 'error' else 0

            # Si falla 3 veces consecutivas, marcar inactivo
            activo = 0 if nuevos_errores >= 3 else 1

            cursor.execute("""
                UPDATE recolectores_estado
                SET ultima_ejecucion = ?, estado = ?, items_recolectados = ?,
                    errores_consecutivos = ?, activo = ?
                WHERE recolector = ?
            """, (datetime.now().isoformat(), estado, items, nuevos_errores, activo, nombre))
        else:
            cursor.execute("""
                INSERT INTO recolectores_estado
                (recolector, ultima_ejecucion, estado, items_recolectados, errores_consecutivos, activo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, datetime.now().isoformat(), estado, items, errores, 1))

        conn.commit()
        conn.close()

    def normalizar_datos(self, datos_raw: dict, fuente: str) -> list:
        """
        Convierte el output de cualquier recolector al formato unificado.
        """
        if isinstance(datos_raw, list):
            return [self._normalizar_item(item, fuente) for item in datos_raw]
        elif isinstance(datos_raw, dict) and 'items' in datos_raw:
            return [self._normalizar_item(item, fuente) for item in datos_raw['items']]
        else:
            return [self._normalizar_item(datos_raw, fuente)]

    def _normalizar_item(self, item: dict, fuente: str) -> dict:
        """Normaliza un item individual al formato unificado."""
        return {
            'titulo': item.get('nombre', item.get('titulo', item.get('name', 'Sin título'))),
            'descripcion': item.get('descripcion', item.get('description', '')),
            'categoria': item.get('categoria', item.get('category', 'general')),
            'url': item.get('url', item.get('link', None)),
            'relevancia_score': 50,
            'tags': item.get('tags', []),
            'fecha_expiracion': item.get('fecha_expiracion', item.get('expiry', None)),
            'datos_raw': json.dumps(item)
        }

    def calcular_relevancia(self, item: dict) -> int:
        """
        Score 0-100 de relevancia de un item recolectado.
        """
        score = 0

        # ¿Es gratuito?
        if any(tag in item.get('tags', []) for tag in ['gratis', 'free', 'gratuito']):
            score += 30

        # ¿Es nuevo (simulado - en producción usaría timestamp de DB)?
        if item.get('relevancia_score', 50) > 50:
            score += 25

        # ¿Está relacionado con trading/IA/infra?
        texto_completo = f"{item['titulo']} {item['descripcion']} {' '.join(item.get('tags', []))}".lower()
        if any(palabra in texto_completo for palabra in ['trading', 'ia', 'ai', 'machine learning', 'infra', 'cloud', 'gpu']):
            score += 25

        # ¿Tiene fecha de expiración próxima?
        if item.get('fecha_expiracion'):
            score += 20

        return min(score, 100)

    def deduplicar(self, items: list) -> list:
        """
        Elimina duplicados comparando titulo y url.
        """
        vistos = set()
        items_unicos = []

        for item in items:
            clave = (item['titulo'], item.get('url', ''))
            if clave not in vistos:
                vistos.add(clave)
                items_unicos.append(item)

        return items_unicos

    def distribuir_a_colmena(self, items: list) -> dict:
        """
        Distribuye items procesados a las divisiones correspondientes.
        Retorna resumen de distribución.
        """
        distribucion = {
            'nube_gratuita': 0,
            'estrategia_trading': 0,
            'herramienta_ia': 0,
            'modelo_ia': 0,
            'api_gratuita': 0,
            'general': 0
        }

        for item in items:
            categoria = item.get('categoria', 'general').lower()

            if 'nube' in categoria or 'cloud' in categoria or 'vps' in categoria:
                distribucion['nube_gratuita'] += 1
            elif 'estrategia' in categoria or 'trading' in categoria:
                distribucion['estrategia_trading'] += 1
            elif 'herramienta' in categoria or 'tool' in categoria:
                distribucion['herramienta_ia'] += 1
            elif 'modelo' in categoria or 'model' in categoria:
                distribucion['modelo_ia'] += 1
            elif 'api' in categoria:
                distribucion['api_gratuita'] += 1
            else:
                distribucion['general'] += 1

        return distribucion

    def ejecutar_ciclo_completo(self) -> dict:
        """
        Ejecuta todos los recolectores activos en paralelo.
        Normaliza → deduplica → calcula relevancia → filtra → distribuye → guarda.
        """
        logger.info("[RECOLECTOR_INTELIGENTE] Iniciando ciclo completo...")

        # Obtener recolectores activos
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT recolector FROM recolectores_estado WHERE activo = 1")
        activos = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not activos:
            activos = list(RECOLECTORES.keys())

        # Ejecutar recolectores en paralelo
        todos_items = []
        recolectores_fallidos = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.ejecutar_recolector, nombre): nombre for nombre in activos}

            for future in as_completed(futures):
                nombre = futures[future]
                try:
                    resultado = future.result()
                    if 'error' in resultado:
                        recolectores_fallidos.append(nombre)
                    else:
                        todos_items.extend(resultado.get('items', []))
                except Exception as e:
                    logger.error(f"[RECOLECTOR_INTELIGENTE] Error ejecutando {nombre}: {e}")
                    recolectores_fallidos.append(nombre)

        # Normalizar datos
        items_normalizados = []
        for resultado in todos_items:
            if isinstance(resultado, dict):
                items_normalizados.extend(self.normalizar_datos(resultado, 'recolector'))

        # Calcular relevancia
        for item in items_normalizados:
            item['relevancia_score'] = self.calcular_relevancia(item)

        # Filtrar score < 30
        items_filtrados = [item for item in items_normalizados if item['relevancia_score'] >= 30]

        # Deduplicar
        items_unicos = self.deduplicar(items_filtrados)

        # Distribuir
        distribucion = self.distribuir_a_colmena(items_unicos)

        # Guardar en SQLite
        total_guardados = self._guardar_inteligencia(items_unicos)

        resumen = {
            'total_recolectado': len(todos_items),
            'total_nuevo': len(items_unicos),
            'total_distribuido': total_guardados,
            'por_categoria': distribucion,
            'recolectores_fallidos': recolectores_fallidos,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"[RECOLECTOR_INTELIGENTE] Ciclo completado: {resumen}")
        return resumen

    def _guardar_inteligencia(self, items: list) -> int:
        """Guarda items de inteligencia en SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        guardados = 0

        for item in items:
            try:
                cursor.execute("""
                    INSERT INTO inteligencia_recolectada
                    (timestamp, fuente, recolector, categoria, titulo, descripcion,
                     url, datos_raw, relevancia_score, tags, fecha_expiracion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    'recolector_inteligente',
                    'multiple',
                    item.get('categoria', 'general'),
                    item['titulo'],
                    item['descripcion'],
                    item.get('url'),
                    item.get('datos_raw', json.dumps(item)),
                    item['relevancia_score'],
                    json.dumps(item.get('tags', [])),
                    item.get('fecha_expiracion')
                ))
                guardados += 1
            except Exception as e:
                logger.error(f"[RECOLECTOR_INTELIGENTE] Error guardando item: {e}")

        conn.commit()
        conn.close()
        return guardados

    def obtener_inteligencia_pendiente(
        self,
        categoria: str = None,
        min_relevancia: int = 50
    ) -> list:
        """
        Retorna items recolectados no procesados aún.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM inteligencia_recolectada WHERE procesado = 0 AND relevancia_score >= ?"
        params = [min_relevancia]

        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)

        query += " ORDER BY relevancia_score DESC"

        cursor.execute(query, params)
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        conn.close()
        return resultados

    def marcar_aplicado(self, item_id: int, aplicado_en: str) -> bool:
        """
        Marca un item de inteligencia como aplicado.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE inteligencia_recolectada
            SET aplicado = 1, aplicado_en = ?, procesado = 1
            WHERE id = ?
        """, (aplicado_en, item_id))

        filas = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"[RECOLECTOR_INTELIGENTE] Item {item_id} marcado como aplicado en {aplicado_en}")
        return filas > 0


def ciclo_recoleccion_inteligencia(db_path: str = DB_PATH) -> dict:
    """
    Función para scheduler: ciclo de recolección cada 6 horas.
    """
    recolector = AgenteRecolectorInteligencia(db_path=db_path)
    return recolector.ejecutar_ciclo_completo()


if __name__ == "__main__":
    # Test básico
    recolector = AgenteRecolectorInteligencia()

    # Test ejecutar recolector individual
    resultado = recolector.ejecutar_recolector("nubes")
    print(f"Recolector nubes: {resultado}")

    # Test ciclo completo
    resumen = recolector.ejecutar_ciclo_completo()
    print(f"Resumen ciclo completo: {resumen}")

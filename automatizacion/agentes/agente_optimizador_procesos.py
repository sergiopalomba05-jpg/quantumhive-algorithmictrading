#!/usr/bin/env python3
"""
Agente Optimizador de Errores y Procesos
========================================
Memoria institucional de errores de QuantumHive.
Registra errores, soluciones y procesos óptimos.
"""

import sqlite3
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = 'agi_memoria_telegram.db'

ERRORES_HISTORICOS = [
    {
        "proceso": "deploy_render",
        "tipo_error": "modelo_deprecado",
        "descripcion": "llama3-70b-8192 decommissioned",
        "causa_raiz": "Groq deprecó el modelo sin aviso previo",
        "solucion_aplicada": "Ejecutar agente_investigacion_modelos.py para obtener modelo activo, actualizar llm_wrapper.py",
        "prevencion_futura": "Siempre consultar agente_investigacion_modelos.py antes de hardcodear cualquier modelo Groq",
        "tiempo_resolucion_minutos": 120,
        "veces_ocurrido": 2,
        "tags": ["groq", "modelo", "deploy", "render"]
    },
    {
        "proceso": "deploy_render",
        "tipo_error": "variable_faltante",
        "descripcion": "LLM_ENGINE y GROQ_API_KEY no configuradas en Render",
        "causa_raiz": "Variables definidas en .env local pero no agregadas en Render dashboard",
        "solucion_aplicada": "Agregar variables via agente_render.py con método PUT /env-vars",
        "prevencion_futura": "Checklist de variables antes de cada deploy: verificar que todas las del .env estén en Render",
        "tiempo_resolucion_minutos": 90,
        "veces_ocurrido": 3,
        "tags": ["render", "variables", "deploy", "env"]
    },
    {
        "proceso": "agente_render",
        "tipo_error": "endpoint_incorrecto",
        "descripcion": "Error 405 Method Not Allowed al agregar variables",
        "causa_raiz": "Endpoint POST incorrecto, Render API usa PUT para env-vars",
        "solucion_aplicada": "Cambiar POST por PUT en agente_render.py endpoint /services/{id}/env-vars",
        "prevencion_futura": "Siempre verificar método HTTP correcto en documentación de Render API antes de implementar",
        "tiempo_resolucion_minutos": 45,
        "veces_ocurrido": 1,
        "tags": ["render", "api", "http", "405"]
    },
    {
        "proceso": "agente_seguridad",
        "tipo_error": "dependencia_incorrecta",
        "descripcion": "cannot import name PBKDF2 from cryptography",
        "causa_raiz": "API cambió en versión actual de cryptography, clase correcta es PBKDF2HMAC",
        "solucion_aplicada": "Reemplazar PBKDF2 por PBKDF2HMAC en agente_seguridad.py",
        "prevencion_futura": "Verificar versión de librería y su API antes de usar clases específicas",
        "tiempo_resolucion_minutos": 30,
        "veces_ocurrido": 1,
        "tags": ["cryptography", "importerror", "dependencia"]
    },
    {
        "proceso": "logs_render",
        "tipo_error": "endpoint_incorrecto",
        "descripcion": "Error 404 al obtener logs de Render",
        "causa_raiz": "Endpoint de logs de Render API diferente al implementado en agente_render.py",
        "solucion_aplicada": "Pendiente resolución — verificar documentación Render API para logs endpoint",
        "prevencion_futura": "Verificar endpoint correcto en docs.render.com antes de implementar",
        "tiempo_resolucion_minutos": 0,
        "resuelto": 0,
        "tags": ["render", "logs", "404", "api"]
    }
]


class AgenteOptimizadorProcesos:
    """Memoria institucional de errores y procesos óptimos."""

    def __init__(self, db_path: str = DB_PATH, event_bus=None):
        self.db_path = db_path
        self.event_bus = event_bus
        self._crear_tablas()
        self._precargar_errores_historicos()

    def _crear_tablas(self):
        """Crea tablas SQLite si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errores_procesos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                proceso TEXT NOT NULL,
                agente TEXT,
                tipo_error TEXT NOT NULL,
                descripcion_error TEXT NOT NULL,
                causa_raiz TEXT,
                solucion_aplicada TEXT,
                tiempo_resolucion_minutos INTEGER,
                resuelto INTEGER DEFAULT 0,
                recurrente INTEGER DEFAULT 0,
                veces_ocurrido INTEGER DEFAULT 1,
                impacto TEXT,
                prevencion_futura TEXT,
                tags TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS procesos_optimizados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                proceso TEXT NOT NULL,
                descripcion TEXT,
                pasos_optimos TEXT,
                prerequisitos TEXT,
                errores_conocidos TEXT,
                tiempo_estimado_minutos INTEGER,
                ultima_ejecucion_exitosa TEXT,
                veces_ejecutado INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.info("[OPTIMIZADOR] Tablas creadas/verificadas")

    def _precargar_errores_historicos(self):
        """Precarga errores históricos si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for error in ERRORES_HISTORICOS:
            cursor.execute("""
                SELECT COUNT(*) FROM errores_procesos
                WHERE proceso = ? AND tipo_error = ?
            """, (error["proceso"], error["tipo_error"]))

            if cursor.fetchone()[0] == 0:
                timestamp = datetime.now().isoformat()
                tags_json = json.dumps(error.get("tags", []))

                cursor.execute("""
                    INSERT INTO errores_procesos (
                        timestamp, proceso, tipo_error, descripcion_error,
                        causa_raiz, solucion_aplicada, tiempo_resolucion_minutos,
                        resuelto, veces_ocurrido, prevencion_futura, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    error["proceso"],
                    error["tipo_error"],
                    error["descripcion"],
                    error.get("causa_raiz"),
                    error.get("solucion_aplicada"),
                    error.get("tiempo_resolucion_minutos"),
                    error.get("resuelto", 1),
                    error.get("veces_ocurrido", 1),
                    error.get("prevencion_futura"),
                    tags_json
                ))

        conn.commit()
        conn.close()
        logger.info("[OPTIMIZADOR] Errores históricos precargados")

    def registrar_error(
        self,
        proceso: str,
        tipo_error: str,
        descripcion: str,
        agente: str = None,
        causa_raiz: str = None,
        impacto: str = None,
        tags: list = None
    ) -> dict:
        """
        Registra un error nuevo en SQLite.
        Si el error ya existe, incrementa veces_ocurrido y marca como recurrente.
        Publica evento en Event Bus: tipo='error_registrado'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar si error ya existe
        cursor.execute("""
            SELECT id, veces_ocurrido FROM errores_procesos
            WHERE proceso = ? AND tipo_error = ?
        """, (proceso, tipo_error))

        existente = cursor.fetchone()

        timestamp = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])

        if existente:
            error_id, veces = existente
            cursor.execute("""
                UPDATE errores_procesos
                SET veces_ocurrido = veces_ocurrido + 1,
                    recurrente = 1,
                    timestamp = ?
                WHERE id = ?
            """, (timestamp, error_id))
            logger.info(f"[OPTIMIZADOR] Error recurrente: {proceso} - {tipo_error}")
        else:
            cursor.execute("""
                INSERT INTO errores_procesos (
                    timestamp, proceso, agente, tipo_error, descripcion_error,
                    causa_raiz, impacto, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, proceso, agente, tipo_error, descripcion, causa_raiz, impacto, tags_json))
            error_id = cursor.lastrowid
            logger.info(f"[OPTIMIZADOR] Error nuevo registrado: {proceso} - {tipo_error}")

        conn.commit()

        # Publicar evento en Event Bus
        if self.event_bus:
            self.event_bus.publicar(
                tipo='error_registrado',
                origen='agente_optimizador_procesos',
                payload={'error_id': error_id, 'proceso': proceso, 'tipo': tipo_error}
            )

        conn.close()

        return {'id': error_id, 'proceso': proceso, 'tipo_error': tipo_error, 'timestamp': timestamp}

    def registrar_solucion(
        self,
        error_id: int,
        solucion: str,
        tiempo_resolucion_minutos: int,
        prevencion_futura: str = None
    ) -> dict:
        """
        Marca el error como resuelto.
        Guarda la solución y el tiempo que tomó.
        Actualiza procesos_optimizados con el aprendizaje.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE errores_procesos
            SET solucion_aplicada = ?, tiempo_resolucion_minutos = ?,
                resuelto = 1, prevencion_futura = ?
            WHERE id = ?
        """, (solucion, tiempo_resolucion_minutos, prevencion_futura, error_id))

        # Obtener info del error para actualizar proceso óptimo
        cursor.execute("""
            SELECT proceso, descripcion_error FROM errores_procesos WHERE id = ?
        """, (error_id,))
        error_info = cursor.fetchone()

        if error_info:
            proceso, descripcion = error_info

            # Actualizar o crear proceso óptimo
            cursor.execute("""
                SELECT id, errores_conocidos FROM procesos_optimizados WHERE proceso = ?
            """, (proceso,))
            proc_info = cursor.fetchone()

            if proc_info:
                proc_id, errores_json = proc_info
                errores = json.loads(errores_json) if errores_json else []
                errores.append({
                    'tipo': cursor.execute("SELECT tipo_error FROM errores_procesos WHERE id = ?", (error_id,)).fetchone()[0],
                    'solucion': solucion
                })
                cursor.execute("""
                    UPDATE procesos_optimizados
                    SET errores_conocidos = ?, ultima_ejecucion_exitosa = ?
                    WHERE id = ?
                """, (json.dumps(errores), datetime.now().isoformat(), proc_id))
            else:
                cursor.execute("""
                    INSERT INTO procesos_optimizados (
                        timestamp, proceso, descripcion, errores_conocidos,
                        ultima_ejecucion_exitosa
                    ) VALUES (?, ?, ?, ?, ?)
                """, (datetime.now().isoformat(), proceso, descripcion,
                      json.dumps([{'tipo': cursor.execute("SELECT tipo_error FROM errores_procesos WHERE id = ?", (error_id,)).fetchone()[0], 'solucion': solucion}]),
                      datetime.now().isoformat()))

        conn.commit()
        conn.close()

        logger.info(f"[OPTIMIZADOR] Solución registrada para error_id {error_id}")
        return {'error_id': error_id, 'solucion': solucion}

    def consultar_errores_similares(
        self,
        proceso: str = None,
        tipo_error: str = None,
        tags: list = None
    ) -> list:
        """
        Busca errores similares en la base de datos.
        Retorna lista ordenada por veces_ocurrido DESC.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM errores_procesos WHERE 1=1"
        params = []

        if proceso:
            query += " AND proceso = ?"
            params.append(proceso)

        if tipo_error:
            query += " AND tipo_error = ?"
            params.append(tipo_error)

        if tags:
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f"%{tag}%")

        query += " ORDER BY veces_ocurrido DESC"

        cursor.execute(query, params)
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        conn.close()
        return resultados

    def obtener_solucion_rapida(self, descripcion_error: str) -> dict:
        """
        Búsqueda por texto libre en descripcion_error y causa_raiz.
        Retorna el error más similar con su solución si existe.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM errores_procesos
            WHERE solucion_aplicada IS NOT NULL AND resuelto = 1
        """)

        columnas = [col[0] for col in cursor.description]
        errores = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        conn.close()

        # Búsqueda simple por coincidencia de palabras
        mejor_match = None
        mejor_score = 0

        palabras_busqueda = set(re.findall(r'\w+', descripcion_error.lower()))

        for error in errores:
            texto = f"{error['descripcion_error']} {error.get('causa_raiz', '')}".lower()
            palabras_error = set(re.findall(r'\w+', texto))

            interseccion = palabras_busqueda & palabras_error
            score = len(interseccion)

            if score > mejor_score and score >= 2:
                mejor_score = score
                mejor_match = error

        if mejor_match:
            confianza = "alta" if mejor_score >= 4 else "media" if mejor_score >= 3 else "baja"
            return {
                'encontrado': True,
                'error_similar': mejor_match,
                'solucion': mejor_match['solucion_aplicada'],
                'confianza': confianza
            }
        else:
            return {'encontrado': False}

    def registrar_proceso_optimo(
        self,
        proceso: str,
        descripcion: str,
        pasos: list,
        prerequisitos: list = None,
        tiempo_estimado: int = None
    ) -> dict:
        """
        Registra el paso a paso óptimo de un proceso.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        pasos_json = json.dumps(pasos)
        prerequisitos_json = json.dumps(prerequisitos or [])

        cursor.execute("""
            INSERT INTO procesos_optimizados (
                timestamp, proceso, descripcion, pasos_optimos,
                prerequisitos, tiempo_estimado_minutos
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), proceso, descripcion, pasos_json, prerequisitos_json, tiempo_estimado))

        conn.commit()
        proc_id = cursor.lastrowid
        conn.close()

        logger.info(f"[OPTIMIZADOR] Proceso óptimo registrado: {proceso}")
        return {'id': proc_id, 'proceso': proceso}

    def obtener_proceso_optimo(self, proceso: str) -> dict:
        """
        Retorna el paso a paso óptimo de un proceso si existe.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM procesos_optimizados WHERE proceso = ?
        """, (proceso,))

        columnas = [col[0] for col in cursor.description]
        resultado = cursor.fetchone()

        conn.close()

        if resultado:
            proceso_dict = dict(zip(columnas, resultado))
            return proceso_dict
        else:
            return None

    def generar_reporte_errores(self, dias: int = 7) -> dict:
        """
        Reporte de los últimos N días.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        fecha_limite = (datetime.now().timestamp() - dias * 86400)
        fecha_limite_iso = datetime.fromtimestamp(fecha_limite).isoformat()

        cursor.execute("""
            SELECT proceso, COUNT(*) as total, SUM(resuelto) as resueltos
            FROM errores_procesos
            WHERE timestamp >= ?
            GROUP BY proceso
            ORDER BY total DESC
        """, (fecha_limite_iso,))

        errores_por_proceso = [{'proceso': row[0], 'total': row[1], 'resueltos': row[2]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT COUNT(*) FROM errores_procesos
            WHERE timestamp >= ? AND recurrente = 1
        """, (fecha_limite_iso,))
        recurrentes = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM errores_procesos
            WHERE timestamp >= ? AND resuelto = 0
        """, (fecha_limite_iso,))
        sin_resolver = cursor.fetchone()[0]

        cursor.execute("""
            SELECT AVG(tiempo_resolucion_minutos) FROM errores_procesos
            WHERE timestamp >= ? AND tiempo_resolucion_minutos > 0
        """, (fecha_limite_iso,))
        tiempo_promedio = cursor.fetchone()[0] or 0

        conn.close()

        reporte = {
            'periodo_dias': dias,
            'fecha_generacion': datetime.now().isoformat(),
            'errores_por_proceso': errores_por_proceso[:5],
            'recurrentes': recurrentes,
            'sin_resolver': sin_resolver,
            'tiempo_promedio_resolucion_minutos': round(tiempo_promedio, 2)
        }

        return reporte

    def analizar_patron_errores(self) -> dict:
        """
        Analiza patrones en los errores registrados.
        Publica evento en Event Bus: tipo='patron_detectado'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT proceso, COUNT(*) as total FROM errores_procesos
            GROUP BY proceso ORDER BY total DESC LIMIT 5
        """)
        procesos_fallidos = [{'proceso': row[0], 'total': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT agente, COUNT(*) as total FROM errores_procesos
            WHERE agente IS NOT NULL
            GROUP BY agente ORDER BY total DESC LIMIT 5
        """)
        agentes_fallidos = [{'agente': row[0], 'total': row[1]} for row in cursor.fetchall()]

        conn.close()

        patron = {
            'procesos_con_mas_errores': procesos_fallidos,
            'agentes_con_mas_errores': agentes_fallidos,
            'fecha_analisis': datetime.now().isoformat()
        }

        if self.event_bus:
            self.event_bus.publicar(
                tipo='patron_detectado',
                origen='agente_optimizador_procesos',
                payload=patron
            )

        return patron

    def registrar_error_deploy(
        self,
        error_log: str,
        modelo_ia: str = None,
        variable_faltante: str = None
    ) -> dict:
        """
        Método específico para errores de deploy en Render.
        Detecta automáticamente el tipo de error del log.
        """
        tipo_error = "desconocido"
        descripcion = error_log[:500]
        causa_raiz = None
        prevencion = None

        if "decommissioned" in error_log.lower() or "not found" in error_log.lower():
            tipo_error = "modelo_deprecado"
            causa_raiz = "Modelo de IA deprecado o no disponible"
            prevencion = "Consultar agente_investigacion_modelos.py antes de deploy"
        elif "not configured" in error_log.lower() or "missing" in error_log.lower():
            tipo_error = "variable_faltante"
            causa_raiz = "Variable de entorno no configurada"
            prevencion = "Verificar checklist de variables antes de cada deploy"
        elif "timeout" in error_log.lower():
            tipo_error = "timeout"
            causa_raiz = "Timeout en deploy o ejecución"
            prevencion = "Optimizar tiempos de espera o dividir proceso"
        elif "ModuleNotFoundError" in error_log:
            tipo_error = "dependencia_faltante"
            causa_raiz = "Dependencia de Python no instalada"
            prevencion = "Verificar requirements.txt antes de deploy"

        return self.registrar_error(
            proceso="deploy_render",
            tipo_error=tipo_error,
            descripcion=descripcion,
            agente="agente_render",
            causa_raiz=causa_raiz,
            impacto="alto",
            tags=["deploy", "render", tipo_error],
            prevencion_futura=prevencion
        )


def generar_reporte_errores_diario(db_path: str = DB_PATH) -> dict:
    """
    Función para scheduler: genera reporte diario de errores.
    """
    optimizador = AgenteOptimizadorProcesos(db_path=db_path)
    return optimizador.generar_reporte_errores(dias=1)


if __name__ == "__main__":
    # Test básico
    optimizador = AgenteOptimizadorProcesos()

    # Test registrar error
    resultado = optimizador.registrar_error(
        proceso="test_proceso",
        tipo_error="test_error",
        descripcion="Error de prueba"
    )
    print(f"Error registrado: {resultado}")

    # Test consultar errores
    similares = optimizador.consultar_errores_similares(proceso="deploy_render")
    print(f"Errores similares encontrados: {len(similares)}")

    # Test solución rápida
    solucion = optimizador.obtener_solucion_rapida("llama3-70b decommissioned")
    print(f"Solución rápida: {solucion}")

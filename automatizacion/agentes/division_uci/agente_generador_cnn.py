"""
Agente Generador CNN - D18: UCI (Unidad de Conocimiento e Inteligencia)
Genera contenido educativo utilizando redes neuronales

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Utiliza redes neuronales para generar contenido educativo
             de trading basado en el conocimiento almacenado.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteGeneradorCNN:
    """Genera contenido educativo utilizando redes neuronales."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente generador CNN.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._init_db()
        
    def _init_db(self):
        """Inicializa la conexión a la base de datos."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._crear_tablas()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar base de datos: {e}")
            raise
            
    def _crear_tablas(self):
        """Crea las tablas necesarias si no existen."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS modelos_cnn (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    tipo_modelo TEXT NOT NULL,
                    arquitectura TEXT,
                    fecha_entrenamiento DATETIME,
                    metricas TEXT,
                    estado TEXT NOT NULL,
                    ruta_modelo TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS solicitudes_generacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    modelo_id INTEGER NOT NULL,
                    tipo_contenido TEXT NOT NULL,
                    tema TEXT NOT NULL,
                    parametros TEXT,
                    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    prioridad INTEGER DEFAULT 0,
                    FOREIGN KEY (modelo_id) REFERENCES modelos_cnn(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS contenido_generado (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    solicitud_id INTEGER NOT NULL,
                    contenido TEXT NOT NULL,
                    tipo_contenido TEXT NOT NULL,
                    calidad REAL DEFAULT 0,
                    tokens_generados INTEGER DEFAULT 0,
                    tiempo_generacion REAL,
                    fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    modelo_utilizado TEXT NOT NULL,
                    FOREIGN KEY (solicitud_id) REFERENCES solicitudes_generacion(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS plantillas_contenido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    tipo_contenido TEXT NOT NULL,
                    estructura TEXT NOT NULL,
                    prompt_base TEXT,
                    parametros_requeridos TEXT,
                    activa BOOLEAN DEFAULT TRUE
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluaciones_contenido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contenido_id INTEGER NOT NULL,
                    evaluador TEXT NOT NULL,
                    puntuacion INTEGER NOT NULL,
                    comentarios TEXT,
                    fecha_evaluacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contenido_id) REFERENCES contenido_generado(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_modelo(self, nombre: str, tipo_modelo: str, arquitectura: str = None,
                        metricas: dict = None, ruta_modelo: str = None) -> int:
        """
        Registra un modelo CNN.
        
        Args:
            nombre: Nombre del modelo
            tipo_modelo: Tipo de modelo (GENERADOR, CLASIFICADOR, EMBEDDING)
            arquitectura: Arquitectura del modelo
            metricas: Métricas de rendimiento
            ruta_modelo: Ruta del modelo guardado
            
        Returns:
            ID del modelo
        """
        try:
            metricas_json = json.dumps(metricas) if metricas else None
            
            self.cursor.execute("""
                INSERT INTO modelos_cnn
                (nombre, tipo_modelo, arquitectura, metricas, estado, ruta_modelo)
                VALUES (?, ?, ?, ?, 'ACTIVO', ?)
            """, (nombre, tipo_modelo, arquitectura, metricas_json, ruta_modelo))
            
            self.conn.commit()
            modelo_id = self.cursor.lastrowid
            logger.info(f"Modelo CNN registrado - ID: {modelo_id} - Nombre: {nombre}")
            return modelo_id
        except Exception as e:
            logger.error(f"Error al registrar modelo: {e}")
            raise
            
    def crear_plantilla(self, nombre: str, tipo_contenido: str, estructura: dict,
                       prompt_base: str = None, parametros_requeridos: List[str] = None) -> int:
        """
        Crea una plantilla de contenido.
        
        Args:
            nombre: Nombre de la plantilla
            tipo_contenido: Tipo de contenido (ARTICULO, TUTORIAL, GUIA)
            estructura: Estructura del contenido
            prompt_base: Prompt base para generación
            parametros_requeridos: Parámetros requeridos
            
        Returns:
            ID de la plantilla
        """
        try:
            estructura_json = json.dumps(estructura)
            parametros_json = json.dumps(parametros_requeridos) if parametros_requeridos else None
            
            self.cursor.execute("""
                INSERT INTO plantillas_contenido
                (nombre, tipo_contenido, estructura, prompt_base, parametros_requeridos, activa)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (nombre, tipo_contenido, estructura_json, prompt_base, parametros_json))
            
            self.conn.commit()
            plantilla_id = self.cursor.lastrowid
            logger.info(f"Plantilla creada - ID: {plantilla_id} - Nombre: {nombre}")
            return plantilla_id
        except Exception as e:
            logger.error(f"Error al crear plantilla: {e}")
            raise
            
    def solicitar_generacion(self, modelo_id: int, tipo_contenido: str, tema: str,
                           parametros: dict = None, prioridad: int = 0) -> int:
        """
        Solicita la generación de contenido.
        
        Args:
            modelo_id: ID del modelo a usar
            tipo_contenido: Tipo de contenido
            tema: Tema del contenido
            parametros: Parámetros adicionales
            prioridad: Prioridad de la solicitud
            
        Returns:
            ID de la solicitud
        """
        try:
            parametros_json = json.dumps(parametros) if parametros else None
            
            self.cursor.execute("""
                INSERT INTO solicitudes_generacion
                (modelo_id, tipo_contenido, tema, parametros, estado, prioridad)
                VALUES (?, ?, ?, ?, 'PENDIENTE', ?)
            """, (modelo_id, tipo_contenido, tema, parametros_json, prioridad))
            
            self.conn.commit()
            solicitud_id = self.cursor.lastrowid
            logger.info(f"Solicitud de generación creada - ID: {solicitud_id} - Tema: {tema}")
            return solicitud_id
        except Exception as e:
            logger.error(f"Error al solicitar generación: {e}")
            raise
            
    def generar_contenido(self, solicitud_id: int, contenido: str, calidad: float = 0.8,
                        tokens_generados: int = 0, tiempo_generacion: float = 0,
                        modelo_utilizado: str = None) -> int:
        """
        Genera contenido basado en una solicitud.
        
        Args:
            solicitud_id: ID de la solicitud
            contenido: Contenido generado
            calidad: Calidad del contenido
            tokens_generados: Cantidad de tokens
            tiempo_generacion: Tiempo de generación
            modelo_utilizado: Modelo utilizado
            
        Returns:
            ID del contenido generado
        """
        try:
            # Obtener modelo de la solicitud
            self.cursor.execute("""
                SELECT modelo_id FROM solicitudes_generacion WHERE id = ?
            """, (solicitud_id,))
            modelo_id = self.cursor.fetchone()[0]
            
            # Obtener nombre del modelo
            self.cursor.execute("""
                SELECT nombre FROM modelos_cnn WHERE id = ?
            """, (modelo_id,))
            nombre_modelo = self.cursor.fetchone()[0]
            
            if not modelo_utilizado:
                modelo_utilizado = nombre_modelo
                
            self.cursor.execute("""
                INSERT INTO contenido_generado
                (solicitud_id, contenido, tipo_contenido, calidad, tokens_generados,
                 tiempo_generacion, modelo_utilizado)
                SELECT ?, ?, tipo_contenido, ?, ?, ?, ?
                FROM solicitudes_generacion WHERE id = ?
            """, (solicitud_id, contenido, calidad, tokens_generados,
                  tiempo_generacion, modelo_utilizado, solicitud_id))
            
            self.conn.commit()
            contenido_id = self.cursor.lastrowid
            
            # Actualizar estado de la solicitud
            self.cursor.execute("""
                UPDATE solicitudes_generacion SET estado = 'COMPLETADO' WHERE id = ?
            """, (solicitud_id,))
            self.conn.commit()
            
            logger.info(f"Contenido generado - ID: {contenido_id} - Solicitud: {solicitud_id}")
            return contenido_id
        except Exception as e:
            logger.error(f"Error al generar contenido: {e}")
            raise
            
    def evaluar_contenido(self, contenido_id: int, evaluador: str, puntuacion: int,
                         comentarios: str = None) -> int:
        """
        Evalúa el contenido generado.
        
        Args:
            contenido_id: ID del contenido
            evaluador: Quién evalúa
            puntuacion: Puntuación (1-10)
            comentarios: Comentarios
            
        Returns:
            ID de la evaluación
        """
        try:
            self.cursor.execute("""
                INSERT INTO evaluaciones_contenido
                (contenido_id, evaluador, puntuacion, comentarios)
                VALUES (?, ?, ?, ?)
            """, (contenido_id, evaluador, puntuacion, comentarios))
            
            self.conn.commit()
            evaluacion_id = self.cursor.lastrowid
            logger.info(f"Evaluación registrada - ID: {evaluacion_id} - Puntuación: {puntuacion}")
            return evaluacion_id
        except Exception as e:
            logger.error(f"Error al evaluar contenido: {e}")
            raise
            
    def obtener_modelos(self, tipo: str = None, estado: str = "ACTIVO") -> List[Dict]:
        """Obtiene modelos CNN registrados."""
        try:
            query = "SELECT * FROM modelos_cnn"
            params = []
            
            conditions = []
            if tipo:
                conditions.append("tipo_modelo = ?")
                params.append(tipo)
            if estado:
                conditions.append("estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'nombre': r[1], 'tipo_modelo': r[2], 'arquitectura': r[3],
                'fecha_entrenamiento': r[4], 'metricas': json.loads(r[5]) if r[5] else None,
                'estado': r[6], 'ruta_modelo': r[7], 'timestamp': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener modelos: {e}")
            return []
            
    def obtener_solicitudes(self, estado: str = None) -> List[Dict]:
        """Obtiene solicitudes de generación."""
        try:
            if estado:
                self.cursor.execute("""
                    SELECT * FROM solicitudes_generacion WHERE estado = ? ORDER BY prioridad DESC, fecha_solicitud ASC
                """, (estado,))
            else:
                self.cursor.execute("""
                    SELECT * FROM solicitudes_generacion ORDER BY prioridad DESC, fecha_solicitud ASC
                """)
                
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'modelo_id': r[1], 'tipo_contenido': r[2], 'tema': r[3],
                'parametros': json.loads(r[4]) if r[4] else None, 'fecha_solicitud': r[5],
                'estado': r[6], 'prioridad': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener solicitudes: {e}")
            return []
            
    def obtener_contenido_generado(self, solicitud_id: int = None) -> List[Dict]:
        """Obtiene contenido generado."""
        try:
            if solicitud_id:
                self.cursor.execute("""
                    SELECT * FROM contenido_generado WHERE solicitud_id = ?
                """, (solicitud_id,))
            else:
                self.cursor.execute("""
                    SELECT * FROM contenido_generado ORDER BY fecha_generacion DESC LIMIT 50
                """)
                
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'solicitud_id': r[1], 'contenido': r[2], 'tipo_contenido': r[3],
                'calidad': r[4], 'tokens_generados': r[5], 'tiempo_generacion': r[6],
                'fecha_generacion': r[7], 'modelo_utilizado': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener contenido: {e}")
            return []
            
    def obtener_plantillas(self, tipo: str = None) -> List[Dict]:
        """Obtiene plantillas de contenido."""
        try:
            if tipo:
                self.cursor.execute("""
                    SELECT * FROM plantillas_contenido WHERE tipo_contenido = ? AND activa = TRUE
                """, (tipo,))
            else:
                self.cursor.execute("""
                    SELECT * FROM plantillas_contenido WHERE activa = TRUE
                """)
                
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'nombre': r[1], 'tipo_contenido': r[2],
                'estructura': json.loads(r[3]), 'prompt_base': r[4],
                'parametros_requeridos': json.loads(r[5]) if r[5] else None, 'activa': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener plantillas: {e}")
            return []
            
    def obtener_estadisticas(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de generación."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_solicitudes,
                    SUM(CASE WHEN estado = 'COMPLETADO' THEN 1 ELSE 0 END) as completadas,
                    SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes,
                    AVG(c.tokens_generados) as avg_tokens,
                    AVG(c.tiempo_generacion) as avg_tiempo
                FROM solicitudes_generacion s
                LEFT JOIN contenido_generado c ON s.id = c.solicitud_id
                WHERE s.fecha_solicitud >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, completadas, pendientes, avg_tokens, avg_tiempo = result
                return {
                    'total_solicitudes': total or 0,
                    'completadas': completadas or 0,
                    'pendientes': pendientes or 0,
                    'tasa_completamiento': round((completadas / total * 100) if total > 0 else 0, 2),
                    'avg_tokens': round(avg_tokens or 0, 0),
                    'avg_tiempo': round(avg_tiempo or 0, 2),
                    'periodo_dias': dias
                }
            return {}
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}
            
    def cerrar(self):
        """Cierra la conexión a la base de datos."""
        try:
            if self.conn:
                self.conn.close()
                logger.info("Conexión a base de datos cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {e}")


if __name__ == "__main__":
    # Ejemplo de uso
    logging.basicConfig(level=logging.INFO)
    
    agente = AgenteGeneradorCNN()
    
    # Ejemplo: registrar modelo
    modelo_id = agente.registrar_modelo(
        nombre="GPT-QuantumHive",
        tipo_modelo="GENERADOR",
        arquitectura="Transformer-12L",
        metricas={"perplexity": 0.85, "accuracy": 0.92},
        ruta_modelo="/models/gpt-qh.pt"
    )
    
    print(f"Modelo registrado - ID: {modelo_id}")
    
    # Ejemplo: crear plantilla
    plantilla_id = agente.crear_plantilla(
        nombre="Articulo Trading",
        tipo_contenido="ARTICULO",
        estructura={"titulo": "str", "introduccion": "str", "cuerpo": "list", "conclusion": "str"},
        prompt_base="Escribe un artículo sobre {tema} para traders de nivel {nivel}",
        parametros_requeridos=["tema", "nivel"]
    )
    
    print(f"Plantilla creada - ID: {plantilla_id}")
    
    # Ejemplo: solicitar generación
    solicitud_id = agente.solicitar_generacion(
        modelo_id=modelo_id,
        tipo_contenido="ARTICULO",
        tema="Scalping en Forex",
        parametros={"nivel": "intermedio", "longitud": 1000},
        prioridad=1
    )
    
    print(f"Solicitud creada - ID: {solicitud_id}")
    
    # Ejemplo: generar contenido
    contenido_id = agente.generar_contenido(
        solicitud_id=solicitud_id,
        contenido="El scalping es una técnica de trading...",
        calidad=0.9,
        tokens_generados=850,
        tiempo_generacion=2.5,
        modelo_utilizado="GPT-QuantumHive"
    )
    
    print(f"Contenido generado - ID: {contenido_id}")
    
    # Ejemplo: evaluar contenido
    evaluacion_id = agente.evaluar_contenido(
        contenido_id=contenido_id,
        evaluador="Experto Trading",
        puntuacion=8,
        comentarios="Buen contenido, pero podría tener más ejemplos"
    )
    
    print(f"Evaluación registrada - ID: {evaluacion_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

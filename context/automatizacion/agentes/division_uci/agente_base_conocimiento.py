"""
Agente Base Conocimiento - D18: UCI (Unidad de Conocimiento e Inteligencia)
Gestiona la base de conocimiento central de QuantumHive

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona la base de conocimiento central, organiza información,
             permite búsquedas inteligentes y mantiene el conocimiento actualizado.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteBaseConocimiento:
    """Gestiona la base de conocimiento central de QuantumHive."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de base de conocimiento.
        
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
                CREATE TABLE IF NOT EXISTS conocimiento_entradas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entrada_id TEXT UNIQUE NOT NULL,
                    titulo TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    subcategoria TEXT,
                    etiquetas TEXT,
                    fuente TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    estado TEXT NOT NULL,
                    prioridad INTEGER DEFAULT 0
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias_conocimiento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT,
                    categoria_padre INTEGER,
                    icono TEXT,
                    color TEXT,
                    orden INTEGER DEFAULT 0,
                    activa BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (categoria_padre) REFERENCES categorias_conocimiento(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS relaciones_conocimiento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entrada_origen TEXT NOT NULL,
                    entrada_destino TEXT NOT NULL,
                    tipo_relacion TEXT NOT NULL,
                    peso REAL DEFAULT 1,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS busquedas_realizadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    termino_busqueda TEXT NOT NULL,
                    resultados_encontrados INTEGER DEFAULT 0,
                    fecha_busqueda DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usuario TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_conocimiento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entrada_id TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    tipo_feedback TEXT NOT NULL,
                    comentario TEXT,
                    utilidad INTEGER,
                    fecha_feedback DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_categoria(self, nombre: str, descripcion: str = None, categoria_padre: int = None,
                       icono: str = None, color: str = None, orden: int = 0) -> int:
        """
        Crea una categoría de conocimiento.
        
        Args:
            nombre: Nombre de la categoría
            descripcion: Descripción
            categoria_padre: ID de categoría padre
            icono: Icono
            color: Color
            orden: Orden de visualización
            
        Returns:
            ID de la categoría
        """
        try:
            self.cursor.execute("""
                INSERT INTO categorias_conocimiento
                (nombre, descripcion, categoria_padre, icono, color, orden, activa)
                VALUES (?, ?, ?, ?, ?, ?, TRUE)
            """, (nombre, descripcion, categoria_padre, icono, color, orden))
            
            self.conn.commit()
            categoria_id = self.cursor.lastrowid
            logger.info(f"Categoría creada - ID: {categoria_id} - Nombre: {nombre}")
            return categoria_id
        except Exception as e:
            logger.error(f"Error al crear categoría: {e}")
            raise
            
    def agregar_entrada(self, entrada_id: str, titulo: str, contenido: str, categoria: str,
                      subcategoria: str = None, etiquetas: List[str] = None, fuente: str = None,
                      prioridad: int = 0) -> int:
        """
        Agrega una entrada de conocimiento.
        
        Args:
            entrada_id: ID único de la entrada
            titulo: Título de la entrada
            contenido: Contenido
            categoria: Categoría
            subcategoria: Subcategoría
            etiquetas: Etiquetas
            fuente: Fuente
            prioridad: Prioridad
            
        Returns:
            ID de la entrada
        """
        try:
            etiquetas_json = json.dumps(etiquetas) if etiquetas else None
            
            self.cursor.execute("""
                INSERT INTO conocimiento_entradas
                (entrada_id, titulo, contenido, categoria, subcategoria, etiquetas, fuente, estado, prioridad)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
            """, (entrada_id, titulo, contenido, categoria, subcategoria, etiquetas_json, fuente, prioridad))
            
            self.conn.commit()
            entrada_db_id = self.cursor.lastrowid
            logger.info(f"Entrada agregada - ID: {entrada_db_id} - Título: {titulo}")
            return entrada_db_id
        except Exception as e:
            logger.error(f"Error al agregar entrada: {e}")
            raise
            
    def actualizar_entrada(self, entrada_id: str, titulo: str = None, contenido: str = None,
                         etiquetas: List[str] = None) -> bool:
        """
        Actualiza una entrada de conocimiento.
        
        Args:
            entrada_id: ID de la entrada
            titulo: Nuevo título
            contenido: Nuevo contenido
            etiquetas: Nuevas etiquetas
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            updates = []
            values = []
            
            if titulo:
                updates.append("titulo = ?")
                values.append(titulo)
            if contenido:
                updates.append("contenido = ?")
                values.append(contenido)
            if etiquetas:
                updates.append("etiquetas = ?")
                values.append(json.dumps(etiquetas))
                
            if not updates:
                return False
                
            updates.append("fecha_actualizacion = ?")
            updates.append("version = version + 1")
            values.append(datetime.now().isoformat())
            values.append(entrada_id)
            
            query = f"UPDATE conocimiento_entradas SET {', '.join(updates)} WHERE entrada_id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logger.info(f"Entrada {entrada_id} actualizada")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar entrada: {e}")
            return False
            
    def crear_relacion(self, entrada_origen: str, entrada_destino: str, tipo_relacion: str,
                      peso: float = 1) -> int:
        """
        Crea una relación entre entradas de conocimiento.
        
        Args:
            entrada_origen: ID de entrada origen
            entrada_destino: ID de entrada destino
            tipo_relacion: Tipo de relación (RELACIONADO, REFIERE, EXPANDE)
            peso: Peso de la relación
            
        Returns:
            ID de la relación
        """
        try:
            self.cursor.execute("""
                INSERT INTO relaciones_conocimiento
                (entrada_origen, entrada_destino, tipo_relacion, peso)
                VALUES (?, ?, ?, ?)
            """, (entrada_origen, entrada_destino, tipo_relacion, peso))
            
            self.conn.commit()
            relacion_id = self.cursor.lastrowid
            logger.info(f"Relación creada - ID: {relacion_id} - Tipo: {tipo_relacion}")
            return relacion_id
        except Exception as e:
            logger.error(f"Error al crear relación: {e}")
            raise
            
    def buscar_conocimiento(self, termino: str, categoria: str = None, limite: int = 20) -> List[Dict]:
        """
        Busca entradas de conocimiento.
        
        Args:
            termino: Término de búsqueda
            categoria: Categoría específica
            limite: Límite de resultados
            
        Returns:
            Lista de entradas encontradas
        """
        try:
            # Registrar búsqueda
            self.cursor.execute("""
                INSERT INTO busquedas_realizadas (termino_busqueda, resultados_encontrados)
                VALUES (?, 0)
            """, (termino,))
            self.conn.commit()
            busqueda_id = self.cursor.lastrowid
            
            query = """
                SELECT * FROM conocimiento_entradas
                WHERE estado = 'ACTIVO' AND (titulo LIKE ? OR contenido LIKE ?)
            """
            params = [f"%{termino}%", f"%{termino}%"]
            
            if categoria:
                query += " AND categoria = ?"
                params.append(categoria)
                
            query += " ORDER BY prioridad DESC, fecha_actualizacion DESC LIMIT ?"
            params.append(limite)
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            # Actualizar resultados de búsqueda
            self.cursor.execute("""
                UPDATE busquedas_realizadas SET resultados_encontrados = ? WHERE id = ?
            """, (len(results), busqueda_id))
            self.conn.commit()
            
            return [{
                'id': r[0], 'entrada_id': r[1], 'titulo': r[2], 'contenido': r[3],
                'categoria': r[4], 'subcategoria': r[5], 'etiquetas': json.loads(r[6]) if r[6] else None,
                'fuente': r[7], 'fecha_creacion': r[8], 'fecha_actualizacion': r[9],
                'version': r[10], 'estado': r[11], 'prioridad': r[12]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al buscar conocimiento: {e}")
            return []
            
    def obtener_entrada(self, entrada_id: str) -> Optional[Dict]:
        """Obtiene una entrada específica de conocimiento."""
        try:
            self.cursor.execute("""
                SELECT * FROM conocimiento_entradas WHERE entrada_id = ?
            """, (entrada_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return None
                
            # Obtener relaciones
            self.cursor.execute("""
                SELECT entrada_destino, tipo_relacion, peso
                FROM relaciones_conocimiento WHERE entrada_origen = ?
            """, (entrada_id,))
            relaciones = [{
                'entrada_destino': r[0], 'tipo_relacion': r[1], 'peso': r[2]
            } for r in self.cursor.fetchall()]
            
            return {
                'id': result[0], 'entrada_id': result[1], 'titulo': result[2],
                'contenido': result[3], 'categoria': result[4], 'subcategoria': result[5],
                'etiquetas': json.loads(result[6]) if result[6] else None,
                'fuente': result[7], 'fecha_creacion': result[8], 'fecha_actualizacion': result[9],
                'version': result[10], 'estado': result[11], 'prioridad': result[12],
                'relaciones': relaciones
            }
        except Exception as e:
            logger.error(f"Error al obtener entrada: {e}")
            return None
            
    def obtener_entradas_categoria(self, categoria: str, limite: int = 50) -> List[Dict]:
        """Obtiene entradas de una categoría."""
        try:
            self.cursor.execute("""
                SELECT * FROM conocimiento_entradas
                WHERE categoria = ? AND estado = 'ACTIVO'
                ORDER BY prioridad DESC, fecha_actualizacion DESC
                LIMIT ?
            """, (categoria, limite))
            
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'entrada_id': r[1], 'titulo': r[2], 'contenido': r[3],
                'categoria': r[4], 'subcategoria': r[5], 'etiquetas': json.loads(r[6]) if r[6] else None,
                'fuente': r[7], 'fecha_creacion': r[8], 'fecha_actualizacion': r[9],
                'version': r[10], 'estado': r[11], 'prioridad': r[12]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener entradas categoría: {e}")
            return []
            
    def agregar_feedback(self, entrada_id: str, usuario: str, tipo_feedback: str,
                        comentario: str = None, utilidad: int = None) -> int:
        """
        Agrega feedback sobre una entrada.
        
        Args:
            entrada_id: ID de la entrada
            usuario: Usuario
            tipo_feedback: Tipo de feedback (POSITIVO, NEGATIVO, SUGERENCIA)
            comentario: Comentario
            utilidad: Puntuación de utilidad (1-5)
            
        Returns:
            ID del feedback
        """
        try:
            self.cursor.execute("""
                INSERT INTO feedback_conocimiento
                (entrada_id, usuario, tipo_feedback, comentario, utilidad)
                VALUES (?, ?, ?, ?, ?)
            """, (entrada_id, usuario, tipo_feedback, comentario, utilidad))
            
            self.conn.commit()
            feedback_id = self.cursor.lastrowid
            logger.info(f"Feedback agregado - ID: {feedback_id} - Tipo: {tipo_feedback}")
            return feedback_id
        except Exception as e:
            logger.error(f"Error al agregar feedback: {e}")
            raise
            
    def obtener_categorias(self) -> List[Dict]:
        """Obtiene todas las categorías."""
        try:
            self.cursor.execute("""
                SELECT * FROM categorias_conocimiento WHERE activa = TRUE ORDER BY orden
            """)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'nombre': r[1], 'descripcion': r[2], 'categoria_padre': r[3],
                'icono': r[4], 'color': r[5], 'orden': r[6], 'activa': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener categorías: {e}")
            return []
            
    def obtener_estadisticas(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de la base de conocimiento."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_entradas,
                    SUM(CASE WHEN estado = 'ACTIVO' THEN 1 ELSE 0 END) as activas,
                    COUNT(DISTINCT categoria) as total_categorias,
                    AVG(utilidad) as avg_utilidad
                FROM conocimiento_entradas
                WHERE fecha_creacion >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, activas, categorias, avg_utilidad = result
                return {
                    'total_entradas': total or 0,
                    'entradas_activas': activas or 0,
                    'total_categorias': categorias or 0,
                    'avg_utilidad': round(avg_utilidad or 0, 2),
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
    
    agente = AgenteBaseConocimiento()
    
    # Ejemplo: crear categoría
    categoria_id = agente.crear_categoria(
        nombre="Estrategias Trading",
        descripcion="Todas las estrategias de trading",
        icono="chart",
        color="#3498db",
        orden=1
    )
    
    print(f"Categoría creada - ID: {categoria_id}")
    
    # Ejemplo: agregar entrada
    entrada_id = agente.agregar_entrada(
        entrada_id="EST-001",
        titulo="Scalping en Forex",
        contenido="El scalping es una técnica de trading que consiste en...",
        categoria="Estrategias Trading",
        subcategoria="Scalping",
        etiquetas=["scalping", "forex", "corto plazo"],
        fuente="Manual Interno",
        prioridad=1
    )
    
    print(f"Entrada agregada - ID: {entrada_id}")
    
    # Ejemplo: crear relación
    relacion_id = agente.crear_relacion(
        entrada_origen="EST-001",
        entrada_destino="EST-002",
        tipo_relacion="RELACIONADO",
        peso=0.8
    )
    
    print(f"Relación creada - ID: {relacion_id}")
    
    # Ejemplo: buscar conocimiento
    resultados = agente.buscar_conocimiento("scalping")
    print(f"Resultados búsqueda: {len(resultados)}")
    
    # Ejemplo: agregar feedback
    feedback_id = agente.agregar_feedback(
        entrada_id="EST-001",
        usuario="Usuario1",
        tipo_feedback="POSITIVO",
        comentario="Muy útil",
        utilidad=5
    )
    
    print(f"Feedback agregado - ID: {feedback_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

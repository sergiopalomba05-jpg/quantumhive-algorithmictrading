"""
Agente Catálogo - D8: Biblioteca Fábrica de Bots
Gestiona el catálogo de bots disponibles

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Organiza y gestiona el catálogo de bots, categorías,
             etiquetas, versiones y disponibilidad de bots en la biblioteca.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteCatalogo:
    """Gestiona el catálogo de bots disponibles."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de catálogo.
        
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
                CREATE TABLE IF NOT EXISTS catalogo_bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    categoria_principal TEXT NOT NULL,
                    tipo_estrategia TEXT NOT NULL,
                    instrumentos TEXT,
                    timeframe TEXT,
                    riesgo TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    version_actual TEXT NOT NULL
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT,
                    icono TEXT,
                    color TEXT,
                    orden INTEGER DEFAULT 0,
                    activa BOOLEAN DEFAULT TRUE
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS etiquetas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    categoria TEXT,
                    descripcion TEXT,
                    activa BOOLEAN DEFAULT TRUE
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_etiquetas (
                    bot_id TEXT NOT NULL,
                    etiqueta_id INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (etiqueta_id) REFERENCES etiquetas(id),
                    PRIMARY KEY (bot_id, etiqueta_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS versiones_bot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    notas_lanzamiento TEXT,
                    fecha_lanzamiento DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cambios TEXT,
                    estable BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (bot_id) REFERENCES catalogo_bots(bot_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS estadisticas_bot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    vistas INTEGER DEFAULT 0,
                    descargas INTEGER DEFAULT 0,
                    valoraciones INTEGER DEFAULT 0,
                    rating_promedio REAL DEFAULT 0,
                    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_id) REFERENCES catalogo_bots(bot_id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_categoria(self, nombre: str, descripcion: str = None, icono: str = None,
                       color: str = None, orden: int = 0) -> int:
        """
        Crea una categoría en el catálogo.
        
        Args:
            nombre: Nombre de la categoría
            descripcion: Descripción
            icono: Icono
            color: Color
            orden: Orden de visualización
            
        Returns:
            ID de la categoría
        """
        try:
            self.cursor.execute("""
                INSERT INTO categorias (nombre, descripcion, icono, color, orden, activa)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (nombre, descripcion, icono, color, orden))
            
            self.conn.commit()
            categoria_id = self.cursor.lastrowid
            logger.info(f"Categoría creada - ID: {categoria_id} - Nombre: {nombre}")
            return categoria_id
        except Exception as e:
            logger.error(f"Error al crear categoría: {e}")
            raise
            
    def crear_etiqueta(self, nombre: str, categoria: str = None, descripcion: str = None) -> int:
        """
        Crea una etiqueta.
        
        Args:
            nombre: Nombre de la etiqueta
            categoria: Categoría
            descripcion: Descripción
            
        Returns:
            ID de la etiqueta
        """
        try:
            self.cursor.execute("""
                INSERT INTO etiquetas (nombre, categoria, descripcion, activa)
                VALUES (?, ?, ?, TRUE)
            """, (nombre, categoria, descripcion))
            
            self.conn.commit()
            etiqueta_id = self.cursor.lastrowid
            logger.info(f"Etiqueta creada - ID: {etiqueta_id} - Nombre: {nombre}")
            return etiqueta_id
        except Exception as e:
            logger.error(f"Error al crear etiqueta: {e}")
            raise
            
    def agregar_bot_catalogo(self, bot_id: str, nombre: str, descripcion: str,
                            categoria_principal: str, tipo_estrategia: str,
                            instrumentos: List[str] = None, timeframe: str = None,
                            riesgo: str = "MEDIO", version: str = "1.0.0") -> int:
        """
        Agrega un bot al catálogo.
        
        Args:
            bot_id: ID del bot
            nombre: Nombre del bot
            descripcion: Descripción
            categoria_principal: Categoría principal
            tipo_estrategia: Tipo de estrategia
            instrumentos: Lista de instrumentos
            timeframe: Timeframe
            riesgo: Nivel de riesgo
            version: Versión actual
            
        Returns:
            ID del bot en catálogo
        """
        try:
            instrumentos_json = json.dumps(instrumentos) if instrumentos else None
            
            self.cursor.execute("""
                INSERT INTO catalogo_bots
                (bot_id, nombre, descripcion, categoria_principal, tipo_estrategia,
                 instrumentos, timeframe, riesgo, estado, version_actual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
            """, (bot_id, nombre, descripcion, categoria_principal, tipo_estrategia,
                  instrumentos_json, timeframe, riesgo, version))
            
            self.conn.commit()
            catalogo_id = self.cursor.lastrowid
            
            # Inicializar estadísticas
            self.cursor.execute("""
                INSERT INTO estadisticas_bot (bot_id) VALUES (?)
            """, (bot_id,))
            self.conn.commit()
            
            logger.info(f"Bot agregado al catálogo - ID: {catalogo_id} - Bot: {nombre}")
            return catalogo_id
        except Exception as e:
            logger.error(f"Error al agregar bot: {e}")
            raise
            
    def asignar_etiqueta(self, bot_id: str, etiqueta_id: int) -> bool:
        """
        Asigna una etiqueta a un bot.
        
        Args:
            bot_id: ID del bot
            etiqueta_id: ID de la etiqueta
            
        Returns:
            True si se asignó correctamente
        """
        try:
            self.cursor.execute("""
                INSERT INTO bot_etiquetas (bot_id, etiqueta_id) VALUES (?, ?)
            """, (bot_id, etiqueta_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al asignar etiqueta: {e}")
            return False
            
    def registrar_version(self, bot_id: str, version: str, notas_lanzamiento: str = None,
                        cambios: dict = None, estable: bool = True) -> int:
        """
        Registra una nueva versión de un bot.
        
        Args:
            bot_id: ID del bot
            version: Versión
            notas_lanzamiento: Notas de lanzamiento
            cambios: Cambios realizados
            estable: Si es estable
            
        Returns:
            ID de la versión
        """
        try:
            cambios_json = json.dumps(cambios) if cambios else None
            
            self.cursor.execute("""
                INSERT INTO versiones_bot
                (bot_id, version, notas_lanzamiento, cambios, estable)
                VALUES (?, ?, ?, ?, ?)
            """, (bot_id, version, notas_lanzamiento, cambios_json, estable))
            
            self.conn.commit()
            version_id = self.cursor.lastrowid
            
            # Actualizar versión actual
            self.cursor.execute("""
                UPDATE catalogo_bots SET version_actual = ?, ultima_actualizacion = ?
                WHERE bot_id = ?
            """, (version, datetime.now().isoformat(), bot_id))
            self.conn.commit()
            
            logger.info(f"Versión registrada - ID: {version_id} - Bot: {bot_id} - Versión: {version}")
            return version_id
        except Exception as e:
            logger.error(f"Error al registrar versión: {e}")
            raise
            
    def actualizar_estadisticas(self, bot_id: str, vistas: int = 0, descargas: int = 0,
                              valoracion: int = None) -> bool:
        """
        Actualiza las estadísticas de un bot.
        
        Args:
            bot_id: ID del bot
            vistas: Incremento de vistas
            descargas: Incremento de descargas
            valoracion: Nueva valoración
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE estadisticas_bot
                SET vistas = vistas + ?,
                    descargas = descargas + ?,
                    ultima_actualizacion = ?
                WHERE bot_id = ?
            """, (vistas, descargas, datetime.now().isoformat(), bot_id))
            
            if valoracion:
                # Recalcular rating promedio
                self.cursor.execute("""
                    UPDATE estadisticas_bot
                    SET valoraciones = valoraciones + 1,
                        rating_promedio = ((rating_promedio * valoraciones) + ?) / (valoraciones + 1),
                        ultima_actualizacion = ?
                    WHERE bot_id = ?
                """, (valoracion, datetime.now().isoformat(), bot_id))
                
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar estadísticas: {e}")
            return False
            
    def obtener_bots_catalogo(self, categoria: str = None, estado: str = "ACTIVO") -> List[Dict]:
        """Obtiene bots del catálogo."""
        try:
            query = """
                SELECT c.*, e.vistas, e.descargas, e.rating_promedio
                FROM catalogo_bots c
                LEFT JOIN estadisticas_bot e ON c.bot_id = e.bot_id
            """
            params = []
            
            conditions = []
            if categoria:
                conditions.append("c.categoria_principal = ?")
                params.append(categoria)
            if estado:
                conditions.append("c.estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY c.ultima_actualizacion DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'bot_id': r[1], 'nombre': r[2], 'descripcion': r[3],
                'categoria_principal': r[4], 'tipo_estrategia': r[5],
                'instrumentos': json.loads(r[6]) if r[6] else None, 'timeframe': r[7],
                'riesgo': r[8], 'fecha_creacion': r[9], 'ultima_actualizacion': r[10],
                'estado': r[11], 'version_actual': r[12],
                'vistas': r[13], 'descargas': r[14], 'rating_promedio': r[15]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener bots: {e}")
            return []
            
    def obtener_bot_detalle(self, bot_id: str) -> Optional[Dict]:
        """Obtiene el detalle de un bot."""
        try:
            self.cursor.execute("""
                SELECT c.*, e.vistas, e.descargas, e.rating_promedio
                FROM catalogo_bots c
                LEFT JOIN estadisticas_bot e ON c.bot_id = e.bot_id
                WHERE c.bot_id = ?
            """, (bot_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return None
                
            # Obtener etiquetas
            self.cursor.execute("""
                SELECT e.nombre FROM etiquetas e
                JOIN bot_etiquetas be ON e.id = be.etiqueta_id
                WHERE be.bot_id = ?
            """, (bot_id,))
            etiquetas = [r[0] for r in self.cursor.fetchall()]
            
            # Obtener versiones
            self.cursor.execute("""
                SELECT * FROM versiones_bot WHERE bot_id = ? ORDER BY fecha_lanzamiento DESC
            """, (bot_id,))
            versiones = [{
                'id': r[0], 'bot_id': r[1], 'version': r[2], 'notas_lanzamiento': r[3],
                'fecha_lanzamiento': r[4], 'cambios': json.loads(r[5]) if r[5] else None,
                'estable': r[6]
            } for r in self.cursor.fetchall()]
            
            return {
                'id': result[0], 'bot_id': result[1], 'nombre': result[2],
                'descripcion': result[3], 'categoria_principal': result[4],
                'tipo_estrategia': result[5],
                'instrumentos': json.loads(result[6]) if result[6] else None,
                'timeframe': result[7], 'riesgo': result[8], 'fecha_creacion': result[9],
                'ultima_actualizacion': result[10], 'estado': result[11],
                'version_actual': result[12], 'vistas': result[13],
                'descargas': result[14], 'rating_promedio': result[15],
                'etiquetas': etiquetas, 'versiones': versiones
            }
        except Exception as e:
            logger.error(f"Error al obtener detalle: {e}")
            return None
            
    def obtener_categorias(self) -> List[Dict]:
        """Obtiene todas las categorías."""
        try:
            self.cursor.execute("""
                SELECT * FROM categorias WHERE activa = TRUE ORDER BY orden
            """)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'nombre': r[1], 'descripcion': r[2],
                'icono': r[3], 'color': r[4], 'orden': r[5], 'activa': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener categorías: {e}")
            return []
            
    def buscar_bots(self, termino: str) -> List[Dict]:
        """Busca bots por término."""
        try:
            self.cursor.execute("""
                SELECT c.*, e.vistas, e.descargas, e.rating_promedio
                FROM catalogo_bots c
                LEFT JOIN estadisticas_bot e ON c.bot_id = e.bot_id
                WHERE c.nombre LIKE ? OR c.descripcion LIKE ? OR c.tipo_estrategia LIKE ?
                ORDER BY e.rating_promedio DESC
            """, (f"%{termino}%", f"%{termino}%", f"%{termino}%"))
            
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'bot_id': r[1], 'nombre': r[2], 'descripcion': r[3],
                'categoria_principal': r[4], 'tipo_estrategia': r[5],
                'instrumentos': json.loads(r[6]) if r[6] else None, 'timeframe': r[7],
                'riesgo': r[8], 'fecha_creacion': r[9], 'ultima_actualizacion': r[10],
                'estado': r[11], 'version_actual': r[12],
                'vistas': r[13], 'descargas': r[14], 'rating_promedio': r[15]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al buscar bots: {e}")
            return []
            
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
    
    agente = AgenteCatalogo()
    
    # Ejemplo: crear categoría
    categoria_id = agente.crear_categoria(
        nombre="Scalping",
        descripcion="Bots de scalping de alta frecuencia",
        icono="scissors",
        color="#FF5733",
        orden=1
    )
    
    print(f"Categoría creada - ID: {categoria_id}")
    
    # Ejemplo: crear etiqueta
    etiqueta_id = agente.crear_etiqueta(
        nombre="EURUSD",
        categoria="Scalping",
        descripcion="Especializado en EURUSD"
    )
    
    print(f"Etiqueta creada - ID: {etiqueta_id}")
    
    # Ejemplo: agregar bot al catálogo
    catalogo_id = agente.agregar_bot_catalogo(
        bot_id="BOT-001",
        nombre="Bot Scalping Pro",
        descripcion="Bot de scalping para EURUSD con alta precisión",
        categoria_principal="Scalping",
        tipo_estrategia="Scalping",
        instrumentos=["EURUSD"],
        timeframe="M1",
        riesgo="MEDIO",
        version="1.0.0"
    )
    
    print(f"Bot agregado - ID: {catalogo_id}")
    
    # Ejemplo: asignar etiqueta
    agente.asignar_etiqueta("BOT-001", etiqueta_id)
    
    # Ejemplo: registrar versión
    version_id = agente.registrar_version(
        bot_id="BOT-001",
        version="1.1.0",
        notas_lanzamiento="Mejora en gestión de riesgo",
        cambios={"riesgo": "Optimizado", "rendimiento": "+5%"},
        estable=True
    )
    
    print(f"Versión registrada - ID: {version_id}")
    
    # Ejemplo: obtener bots
    bots = agente.obtener_bots_catalogo()
    print(f"Bots en catálogo: {len(bots)}")
    
    # Ejemplo: obtener detalle
    detalle = agente.obtener_bot_detalle("BOT-001")
    print(f"Detalle bot: {detalle['nombre']} - Versión: {detalle['version_actual']}")
    
    agente.cerrar()

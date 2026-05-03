"""
Agente Recolector Videos - D18: UCI (Unidad de Conocimiento e Inteligencia)
Recolecta y procesa videos educativos de trading

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Recolecta videos educativos de trading de diversas fuentes,
             extrae información relevante y los almacena en la base de conocimiento.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteRecolectorVideos:
    """Recolecta y procesa videos educativos de trading."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente recolector de videos.
        
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
                CREATE TABLE IF NOT EXISTS fuentes_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    plataforma TEXT NOT NULL,
                    url_base TEXT,
                    tipo_fuente TEXT NOT NULL,
                    configuracion TEXT,
                    activa BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos_recolectados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    fuente_id INTEGER NOT NULL,
                    titulo TEXT NOT NULL,
                    descripcion TEXT,
                    autor TEXT,
                    url TEXT NOT NULL,
                    duracion INTEGER,
                    fecha_publicacion DATETIME,
                    fecha_recoleccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    categoria TEXT,
                    etiquetas TEXT,
                    estado_procesamiento TEXT NOT NULL,
                    FOREIGN KEY (fuente_id) REFERENCES fuentes_videos(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    texto_transcripcion TEXT,
                    idioma TEXT DEFAULT 'es',
                    metodo_extraccion TEXT NOT NULL,
                    fecha_procesamiento DATETIME DEFAULT CURRENT_TIMESTAMP,
                    calidad TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos_recolectados(video_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS segmentos_video (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcripcion_id INTEGER NOT NULL,
                    tiempo_inicio REAL NOT NULL,
                    tiempo_fin REAL NOT NULL,
                    texto TEXT NOT NULL,
                    tema TEXT,
                    importancia INTEGER DEFAULT 0,
                    FOREIGN KEY (transcripcion_id) REFERENCES transcripciones(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS conocimiento_extraido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    tipo_conocimiento TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    confianza REAL DEFAULT 0,
                    categoria TEXT,
                    fecha_extraccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    validado BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (video_id) REFERENCES videos_recolectados(video_id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_fuente(self, nombre: str, plataforma: str, url_base: str = None,
                        tipo_fuente: str = "API", configuracion: dict = None) -> int:
        """
        Registra una fuente de videos.
        
        Args:
            nombre: Nombre de la fuente
            plataforma: Plataforma (YouTube, Vimeo, etc.)
            url_base: URL base
            tipo_fuente: Tipo de fuente (API, RSS, MANUAL)
            configuracion: Configuración de la fuente
            
        Returns:
            ID de la fuente
        """
        try:
            configuracion_json = json.dumps(configuracion) if configuracion else None
            
            self.cursor.execute("""
                INSERT INTO fuentes_videos
                (nombre, plataforma, url_base, tipo_fuente, configuracion, activa)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (nombre, plataforma, url_base, tipo_fuente, configuracion_json))
            
            self.conn.commit()
            fuente_id = self.cursor.lastrowid
            logger.info(f"Fuente registrada - ID: {fuente_id} - Nombre: {nombre}")
            return fuente_id
        except Exception as e:
            logger.error(f"Error al registrar fuente: {e}")
            raise
            
    def recolectar_video(self, video_id: str, fuente_id: int, titulo: str, url: str,
                        descripcion: str = None, autor: str = None, duracion: int = None,
                        fecha_publicacion: datetime = None, categoria: str = None,
                        etiquetas: List[str] = None) -> int:
        """
        Recolecta un video y lo almacena.
        
        Args:
            video_id: ID del video
            fuente_id: ID de la fuente
            titulo: Título del video
            url: URL del video
            descripcion: Descripción
            autor: Autor
            duracion: Duración en segundos
            fecha_publicacion: Fecha de publicación
            categoria: Categoría
            etiquetas: Etiquetas
            
        Returns:
            ID del video recolectado
        """
        try:
            etiquetas_json = json.dumps(etiquetas) if etiquetas else None
            
            self.cursor.execute("""
                INSERT INTO videos_recolectados
                (video_id, fuente_id, titulo, descripcion, autor, url, duracion,
                 fecha_publicacion, categoria, etiquetas, estado_procesamiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
            """, (video_id, fuente_id, titulo, descripcion, autor, url, duracion,
                  fecha_publicacion.isoformat() if fecha_publicacion else None,
                  categoria, etiquetas_json))
            
            self.conn.commit()
            video_db_id = self.cursor.lastrowid
            logger.info(f"Video recolectado - ID: {video_db_id} - Título: {titulo}")
            return video_db_id
        except Exception as e:
            logger.error(f"Error al recolectar video: {e}")
            raise
            
    def registrar_transcripcion(self, video_id: str, texto_transcripcion: str,
                              metodo_extraccion: str, idioma: str = "es",
                              calidad: str = "MEDIA") -> int:
        """
        Registra la transcripción de un video.
        
        Args:
            video_id: ID del video
            texto_transcripcion: Texto de la transcripción
            metodo_extraccion: Método de extracción
            idioma: Idioma
            calidad: Calidad de la transcripción
            
        Returns:
            ID de la transcripción
        """
        try:
            self.cursor.execute("""
                INSERT INTO transcripciones
                (video_id, texto_transcripcion, idioma, metodo_extraccion, calidad)
                VALUES (?, ?, ?, ?, ?)
            """, (video_id, texto_transcripcion, idioma, metodo_extraccion, calidad))
            
            self.conn.commit()
            transcripcion_id = self.cursor.lastrowid
            
            # Actualizar estado del video
            self.cursor.execute("""
                UPDATE videos_recolectados SET estado_procesamiento = 'TRANSCRITO' WHERE video_id = ?
            """, (video_id,))
            self.conn.commit()
            
            logger.info(f"Transcripción registrada - ID: {transcripcion_id} - Video: {video_id}")
            return transcripcion_id
        except Exception as e:
            logger.error(f"Error al registrar transcripción: {e}")
            raise
            
    def segmentar_transcripcion(self, transcripcion_id: int, segmentos: List[Dict]) -> int:
        """
        Segmenta la transcripción en partes más pequeñas.
        
        Args:
            transcripcion_id: ID de la transcripción
            segmentos: Lista de segmentos con tiempo_inicio, tiempo_fin, texto, tema
            
        Returns:
            Cantidad de segmentos creados
        """
        try:
            count = 0
            for segmento in segmentos:
                self.cursor.execute("""
                    INSERT INTO segmentos_video
                    (transcripcion_id, tiempo_inicio, tiempo_fin, texto, tema, importancia)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (transcripcion_id, segmento['tiempo_inicio'], segmento['tiempo_fin'],
                      segmento['texto'], segmento.get('tema'), segmento.get('importancia', 0)))
                count += 1
                
            self.conn.commit()
            logger.info(f"{count} segmentos creados - Transcripción ID: {transcripcion_id}")
            return count
        except Exception as e:
            logger.error(f"Error al segmentar: {e}")
            raise
            
    def extraer_conocimiento(self, video_id: str, tipo_conocimiento: str, contenido: str,
                           categoria: str = None, confianza: float = 0.8) -> int:
        """
        Extrae conocimiento de un video.
        
        Args:
            video_id: ID del video
            tipo_conocimiento: Tipo de conocimiento (ESTRATEGIA, TECNICA, PSICOLOGIA)
            contenido: Contenido del conocimiento
            categoria: Categoría
            confianza: Nivel de confianza
            
        Returns:
            ID del conocimiento extraído
        """
        try:
            self.cursor.execute("""
                INSERT INTO conocimiento_extraido
                (video_id, tipo_conocimiento, contenido, confianza, categoria, validado)
                VALUES (?, ?, ?, ?, ?, FALSE)
            """, (video_id, tipo_conocimiento, contenido, confianza, categoria))
            
            self.conn.commit()
            conocimiento_id = self.cursor.lastrowid
            
            # Actualizar estado del video
            self.cursor.execute("""
                UPDATE videos_recolectados SET estado_procesamiento = 'PROCESADO' WHERE video_id = ?
            """, (video_id,))
            self.conn.commit()
            
            logger.info(f"Conocimiento extraído - ID: {conocimiento_id} - Tipo: {tipo_conocimiento}")
            return conocimiento_id
        except Exception as e:
            logger.error(f"Error al extraer conocimiento: {e}")
            raise
            
    def validar_conocimiento(self, conocimiento_id: int, validado: bool = True) -> bool:
        """
        Valida un conocimiento extraído.
        
        Args:
            conocimiento_id: ID del conocimiento
            validado: Si está validado
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE conocimiento_extraido SET validado = ? WHERE id = ?
            """, (validado, conocimiento_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al validar conocimiento: {e}")
            return False
            
    def obtener_videos(self, fuente_id: int = None, categoria: str = None,
                     estado: str = None) -> List[Dict]:
        """Obtiene videos recolectados."""
        try:
            query = "SELECT * FROM videos_recolectados"
            params = []
            
            conditions = []
            if fuente_id:
                conditions.append("fuente_id = ?")
                params.append(fuente_id)
            if categoria:
                conditions.append("categoria = ?")
                params.append(categoria)
            if estado:
                conditions.append("estado_procesamiento = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY fecha_recoleccion DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'video_id': r[1], 'fuente_id': r[2], 'titulo': r[3],
                'descripcion': r[4], 'autor': r[5], 'url': r[6], 'duracion': r[7],
                'fecha_publicacion': r[8], 'fecha_recoleccion': r[9], 'categoria': r[10],
                'etiquetas': json.loads(r[11]) if r[11] else None, 'estado_procesamiento': r[12]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener videos: {e}")
            return []
            
    def obtener_transcripcion_video(self, video_id: str) -> Optional[Dict]:
        """Obtiene la transcripción de un video."""
        try:
            self.cursor.execute("""
                SELECT * FROM transcripciones WHERE video_id = ?
            """, (video_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0], 'video_id': result[1], 'texto_transcripcion': result[2],
                'idioma': result[3], 'metodo_extraccion': result[4],
                'fecha_procesamiento': result[5], 'calidad': result[6]
            }
        except Exception as e:
            logger.error(f"Error al obtener transcripción: {e}")
            return None
            
    def obtener_conocimiento_video(self, video_id: str) -> List[Dict]:
        """Obtiene el conocimiento extraído de un video."""
        try:
            self.cursor.execute("""
                SELECT * FROM conocimiento_extraido WHERE video_id = ?
            """, (video_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'video_id': r[1], 'tipo_conocimiento': r[2],
                'contenido': r[3], 'confianza': r[4], 'categoria': r[5],
                'fecha_extraccion': r[6], 'validado': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener conocimiento: {e}")
            return []
            
    def buscar_conocimiento(self, termino: str, tipo: str = None) -> List[Dict]:
        """Busca conocimiento por término."""
        try:
            query = """
                SELECT k.*, v.titulo
                FROM conocimiento_extraido k
                JOIN videos_recolectados v ON k.video_id = v.video_id
                WHERE k.contenido LIKE ?
            """
            params = [f"%{termino}%"]
            
            if tipo:
                query += " AND k.tipo_conocimiento = ?"
                params.append(tipo)
                
            query += " ORDER BY k.confianza DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'video_id': r[1], 'tipo_conocimiento': r[2],
                'contenido': r[3], 'confianza': r[4], 'categoria': r[5],
                'fecha_extraccion': r[6], 'validado': r[7], 'titulo_video': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al buscar conocimiento: {e}")
            return []
            
    def obtener_estadisticas(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de recolección."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    SUM(CASE WHEN estado_procesamiento = 'PROCESADO' THEN 1 ELSE 0 END) as procesados,
                    SUM(CASE WHEN estado_procesamiento = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes
                FROM videos_recolectados
                WHERE fecha_recoleccion >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, procesados, pendientes = result
                return {
                    'total_videos': total or 0,
                    'procesados': procesados or 0,
                    'pendientes': pendientes or 0,
                    'tasa_procesamiento': round((procesados / total * 100) if total > 0 else 0, 2),
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
    
    agente = AgenteRecolectorVideos()
    
    # Ejemplo: registrar fuente
    fuente_id = agente.registrar_fuente(
        nombre="YouTube Trading Academy",
        plataforma="YouTube",
        url_base="https://youtube.com",
        tipo_fuente="API",
        configuracion={"api_key": "xxx", "channel_id": "UCxxx"}
    )
    
    print(f"Fuente registrada - ID: {fuente_id}")
    
    # Ejemplo: recolectar video
    video_id = agente.recolectar_video(
        video_id="YT-001",
        fuente_id=fuente_id,
        titulo="Scalping Strategies for Beginners",
        url="https://youtube.com/watch?v=xxx",
        descripcion="Complete guide to scalping",
        autor="Trading Master",
        duracion=1800,
        categoria="SCALPING",
        etiquetas=["scalping", "beginners", "forex"]
    )
    
    print(f"Video recolectado - ID: {video_id}")
    
    # Ejemplo: registrar transcripción
    transcripcion_id = agente.registrar_transcripcion(
        video_id="YT-001",
        texto_transcripcion="Welcome to this scalping tutorial...",
        metodo_extraccion="API",
        calidad="ALTA"
    )
    
    print(f"Transcripción registrada - ID: {transcripcion_id}")
    
    # Ejemplo: extraer conocimiento
    conocimiento_id = agente.extraer_conocimiento(
        video_id="YT-001",
        tipo_conocimiento="ESTRATEGIA",
        contenido="Scalping requires quick entry and exit...",
        categoria="SCALPING",
        confianza=0.9
    )
    
    print(f"Conocimiento extraído - ID: {conocimiento_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

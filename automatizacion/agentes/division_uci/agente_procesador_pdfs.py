"""
Agente Procesador PDFs - D18: UCI (Unidad de Conocimiento e Inteligencia)
Procesa y extrae información de documentos PDF

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Procesa documentos PDF de trading, extrae texto,
             estructuras el contenido y lo almacena en la base de conocimiento.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteProcesadorPdfs:
    """Procesa y extrae información de documentos PDF."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente procesador de PDFs.
        
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
                CREATE TABLE IF NOT EXISTS documentos_pdf (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archivo_id TEXT UNIQUE NOT NULL,
                    nombre_archivo TEXT NOT NULL,
                    ruta_archivo TEXT,
                    tamano_bytes INTEGER,
                    paginas INTEGER,
                    autor TEXT,
                    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
                    categoria TEXT,
                    etiquetas TEXT,
                    estado_procesamiento TEXT NOT NULL,
                    origen TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS paginas_documento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id INTEGER NOT NULL,
                    numero_pagina INTEGER NOT NULL,
                    texto_extraido TEXT,
                    texto_limpio TEXT,
                    fecha_procesamiento DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metodo_extraccion TEXT NOT NULL,
                    FOREIGN KEY (documento_id) REFERENCES documentos_pdf(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS secciones_documento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pagina_id INTEGER NOT NULL,
                    tipo_seccion TEXT NOT NULL,
                    titulo TEXT,
                    contenido TEXT,
                    posicion_inicio INTEGER,
                    posicion_fin INTEGER,
                    importancia INTEGER DEFAULT 0,
                    FOREIGN KEY (pagina_id) REFERENCES paginas_documento(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadatos_documento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id INTEGER NOT NULL,
                    clave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    FOREIGN KEY (documento_id) REFERENCES documentos_pdf(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS conocimiento_pdf (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id INTEGER NOT NULL,
                    tipo_conocimiento TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    contexto TEXT,
                    pagina_referencia INTEGER,
                    confianza REAL DEFAULT 0,
                    categoria TEXT,
                    fecha_extraccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    validado BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (documento_id) REFERENCES documentos_pdf(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_documento(self, archivo_id: str, nombre_archivo: str, ruta_archivo: str = None,
                          tamano_bytes: int = None, paginas: int = None, autor: str = None,
                          categoria: str = None, etiquetas: List[str] = None, origen: str = "MANUAL") -> int:
        """
        Registra un documento PDF.
        
        Args:
            archivo_id: ID único del archivo
            nombre_archivo: Nombre del archivo
            ruta_archivo: Ruta del archivo
            tamano_bytes: Tamaño en bytes
            paginas: Cantidad de páginas
            autor: Autor del documento
            categoria: Categoría
            etiquetas: Etiquetas
            origen: Origen del documento
            
        Returns:
            ID del documento
        """
        try:
            etiquetas_json = json.dumps(etiquetas) if etiquetas else None
            
            self.cursor.execute("""
                INSERT INTO documentos_pdf
                (archivo_id, nombre_archivo, ruta_archivo, tamano_bytes, paginas, autor,
                 categoria, etiquetas, estado_procesamiento, origen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)
            """, (archivo_id, nombre_archivo, ruta_archivo, tamano_bytes, paginas, autor,
                  categoria, etiquetas_json, origen))
            
            self.conn.commit()
            documento_id = self.cursor.lastrowid
            logger.info(f"Documento registrado - ID: {documento_id} - Archivo: {nombre_archivo}")
            return documento_id
        except Exception as e:
            logger.error(f"Error al registrar documento: {e}")
            raise
            
    def procesar_pagina(self, documento_id: int, numero_pagina: int, texto_extraido: str,
                       metodo_extraccion: str = "OCR") -> int:
        """
        Procesa una página del documento.
        
        Args:
            documento_id: ID del documento
            numero_pagina: Número de página
            texto_extraido: Texto extraído
            metodo_extraccion: Método de extracción
            
        Returns:
            ID de la página procesada
        """
        try:
            # Limpieza básica del texto
            texto_limpio = self._limpiar_texto(texto_extraido)
            
            self.cursor.execute("""
                INSERT INTO paginas_documento
                (documento_id, numero_pagina, texto_extraido, texto_limpio, metodo_extraccion)
                VALUES (?, ?, ?, ?, ?)
            """, (documento_id, numero_pagina, texto_extraido, texto_limpio, metodo_extraccion))
            
            self.conn.commit()
            pagina_id = self.cursor.lastrowid
            logger.debug(f"Página procesada - ID: {pagina_id} - Página: {numero_pagina}")
            return pagina_id
        except Exception as e:
            logger.error(f"Error al procesar página: {e}")
            raise
            
    def _limpiar_texto(self, texto: str) -> str:
        """Limpia el texto extraído."""
        if not texto:
            return ""
        # Eliminar espacios múltiples
        texto = " ".join(texto.split())
        # Eliminar caracteres especiales no deseados
        return texto.strip()
        
    def extraer_seccion(self, pagina_id: int, tipo_seccion: str, titulo: str = None,
                       contenido: str = None, posicion_inicio: int = None,
                       posicion_fin: int = None, importancia: int = 0) -> int:
        """
        Extrae una sección de una página.
        
        Args:
            pagina_id: ID de la página
            tipo_seccion: Tipo de sección (TITULO, SUBTITULO, PARRAFO, TABLA, IMAGEN)
            titulo: Título
            contenido: Contenido
            posicion_inicio: Posición de inicio
            posicion_fin: Posición de fin
            importancia: Nivel de importancia
            
        Returns:
            ID de la sección
        """
        try:
            self.cursor.execute("""
                INSERT INTO secciones_documento
                (pagina_id, tipo_seccion, titulo, contenido, posicion_inicio, posicion_fin, importancia)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pagina_id, tipo_seccion, titulo, contenido, posicion_inicio, posicion_fin, importancia))
            
            self.conn.commit()
            seccion_id = self.cursor.lastrowid
            return seccion_id
        except Exception as e:
            logger.error(f"Error al extraer sección: {e}")
            raise
            
    def agregar_metadato(self, documento_id: int, clave: str, valor: str) -> bool:
        """
        Agrega metadatos al documento.
        
        Args:
            documento_id: ID del documento
            clave: Clave del metadato
            valor: Valor del metadato
            
        Returns:
            True si se agregó correctamente
        """
        try:
            self.cursor.execute("""
                INSERT INTO metadatos_documento (documento_id, clave, valor)
                VALUES (?, ?, ?)
            """, (documento_id, clave, valor))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al agregar metadato: {e}")
            return False
            
    def extraer_conocimiento(self, documento_id: int, tipo_conocimiento: str, contenido: str,
                           contexto: str = None, pagina_referencia: int = None,
                           categoria: str = None, confianza: float = 0.8) -> int:
        """
        Extrae conocimiento del documento.
        
        Args:
            documento_id: ID del documento
            tipo_conocimiento: Tipo de conocimiento (CONCEPTO, ESTRATEGIA, REGLA, EJEMPLO)
            contenido: Contenido del conocimiento
            contexto: Contexto
            pagina_referencia: Página de referencia
            categoria: Categoría
            confianza: Nivel de confianza
            
        Returns:
            ID del conocimiento extraído
        """
        try:
            self.cursor.execute("""
                INSERT INTO conocimiento_pdf
                (documento_id, tipo_conocimiento, contenido, contexto, pagina_referencia,
                 confianza, categoria, validado)
                VALUES (?, ?, ?, ?, ?, ?, ?, FALSE)
            """, (documento_id, tipo_conocimiento, contenido, contexto, pagina_referencia,
                  confianza, categoria))
            
            self.conn.commit()
            conocimiento_id = self.cursor.lastrowid
            
            # Actualizar estado del documento
            self.cursor.execute("""
                UPDATE documentos_pdf SET estado_procesamiento = 'PROCESADO' WHERE id = ?
            """, (documento_id,))
            self.conn.commit()
            
            logger.info(f"Conocimiento extraído - ID: {conocimiento_id} - Tipo: {tipo_conocimiento}")
            return conocimiento_id
        except Exception as e:
            logger.error(f"Error al extraer conocimiento: {e}")
            raise
            
    def finalizar_procesamiento(self, documento_id: int) -> bool:
        """
        Finaliza el procesamiento de un documento.
        
        Args:
            documento_id: ID del documento
            
        Returns:
            True si se finalizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE documentos_pdf SET estado_procesamiento = 'COMPLETADO' WHERE id = ?
            """, (documento_id,))
            self.conn.commit()
            logger.info(f"Procesamiento finalizado - Documento ID: {documento_id}")
            return True
        except Exception as e:
            logger.error(f"Error al finalizar procesamiento: {e}")
            return False
            
    def obtener_documentos(self, categoria: str = None, estado: str = None) -> List[Dict]:
        """Obtiene documentos PDF."""
        try:
            query = "SELECT * FROM documentos_pdf"
            params = []
            
            conditions = []
            if categoria:
                conditions.append("categoria = ?")
                params.append(categoria)
            if estado:
                conditions.append("estado_procesamiento = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY fecha_carga DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'archivo_id': r[1], 'nombre_archivo': r[2], 'ruta_archivo': r[3],
                'tamano_bytes': r[4], 'paginas': r[5], 'autor': r[6], 'fecha_carga': r[7],
                'categoria': r[8], 'etiquetas': json.loads(r[9]) if r[9] else None,
                'estado_procesamiento': r[10], 'origen': r[11]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener documentos: {e}")
            return []
            
    def obtener_paginas_documento(self, documento_id: int) -> List[Dict]:
        """Obtiene las páginas de un documento."""
        try:
            self.cursor.execute("""
                SELECT * FROM paginas_documento WHERE documento_id = ? ORDER BY numero_pagina
            """, (documento_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'documento_id': r[1], 'numero_pagina': r[2],
                'texto_extraido': r[3], 'texto_limpio': r[4],
                'fecha_procesamiento': r[5], 'metodo_extraccion': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener páginas: {e}")
            return []
            
    def obtener_conocimiento_documento(self, documento_id: int) -> List[Dict]:
        """Obtiene el conocimiento extraído de un documento."""
        try:
            self.cursor.execute("""
                SELECT * FROM conocimiento_pdf WHERE documento_id = ?
            """, (documento_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'documento_id': r[1], 'tipo_conocimiento': r[2],
                'contenido': r[3], 'contexto': r[4], 'pagina_referencia': r[5],
                'confianza': r[6], 'categoria': r[7], 'fecha_extraccion': r[8],
                'validado': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener conocimiento: {e}")
            return []
            
    def buscar_conocimiento(self, termino: str, tipo: str = None) -> List[Dict]:
        """Busca conocimiento por término."""
        try:
            query = """
                SELECT k.*, d.nombre_archivo
                FROM conocimiento_pdf k
                JOIN documentos_pdf d ON k.documento_id = d.id
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
                'id': r[0], 'documento_id': r[1], 'tipo_conocimiento': r[2],
                'contenido': r[3], 'contexto': r[4], 'pagina_referencia': r[5],
                'confianza': r[6], 'categoria': r[7], 'fecha_extraccion': r[8],
                'validado': r[9], 'nombre_archivo': r[10]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al buscar conocimiento: {e}")
            return []
            
    def obtener_estadisticas(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de procesamiento."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_documentos,
                    SUM(CASE WHEN estado_procesamiento = 'COMPLETADO' THEN 1 ELSE 0 END) as completados,
                    SUM(CASE WHEN estado_procesamiento = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes,
                    SUM(paginas) as total_paginas
                FROM documentos_pdf
                WHERE fecha_carga >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, completados, pendientes, total_paginas = result
                return {
                    'total_documentos': total or 0,
                    'completados': completados or 0,
                    'pendientes': pendientes or 0,
                    'total_paginas': total_paginas or 0,
                    'tasa_completamiento': round((completados / total * 100) if total > 0 else 0, 2),
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
    
    agente = AgenteProcesadorPdfs()
    
    # Ejemplo: registrar documento
    documento_id = agente.registrar_documento(
        archivo_id="PDF-001",
        nombre_archivo="Trading Strategies Guide.pdf",
        ruta_archivo="/docs/guide.pdf",
        tamano_bytes=1024000,
        paginas=50,
        autor="Expert Trader",
        categoria="ESTRATEGIAS",
        etiquetas=["scalping", "swing", "forex"],
        origen="MANUAL"
    )
    
    print(f"Documento registrado - ID: {documento_id}")
    
    # Ejemplo: procesar página
    pagina_id = agente.procesar_pagina(
        documento_id=documento_id,
        numero_pagina=1,
        texto_extraido="Chapter 1: Introduction to Trading...",
        metodo_extraccion="OCR"
    )
    
    print(f"Página procesada - ID: {pagina_id}")
    
    # Ejemplo: extraer sección
    seccion_id = agente.extraer_seccion(
        pagina_id=pagina_id,
        tipo_seccion="TITULO",
        titulo="Introduction to Trading",
        contenido="Complete guide to trading strategies...",
        importancia=1
    )
    
    print(f"Sección extraída - ID: {seccion_id}")
    
    # Ejemplo: extraer conocimiento
    conocimiento_id = agente.extraer_conocimiento(
        documento_id=documento_id,
        tipo_conocimiento="CONCEPTO",
        contenido="Risk management is essential in trading...",
        contexto="Chapter 1",
        pagina_referencia=1,
        categoria="RIESGO",
        confianza=0.9
    )
    
    print(f"Conocimiento extraído - ID: {conocimiento_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

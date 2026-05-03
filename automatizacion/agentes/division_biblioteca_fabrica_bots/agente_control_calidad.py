"""
Agente Control Calidad - D8: Biblioteca Fábrica de Bots
Valida y prueba bots antes de producción

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Realiza pruebas de calidad en los bots generados,
             valida backtesting, parámetros y rendimiento antes de aprobar
             para producción.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteControlCalidad:
    """Valida y prueba bots antes de producción."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de control de calidad.
        
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
                CREATE TABLE IF NOT EXISTS pruebas_bot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    nombre_bot TEXT NOT NULL,
                    tipo_prueba TEXT NOT NULL,
                    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin DATETIME,
                    estado TEXT NOT NULL,
                    resultado TEXT,
                    observaciones TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS criterios_calidad (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT,
                    metricas TEXT NOT NULL,
                    valores_minimos TEXT NOT NULL,
                    activo BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS resultados_metricas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prueba_id INTEGER NOT NULL,
                    metrica TEXT NOT NULL,
                    valor REAL NOT NULL,
                    umbral_min REAL,
                    umbral_max REAL,
                    aprobado BOOLEAN NOT NULL,
                    FOREIGN KEY (prueba_id) REFERENCES pruebas_bot(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS aprobaciones_bot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    nombre_bot TEXT NOT NULL,
                    version TEXT NOT NULL,
                    aprobado_por TEXT NOT NULL,
                    fecha_aprobacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    comentarios TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS defectos_encontrados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prueba_id INTEGER NOT NULL,
                    tipo_defecto TEXT NOT NULL,
                    severidad TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prueba_id) REFERENCES pruebas_bot(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_criterio_calidad(self, nombre: str, descripcion: str, metricas: dict,
                              valores_minimos: dict) -> int:
        """
        Crea un criterio de calidad.
        
        Args:
            nombre: Nombre del criterio
            descripcion: Descripción
            metricas: Diccionario de métricas
            valores_minimos: Valores mínimos requeridos
            
        Returns:
            ID del criterio
        """
        try:
            metricas_json = json.dumps(metricas)
            valores_json = json.dumps(valores_minimos)
            
            self.cursor.execute("""
                INSERT INTO criterios_calidad
                (nombre, descripcion, metricas, valores_minimos, activo)
                VALUES (?, ?, ?, ?, TRUE)
            """, (nombre, descripcion, metricas_json, valores_json))
            
            self.conn.commit()
            criterio_id = self.cursor.lastrowid
            logger.info(f"Criterio de calidad creado - ID: {criterio_id} - Nombre: {nombre}")
            return criterio_id
        except Exception as e:
            logger.error(f"Error al crear criterio: {e}")
            raise
            
    def iniciar_prueba(self, bot_id: str, nombre_bot: str, tipo_prueba: str) -> int:
        """
        Inicia una prueba de calidad para un bot.
        
        Args:
            bot_id: ID del bot
            nombre_bot: Nombre del bot
            tipo_prueba: Tipo de prueba (BACKTEST, FORWARD, UNITARIAS)
            
        Returns:
            ID de la prueba
        """
        try:
            self.cursor.execute("""
                INSERT INTO pruebas_bot (bot_id, nombre_bot, tipo_prueba, estado)
                VALUES (?, ?, ?, 'EN_PROGRESO')
            """, (bot_id, nombre_bot, tipo_prueba))
            
            self.conn.commit()
            prueba_id = self.cursor.lastrowid
            logger.info(f"Prueba iniciada - ID: {prueba_id} - Bot: {nombre_bot}")
            return prueba_id
        except Exception as e:
            logger.error(f"Error al iniciar prueba: {e}")
            raise
            
    def registrar_resultado_metrica(self, prueba_id: int, metrica: str, valor: float,
                                  umbral_min: float = None, umbral_max: float = None) -> int:
        """
        Registra el resultado de una métrica.
        
        Args:
            prueba_id: ID de la prueba
            metrica: Nombre de la métrica
            valor: Valor obtenido
            umbral_min: Umbral mínimo
            umbral_max: Umbral máximo
            
        Returns:
            ID del resultado
        """
        try:
            # Determinar si aprobó
            aprobado = True
            if umbral_min and valor < umbral_min:
                aprobado = False
            if umbral_max and valor > umbral_max:
                aprobado = False
                
            self.cursor.execute("""
                INSERT INTO resultados_metricas
                (prueba_id, metrica, valor, umbral_min, umbral_max, aprobado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (prueba_id, metrica, valor, umbral_min, umbral_max, aprobado))
            
            self.conn.commit()
            resultado_id = self.cursor.lastrowid
            return resultado_id
        except Exception as e:
            logger.error(f"Error al registrar métrica: {e}")
            raise
            
    def registrar_defecto(self, prueba_id: int, tipo_defecto: str, severidad: str,
                         descripcion: str) -> int:
        """
        Registra un defecto encontrado.
        
        Args:
            prueba_id: ID de la prueba
            tipo_defecto: Tipo de defecto
            severidad: Severidad (CRITICO, ALTO, MEDIO, BAJO)
            descripcion: Descripción
            
        Returns:
            ID del defecto
        """
        try:
            self.cursor.execute("""
                INSERT INTO defectos_encontrados
                (prueba_id, tipo_defecto, severidad, descripcion, estado)
                VALUES (?, ?, ?, ?, 'ABIERTO')
            """, (prueba_id, tipo_defecto, severidad, descripcion))
            
            self.conn.commit()
            defecto_id = self.cursor.lastrowid
            logger.warning(f"Defecto registrado - ID: {defecto_id} - Severidad: {severidad}")
            return defecto_id
        except Exception as e:
            logger.error(f"Error al registrar defecto: {e}")
            raise
            
    def finalizar_prueba(self, prueba_id: int, resultado: str, observaciones: str = None) -> bool:
        """
        Finaliza una prueba.
        
        Args:
            prueba_id: ID de la prueba
            resultado: Resultado (APROBADO, RECHAZADO, CONDICIONAL)
            observaciones: Observaciones
            
        Returns:
            True si se finalizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE pruebas_bot
                SET estado = 'COMPLETADO', resultado = ?, fecha_fin = ?, observaciones = ?
                WHERE id = ?
            """, (resultado, datetime.now().isoformat(), observaciones, prueba_id))
            
            self.conn.commit()
            logger.info(f"Prueba {prueba_id} finalizada - Resultado: {resultado}")
            return True
        except Exception as e:
            logger.error(f"Error al finalizar prueba: {e}")
            return False
            
    def aprobar_bot(self, bot_id: str, nombre_bot: str, version: str, aprobado_por: str,
                   estado: str = "APROBADO", comentarios: str = None) -> int:
        """
        Aprueba o rechaza un bot para producción.
        
        Args:
            bot_id: ID del bot
            nombre_bot: Nombre del bot
            version: Versión
            aprobado_por: Quién aprobó
            estado: Estado (APROBADO, RECHAZADO, PENDIENTE)
            comentarios: Comentarios
            
        Returns:
            ID de la aprobación
        """
        try:
            self.cursor.execute("""
                INSERT INTO aprobaciones_bot
                (bot_id, nombre_bot, version, aprobado_por, estado, comentarios)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (bot_id, nombre_bot, version, aprobado_por, estado, comentarios))
            
            self.conn.commit()
            aprobacion_id = self.cursor.lastrowid
            logger.info(f"Bot {nombre_bot} - Estado: {estado} - Por: {aprobado_por}")
            return aprobacion_id
        except Exception as e:
            logger.error(f"Error al aprobar bot: {e}")
            raise
            
    def obtener_pruebas_bot(self, bot_id: str = None, estado: str = None) -> List[Dict]:
        """Obtiene pruebas de bots."""
        try:
            query = "SELECT * FROM pruebas_bot"
            params = []
            
            conditions = []
            if bot_id:
                conditions.append("bot_id = ?")
                params.append(bot_id)
            if estado:
                conditions.append("estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY fecha_inicio DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'bot_id': r[1], 'nombre_bot': r[2], 'tipo_prueba': r[3],
                'fecha_inicio': r[4], 'fecha_fin': r[5], 'estado': r[6],
                'resultado': r[7], 'observaciones': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener pruebas: {e}")
            return []
            
    def obtener_resultados_prueba(self, prueba_id: int) -> List[Dict]:
        """Obtiene los resultados de métricas de una prueba."""
        try:
            self.cursor.execute("""
                SELECT * FROM resultados_metricas WHERE prueba_id = ?
            """, (prueba_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'prueba_id': r[1], 'metrica': r[2], 'valor': r[3],
                'umbral_min': r[4], 'umbral_max': r[5], 'aprobado': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener resultados: {e}")
            return []
            
    def obtener_defectos(self, prueba_id: int = None, estado: str = None) -> List[Dict]:
        """Obtiene defectos encontrados."""
        try:
            query = "SELECT * FROM defectos_encontrados"
            params = []
            
            conditions = []
            if prueba_id:
                conditions.append("prueba_id = ?")
                params.append(prueba_id)
            if estado:
                conditions.append("estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY fecha_deteccion DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'prueba_id': r[1], 'tipo_defecto': r[2],
                'severidad': r[3], 'descripcion': r[4], 'estado': r[5],
                'fecha_deteccion': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener defectos: {e}")
            return []
            
    def obtener_aprobaciones_bot(self, bot_id: str = None) -> List[Dict]:
        """Obtiene aprobaciones de bots."""
        try:
            if bot_id:
                self.cursor.execute("""
                    SELECT * FROM aprobaciones_bot WHERE bot_id = ? ORDER BY fecha_aprobacion DESC
                """, (bot_id,))
            else:
                self.cursor.execute("""
                    SELECT * FROM aprobaciones_bot ORDER BY fecha_aprobacion DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'bot_id': r[1], 'nombre_bot': r[2], 'version': r[3],
                'aprobado_por': r[4], 'fecha_aprobacion': r[5], 'estado': r[6],
                'comentarios': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener aprobaciones: {e}")
            return []
            
    def obtener_estadisticas_calidad(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de control de calidad."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_pruebas,
                    SUM(CASE WHEN resultado = 'APROBADO' THEN 1 ELSE 0 END) as aprobadas,
                    SUM(CASE WHEN resultado = 'RECHAZADO' THEN 1 ELSE 0 END) as rechazadas,
                    SUM(CASE WHEN resultado = 'CONDICIONAL' THEN 1 ELSE 0 END) as condicionales
                FROM pruebas_bot
                WHERE fecha_inicio >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, aprobadas, rechazadas, condicionales = result
                return {
                    'total_pruebas': total or 0,
                    'aprobadas': aprobadas or 0,
                    'rechazadas': rechazadas or 0,
                    'condicionales': condicionales or 0,
                    'tasa_aprobacion': round((aprobadas / total * 100) if total > 0 else 0, 2),
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
    
    agente = AgenteControlCalidad()
    
    # Ejemplo: crear criterio
    criterio_id = agente.crear_criterio_calidad(
        nombre="Bot-Standard",
        descripcion="Criterios estándar para bots de producción",
        metricas={"profit_factor": "ratio", "max_dd": "porcentaje", "sharpe": "ratio"},
        valores_minimos={"profit_factor": 1.5, "max_dd": 20, "sharpe": 1.0}
    )
    
    print(f"Criterio creado - ID: {criterio_id}")
    
    # Ejemplo: iniciar prueba
    prueba_id = agente.iniciar_prueba(
        bot_id="BOT-001",
        nombre_bot="Bot-Scalping-EURUSD",
        tipo_prueba="BACKTEST"
    )
    
    print(f"Prueba iniciada - ID: {prueba_id}")
    
    # Ejemplo: registrar métricas
    agente.registrar_resultado_metrica(prueba_id, "profit_factor", 1.8, 1.5)
    agente.registrar_resultado_metrica(prueba_id, "max_dd", 15, None, 20)
    agente.registrar_resultado_metrica(prueba_id, "sharpe", 1.2, 1.0)
    
    print("Métricas registradas")
    
    # Ejemplo: finalizar prueba
    agente.finalizar_prueba(prueba_id, "APROBADO", "Todas las métricas cumplen criterios")
    
    # Ejemplo: aprobar bot
    aprobacion_id = agente.aprobar_bot(
        bot_id="BOT-001",
        nombre_bot="Bot-Scalping-EURUSD",
        version="1.0",
        aprobado_por="Control Calidad",
        estado="APROBADO"
    )
    
    print(f"Bot aprobado - ID: {aprobacion_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas_calidad()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

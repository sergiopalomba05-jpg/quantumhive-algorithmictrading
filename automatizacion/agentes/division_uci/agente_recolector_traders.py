"""
Agente Recolector Traders - D18: UCI (Unidad de Conocimiento e Inteligencia)
Recolecta información y perfiles de traders exitosos

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Recolecta información de traders exitosos, analiza sus estrategias,
             patrones de trading y genera perfiles para la base de conocimiento.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteRecolectorTraders:
    """Recolecta información y perfiles de traders exitosos."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente recolector de traders.
        
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
                CREATE TABLE IF NOT EXISTS perfiles_trader (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trader_id TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    plataforma TEXT NOT NULL,
                    url_perfil TEXT,
                    especialidad TEXT,
                    nivel_experiencia TEXT,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS estadisticas_trader (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trader_id TEXT NOT NULL,
                    profit_factor REAL,
                    max_dd REAL,
                    sharpe_ratio REAL,
                    winrate REAL,
                    total_trades INTEGER,
                    capital_inicial REAL,
                    capital_actual REAL,
                    periodo_analisis TEXT,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trader_id) REFERENCES perfiles_trader(trader_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS estrategias_trader (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trader_id TEXT NOT NULL,
                    nombre_estrategia TEXT NOT NULL,
                    tipo_estrategia TEXT NOT NULL,
                    instrumentos TEXT,
                    timeframe TEXT,
                    descripcion TEXT,
                    parametros TEXT,
                    rendimiento_promedio REAL,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trader_id) REFERENCES perfiles_trader(trader_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS patrones_trading (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trader_id TEXT NOT NULL,
                    nombre_patron TEXT NOT NULL,
                    tipo_patron TEXT NOT NULL,
                    descripcion TEXT,
                    condiciones_entrada TEXT,
                    condiciones_salida TEXT,
                    gestion_riesgo TEXT,
                    frecuencia_uso INTEGER DEFAULT 0,
                    exito_promedio REAL,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trader_id) REFERENCES perfiles_trader(trader_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS fuentes_trader (
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
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_fuente(self, nombre: str, plataforma: str, url_base: str = None,
                        tipo_fuente: str = "API", configuracion: dict = None) -> int:
        """
        Registra una fuente de traders.
        
        Args:
            nombre: Nombre de la fuente
            plataforma: Plataforma (Myfxbook, TradingView, etc.)
            url_base: URL base
            tipo_fuente: Tipo de fuente (API, WEB, MANUAL)
            configuracion: Configuración de la fuente
            
        Returns:
            ID de la fuente
        """
        try:
            configuracion_json = json.dumps(configuracion) if configuracion else None
            
            self.cursor.execute("""
                INSERT INTO fuentes_trader
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
            
    def recolectar_perfil(self, trader_id: str, nombre: str, plataforma: str,
                         url_perfil: str = None, especialidad: str = None,
                         nivel_experiencia: str = "INTERMEDIO") -> int:
        """
        Recolecta un perfil de trader.
        
        Args:
            trader_id: ID único del trader
            nombre: Nombre del trader
            plataforma: Plataforma
            url_perfil: URL del perfil
            especialidad: Especialidad
            nivel_experiencia: Nivel de experiencia
            
        Returns:
            ID del perfil
        """
        try:
            self.cursor.execute("""
                INSERT INTO perfiles_trader
                (trader_id, nombre, plataforma, url_perfil, especialidad, nivel_experiencia, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO')
            """, (trader_id, nombre, plataforma, url_perfil, especialidad, nivel_experiencia))
            
            self.conn.commit()
            perfil_id = self.cursor.lastrowid
            logger.info(f"Perfil recolectado - ID: {perfil_id} - Trader: {nombre}")
            return perfil_id
        except Exception as e:
            logger.error(f"Error al recolectar perfil: {e}")
            raise
            
    def registrar_estadisticas(self, trader_id: str, profit_factor: float = None,
                             max_dd: float = None, sharpe_ratio: float = None,
                             winrate: float = None, total_trades: int = None,
                             capital_inicial: float = None, capital_actual: float = None,
                             periodo_analisis: str = "MES") -> int:
        """
        Registra estadísticas de un trader.
        
        Args:
            trader_id: ID del trader
            profit_factor: Profit factor
            max_dd: Máximo drawdown
            sharpe_ratio: Sharpe ratio
            winrate: Win rate
            total_trades: Total de trades
            capital_inicial: Capital inicial
            capital_actual: Capital actual
            periodo_analisis: Período de análisis
            
        Returns:
            ID de las estadísticas
        """
        try:
            self.cursor.execute("""
                INSERT INTO estadisticas_trader
                (trader_id, profit_factor, max_dd, sharpe_ratio, winrate, total_trades,
                 capital_inicial, capital_actual, periodo_analisis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (trader_id, profit_factor, max_dd, sharpe_ratio, winrate, total_trades,
                  capital_inicial, capital_actual, periodo_analisis))
            
            self.conn.commit()
            estadisticas_id = self.cursor.lastrowid
            
            # Actualizar fecha de actualización del perfil
            self.cursor.execute("""
                UPDATE perfiles_trader SET ultima_actualizacion = ? WHERE trader_id = ?
            """, (datetime.now().isoformat(), trader_id))
            self.conn.commit()
            
            logger.info(f"Estadísticas registradas - ID: {estadisticas_id} - Trader: {trader_id}")
            return estadisticas_id
        except Exception as e:
            logger.error(f"Error al registrar estadísticas: {e}")
            raise
            
    def registrar_estrategia(self, trader_id: str, nombre_estrategia: str,
                           tipo_estrategia: str, instrumentos: List[str] = None,
                           timeframe: str = None, descripcion: str = None,
                           parametros: dict = None, rendimiento_promedio: float = None) -> int:
        """
        Registra una estrategia de un trader.
        
        Args:
            trader_id: ID del trader
            nombre_estrategia: Nombre de la estrategia
            tipo_estrategia: Tipo de estrategia
            instrumentos: Lista de instrumentos
            timeframe: Timeframe
            descripcion: Descripción
            parametros: Parámetros
            rendimiento_promedio: Rendimiento promedio
            
        Returns:
            ID de la estrategia
        """
        try:
            instrumentos_json = json.dumps(instrumentos) if instrumentos else None
            parametros_json = json.dumps(parametros) if parametros else None
            
            self.cursor.execute("""
                INSERT INTO estrategias_trader
                (trader_id, nombre_estrategia, tipo_estrategia, instrumentos, timeframe,
                 descripcion, parametros, rendimiento_promedio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (trader_id, nombre_estrategia, tipo_estrategia, instrumentos_json,
                  timeframe, descripcion, parametros_json, rendimiento_promedio))
            
            self.conn.commit()
            estrategia_id = self.cursor.lastrowid
            logger.info(f"Estrategia registrada - ID: {estrategia_id} - Nombre: {nombre_estrategia}")
            return estrategia_id
        except Exception as e:
            logger.error(f"Error al registrar estrategia: {e}")
            raise
            
    def registrar_patron(self, trader_id: str, nombre_patron: str, tipo_patron: str,
                       descripcion: str = None, condiciones_entrada: dict = None,
                       condiciones_salida: dict = None, gestion_riesgo: str = None,
                       frecuencia_uso: int = 0, exito_promedio: float = None) -> int:
        """
        Registra un patrón de trading.
        
        Args:
            trader_id: ID del trader
            nombre_patron: Nombre del patrón
            tipo_patron: Tipo de patrón
            descripcion: Descripción
            condiciones_entrada: Condiciones de entrada
            condiciones_salida: Condiciones de salida
            gestion_riesgo: Gestión de riesgo
            frecuencia_uso: Frecuencia de uso
            exito_promedio: Éxito promedio
            
        Returns:
            ID del patrón
        """
        try:
            entrada_json = json.dumps(condiciones_entrada) if condiciones_entrada else None
            salida_json = json.dumps(condiciones_salida) if condiciones_salida else None
            
            self.cursor.execute("""
                INSERT INTO patrones_trading
                (trader_id, nombre_patron, tipo_patron, descripcion, condiciones_entrada,
                 condiciones_salida, gestion_riesgo, frecuencia_uso, exito_promedio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (trader_id, nombre_patron, tipo_patron, descripcion, entrada_json,
                  salida_json, gestion_riesgo, frecuencia_uso, exito_promedio))
            
            self.conn.commit()
            patron_id = self.cursor.lastrowid
            logger.info(f"Patrón registrado - ID: {patron_id} - Nombre: {nombre_patron}")
            return patron_id
        except Exception as e:
            logger.error(f"Error al registrar patrón: {e}")
            raise
            
    def obtener_perfiles(self, especialidad: str = None, estado: str = "ACTIVO") -> List[Dict]:
        """Obtiene perfiles de traders."""
        try:
            query = "SELECT * FROM perfiles_trader"
            params = []
            
            conditions = []
            if especialidad:
                conditions.append("especialidad = ?")
                params.append(especialidad)
            if estado:
                conditions.append("estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY ultima_actualizacion DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'trader_id': r[1], 'nombre': r[2], 'plataforma': r[3],
                'url_perfil': r[4], 'especialidad': r[5], 'nivel_experiencia': r[6],
                'fecha_registro': r[7], 'ultima_actualizacion': r[8], 'estado': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener perfiles: {e}")
            return []
            
    def obtener_estadisticas_trader(self, trader_id: str) -> List[Dict]:
        """Obtiene estadísticas de un trader."""
        try:
            self.cursor.execute("""
                SELECT * FROM estadisticas_trader WHERE trader_id = ? ORDER BY fecha_registro DESC
            """, (trader_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'trader_id': r[1], 'profit_factor': r[2], 'max_dd': r[3],
                'sharpe_ratio': r[4], 'winrate': r[5], 'total_trades': r[6],
                'capital_inicial': r[7], 'capital_actual': r[8],
                'periodo_analisis': r[9], 'fecha_registro': r[10]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return []
            
    def obtener_estrategias_trader(self, trader_id: str) -> List[Dict]:
        """Obtiene estrategias de un trader."""
        try:
            self.cursor.execute("""
                SELECT * FROM estrategias_trader WHERE trader_id = ?
            """, (trader_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'trader_id': r[1], 'nombre_estrategia': r[2],
                'tipo_estrategia': r[3], 'instrumentos': json.loads(r[4]) if r[4] else None,
                'timeframe': r[5], 'descripcion': r[6],
                'parametros': json.loads(r[7]) if r[7] else None,
                'rendimiento_promedio': r[8], 'fecha_registro': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener estrategias: {e}")
            return []
            
    def obtener_patrones_trader(self, trader_id: str) -> List[Dict]:
        """Obtiene patrones de un trader."""
        try:
            self.cursor.execute("""
                SELECT * FROM patrones_trading WHERE trader_id = ? ORDER BY exito_promedio DESC
            """, (trader_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'trader_id': r[1], 'nombre_patron': r[2], 'tipo_patron': r[3],
                'descripcion': r[4], 'condiciones_entrada': json.loads(r[5]) if r[5] else None,
                'condiciones_salida': json.loads(r[6]) if r[6] else None,
                'gestion_riesgo': r[7], 'frecuencia_uso': r[8],
                'exito_promedio': r[9], 'fecha_registro': r[10]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener patrones: {e}")
            return []
            
    def buscar_traders_por_estrategia(self, tipo_estrategia: str) -> List[Dict]:
        """Busca traders por tipo de estrategia."""
        try:
            self.cursor.execute("""
                SELECT DISTINCT p.* FROM perfiles_trader p
                JOIN estrategias_trader e ON p.trader_id = e.trader_id
                WHERE e.tipo_estrategia = ? AND p.estado = 'ACTIVO'
            """, (tipo_estrategia,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'trader_id': r[1], 'nombre': r[2], 'plataforma': r[3],
                'url_perfil': r[4], 'especialidad': r[5], 'nivel_experiencia': r[6],
                'fecha_registro': r[7], 'ultima_actualizacion': r[8], 'estado': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al buscar traders: {e}")
            return []
            
    def obtener_estadisticas(self, dias: int = 30) -> Dict:
        """Obtiene estadísticas de recolección."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_traders,
                    AVG(s.capital_actual) as avg_capital,
                    AVG(s.winrate) as avg_winrate,
                    AVG(s.profit_factor) as avg_profit_factor
                FROM perfiles_trader p
                LEFT JOIN estadisticas_trader s ON p.trader_id = s.trader_id
                WHERE p.fecha_registro >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, avg_capital, avg_winrate, avg_profit_factor = result
                return {
                    'total_traders': total or 0,
                    'avg_capital': round(avg_capital or 0, 2),
                    'avg_winrate': round(avg_winrate or 0, 2),
                    'avg_profit_factor': round(avg_profit_factor or 0, 2),
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
    
    agente = AgenteRecolectorTraders()
    
    # Ejemplo: registrar fuente
    fuente_id = agente.registrar_fuente(
        nombre="Myfxbook Top Traders",
        plataforma="Myfxbook",
        url_base="https://myfxbook.com",
        tipo_fuente="API",
        configuracion={"api_key": "xxx"}
    )
    
    print(f"Fuente registrada - ID: {fuente_id}")
    
    # Ejemplo: recolectar perfil
    perfil_id = agente.recolectar_perfil(
        trader_id="TRD-001",
        nombre="TraderPro",
        plataforma="Myfxbook",
        url_perfil="https://myfxbook.com/traderpro",
        especialidad="SCALPING",
        nivel_experiencia="AVANZADO"
    )
    
    print(f"Perfil recolectado - ID: {perfil_id}")
    
    # Ejemplo: registrar estadísticas
    estadisticas_id = agente.registrar_estadisticas(
        trader_id="TRD-001",
        profit_factor=2.5,
        max_dd=15,
        sharpe_ratio=1.8,
        winrate=65,
        total_trades=500,
        capital_inicial=10000,
        capital_actual=25000
    )
    
    print(f"Estadísticas registradas - ID: {estadisticas_id}")
    
    # Ejemplo: registrar estrategia
    estrategia_id = agente.registrar_estrategia(
        trader_id="TRD-001",
        nombre_estrategia="Scalping EURUSD",
        tipo_estrategia="SCALPING",
        instrumentos=["EURUSD"],
        timeframe="M1",
        descripcion="Estrategia de scalping para EURUSD",
        rendimiento_promedio=150
    )
    
    print(f"Estrategia registrada - ID: {estrategia_id}")
    
    # Ejemplo: registrar patrón
    patron_id = agente.registrar_patron(
        trader_id="TRD-001",
        nombre_patron="Breakout London",
        tipo_patron="BREAKOUT",
        descripcion="Patrón de breakout en apertura de Londres",
        frecuencia_uso=30,
        exito_promedio=70
    )
    
    print(f"Patrón registrado - ID: {patron_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

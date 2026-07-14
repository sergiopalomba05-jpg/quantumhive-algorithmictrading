"""
Agente Pool Capital - D16: Sala de Inversión Colmena
Gestiona pool de capital colectivo

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona el pool de capital colectivo de QuantumHive,
             administra asignaciones, rendimientos y distribución de capital.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgentePoolCapital:
    """Gestiona el pool de capital colectivo."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de pool de capital.
        
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
                CREATE TABLE IF NOT EXISTS pool_capital (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    capital_total REAL NOT NULL,
                    capital_disponible REAL NOT NULL,
                    capital_asignado REAL NOT NULL,
                    capital_bloqueado REAL NOT NULL,
                    moneda TEXT DEFAULT 'USD',
                    fecha_inicio DATETIME NOT NULL,
                    estado TEXT NOT NULL,
                    descripcion TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS inversores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    inversor_id TEXT NOT NULL,
                    nombre_inversor TEXT NOT NULL,
                    inversion_inicial REAL NOT NULL,
                    inversion_actual REAL NOT NULL,
                    porcentaje_participacion REAL NOT NULL,
                    fecha_inversion DATETIME NOT NULL,
                    estado TEXT NOT NULL,
                    FOREIGN KEY (pool_id) REFERENCES pool_capital(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS asignaciones_capital (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    cuenta_asignada TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    monto_asignado REAL NOT NULL,
                    rendimiento_actual REAL DEFAULT 0,
                    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    FOREIGN KEY (pool_id) REFERENCES pool_capital(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS rendimientos_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    periodo TEXT NOT NULL,
                    rendimiento_porcentaje REAL NOT NULL,
                    rendimiento_absoluto REAL NOT NULL,
                    fecha_inicio_periodo DATETIME NOT NULL,
                    fecha_fin_periodo DATETIME NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES pool_capital(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_transacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    tipo_transaccion TEXT NOT NULL,
                    monto REAL NOT NULL,
                    descripcion TEXT,
                    fecha_transaccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES pool_capital(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_pool(self, nombre: str, capital_inicial: float, moneda: str = "USD",
                  descripcion: str = None) -> int:
        """
        Crea un nuevo pool de capital.
        
        Args:
            nombre: Nombre del pool
            capital_inicial: Capital inicial
            moneda: Moneda del capital
            descripcion: Descripción del pool
            
        Returns:
            ID del pool creado
        """
        try:
            self.cursor.execute("""
                INSERT INTO pool_capital
                (nombre, capital_total, capital_disponible, capital_asignado, capital_bloqueado,
                 moneda, fecha_inicio, estado, descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
            """, (nombre, capital_inicial, capital_inicial, 0, 0, moneda,
                  datetime.now().isoformat(), descripcion))
            
            self.conn.commit()
            pool_id = self.cursor.lastrowid
            logger.info(f"Pool de capital creado - ID: {pool_id} - Nombre: {nombre}")
            return pool_id
        except Exception as e:
            logger.error(f"Error al crear pool: {e}")
            raise
            
    def agregar_inversor(self, pool_id: int, inversor_id: str, nombre_inversor: str,
                        monto_inversion: float) -> int:
        """
        Agrega un inversor al pool.
        
        Args:
            pool_id: ID del pool
            inversor_id: ID del inversor
            nombre_inversor: Nombre del inversor
            monto_inversion: Monto de inversión
            
        Returns:
            ID del inversor agregado
        """
        try:
            # Obtener capital total del pool
            self.cursor.execute("""
                SELECT capital_total FROM pool_capital WHERE id = ?
            """, (pool_id,))
            capital_total = self.cursor.fetchone()[0]
            
            porcentaje = (monto_inversion / capital_total * 100) if capital_total > 0 else 0
            
            self.cursor.execute("""
                INSERT INTO inversores
                (pool_id, inversor_id, nombre_inversor, inversion_inicial, inversion_actual,
                 porcentaje_participacion, fecha_inversion, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVO')
            """, (pool_id, inversor_id, nombre_inversor, monto_inversion, monto_inversion,
                  porcentaje, datetime.now().isoformat()))
            
            self.conn.commit()
            inversor_db_id = self.cursor.lastrowid
            
            # Registrar transacción
            self._registrar_transaccion(pool_id, 'APORTE', monto_inversion,
                                      f"Aporte de {nombre_inversor}")
            
            logger.info(f"Inversor agregado - ID: {inversor_db_id} - Pool: {pool_id}")
            return inversor_db_id
        except Exception as e:
            logger.error(f"Error al agregar inversor: {e}")
            raise
            
    def asignar_capital(self, pool_id: int, cuenta: str, propfirm: str, monto: float) -> int:
        """
        Asigna capital a una cuenta.
        
        Args:
            pool_id: ID del pool
            cuenta: Número de cuenta
            propfirm: Propfirm
            monto: Monto a asignar
            
        Returns:
            ID de la asignación
        """
        try:
            # Verificar capital disponible
            self.cursor.execute("""
                SELECT capital_disponible FROM pool_capital WHERE id = ?
            """, (pool_id,))
            disponible = self.cursor.fetchone()[0]
            
            if monto > disponible:
                raise Exception(f"Capital insuficiente. Disponible: {disponible}, Solicitado: {monto}")
                
            self.cursor.execute("""
                INSERT INTO asignaciones_capital
                (pool_id, cuenta_asignada, propfirm, monto_asignado, estado)
                VALUES (?, ?, ?, ?, 'ACTIVA')
            """, (pool_id, cuenta, propfirm, monto))
            
            # Actualizar pool
            self.cursor.execute("""
                UPDATE pool_capital
                SET capital_disponible = capital_disponible - ?,
                    capital_asignado = capital_asignado + ?
                WHERE id = ?
            """, (monto, monto, pool_id))
            
            self.conn.commit()
            asignacion_id = self.cursor.lastrowid
            
            # Registrar transacción
            self._registrar_transaccion(pool_id, 'ASIGNACION', monto,
                                      f"Asignación a cuenta {cuenta}")
            
            logger.info(f"Capital asignado - ID: {asignacion_id} - Cuenta: {cuenta}")
            return asignacion_id
        except Exception as e:
            logger.error(f"Error al asignar capital: {e}")
            raise
            
    def actualizar_rendimiento_asignacion(self, asignacion_id: int, rendimiento: float) -> bool:
        """
        Actualiza el rendimiento de una asignación.
        
        Args:
            asignacion_id: ID de la asignación
            rendimiento: Rendimiento actual
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE asignaciones_capital SET rendimiento_actual = ? WHERE id = ?
            """, (rendimiento, asignacion_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar rendimiento: {e}")
            return False
            
    def registrar_rendimiento_periodo(self, pool_id: int, periodo: str, rendimiento_pct: float,
                                    rendimiento_abs: float, fecha_inicio: datetime,
                                    fecha_fin: datetime) -> int:
        """
        Registra el rendimiento de un período.
        
        Args:
            pool_id: ID del pool
            periodo: Identificador del período (ej: "2026-05")
            rendimiento_pct: Rendimiento en porcentaje
            rendimiento_abs: Rendimiento absoluto
            fecha_inicio: Inicio del período
            fecha_fin: Fin del período
            
        Returns:
            ID del rendimiento registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO rendimientos_pool
                (pool_id, periodo, rendimiento_porcentaje, rendimiento_absoluto,
                 fecha_inicio_periodo, fecha_fin_periodo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pool_id, periodo, rendimiento_pct, rendimiento_abs,
                  fecha_inicio.isoformat(), fecha_fin.isoformat()))
            
            self.conn.commit()
            rendimiento_id = self.cursor.lastrowid
            logger.info(f"Rendimiento registrado - ID: {rendimiento_id} - Periodo: {periodo}")
            return rendimiento_id
        except Exception as e:
            logger.error(f"Error al registrar rendimiento: {e}")
            raise
            
    def _registrar_transaccion(self, pool_id: int, tipo: str, monto: float, descripcion: str):
        """Registra una transacción en el pool."""
        try:
            self.cursor.execute("""
                INSERT INTO historico_transacciones (pool_id, tipo_transaccion, monto, descripcion)
                VALUES (?, ?, ?, ?)
            """, (pool_id, tipo, monto, descripcion))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar transacción: {e}")
            
    def obtener_pool(self, pool_id: int) -> Optional[Dict]:
        """Obtiene información de un pool."""
        try:
            self.cursor.execute("""
                SELECT * FROM pool_capital WHERE id = ?
            """, (pool_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'nombre': result[1], 'capital_total': result[2],
                    'capital_disponible': result[3], 'capital_asignado': result[4],
                    'capital_bloqueado': result[5], 'moneda': result[6],
                    'fecha_inicio': result[7], 'estado': result[8], 'descripcion': result[9]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener pool: {e}")
            return None
            
    def obtener_inversores(self, pool_id: int) -> List[Dict]:
        """Obtiene los inversores de un pool."""
        try:
            self.cursor.execute("""
                SELECT * FROM inversores WHERE pool_id = ? ORDER BY fecha_inversion DESC
            """, (pool_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'pool_id': r[1], 'inversor_id': r[2], 'nombre_inversor': r[3],
                'inversion_inicial': r[4], 'inversion_actual': r[5],
                'porcentaje_participacion': r[6], 'fecha_inversion': r[7], 'estado': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener inversores: {e}")
            return []
            
    def obtener_asignaciones(self, pool_id: int) -> List[Dict]:
        """Obtiene las asignaciones de capital de un pool."""
        try:
            self.cursor.execute("""
                SELECT * FROM asignaciones_capital WHERE pool_id = ? ORDER BY fecha_asignacion DESC
            """, (pool_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'pool_id': r[1], 'cuenta_asignada': r[2], 'propfirm': r[3],
                'monto_asignado': r[4], 'rendimiento_actual': r[5], 'fecha_asignacion': r[6],
                'estado': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener asignaciones: {e}")
            return []
            
    def obtener_rendimientos(self, pool_id: int, periodos: int = 12) -> List[Dict]:
        """Obtiene los rendimientos históricos de un pool."""
        try:
            self.cursor.execute("""
                SELECT * FROM rendimientos_pool
                WHERE pool_id = ?
                ORDER BY fecha_inicio_periodo DESC
                LIMIT ?
            """, (pool_id, periodos))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'pool_id': r[1], 'periodo': r[2],
                'rendimiento_porcentaje': r[3], 'rendimiento_absoluto': r[4],
                'fecha_inicio_periodo': r[5], 'fecha_fin_periodo': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener rendimientos: {e}")
            return []
            
    def obtener_transacciones(self, pool_id: int, dias: int = 30) -> List[Dict]:
        """Obtiene el histórico de transacciones de un pool."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT * FROM historico_transacciones
                WHERE pool_id = ? AND fecha_transaccion >= ?
                ORDER BY fecha_transaccion DESC
            """, (pool_id, fecha_limite.isoformat()))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'pool_id': r[1], 'tipo_transaccion': r[2],
                'monto': r[3], 'descripcion': r[4], 'fecha_transaccion': r[5]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener transacciones: {e}")
            return []
            
    def obtener_resumen_pool(self, pool_id: int) -> Dict:
        """Obtiene un resumen completo del pool."""
        try:
            pool = self.obtener_pool(pool_id)
            if not pool:
                return {}
                
            inversores = self.obtener_inversores(pool_id)
            asignaciones = self.obtener_asignaciones(pool_id)
            rendimientos = self.obtener_rendimientos(pool_id, 3)
            
            total_inversores = sum(i['inversion_actual'] for i in inversores)
            total_asignado = sum(a['monto_asignado'] for a in asignaciones)
            total_rendimiento = sum(a['rendimiento_actual'] for a in asignaciones)
            
            return {
                'pool': pool,
                'total_inversores': total_inversores,
                'numero_inversores': len(inversores),
                'total_asignado': total_asignado,
                'numero_asignaciones': len(asignaciones),
                'rendimiento_total': total_rendimiento,
                'ultimos_rendimientos': rendimientos
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            return {}
            
    def retirar_capital(self, asignacion_id: int, monto: float) -> bool:
        """
        Retira capital de una asignación.
        
        Args:
            asignacion_id: ID de la asignación
            monto: Monto a retirar
            
        Returns:
            True si se retiró correctamente
        """
        try:
            # Obtener asignación
            self.cursor.execute("""
                SELECT pool_id, cuenta_asignada, monto_asignado FROM asignaciones_capital WHERE id = ?
            """, (asignacion_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False
                
            pool_id, cuenta, monto_asignado = result
            
            # Actualizar asignación
            nuevo_monto = max(0, monto_asignado - monto)
            
            if nuevo_monto == 0:
                self.cursor.execute("""
                    UPDATE asignaciones_capital SET estado = 'CERRADA' WHERE id = ?
                """, (asignacion_id,))
            else:
                self.cursor.execute("""
                    UPDATE asignaciones_capital SET monto_asignado = ? WHERE id = ?
                """, (nuevo_monto, asignacion_id))
                
            # Actualizar pool
            self.cursor.execute("""
                UPDATE pool_capital
                SET capital_asignado = capital_asignado - ?,
                    capital_disponible = capital_disponible + ?
                WHERE id = ?
            """, (monto, monto, pool_id))
            
            self.conn.commit()
            
            # Registrar transacción
            self._registrar_transaccion(pool_id, 'RETIRO', monto,
                                      f"Retiro de cuenta {cuenta}")
            
            logger.info(f"Capital retirado de asignación {asignacion_id}")
            return True
        except Exception as e:
            logger.error(f"Error al retirar capital: {e}")
            return False
            
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
    
    agente = AgentePoolCapital()
    
    # Ejemplo: crear pool
    pool_id = agente.crear_pool(
        nombre="Pool-QH-2026",
        capital_inicial=100000,
        moneda="USD",
        descripcion="Pool de capital principal QuantumHive 2026"
    )
    
    print(f"Pool creado - ID: {pool_id}")
    
    # Ejemplo: agregar inversor
    inversor_id = agente.agregar_inversor(
        pool_id=pool_id,
        inversor_id="INV001",
        nombre_inversor="Inversor A",
        monto_inversion=50000
    )
    
    print(f"Inversor agregado - ID: {inversor_id}")
    
    # Ejemplo: asignar capital
    asignacion_id = agente.asignar_capital(
        pool_id=pool_id,
        cuenta="123456",
        propfirm="FTMO",
        monto=10000
    )
    
    print(f"Capital asignado - ID: {asignacion_id}")
    
    # Ejemplo: obtener resumen
    resumen = agente.obtener_resumen_pool(pool_id)
    print(f"Resumen pool: {resumen}")
    
    agente.cerrar()

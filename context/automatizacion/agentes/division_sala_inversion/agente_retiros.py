"""
Agente Retiros - D16: Sala de Inversión Colmena
Gestiona solicitudes y procesamiento de retiros

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona las solicitudes de retiro de inversores,
             procesa los pagos y mantiene el histórico de retiros.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteRetiros:
    """Gestiona solicitudes y procesamiento de retiros."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de retiros.
        
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
                CREATE TABLE IF NOT EXISTS solicitudes_retiro (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inversor_id TEXT NOT NULL,
                    nombre_inversor TEXT NOT NULL,
                    pool_id INTEGER NOT NULL,
                    monto_solicitado REAL NOT NULL,
                    moneda TEXT DEFAULT 'USD',
                    metodo_pago TEXT NOT NULL,
                    datos_pago TEXT NOT NULL,
                    motivo TEXT,
                    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    fecha_procesamiento DATETIME,
                    observaciones TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS retiros_procesados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    solicitud_id INTEGER NOT NULL,
                    monto_enviado REAL NOT NULL,
                    comision REAL DEFAULT 0,
                    monto_neto REAL NOT NULL,
                    metodo_pago TEXT NOT NULL,
                    referencia_transaccion TEXT,
                    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado_pago TEXT NOT NULL,
                    FOREIGN KEY (solicitud_id) REFERENCES solicitudes_retiro(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuraciones_retiro (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    monto_minimo REAL NOT NULL,
                    monto_maximo REAL DEFAULT NULL,
                    dias_procesamiento INTEGER DEFAULT 7,
                    metodos_permitidos TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_retiros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inversor_id TEXT NOT NULL,
                    pool_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    fecha_retiro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_configuracion_retiro(self, pool_id: int, monto_minimo: float,
                                  monto_maximo: float = None, dias_procesamiento: int = 7,
                                  metodos_permitidos: List[str] = None) -> int:
        """
        Crea configuración de retiros para un pool.
        
        Args:
            pool_id: ID del pool
            monto_minimo: Monto mínimo de retiro
            monto_maximo: Monto máximo de retiro
            dias_procesamiento: Días para procesar
            metodos_permitidos: Lista de métodos permitidos
            
        Returns:
            ID de la configuración
        """
        try:
            metodos_json = json.dumps(metodos_permitidos) if metodos_permitidos else None
            
            self.cursor.execute("""
                INSERT INTO configuraciones_retiro
                (pool_id, monto_minimo, monto_maximo, dias_procesamiento, metodos_permitidos, activo)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (pool_id, monto_minimo, monto_maximo, dias_procesamiento, metodos_json))
            
            self.conn.commit()
            config_id = self.cursor.lastrowid
            logger.info(f"Configuración de retiro creada - ID: {config_id} - Pool: {pool_id}")
            return config_id
        except Exception as e:
            logger.error(f"Error al crear configuración: {e}")
            raise
            
    def crear_solicitud_retiro(self, inversor_id: str, nombre_inversor: str, pool_id: int,
                             monto: float, metodo_pago: str, datos_pago: dict,
                             motivo: str = None) -> int:
        """
        Crea una solicitud de retiro.
        
        Args:
            inversor_id: ID del inversor
            nombre_inversor: Nombre del inversor
            pool_id: ID del pool
            monto: Monto a retirar
            metodo_pago: Método de pago
            datos_pago: Datos del pago (dict)
            motivo: Motivo del retiro
            
        Returns:
            ID de la solicitud
        """
        try:
            # Verificar configuración
            config = self._obtener_configuracion(pool_id)
            if not config:
                raise Exception("No hay configuración de retiro para este pool")
                
            if monto < config['monto_minimo']:
                raise Exception(f"Monto mínimo es {config['monto_minimo']}")
            if config['monto_maximo'] and monto > config['monto_maximo']:
                raise Exception(f"Monto máximo es {config['monto_maximo']}")
                
            datos_pago_json = json.dumps(datos_pago)
            
            self.cursor.execute("""
                INSERT INTO solicitudes_retiro
                (inversor_id, nombre_inversor, pool_id, monto_solicitado, metodo_pago,
                 datos_pago, motivo, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
            """, (inversor_id, nombre_inversor, pool_id, monto, metodo_pago,
                  datos_pago_json, motivo))
            
            self.conn.commit()
            solicitud_id = self.cursor.lastrowid
            logger.info(f"Solicitud de retiro creada - ID: {solicitud_id} - Inversor: {inversor_id}")
            return solicitud_id
        except Exception as e:
            logger.error(f"Error al crear solicitud: {e}")
            raise
            
    def _obtener_configuracion(self, pool_id: int) -> Optional[Dict]:
        """Obtiene la configuración de retiro de un pool."""
        try:
            self.cursor.execute("""
                SELECT * FROM configuraciones_retiro
                WHERE pool_id = ? AND activo = TRUE
                ORDER BY timestamp DESC LIMIT 1
            """, (pool_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'pool_id': result[1], 'monto_minimo': result[2],
                    'monto_maximo': result[3], 'dias_procesamiento': result[4],
                    'metodos_permitidos': json.loads(result[5]) if result[5] else None
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración: {e}")
            return None
            
    def procesar_retiro(self, solicitud_id: int, monto_enviado: float, comision: float = 0,
                       referencia: str = None) -> int:
        """
        Procesa un retiro.
        
        Args:
            solicitud_id: ID de la solicitud
            monto_enviado: Monto enviado
            comisión: Comisión aplicada
            referencia: Referencia de transacción
            
        Returns:
            ID del retiro procesado
        """
        try:
            # Obtener solicitud
            self.cursor.execute("""
                SELECT inversor_id, pool_id, monto_solicitado FROM solicitudes_retiro WHERE id = ?
            """, (solicitud_id,))
            solicitud = self.cursor.fetchone()
            
            if not solicitud:
                raise Exception("Solicitud no encontrada")
                
            inversor_id, pool_id, monto_solicitado = solicitud
            monto_neto = monto_enviado - comision
            
            # Registrar retiro procesado
            self.cursor.execute("""
                INSERT INTO retiros_procesados
                (solicitud_id, monto_enviado, comision, monto_neto, metodo_pago,
                 referencia_transaccion, estado_pago)
                SELECT ?, ?, ?, ?, metodo_pago, ?, 'COMPLETADO'
                FROM solicitudes_retiro WHERE id = ?
            """, (monto_enviado, comision, monto_neto, referencia, solicitud_id))
            
            self.conn.commit()
            retiro_id = self.cursor.lastrowid
            
            # Actualizar solicitud
            self.cursor.execute("""
                UPDATE solicitudes_retiro
                SET estado = 'COMPLETADO', fecha_procesamiento = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), solicitud_id))
            
            # Registrar en histórico
            self.cursor.execute("""
                INSERT INTO historico_retiros (inversor_id, pool_id, monto, estado)
                VALUES (?, ?, ?, 'COMPLETADO')
            """, (inversor_id, pool_id, monto_enviado))
            
            self.conn.commit()
            logger.info(f"Retiro procesado - ID: {retiro_id} - Solicitud: {solicitud_id}")
            return retiro_id
        except Exception as e:
            logger.error(f"Error al procesar retiro: {e}")
            raise
            
    def rechazar_solicitud(self, solicitud_id: int, motivo: str) -> bool:
        """
        Rechaza una solicitud de retiro.
        
        Args:
            solicitud_id: ID de la solicitud
            motivo: Motivo del rechazo
            
        Returns:
            True si se rechazó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE solicitudes_retiro
                SET estado = 'RECHAZADA', observaciones = ?, fecha_procesamiento = ?
                WHERE id = ?
            """, (motivo, datetime.now().isoformat(), solicitud_id))
            
            self.conn.commit()
            logger.info(f"Solicitud {solicitud_id} rechazada")
            return True
        except Exception as e:
            logger.error(f"Error al rechazar solicitud: {e}")
            return False
            
    def obtener_solicitudes(self, pool_id: int = None, estado: str = None) -> List[Dict]:
        """Obtiene solicitudes de retiro."""
        try:
            query = "SELECT * FROM solicitudes_retiro"
            params = []
            
            conditions = []
            if pool_id:
                conditions.append("pool_id = ?")
                params.append(pool_id)
            if estado:
                conditions.append("estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY fecha_solicitud DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'inversor_id': r[1], 'nombre_inversor': r[2],
                'pool_id': r[3], 'monto_solicitado': r[4], 'moneda': r[5],
                'metodo_pago': r[6], 'datos_pago': json.loads(r[7]) if r[7] else None,
                'motivo': r[8], 'fecha_solicitud': r[9], 'estado': r[10],
                'fecha_procesamiento': r[11], 'observaciones': r[12]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener solicitudes: {e}")
            return []
            
    def obtener_retiros_procesados(self, solicitud_id: int = None) -> List[Dict]:
        """Obtiene retiros procesados."""
        try:
            if solicitud_id:
                self.cursor.execute("""
                    SELECT * FROM retiros_procesados WHERE solicitud_id = ?
                """, (solicitud_id,))
            else:
                self.cursor.execute("""
                    SELECT * FROM retiros_procesados ORDER BY fecha_envio DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'solicitud_id': r[1], 'monto_enviado': r[2],
                'comision': r[3], 'monto_neto': r[4], 'metodo_pago': r[5],
                'referencia_transaccion': r[6], 'fecha_envio': r[7], 'estado_pago': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener retiros procesados: {e}")
            return []
            
    def obtener_historico_inversor(self, inversor_id: str) -> List[Dict]:
        """Obtiene el histórico de retiros de un inversor."""
        try:
            self.cursor.execute("""
                SELECT * FROM historico_retiros WHERE inversor_id = ?
                ORDER BY fecha_retiro DESC
            """, (inversor_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'inversor_id': r[1], 'pool_id': r[2],
                'monto': r[3], 'fecha_retiro': r[4], 'estado': r[5]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener histórico: {e}")
            return []
            
    def obtener_estadisticas(self, pool_id: int, dias: int = 30) -> Dict:
        """Obtiene estadísticas de retiros."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_solicitudes,
                    SUM(monto_solicitado) as total_solicitado,
                    SUM(CASE WHEN estado = 'COMPLETADO' THEN monto_solicitado ELSE 0 END) as total_completado,
                    SUM(CASE WHEN estado = 'PENDIENTE' THEN monto_solicitado ELSE 0 END) as total_pendiente,
                    AVG(CASE WHEN estado = 'COMPLETADO' THEN 
                        julianday(fecha_procesamiento) - julianday(fecha_solicitud) ELSE NULL END) as avg_dias
                FROM solicitudes_retiro
                WHERE pool_id = ? AND fecha_solicitud >= ?
            """, (pool_id, fecha_limite.isoformat()))
            
            result = self.cursor.fetchone()
            
            if result:
                total, total_solicitado, total_completado, total_pendiente, avg_dias = result
                return {
                    'total_solicitudes': total or 0,
                    'total_solicitado': total_solicitado or 0,
                    'total_completado': total_completado or 0,
                    'total_pendiente': total_pendiente or 0,
                    'tasa_completamiento': round((total_completado / total_solicitado * 100) if total_solicitado > 0 else 0, 2),
                    'avg_dias_procesamiento': round(avg_dias or 0, 1),
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
    
    agente = AgenteRetiros()
    
    # Ejemplo: crear configuración
    config_id = agente.crear_configuracion_retiro(
        pool_id=1,
        monto_minimo=100,
        monto_maximo=50000,
        dias_procesamiento=5,
        metodos_permitidos=["BANK_TRANSFER", "CRYPTO", "PAYPAL"]
    )
    
    print(f"Configuración creada - ID: {config_id}")
    
    # Ejemplo: crear solicitud
    solicitud_id = agente.crear_solicitud_retiro(
        inversor_id="INV001",
        nombre_inversor="Inversor A",
        pool_id=1,
        monto=5000,
        metodo_pago="BANK_TRANSFER",
        datos_pago={"banco": "BBVA", "cbu": "0000000000000000000000"},
        motivo="Retiro de ganancias mensuales"
    )
    
    print(f"Solicitud creada - ID: {solicitud_id}")
    
    # Ejemplo: procesar retiro
    retiro_id = agente.procesar_retiro(
        solicitud_id=solicitud_id,
        monto_enviado=5000,
        comision=25,
        referencia="TXN-20260503-001"
    )
    
    print(f"Retiro procesado - ID: {retiro_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas(pool_id=1)
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

"""
Agente Gestor Cuentas - D2B: PropFirms y Dispersión de Cuentas
Asigna cuenta por servidor, firma, riesgo

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona la asignación de cuentas a servidores, firmas y perfiles de riesgo,
             optimiza la distribución de cuentas entre VPS y configuraciones.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteGestorCuentas:
    """Gestiona la asignación de cuentas a servidores y configuraciones."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente gestor de cuentas.
        
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
                CREATE TABLE IF NOT EXISTS servidores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    ip TEXT NOT NULL,
                    proveedor TEXT NOT NULL,
                    ubicacion TEXT,
                    capacidad_maxima INTEGER NOT NULL,
                    cuentas_actuales INTEGER DEFAULT 0,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS firmas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    tipo TEXT NOT NULL,
                    descripcion TEXT,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS perfiles_riesgo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    riesgo_porcentaje REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    lotaje_base REAL NOT NULL,
                    descripcion TEXT,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS asignaciones_cuentas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    servidor_id INTEGER NOT NULL,
                    firma_id INTEGER NOT NULL,
                    perfil_riesgo_id INTEGER NOT NULL,
                    cliente_id TEXT,
                    estado TEXT NOT NULL,
                    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ultima_actualizacion DATETIME,
                    metadata TEXT,
                    FOREIGN KEY (servidor_id) REFERENCES servidores(id),
                    FOREIGN KEY (firma_id) REFERENCES firmas(id),
                    FOREIGN KEY (perfil_riesgo_id) REFERENCES perfiles_riesgo(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reglas_asignacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    propfirm TEXT NOT NULL,
                    servidor_preferido TEXT,
                    firma_preferida TEXT,
                    perfil_riesgo_preferido TEXT,
                    max_cuentas_por_servidor INTEGER,
                    activa BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_servidor(self, nombre: str, ip: str, proveedor: str, ubicacion: str = None,
                          capacidad_maxima: int = 10) -> int:
        """
        Registra un servidor VPS.
        
        Args:
            nombre: Nombre del servidor
            ip: IP del servidor
            proveedor: Proveedor del VPS
            ubicacion: Ubicación del servidor
            capacidad_maxima: Capacidad máxima de cuentas
            
        Returns:
            ID del servidor registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO servidores (nombre, ip, proveedor, ubicacion, capacidad_maxima, estado)
                VALUES (?, ?, ?, ?, ?, 'ACTIVO')
            """, (nombre, ip, proveedor, ubicacion, capacidad_maxima))
            
            self.conn.commit()
            servidor_id = self.cursor.lastrowid
            logger.info(f"Servidor registrado - ID: {servidor_id} - Nombre: {nombre}")
            return servidor_id
        except Exception as e:
            logger.error(f"Error al registrar servidor: {e}")
            raise
            
    def registrar_firma(self, nombre: str, tipo: str, descripcion: str = None) -> int:
        """
        Registra una firma (configuración de fingerprint).
        
        Args:
            nombre: Nombre de la firma
            tipo: Tipo de firma
            descripcion: Descripción
            
        Returns:
            ID de la firma registrada
        """
        try:
            self.cursor.execute("""
                INSERT INTO firmas (nombre, tipo, descripcion, estado)
                VALUES (?, ?, ?, 'ACTIVA')
            """, (nombre, tipo, descripcion))
            
            self.conn.commit()
            firma_id = self.cursor.lastrowid
            logger.info(f"Firma registrada - ID: {firma_id} - Nombre: {nombre}")
            return firma_id
        except Exception as e:
            logger.error(f"Error al registrar firma: {e}")
            raise
            
    def registrar_perfil_riesgo(self, nombre: str, riesgo_porcentaje: float, max_drawdown: float,
                                lotaje_base: float, descripcion: str = None) -> int:
        """
        Registra un perfil de riesgo.
        
        Args:
            nombre: Nombre del perfil
            riesgo_porcentaje: Riesgo por trade
            max_drawdown: Máximo drawdown
            lotaje_base: Lotaje base
            descripcion: Descripción
            
        Returns:
            ID del perfil registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO perfiles_riesgo (nombre, riesgo_porcentaje, max_drawdown, lotaje_base, descripcion, estado)
                VALUES (?, ?, ?, ?, ?, 'ACTIVO')
            """, (nombre, riesgo_porcentaje, max_drawdown, lotaje_base, descripcion))
            
            self.conn.commit()
            perfil_id = self.cursor.lastrowid
            logger.info(f"Perfil de riesgo registrado - ID: {perfil_id} - Nombre: {nombre}")
            return perfil_id
        except Exception as e:
            logger.error(f"Error al registrar perfil de riesgo: {e}")
            raise
            
    def asignar_cuenta(self, cuenta: str, propfirm: str, cliente_id: str = None,
                      servidor_id: int = None, firma_id: int = None,
                      perfil_riesgo_id: int = None, metadata: dict = None) -> int:
        """
        Asigna una cuenta a servidor, firma y perfil de riesgo.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Propfirm
            cliente_id: ID del cliente
            servidor_id: ID del servidor (opcional, auto-asigna si None)
            firma_id: ID de la firma (opcional, auto-asigna si None)
            perfil_riesgo_id: ID del perfil de riesgo (opcional, auto-asigna si None)
            metadata: Metadatos adicionales
            
        Returns:
            ID de la asignación
        """
        try:
            # Auto-asignar si no se especifican
            if servidor_id is None:
                servidor_id = self._obtener_servidor_disponible()
            if firma_id is None:
                firma_id = self._obtener_firma_disponible()
            if perfil_riesgo_id is None:
                perfil_riesgo_id = self._obtener_perfil_riesgo_por_defecto()
                
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.cursor.execute("""
                INSERT INTO asignaciones_cuentas
                (cuenta, propfirm, servidor_id, firma_id, perfil_riesgo_id, cliente_id, estado, metadata)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVA', ?)
            """, (cuenta, propfirm, servidor_id, firma_id, perfil_riesgo_id, cliente_id, metadata_json))
            
            self.conn.commit()
            asignacion_id = self.cursor.lastrowid
            
            # Actualizar contador de cuentas del servidor
            self._actualizar_cuentas_servidor(servidor_id, 1)
            
            logger.info(f"Cuenta asignada - ID: {asignacion_id} - Cuenta: {cuenta}")
            return asignacion_id
        except Exception as e:
            logger.error(f"Error al asignar cuenta: {e}")
            raise
            
    def _obtener_servidor_disponible(self) -> int:
        """Obtiene el servidor con mayor capacidad disponible."""
        try:
            self.cursor.execute("""
                SELECT id, capacidad_maxima - cuentas_actuales as disponible
                FROM servidores
                WHERE estado = 'ACTIVO' AND cuentas_actuales < capacidad_maxima
                ORDER BY disponible DESC
                LIMIT 1
            """)
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Si no hay disponible, crear uno nuevo o usar el primero
                self.cursor.execute("""
                    SELECT id FROM servidores WHERE estado = 'ACTIVO' LIMIT 1
                """)
                result = self.cursor.fetchone()
                if result:
                    return result[0]
                raise Exception("No hay servidores disponibles")
        except Exception as e:
            logger.error(f"Error al obtener servidor disponible: {e}")
            raise
            
    def _obtener_firma_disponible(self) -> int:
        """Obtiene una firma disponible."""
        try:
            self.cursor.execute("""
                SELECT id FROM firmas WHERE estado = 'ACTIVA' LIMIT 1
            """)
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            raise Exception("No hay firmas disponibles")
        except Exception as e:
            logger.error(f"Error al obtener firma disponible: {e}")
            raise
            
    def _obtener_perfil_riesgo_por_defecto(self) -> int:
        """Obtiene el perfil de riesgo por defecto."""
        try:
            self.cursor.execute("""
                SELECT id FROM perfiles_riesgo WHERE estado = 'ACTIVO' LIMIT 1
            """)
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            raise Exception("No hay perfiles de riesgo disponibles")
        except Exception as e:
            logger.error(f"Error al obtener perfil de riesgo por defecto: {e}")
            raise
            
    def _actualizar_cuentas_servidor(self, servidor_id: int, incremento: int):
        """Actualiza el contador de cuentas de un servidor."""
        try:
            self.cursor.execute("""
                UPDATE servidores SET cuentas_actuales = cuentas_actuales + ?
                WHERE id = ?
            """, (incremento, servidor_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al actualizar cuentas servidor: {e}")
            
    def obtener_asignacion(self, cuenta: str) -> Optional[Dict]:
        """
        Obtiene la asignación de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            
        Returns:
            Diccionario con información o None
        """
        try:
            self.cursor.execute("""
                SELECT a.*, s.nombre as servidor_nombre, f.nombre as firma_nombre, p.nombre as perfil_nombre
                FROM asignaciones_cuentas a
                JOIN servidores s ON a.servidor_id = s.id
                JOIN firmas f ON a.firma_id = f.id
                JOIN perfiles_riesgo p ON a.perfil_riesgo_id = p.id
                WHERE a.cuenta = ?
            """, (cuenta,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'cuenta': result[1], 'propfirm': result[2],
                    'servidor_id': result[3], 'firma_id': result[4], 'perfil_riesgo_id': result[5],
                    'cliente_id': result[6], 'estado': result[7], 'fecha_asignacion': result[8],
                    'ultima_actualizacion': result[9], 'metadata': json.loads(result[10]) if result[10] else None,
                    'servidor_nombre': result[11], 'firma_nombre': result[12], 'perfil_nombre': result[13]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener asignación: {e}")
            return None
            
    def obtener_asignaciones_cliente(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene todas las asignaciones de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de asignaciones
        """
        try:
            self.cursor.execute("""
                SELECT a.*, s.nombre as servidor_nombre, f.nombre as firma_nombre, p.nombre as perfil_nombre
                FROM asignaciones_cuentas a
                JOIN servidores s ON a.servidor_id = s.id
                JOIN firmas f ON a.firma_id = f.id
                JOIN perfiles_riesgo p ON a.perfil_riesgo_id = p.id
                WHERE a.cliente_id = ?
                ORDER BY a.fecha_asignacion DESC
            """, (cliente_id,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'propfirm': r[2],
                'servidor_id': r[3], 'firma_id': r[4], 'perfil_riesgo_id': r[5],
                'cliente_id': r[6], 'estado': r[7], 'fecha_asignacion': r[8],
                'ultima_actualizacion': r[9], 'metadata': json.loads(r[10]) if r[10] else None,
                'servidor_nombre': r[11], 'firma_nombre': r[12], 'perfil_nombre': r[13]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener asignaciones del cliente: {e}")
            return []
            
    def obtener_asignaciones_propfirm(self, propfirm: str) -> List[Dict]:
        """
        Obtiene todas las asignaciones de una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            
        Returns:
            Lista de asignaciones
        """
        try:
            self.cursor.execute("""
                SELECT a.*, s.nombre as servidor_nombre, f.nombre as firma_nombre, p.nombre as perfil_nombre
                FROM asignaciones_cuentas a
                JOIN servidores s ON a.servidor_id = s.id
                JOIN firmas f ON a.firma_id = f.id
                JOIN perfiles_riesgo p ON a.perfil_riesgo_id = p.id
                WHERE a.propfirm = ?
                ORDER BY a.fecha_asignacion DESC
            """, (propfirm,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'propfirm': r[2],
                'servidor_id': r[3], 'firma_id': r[4], 'perfil_riesgo_id': r[5],
                'cliente_id': r[6], 'estado': r[7], 'fecha_asignacion': r[8],
                'ultima_actualizacion': r[9], 'metadata': json.loads(r[10]) if r[10] else None,
                'servidor_nombre': r[11], 'firma_nombre': r[12], 'perfil_nombre': r[13]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener asignaciones de propfirm: {e}")
            return []
            
    def obtener_servidores(self) -> List[Dict]:
        """Obtiene todos los servidores."""
        try:
            self.cursor.execute("""
                SELECT * FROM servidores ORDER BY nombre
            """)
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'nombre': r[1], 'ip': r[2], 'proveedor': r[3],
                'ubicacion': r[4], 'capacidad_maxima': r[5], 'cuentas_actuales': r[6],
                'estado': r[7], 'timestamp': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener servidores: {e}")
            return []
            
    def obtener_firmas(self) -> List[Dict]:
        """Obtiene todas las firmas."""
        try:
            self.cursor.execute("""
                SELECT * FROM firmas ORDER BY nombre
            """)
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'nombre': r[1], 'tipo': r[2], 'descripcion': r[3],
                'estado': r[4], 'timestamp': r[5]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener firmas: {e}")
            return []
            
    def obtener_perfiles_riesgo(self) -> List[Dict]:
        """Obtiene todos los perfiles de riesgo."""
        try:
            self.cursor.execute("""
                SELECT * FROM perfiles_riesgo ORDER BY nombre
            """)
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'nombre': r[1], 'riesgo_porcentaje': r[2],
                'max_drawdown': r[3], 'lotaje_base': r[4], 'descripcion': r[5],
                'estado': r[6], 'timestamp': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener perfiles de riesgo: {e}")
            return []
            
    def actualizar_asignacion(self, asignacion_id: int, servidor_id: int = None,
                            firma_id: int = None, perfil_riesgo_id: int = None,
                            estado: str = None) -> bool:
        """
        Actualiza una asignación de cuenta.
        
        Args:
            asignacion_id: ID de la asignación
            servidor_id: Nuevo ID de servidor
            firma_id: Nuevo ID de firma
            perfil_riesgo_id: Nuevo ID de perfil de riesgo
            estado: Nuevo estado
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Obtener asignación actual
            self.cursor.execute("""
                SELECT servidor_id, estado FROM asignaciones_cuentas WHERE id = ?
            """, (asignacion_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False
                
            servidor_actual, estado_actual = result
            
            updates = []
            values = []
            
            if servidor_id and servidor_id != servidor_actual:
                updates.append("servidor_id = ?")
                values.append(servidor_id)
                # Actualizar contadores
                self._actualizar_cuentas_servidor(servidor_actual, -1)
                self._actualizar_cuentas_servidor(servidor_id, 1)
                
            if firma_id:
                updates.append("firma_id = ?")
                values.append(firma_id)
                
            if perfil_riesgo_id:
                updates.append("perfil_riesgo_id = ?")
                values.append(perfil_riesgo_id)
                
            if estado:
                updates.append("estado = ?")
                values.append(estado)
                
            if not updates:
                return False
                
            updates.append("ultima_actualizacion = ?")
            values.append(datetime.now().isoformat())
            values.append(asignacion_id)
            
            query = f"UPDATE asignaciones_cuentas SET {', '.join(updates)} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logger.info(f"Asignación {asignacion_id} actualizada")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar asignación: {e}")
            return False
            
    def desactivar_asignacion(self, asignacion_id: int) -> bool:
        """
        Desactiva una asignación de cuenta.
        
        Args:
            asignacion_id: ID de la asignación
            
        Returns:
            True si se desactivó correctamente
        """
        try:
            # Obtener servidor antes de desactivar
            self.cursor.execute("""
                SELECT servidor_id FROM asignaciones_cuentas WHERE id = ?
            """, (asignacion_id,))
            result = self.cursor.fetchone()
            
            if result:
                servidor_id = result[0]
                self._actualizar_cuentas_servidor(servidor_id, -1)
                
            self.cursor.execute("""
                UPDATE asignaciones_cuentas SET estado = 'INACTIVA', ultima_actualizacion = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), asignacion_id))
            self.conn.commit()
            
            logger.info(f"Asignación {asignacion_id} desactivada")
            return True
        except Exception as e:
            logger.error(f"Error al desactivar asignación: {e}")
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
    
    agente = AgenteGestorCuentas()
    
    # Ejemplo: registrar servidor
    servidor_id = agente.registrar_servidor(
        nombre="VPS-NY-01",
        ip="192.168.1.100",
        proveedor="DigitalOcean",
        ubicacion="New York",
        capacidad_maxima=20
    )
    
    print(f"Servidor registrado - ID: {servidor_id}")
    
    # Ejemplo: registrar firma
    firma_id = agente.registrar_firma(
        nombre="Firma-FTMO-01",
        tipo="hardware",
        descripcion="Fingerprint específico para FTMO"
    )
    
    print(f"Firma registrada - ID: {firma_id}")
    
    # Ejemplo: registrar perfil de riesgo
    perfil_id = agente.registrar_perfil_riesgo(
        nombre="Conservador",
        riesgo_porcentaje=1.0,
        max_drawdown=5.0,
        lotaje_base=0.01,
        descripcion="Perfil de riesgo conservador"
    )
    
    print(f"Perfil de riesgo registrado - ID: {perfil_id}")
    
    # Ejemplo: asignar cuenta
    asignacion_id = agente.asignar_cuenta(
        cuenta="123456",
        propfirm="FTMO",
        cliente_id="CLI001",
        servidor_id=servidor_id,
        firma_id=firma_id,
        perfil_riesgo_id=perfil_id
    )
    
    print(f"Cuenta asignada - ID: {asignacion_id}")
    
    # Ejemplo: obtener asignación
    asignacion = agente.obtener_asignacion("123456")
    print(f"Asignación: {asignacion}")
    
    # Ejemplo: obtener servidores
    servidores = agente.obtener_servidores()
    print(f"Servidores: {len(servidores)}")
    
    agente.cerrar()

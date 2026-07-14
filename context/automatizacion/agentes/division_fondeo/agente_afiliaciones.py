"""
Agente Afiliaciones - D2: Gestión de Fondeo y Challenges
Acuerdos con PropFirms, cupones, comisiones

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona acuerdos de afiliación con propfirms, cupones de descuento,
             comisiones por referido y seguimiento de partnerships.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AgenteAfiliaciones:
    """Gestiona acuerdos de afiliación con propfirms."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de afiliaciones.
        
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
                CREATE TABLE IF NOT EXISTS acuerdos_propfirm (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    propfirm TEXT NOT NULL,
                    tipo_acuerdo TEXT NOT NULL,
                    comision_porcentaje REAL NOT NULL,
                    comision_fija REAL DEFAULT 0,
                    cupon_codigo TEXT,
                    cupon_descuento REAL,
                    cupon_usos INTEGER DEFAULT 0,
                    cupon_max_usos INTEGER,
                    estado TEXT NOT NULL,
                    fecha_inicio DATETIME NOT NULL,
                    fecha_fin DATETIME,
                    condiciones TEXT,
                    observaciones TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS referidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acuerdo_id INTEGER NOT NULL,
                    referido_id TEXT NOT NULL,
                    referido_nombre TEXT NOT NULL,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    monto_comisionado REAL DEFAULT 0,
                    fecha_comision DATETIME,
                    FOREIGN KEY (acuerdo_id) REFERENCES acuerdos_propfirm(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS comisiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acuerdo_id INTEGER NOT NULL,
                    referido_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    porcentaje REAL NOT NULL,
                    fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_pago DATETIME,
                    estado TEXT NOT NULL,
                    metodo_pago TEXT,
                    referencia TEXT,
                    FOREIGN KEY (acuerdo_id) REFERENCES acuerdos_propfirm(id),
                    FOREIGN KEY (referido_id) REFERENCES referidos(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS cupones_usos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cupon_codigo TEXT NOT NULL,
                    cliente_id TEXT NOT NULL,
                    cliente_nombre TEXT NOT NULL,
                    descuento_aplicado REAL NOT NULL,
                    fecha_uso DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_acuerdo(self, propfirm: str, tipo_acuerdo: str, comision_porcentaje: float,
                         comision_fija: float = 0, cupon_codigo: str = None,
                         cupon_descuento: float = None, cupon_max_usos: int = None,
                         fecha_inicio: datetime = None, fecha_fin: datetime = None,
                         condiciones: str = None) -> int:
        """
        Registra un acuerdo de afiliación con una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            tipo_acuerdo: Tipo de acuerdo (ej: referral, partnership)
            comision_porcentaje: Porcentaje de comisión
            comision_fija: Comisión fija (opcional)
            cupon_codigo: Código del cupón (opcional)
            cupon_descuento: Descuento del cupón (opcional)
            cupon_max_usos: Máximo de usos del cupón (opcional)
            fecha_inicio: Fecha de inicio del acuerdo
            fecha_fin: Fecha de fin del acuerdo (opcional)
            condiciones: Condiciones del acuerdo
            
        Returns:
            ID del acuerdo registrado
        """
        try:
            if fecha_inicio is None:
                fecha_inicio = datetime.now()
                
            self.cursor.execute("""
                INSERT INTO acuerdos_propfirm
                (propfirm, tipo_acuerdo, comision_porcentaje, comision_fija,
                 cupon_codigo, cupon_descuento, cupon_max_usos, estado,
                 fecha_inicio, fecha_fin, condiciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (propfirm, tipo_acuerdo, comision_porcentaje, comision_fija,
                  cupon_codigo, cupon_descuento, cupon_max_usos, 'ACTIVO',
                  fecha_inicio.isoformat(), 
                  fecha_fin.isoformat() if fecha_fin else None,
                  condiciones))
            
            self.conn.commit()
            acuerdo_id = self.cursor.lastrowid
            logger.info(f"Acuerdo registrado con {propfirm} - ID: {acuerdo_id}")
            return acuerdo_id
        except Exception as e:
            logger.error(f"Error al registrar acuerdo: {e}")
            raise
            
    def registrar_referido(self, acuerdo_id: int, referido_id: str, referido_nombre: str) -> int:
        """
        Registra un referido bajo un acuerdo.
        
        Args:
            acuerdo_id: ID del acuerdo
            referido_id: ID del referido
            referido_nombre: Nombre del referido
            
        Returns:
            ID del referido registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO referidos (acuerdo_id, referido_id, referido_nombre, estado)
                VALUES (?, ?, ?, 'PENDIENTE')
            """, (acuerdo_id, referido_id, referido_nombre))
            
            self.conn.commit()
            referido_id_db = self.cursor.lastrowid
            logger.info(f"Referido registrado - ID: {referido_id_db} - Nombre: {referido_nombre}")
            return referido_id_db
        except Exception as e:
            logger.error(f"Error al registrar referido: {e}")
            raise
            
    def usar_cupon(self, cupon_codigo: str, cliente_id: str, cliente_nombre: str) -> Optional[float]:
        """
        Registra el uso de un cupón y devuelve el descuento aplicado.
        
        Args:
            cupon_codigo: Código del cupón
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente
            
        Returns:
            Descuento aplicado o None si el cupón no es válido
        """
        try:
            # Verificar cupón
            self.cursor.execute("""
                SELECT cupon_descuento, cupon_usos, cupon_max_usos, estado
                FROM acuerdos_propfirm
                WHERE cupon_codigo = ? AND estado = 'ACTIVO'
            """, (cupon_codigo,))
            
            result = self.cursor.fetchone()
            
            if not result:
                logger.warning(f"Cupón {cupon_codigo} no encontrado o inactivo")
                return None
                
            descuento, usos, max_usos, estado = result
            
            # Verificar límite de usos
            if max_usos and usos >= max_usos:
                logger.warning(f"Cupón {cupon_codigo} alcanzó máximo de usos")
                return None
                
            # Registrar uso
            self.cursor.execute("""
                INSERT INTO cupones_usos (cupon_codigo, cliente_id, cliente_nombre, descuento_aplicado)
                VALUES (?, ?, ?, ?)
            """, (cupon_codigo, cliente_id, cliente_nombre, descuento))
            
            # Actualizar contador de usos
            self.cursor.execute("""
                UPDATE acuerdos_propfirm SET cupon_usos = cupon_usos + 1
                WHERE cupon_codigo = ?
            """, (cupon_codigo,))
            
            self.conn.commit()
            logger.info(f"Cupón {cupon_codigo} usado por {cliente_nombre} - Descuento: {descuento}")
            return descuento
        except Exception as e:
            logger.error(f"Error al usar cupón: {e}")
            return None
            
    def generar_comision(self, acuerdo_id: int, referido_id: int, monto: float) -> int:
        """
        Genera una comisión por un referido.
        
        Args:
            acuerdo_id: ID del acuerdo
            referido_id: ID del referido
            monto: Monto sobre el que se calcula la comisión
            
        Returns:
            ID de la comisión generada
        """
        try:
            # Obtener términos del acuerdo
            self.cursor.execute("""
                SELECT comision_porcentaje, comision_fija FROM acuerdos_propfirm WHERE id = ?
            """, (acuerdo_id,))
            result = self.cursor.fetchone()
            
            if not result:
                logger.error(f"Acuerdo {acuerdo_id} no encontrado")
                return 0
                
            porcentaje, fija = result
            
            # Calcular comisión
            comision = (monto * porcentaje / 100) + fija
            
            # Registrar comisión
            self.cursor.execute("""
                INSERT INTO comisiones
                (acuerdo_id, referido_id, monto, porcentaje, estado)
                VALUES (?, ?, ?, ?, 'PENDIENTE')
            """, (acuerdo_id, referido_id, comision, porcentaje))
            
            self.conn.commit()
            comision_id = self.cursor.lastrowid
            
            # Actualizar referido
            self.cursor.execute("""
                UPDATE referidos SET estado = 'COMISIONADO', monto_comisionado = ?, fecha_comision = ?
                WHERE id = ?
            """, (comision, datetime.now().isoformat(), referido_id))
            self.conn.commit()
            
            logger.info(f"Comisión generada - ID: {comision_id} - Monto: {comision}")
            return comision_id
        except Exception as e:
            logger.error(f"Error al generar comisión: {e}")
            raise
            
    def marcar_comision_pagada(self, comision_id: int, metodo_pago: str, referencia: str = None) -> bool:
        """
        Marca una comisión como pagada.
        
        Args:
            comision_id: ID de la comisión
            metodo_pago: Método de pago
            referencia: Referencia del pago
            
        Returns:
            True si se marcó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE comisiones
                SET estado = 'PAGADA', fecha_pago = ?, metodo_pago = ?, referencia = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), metodo_pago, referencia, comision_id))
            
            self.conn.commit()
            logger.info(f"Comisión {comision_id} marcada como pagada")
            return True
        except Exception as e:
            logger.error(f"Error al marcar comisión como pagada: {e}")
            return False
            
    def obtener_acuerdo(self, acuerdo_id: int) -> Optional[Dict]:
        """
        Obtiene información de un acuerdo.
        
        Args:
            acuerdo_id: ID del acuerdo
            
        Returns:
            Diccionario con información o None
        """
        try:
            self.cursor.execute("""
                SELECT * FROM acuerdos_propfirm WHERE id = ?
            """, (acuerdo_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'propfirm': result[1], 'tipo_acuerdo': result[2],
                    'comision_porcentaje': result[3], 'comision_fija': result[4],
                    'cupon_codigo': result[5], 'cupon_descuento': result[6],
                    'cupon_usos': result[7], 'cupon_max_usos': result[8],
                    'estado': result[9], 'fecha_inicio': result[10], 'fecha_fin': result[11],
                    'condiciones': result[12], 'observaciones': result[13]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener acuerdo: {e}")
            return None
            
    def obtener_acuerdos_propfirm(self, propfirm: str) -> List[Dict]:
        """
        Obtiene todos los acuerdos de una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            
        Returns:
            Lista de acuerdos
        """
        try:
            self.cursor.execute("""
                SELECT * FROM acuerdos_propfirm WHERE propfirm = ? ORDER BY fecha_inicio DESC
            """, (propfirm,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'propfirm': r[1], 'tipo_acuerdo': r[2],
                'comision_porcentaje': r[3], 'comision_fija': r[4],
                'cupon_codigo': r[5], 'cupon_descuento': r[6],
                'cupon_usos': r[7], 'cupon_max_usos': r[8],
                'estado': r[9], 'fecha_inicio': r[10], 'fecha_fin': r[11],
                'condiciones': r[12], 'observaciones': r[13]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener acuerdos de propfirm: {e}")
            return []
            
    def obtener_todos_acuerdos(self, estado: str = None) -> List[Dict]:
        """
        Obtiene todos los acuerdos, opcionalmente filtrados por estado.
        
        Args:
            estado: Estado para filtrar (opcional)
            
        Returns:
            Lista de acuerdos
        """
        try:
            if estado:
                self.cursor.execute("""
                    SELECT * FROM acuerdos_propfirm WHERE estado = ? ORDER BY fecha_inicio DESC
                """, (estado,))
            else:
                self.cursor.execute("""
                    SELECT * FROM acuerdos_propfirm ORDER BY fecha_inicio DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'propfirm': r[1], 'tipo_acuerdo': r[2],
                'comision_porcentaje': r[3], 'comision_fija': r[4],
                'cupon_codigo': r[5], 'cupon_descuento': r[6],
                'cupon_usos': r[7], 'cupon_max_usos': r[8],
                'estado': r[9], 'fecha_inicio': r[10], 'fecha_fin': r[11],
                'condiciones': r[12], 'observaciones': r[13]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener todos los acuerdos: {e}")
            return []
            
    def obtener_referidos_acuerdo(self, acuerdo_id: int) -> List[Dict]:
        """
        Obtiene todos los referidos de un acuerdo.
        
        Args:
            acuerdo_id: ID del acuerdo
            
        Returns:
            Lista de referidos
        """
        try:
            self.cursor.execute("""
                SELECT * FROM referidos WHERE acuerdo_id = ? ORDER BY fecha_registro DESC
            """, (acuerdo_id,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'acuerdo_id': r[1], 'referido_id': r[2],
                'referido_nombre': r[3], 'fecha_registro': r[4],
                'estado': r[5], 'monto_comisionado': r[6], 'fecha_comision': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener referidos: {e}")
            return []
            
    def obtener_comisiones(self, acuerdo_id: int = None, estado: str = None) -> List[Dict]:
        """
        Obtiene comisiones, opcionalmente filtradas.
        
        Args:
            acuerdo_id: ID del acuerdo (opcional)
            estado: Estado para filtrar (opcional)
            
        Returns:
            Lista de comisiones
        """
        try:
            if acuerdo_id and estado:
                self.cursor.execute("""
                    SELECT * FROM comisiones WHERE acuerdo_id = ? AND estado = ?
                    ORDER BY fecha_generacion DESC
                """, (acuerdo_id, estado))
            elif acuerdo_id:
                self.cursor.execute("""
                    SELECT * FROM comisiones WHERE acuerdo_id = ? ORDER BY fecha_generacion DESC
                """, (acuerdo_id,))
            elif estado:
                self.cursor.execute("""
                    SELECT * FROM comisiones WHERE estado = ? ORDER BY fecha_generacion DESC
                """, (estado,))
            else:
                self.cursor.execute("""
                    SELECT * FROM comisiones ORDER BY fecha_generacion DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'acuerdo_id': r[1], 'referido_id': r[2],
                'monto': r[3], 'porcentaje': r[4], 'fecha_generacion': r[5],
                'fecha_pago': r[6], 'estado': r[7], 'metodo_pago': r[8], 'referencia': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener comisiones: {e}")
            return []
            
    def obtener_resumen_comisiones(self, acuerdo_id: int = None) -> Dict:
        """
        Obtiene un resumen de comisiones.
        
        Args:
            acuerdo_id: ID del acuerdo (opcional)
            
        Returns:
            Diccionario con resumen
        """
        try:
            if acuerdo_id:
                self.cursor.execute("""
                    SELECT estado, COUNT(*), SUM(monto) FROM comisiones
                    WHERE acuerdo_id = ? GROUP BY estado
                """, (acuerdo_id,))
            else:
                self.cursor.execute("""
                    SELECT estado, COUNT(*), SUM(monto) FROM comisiones GROUP BY estado
                """)
                
            resultados = self.cursor.fetchall()
            
            resumen = {
                'pendientes': 0,
                'pendientes_monto': 0,
                'pagadas': 0,
                'pagadas_monto': 0,
                'total': 0,
                'total_monto': 0
            }
            
            for estado, count, monto in resultados:
                if estado == 'PENDIENTE':
                    resumen['pendientes'] = count
                    resumen['pendientes_monto'] = monto or 0
                elif estado == 'PAGADA':
                    resumen['pagadas'] = count
                    resumen['pagadas_monto'] = monto or 0
                    
                resumen['total'] += count
                resumen['total_monto'] += monto or 0
                
            return resumen
        except Exception as e:
            logger.error(f"Error al obtener resumen de comisiones: {e}")
            return {}
            
    def suspender_acuerdo(self, acuerdo_id: int, motivo: str) -> bool:
        """
        Suspende un acuerdo de afiliación.
        
        Args:
            acuerdo_id: ID del acuerdo
            motivo: Motivo de la suspensión
            
        Returns:
            True si se suspendió correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE acuerdos_propfirm SET estado = 'SUSPENDIDO', observaciones = ?
                WHERE id = ?
            """, (motivo, acuerdo_id))
            self.conn.commit()
            logger.info(f"Acuerdo {acuerdo_id} suspendido - Motivo: {motivo}")
            return True
        except Exception as e:
            logger.error(f"Error al suspender acuerdo: {e}")
            return False
            
    def reactivar_acuerdo(self, acuerdo_id: int) -> bool:
        """
        Reactiva un acuerdo suspendido.
        
        Args:
            acuerdo_id: ID del acuerdo
            
        Returns:
            True si se reactivó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE acuerdos_propfirm SET estado = 'ACTIVO', observaciones = NULL
                WHERE id = ?
            """, (acuerdo_id,))
            self.conn.commit()
            logger.info(f"Acuerdo {acuerdo_id} reactivado")
            return True
        except Exception as e:
            logger.error(f"Error al reactivar acuerdo: {e}")
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
    
    agente = AgenteAfiliaciones()
    
    # Ejemplo: registrar acuerdo
    acuerdo_id = agente.registrar_acuerdo(
        propfirm="FTMO",
        tipo_acuerdo="referral",
        comision_porcentaje=10,
        comision_fija=0,
        cupon_codigo="QHFTMO10",
        cupon_descuento=10,
        cupon_max_usos=100
    )
    
    print(f"Acuerdo registrado - ID: {acuerdo_id}")
    
    # Ejemplo: registrar referido
    referido_id = agente.registrar_referido(
        acuerdo_id=acuerdo_id,
        referido_id="CLI001",
        referido_nombre="Juan Pérez"
    )
    
    print(f"Referido registrado - ID: {referido_id}")
    
    # Ejemplo: usar cupón
    descuento = agente.usar_cupon("QHFTMO10", "CLI002", "María García")
    print(f"Descuento aplicado: {descuento}")
    
    # Ejemplo: generar comisión
    comision_id = agente.generar_comision(acuerdo_id, referido_id, 500)
    print(f"Comisión generada - ID: {comision_id}")
    
    # Ejemplo: obtener resumen
    resumen = agente.obtener_resumen_comisiones(acuerdo_id)
    print(f"Resumen comisiones: {resumen}")
    
    agente.cerrar()

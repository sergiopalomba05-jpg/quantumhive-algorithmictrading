"""
Agente Cobro Fondeo - D2: Gestión de Fondeo y Challenges
Cobra cuando PropFirm paga

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona el cobro de comisiones cuando las propfirms realizan pagos,
             monitorea pagos pendientes, registra transacciones y alertas.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

class AgenteCobroFondeo:
    """Gestiona el cobro de comisiones de propfirms."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de cobro de fondeo.
        
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
                CREATE TABLE IF NOT EXISTS pagos_propfirm (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    cliente_nombre TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    cuenta_fondeada TEXT NOT NULL,
                    monto_esperado REAL NOT NULL,
                    monto_recibido REAL DEFAULT 0,
                    moneda TEXT DEFAULT 'USD',
                    fecha_esperada DATETIME NOT NULL,
                    fecha_recibida DATETIME,
                    estado TEXT NOT NULL,
                    metodo_pago TEXT,
                    referencia TEXT,
                    comprobante_url TEXT,
                    observaciones TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS alertas_cobro (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pago_propfirm_id INTEGER NOT NULL,
                    tipo_alerta TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    leida BOOLEAN DEFAULT FALSE,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pago_propfirm_id) REFERENCES pagos_propfirm(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_cobros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pago_propfirm_id INTEGER NOT NULL,
                    accion TEXT NOT NULL,
                    detalle TEXT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pago_propfirm_id) REFERENCES pagos_propfirm(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_pago_esperado(self, cliente_id: str, cliente_nombre: str, propfirm: str,
                                cuenta_fondeada: str, monto_esperado: float,
                                fecha_esperada: datetime, moneda: str = "USD") -> int:
        """
        Registra un pago esperado de propfirm.
        
        Args:
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente
            propfirm: Nombre de la propfirm
            cuenta_fondeada: Número de cuenta fondeada
            monto_esperado: Monto esperado
            fecha_esperada: Fecha esperada del pago
            moneda: Moneda del pago
            
        Returns:
            ID del pago registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO pagos_propfirm
                (cliente_id, cliente_nombre, propfirm, cuenta_fondeada, monto_esperado,
                 moneda, fecha_esperada, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, cliente_nombre, propfirm, cuenta_fondeada, monto_esperado,
                  moneda, fecha_esperada.isoformat(), 'PENDIENTE'))
            
            self.conn.commit()
            pago_id = self.cursor.lastrowid
            logger.info(f"Pago esperado registrado - ID: {pago_id} - Propfirm: {propfirm}")
            
            # Programar alerta para fecha esperada
            self._crear_alerta(pago_id, 'FECHA_ESPERADA', 
                              f"Pago esperado de {propfirm} para {fecha_esperada}")
            
            return pago_id
        except Exception as e:
            logger.error(f"Error al registrar pago esperado: {e}")
            raise
            
    def registrar_pago_recibido(self, pago_id: int, monto_recibido: float, 
                               metodo_pago: str, referencia: str = None,
                               comprobante_url: str = None) -> bool:
        """
        Registra que se recibió un pago de propfirm.
        
        Args:
            pago_id: ID del pago
            monto_recibido: Monto recibido
            metodo_pago: Método de pago
            referencia: Referencia del pago
            comprobante_url: URL del comprobante
            
        Returns:
            True si se registró correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE pagos_propfirm
                SET monto_recibido = ?, fecha_recibida = ?, estado = ?,
                    metodo_pago = ?, referencia = ?, comprobante_url = ?
                WHERE id = ?
            """, (monto_recibido, datetime.now().isoformat(), 'RECIBIDO',
                  metodo_pago, referencia, comprobante_url, pago_id))
            
            self.conn.commit()
            
            # Registrar en histórico
            self._registrar_historico(pago_id, 'PAGO_RECIBIDO',
                                    f"Monto: {monto_recibido} - Método: {metodo_pago}")
            
            # Crear alerta
            self._crear_alerta(pago_id, 'PAGO_RECIBIDO',
                            f"Pago recibido de propfirm - Monto: {monto_recibido}")
            
            logger.info(f"Pago recibido registrado - ID: {pago_id} - Monto: {monto_recibido}")
            return True
        except Exception as e:
            logger.error(f"Error al registrar pago recibido: {e}")
            return False
            
    def verificar_pagos_pendientes(self) -> List[Dict]:
        """
        Verifica pagos pendientes y alerta si vencieron.
        
        Returns:
            Lista de pagos pendientes
        """
        try:
            hoy = datetime.now()
            
            self.cursor.execute("""
                SELECT * FROM pagos_propfirm
                WHERE estado = 'PENDIENTE' AND fecha_esperada < ?
                ORDER BY fecha_esperada ASC
            """, (hoy.isoformat(),))
            
            results = self.cursor.fetchall()
            pagos_vencidos = []
            
            for r in results:
                pago = {
                    'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2],
                    'propfirm': r[3], 'cuenta_fondeada': r[4], 'monto_esperado': r[5],
                    'monto_recibido': r[6], 'moneda': r[7], 'fecha_esperada': r[8],
                    'fecha_recibida': r[9], 'estado': r[10], 'metodo_pago': r[11],
                    'referencia': r[12], 'comprobante_url': r[13], 'observaciones': r[14]
                }
                pagos_vencidos.append(pago)
                
                # Crear alerta de vencimiento
                self._crear_alerta(pago['id'], 'VENCIDO',
                                f"Pago vencido de {pago['propfirm']} - {pago['monto_esperado']} {pago['moneda']}")
                
            return pagos_vencidos
        except Exception as e:
            logger.error(f"Error al verificar pagos pendientes: {e}")
            return []
            
    def obtener_pago(self, pago_id: int) -> Optional[Dict]:
        """
        Obtiene información de un pago.
        
        Args:
            pago_id: ID del pago
            
        Returns:
            Diccionario con información del pago o None
        """
        try:
            self.cursor.execute("""
                SELECT * FROM pagos_propfirm WHERE id = ?
            """, (pago_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'cliente_id': result[1], 'cliente_nombre': result[2],
                    'propfirm': result[3], 'cuenta_fondeada': result[4], 'monto_esperado': result[5],
                    'monto_recibido': result[6], 'moneda': result[7], 'fecha_esperada': result[8],
                    'fecha_recibida': result[9], 'estado': result[10], 'metodo_pago': result[11],
                    'referencia': result[12], 'comprobante_url': result[13], 'observaciones': result[14]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener pago: {e}")
            return None
            
    def obtener_pagos_cliente(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene todos los pagos de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de pagos del cliente
        """
        try:
            self.cursor.execute("""
                SELECT * FROM pagos_propfirm
                WHERE cliente_id = ?
                ORDER BY fecha_esperada DESC
            """, (cliente_id,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2],
                'propfirm': r[3], 'cuenta_fondeada': r[4], 'monto_esperado': r[5],
                'monto_recibido': r[6], 'moneda': r[7], 'fecha_esperada': r[8],
                'fecha_recibida': r[9], 'estado': r[10], 'metodo_pago': r[11],
                'referencia': r[12], 'comprobante_url': r[13], 'observaciones': r[14]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener pagos del cliente: {e}")
            return []
            
    def obtener_pagos_propfirm(self, propfirm: str) -> List[Dict]:
        """
        Obtiene todos los pagos de una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            
        Returns:
            Lista de pagos de la propfirm
        """
        try:
            self.cursor.execute("""
                SELECT * FROM pagos_propfirm
                WHERE propfirm = ?
                ORDER BY fecha_esperada DESC
            """, (propfirm,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2],
                'propfirm': r[3], 'cuenta_fondeada': r[4], 'monto_esperado': r[5],
                'monto_recibido': r[6], 'moneda': r[7], 'fecha_esperada': r[8],
                'fecha_recibida': r[9], 'estado': r[10], 'metodo_pago': r[11],
                'referencia': r[12], 'comprobante_url': r[13], 'observaciones': r[14]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener pagos de propfirm: {e}")
            return []
            
    def obtener_resumen_mes(self, mes: int, anio: int) -> Dict:
        """
        Obtiene un resumen de cobros de un mes.
        
        Args:
            mes: Mes (1-12)
            anio: Año
            
        Returns:
            Diccionario con resumen
        """
        try:
            fecha_inicio = datetime(anio, mes, 1)
            if mes == 12:
                fecha_fin = datetime(anio + 1, 1, 1)
            else:
                fecha_fin = datetime(anio, mes + 1, 1)
                
            self.cursor.execute("""
                SELECT estado, SUM(monto_esperado), SUM(monto_recibido), COUNT(*)
                FROM pagos_propfirm
                WHERE fecha_esperada >= ? AND fecha_esperada < ?
                GROUP BY estado
            """, (fecha_inicio.isoformat(), fecha_fin.isoformat()))
            
            resultados = self.cursor.fetchall()
            
            resumen = {
                'mes': mes,
                'anio': anio,
                'total_esperado': 0,
                'total_recibido': 0,
                'pendientes': 0,
                'recibidos': 0,
                'vencidos': 0
            }
            
            for estado, esperado, recibido, count in resultados:
                if estado == 'PENDIENTE':
                    resumen['pendientes'] = count
                    resumen['total_esperado'] += esperado or 0
                elif estado == 'RECIBIDO':
                    resumen['recibidos'] = count
                    resumen['total_recibido'] += recibido or 0
                    resumen['total_esperado'] += esperado or 0
                    
            return resumen
        except Exception as e:
            logger.error(f"Error al obtener resumen del mes: {e}")
            return {}
            
    def _crear_alerta(self, pago_propfirm_id: int, tipo_alerta: str, mensaje: str):
        """Crea una alerta para un pago."""
        try:
            self.cursor.execute("""
                INSERT INTO alertas_cobro (pago_propfirm_id, tipo_alerta, mensaje)
                VALUES (?, ?, ?)
            """, (pago_propfirm_id, tipo_alerta, mensaje))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear alerta: {e}")
            
    def _registrar_historico(self, pago_propfirm_id: int, accion: str, detalle: str = None):
        """Registra una acción en el histórico."""
        try:
            self.cursor.execute("""
                INSERT INTO historico_cobros (pago_propfirm_id, accion, detalle)
                VALUES (?, ?, ?)
            """, (pago_propfirm_id, accion, detalle))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar histórico: {e}")
            
    def obtener_alertas(self, pago_id: int = None, no_leidas: bool = False) -> List[Dict]:
        """
        Obtiene alertas de cobro.
        
        Args:
            pago_id: ID del pago (opcional)
            no_leidas: Solo alertas no leídas
            
        Returns:
            Lista de alertas
        """
        try:
            if pago_id and no_leidas:
                self.cursor.execute("""
                    SELECT * FROM alertas_cobro
                    WHERE pago_propfirm_id = ? AND leida = FALSE
                    ORDER BY fecha DESC
                """, (pago_id,))
            elif pago_id:
                self.cursor.execute("""
                    SELECT * FROM alertas_cobro
                    WHERE pago_propfirm_id = ?
                    ORDER BY fecha DESC
                """, (pago_id,))
            elif no_leidas:
                self.cursor.execute("""
                    SELECT * FROM alertas_cobro
                    WHERE leida = FALSE
                    ORDER BY fecha DESC
                """)
            else:
                self.cursor.execute("""
                    SELECT * FROM alertas_cobro
                    ORDER BY fecha DESC
                """)
                
            results = self.cursor.fetchall()
            return [{'id': r[0], 'pago_propfirm_id': r[1], 'tipo_alerta': r[2],
                    'mensaje': r[3], 'leida': r[4], 'fecha': r[5]} for r in results]
        except Exception as e:
            logger.error(f"Error al obtener alertas: {e}")
            return []
            
    def marcar_alerta_leida(self, alerta_id: int) -> bool:
        """
        Marca una alerta como leída.
        
        Args:
            alerta_id: ID de la alerta
            
        Returns:
            True si se marcó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE alertas_cobro SET leida = TRUE WHERE id = ?
            """, (alerta_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al marcar alerta como leída: {e}")
            return False
            
    def actualizar_observaciones(self, pago_id: int, observaciones: str) -> bool:
        """
        Actualiza las observaciones de un pago.
        
        Args:
            pago_id: ID del pago
            observaciones: Nuevas observaciones
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE pagos_propfirm SET observaciones = ? WHERE id = ?
            """, (observaciones, pago_id))
            self.conn.commit()
            
            self._registrar_historico(pago_id, 'OBSERVACIONES_ACTUALIZADAS', observaciones)
            return True
        except Exception as e:
            logger.error(f"Error al actualizar observaciones: {e}")
            return False
            
    def obtener_historico_pago(self, pago_id: int) -> List[Dict]:
        """
        Obtiene el histórico de acciones de un pago.
        
        Args:
            pago_id: ID del pago
            
        Returns:
            Lista de acciones históricas
        """
        try:
            self.cursor.execute("""
                SELECT * FROM historico_cobros
                WHERE pago_propfirm_id = ?
                ORDER BY fecha DESC
            """, (pago_id,))
            
            results = self.cursor.fetchall()
            return [{'id': r[0], 'pago_propfirm_id': r[1], 'accion': r[2],
                    'detalle': r[3], 'fecha': r[4]} for r in results]
        except Exception as e:
            logger.error(f"Error al obtener histórico: {e}")
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
    
    agente = AgenteCobroFondeo()
    
    # Ejemplo: registrar pago esperado
    pago_id = agente.registrar_pago_esperado(
        cliente_id="CLI001",
        cliente_nombre="Juan Pérez",
        propfirm="FTMO",
        cuenta_fondeada="789012",
        monto_esperado=2000,
        fecha_esperada=datetime.now() + timedelta(days=15),
        moneda="USD"
    )
    
    print(f"Pago esperado registrado - ID: {pago_id}")
    
    # Ejemplo: registrar pago recibido
    agente.registrar_pago_recibido(
        pago_id=pago_id,
        monto_recibido=2000,
        metodo_pago="Crypto",
        referencia="TX123456"
    )
    
    # Ejemplo: verificar pagos pendientes
    pendientes = agente.verificar_pagos_pendientes()
    print(f"Pagos pendientes vencidos: {len(pendientes)}")
    
    # Ejemplo: obtener resumen del mes
    resumen = agente.obtener_resumen_mes(5, 2026)
    print(f"Resumen mes: {resumen}")
    
    agente.cerrar()

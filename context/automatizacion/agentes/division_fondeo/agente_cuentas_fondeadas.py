"""
Agente Cuentas Fondeadas - D2: Gestión de Fondeo y Challenges
Registro balance, DD, cobro QH

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Registra y monitorea cuentas fondeadas, tracking de balance,
             drawdown, y gestiona el cobro de comisiones QuantumHive.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class AgenteCuentasFondeadas:
    """Registra y monitorea cuentas fondeadas."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de cuentas fondeadas.
        
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
                CREATE TABLE IF NOT EXISTS cuentas_fondeadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    cliente_nombre TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    cuenta_fondeada TEXT NOT NULL,
                    tipo_cuenta TEXT NOT NULL,
                    balance_inicial REAL NOT NULL,
                    balance_actual REAL NOT NULL,
                    equity REAL NOT NULL,
                    profit_total REAL NOT NULL,
                    drawdown_actual REAL NOT NULL,
                    drawdown_max REAL NOT NULL,
                    split_porcentaje REAL NOT NULL,
                    split_qh REAL NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_fondeo DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ultimo_pago_qh DATETIME,
                    proximo_pago_qh DATETIME,
                    observaciones TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta_fondeada TEXT NOT NULL,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    profit REAL NOT NULL,
                    drawdown REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagos_qh (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta_fondeada TEXT NOT NULL,
                    cliente_id TEXT NOT NULL,
                    monto REAL NOT NULL,
                    periodo_inicio DATETIME NOT NULL,
                    periodo_fin DATETIME NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_pago DATETIME,
                    metodo_pago TEXT,
                    comprobante TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_cuenta_fondeada(self, cliente_id: str, cliente_nombre: str, propfirm: str,
                                  cuenta_fondeada: str, tipo_cuenta: str, balance_inicial: float,
                                  split_porcentaje: float) -> int:
        """
        Registra una nueva cuenta fondeada.
        
        Args:
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente
            propfirm: Nombre de la propfirm
            cuenta_fondeada: Número de cuenta fondeada
            tipo_cuenta: Tipo de cuenta (ej: 10k, 50k, 100k)
            balance_inicial: Balance inicial
            split_porcentaje: Porcentaje de split para QH
            
        Returns:
            ID de la cuenta registrada
        """
        try:
            split_qh = balance_inicial * (split_porcentaje / 100)
            
            self.cursor.execute("""
                INSERT INTO cuentas_fondeadas
                (cliente_id, cliente_nombre, propfirm, cuenta_fondeada, tipo_cuenta,
                 balance_inicial, balance_actual, equity, profit_total, drawdown_actual,
                 drawdown_max, split_porcentaje, split_qh, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, cliente_nombre, propfirm, cuenta_fondeada, tipo_cuenta,
                  balance_inicial, balance_inicial, balance_inicial, 0, 0, 0,
                  split_porcentaje, split_qh, 'ACTIVA'))
            
            self.conn.commit()
            cuenta_id = self.cursor.lastrowid
            logger.info(f"Cuenta fondeada registrada - ID: {cuenta_id} - Cliente: {cliente_nombre}")
            return cuenta_id
        except Exception as e:
            logger.error(f"Error al registrar cuenta fondeada: {e}")
            raise
            
    def actualizar_balance(self, cuenta_fondeada: str, balance: float, equity: float) -> bool:
        """
        Actualiza el balance y equity de una cuenta fondeada.
        
        Args:
            cuenta_fondeada: Número de cuenta
            balance: Balance actual
            equity: Equity actual
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Obtener datos actuales
            self.cursor.execute("""
                SELECT balance_inicial FROM cuentas_fondeadas WHERE cuenta_fondeada = ?
            """, (cuenta_fondeada,))
            result = self.cursor.fetchone()
            
            if not result:
                logger.error(f"Cuenta {cuenta_fondeada} no encontrada")
                return False
                
            balance_inicial = result[0]
            profit_total = balance - balance_inicial
            drawdown_actual = balance_inicial - equity if equity < balance_inicial else 0
            
            # Actualizar cuenta
            self.cursor.execute("""
                UPDATE cuentas_fondeadas
                SET balance_actual = ?, equity = ?, profit_total = ?, drawdown_actual = ?
                WHERE cuenta_fondeada = ?
            """, (balance, equity, profit_total, drawdown_actual, cuenta_fondeada))
            
            # Actualizar máximo drawdown si es necesario
            self._actualizar_max_drawdown(cuenta_fondeada, drawdown_actual)
            
            self.conn.commit()
            
            # Registrar en histórico
            self._registrar_historico(cuenta_fondeada, balance, equity, profit_total, drawdown_actual)
            
            return True
        except Exception as e:
            logger.error(f"Error al actualizar balance: {e}")
            return False
            
    def _actualizar_max_drawdown(self, cuenta_fondeada: str, drawdown_actual: float):
        """Actualiza el máximo drawdown si el actual es mayor."""
        try:
            self.cursor.execute("""
                SELECT drawdown_max FROM cuentas_fondeadas WHERE cuenta_fondeada = ?
            """, (cuenta_fondeada,))
            result = self.cursor.fetchone()
            
            if result and drawdown_actual > result[0]:
                self.cursor.execute("""
                    UPDATE cuentas_fondeadas SET drawdown_max = ? WHERE cuenta_fondeada = ?
                """, (drawdown_actual, cuenta_fondeada))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error al actualizar max drawdown: {e}")
            
    def _registrar_historico(self, cuenta_fondeada: str, balance: float, equity: float,
                           profit: float, drawdown: float):
        """Registra en el histórico de balance."""
        try:
            self.cursor.execute("""
                INSERT INTO historico_balance (cuenta_fondeada, balance, equity, profit, drawdown)
                VALUES (?, ?, ?, ?, ?)
            """, (cuenta_fondeada, balance, equity, profit, drawdown))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar histórico: {e}")
            
    def obtener_cuenta(self, cuenta_fondeada: str) -> Optional[Dict]:
        """
        Obtiene información de una cuenta fondeada.
        
        Args:
            cuenta_fondeada: Número de cuenta
            
        Returns:
            Diccionario con información o None
        """
        try:
            self.cursor.execute("""
                SELECT * FROM cuentas_fondeadas WHERE cuenta_fondeada = ?
            """, (cuenta_fondeada,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'cliente_id': result[1],
                    'cliente_nombre': result[2],
                    'propfirm': result[3],
                    'cuenta_fondeada': result[4],
                    'tipo_cuenta': result[5],
                    'balance_inicial': result[6],
                    'balance_actual': result[7],
                    'equity': result[8],
                    'profit_total': result[9],
                    'drawdown_actual': result[10],
                    'drawdown_max': result[11],
                    'split_porcentaje': result[12],
                    'split_qh': result[13],
                    'estado': result[14],
                    'fecha_fondeo': result[15],
                    'ultimo_pago_qh': result[16],
                    'proximo_pago_qh': result[17],
                    'observaciones': result[18]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener cuenta: {e}")
            return None
            
    def obtener_cuentas_cliente(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene todas las cuentas fondeadas de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de cuentas del cliente
        """
        try:
            self.cursor.execute("""
                SELECT * FROM cuentas_fondeadas WHERE cliente_id = ? ORDER BY fecha_fondeo DESC
            """, (cliente_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2], 'propfirm': r[3],
                'cuenta_fondeada': r[4], 'tipo_cuenta': r[5], 'balance_inicial': r[6],
                'balance_actual': r[7], 'equity': r[8], 'profit_total': r[9],
                'drawdown_actual': r[10], 'drawdown_max': r[11], 'split_porcentaje': r[12],
                'split_qh': r[13], 'estado': r[14], 'fecha_fondeo': r[15],
                'ultimo_pago_qh': r[16], 'proximo_pago_qh': r[17], 'observaciones': r[18]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener cuentas del cliente: {e}")
            return []
            
    def obtener_todas_cuentas(self, estado: str = None) -> List[Dict]:
        """
        Obtiene todas las cuentas fondeadas, opcionalmente filtradas por estado.
        
        Args:
            estado: Estado para filtrar (opcional)
            
        Returns:
            Lista de cuentas
        """
        try:
            if estado:
                self.cursor.execute("""
                    SELECT * FROM cuentas_fondeadas WHERE estado = ? ORDER BY fecha_fondeo DESC
                """, (estado,))
            else:
                self.cursor.execute("""
                    SELECT * FROM cuentas_fondeadas ORDER BY fecha_fondeo DESC
                """)
                
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2], 'propfirm': r[3],
                'cuenta_fondeada': r[4], 'tipo_cuenta': r[5], 'balance_inicial': r[6],
                'balance_actual': r[7], 'equity': r[8], 'profit_total': r[9],
                'drawdown_actual': r[10], 'drawdown_max': r[11], 'split_porcentaje': r[12],
                'split_qh': r[13], 'estado': r[14], 'fecha_fondeo': r[15],
                'ultimo_pago_qh': r[16], 'proximo_pago_qh': r[17], 'observaciones': r[18]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener todas las cuentas: {e}")
            return []
            
    def obtener_historico(self, cuenta_fondeada: str, dias: int = 30) -> List[Dict]:
        """
        Obtiene el histórico de balance de una cuenta.
        
        Args:
            cuenta_fondeada: Número de cuenta
            dias: Días de histórico
            
        Returns:
            Lista de registros históricos
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT * FROM historico_balance
                WHERE cuenta_fondeada = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (cuenta_fondeada, fecha_limite.isoformat()))
            
            results = self.cursor.fetchall()
            return [{'id': r[0], 'cuenta_fondeada': r[1], 'balance': r[2],
                    'equity': r[3], 'profit': r[4], 'drawdown': r[5],
                    'timestamp': r[6]} for r in results]
        except Exception as e:
            logger.error(f"Error al obtener histórico: {e}")
            return []
            
    def calcular_split_qh(self, cuenta_fondeada: str, periodo_inicio: datetime,
                         periodo_fin: datetime) -> float:
        """
        Calcula el split de QuantumHive para un período.
        
        Args:
            cuenta_fondeada: Número de cuenta
            periodo_inicio: Inicio del período
            periodo_fin: Fin del período
            
        Returns:
            Monto del split QH
        """
        try:
            cuenta = self.obtener_cuenta(cuenta_fondeada)
            if not cuenta:
                return 0
                
            # Obtener profit del período
            self.cursor.execute("""
                SELECT profit FROM historico_balance
                WHERE cuenta_fondeada = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (cuenta_fondeada, periodo_inicio.isoformat(), periodo_fin.isoformat()))
            
            resultados = self.cursor.fetchall()
            
            if not resultados:
                return 0
                
            profit_inicio = resultados[0][0] if resultados else 0
            profit_fin = resultados[-1][0] if resultados else 0
            profit_periodo = profit_fin - profit_inicio
            
            # Calcular split QH
            split_qh = profit_periodo * (cuenta['split_porcentaje'] / 100)
            
            return max(0, split_qh)  # No negativo
        except Exception as e:
            logger.error(f"Error al calcular split QH: {e}")
            return 0
            
    def registrar_pago_qh(self, cuenta_fondeada: str, cliente_id: str, monto: float,
                        periodo_inicio: datetime, periodo_fin: datetime,
                        metodo_pago: str = None, comprobante: str = None) -> int:
        """
        Registra un pago de split QuantumHive.
        
        Args:
            cuenta_fondeada: Número de cuenta
            cliente_id: ID del cliente
            monto: Monto del pago
            periodo_inicio: Inicio del período
            periodo_fin: Fin del período
            metodo_pago: Método de pago
            comprobante: Comprobante del pago
            
        Returns:
            ID del pago registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO pagos_qh
                (cuenta_fondeada, cliente_id, monto, periodo_inicio, periodo_fin,
                 estado, fecha_pago, metodo_pago, comprobante)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cuenta_fondeada, cliente_id, monto, periodo_inicio.isoformat(),
                  periodo_fin.isoformat(), 'PAGADO', datetime.now().isoformat(),
                  metodo_pago, comprobante))
            
            self.conn.commit()
            pago_id = self.cursor.lastrowid
            
            # Actualizar cuenta con último pago
            self.cursor.execute("""
                UPDATE cuentas_fondeadas
                SET ultimo_pago_qh = ?, proximo_pago_qh = ?
                WHERE cuenta_fondeada = ?
            """, (datetime.now().isoformat(), 
                  (datetime.now() + timedelta(days=30)).isoformat(),
                  cuenta_fondeada))
            self.conn.commit()
            
            logger.info(f"Pago QH registrado - ID: {pago_id} - Monto: {monto}")
            return pago_id
        except Exception as e:
            logger.error(f"Error al registrar pago QH: {e}")
            raise
            
    def obtener_pagos(self, cuenta_fondeada: str = None) -> List[Dict]:
        """
        Obtiene pagos QH, opcionalmente filtrados por cuenta.
        
        Args:
            cuenta_fondeada: Número de cuenta (opcional)
            
        Returns:
            Lista de pagos
        """
        try:
            if cuenta_fondeada:
                self.cursor.execute("""
                    SELECT * FROM pagos_qh WHERE cuenta_fondeada = ? ORDER BY timestamp DESC
                """, (cuenta_fondeada,))
            else:
                self.cursor.execute("""
                    SELECT * FROM pagos_qh ORDER BY timestamp DESC
                """)
                
            results = self.cursor.fetchall()
            return [{'id': r[0], 'cuenta_fondeada': r[1], 'cliente_id': r[2],
                    'monto': r[3], 'periodo_inicio': r[4], 'periodo_fin': r[5],
                    'estado': r[6], 'fecha_pago': r[7], 'metodo_pago': r[8],
                    'comprobante': r[9], 'timestamp': r[10]} for r in results]
        except Exception as e:
            logger.error(f"Error al obtener pagos: {e}")
            return []
            
    def suspender_cuenta(self, cuenta_fondeada: str, motivo: str) -> bool:
        """
        Suspende una cuenta fondeada.
        
        Args:
            cuenta_fondeada: Número de cuenta
            motivo: Motivo de la suspensión
            
        Returns:
            True si se suspendió correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE cuentas_fondeadas
                SET estado = 'SUSPENDIDA', observaciones = ?
                WHERE cuenta_fondeada = ?
            """, (motivo, cuenta_fondeada))
            self.conn.commit()
            logger.info(f"Cuenta {cuenta_fondeada} suspendida - Motivo: {motivo}")
            return True
        except Exception as e:
            logger.error(f"Error al suspender cuenta: {e}")
            return False
            
    def reactivar_cuenta(self, cuenta_fondeada: str) -> bool:
        """
        Reactiva una cuenta suspendida.
        
        Args:
            cuenta_fondeada: Número de cuenta
            
        Returns:
            True si se reactivó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE cuentas_fondeadas
                SET estado = 'ACTIVA', observaciones = NULL
                WHERE cuenta_fondeada = ?
            """, (cuenta_fondeada,))
            self.conn.commit()
            logger.info(f"Cuenta {cuenta_fondeada} reactivada")
            return True
        except Exception as e:
            logger.error(f"Error al reactivar cuenta: {e}")
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
    
    agente = AgenteCuentasFondeadas()
    
    # Ejemplo: registrar cuenta fondeada
    cuenta_id = agente.registrar_cuenta_fondeada(
        cliente_id="CLI001",
        cliente_nombre="Juan Pérez",
        propfirm="FTMO",
        cuenta_fondeada="789012",
        tipo_cuenta="10k",
        balance_inicial=10000,
        split_porcentaje=20
    )
    
    print(f"Cuenta fondeada registrada - ID: {cuenta_id}")
    
    # Ejemplo: actualizar balance
    agente.actualizar_balance("789012", 10500, 10450)
    
    # Ejemplo: obtener cuenta
    cuenta = agente.obtener_cuenta("789012")
    print(f"Cuenta: {cuenta}")
    
    # Ejemplo: obtener histórico
    historico = agente.obtener_historico("789012", dias=30)
    print(f"Registros históricos: {len(historico)}")
    
    agente.cerrar()

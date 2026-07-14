"""
Agente Monitor Drawdown - D1: Enjambre CFDs/US30
Monitorea drawdown en tiempo real, alerta límites

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Monitorea el drawdown de cuentas de trading en tiempo real,
             alerta cuando se acerca a límites críticos y puede detener trading.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class AgenteMonitorDrawdown:
    """Monitorea drawdown en tiempo real y alerta límites."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de monitoreo de drawdown.
        
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
                CREATE TABLE IF NOT EXISTS drawdown_monitor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    drawdown REAL NOT NULL,
                    drawdown_percent REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    max_drawdown_percent REAL NOT NULL,
                    alerta_nivel TEXT,
                    trading_activo BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def conectar_mt5(self, login: int, password: str, server: str) -> bool:
        """
        Conecta a MetaTrader 5.
        
        Args:
            login: Número de cuenta
            password: Contraseña
            server: Servidor
            
        Returns:
            True si la conexión fue exitosa
        """
        try:
            if not mt5.initialize():
                logger.error("Error al inicializar MT5")
                return False
                
            if not mt5.login(login, password, server):
                logger.error(f"Error al login en cuenta {login}")
                mt5.shutdown()
                return False
                
            logger.info(f"Conectado a cuenta {login}")
            return True
        except Exception as e:
            logger.error(f"Error al conectar MT5: {e}")
            return False
            
    def obtener_info_cuenta(self) -> Optional[Dict]:
        """
        Obtiene información de la cuenta actual.
        
        Returns:
            Diccionario con información de la cuenta o None
        """
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("No se pudo obtener información de la cuenta")
                return None
                
            return {
                'login': account_info.login,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'profit': account_info.profit
            }
        except Exception as e:
            logger.error(f"Error al obtener información de cuenta: {e}")
            return None
            
    def calcular_drawdown(self, balance: float, equity: float) -> Dict[str, float]:
        """
        Calcula el drawdown actual.
        
        Args:
            balance: Balance de la cuenta
            equity: Equity actual
            
        Returns:
            Diccionario con drawdown absoluto y porcentual
        """
        drawdown = balance - equity
        drawdown_percent = (drawdown / balance * 100) if balance > 0 else 0
        
        return {
            'drawdown': drawdown,
            'drawdown_percent': drawdown_percent
        }
        
    def obtener_max_drawdown(self, cuenta: str) -> Dict[str, float]:
        """
        Obtiene el máximo drawdown histórico de la cuenta.
        
        Args:
            cuenta: Número de cuenta
            
        Returns:
            Diccionario con máximo drawdown
        """
        try:
            self.cursor.execute("""
                SELECT MAX(max_drawdown), MAX(max_drawdown_percent)
                FROM drawdown_monitor
                WHERE cuenta = ?
            """, (cuenta,))
            result = self.cursor.fetchone()
            
            if result and result[0] is not None:
                return {
                    'max_drawdown': result[0],
                    'max_drawdown_percent': result[1]
                }
            return {'max_drawdown': 0, 'max_drawdown_percent': 0}
        except Exception as e:
            logger.error(f"Error al obtener max drawdown: {e}")
            return {'max_drawdown': 0, 'max_drawdown_percent': 0}
            
    def evaluar_nivel_alerta(self, drawdown_percent: float) -> str:
        """
        Evalúa el nivel de alerta según el drawdown.
        
        Args:
            drawdown_percent: Drawdown en porcentaje
            
        Returns:
            Nivel de alerta: VERDE, AMARILLO, NARANJA, ROJO, NEGRO
        """
        if drawdown_percent < 3:
            return "VERDE"
        elif drawdown_percent < 5:
            return "AMARILLO"
        elif drawdown_percent < 8:
            return "NARANJA"
        elif drawdown_percent < 10:
            return "ROJO"
        else:
            return "NEGRO"
            
    def registrar_monitoreo(self, cuenta: str, balance: float, equity: float, 
                           drawdown: float, drawdown_percent: float, 
                           max_drawdown: float, max_drawdown_percent: float,
                           alerta_nivel: str, trading_activo: bool):
        """
        Registra el monitoreo en la base de datos.
        
        Args:
            cuenta: Número de cuenta
            balance: Balance actual
            equity: Equity actual
            drawdown: Drawdown absoluto
            drawdown_percent: Drawdown en porcentaje
            max_drawdown: Máximo drawdown absoluto
            max_drawdown_percent: Máximo drawdown en porcentaje
            alerta_nivel: Nivel de alerta
            trading_activo: Si el trading está activo
        """
        try:
            self.cursor.execute("""
                INSERT INTO drawdown_monitor 
                (cuenta, balance, equity, drawdown, drawdown_percent,
                 max_drawdown, max_drawdown_percent, alerta_nivel, trading_activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cuenta, balance, equity, drawdown, drawdown_percent,
                  max_drawdown, max_drawdown_percent, alerta_nivel, trading_activo))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar monitoreo: {e}")
            
    def actualizar_max_drawdown(self, cuenta: str, drawdown: float, drawdown_percent: float):
        """
        Actualiza el máximo drawdown si el actual es mayor.
        
        Args:
            cuenta: Número de cuenta
            drawdown: Drawdown absoluto actual
            drawdown_percent: Drawdown en porcentaje actual
        """
        try:
            max_dd = self.obtener_max_drawdown(cuenta)
            
            if drawdown > max_dd['max_drawdown']:
                self.cursor.execute("""
                    UPDATE drawdown_monitor
                    SET max_drawdown = ?, max_drawdown_percent = ?
                    WHERE cuenta = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (drawdown, drawdown_percent, cuenta))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error al actualizar max drawdown: {e}")
            
    def monitorear_cuenta(self, cuenta: str, login: int, password: str, server: str) -> Dict:
        """
        Monitorea una cuenta específica.
        
        Args:
            cuenta: Número de cuenta
            login: Login de MT5
            password: Contraseña
            server: Servidor
            
        Returns:
            Diccionario con resultado del monitoreo
        """
        resultado = {
            'cuenta': cuenta,
            'exitoso': False,
            'balance': 0,
            'equity': 0,
            'drawdown': 0,
            'drawdown_percent': 0,
            'alerta_nivel': 'VERDE',
            'trading_activo': True,
            'mensaje': ''
        }
        
        try:
            # Conectar a MT5
            if not self.conectar_mt5(login, password, server):
                resultado['mensaje'] = "Error al conectar a MT5"
                return resultado
                
            # Obtener información de cuenta
            info = self.obtener_info_cuenta()
            if not info:
                resultado['mensaje'] = "Error al obtener información de cuenta"
                mt5.shutdown()
                return resultado
                
            balance = info['balance']
            equity = info['equity']
            
            # Calcular drawdown
            dd = self.calcular_drawdown(balance, equity)
            
            # Obtener máximo drawdown histórico
            max_dd = self.obtener_max_drawdown(cuenta)
            
            # Actualizar máximo si es necesario
            if dd['drawdown'] > max_dd['max_drawdown']:
                max_dd = {
                    'max_drawdown': dd['drawdown'],
                    'max_drawdown_percent': dd['drawdown_percent']
                }
                self.actualizar_max_drawdown(cuenta, dd['drawdown'], dd['drawdown_percent'])
                
            # Evaluar nivel de alerta
            alerta_nivel = self.evaluar_nivel_alerta(dd['drawdown_percent'])
            
            # Determinar si trading debe estar activo
            trading_activo = alerta_nivel != "NEGRO"
            
            # Registrar monitoreo
            self.registrar_monitoreo(
                cuenta, balance, equity, dd['drawdown'], dd['drawdown_percent'],
                max_dd['max_drawdown'], max_dd['max_drawdown_percent'],
                alerta_nivel, trading_activo
            )
            
            # Actualizar resultado
            resultado.update({
                'exitoso': True,
                'balance': balance,
                'equity': equity,
                'drawdown': dd['drawdown'],
                'drawdown_percent': dd['drawdown_percent'],
                'alerta_nivel': alerta_nivel,
                'trading_activo': trading_activo,
                'mensaje': f"Monitoreo exitoso - Alerta: {alerta_nivel}"
            })
            
            mt5.shutdown()
            
        except Exception as e:
            resultado['mensaje'] = f"Error durante monitoreo: {e}"
            logger.error(f"Error al monitorear cuenta {cuenta}: {e}")
            
        return resultado
        
    def obtener_historico(self, cuenta: str, horas: int = 24) -> list:
        """
        Obtiene el histórico de monitoreo de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            horas: Horas de histórico a recuperar
            
        Returns:
            Lista de registros de monitoreo
        """
        try:
            fecha_limite = datetime.now() - timedelta(hours=horas)
            
            self.cursor.execute("""
                SELECT * FROM drawdown_monitor
                WHERE cuenta = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (cuenta, fecha_limite.isoformat()))
            
            return self.cursor.fetchall()
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
    
    agente = AgenteMonitorDrawdown()
    
    # Ejemplo de monitoreo (reemplazar con credenciales reales)
    resultado = agente.monitorear_cuenta(
        cuenta="123456",
        login=123456,
        password="tu_password",
        server="tu_broker"
    )
    
    print(f"Resultado monitoreo: {resultado}")
    
    # Obtener histórico
    historico = agente.obtener_historico("123456", horas=24)
    print(f"Registros históricos: {len(historico)}")
    
    agente.cerrar()

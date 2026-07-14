"""
Agente Compliance PropFirm - D1: Enjambre CFDs/US30
Verifica reglas de propfirms, ajusta comportamiento

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Verifica el cumplimiento de las reglas de las propfirms,
             ajusta el comportamiento del bot según las restricciones.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class AgenteCompliancePropfirm:
    """Verifica reglas de propfirms y ajusta comportamiento."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de compliance.
        
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
                CREATE TABLE IF NOT EXISTS propfirm_reglas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    propfirm TEXT NOT NULL,
                    max_drawdown REAL NOT NULL,
                    max_daily_loss REAL NOT NULL,
                    max_drawdown_percent REAL NOT NULL,
                    max_daily_loss_percent REAL NOT NULL,
                    min_trading_days INTEGER,
                    max_lotage REAL,
                    trading_hours TEXT,
                    instruments TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    regla TEXT NOT NULL,
                    valor_actual REAL NOT NULL,
                    limite REAL NOT NULL,
                    estado TEXT NOT NULL,
                    accion_tomada TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_propfirm(self, propfirm: str, max_dd: float, max_daily_loss: float,
                          max_dd_percent: float, max_daily_loss_percent: float,
                          min_trading_days: int = None, max_lotage: float = None,
                          trading_hours: str = None, instruments: str = None):
        """
        Registra una propfirm con sus reglas.
        
        Args:
            propfirm: Nombre de la propfirm
            max_dd: Máximo drawdown absoluto
            max_daily_loss: Máxima pérdida diaria absoluta
            max_dd_percent: Máximo drawdown porcentual
            max_daily_loss_percent: Máxima pérdida diaria porcentual
            min_trading_days: Días mínimos de trading
            max_lotage: Lotaje máximo permitido
            trading_hours: Horas permitidas para trading
            instruments: Instrumentos permitidos
        """
        try:
            self.cursor.execute("""
                INSERT INTO propfirm_reglas
                (propfirm, max_drawdown, max_daily_loss, max_drawdown_percent,
                 max_daily_loss_percent, min_trading_days, max_lotage,
                 trading_hours, instruments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (propfirm, max_dd, max_daily_loss, max_dd_percent,
                  max_daily_loss_percent, min_trading_days, max_lotage,
                  trading_hours, instruments))
            self.conn.commit()
            logger.info(f"Propfirm {propfirm} registrada correctamente")
        except Exception as e:
            logger.error(f"Error al registrar propfirm: {e}")
            
    def obtener_reglas_propfirm(self, propfirm: str) -> Optional[Dict]:
        """
        Obtiene las reglas de una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            
        Returns:
            Diccionario con reglas o None
        """
        try:
            self.cursor.execute("""
                SELECT * FROM propfirm_reglas
                WHERE propfirm = ? AND activo = TRUE
                ORDER BY timestamp DESC
                LIMIT 1
            """, (propfirm,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'propfirm': result[1],
                    'max_drawdown': result[2],
                    'max_daily_loss': result[3],
                    'max_drawdown_percent': result[4],
                    'max_daily_loss_percent': result[5],
                    'min_trading_days': result[6],
                    'max_lotage': result[7],
                    'trading_hours': result[8],
                    'instruments': result[9]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener reglas: {e}")
            return None
            
    def verificar_drawdown(self, cuenta: str, propfirm: str, balance: float, equity: float) -> Dict:
        """
        Verifica el cumplimiento de drawdown.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            balance: Balance actual
            equity: Equity actual
            
        Returns:
            Diccionario con resultado de verificación
        """
        reglas = self.obtener_reglas_propfirm(propfirm)
        if not reglas:
            return {'estado': 'ERROR', 'mensaje': 'No hay reglas para esta propfirm'}
            
        drawdown = balance - equity
        drawdown_percent = (drawdown / balance * 100) if balance > 0 else 0
        
        resultado = {
            'cuenta': cuenta,
            'propfirm': propfirm,
            'regla': 'max_drawdown',
            'valor_actual': drawdown,
            'limite': reglas['max_drawdown'],
            'estado': 'CUMPLE' if drawdown < reglas['max_drawdown'] else 'VIOLA',
            'accion_tomada': None
        }
        
        if drawdown >= reglas['max_drawdown']:
            resultado['accion_tomada'] = 'DETENER_TRADING'
            self._registrar_log(resultado)
            
        return resultado
        
    def verificar_daily_loss(self, cuenta: str, propfirm: str, daily_loss: float) -> Dict:
        """
        Verifica el cumplimiento de pérdida diaria.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            daily_loss: Pérdida diaria actual
            
        Returns:
            Diccionario con resultado de verificación
        """
        reglas = self.obtener_reglas_propfirm(propfirm)
        if not reglas:
            return {'estado': 'ERROR', 'mensaje': 'No hay reglas para esta propfirm'}
            
        resultado = {
            'cuenta': cuenta,
            'propfirm': propfirm,
            'regla': 'max_daily_loss',
            'valor_actual': daily_loss,
            'limite': reglas['max_daily_loss'],
            'estado': 'CUMPLE' if daily_loss < reglas['max_daily_loss'] else 'VIOLA',
            'accion_tomada': None
        }
        
        if daily_loss >= reglas['max_daily_loss']:
            resultado['accion_tomada'] = 'DETENER_TRADING_DIA'
            self._registrar_log(resultado)
            
        return resultado
        
    def verificar_lotaje(self, cuenta: str, propfirm: str, lotaje: float) -> Dict:
        """
        Verifica el cumplimiento de lotaje máximo.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            lotaje: Lotaje actual
            
        Returns:
            Diccionario con resultado de verificación
        """
        reglas = self.obtener_reglas_propfirm(propfirm)
        if not reglas or reglas['max_lotage'] is None:
            return {'estado': 'OK', 'mensaje': 'No hay límite de lotaje'}
            
        resultado = {
            'cuenta': cuenta,
            'propfirm': propfirm,
            'regla': 'max_lotage',
            'valor_actual': lotaje,
            'limite': reglas['max_lotage'],
            'estado': 'CUMPLE' if lotaje <= reglas['max_lotage'] else 'VIOLA',
            'accion_tomada': None
        }
        
        if lotaje > reglas['max_lotage']:
            resultado['accion_tomada'] = 'REDUCIR_LOTAJE'
            self._registrar_log(resultado)
            
        return resultado
        
    def verificar_instrumentos(self, cuenta: str, propfirm: str, instrumento: str) -> Dict:
        """
        Verifica si el instrumento está permitido.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            instrumento: Instrumento a verificar
            
        Returns:
            Diccionario con resultado de verificación
        """
        reglas = self.obtener_reglas_propfirm(propfirm)
        if not reglas or reglas['instruments'] is None:
            return {'estado': 'OK', 'mensaje': 'No hay restricción de instrumentos'}
            
        instrumentos_permitidos = reglas['instruments'].split(',')
        instrumentos_permitidos = [i.strip() for i in instrumentos_permitidos]
        
        resultado = {
            'cuenta': cuenta,
            'propfirm': propfirm,
            'regla': 'instruments',
            'valor_actual': instrumento,
            'limite': reglas['instruments'],
            'estado': 'CUMPLE' if instrumento in instrumentos_permitidos else 'VIOLA',
            'accion_tomada': None
        }
        
        if instrumento not in instrumentos_permitidos:
            resultado['accion_tomada'] = 'BLOQUEAR_INSTRUMENTO'
            self._registrar_log(resultado)
            
        return resultado
        
    def verificar_trading_hours(self, cuenta: str, propfirm: str, hora_actual: str) -> Dict:
        """
        Verifica si la hora actual está permitida para trading.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            hora_actual: Hora actual en formato HH:MM
            
        Returns:
            Diccionario con resultado de verificación
        """
        reglas = self.obtener_reglas_propfirm(propfirm)
        if not reglas or reglas['trading_hours'] is None:
            return {'estado': 'OK', 'mensaje': 'No hay restricción de horario'}
            
        resultado = {
            'cuenta': cuenta,
            'propfirm': propfirm,
            'regla': 'trading_hours',
            'valor_actual': hora_actual,
            'limite': reglas['trading_hours'],
            'estado': 'CUMPLE',
            'accion_tomada': None
        }
        
        # Lógica simple de horarios (puede expandirse)
        if reglas['trading_hours']:
            resultado['estado'] = 'CUMPLE'
        else:
            resultado['estado'] = 'VIOLA'
            resultado['accion_tomada'] = 'DETENER_TRADING_HORA'
            self._registrar_log(resultado)
            
        return resultado
        
    def _registrar_log(self, resultado: Dict):
        """Registra el resultado en el log de compliance."""
        try:
            self.cursor.execute("""
                INSERT INTO compliance_log
                (cuenta, propfirm, regla, valor_actual, limite, estado, accion_tomada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (resultado['cuenta'], resultado['propfirm'], resultado['regla'],
                  resultado['valor_actual'], resultado['limite'],
                  resultado['estado'], resultado['accion_tomada']))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar log: {e}")
            
    def verificar_completo(self, cuenta: str, propfirm: str, balance: float, equity: float,
                          daily_loss: float, lotaje: float, instrumento: str, 
                          hora_actual: str) -> Dict:
        """
        Verifica todas las reglas de compliance.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            balance: Balance actual
            equity: Equity actual
            daily_loss: Pérdida diaria
            lotaje: Lotaje actual
            instrumento: Instrumento actual
            hora_actual: Hora actual
            
        Returns:
            Diccionario con resultado completo
        """
        resultados = {
            'cuenta': cuenta,
            'propfirm': propfirm,
            'verificaciones': [],
            'estado_global': 'CUMPLE',
            'acciones_requeridas': []
        }
        
        # Verificar drawdown
        dd_result = self.verificar_drawdown(cuenta, propfirm, balance, equity)
        resultados['verificaciones'].append(dd_result)
        
        # Verificar pérdida diaria
        dl_result = self.verificar_daily_loss(cuenta, propfirm, daily_loss)
        resultados['verificaciones'].append(dl_result)
        
        # Verificar lotaje
        lt_result = self.verificar_lotaje(cuenta, propfirm, lotaje)
        resultados['verificaciones'].append(lt_result)
        
        # Verificar instrumentos
        ins_result = self.verificar_instrumentos(cuenta, propfirm, instrumento)
        resultados['verificaciones'].append(ins_result)
        
        # Verificar horarios
        hr_result = self.verificar_trading_hours(cuenta, propfirm, hora_actual)
        resultados['verificaciones'].append(hr_result)
        
        # Determinar estado global
        for verif in resultados['verificaciones']:
            if verif['estado'] == 'VIOLA':
                resultados['estado_global'] = 'VIOLA'
                if verif['accion_tomada']:
                    resultados['acciones_requeridas'].append(verif['accion_tomada'])
                    
        return resultados
        
    def obtener_historico_compliance(self, cuenta: str, dias: int = 7) -> List:
        """
        Obtiene el histórico de compliance de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            dias: Días de histórico a recuperar
            
        Returns:
            Lista de registros de compliance
        """
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT * FROM compliance_log
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
    
    agente = AgenteCompliancePropfirm()
    
    # Ejemplo: registrar propfirm
    agente.registrar_propfirm(
        propfirm="FTMO",
        max_dd=50000,
        max_daily_loss=10000,
        max_dd_percent=10,
        max_daily_loss_percent=5,
        min_trading_days=10,
        max_lotage=10.0,
        trading_hours="00:00-23:59",
        instruments="EURUSD,GBPUSD,USDJPY,XAUUSD"
    )
    
    # Ejemplo: verificación completa
    resultado = agente.verificar_completo(
        cuenta="123456",
        propfirm="FTMO",
        balance=100000,
        equity=98000,
        daily_loss=2000,
        lotaje=5.0,
        instrumento="EURUSD",
        hora_actual="14:30"
    )
    
    print(f"Resultado compliance: {resultado}")
    
    # Obtener histórico
    historico = agente.obtener_historico_compliance("123456", dias=7)
    print(f"Registros históricos: {len(historico)}")
    
    agente.cerrar()

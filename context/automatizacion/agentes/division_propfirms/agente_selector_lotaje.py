"""
Agente Selector Lotaje - D2B: PropFirms y Dispersión de Cuentas
Calcula lotaje óptimo según riesgo y cuenta

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Calcula el lotaje óptimo para cada operación basándose
             en el perfil de riesgo, balance de la cuenta y reglas de la propfirm.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteSelectorLotaje:
    """Calcula lotaje óptimo según riesgo y cuenta."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente selector de lotaje.
        
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
                CREATE TABLE IF NOT EXISTS perfiles_riesgo_cuenta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT UNIQUE NOT NULL,
                    riesgo_porcentaje REAL NOT NULL,
                    max_drawdown_porcentaje REAL NOT NULL,
                    max_riesgo_por_trade REAL NOT NULL,
                    lotaje_maximo REAL NOT NULL,
                    lotaje_minimo REAL NOT NULL,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reglas_propfirm_lotaje (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    propfirm TEXT NOT NULL,
                    lotaje_maximo REAL NOT NULL,
                    lotaje_minimo REAL NOT NULL,
                    max_posiciones_abiertas INTEGER,
                    max_riesgo_total REAL,
                    restricciones TEXT,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculos_lotaje (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    stop_loss_pips REAL NOT NULL,
                    riesgo_porcentaje REAL NOT NULL,
                    lotaje_calculado REAL NOT NULL,
                    lotaje_ajustado REAL NOT NULL,
                    motivo_ajuste TEXT,
                    fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS instrumentos_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simbolo TEXT UNIQUE NOT NULL,
                    valor_pip REAL NOT NULL,
                    contrato_size REAL NOT NULL,
                    lotaje_minimo REAL NOT NULL,
                    lotaje_maximo REAL NOT NULL,
                    paso_lotaje REAL NOT NULL,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_perfil_riesgo_cuenta(self, cuenta: str, riesgo_porcentaje: float,
                                       max_drawdown: float, max_riesgo_trade: float,
                                       lotaje_max: float, lotaje_min: float = 0.01) -> int:
        """
        Registra un perfil de riesgo para una cuenta.
        
        Args:
            cuenta: Número de cuenta
            riesgo_porcentaje: Riesgo por trade en porcentaje del balance
            max_drawdown: Máximo drawdown permitido en porcentaje
            max_riesgo_trade: Máximo riesgo por trade en porcentaje
            lotaje_max: Lotaje máximo permitido
            lotaje_min: Lotaje mínimo permitido
            
        Returns:
            ID del perfil registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO perfiles_riesgo_cuenta
                (cuenta, riesgo_porcentaje, max_drawdown_porcentaje, max_riesgo_por_trade,
                 lotaje_maximo, lotaje_minimo, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO')
            """, (cuenta, riesgo_porcentaje, max_drawdown, max_riesgo_trade,
                  lotaje_max, lotaje_min))
            
            self.conn.commit()
            perfil_id = self.cursor.lastrowid
            logger.info(f"Perfil de riesgo registrado - ID: {perfil_id} - Cuenta: {cuenta}")
            return perfil_id
        except Exception as e:
            logger.error(f"Error al registrar perfil de riesgo: {e}")
            raise
            
    def registrar_regla_propfirm(self, propfirm: str, lotaje_max: float, lotaje_min: float = 0.01,
                               max_posiciones: int = None, max_riesgo_total: float = None,
                               restricciones: dict = None) -> int:
        """
        Registra reglas de lotaje para una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            lotaje_max: Lotaje máximo
            lotaje_min: Lotaje mínimo
            max_posiciones: Máximo de posiciones abiertas
            max_riesgo_total: Máximo riesgo total
            restricciones: Restricciones adicionales (dict)
            
        Returns:
            ID de la regla registrada
        """
        try:
            restricciones_json = json.dumps(restricciones) if restricciones else None
            
            self.cursor.execute("""
                INSERT INTO reglas_propfirm_lotaje
                (propfirm, lotaje_maximo, lotaje_minimo, max_posiciones_abiertas,
                 max_riesgo_total, restricciones, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVA')
            """, (propfirm, lotaje_max, lotaje_min, max_posiciones, max_riesgo_total,
                  restricciones_json))
            
            self.conn.commit()
            regla_id = self.cursor.lastrowid
            logger.info(f"Regla de propfirm registrada - ID: {regla_id} - Propfirm: {propfirm}")
            return regla_id
        except Exception as e:
            logger.error(f"Error al registrar regla de propfirm: {e}")
            raise
            
    def registrar_instrumento(self, simbolo: str, valor_pip: float, contrato_size: float = 100000,
                            lotaje_min: float = 0.01, lotaje_max: float = 100,
                            paso_lotaje: float = 0.01) -> int:
        """
        Registra la configuración de un instrumento.
        
        Args:
            simbolo: Símbolo del instrumento
            valor_pip: Valor de un pip
            contrato_size: Tamaño del contrato
            lotaje_min: Lotaje mínimo
            lotaje_max: Lotaje máximo
            paso_lotaje: Paso del lotaje
            
        Returns:
            ID del instrumento registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO instrumentos_config
                (simbolo, valor_pip, contrato_size, lotaje_minimo, lotaje_maximo, paso_lotaje, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO')
            """, (simbolo, valor_pip, contrato_size, lotaje_min, lotaje_max, paso_lotaje))
            
            self.conn.commit()
            instrumento_id = self.cursor.lastrowid
            logger.info(f"Instrumento registrado - ID: {instrumento_id} - Símbolo: {simbolo}")
            return instrumento_id
        except Exception as e:
            logger.error(f"Error al registrar instrumento: {e}")
            raise
            
    def calcular_lotaje(self, cuenta: str, propfirm: str, balance: float, equity: float,
                       stop_loss_pips: float, simbolo: str = "EURUSD") -> Dict:
        """
        Calcula el lotaje óptimo para una operación.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Nombre de la propfirm
            balance: Balance actual
            equity: Equity actual
            stop_loss_pips: Stop loss en pips
            simbolo: Símbolo del instrumento
            
        Returns:
            Diccionario con resultado del cálculo
        """
        try:
            # Obtener perfil de riesgo de la cuenta
            perfil = self._obtener_perfil_cuenta(cuenta)
            if not perfil:
                return {'exito': False, 'mensaje': 'No hay perfil de riesgo para la cuenta'}
                
            # Obtener reglas de la propfirm
            reglas_prop = self._obtener_reglas_propfirm(propfirm)
            if not reglas_prop:
                return {'exito': False, 'mensaje': 'No hay reglas para la propfirm'}
                
            # Obtener configuración del instrumento
            instrumento = self._obtener_instrumento(simbolo)
            if not instrumento:
                instrumento = {'valor_pip': 10, 'paso_lotaje': 0.01}  # Valores por defecto
                
            # Calcular lotaje base según riesgo
            riesgo_porcentaje = perfil['riesgo_porcentaje']
            valor_riesgo = equity * (riesgo_porcentaje / 100)
            valor_pip = instrumento['valor_pip']
            riesgo_pip = stop_loss_pips * valor_pip
            
            lotaje_calculado = valor_riesgo / riesgo_pip if riesgo_pip > 0 else 0
            
            # Aplicar límites del perfil
            lotaje_calculado = max(perfil['lotaje_minimo'],
                                  min(lotaje_calculado, perfil['lotaje_maximo']))
            
            # Aplicar límites de la propfirm
            lotaje_ajustado = max(reglas_prop['lotaje_minimo'],
                                 min(lotaje_calculado, reglas_prop['lotaje_maximo']))
            
            # Ajustar al paso del lotaje
            paso = instrumento.get('paso_lotaje', 0.01)
            lotaje_ajustado = round(lotaje_ajustado / paso) * paso
            
            # Determinar motivo de ajuste
            motivo_ajuste = []
            if lotaje_ajustado != lotaje_calculado:
                if lotaje_ajustado > lotaje_calculado:
                    motivo_ajuste.append("Aumentado al mínimo permitido")
                else:
                    if lotaje_ajustado == reglas_prop['lotaje_maximo']:
                        motivo_ajuste.append("Limitado por regla propfirm")
                    elif lotaje_ajustado == perfil['lotaje_maximo']:
                        motivo_ajuste.append("Limitado por perfil riesgo")
                        
            # Registrar cálculo
            self._registrar_calculo(
                cuenta, propfirm, balance, equity, stop_loss_pips,
                riesgo_porcentaje, lotaje_calculado, lotaje_ajustado,
                ", ".join(motivo_ajuste) if motivo_ajuste else None
            )
            
            return {
                'exito': True,
                'cuenta': cuenta,
                'propfirm': propfirm,
                'balance': balance,
                'equity': equity,
                'stop_loss_pips': stop_loss_pips,
                'riesgo_porcentaje': riesgo_porcentaje,
                'lotaje_calculado': round(lotaje_calculado, 2),
                'lotaje_ajustado': round(lotaje_ajustado, 2),
                'motivo_ajuste': ", ".join(motivo_ajuste) if motivo_ajuste else "Sin ajustes",
                'valor_riesgo_usd': round(valor_riesgo, 2),
                'riesgo_porcentaje_actual': round((lotaje_ajustado * riesgo_pip / equity * 100), 2)
            }
        except Exception as e:
            logger.error(f"Error al calcular lotaje: {e}")
            return {'exito': False, 'mensaje': str(e)}
            
    def _obtener_perfil_cuenta(self, cuenta: str) -> Optional[Dict]:
        """Obtiene el perfil de riesgo de una cuenta."""
        try:
            self.cursor.execute("""
                SELECT * FROM perfiles_riesgo_cuenta
                WHERE cuenta = ? AND estado = 'ACTIVO'
                ORDER BY timestamp DESC LIMIT 1
            """, (cuenta,))
            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'cuenta': result[1], 'riesgo_porcentaje': result[2],
                    'max_drawdown_porcentaje': result[3], 'max_riesgo_por_trade': result[4],
                    'lotaje_maximo': result[5], 'lotaje_minimo': result[6]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener perfil cuenta: {e}")
            return None
            
    def _obtener_reglas_propfirm(self, propfirm: str) -> Optional[Dict]:
        """Obtiene las reglas de una propfirm."""
        try:
            self.cursor.execute("""
                SELECT * FROM reglas_propfirm_lotaje
                WHERE propfirm = ? AND estado = 'ACTIVA'
                ORDER BY timestamp DESC LIMIT 1
            """, (propfirm,))
            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'propfirm': result[1], 'lotaje_maximo': result[2],
                    'lotaje_minimo': result[3], 'max_posiciones_abiertas': result[4],
                    'max_riesgo_total': result[5], 'restricciones': result[6]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener reglas propfirm: {e}")
            return None
            
    def _obtener_instrumento(self, simbolo: str) -> Optional[Dict]:
        """Obtiene la configuración de un instrumento."""
        try:
            self.cursor.execute("""
                SELECT * FROM instrumentos_config
                WHERE simbolo = ? AND estado = 'ACTIVO'
                ORDER BY timestamp DESC LIMIT 1
            """, (simbolo,))
            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'simbolo': result[1], 'valor_pip': result[2],
                    'contrato_size': result[3], 'lotaje_minimo': result[4],
                    'lotaje_maximo': result[5], 'paso_lotaje': result[6]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener instrumento: {e}")
            return None
            
    def _registrar_calculo(self, cuenta: str, propfirm: str, balance: float, equity: float,
                         stop_loss_pips: float, riesgo_porcentaje: float,
                         lotaje_calculado: float, lotaje_ajustado: float, motivo_ajuste: str):
        """Registra un cálculo de lotaje."""
        try:
            self.cursor.execute("""
                INSERT INTO calculos_lotaje
                (cuenta, propfirm, balance, equity, stop_loss_pips, riesgo_porcentaje,
                 lotaje_calculado, lotaje_ajustado, motivo_ajuste)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cuenta, propfirm, balance, equity, stop_loss_pips, riesgo_porcentaje,
                  lotaje_calculado, lotaje_ajustado, motivo_ajuste))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar cálculo: {e}")
            
    def obtener_historico_calculos(self, cuenta: str = None, dias: int = 30) -> List[Dict]:
        """Obtiene el histórico de cálculos de lotaje."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            if cuenta:
                self.cursor.execute("""
                    SELECT * FROM calculos_lotaje
                    WHERE cuenta = ? AND fecha_calculo >= ?
                    ORDER BY fecha_calculo DESC
                """, (cuenta, fecha_limite.isoformat()))
            else:
                self.cursor.execute("""
                    SELECT * FROM calculos_lotaje
                    WHERE fecha_calculo >= ?
                    ORDER BY fecha_calculo DESC
                """, (fecha_limite.isoformat(),))
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'propfirm': r[2], 'balance': r[3],
                'equity': r[4], 'stop_loss_pips': r[5], 'riesgo_porcentaje': r[6],
                'lotaje_calculado': r[7], 'lotaje_ajustado': r[8], 'motivo_ajuste': r[9],
                'fecha_calculo': r[10]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener histórico: {e}")
            return []
            
    def actualizar_perfil_cuenta(self, cuenta: str, riesgo_porcentaje: float = None,
                               max_drawdown: float = None, max_riesgo_trade: float = None,
                               lotaje_max: float = None) -> bool:
        """Actualiza el perfil de riesgo de una cuenta."""
        try:
            updates = []
            values = []
            
            if riesgo_porcentaje:
                updates.append("riesgo_porcentaje = ?")
                values.append(riesgo_porcentaje)
            if max_drawdown:
                updates.append("max_drawdown_porcentaje = ?")
                values.append(max_drawdown)
            if max_riesgo_trade:
                updates.append("max_riesgo_por_trade = ?")
                values.append(max_riesgo_trade)
            if lotaje_max:
                updates.append("lotaje_maximo = ?")
                values.append(lotaje_max)
                
            if not updates:
                return False
                
            values.append(cuenta)
            query = f"UPDATE perfiles_riesgo_cuenta SET {', '.join(updates)} WHERE cuenta = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logger.info(f"Perfil de cuenta {cuenta} actualizado")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar perfil: {e}")
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
    
    agente = AgenteSelectorLotaje()
    
    # Ejemplo: registrar perfil
    perfil_id = agente.registrar_perfil_riesgo_cuenta(
        cuenta="123456",
        riesgo_porcentaje=1.0,
        max_drawdown=5.0,
        max_riesgo_trade=2.0,
        lotaje_max=10.0,
        lotaje_min=0.01
    )
    
    print(f"Perfil registrado - ID: {perfil_id}")
    
    # Ejemplo: registrar regla propfirm
    regla_id = agente.registrar_regla_propfirm(
        propfirm="FTMO",
        lotaje_max=100.0,
        lotaje_min=0.01,
        max_posiciones=5,
        max_riesgo_total=10.0
    )
    
    print(f"Regla registrada - ID: {regla_id}")
    
    # Ejemplo: registrar instrumento
    instrumento_id = agente.registrar_instrumento(
        simbolo="EURUSD",
        valor_pip=10,
        contrato_size=100000
    )
    
    print(f"Instrumento registrado - ID: {instrumento_id}")
    
    # Ejemplo: calcular lotaje
    resultado = agente.calcular_lotaje(
        cuenta="123456",
        propfirm="FTMO",
        balance=10000,
        equity=10000,
        stop_loss_pips=20,
        simbolo="EURUSD"
    )
    
    print(f"Cálculo lotaje: {resultado}")
    
    # Ejemplo: obtener histórico
    historico = agente.obtener_historico_calculos("123456")
    print(f"Registros históricos: {len(historico)}")
    
    agente.cerrar()

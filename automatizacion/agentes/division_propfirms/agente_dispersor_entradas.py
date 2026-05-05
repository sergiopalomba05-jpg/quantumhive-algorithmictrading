"""
Agente Dispersor Entradas - D2B: PropFirms y Dispersión de Cuentas
Distribuye entradas entre múltiples cuentas

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Distribuye las señales de entrada entre múltiples cuentas
             para diversificar el riesgo y optimizar el uso del capital.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteDispersorEntradas:
    """Distribuye entradas entre múltiples cuentas."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente dispersor de entradas.
        
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
                CREATE TABLE IF NOT EXISTS grupos_cuentas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT,
                    estrategia_distribucion TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS cuentas_grupo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grupo_id INTEGER NOT NULL,
                    cuenta TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    peso REAL NOT NULL,
                    balance_actual REAL NOT NULL,
                    estado TEXT NOT NULL,
                    FOREIGN KEY (grupo_id) REFERENCES grupos_cuentas(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS señales_recibidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grupo_id INTEGER NOT NULL,
                    simbolo TEXT NOT NULL,
                    tipo_orden TEXT NOT NULL,
                    precio_entrada REAL NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    lotaje_base REAL NOT NULL,
                    fecha_señal DATETIME DEFAULT CURRENT_TIMESTAMP,
                    procesada BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (grupo_id) REFERENCES grupos_cuentas(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ordenes_distribuidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    señal_id INTEGER NOT NULL,
                    cuenta TEXT NOT NULL,
                    simbolo TEXT NOT NULL,
                    tipo_orden TEXT NOT NULL,
                    lotaje REAL NOT NULL,
                    precio_entrada REAL NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    fecha_ejecucion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    ticket_mt5 TEXT,
                    FOREIGN KEY (señal_id) REFERENCES señales_recibidas(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_distribucion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    señal_id INTEGER NOT NULL,
                    grupo_id INTEGER NOT NULL,
                    total_cuentas INTEGER NOT NULL,
                    cuentas_exitosas INTEGER NOT NULL,
                    cuentas_fallidas INTEGER NOT NULL,
                    fecha_distribucion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (señal_id) REFERENCES señales_recibidas(id),
                    FOREIGN KEY (grupo_id) REFERENCES grupos_cuentas(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_grupo_cuentas(self, nombre: str, estrategia_distribucion: str = 
                           "proporcional_balance", descripcion: str = None) -> int:
        """
        Crea un grupo de cuentas para distribución.
        
        Args:
            nombre: Nombre del grupo
            estrategia_distribucion: Estrategia de distribución (proporcional_balance, igual, ponderado)
            descripcion: Descripción del grupo
            
        Returns:
            ID del grupo creado
        """
        try:
            self.cursor.execute("""
                INSERT INTO grupos_cuentas (nombre, descripcion, estrategia_distribucion, estado)
                VALUES (?, ?, ?, 'ACTIVO')
            """, (nombre, descripcion, estrategia_distribucion))
            
            self.conn.commit()
            grupo_id = self.cursor.lastrowid
            logger.info(f"Grupo de cuentas creado - ID: {grupo_id} - Nombre: {nombre}")
            return grupo_id
        except Exception as e:
            logger.error(f"Error al crear grupo de cuentas: {e}")
            raise
            
    def agregar_cuenta_grupo(self, grupo_id: int, cuenta: str, propfirm: str,
                            peso: float = 1.0, balance_actual: float = None) -> int:
        """
        Agrega una cuenta a un grupo.
        
        Args:
            grupo_id: ID del grupo
            cuenta: Número de cuenta
            propfirm: Propfirm
            peso: Peso de la cuenta en la distribución
            balance_actual: Balance actual
            
        Returns:
            ID de la cuenta en el grupo
        """
        try:
            if balance_actual is None:
                balance_actual = 10000  # Valor por defecto
                
            self.cursor.execute("""
                INSERT INTO cuentas_grupo (grupo_id, cuenta, propfirm, peso, balance_actual, estado)
                VALUES (?, ?, ?, ?, ?, 'ACTIVA')
            """, (grupo_id, cuenta, propfirm, peso, balance_actual))
            
            self.conn.commit()
            cuenta_grupo_id = self.cursor.lastrowid
            logger.info(f"Cuenta agregada al grupo - ID: {cuenta_grupo_id} - Cuenta: {cuenta}")
            return cuenta_grupo_id
        except Exception as e:
            logger.error(f"Error al agregar cuenta al grupo: {e}")
            raise
            
    def recibir_señal(self, grupo_id: int, simbolo: str, tipo_orden: str,
                      precio_entrada: float, lotaje_base: float,
                      stop_loss: float = None, take_profit: float = None) -> int:
        """
        Recibe una señal de trading para distribuir.
        
        Args:
            grupo_id: ID del grupo
            simbolo: Símbolo del instrumento
            tipo_orden: Tipo de orden (BUY, SELL)
            precio_entrada: Precio de entrada
            lotaje_base: Lotaje base
            stop_loss: Stop loss
            take_profit: Take profit
            
        Returns:
            ID de la señal recibida
        """
        try:
            self.cursor.execute("""
                INSERT INTO señales_recibidas
                (grupo_id, simbolo, tipo_orden, precio_entrada, stop_loss, take_profit, lotaje_base)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (grupo_id, simbolo, tipo_orden, precio_entrada, stop_loss, take_profit, lotaje_base))
            
            self.conn.commit()
            señal_id = self.cursor.lastrowid
            logger.info(f"Señal recibida - ID: {señal_id} - Símbolo: {simbolo}")
            return señal_id
        except Exception as e:
            logger.error(f"Error al recibir señal: {e}")
            raise
            
    def distribuir_señal(self, señal_id: int) -> Dict:
        """
        Distribuye una señal entre las cuentas del grupo.
        
        Args:
            señal_id: ID de la señal
            
        Returns:
            Diccionario con resultado de la distribución
        """
        try:
            # Obtener señal
            self.cursor.execute("""
                SELECT * FROM señales_recibidas WHERE id = ?
            """, (señal_id,))
            señal = self.cursor.fetchone()
            
            if not señal:
                return {'exito': False, 'mensaje': 'Señal no encontrada'}
                
            grupo_id = señal[1]
            simbolo = señal[2]
            tipo_orden = señal[3]
            precio_entrada = señal[4]
            stop_loss = señal[5]
            take_profit = señal[6]
            lotaje_base = señal[7]
            
            # Obtener cuentas del grupo
            self.cursor.execute("""
                SELECT * FROM cuentas_grupo WHERE grupo_id = ? AND estado = 'ACTIVA'
            """, (grupo_id,))
            cuentas = self.cursor.fetchall()
            
            if not cuentas:
                return {'exito': False, 'mensaje': 'No hay cuentas activas en el grupo'}
                
            # Obtener estrategia de distribución
            self.cursor.execute("""
                SELECT estrategia_distribucion FROM grupos_cuentas WHERE id = ?
            """, (grupo_id,))
            estrategia = self.cursor.fetchone()[0]
            
            # Calcular lotajes según estrategia
            lotajes = self._calcular_lotajes(cuentas, lotaje_base, estrategia)
            
            # Distribuir órdenes
            exitosas = 0
            fallidas = 0
            
            for cuenta_row, lotaje in zip(cuentas, lotajes):
                cuenta = cuenta_row[2]
                
                try:
                    orden_id = self._ejecutar_orden(
                        señal_id, cuenta, simbolo, tipo_orden, lotaje,
                        precio_entrada, stop_loss, take_profit
                    )
                    exitosas += 1
                except Exception as e:
                    logger.error(f"Error al ejecutar orden en cuenta {cuenta}: {e}")
                    fallidas += 1
                    
            # Marcar señal como procesada
            self.cursor.execute("""
                UPDATE señales_recibidas SET procesada = TRUE WHERE id = ?
            """, (señal_id,))
            
            # Registrar histórico
            self.cursor.execute("""
                INSERT INTO historico_distribucion
                (señal_id, grupo_id, total_cuentas, cuentas_exitosas, cuentas_fallidas)
                VALUES (?, ?, ?, ?, ?)
            """, (señal_id, grupo_id, len(cuentas), exitosas, fallidas))
            
            self.conn.commit()
            
            return {
                'exito': True,
                'total_cuentas': len(cuentas),
                'exitosas': exitosas,
                'fallidas': fallidas,
                'tasa_exito': round(exitas / len(cuentas) * 100, 2)
            }
        except Exception as e:
            logger.error(f"Error al distribuir señal: {e}")
            return {'exito': False, 'mensaje': str(e)}
            
    def _calcular_lotajes(self, cuentas: List, lotaje_base: float, estrategia: str) -> List[float]:
        """Calcula el lotaje para cada cuenta según la estrategia."""
        lotajes = []
        
        if estrategia == "igual":
            # Distribución igual
            lotaje_por_cuenta = lotaje_base / len(cuentas)
            lotajes = [lotaje_por_cuenta] * len(cuentas)
            
        elif estrategia == "proporcional_balance":
            # Proporcional al balance
            total_balance = sum(c[5] for c in cuentas)
            for cuenta in cuentas:
                peso_balance = cuenta[5] / total_balance
                lotajes.append(lotaje_base * peso_balance)
                
        elif estrategia == "ponderado":
            # Según peso asignado
            total_peso = sum(c[4] for c in cuentas)
            for cuenta in cuentas:
                peso_normalizado = cuenta[4] / total_peso
                lotajes.append(lotaje_base * peso_normalizado)
                
        else:
            # Por defecto: igual
            lotaje_por_cuenta = lotaje_base / len(cuentas)
            lotajes = [lotaje_por_cuenta] * len(cuentas)
            
        return lotajes
        
    def _ejecutar_orden(self, señal_id: int, cuenta: str, simbolo: str, tipo_orden: str,
                       lotaje: float, precio_entrada: float, stop_loss: float,
                       take_profit: float) -> int:
        """Ejecuta una orden en una cuenta (simulado)."""
        try:
            # Aquí iría la lógica real de ejecución con MT5
            # Por ahora, simulamos la ejecución
            
            self.cursor.execute("""
                INSERT INTO ordenes_distribuidas
                (señal_id, cuenta, simbolo, tipo_orden, lotaje, precio_entrada, stop_loss, take_profit, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EJECUTADA')
            """, (señal_id, cuenta, simbolo, tipo_orden, lotaje, precio_entrada, stop_loss, take_profit))
            
            self.conn.commit()
            orden_id = self.cursor.lastrowid
            logger.info(f"Orden ejecutada - ID: {orden_id} - Cuenta: {cuenta} - Lotaje: {lotaje}")
            return orden_id
        except Exception as e:
            logger.error(f"Error al ejecutar orden: {e}")
            raise
            
    def obtener_grupo(self, grupo_id: int) -> Optional[Dict]:
        """Obtiene información de un grupo."""
        try:
            self.cursor.execute("""
                SELECT * FROM grupos_cuentas WHERE id = ?
            """, (grupo_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'nombre': result[1], 'descripcion': result[2],
                    'estrategia_distribucion': result[3], 'estado': result[4], 'timestamp': result[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener grupo: {e}")
            return None
            
    def obtener_cuentas_grupo(self, grupo_id: int) -> List[Dict]:
        """Obtiene las cuentas de un grupo."""
        try:
            self.cursor.execute("""
                SELECT * FROM cuentas_grupo WHERE grupo_id = ?
            """, (grupo_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'grupo_id': r[1], 'cuenta': r[2], 'propfirm': r[3],
                'peso': r[4], 'balance_actual': r[5], 'estado': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener cuentas del grupo: {e}")
            return []
            
    def obtener_señales_pendientes(self, grupo_id: int = None) -> List[Dict]:
        """Obtiene señales pendientes de procesar."""
        try:
            if grupo_id:
                self.cursor.execute("""
                    SELECT * FROM señales_recibidas
                    WHERE grupo_id = ? AND procesada = FALSE
                    ORDER BY fecha_señal ASC
                """, (grupo_id,))
            else:
                self.cursor.execute("""
                    SELECT * FROM señales_recibidas
                    WHERE procesada = FALSE
                    ORDER BY fecha_señal ASC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'grupo_id': r[1], 'simbolo': r[2], 'tipo_orden': r[3],
                'precio_entrada': r[4], 'stop_loss': r[5], 'take_profit': r[6],
                'lotaje_base': r[7], 'fecha_señal': r[8], 'procesada': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener señales pendientes: {e}")
            return []
            
    def obtener_ordenes_distribuidas(self, señal_id: int = None, cuenta: str = None) -> List[Dict]:
        """Obtiene órdenes distribuidas."""
        try:
            if señal_id:
                self.cursor.execute("""
                    SELECT * FROM ordenes_distribuidas WHERE señal_id = ?
                """, (señal_id,))
            elif cuenta:
                self.cursor.execute("""
                    SELECT * FROM ordenes_distribuidas WHERE cuenta = ?
                """, (cuenta,))
            else:
                self.cursor.execute("""
                    SELECT * FROM ordenes_distribuidas ORDER BY fecha_ejecucion DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'señal_id': r[1], 'cuenta': r[2], 'simbolo': r[3],
                'tipo_orden': r[4], 'lotaje': r[5], 'precio_entrada': r[6],
                'stop_loss': r[7], 'take_profit': r[8], 'fecha_ejecucion': r[9],
                'estado': r[10], 'ticket_mt5': r[11]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener órdenes distribuidas: {e}")
            return []
            
    def actualizar_balance_cuenta(self, cuenta_grupo_id: int, nuevo_balance: float) -> bool:
        """Actualiza el balance de una cuenta en el grupo."""
        try:
            self.cursor.execute("""
                UPDATE cuentas_grupo SET balance_actual = ? WHERE id = ?
            """, (nuevo_balance, cuenta_grupo_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar balance: {e}")
            return False
            
    def obtener_estadisticas_grupo(self, grupo_id: int, dias: int = 30) -> Dict:
        """Obtiene estadísticas de un grupo."""
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_señales,
                    SUM(CASE WHEN procesada = TRUE THEN 1 ELSE 0 END) as procesadas,
                    AVG(h.cuentas_exitosas) as avg_exitosas,
                    AVG(h.cuentas_fallidas) as avg_fallidas
                FROM señales_recibidas s
                LEFT JOIN historico_distribucion h ON s.id = h.señal_id
                WHERE s.grupo_id = ? AND s.fecha_señal >= ?
            """, (grupo_id, fecha_limite.isoformat()))
            
            result = self.cursor.fetchone()
            
            if result:
                total, procesadas, avg_exitosas, avg_fallidas = result
                return {
                    'total_señales': total or 0,
                    'procesadas': procesadas or 0,
                    'tasa_procesamiento': round((procesadas / total * 100) if total > 0 else 0, 2),
                    'avg_exitosas_por_señal': round(avg_exitosas or 0, 2),
                    'avg_fallidas_por_señal': round(avg_fallidas or 0, 2),
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
    
    agente = AgenteDispersorEntradas()
    
    # Ejemplo: crear grupo
    grupo_id = agente.crear_grupo_cuentas(
        nombre="Grupo-FTMO-01",
        estrategia_distribucion="proporcional_balance",
        descripcion="Grupo de cuentas FTMO para distribución de señales"
    )
    
    print(f"Grupo creado - ID: {grupo_id}")
    
    # Ejemplo: agregar cuentas
    agente.agregar_cuenta_grupo(grupo_id, "123456", "FTMO", peso=1.0, balance_actual=10000)
    agente.agregar_cuenta_grupo(grupo_id, "789012", "FTMO", peso=1.5, balance_actual=15000)
    agente.agregar_cuenta_grupo(grupo_id, "345678", "FTMO", peso=1.0, balance_actual=10000)
    
    print("Cuentas agregadas al grupo")
    
    # Ejemplo: recibir señal
    señal_id = agente.recibir_señal(
        grupo_id=grupo_id,
        simbolo="EURUSD",
        tipo_orden="BUY",
        precio_entrada=1.0850,
        lotaje_base=0.3,
        stop_loss=1.0800,
        take_profit=1.0900
    )
    
    print(f"Señal recibida - ID: {señal_id}")
    
    # Ejemplo: distribuir señal
    resultado = agente.distribuir_señal(señal_id)
    print(f"Distribución: {resultado}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas_grupo(grupo_id)
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

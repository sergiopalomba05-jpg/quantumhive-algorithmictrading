"""
Agente Challenge - D2: Gestión de Fondeo y Challenges
Gestiona pase challenge por cliente

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona el proceso de challenge de propfirms por cliente,
             monitorea progreso, alerta hitos y transición a funded.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class AgenteChallenge:
    """Gestiona el proceso de challenge de propfirms."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de gestión de challenges.
        
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
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    cliente_nombre TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    cuenta_challenge TEXT NOT NULL,
                    tipo_challenge TEXT NOT NULL,
                    balance_inicial REAL NOT NULL,
                    balance_actual REAL NOT NULL,
                    profit_objetivo REAL NOT NULL,
                    profit_actual REAL NOT NULL,
                    drawdown_max REAL NOT NULL,
                    drawdown_actual REAL NOT NULL,
                    dias_requeridos INTEGER NOT NULL,
                    dias_transcurridos INTEGER DEFAULT 0,
                    estado TEXT NOT NULL,
                    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin DATETIME,
                    cuenta_fondeada TEXT,
                    observaciones TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS challenge_hitos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challenge_id INTEGER NOT NULL,
                    hito_tipo TEXT NOT NULL,
                    hito_valor REAL NOT NULL,
                    hito_actual REAL NOT NULL,
                    fecha_alcanzado DATETIME,
                    FOREIGN KEY (challenge_id) REFERENCES challenges(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS challenge_alertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challenge_id INTEGER NOT NULL,
                    tipo_alerta TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    leida BOOLEAN DEFAULT FALSE,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (challenge_id) REFERENCES challenges(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_challenge(self, cliente_id: str, cliente_nombre: str, propfirm: str,
                       cuenta_challenge: str, tipo_challenge: str, balance_inicial: float,
                       profit_objetivo: float, drawdown_max: float, dias_requeridos: int) -> int:
        """
        Crea un nuevo challenge.
        
        Args:
            cliente_id: ID del cliente
            cliente_nombre: Nombre del cliente
            propfirm: Nombre de la propfirm
            cuenta_challenge: Número de cuenta del challenge
            tipo_challenge: Tipo de challenge (ej: 10k, 50k, 100k)
            balance_inicial: Balance inicial del challenge
            profit_objetivo: Profit objetivo para pasar
            drawdown_max: Drawdown máximo permitido
            dias_requeridos: Días requeridos para completar
            
        Returns:
            ID del challenge creado
        """
        try:
            self.cursor.execute("""
                INSERT INTO challenges
                (cliente_id, cliente_nombre, propfirm, cuenta_challenge, tipo_challenge,
                 balance_inicial, balance_actual, profit_objetivo, profit_actual,
                 drawdown_max, drawdown_actual, dias_requeridos, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, cliente_nombre, propfirm, cuenta_challenge, tipo_challenge,
                  balance_inicial, balance_inicial, profit_objetivo, 0,
                  drawdown_max, 0, dias_requeridos, 'ACTIVO'))
            
            self.conn.commit()
            challenge_id = self.cursor.lastrowid
            logger.info(f"Challenge creado para cliente {cliente_nombre} - ID: {challenge_id}")
            return challenge_id
        except Exception as e:
            logger.error(f"Error al crear challenge: {e}")
            raise
            
    def actualizar_progreso(self, challenge_id: int, balance_actual: float, 
                           drawdown_actual: float, dias_transcurridos: int = None) -> bool:
        """
        Actualiza el progreso de un challenge.
        
        Args:
            challenge_id: ID del challenge
            balance_actual: Balance actual
            drawdown_actual: Drawdown actual
            dias_transcurridos: Días transcurridos (opcional)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Obtener datos actuales
            self.cursor.execute("""
                SELECT balance_inicial, profit_objetivo, drawdown_max, dias_requeridos
                FROM challenges WHERE id = ?
            """, (challenge_id,))
            result = self.cursor.fetchone()
            
            if not result:
                logger.error(f"Challenge {challenge_id} no encontrado")
                return False
                
            balance_inicial, profit_objetivo, drawdown_max, dias_requeridos = result
            
            # Calcular profit actual
            profit_actual = balance_actual - balance_inicial
            
            # Actualizar progreso
            if dias_transcurridos is not None:
                self.cursor.execute("""
                    UPDATE challenges
                    SET balance_actual = ?, profit_actual = ?, drawdown_actual = ?, dias_transcurridos = ?
                    WHERE id = ?
                """, (balance_actual, profit_actual, drawdown_actual, dias_transcurridos, challenge_id))
            else:
                self.cursor.execute("""
                    UPDATE challenges
                    SET balance_actual = ?, profit_actual = ?, drawdown_actual = ?
                    WHERE id = ?
                """, (balance_actual, profit_actual, drawdown_actual, challenge_id))
            
            self.conn.commit()
            
            # Verificar hitos
            self._verificar_hitos(challenge_id, profit_actual, profit_objetivo)
            
            # Verificar si pasó o falló
            self._evaluar_estado(challenge_id, profit_actual, profit_objetivo, 
                              drawdown_actual, drawdown_max, dias_transcurridos, dias_requeridos)
            
            return True
        except Exception as e:
            logger.error(f"Error al actualizar progreso: {e}")
            return False
            
    def _verificar_hitos(self, challenge_id: int, profit_actual: float, profit_objetivo: float):
        """Verifica y registra hitos alcanzados."""
        try:
            # Hito 50%
            if profit_actual >= profit_objetivo * 0.5:
                self._registrar_hito(challenge_id, 'profit_50%', profit_objetivo * 0.5, profit_actual)
                
            # Hito 75%
            if profit_actual >= profit_objetivo * 0.75:
                self._registrar_hito(challenge_id, 'profit_75%', profit_objetivo * 0.75, profit_actual)
                
            # Hito 100%
            if profit_actual >= profit_objetivo:
                self._registrar_hito(challenge_id, 'profit_100%', profit_objetivo, profit_actual)
                
        except Exception as e:
            logger.error(f"Error al verificar hitos: {e}")
            
    def _registrar_hito(self, challenge_id: int, hito_tipo: str, hito_valor: float, hito_actual: float):
        """Registra un hito alcanzado."""
        try:
            # Verificar si ya existe
            self.cursor.execute("""
                SELECT id FROM challenge_hitos
                WHERE challenge_id = ? AND hito_tipo = ?
            """, (challenge_id, hito_tipo))
            
            if self.cursor.fetchone():
                return  # Ya registrado
                
            self.cursor.execute("""
                INSERT INTO challenge_hitos (challenge_id, hito_tipo, hito_valor, hito_actual, fecha_alcanzado)
                VALUES (?, ?, ?, ?, ?)
            """, (challenge_id, hito_tipo, hito_valor, hito_actual, datetime.now().isoformat()))
            
            self.conn.commit()
            logger.info(f"Hito {hito_tipo} registrado para challenge {challenge_id}")
            
            # Crear alerta
            self._crear_alerta(challenge_id, 'HITO', f"Hito alcanzado: {hito_tipo}")
            
        except Exception as e:
            logger.error(f"Error al registrar hito: {e}")
            
    def _evaluar_estado(self, challenge_id: int, profit_actual: float, profit_objetivo: float,
                       drawdown_actual: float, drawdown_max: float, dias_transcurridos: int,
                       dias_requeridos: int):
        """Evalúa el estado del challenge."""
        try:
            estado_actual = None
            mensaje = ""
            
            # Verificar si pasó
            if profit_actual >= profit_objetivo and dias_transcurridos <= dias_requeridos:
                estado_actual = 'APROBADO'
                mensaje = "Challenge aprobado - Profit objetivo alcanzado"
                self._crear_alerta(challenge_id, 'APROBADO', mensaje)
                
            # Verificar si falló por drawdown
            elif drawdown_actual >= drawdown_max:
                estado_actual = 'FALLADO_DD'
                mensaje = f"Challenge fallado - Drawdown excedido: {drawdown_actual:.2f}/{drawdown_max:.2f}"
                self._crear_alerta(challenge_id, 'FALLADO', mensaje)
                
            # Verificar si falló por tiempo
            elif dias_transcurridos > dias_requeridos:
                estado_actual = 'FALLADO_TIEMPO'
                mensaje = f"Challenge fallado - Días excedidos: {dias_transcurridos}/{dias_requeridos}"
                self._crear_alerta(challenge_id, 'FALLADO', mensaje)
                
            # Actualizar estado si cambió
            if estado_actual:
                self.cursor.execute("""
                    UPDATE challenges SET estado = ?, fecha_fin = ?, observaciones = ?
                    WHERE id = ?
                """, (estado_actual, datetime.now().isoformat(), mensaje, challenge_id))
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"Error al evaluar estado: {e}")
            
    def _crear_alerta(self, challenge_id: int, tipo_alerta: str, mensaje: str):
        """Crea una alerta para el challenge."""
        try:
            self.cursor.execute("""
                INSERT INTO challenge_alertas (challenge_id, tipo_alerta, mensaje)
                VALUES (?, ?, ?)
            """, (challenge_id, tipo_alerta, mensaje))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear alerta: {e}")
            
    def obtener_challenge(self, challenge_id: int) -> Optional[Dict]:
        """
        Obtiene información de un challenge.
        
        Args:
            challenge_id: ID del challenge
            
        Returns:
            Diccionario con información del challenge o None
        """
        try:
            self.cursor.execute("""
                SELECT * FROM challenges WHERE id = ?
            """, (challenge_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'cliente_id': result[1],
                    'cliente_nombre': result[2],
                    'propfirm': result[3],
                    'cuenta_challenge': result[4],
                    'tipo_challenge': result[5],
                    'balance_inicial': result[6],
                    'balance_actual': result[7],
                    'profit_objetivo': result[8],
                    'profit_actual': result[9],
                    'drawdown_max': result[10],
                    'drawdown_actual': result[11],
                    'dias_requeridos': result[12],
                    'dias_transcurridos': result[13],
                    'estado': result[14],
                    'fecha_inicio': result[15],
                    'fecha_fin': result[16],
                    'cuenta_fondeada': result[17],
                    'observaciones': result[18]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener challenge: {e}")
            return None
            
    def obtener_challenges_cliente(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene todos los challenges de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de challenges del cliente
        """
        try:
            self.cursor.execute("""
                SELECT * FROM challenges WHERE cliente_id = ? ORDER BY fecha_inicio DESC
            """, (cliente_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2], 'propfirm': r[3],
                'cuenta_challenge': r[4], 'tipo_challenge': r[5], 'balance_inicial': r[6],
                'balance_actual': r[7], 'profit_objetivo': r[8], 'profit_actual': r[9],
                'drawdown_max': r[10], 'drawdown_actual': r[11], 'dias_requeridos': r[12],
                'dias_transcurridos': r[13], 'estado': r[14], 'fecha_inicio': r[15],
                'fecha_fin': r[16], 'cuenta_fondeada': r[17], 'observaciones': r[18]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener challenges del cliente: {e}")
            return []
            
    def obtener_challenges_activos(self) -> List[Dict]:
        """
        Obtiene todos los challenges activos.
        
        Returns:
            Lista de challenges activos
        """
        try:
            self.cursor.execute("""
                SELECT * FROM challenges WHERE estado = 'ACTIVO' ORDER BY fecha_inicio DESC
            """)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'cliente_id': r[1], 'cliente_nombre': r[2], 'propfirm': r[3],
                'cuenta_challenge': r[4], 'tipo_challenge': r[5], 'balance_inicial': r[6],
                'balance_actual': r[7], 'profit_objetivo': r[8], 'profit_actual': r[9],
                'drawdown_max': r[10], 'drawdown_actual': r[11], 'dias_requeridos': r[12],
                'dias_transcurridos': r[13], 'estado': r[14], 'fecha_inicio': r[15],
                'fecha_fin': r[16], 'cuenta_fondeada': r[17], 'observaciones': r[18]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener challenges activos: {e}")
            return []
            
    def obtener_alertas(self, challenge_id: int, no_leidas: bool = False) -> List[Dict]:
        """
        Obtiene alertas de un challenge.
        
        Args:
            challenge_id: ID del challenge
            no_leidas: Solo alertas no leídas
            
        Returns:
            Lista de alertas
        """
        try:
            if no_leidas:
                self.cursor.execute("""
                    SELECT * FROM challenge_alertas
                    WHERE challenge_id = ? AND leida = FALSE
                    ORDER BY fecha DESC
                """, (challenge_id,))
            else:
                self.cursor.execute("""
                    SELECT * FROM challenge_alertas
                    WHERE challenge_id = ?
                    ORDER BY fecha DESC
                """, (challenge_id,))
                
            results = self.cursor.fetchall()
            return [{'id': r[0], 'challenge_id': r[1], 'tipo_alerta': r[2],
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
                UPDATE challenge_alertas SET leida = TRUE WHERE id = ?
            """, (alerta_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al marcar alerta como leída: {e}")
            return False
            
    def transicionar_fondeado(self, challenge_id: int, cuenta_fondeada: str) -> bool:
        """
        Transiciona un challenge aprobado a cuenta fondeada.
        
        Args:
            challenge_id: ID del challenge
            cuenta_fondeada: Número de cuenta fondeada
            
        Returns:
            True si se transicionó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE challenges
                SET cuenta_fondeada = ?, estado = 'FONDEADO'
                WHERE id = ? AND estado = 'APROBADO'
            """, (cuenta_fondeada, challenge_id))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Challenge {challenge_id} transicionado a fondeado - cuenta: {cuenta_fondeada}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al transicionar a fondeado: {e}")
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
    
    agente = AgenteChallenge()
    
    # Ejemplo: crear challenge
    challenge_id = agente.crear_challenge(
        cliente_id="CLI001",
        cliente_nombre="Juan Pérez",
        propfirm="FTMO",
        cuenta_challenge="123456",
        tipo_challenge="10k",
        balance_inicial=10000,
        profit_objetivo=1000,
        drawdown_max=500,
        dias_requeridos=30
    )
    
    print(f"Challenge creado - ID: {challenge_id}")
    
    # Ejemplo: actualizar progreso
    agente.actualizar_progreso(
        challenge_id=challenge_id,
        balance_actual=10500,
        drawdown_actual=200,
        dias_transcurridos=15
    )
    
    # Ejemplo: obtener challenges activos
    activos = agente.obtener_challenges_activos()
    print(f"Challenges activos: {len(activos)}")
    
    # Ejemplo: obtener alertas
    alertas = agente.obtener_alertas(challenge_id)
    print(f"Alertas: {len(alertas)}")
    
    agente.cerrar()

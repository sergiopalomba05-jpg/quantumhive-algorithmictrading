"""
Agente Pricing - D8: Biblioteca Fábrica de Bots
Gestiona precios y licencias de bots

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Define y gestiona los precios de los bots, licencias,
             modelos de pago y descuentos para la venta de bots.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgentePricing:
    """Gestiona precios y licencias de bots."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de pricing.
        
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
                CREATE TABLE IF NOT EXISTS productos_bot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    categoria TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS planes_precio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    nombre_plan TEXT NOT NULL,
                    tipo_precio TEXT NOT NULL,
                    precio_base REAL NOT NULL,
                    moneda TEXT DEFAULT 'USD',
                    periodicidad TEXT,
                    caracteristicas TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (bot_id) REFERENCES productos_bot(bot_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS licencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    plan_id INTEGER NOT NULL,
                    cliente_id TEXT NOT NULL,
                    tipo_licencia TEXT NOT NULL,
                    fecha_inicio DATETIME NOT NULL,
                    fecha_fin DATETIME,
                    estado TEXT NOT NULL,
                    FOREIGN KEY (bot_id) REFERENCES productos_bot(bot_id),
                    FOREIGN KEY (plan_id) REFERENCES planes_precio(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS descuentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    porcentaje REAL NOT NULL,
                    tipo_descuento TEXT NOT NULL,
                    bot_id TEXT,
                    fecha_inicio DATETIME NOT NULL,
                    fecha_fin DATETIME NOT NULL,
                    usos_maximos INTEGER,
                    usos_actuales INTEGER DEFAULT 0,
                    activo BOOLEAN DEFAULT TRUE
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    plan_id INTEGER NOT NULL,
                    cliente_id TEXT NOT NULL,
                    monto REAL NOT NULL,
                    moneda TEXT DEFAULT 'USD',
                    descuento_aplicado REAL DEFAULT 0,
                    monto_final REAL NOT NULL,
                    metodo_pago TEXT NOT NULL,
                    fecha_venta DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_producto_bot(self, bot_id: str, nombre: str, descripcion: str,
                          categoria: str) -> int:
        """
        Crea un producto de bot.
        
        Args:
            bot_id: ID del bot
            nombre: Nombre del bot
            descripcion: Descripción
            categoria: Categoría
            
        Returns:
            ID del producto
        """
        try:
            self.cursor.execute("""
                INSERT INTO productos_bot (bot_id, nombre, descripcion, categoria, estado)
                VALUES (?, ?, ?, ?, 'ACTIVO')
            """, (bot_id, nombre, descripcion, categoria))
            
            self.conn.commit()
            producto_id = self.cursor.lastrowid
            logger.info(f"Producto bot creado - ID: {producto_id} - Bot: {nombre}")
            return producto_id
        except Exception as e:
            logger.error(f"Error al crear producto: {e}")
            raise
            
    def crear_plan_precio(self, bot_id: str, nombre_plan: str, tipo_precio: str,
                         precio_base: float, periodicidad: str = None,
                         caracteristicas: dict = None) -> int:
        """
        Crea un plan de precio para un bot.
        
        Args:
            bot_id: ID del bot
            nombre_plan: Nombre del plan
            tipo_precio: Tipo (UNICO, SUSCRIPCION, FREEMIUM)
            precio_base: Precio base
            periodicidad: Periodicidad (MENSUAL, ANUAL)
            caracteristicas: Características del plan
            
        Returns:
            ID del plan
        """
        try:
            caracteristicas_json = json.dumps(caracteristicas) if caracteristicas else None
            
            self.cursor.execute("""
                INSERT INTO planes_precio
                (bot_id, nombre_plan, tipo_precio, precio_base, periodicidad, caracteristicas, activo)
                VALUES (?, ?, ?, ?, ?, ?, TRUE)
            """, (bot_id, nombre_plan, tipo_precio, precio_base, periodicidad, caracteristicas_json))
            
            self.conn.commit()
            plan_id = self.cursor.lastrowid
            logger.info(f"Plan de precio creado - ID: {plan_id} - Plan: {nombre_plan}")
            return plan_id
        except Exception as e:
            logger.error(f"Error al crear plan: {e}")
            raise
            
    def crear_descuento(self, codigo: str, porcentaje: float, tipo_descuento: str,
                       bot_id: str = None, fecha_inicio: datetime = None,
                       fecha_fin: datetime = None, usos_maximos: int = None) -> int:
        """
        Crea un código de descuento.
        
        Args:
            codigo: Código del descuento
            porcentaje: Porcentaje de descuento
            tipo_descuento: Tipo (GENERAL, ESPECIFICO, PRIMERA_COMPRA)
            bot_id: Bot específico (opcional)
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            usos_maximos: Usos máximos
            
        Returns:
            ID del descuento
        """
        try:
            if not fecha_inicio:
                fecha_inicio = datetime.now()
            if not fecha_fin:
                from datetime import timedelta
                fecha_fin = fecha_inicio + timedelta(days=30)
                
            self.cursor.execute("""
                INSERT INTO descuentos
                (codigo, porcentaje, tipo_descuento, bot_id, fecha_inicio, fecha_fin, usos_maximos, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (codigo, porcentaje, tipo_descuento, bot_id, fecha_inicio.isoformat(),
                  fecha_fin.isoformat(), usos_maximos))
            
            self.conn.commit()
            descuento_id = self.cursor.lastrowid
            logger.info(f"Descuento creado - ID: {descuento_id} - Código: {codigo}")
            return descuento_id
        except Exception as e:
            logger.error(f"Error al crear descuento: {e}")
            raise
            
    def emitir_licencia(self, bot_id: str, plan_id: int, cliente_id: str,
                       tipo_licencia: str, fecha_inicio: datetime,
                       fecha_fin: datetime = None) -> int:
        """
        Emite una licencia para un bot.
        
        Args:
            bot_id: ID del bot
            plan_id: ID del plan
            cliente_id: ID del cliente
            tipo_licencia: Tipo (PERPETUA, TEMPORAL, TRIAL)
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            ID de la licencia
        """
        try:
            self.cursor.execute("""
                INSERT INTO licencias
                (bot_id, plan_id, cliente_id, tipo_licencia, fecha_inicio, fecha_fin, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVA')
            """, (bot_id, plan_id, cliente_id, tipo_licencia, fecha_inicio.isoformat(),
                  fecha_fin.isoformat() if fecha_fin else None))
            
            self.conn.commit()
            licencia_id = self.cursor.lastrowid
            logger.info(f"Licencia emitida - ID: {licencia_id} - Cliente: {cliente_id}")
            return licencia_id
        except Exception as e:
            logger.error(f"Error al emitir licencia: {e}")
            raise
            
    def registrar_venta(self, bot_id: str, plan_id: int, cliente_id: str,
                       monto: float, metodo_pago: str, descuento: float = 0) -> int:
        """
        Registra una venta.
        
        Args:
            bot_id: ID del bot
            plan_id: ID del plan
            cliente_id: ID del cliente
            monto: Monto original
            metodo_pago: Método de pago
            descuento: Descuento aplicado
            
        Returns:
            ID de la venta
        """
        try:
            monto_final = monto - (monto * descuento / 100)
            
            self.cursor.execute("""
                INSERT INTO ventas
                (bot_id, plan_id, cliente_id, monto, descuento_aplicado, monto_final, metodo_pago, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'COMPLETADA')
            """, (bot_id, plan_id, cliente_id, monto, descuento, monto_final, metodo_pago))
            
            self.conn.commit()
            venta_id = self.cursor.lastrowid
            logger.info(f"Venta registrada - ID: {venta_id} - Monto: {monto_final}")
            return venta_id
        except Exception as e:
            logger.error(f"Error al registrar venta: {e}")
            raise
            
    def aplicar_descuento(self, codigo: str, bot_id: str = None) -> Optional[float]:
        """
        Aplica un código de descuento y retorna el porcentaje.
        
        Args:
            codigo: Código del descuento
            bot_id: Bot específico
            
        Returns:
            Porcentaje de descuento o None si no es válido
        """
        try:
            self.cursor.execute("""
                SELECT porcentaje, usos_maximos, usos_actuales, fecha_fin, bot_id
                FROM descuentos WHERE codigo = ? AND activo = TRUE
            """, (codigo,))
            
            result = self.cursor.fetchone()
            if not result:
                return None
                
            porcentaje, usos_maximos, usos_actuales, fecha_fin, descuento_bot_id = result
            
            # Verificar fecha
            if datetime.now() > datetime.fromisoformat(fecha_fin):
                return None
                
            # Verificar bot específico
            if descuento_bot_id and descuento_bot_id != bot_id:
                return None
                
            # Verificar usos
            if usos_maximos and usos_actuales >= usos_maximos:
                return None
                
            # Incrementar usos
            self.cursor.execute("""
                UPDATE descuentos SET usos_actuales = usos_actuales + 1 WHERE codigo = ?
            """, (codigo,))
            self.conn.commit()
            
            return porcentaje
        except Exception as e:
            logger.error(f"Error al aplicar descuento: {e}")
            return None
            
    def obtener_planes_bot(self, bot_id: str) -> List[Dict]:
        """Obtiene los planes de precio de un bot."""
        try:
            self.cursor.execute("""
                SELECT * FROM planes_precio WHERE bot_id = ? AND activo = TRUE
            """, (bot_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'bot_id': r[1], 'nombre_plan': r[2], 'tipo_precio': r[3],
                'precio_base': r[4], 'moneda': r[5], 'periodicidad': r[6],
                'caracteristicas': json.loads(r[7]) if r[7] else None, 'activo': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener planes: {e}")
            return []
            
    def obtener_licencias_cliente(self, cliente_id: str) -> List[Dict]:
        """Obtiene las licencias de un cliente."""
        try:
            self.cursor.execute("""
                SELECT * FROM licencias WHERE cliente_id = ? AND estado = 'ACTIVA'
                ORDER BY fecha_inicio DESC
            """, (cliente_id,))
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'bot_id': r[1], 'plan_id': r[2], 'cliente_id': r[3],
                'tipo_licencia': r[4], 'fecha_inicio': r[5], 'fecha_fin': r[6],
                'estado': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener licencias: {e}")
            return []
            
    def obtener_ventas(self, bot_id: str = None, dias: int = 30) -> List[Dict]:
        """Obtiene ventas."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            if bot_id:
                self.cursor.execute("""
                    SELECT * FROM ventas WHERE bot_id = ? AND fecha_venta >= ?
                    ORDER BY fecha_venta DESC
                """, (bot_id, fecha_limite.isoformat()))
            else:
                self.cursor.execute("""
                    SELECT * FROM ventas WHERE fecha_venta >= ? ORDER BY fecha_venta DESC
                """, (fecha_limite.isoformat(),))
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'bot_id': r[1], 'plan_id': r[2], 'cliente_id': r[3],
                'monto': r[4], 'moneda': r[5], 'descuento_aplicado': r[6],
                'monto_final': r[7], 'metodo_pago': r[8], 'fecha_venta': r[9],
                'estado': r[10]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener ventas: {e}")
            return []
            
    def obtener_estadisticas_ventas(self, bot_id: str = None, dias: int = 30) -> Dict:
        """Obtiene estadísticas de ventas."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            if bot_id:
                self.cursor.execute("""
                    SELECT 
                        COUNT(*) as total_ventas,
                        SUM(monto_final) as total_revenue,
                        AVG(monto_final) as avg_ticket,
                        SUM(CASE WHEN descuento_aplicado > 0 THEN 1 ELSE 0 END) as ventas_con_descuento
                    FROM ventas
                    WHERE bot_id = ? AND fecha_venta >= ? AND estado = 'COMPLETADA'
                """, (bot_id, fecha_limite.isoformat()))
            else:
                self.cursor.execute("""
                    SELECT 
                        COUNT(*) as total_ventas,
                        SUM(monto_final) as total_revenue,
                        AVG(monto_final) as avg_ticket,
                        SUM(CASE WHEN descuento_aplicado > 0 THEN 1 ELSE 0 END) as ventas_con_descuento
                    FROM ventas
                    WHERE fecha_venta >= ? AND estado = 'COMPLETADA'
                """, (fecha_limite.isoformat(),))
                
            result = self.cursor.fetchone()
            
            if result:
                total, revenue, avg_ticket, con_descuento = result
                return {
                    'total_ventas': total or 0,
                    'total_revenue': revenue or 0,
                    'avg_ticket': round(avg_ticket or 0, 2),
                    'ventas_con_descuento': con_descuento or 0,
                    'tasa_descuento': round((con_descuento / total * 100) if total > 0 else 0, 2),
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
    
    agente = AgentePricing()
    
    # Ejemplo: crear producto
    producto_id = agente.crear_producto_bot(
        bot_id="BOT-001",
        nombre="Bot Scalping Pro",
        descripcion="Bot de scalping para EURUSD",
        categoria="SCALPING"
    )
    
    print(f"Producto creado - ID: {producto_id}")
    
    # Ejemplo: crear plan
    plan_id = agente.crear_plan_precio(
        bot_id="BOT-001",
        nombre_plan="Premium",
        tipo_precio="SUSCRIPCION",
        precio_base=99.99,
        periodicidad="MENSUAL",
        caracteristicas={"soporte": "24/7", "actualizaciones": True, "backtesting": True}
    )
    
    print(f"Plan creado - ID: {plan_id}")
    
    # Ejemplo: crear descuento
    descuento_id = agente.crear_descuento(
        codigo="LAUNCH20",
        porcentaje=20,
        tipo_descuento="GENERAL"
    )
    
    print(f"Descuento creado - ID: {descuento_id}")
    
    # Ejemplo: emitir licencia
    licencia_id = agente.emitir_licencia(
        bot_id="BOT-001",
        plan_id=plan_id,
        cliente_id="CLI-001",
        tipo_licencia="TEMPORAL",
        fecha_inicio=datetime.now(),
        fecha_fin=datetime.now().replace(year=datetime.now().year + 1)
    )
    
    print(f"Licencia emitida - ID: {licencia_id}")
    
    # Ejemplo: registrar venta
    venta_id = agente.registrar_venta(
        bot_id="BOT-001",
        plan_id=plan_id,
        cliente_id="CLI-001",
        monto=99.99,
        metodo_pago="CRYPTO",
        descuento=20
    )
    
    print(f"Venta registrada - ID: {venta_id}")
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas_ventas()
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

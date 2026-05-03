"""
Agente Sala Visual - D16: Sala de Inversión Colmena
Dashboard visual para monitoreo en tiempo real

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Genera y gestiona datos para el dashboard visual de la Sala
             de Inversión, mostrando métricas, KPIs y alertas en tiempo real.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteSalaVisual:
    """Gestiona el dashboard visual de la Sala de Inversión."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de sala visual.
        
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
                CREATE TABLE IF NOT EXISTS kpis_sala (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    tipo TEXT NOT NULL,
                    valor_actual REAL NOT NULL,
                    valor_objetivo REAL,
                    unidad TEXT,
                    estado TEXT NOT NULL,
                    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas_tiempo_real (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    propfirm TEXT NOT NULL,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    drawdown_actual REAL NOT NULL,
                    profit_dia REAL NOT NULL,
                    profit_semana REAL NOT NULL,
                    profit_mes REAL NOT NULL,
                    posiciones_abiertas INTEGER NOT NULL,
                    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS alertas_sala (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_alerta TEXT NOT NULL,
                    severidad TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    cuenta TEXT,
                    propfirm TEXT,
                    fecha_alerta DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS widgets_dashboard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    tipo_widget TEXT NOT NULL,
                    configuracion TEXT NOT NULL,
                    posicion_x INTEGER NOT NULL,
                    posicion_y INTEGER NOT NULL,
                    ancho INTEGER NOT NULL,
                    alto INTEGER NOT NULL,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_sesiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_sesion DATETIME NOT NULL,
                    capital_total REAL NOT NULL,
                    ganancias_dia REAL NOT NULL,
                    cuentas_activas INTEGER NOT NULL,
                    alertas_generadas INTEGER NOT NULL,
                    duracion_sesion_minutos INTEGER NOT NULL
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_kpi(self, nombre: str, tipo: str, valor_actual: float,
                     valor_objetivo: float = None, unidad: str = None) -> int:
        """
        Registra o actualiza un KPI.
        
        Args:
            nombre: Nombre del KPI
            tipo: Tipo de KPI (FINANCIERO, OPERATIVO, RIESGO)
            valor_actual: Valor actual
            valor_objetivo: Valor objetivo
            unidad: Unidad de medida
            
        Returns:
            ID del KPI
        """
        try:
            # Verificar si existe
            self.cursor.execute("""
                SELECT id FROM kpis_sala WHERE nombre = ?
            """, (nombre,))
            existe = self.cursor.fetchone()
            
            estado = self._calcular_estado_kpi(valor_actual, valor_objetivo)
            
            if existe:
                self.cursor.execute("""
                    UPDATE kpis_sala
                    SET tipo = ?, valor_actual = ?, valor_objetivo = ?, unidad = ?, estado = ?,
                        ultima_actualizacion = ?
                    WHERE nombre = ?
                """, (tipo, valor_actual, valor_objetivo, unidad, estado,
                      datetime.now().isoformat(), nombre))
                kpi_id = existe[0]
            else:
                self.cursor.execute("""
                    INSERT INTO kpis_sala
                    (nombre, tipo, valor_actual, valor_objetivo, unidad, estado)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nombre, tipo, valor_actual, valor_objetivo, unidad, estado))
                self.conn.commit()
                kpi_id = self.cursor.lastrowid
                
            self.conn.commit()
            logger.info(f"KPI registrado/actualizado - ID: {kpi_id} - Nombre: {nombre}")
            return kpi_id
        except Exception as e:
            logger.error(f"Error al registrar KPI: {e}")
            raise
            
    def _calcular_estado_kpi(self, valor_actual: float, valor_objetivo: float) -> str:
        """Calcula el estado de un KPI."""
        if valor_objetivo is None:
            return 'NEUTRAL'
        elif valor_actual >= valor_objetivo:
            return 'POSITIVO'
        elif valor_actual >= valor_objetivo * 0.8:
            return 'ADVERTENCIA'
        else:
            return 'CRITICO'
            
    def actualizar_metrica_tiempo_real(self, cuenta: str, propfirm: str, balance: float,
                                     equity: float, drawdown: float, profit_dia: float,
                                     profit_semana: float, profit_mes: float,
                                     posiciones_abiertas: int) -> int:
        """
        Actualiza métricas en tiempo real de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Propfirm
            balance: Balance actual
            equity: Equity actual
            drawdown: Drawdown actual
            profit_dia: Profit del día
            profit_semana: Profit de la semana
            profit_mes: Profit del mes
            posiciones_abiertas: Posiciones abiertas
            
        Returns:
            ID de la métrica
        """
        try:
            # Verificar si existe
            self.cursor.execute("""
                SELECT id FROM metricas_tiempo_real WHERE cuenta = ?
            """, (cuenta,))
            existe = self.cursor.fetchone()
            
            if existe:
                self.cursor.execute("""
                    UPDATE metricas_tiempo_real
                    SET propfirm = ?, balance = ?, equity = ?, drawdown_actual = ?,
                        profit_dia = ?, profit_semana = ?, profit_mes = ?,
                        posiciones_abiertas = ?, ultima_actualizacion = ?
                    WHERE cuenta = ?
                """, (propfirm, balance, equity, drawdown, profit_dia, profit_semana,
                      profit_mes, posiciones_abiertas, datetime.now().isoformat(), cuenta))
                metrica_id = existe[0]
            else:
                self.cursor.execute("""
                    INSERT INTO metricas_tiempo_real
                    (cuenta, propfirm, balance, equity, drawdown_actual, profit_dia,
                     profit_semana, profit_mes, posiciones_abiertas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cuenta, propfirm, balance, equity, drawdown, profit_dia,
                      profit_semana, profit_mes, posiciones_abiertas))
                self.conn.commit()
                metrica_id = self.cursor.lastrowid
                
            self.conn.commit()
            logger.debug(f"Métrica actualizada - Cuenta: {cuenta}")
            return metrica_id
        except Exception as e:
            logger.error(f"Error al actualizar métrica: {e}")
            raise
            
    def generar_alerta(self, tipo_alerta: str, severidad: str, mensaje: str,
                       cuenta: str = None, propfirm: str = None) -> int:
        """
        Genera una alerta para la sala.
        
        Args:
            tipo_alerta: Tipo de alerta (DRAWDOWN, RIESGO, OPERATIVO, SISTEMA)
            severidad: Severidad (INFO, WARNING, CRITICAL)
            mensaje: Mensaje de la alerta
            cuenta: Cuenta relacionada (opcional)
            propfirm: Propfirm relacionada (opcional)
            
        Returns:
            ID de la alerta
        """
        try:
            self.cursor.execute("""
                INSERT INTO alertas_sala
                (tipo_alerta, severidad, mensaje, cuenta, propfirm, estado)
                VALUES (?, ?, ?, ?, ?, 'ACTIVA')
            """, (tipo_alerta, severidad, mensaje, cuenta, propfirm))
            
            self.conn.commit()
            alerta_id = self.cursor.lastrowid
            logger.warning(f"Alerta generada - ID: {alerta_id} - Tipo: {tipo_alerta} - {mensaje}")
            return alerta_id
        except Exception as e:
            logger.error(f"Error al generar alerta: {e}")
            raise
            
    def crear_widget(self, nombre: str, tipo_widget: str, configuracion: dict,
                    posicion_x: int, posicion_y: int, ancho: int, alto: int) -> int:
        """
        Crea un widget para el dashboard.
        
        Args:
            nombre: Nombre del widget
            tipo_widget: Tipo de widget (GRAFICA, TABLA, TARJETA, ALERTAS)
            configuracion: Configuración del widget (dict)
            posicion_x: Posición X
            posicion_y: Posición Y
            ancho: Ancho
            alto: Alto
            
        Returns:
            ID del widget
        """
        try:
            configuracion_json = json.dumps(configuracion)
            
            self.cursor.execute("""
                INSERT INTO widgets_dashboard
                (nombre, tipo_widget, configuracion, posicion_x, posicion_y, ancho, alto, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVO')
            """, (nombre, tipo_widget, configuracion_json, posicion_x, posicion_y,
                  ancho, alto))
            
            self.conn.commit()
            widget_id = self.cursor.lastrowid
            logger.info(f"Widget creado - ID: {widget_id} - Nombre: {nombre}")
            return widget_id
        except Exception as e:
            logger.error(f"Error al crear widget: {e}")
            raise
            
    def obtener_kpis(self, tipo: str = None) -> List[Dict]:
        """Obtiene los KPIs registrados."""
        try:
            if tipo:
                self.cursor.execute("""
                    SELECT * FROM kpis_sala WHERE tipo = ? ORDER BY ultima_actualizacion DESC
                """, (tipo,))
            else:
                self.cursor.execute("""
                    SELECT * FROM kpis_sala ORDER BY ultima_actualizacion DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'nombre': r[1], 'tipo': r[2], 'valor_actual': r[3],
                'valor_objetivo': r[4], 'unidad': r[5], 'estado': r[6],
                'ultima_actualizacion': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener KPIs: {e}")
            return []
            
    def obtener_metricas_tiempo_real(self) -> List[Dict]:
        """Obtiene las métricas en tiempo real de todas las cuentas."""
        try:
            self.cursor.execute("""
                SELECT * FROM metricas_tiempo_real ORDER BY ultima_actualizacion DESC
            """)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'cuenta': r[1], 'propfirm': r[2], 'balance': r[3],
                'equity': r[4], 'drawdown_actual': r[5], 'profit_dia': r[6],
                'profit_semana': r[7], 'profit_mes': r[8], 'posiciones_abiertas': r[9],
                'ultima_actualizacion': r[10]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener métricas tiempo real: {e}")
            return []
            
    def obtener_alertas_activas(self, severidad: str = None) -> List[Dict]:
        """Obtiene las alertas activas."""
        try:
            if severidad:
                self.cursor.execute("""
                    SELECT * FROM alertas_sala WHERE estado = 'ACTIVA' AND severidad = ?
                    ORDER BY fecha_alerta DESC
                """, (severidad,))
            else:
                self.cursor.execute("""
                    SELECT * FROM alertas_sala WHERE estado = 'ACTIVA'
                    ORDER BY fecha_alerta DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'tipo_alerta': r[1], 'severidad': r[2], 'mensaje': r[3],
                'cuenta': r[4], 'propfirm': r[5], 'fecha_alerta': r[6], 'estado': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener alertas: {e}")
            return []
            
    def obtener_widgets(self) -> List[Dict]:
        """Obtiene los widgets del dashboard."""
        try:
            self.cursor.execute("""
                SELECT * FROM widgets_dashboard WHERE estado = 'ACTIVO' ORDER BY posicion_y, posicion_x
            """)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'nombre': r[1], 'tipo_widget': r[2],
                'configuracion': json.loads(r[3]), 'posicion_x': r[4],
                'posicion_y': r[5], 'ancho': r[6], 'alto': r[7], 'estado': r[8]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener widgets: {e}")
            return []
            
    def obtener_resumen_dashboard(self) -> Dict:
        """Obtiene un resumen completo para el dashboard."""
        try:
            kpis = self.obtener_kpis()
            metricas = self.obtener_metricas_tiempo_real()
            alertas = self.obtener_alertas_activas()
            widgets = self.obtener_widgets()
            
            # Calcular agregados
            total_balance = sum(m['balance'] for m in metricas)
            total_equity = sum(m['equity'] for m in metricas)
            total_profit_dia = sum(m['profit_dia'] for m in metricas)
            total_cuentas = len(metricas)
            alertas_criticas = len([a for a in alertas if a['severidad'] == 'CRITICAL'])
            
            return {
                'kpis': kpis,
                'metricas_tiempo_real': metricas,
                'alertas': alertas,
                'widgets': widgets,
                'resumen': {
                    'total_balance': total_balance,
                    'total_equity': total_equity,
                    'total_profit_dia': total_profit_dia,
                    'total_cuentas': total_cuentas,
                    'alertas_criticas': alertas_criticas,
                    'alertas_activas': len(alertas)
                }
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen dashboard: {e}")
            return {}
            
    def marcar_alerta_resuelta(self, alerta_id: int) -> bool:
        """
        Marca una alerta como resuelta.
        
        Args:
            alerta_id: ID de la alerta
            
        Returns:
            True si se marcó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE alertas_sala SET estado = 'RESUELTA' WHERE id = ?
            """, (alerta_id,))
            self.conn.commit()
            logger.info(f"Alerta {alerta_id} marcada como resuelta")
            return True
        except Exception as e:
            logger.error(f"Error al marcar alerta resuelta: {e}")
            return False
            
    def limpiar_alertas_antiguas(self, dias: int = 7) -> int:
        """
        Limpia alertas antiguas.
        
        Args:
            dias: Días de antigüedad
            
        Returns:
            Cantidad de alertas limpiadas
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                UPDATE alertas_sala SET estado = 'ARCHIVADA'
                WHERE fecha_alerta < ? AND estado = 'ACTIVA'
            """, (fecha_limite.isoformat(),))
            
            self.conn.commit()
            count = self.cursor.rowcount
            logger.info(f"{count} alertas antiguas archivadas")
            return count
        except Exception as e:
            logger.error(f"Error al limpiar alertas: {e}")
            return 0
            
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
    
    agente = AgenteSalaVisual()
    
    # Ejemplo: registrar KPIs
    agente.registrar_kpi("Capital Total", "FINANCIERO", 150000, 200000, "USD")
    agente.registrar_kpi("Ganancias Diarias", "FINANCIERO", 2500, 3000, "USD")
    agente.registrar_kpi("Cuentas Activas", "OPERATIVO", 25, 30, "cuentas")
    
    print("KPIs registrados")
    
    # Ejemplo: actualizar métricas
    agente.actualizar_metrica_tiempo_real(
        cuenta="123456", propfirm="FTMO", balance=10000, equity=10250,
        drawdown=2.5, profit_dia=250, profit_semana=800, profit_mes=2500,
        posiciones_abiertas=2
    )
    
    print("Métricas actualizadas")
    
    # Ejemplo: generar alerta
    agente.generar_alerta("DRAWDOWN", "WARNING", "Cuenta 123456 supera 5% drawdown", "123456", "FTMO")
    
    print("Alerta generada")
    
    # Ejemplo: crear widget
    agente.crear_widget(
        nombre="Grafica Capital",
        tipo_widget="GRAFICA",
        configuracion={"tipo": "linea", "datos": "capital"},
        posicion_x=0, posicion_y=0, ancho=6, alto=4
    )
    
    print("Widget creado")
    
    # Ejemplo: obtener resumen
    resumen = agente.obtener_resumen_dashboard()
    print(f"Resumen dashboard: {resumen['resumen']}")
    
    agente.cerrar()

"""
Agente Distribución Ganancias - D16: Sala de Inversión Colmena
Distribuye ganancias entre inversores y QuantumHive

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Calcula y distribuye las ganancias entre los inversores
             y QuantumHive según los porcentajes establecidos.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteDistribucionGanancias:
    """Distribuye ganancias entre inversores y QuantumHive."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de distribución de ganancias.
        
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
                CREATE TABLE IF NOT EXISTS reglas_distribucion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    porcentaje_quantumhive REAL NOT NULL,
                    porcentaje_inversores REAL NOT NULL,
                    retencion_impuestos REAL DEFAULT 0,
                    comision_gestion REAL DEFAULT 0,
                    estado TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS periodos_distribucion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    periodo TEXT NOT NULL,
                    fecha_inicio DATETIME NOT NULL,
                    fecha_fin DATETIME NOT NULL,
                    ganancias_totales REAL NOT NULL,
                    capital_base REAL NOT NULL,
                    rendimiento_porcentaje REAL NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS distribuciones_realizadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo_id INTEGER NOT NULL,
                    inversor_id TEXT NOT NULL,
                    nombre_inversor TEXT NOT NULL,
                    porcentaje_participacion REAL NOT NULL,
                    ganancia_asignada REAL NOT NULL,
                    monto_distribuido REAL NOT NULL,
                    estado_pago TEXT NOT NULL,
                    fecha_pago DATETIME,
                    metodo_pago TEXT,
                    FOREIGN KEY (periodo_id) REFERENCES periodos_distribucion(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS distribuciones_quantumhive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo_id INTEGER NOT NULL,
                    concepto TEXT NOT NULL,
                    porcentaje REAL NOT NULL,
                    monto REAL NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_pago DATETIME,
                    FOREIGN KEY (periodo_id) REFERENCES periodos_distribucion(id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_pagos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo_id INTEGER NOT NULL,
                    beneficiario TEXT NOT NULL,
                    tipo_beneficiario TEXT NOT NULL,
                    monto REAL NOT NULL,
                    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
                    referencia_pago TEXT,
                    FOREIGN KEY (periodo_id) REFERENCES periodos_distribucion(id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_regla_distribucion(self, pool_id: int, porcentaje_qh: float,
                                porcentaje_inversores: float, retencion_impuestos: float = 0,
                                comision_gestion: float = 0) -> int:
        """
        Crea reglas de distribución para un pool.
        
        Args:
            pool_id: ID del pool
            porcentaje_qh: Porcentaje para QuantumHive
            porcentaje_inversores: Porcentaje para inversores
            retencion_impuestos: Retención de impuestos
            comision_gestion: Comisión de gestión
            
        Returns:
            ID de la regla creada
        """
        try:
            self.cursor.execute("""
                INSERT INTO reglas_distribucion
                (pool_id, porcentaje_quantumhive, porcentaje_inversores,
                 retencion_impuestos, comision_gestion, estado)
                VALUES (?, ?, ?, ?, ?, 'ACTIVA')
            """, (pool_id, porcentaje_qh, porcentaje_inversores,
                  retencion_impuestos, comision_gestion))
            
            self.conn.commit()
            regla_id = self.cursor.lastrowid
            logger.info(f"Regla de distribución creada - ID: {regla_id} - Pool: {pool_id}")
            return regla_id
        except Exception as e:
            logger.error(f"Error al crear regla de distribución: {e}")
            raise
            
    def calcular_distribucion_periodo(self, pool_id: int, periodo: str,
                                    fecha_inicio: datetime, fecha_fin: datetime,
                                    ganancias_totales: float, capital_base: float) -> Dict:
        """
        Calcula la distribución de ganancias para un período.
        
        Args:
            pool_id: ID del pool
            periodo: Identificador del período
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            ganancias_totales: Ganancias totales
            capital_base: Capital base
            
        Returns:
            Diccionario con resultado del cálculo
        """
        try:
            # Obtener reglas de distribución
            self.cursor.execute("""
                SELECT porcentaje_quantumhive, porcentaje_inversores, retencion_impuestos, comision_gestion
                FROM reglas_distribucion WHERE pool_id = ? AND estado = 'ACTIVA'
                ORDER BY timestamp DESC LIMIT 1
            """, (pool_id,))
            regla = self.cursor.fetchone()
            
            if not regla:
                return {'exito': False, 'mensaje': 'No hay reglas de distribución activas'}
                
            pct_qh, pct_inv, ret_imp, com_gestion = regla
            
            # Calcular rendimiento
            rendimiento_pct = (ganancias_totales / capital_base * 100) if capital_base > 0 else 0
            
            # Crear período
            self.cursor.execute("""
                INSERT INTO periodos_distribucion
                (pool_id, periodo, fecha_inicio, fecha_fin, ganancias_totales,
                 capital_base, rendimiento_porcentaje, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
            """, (pool_id, periodo, fecha_inicio.isoformat(), fecha_fin.isoformat(),
                  ganancias_totales, capital_base, rendimiento_pct))
            
            self.conn.commit()
            periodo_id = self.cursor.lastrowid
            
            # Calcular deducciones
            impuestos = ganancias_totales * (ret_imp / 100)
            comision = ganancias_totales * (com_gestion / 100)
            ganancias_neta = ganancias_totales - impuestos - comision
            
            # Calcular distribución QH
            ganancia_qh = ganancias_neta * (pct_qh / 100)
            
            # Calcular distribución inversores
            ganancia_inversores = ganancias_neta * (pct_inv / 100)
            
            return {
                'exito': True,
                'periodo_id': periodo_id,
                'ganancias_totales': ganancias_totales,
                'impuestos': impuestos,
                'comision_gestion': comision,
                'ganancias_neta': ganancias_neta,
                'ganancia_qh': ganancia_qh,
                'ganancia_inversores': ganancia_inversores,
                'rendimiento_porcentaje': rendimiento_pct
            }
        except Exception as e:
            logger.error(f"Error al calcular distribución: {e}")
            return {'exito': False, 'mensaje': str(e)}
            
    def distribuir_a_inversores(self, periodo_id: int, inversores: List[Dict]) -> bool:
        """
        Distribuye ganancias a los inversores.
        
        Args:
            periodo_id: ID del período
            inversores: Lista de inversores con sus porcentajes
            
        Returns:
            True si se distribuyó correctamente
        """
        try:
            # Obtener ganancia total para inversores del período
            self.cursor.execute("""
                SELECT ganancias_totales FROM periodos_distribucion WHERE id = ?
            """, (periodo_id,))
            ganancias_totales = self.cursor.fetchone()[0]
            
            # Obtener reglas
            self.cursor.execute("""
                SELECT porcentaje_inversores FROM reglas_distribucion
                WHERE id IN (SELECT regla_id FROM periodos_distribucion WHERE id = ?)
            """, (periodo_id,))
            pct_inv = self.cursor.fetchone()[0]
            
            ganancia_inversores_total = ganancias_totales * (pct_inv / 100)
            
            # Distribuir a cada inversor
            for inversor in inversores:
                porcentaje = inversor['porcentaje_participacion']
                ganancia = ganancia_inversores_total * (porcentaje / 100)
                
                self.cursor.execute("""
                    INSERT INTO distribuciones_realizadas
                    (periodo_id, inversor_id, nombre_inversor, porcentaje_participacion,
                     ganancia_asignada, monto_distribuido, estado_pago)
                    VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE')
                """, (periodo_id, inversor['inversor_id'], inversor['nombre_inversor'],
                      porcentaje, ganancia, ganancia))
                
            self.conn.commit()
            logger.info(f"Distribución a inversores registrada - Período: {periodo_id}")
            return True
        except Exception as e:
            logger.error(f"Error al distribuir a inversores: {e}")
            return False
            
    def distribuir_a_quantumhive(self, periodo_id: int, conceptos: Dict[str, float]) -> bool:
        """
        Distribuye ganancias a QuantumHive por conceptos.
        
        Args:
            periodo_id: ID del período
            conceptos: Diccionario con conceptos y porcentajes
            
        Returns:
            True si se distribuyó correctamente
        """
        try:
            # Obtener ganancia QH del período
            self.cursor.execute("""
                SELECT ganancias_totales FROM periodos_distribucion WHERE id = ?
            """, (periodo_id,))
            ganancias_totales = self.cursor.fetchone()[0]
            
            # Obtener porcentaje QH
            self.cursor.execute("""
                SELECT porcentaje_quantumhive FROM reglas_distribucion
                WHERE id IN (SELECT regla_id FROM periodos_distribucion WHERE id = ?)
            """, (periodo_id,))
            pct_qh = self.cursor.fetchone()[0]
            
            ganancia_qh_total = ganancias_totales * (pct_qh / 100)
            
            # Distribuir por conceptos
            total_porcentaje = sum(conceptos.values())
            
            for concepto, porcentaje in conceptos.items():
                monto = ganancia_qh_total * (porcentaje / total_porcentaje)
                
                self.cursor.execute("""
                    INSERT INTO distribuciones_quantumhive
                    (periodo_id, concepto, porcentaje, monto, estado)
                    VALUES (?, ?, ?, ?, 'PENDIENTE')
                """, (periodo_id, concepto, porcentaje, monto))
                
            self.conn.commit()
            logger.info(f"Distribución a QuantumHive registrada - Período: {periodo_id}")
            return True
        except Exception as e:
            logger.error(f"Error al distribuir a QuantumHive: {e}")
            return False
            
    def registrar_pago(self, periodo_id: int, beneficiario: str, tipo_beneficiario: str,
                      monto: float, referencia: str = None) -> int:
        """
        Registra un pago realizado.
        
        Args:
            periodo_id: ID del período
            beneficiario: Nombre del beneficiario
            tipo_beneficiario: Tipo (INVERSOR, QUANTUMHIVE)
            monto: Monto del pago
            referencia: Referencia del pago
            
        Returns:
            ID del pago registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO historico_pagos
                (periodo_id, beneficiario, tipo_beneficiario, monto, referencia_pago)
                VALUES (?, ?, ?, ?, ?)
            """, (periodo_id, beneficiario, tipo_beneficiario, monto, referencia))
            
            self.conn.commit()
            pago_id = self.cursor.lastrowid
            logger.info(f"Pago registrado - ID: {pago_id} - Beneficiario: {beneficiario}")
            return pago_id
        except Exception as e:
            logger.error(f"Error al registrar pago: {e}")
            raise
            
    def actualizar_estado_pago_inversor(self, distribucion_id: int, estado: str,
                                       fecha_pago: datetime = None, metodo_pago: str = None) -> bool:
        """
        Actualiza el estado de un pago a inversor.
        
        Args:
            distribucion_id: ID de la distribución
            estado: Estado del pago (PENDIENTE, PAGADO, FALLIDO)
            fecha_pago: Fecha del pago
            metodo_pago: Método de pago
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE distribuciones_realizadas
                SET estado_pago = ?, fecha_pago = ?, metodo_pago = ?
                WHERE id = ?
            """, (estado, fecha_pago.isoformat() if fecha_pago else None, metodo_pago,
                  distribucion_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar estado pago: {e}")
            return False
            
    def obtener_periodos(self, pool_id: int = None, estado: str = None) -> List[Dict]:
        """Obtiene períodos de distribución."""
        try:
            query = "SELECT * FROM periodos_distribucion"
            params = []
            
            conditions = []
            if pool_id:
                conditions.append("pool_id = ?")
                params.append(pool_id)
            if estado:
                conditions.append("estado = ?")
                params.append(estado)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY fecha_calculo DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'pool_id': r[1], 'periodo': r[2], 'fecha_inicio': r[3],
                'fecha_fin': r[4], 'ganancias_totales': r[5], 'capital_base': r[6],
                'rendimiento_porcentaje': r[7], 'estado': r[8], 'fecha_calculo': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener períodos: {e}")
            return []
            
    def obtener_distribuciones_periodo(self, periodo_id: int) -> Dict:
        """Obtiene las distribuciones de un período."""
        try:
            # Distribuciones a inversores
            self.cursor.execute("""
                SELECT * FROM distribuciones_realizadas WHERE periodo_id = ?
            """, (periodo_id,))
            inv_results = self.cursor.fetchall()
            
            # Distribuciones a QH
            self.cursor.execute("""
                SELECT * FROM distribuciones_quantumhive WHERE periodo_id = ?
            """, (periodo_id,))
            qh_results = self.cursor.fetchall()
            
            return {
                'inversores': [{
                    'id': r[0], 'periodo_id': r[1], 'inversor_id': r[2],
                    'nombre_inversor': r[3], 'porcentaje_participacion': r[4],
                    'ganancia_asignada': r[5], 'monto_distribuido': r[6],
                    'estado_pago': r[7], 'fecha_pago': r[8], 'metodo_pago': r[9]
                } for r in inv_results],
                'quantumhive': [{
                    'id': r[0], 'periodo_id': r[1], 'concepto': r[2],
                    'porcentaje': r[3], 'monto': r[4], 'estado': r[5], 'fecha_pago': r[6]
                } for r in qh_results]
            }
        except Exception as e:
            logger.error(f"Error al obtener distribuciones: {e}")
            return {}
            
    def obtener_resumen_distribuciones(self, pool_id: int, dias: int = 90) -> Dict:
        """Obtiene un resumen de distribuciones."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_periodos,
                    SUM(ganancias_totales) as total_ganancias,
                    AVG(rendimiento_porcentaje) as avg_rendimiento,
                    SUM(CASE WHEN estado = 'COMPLETADO' THEN 1 ELSE 0 END) as completados
                FROM periodos_distribucion
                WHERE pool_id = ? AND fecha_calculo >= ?
            """, (pool_id, fecha_limite.isoformat()))
            
            result = self.cursor.fetchone()
            
            if result:
                total_periodos, total_ganancias, avg_rendimiento, completados = result
                return {
                    'total_periodos': total_periodos or 0,
                    'total_ganancias': total_ganancias or 0,
                    'avg_rendimiento': round(avg_rendimiento or 0, 2),
                    'periodos_completados': completados or 0,
                    'periodo_dias': dias
                }
            return {}
        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            return {}
            
    def cerrar_periodo(self, periodo_id: int) -> bool:
        """
        Cierra un período de distribución.
        
        Args:
            periodo_id: ID del período
            
        Returns:
            True si se cerró correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE periodos_distribucion SET estado = 'COMPLETADO' WHERE id = ?
            """, (periodo_id,))
            self.conn.commit()
            logger.info(f"Período {periodo_id} cerrado")
            return True
        except Exception as e:
            logger.error(f"Error al cerrar período: {e}")
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
    
    agente = AgenteDistribucionGanancias()
    
    # Ejemplo: crear regla
    regla_id = agente.crear_regla_distribucion(
        pool_id=1,
        porcentaje_qh=30,
        porcentaje_inversores=70,
        retencion_impuestos=5,
        comision_gestion=2
    )
    
    print(f"Regla creada - ID: {regla_id}")
    
    # Ejemplo: calcular distribución
    resultado = agente.calcular_distribucion_periodo(
        pool_id=1,
        periodo="2026-05",
        fecha_inicio=datetime(2026, 5, 1),
        fecha_fin=datetime(2026, 5, 31),
        ganancias_totales=15000,
        capital_base=100000
    )
    
    print(f"Cálculo distribución: {resultado}")
    
    # Ejemplo: distribuir a inversores
    inversores = [
        {'inversor_id': 'INV001', 'nombre_inversor': 'Inversor A', 'porcentaje_participacion': 50},
        {'inversor_id': 'INV002', 'nombre_inversor': 'Inversor B', 'porcentaje_participacion': 50}
    ]
    
    agente.distribuir_a_inversores(resultado['periodo_id'], inversores)
    
    # Ejemplo: distribuir a QH
    conceptos = {'Operaciones': 40, 'Desarrollo': 30, 'Marketing': 30}
    agente.distribuir_a_quantumhive(resultado['periodo_id'], conceptos)
    
    # Ejemplo: obtener distribuciones
    dist = agente.obtener_distribuciones_periodo(resultado['periodo_id'])
    print(f"Distribuciones: {len(dist['inversores'])} inversores, {len(dist['quantumhive'])} conceptos QH")
    
    agente.cerrar()

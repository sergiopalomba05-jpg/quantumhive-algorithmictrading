"""
Agente Rotación VPS - D2B: PropFirms y Dispersión de Cuentas
Rota cuentas entre VPS para evitar detección

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona la rotación de cuentas entre diferentes servidores VPS
             para evitar patrones de detección por parte de las propfirms.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import json

logger = logging.getLogger(__name__)

class AgenteRotacionVPS:
    """Gestiona la rotación de cuentas entre VPS."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de rotación VPS.
        
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
                CREATE TABLE IF NOT EXISTS rotaciones_programadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    servidor_actual TEXT NOT NULL,
                    servidor_destino TEXT NOT NULL,
                    fecha_programada DATETIME NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_ejecucion DATETIME,
                    observaciones TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_rotaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    servidor_origen TEXT NOT NULL,
                    servidor_destino TEXT NOT NULL,
                    fecha_rotacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    exito BOOLEAN NOT NULL,
                    tiempo_ejecucion REAL,
                    observaciones TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS politicas_rotacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    propfirm TEXT NOT NULL,
                    intervalo_minimo_dias INTEGER NOT NULL,
                    intervalo_maximo_dias INTEGER NOT NULL,
                    rotacion_obligatoria BOOLEAN DEFAULT FALSE,
                    servidores_excluidos TEXT,
                    activa BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS vps_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    ip TEXT NOT NULL,
                    ubicacion TEXT NOT NULL,
                    latencia_promedio REAL,
                    estado TEXT NOT NULL,
                    prioridad INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_vps(self, nombre: str, ip: str, ubicacion: str, latencia_promedio: float = None,
                      prioridad: int = 1) -> int:
        """
        Registra un VPS en el pool.
        
        Args:
            nombre: Nombre del VPS
            ip: IP del VPS
            ubicacion: Ubicación del VPS
            latencia_promedio: Latencia promedio en ms
            prioridad: Prioridad del VPS (mayor = más usado)
            
        Returns:
            ID del VPS registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO vps_pool (nombre, ip, ubicacion, latencia_promedio, estado, prioridad)
                VALUES (?, ?, ?, ?, 'ACTIVO', ?)
            """, (nombre, ip, ubicacion, latencia_promedio, prioridad))
            
            self.conn.commit()
            vps_id = self.cursor.lastrowid
            logger.info(f"VPS registrado - ID: {vps_id} - Nombre: {nombre}")
            return vps_id
        except Exception as e:
            logger.error(f"Error al registrar VPS: {e}")
            raise
            
    def registrar_politica_rotacion(self, propfirm: str, intervalo_min: int, intervalo_max: int,
                                   rotacion_obligatoria: bool = False,
                                   servidores_excluidos: List[str] = None) -> int:
        """
        Registra una política de rotación para una propfirm.
        
        Args:
            propfirm: Nombre de la propfirm
            intervalo_min: Intervalo mínimo en días
            intervalo_max: Intervalo máximo en días
            rotacion_obligatoria: Si la rotación es obligatoria
            servidores_excluidos: Lista de servidores excluidos
            
        Returns:
            ID de la política registrada
        """
        try:
            excluidos_json = json.dumps(servidores_excluidos) if servidores_excluidos else None
            
            self.cursor.execute("""
                INSERT INTO politicas_rotacion
                (propfirm, intervalo_minimo_dias, intervalo_maximo_dias,
                 rotacion_obligatoria, servidores_excluidos, activa)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (propfirm, intervalo_min, intervalo_max, rotacion_obligatoria, excluidos_json))
            
            self.conn.commit()
            politica_id = self.cursor.lastrowid
            logger.info(f"Política de rotación registrada - ID: {politica_id} - Propfirm: {propfirm}")
            return politica_id
        except Exception as e:
            logger.error(f"Error al registrar política de rotación: {e}")
            raise
            
    def programar_rotacion(self, cuenta: str, servidor_actual: str, servidor_destino: str,
                          fecha_programada: datetime, observaciones: str = None) -> int:
        """
        Programa una rotación de cuenta.
        
        Args:
            cuenta: Número de cuenta
            servidor_actual: Servidor actual
            servidor_destino: Servidor destino
            fecha_programada: Fecha de la rotación
            observaciones: Observaciones
            
        Returns:
            ID de la rotación programada
        """
        try:
            self.cursor.execute("""
                INSERT INTO rotaciones_programadas
                (cuenta, servidor_actual, servidor_destino, fecha_programada, estado, observaciones)
                VALUES (?, ?, ?, ?, 'PROGRAMADA', ?)
            """, (cuenta, servidor_actual, servidor_destino, fecha_programada.isoformat(), observaciones))
            
            self.conn.commit()
            rotacion_id = self.cursor.lastrowid
            logger.info(f"Rotación programada - ID: {rotacion_id} - Cuenta: {cuenta}")
            return rotacion_id
        except Exception as e:
            logger.error(f"Error al programar rotación: {e}")
            raise
            
    def ejecutar_rotacion(self, rotacion_id: int) -> bool:
        """
        Ejecuta una rotación programada.
        
        Args:
            rotacion_id: ID de la rotación
            
        Returns:
            True si se ejecutó correctamente
        """
        try:
            # Obtener rotación programada
            self.cursor.execute("""
                SELECT cuenta, servidor_actual, servidor_destino
                FROM rotaciones_programadas WHERE id = ?
            """, (rotacion_id,))
            result = self.cursor.fetchone()
            
            if not result:
                logger.error(f"Rotación {rotacion_id} no encontrada")
                return False
                
            cuenta, servidor_origen, servidor_destino = result
            
            # Simular ejecución (aquí iría la lógica real de migración)
            inicio = datetime.now()
            exito = self._migrar_cuenta(cuenta, servidor_origen, servidor_destino)
            fin = datetime.now()
            tiempo_ejecucion = (fin - inicio).total_seconds()
            
            # Registrar en histórico
            self.cursor.execute("""
                INSERT INTO historico_rotaciones
                (cuenta, servidor_origen, servidor_destino, fecha_rotacion, exito, tiempo_ejecucion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cuenta, servidor_origen, servidor_destino, fin.isoformat(), exito, tiempo_ejecucion))
            
            # Actualizar estado de rotación programada
            estado = 'COMPLETADA' if exito else 'FALLIDA'
            self.cursor.execute("""
                UPDATE rotaciones_programadas
                SET estado = ?, fecha_ejecucion = ?, observaciones = ?
                WHERE id = ?
            """, (estado, fin.isoformat(), f"Tiempo: {tiempo_ejecucion:.2f}s", rotacion_id))
            
            self.conn.commit()
            
            if exito:
                logger.info(f"Rotación {rotacion_id} completada exitosamente")
            else:
                logger.error(f"Rotación {rotacion_id} falló")
                
            return exito
        except Exception as e:
            logger.error(f"Error al ejecutar rotación: {e}")
            return False
            
    def _migrar_cuenta(self, cuenta: str, servidor_origen: str, servidor_destino: str) -> bool:
        """
        Migra una cuenta entre servidores (simulado).
        
        Args:
            cuenta: Número de cuenta
            servidor_origen: Servidor origen
            servidor_destino: Servidor destino
            
        Returns:
            True si la migración fue exitosa
        """
        try:
            # Aquí iría la lógica real de migración:
            # - Detener bot en servidor origen
            # - Copiar configuración y estado
            # - Iniciar bot en servidor destino
            # - Verificar conectividad
            
            # Simulación exitosa
            logger.info(f"Migrando cuenta {cuenta} de {servidor_origen} a {servidor_destino}")
            return True
        except Exception as e:
            logger.error(f"Error al migrar cuenta: {e}")
            return False
            
    def obtener_rotaciones_pendientes(self) -> List[Dict]:
        """
        Obtiene rotaciones pendientes para ejecutar.
        
        Returns:
            Lista de rotaciones pendientes
        """
        try:
            ahora = datetime.now()
            
            self.cursor.execute("""
                SELECT * FROM rotaciones_programadas
                WHERE estado = 'PROGRAMADA' AND fecha_programada <= ?
                ORDER BY fecha_programada ASC
            """, (ahora.isoformat(),))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'servidor_actual': r[2],
                'servidor_destino': r[3], 'fecha_programada': r[4],
                'estado': r[5], 'fecha_ejecucion': r[6], 'observaciones': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener rotaciones pendientes: {e}")
            return []
            
    def obtener_vps_disponibles(self, cuenta: str = None, propfirm: str = None) -> List[Dict]:
        """
        Obtiene VPS disponibles para rotación.
        
        Args:
            cuenta: Cuenta actual (para evitar el servidor actual)
            propfirm: Propfirm (para aplicar políticas)
            
        Returns:
            Lista de VPS disponibles
        """
        try:
            self.cursor.execute("""
                SELECT * FROM vps_pool WHERE estado = 'ACTIVO' ORDER BY prioridad DESC
            """)
            results = self.cursor.fetchall()
            
            vps_list = [{
                'id': r[0], 'nombre': r[1], 'ip': r[2], 'ubicacion': r[3],
                'latencia_promedio': r[4], 'estado': r[5], 'prioridad': r[6]
            } for r in results]
            
            # Aplicar políticas de propfirm si se especifica
            if propfirm:
                vps_list = self._aplicar_politicas(vps_list, propfirm)
                
            return vps_list
        except Exception as e:
            logger.error(f"Error al obtener VPS disponibles: {e}")
            return []
            
    def _aplicar_politicas(self, vps_list: List[Dict], propfirm: str) -> List[Dict]:
        """Aplica políticas de rotación de propfirm."""
        try:
            self.cursor.execute("""
                SELECT servidores_excluidos FROM politicas_rotacion
                WHERE propfirm = ? AND activa = TRUE
            """, (propfirm,))
            result = self.cursor.fetchone()
            
            if result and result[0]:
                excluidos = json.loads(result[0])
                vps_list = [v for v in vps_list if v['nombre'] not in excluidos]
                
            return vps_list
        except Exception as e:
            logger.error(f"Error al aplicar políticas: {e}")
            return vps_list
            
    def generar_rotacion_automatica(self, cuenta: str, propfirm: str, servidor_actual: str) -> Optional[Dict]:
        """
        Genera una rotación automática basada en políticas.
        
        Args:
            cuenta: Número de cuenta
            propfirm: Propfirm
            servidor_actual: Servidor actual
            
        Returns:
            Diccionario con la rotación generada o None
        """
        try:
            # Obtener política
            self.cursor.execute("""
                SELECT intervalo_minimo_dias, intervalo_maximo_dias
                FROM politicas_rotacion WHERE propfirm = ? AND activa = TRUE
            """, (propfirm,))
            result = self.cursor.fetchone()
            
            if not result:
                logger.warning(f"No hay política para {propfirm}")
                return None
                
            min_dias, max_dias = result
            
            # Obtener VPS disponibles
            vps_disponibles = self.obtener_vps_disponibles(cuenta, propfirm)
            
            if not vps_disponibles:
                logger.warning("No hay VPS disponibles para rotación")
                return None
                
            # Seleccionar servidor destino (prioridad aleatoria entre top 3)
            top_vps = vps_disponibles[:3]
            servidor_destino = random.choice(top_vps)['nombre']
            
            # Calcular fecha de rotación
            dias_aleatorios = random.randint(min_dias, max_dias)
            fecha_rotacion = datetime.now() + timedelta(days=dias_aleatorios)
            
            rotacion = {
                'cuenta': cuenta,
                'servidor_actual': servidor_actual,
                'servidor_destino': servidor_destino,
                'fecha_programada': fecha_rotacion,
                'dias_espera': dias_aleatorios
            }
            
            return rotacion
        except Exception as e:
            logger.error(f"Error al generar rotación automática: {e}")
            return None
            
    def obtener_historico_rotaciones(self, cuenta: str = None, dias: int = 30) -> List[Dict]:
        """
        Obtiene el histórico de rotaciones.
        
        Args:
            cuenta: Cuenta específica (opcional)
            dias: Días de histórico
            
        Returns:
            Lista de rotaciones históricas
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            if cuenta:
                self.cursor.execute("""
                    SELECT * FROM historico_rotaciones
                    WHERE cuenta = ? AND fecha_rotacion >= ?
                    ORDER BY fecha_rotacion DESC
                """, (cuenta, fecha_limite.isoformat()))
            else:
                self.cursor.execute("""
                    SELECT * FROM historico_rotaciones
                    WHERE fecha_rotacion >= ?
                    ORDER BY fecha_rotacion DESC
                """, (fecha_limite.isoformat(),))
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'servidor_origen': r[2],
                'servidor_destino': r[3], 'fecha_rotacion': r[4],
                'exito': r[5], 'tiempo_ejecucion': r[6], 'observaciones': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener histórico de rotaciones: {e}")
            return []
            
    def obtener_estadisticas_rotaciones(self, dias: int = 30) -> Dict:
        """
        Obtiene estadísticas de rotaciones.
        
        Args:
            dias: Días para estadísticas
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN exito = TRUE THEN 1 ELSE 0 END) as exitosas,
                    SUM(CASE WHEN exito = FALSE THEN 1 ELSE 0 END) as fallidas,
                    AVG(tiempo_ejecucion) as tiempo_promedio
                FROM historico_rotaciones
                WHERE fecha_rotacion >= ?
            """, (fecha_limite.isoformat(),))
            
            result = self.cursor.fetchone()
            
            if result:
                total, exitosas, fallidas, tiempo_promedio = result
                tasa_exito = (exitosas / total * 100) if total > 0 else 0
                
                return {
                    'total': total or 0,
                    'exitosas': exitosas or 0,
                    'fallidas': fallidas or 0,
                    'tasa_exito': round(tasa_exito, 2),
                    'tiempo_promedio_segundos': round(tiempo_promedio or 0, 2),
                    'periodo_dias': dias
                }
            return {}
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}
            
    def cancelar_rotacion(self, rotacion_id: int, motivo: str = None) -> bool:
        """
        Cancela una rotación programada.
        
        Args:
            rotacion_id: ID de la rotación
            motivo: Motivo de cancelación
            
        Returns:
            True si se canceló correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE rotaciones_programadas
                SET estado = 'CANCELADA', observaciones = ?
                WHERE id = ?
            """, (f"Cancelada: {motivo}" if motivo else "Cancelada", rotacion_id))
            
            self.conn.commit()
            logger.info(f"Rotación {rotacion_id} cancelada")
            return True
        except Exception as e:
            logger.error(f"Error al cancelar rotación: {e}")
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
    
    agente = AgenteRotacionVPS()
    
    # Ejemplo: registrar VPS
    vps_id = agente.registrar_vps(
        nombre="VPS-NY-01",
        ip="192.168.1.100",
        ubicacion="New York",
        latencia_promedio=45.5,
        prioridad=1
    )
    
    print(f"VPS registrado - ID: {vps_id}")
    
    # Ejemplo: registrar política
    politica_id = agente.registrar_politica_rotacion(
        propfirm="FTMO",
        intervalo_min=7,
        intervalo_max=14,
        rotacion_obligatoria=True
    )
    
    print(f"Política registrada - ID: {politica_id}")
    
    # Ejemplo: programar rotación
    rotacion_id = agente.programar_rotacion(
        cuenta="123456",
        servidor_actual="VPS-NY-01",
        servidor_destino="VPS-LON-01",
        fecha_programada=datetime.now() + timedelta(days=10)
    )
    
    print(f"Rotación programada - ID: {rotacion_id}")
    
    # Ejemplo: ejecutar rotación
    agente.ejecutar_rotacion(rotacion_id)
    
    # Ejemplo: obtener estadísticas
    stats = agente.obtener_estadisticas_rotaciones(dias=30)
    print(f"Estadísticas: {stats}")
    
    agente.cerrar()

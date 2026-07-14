"""
Agente Anti Detección - D2B: PropFirms y Dispersión de Cuentas
Randomiza comportamiento para evitar patrones

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Randomiza el comportamiento de trading para evitar patrones
             de detección por parte de las propfirms, variando horarios,
             lotajes y tiempos de ejecución.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import json

logger = logging.getLogger(__name__)

class AgenteAntiDeteccion:
    """Randomiza comportamiento para evitar detección de patrones."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente anti-detección.
        
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
                CREATE TABLE IF NOT EXISTS perfiles_randomizacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    cuenta TEXT NOT NULL,
                    variacion_lotaje_min REAL NOT NULL,
                    variacion_lotaje_max REAL NOT NULL,
                    variacion_tiempo_min_segundos INTEGER NOT NULL,
                    variacion_tiempo_max_segundos INTEGER NOT NULL,
                    horarios_ventana TEXT,
                    dias_inactivos TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos_randomizacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    tipo_evento TEXT NOT NULL,
                    valor_original REAL NOT NULL,
                    valor_randomizado REAL NOT NULL,
                    variacion_porcentaje REAL NOT NULL,
                    fecha_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
                    perfil_id INTEGER
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS patrones_detectados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    tipo_patron TEXT NOT NULL,
                    severidad TEXT NOT NULL,
                    fecha_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accion_tomada TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas_comportamiento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuenta TEXT NOT NULL,
                    metrica TEXT NOT NULL,
                    valor_actual REAL NOT NULL,
                    valor_promedio REAL NOT NULL,
                    desviacion_estandar REAL NOT NULL,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def crear_perfil_randomizacion(self, nombre: str, cuenta: str,
                                   variacion_lotaje_min: float = 0.9,
                                   variacion_lotaje_max: float = 1.1,
                                   variacion_tiempo_min: int = 1,
                                   variacion_tiempo_max: int = 30,
                                   horarios_ventana: str = None,
                                   dias_inactivos: str = None) -> int:
        """
        Crea un perfil de randomización para una cuenta.
        
        Args:
            nombre: Nombre del perfil
            cuenta: Número de cuenta
            variacion_lotaje_min: Variación mínima de lotaje (ej: 0.9 = -10%)
            variacion_lotaje_max: Variación máxima de lotaje (ej: 1.1 = +10%)
            variacion_tiempo_min: Variación mínima de tiempo en segundos
            variacion_tiempo_max: Variación máxima de tiempo en segundos
            horarios_ventana: Horarios de ventana de trading (JSON)
            dias_inactivos: Días de inactividad (JSON)
            
        Returns:
            ID del perfil creado
        """
        try:
            self.cursor.execute("""
                INSERT INTO perfiles_randomizacion
                (nombre, cuenta, variacion_lotaje_min, variacion_lotaje_max,
                 variacion_tiempo_min_segundos, variacion_tiempo_max_segundos,
                 horarios_ventana, dias_inactivos, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (nombre, cuenta, variacion_lotaje_min, variacion_lotaje_max,
                  variacion_tiempo_min, variacion_tiempo_max, horarios_ventana, dias_inactivos))
            
            self.conn.commit()
            perfil_id = self.cursor.lastrowid
            logger.info(f"Perfil de randomización creado - ID: {perfil_id} - Cuenta: {cuenta}")
            return perfil_id
        except Exception as e:
            logger.error(f"Error al crear perfil de randomización: {e}")
            raise
            
    def randomizar_lotaje(self, cuenta: str, lotaje_original: float) -> float:
        """
        Aplica variación aleatoria al lotaje.
        
        Args:
            cuenta: Número de cuenta
            lotaje_original: Lotaje original
            
        Returns:
            Lotaje randomizado
        """
        try:
            # Obtener perfil
            perfil = self._obtener_perfil_activo(cuenta)
            
            if not perfil:
                return lotaje_original
                
            variacion = random.uniform(perfil['variacion_lotaje_min'], perfil['variacion_lotaje_max'])
            lotaje_randomizado = lotaje_original * variacion
            
            # Registrar evento
            variacion_pct = ((lotaje_randomizado - lotaje_original) / lotaje_original * 100)
            self._registrar_evento(cuenta, 'LOTAJE', lotaje_original, lotaje_randomizado, 
                                  variacion_pct, perfil['id'])
            
            logger.info(f"Lotaje randomizado: {lotaje_original} -> {lotaje_randomizado:.4f} ({variacion_pct:.2f}%)")
            return lotaje_randomizado
        except Exception as e:
            logger.error(f"Error al randomizar lotaje: {e}")
            return lotaje_original
            
    def randomizar_tiempo_ejecucion(self, cuenta: str, tiempo_base: int = 0) -> int:
        """
        Calcula un tiempo de espera aleatorio antes de ejecutar.
        
        Args:
            cuenta: Número de cuenta
            tiempo_base: Tiempo base en segundos
            
        Returns:
            Tiempo randomizado en segundos
        """
        try:
            perfil = self._obtener_perfil_activo(cuenta)
            
            if not perfil:
                return tiempo_base
                
            variacion = random.randint(perfil['variacion_tiempo_min'], perfil['variacion_tiempo_max'])
            tiempo_randomizado = tiempo_base + variacion
            
            logger.info(f"Tiempo randomizado: {tiempo_base}s -> {tiempo_randomizado}s")
            return tiempo_randomizado
        except Exception as e:
            logger.error(f"Error al randomizar tiempo: {e}")
            return tiempo_base
            
    def verificar_horario_permitido(self, cuenta: str) -> bool:
        """
        Verifica si el horario actual está permitido según el perfil.
        
        Args:
            cuenta: Número de cuenta
            
        Returns:
            True si el horario está permitido
        """
        try:
            perfil = self._obtener_perfil_activo(cuenta)
            
            if not perfil or not perfil['horarios_ventana']:
                return True  # Sin restricciones
                
            horarios = json.loads(perfil['horarios_ventana'])
            ahora = datetime.now()
            hora_actual = ahora.hour * 60 + ahora.minute  # Minutos desde medianoche
            
            for ventana in horarios:
                inicio = ventana['inicio']  # formato "HH:MM"
                fin = ventana['fin']  # formato "HH:MM"
                
                inicio_min = int(inicio.split(':')[0]) * 60 + int(inicio.split(':')[1])
                fin_min = int(fin.split(':')[0]) * 60 + int(fin.split(':')[1])
                
                if inicio_min <= hora_actual <= fin_min:
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error al verificar horario: {e}")
            return True
            
    def verificar_dia_activo(self, cuenta: str) -> bool:
        """
        Verifica si el día actual está activo según el perfil.
        
        Args:
            cuenta: Número de cuenta
            
        Returns:
            True si el día está activo
        """
        try:
            perfil = self._obtener_perfil_activo(cuenta)
            
            if not perfil or not perfil['dias_inactivos']:
                return True  # Sin restricciones
                
            dias_inactivos = json.loads(perfil['dias_inactivos'])
            hoy = datetime.now().strftime('%A').upper()
            
            return hoy not in dias_inactivos
        except Exception as e:
            logger.error(f"Error al verificar día activo: {e}")
            return True
            
    def _obtener_perfil_activo(self, cuenta: str) -> Optional[Dict]:
        """Obtiene el perfil activo de una cuenta."""
        try:
            self.cursor.execute("""
                SELECT * FROM perfiles_randomizacion
                WHERE cuenta = ? AND activo = TRUE
                ORDER BY timestamp DESC LIMIT 1
            """, (cuenta,))
            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'nombre': result[1], 'cuenta': result[2],
                    'variacion_lotaje_min': result[3], 'variacion_lotaje_max': result[4],
                    'variacion_tiempo_min': result[5], 'variacion_tiempo_max': result[6],
                    'horarios_ventana': result[7], 'dias_inactivos': result[8]
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener perfil activo: {e}")
            return None
            
    def _registrar_evento(self, cuenta: str, tipo_evento: str, valor_original: float,
                         valor_randomizado: float, variacion_porcentaje: float, perfil_id: int):
        """Registra un evento de randomización."""
        try:
            self.cursor.execute("""
                INSERT INTO eventos_randomizacion
                (cuenta, tipo_evento, valor_original, valor_randomizado, variacion_porcentaje, perfil_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cuenta, tipo_evento, valor_original, valor_randomizado,
                  variacion_porcentaje, perfil_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al registrar evento: {e}")
            
    def detectar_patron(self, cuenta: str, tipo_patron: str, severidad: str = 'MEDIA') -> int:
        """
        Registra la detección de un patrón sospechoso.
        
        Args:
            cuenta: Número de cuenta
            tipo_patron: Tipo de patrón detectado
            severidad: Severidad del patrón (BAJA, MEDIA, ALTA)
            
        Returns:
            ID del patrón registrado
        """
        try:
            accion = self._determinar_accion(tipo_patron, severidad)
            
            self.cursor.execute("""
                INSERT INTO patrones_detectados (cuenta, tipo_patron, severidad, accion_tomada)
                VALUES (?, ?, ?, ?)
            """, (cuenta, tipo_patron, severidad, accion))
            
            self.conn.commit()
            patron_id = self.cursor.lastrowid
            logger.warning(f"Patrón detectado - ID: {patron_id} - Tipo: {tipo_patron} - Acción: {accion}")
            return patron_id
        except Exception as e:
            logger.error(f"Error al detectar patrón: {e}")
            raise
            
    def _determinar_accion(self, tipo_patron: str, severidad: str) -> str:
        """Determina la acción a tomar ante un patrón detectado."""
        if severidad == 'ALTA':
            return 'DETENER_TRADING'
        elif severidad == 'MEDIA':
            return 'REDUCIR_FRECUENCIA'
        else:
            return 'MONITOREAR'
            
    def actualizar_metrica_comportamiento(self, cuenta: str, metrica: str, valor: float) -> bool:
        """
        Actualiza una métrica de comportamiento de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            metrica: Nombre de la métrica
            valor: Valor actual
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Obtener valores anteriores si existen
            self.cursor.execute("""
                SELECT valor_promedio, desviacion_estandar
                FROM metricas_comportamiento
                WHERE cuenta = ? AND metrica = ?
                ORDER BY fecha_actualizacion DESC LIMIT 1
            """, (cuenta, metrica))
            
            result = self.cursor.fetchone()
            
            if result:
                promedio_anterior, desviacion_anterior = result
                # Calcular nuevo promedio y desviación (simplificado)
                nuevo_promedio = (promedio_anterior + valor) / 2
                nueva_desviacion = abs(valor - nuevo_promedio)
            else:
                nuevo_promedio = valor
                nueva_desviacion = 0
                
            self.cursor.execute("""
                INSERT INTO metricas_comportamiento
                (cuenta, metrica, valor_actual, valor_promedio, desviacion_estandar)
                VALUES (?, ?, ?, ?, ?)
            """, (cuenta, metrica, valor, nuevo_promedio, nueva_desviacion))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar métrica: {e}")
            return False
            
    def obtener_metricas(self, cuenta: str) -> List[Dict]:
        """
        Obtiene las métricas de comportamiento de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            
        Returns:
            Lista de métricas
        """
        try:
            self.cursor.execute("""
                SELECT * FROM metricas_comportamiento
                WHERE cuenta = ?
                ORDER BY fecha_actualizacion DESC
            """, (cuenta,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'metrica': r[2],
                'valor_actual': r[3], 'valor_promedio': r[4],
                'desviacion_estandar': r[5], 'fecha_actualizacion': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener métricas: {e}")
            return []
            
    def obtener_eventos_randomizacion(self, cuenta: str, dias: int = 7) -> List[Dict]:
        """
        Obtiene los eventos de randomización de una cuenta.
        
        Args:
            cuenta: Número de cuenta
            dias: Días de histórico
            
        Returns:
            Lista de eventos
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            self.cursor.execute("""
                SELECT * FROM eventos_randomizacion
                WHERE cuenta = ? AND fecha_evento >= ?
                ORDER BY fecha_evento DESC
            """, (cuenta, fecha_limite.isoformat()))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'tipo_evento': r[2],
                'valor_original': r[3], 'valor_randomizado': r[4],
                'variacion_porcentaje': r[5], 'fecha_evento': r[6], 'perfil_id': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener eventos: {e}")
            return []
            
    def obtener_patrones_detectados(self, cuenta: str = None, dias: int = 30) -> List[Dict]:
        """
        Obtiene patrones detectados.
        
        Args:
            cuenta: Cuenta específica (opcional)
            dias: Días de histórico
            
        Returns:
            Lista de patrones
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            if cuenta:
                self.cursor.execute("""
                    SELECT * FROM patrones_detectados
                    WHERE cuenta = ? AND fecha_deteccion >= ?
                    ORDER BY fecha_deteccion DESC
                """, (cuenta, fecha_limite.isoformat()))
            else:
                self.cursor.execute("""
                    SELECT * FROM patrones_detectados
                    WHERE fecha_deteccion >= ?
                    ORDER BY fecha_deteccion DESC
                """, (fecha_limite.isoformat(),))
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cuenta': r[1], 'tipo_patron': r[2],
                'severidad': r[3], 'fecha_deteccion': r[4], 'accion_tomada': r[5]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener patrones: {e}")
            return []
            
    def desactivar_perfil(self, perfil_id: int) -> bool:
        """
        Desactiva un perfil de randomización.
        
        Args:
            perfil_id: ID del perfil
            
        Returns:
            True si se desactivó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE perfiles_randomizacion SET activo = FALSE WHERE id = ?
            """, (perfil_id,))
            self.conn.commit()
            logger.info(f"Perfil {perfil_id} desactivado")
            return True
        except Exception as e:
            logger.error(f"Error al desactivar perfil: {e}")
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
    
    agente = AgenteAntiDeteccion()
    
    # Ejemplo: crear perfil
    perfil_id = agente.crear_perfil_randomizacion(
        nombre="Perfil-FTMO-01",
        cuenta="123456",
        variacion_lotaje_min=0.85,
        variacion_lotaje_max=1.15,
        variacion_tiempo_min=2,
        variacion_tiempo_max=45,
        horarios_ventana=json.dumps([
            {"inicio": "08:00", "fin": "12:00"},
            {"inicio": "14:00", "fin": "18:00"}
        ]),
        dias_inactivos=json.dumps(["SATURDAY", "SUNDAY"])
    )
    
    print(f"Perfil creado - ID: {perfil_id}")
    
    # Ejemplo: randomizar lotaje
    lotaje_randomizado = agente.randomizar_lotaje("123456", 0.1)
    print(f"Lotaje randomizado: {lotaje_randomizado}")
    
    # Ejemplo: randomizar tiempo
    tiempo = agente.randomizar_tiempo_ejecucion("123456", 5)
    print(f"Tiempo randomizado: {tiempo}s")
    
    # Ejemplo: verificar horario
    horario_ok = agente.verificar_horario_permitido("123456")
    print(f"Horario permitido: {horario_ok}")
    
    # Ejemplo: detectar patrón
    patron_id = agente.detectar_patron("123456", "ENTADAS_SIMULTANEAS", "MEDIA")
    print(f"Patrón detectado - ID: {patron_id}")
    
    # Ejemplo: obtener eventos
    eventos = agente.obtener_eventos_randomizacion("123456")
    print(f"Eventos de randomización: {len(eventos)}")
    
    agente.cerrar()

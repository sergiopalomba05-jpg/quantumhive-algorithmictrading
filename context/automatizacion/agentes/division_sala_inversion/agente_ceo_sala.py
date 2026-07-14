"""
Agente CEO Sala - D16: Sala de Inversión Colmena
Interfaz de CEO para toma de decisiones estratégicas

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Proporciona una interfaz ejecutiva para la Sala de Inversión,
             permitiendo al CEO tomar decisiones estratégicas basadas en datos.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteCEOSala:
    """Interfaz de CEO para toma de decisiones estratégicas."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente CEO Sala.
        
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
                CREATE TABLE IF NOT EXISTS decisiones_ceo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_decision TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    contexto TEXT,
                    impacto_estimado TEXT,
                    fecha_decision DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    resultado TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS objetivos_sala (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descripcion TEXT,
                    metricas TEXT NOT NULL,
                    valor_objetivo REAL NOT NULL,
                    valor_actual REAL DEFAULT 0,
                    fecha_inicio DATETIME NOT NULL,
                    fecha_objetivo DATETIME NOT NULL,
                    estado TEXT NOT NULL,
                    prioridad TEXT NOT NULL
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reuniones_sala (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    fecha_reunion DATETIME NOT NULL,
                    participantes TEXT NOT NULL,
                    agenda TEXT,
                    conclusiones TEXT,
                    acciones_pendientes TEXT,
                    estado TEXT NOT NULL
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reportes_ejecutivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_reporte TEXT NOT NULL,
                    periodo TEXT NOT NULL,
                    datos_reporte TEXT NOT NULL,
                    resumen_ejecutivo TEXT,
                    fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    generado_por TEXT NOT NULL
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS alertas_criticas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_alerta TEXT NOT NULL,
                    severidad TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    area_afectada TEXT NOT NULL,
                    fecha_alerta DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    accion_tomada TEXT
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_decision(self, tipo_decision: str, descripcion: str, contexto: str = None,
                         impacto_estimado: str = None) -> int:
        """
        Registra una decisión del CEO.
        
        Args:
            tipo_decision: Tipo de decisión (ESTRATEGICA, OPERATIVA, FINANCIERA)
            descripcion: Descripción de la decisión
            contexto: Contexto de la decisión
            impacto_estimado: Impacto estimado
            
        Returns:
            ID de la decisión registrada
        """
        try:
            self.cursor.execute("""
                INSERT INTO decisiones_ceo
                (tipo_decision, descripcion, contexto, impacto_estimado, estado)
                VALUES (?, ?, ?, ?, 'EN_PROGRESO')
            """, (tipo_decision, descripcion, contexto, impacto_estimado))
            
            self.conn.commit()
            decision_id = self.cursor.lastrowid
            logger.info(f"Decisión registrada - ID: {decision_id} - Tipo: {tipo_decision}")
            return decision_id
        except Exception as e:
            logger.error(f"Error al registrar decisión: {e}")
            raise
            
    def crear_objetivo(self, titulo: str, descripcion: str, metricas: dict,
                      valor_objetivo: float, fecha_inicio: datetime, fecha_objetivo: datetime,
                      prioridad: str = "MEDIA") -> int:
        """
        Crea un objetivo para la Sala de Inversión.
        
        Args:
            titulo: Título del objetivo
            descripcion: Descripción
            metricas: Diccionario de métricas
            valor_objetivo: Valor objetivo
            fecha_inicio: Fecha de inicio
            fecha_objetivo: Fecha objetivo
            prioridad: Prioridad (ALTA, MEDIA, BAJA)
            
        Returns:
            ID del objetivo creado
        """
        try:
            metricas_json = json.dumps(metricas)
            
            self.cursor.execute("""
                INSERT INTO objetivos_sala
                (titulo, descripcion, metricas, valor_objetivo, fecha_inicio,
                 fecha_objetivo, estado, prioridad)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
            """, (titulo, descripcion, metricas_json, valor_objetivo,
                  fecha_inicio.isoformat(), fecha_objetivo.isoformat(), prioridad))
            
            self.conn.commit()
            objetivo_id = self.cursor.lastrowid
            logger.info(f"Objetivo creado - ID: {objetivo_id} - Título: {titulo}")
            return objetivo_id
        except Exception as e:
            logger.error(f"Error al crear objetivo: {e}")
            raise
            
    def programar_reunion(self, titulo: str, fecha_reunion: datetime,
                         participantes: List[str], agenda: str = None) -> int:
        """
        Programa una reunión de la Sala de Inversión.
        
        Args:
            titulo: Título de la reunión
            fecha_reunion: Fecha y hora
            participantes: Lista de participantes
            agenda: Agenda de la reunión
            
        Returns:
            ID de la reunión
        """
        try:
            participantes_json = json.dumps(participantes)
            
            self.cursor.execute("""
                INSERT INTO reuniones_sala
                (titulo, fecha_reunion, participantes, agenda, estado)
                VALUES (?, ?, ?, ?, 'PROGRAMADA')
            """, (titulo, fecha_reunion.isoformat(), participantes_json, agenda))
            
            self.conn.commit()
            reunion_id = self.cursor.lastrowid
            logger.info(f"Reunión programada - ID: {reunion_id} - Fecha: {fecha_reunion}")
            return reunion_id
        except Exception as e:
            logger.error(f"Error al programar reunión: {e}")
            raise
            
    def generar_reporte_ejecutivo(self, tipo_reporte: str, periodo: str,
                                 datos_reporte: dict, resumen_ejecutivo: str = None,
                                 generado_por: str = "CEO") -> int:
        """
        Genera un reporte ejecutivo.
        
        Args:
            tipo_reporte: Tipo de reporte (FINANCIERO, OPERATIVO, ESTRATEGICO)
            periodo: Período del reporte
            datos_reporte: Datos del reporte
            resumen_ejecutivo: Resumen ejecutivo
            generado_por: Quién generó el reporte
            
        Returns:
            ID del reporte
        """
        try:
            datos_json = json.dumps(datos_reporte)
            
            self.cursor.execute("""
                INSERT INTO reportes_ejecutivos
                (tipo_reporte, periodo, datos_reporte, resumen_ejecutivo, generado_por)
                VALUES (?, ?, ?, ?, ?)
            """, (tipo_reporte, periodo, datos_json, resumen_ejecutivo, generado_por))
            
            self.conn.commit()
            reporte_id = self.cursor.lastrowid
            logger.info(f"Reporte ejecutivo generado - ID: {reporte_id} - Tipo: {tipo_reporte}")
            return reporte_id
        except Exception as e:
            logger.error(f"Error al generar reporte: {e}")
            raise
            
    def generar_alerta_critica(self, tipo_alerta: str, severidad: str, descripcion: str,
                             area_afectada: str) -> int:
        """
        Genera una alerta crítica para el CEO.
        
        Args:
            tipo_alerta: Tipo de alerta
            severidad: Severidad (ALTA, MEDIA, BAJA)
            descripcion: Descripción
            area_afectada: Área afectada
            
        Returns:
            ID de la alerta
        """
        try:
            self.cursor.execute("""
                INSERT INTO alertas_criticas
                (tipo_alerta, severidad, descripcion, area_afectada, estado)
                VALUES (?, ?, ?, ?, 'ACTIVA')
            """, (tipo_alerta, severidad, descripcion, area_afectada))
            
            self.conn.commit()
            alerta_id = self.cursor.lastrowid
            logger.warning(f"Alerta crítica generada - ID: {alerta_id} - Severidad: {severidad}")
            return alerta_id
        except Exception as e:
            logger.error(f"Error al generar alerta: {e}")
            raise
            
    def actualizar_decision(self, decision_id: int, estado: str = None, resultado: str = None) -> bool:
        """
        Actualiza el estado de una decisión.
        
        Args:
            decision_id: ID de la decisión
            estado: Nuevo estado
            resultado: Resultado
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            updates = []
            values = []
            
            if estado:
                updates.append("estado = ?")
                values.append(estado)
            if resultado:
                updates.append("resultado = ?")
                values.append(resultado)
                
            if not updates:
                return False
                
            values.append(decision_id)
            query = f"UPDATE decisiones_ceo SET {', '.join(updates)} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logger.info(f"Decisión {decision_id} actualizada")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar decisión: {e}")
            return False
            
    def actualizar_progreso_objetivo(self, objetivo_id: int, valor_actual: float) -> bool:
        """
        Actualiza el progreso de un objetivo.
        
        Args:
            objetivo_id: ID del objetivo
            valor_actual: Valor actual
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE objetivos_sala SET valor_actual = ? WHERE id = ?
            """, (valor_actual, objetivo_id))
            
            # Verificar si se alcanzó el objetivo
            self.cursor.execute("""
                SELECT valor_objetivo FROM objetivos_sala WHERE id = ?
            """, (objetivo_id,))
            valor_objetivo = self.cursor.fetchone()[0]
            
            if valor_actual >= valor_objetivo:
                self.cursor.execute("""
                    UPDATE objetivos_sala SET estado = 'COMPLETADO' WHERE id = ?
                """, (objetivo_id,))
                
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar progreso: {e}")
            return False
            
    def finalizar_reunion(self, reunion_id: int, conclusiones: str, acciones_pendientes: dict) -> bool:
        """
        Finaliza una reunión registrando conclusiones y acciones.
        
        Args:
            reunion_id: ID de la reunión
            conclusiones: Conclusiones
            acciones_pendientes: Acciones pendientes
            
        Returns:
            True si se finalizó correctamente
        """
        try:
            acciones_json = json.dumps(acciones_pendientes)
            
            self.cursor.execute("""
                UPDATE reuniones_sala
                SET conclusiones = ?, acciones_pendientes = ?, estado = 'COMPLETADA'
                WHERE id = ?
            """, (conclusiones, acciones_json, reunion_id))
            
            self.conn.commit()
            logger.info(f"Reunión {reunion_id} finalizada")
            return True
        except Exception as e:
            logger.error(f"Error al finalizar reunión: {e}")
            return False
            
    def resolver_alerta(self, alerta_id: int, accion_tomada: str) -> bool:
        """
        Marca una alerta como resuelta.
        
        Args:
            alerta_id: ID de la alerta
            accion_tomada: Acción tomada
            
        Returns:
            True si se resolvió correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE alertas_criticas SET estado = 'RESUELTA', accion_tomada = ? WHERE id = ?
            """, (accion_tomada, alerta_id))
            self.conn.commit()
            logger.info(f"Alerta {alerta_id} resuelta")
            return True
        except Exception as e:
            logger.error(f"Error al resolver alerta: {e}")
            return False
            
    def obtener_decisiones(self, estado: str = None, dias: int = 30) -> List[Dict]:
        """Obtiene decisiones registradas."""
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            if estado:
                self.cursor.execute("""
                    SELECT * FROM decisiones_ceo
                    WHERE estado = ? AND fecha_decision >= ?
                    ORDER BY fecha_decision DESC
                """, (estado, fecha_limite.isoformat()))
            else:
                self.cursor.execute("""
                    SELECT * FROM decisiones_ceo
                    WHERE fecha_decision >= ?
                    ORDER BY fecha_decision DESC
                """, (fecha_limite.isoformat(),))
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'tipo_decision': r[1], 'descripcion': r[2],
                'contexto': r[3], 'impacto_estimado': r[4], 'fecha_decision': r[5],
                'estado': r[6], 'resultado': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener decisiones: {e}")
            return []
            
    def obtener_objetivos(self, estado: str = None) -> List[Dict]:
        """Obtiene objetivos."""
        try:
            if estado:
                self.cursor.execute("""
                    SELECT * FROM objetivos_sala WHERE estado = ? ORDER BY prioridad DESC
                """, (estado,))
            else:
                self.cursor.execute("""
                    SELECT * FROM objetivos_sala ORDER BY prioridad DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'titulo': r[1], 'descripcion': r[2],
                'metricas': json.loads(r[3]) if r[3] else None,
                'valor_objetivo': r[4], 'valor_actual': r[5],
                'fecha_inicio': r[6], 'fecha_objetivo': r[7],
                'estado': r[8], 'prioridad': r[9]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener objetivos: {e}")
            return []
            
    def obtener_alertas_activas(self) -> List[Dict]:
        """Obtiene alertas críticas activas."""
        try:
            self.cursor.execute("""
                SELECT * FROM alertas_criticas WHERE estado = 'ACTIVA'
                ORDER BY fecha_alerta DESC
            """)
            results = self.cursor.fetchall()
            
            return [{
                'id': r[0], 'tipo_alerta': r[1], 'severidad': r[2],
                'descripcion': r[3], 'area_afectada': r[4],
                'fecha_alerta': r[5], 'estado': r[6], 'accion_tomada': r[7]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener alertas: {e}")
            return []
            
    def obtener_dashboard_ceo(self) -> Dict:
        """Obtiene un dashboard ejecutivo para el CEO."""
        try:
            objetivos = self.obtener_objetivos()
            alertas = self.obtener_alertas_activas()
            decisiones = self.obtener_decisiones(dias=7)
            
            # Calcular agregados
            objetivos_completados = len([o for o in objetivos if o['estado'] == 'COMPLETADO'])
            objetivos_pendientes = len([o for o in objetivos if o['estado'] == 'ACTIVO'])
            alertas_alta = len([a for a in alertas if a['severidad'] == 'ALTA'])
            
            return {
                'resumen': {
                    'objetivos_completados': objetivos_completados,
                    'objetivos_pendientes': objetivos_pendientes,
                    'alertas_activas': len(alertas),
                    'alertas_alta_prioridad': alertas_alta,
                    'decisiones_semana': len(decisiones)
                },
                'objetivos': objetivos,
                'alertas': alertas,
                'decisiones_recientes': decisiones
            }
        except Exception as e:
            logger.error(f"Error al obtener dashboard: {e}")
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
    
    agente = AgenteCEOSala()
    
    # Ejemplo: registrar decisión
    decision_id = agente.registrar_decision(
        tipo_decision="ESTRATEGICA",
        descripcion="Expandir operaciones a 2 nuevas propfirms",
        contexto="Crecimiento del 20% en Q1, capacidad disponible",
        impacto_estimado="Aumento del 30% en capital gestionado"
    )
    
    print(f"Decisión registrada - ID: {decision_id}")
    
    # Ejemplo: crear objetivo
    objetivo_id = agente.crear_objetivo(
        titulo="Alcanzar $200K en capital gestionado",
        descripcion="Objetivo de capital total gestionado para fin de año",
        metricas={"capital_total": "USD"},
        valor_objetivo=200000,
        fecha_inicio=datetime(2026, 1, 1),
        fecha_objetivo=datetime(2026, 12, 31),
        prioridad="ALTA"
    )
    
    print(f"Objetivo creado - ID: {objetivo_id}")
    
    # Ejemplo: generar alerta
    alerta_id = agente.generar_alerta_critica(
        tipo_alerta="RIESGO",
        severidad="ALTA",
        descripcion="Drawdown superior al 8% en pool principal",
        area_afectada="Gestión de Riesgo"
    )
    
    print(f"Alerta generada - ID: {alerta_id}")
    
    # Ejemplo: obtener dashboard
    dashboard = agente.obtener_dashboard_ceo()
    print(f"Dashboard CEO: {dashboard['resumen']}")
    
    agente.cerrar()

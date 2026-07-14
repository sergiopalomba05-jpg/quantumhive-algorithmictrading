"""
Agente Onboarding Cliente - D2: Gestión de Fondeo y Challenges
Alta nuevo cliente, asigna bot challenge

Autor: Cascade
Fecha: 3 de mayo de 2026
Descripción: Gestiona el proceso de onboarding de nuevos clientes,
             registra información, asigna bot de challenge y envía instrucciones.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class AgenteOnboardingCliente:
    """Gestiona el onboarding de nuevos clientes."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        """
        Inicializa el agente de onboarding.
        
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
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    email TEXT,
                    telefono TEXT,
                    telegram_id TEXT,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    propfirm_preferida TEXT,
                    tipo_cuenta_deseado TEXT,
                    presupuesto REAL,
                    observaciones TEXT,
                    metadata TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS onboarding_pasos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    paso TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_completado DATETIME,
                    notas TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS asignaciones_bot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    bot_id TEXT NOT NULL,
                    tipo_bot TEXT NOT NULL,
                    cuenta_asignada TEXT,
                    propfirm TEXT,
                    tipo_challenge TEXT,
                    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT NOT NULL,
                    configuracion TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS documentos_cliente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    tipo_documento TEXT NOT NULL,
                    url_documento TEXT,
                    estado TEXT NOT NULL,
                    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
                    verificado BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise
            
    def registrar_cliente(self, cliente_id: str, nombre: str, email: str = None,
                        telefono: str = None, telegram_id: str = None,
                        propfirm_preferida: str = None, tipo_cuenta_deseado: str = None,
                        presupuesto: float = None, observaciones: str = None,
                        metadata: dict = None) -> int:
        """
        Registra un nuevo cliente.
        
        Args:
            cliente_id: ID único del cliente
            nombre: Nombre completo del cliente
            email: Email del cliente
            telefono: Teléfono del cliente
            telegram_id: ID de Telegram
            propfirm_preferida: Propfirm preferida
            tipo_cuenta_deseado: Tipo de cuenta deseado
            presupuesto: Presupuesto del cliente
            observaciones: Observaciones adicionales
            metadata: Metadatos adicionales (dict)
            
        Returns:
            ID del cliente registrado
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.cursor.execute("""
                INSERT INTO clientes
                (cliente_id, nombre, email, telefono, telegram_id, estado,
                 propfirm_preferida, tipo_cuenta_deseado, presupuesto, observaciones, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, nombre, email, telefono, telegram_id, 'ONBOARDING',
                  propfirm_preferida, tipo_cuenta_deseado, presupuesto, observaciones, metadata_json))
            
            self.conn.commit()
            cliente_db_id = self.cursor.lastrowid
            
            # Iniciar pasos de onboarding
            self._iniciar_pasos_onboarding(cliente_id)
            
            logger.info(f"Cliente registrado - ID: {cliente_db_id} - Nombre: {nombre}")
            return cliente_db_id
        except Exception as e:
            logger.error(f"Error al registrar cliente: {e}")
            raise
            
    def _iniciar_pasos_onboarding(self, cliente_id: str):
        """Inicia los pasos de onboarding para un cliente."""
        try:
            pasos = [
                'REGISTRO_COMPLETO',
                'DOCUMENTACION_VERIFICADA',
                'PROP_FIRM_SELECCIONADA',
                'CHALLENGE_COMPRADO',
                'BOT_ASIGNADO',
                'CONFIGURACION_COMPLETA',
                'PRIMER_TRADE_EJECUTADO',
                'ONBOARDING_COMPLETO'
            ]
            
            for paso in pasos:
                self.cursor.execute("""
                    INSERT INTO onboarding_pasos (cliente_id, paso, estado)
                    VALUES (?, ?, 'PENDIENTE')
                """, (cliente_id, paso))
            
            # Marcar primer paso como completado
            self.completar_paso(cliente_id, 'REGISTRO_COMPLETO')
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error al iniciar pasos onboarding: {e}")
            
    def completar_paso(self, cliente_id: str, paso: str, notas: str = None) -> bool:
        """
        Marca un paso de onboarding como completado.
        
        Args:
            cliente_id: ID del cliente
            paso: Nombre del paso
            notas: Notas adicionales
            
        Returns:
            True si se completó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE onboarding_pasos
                SET estado = 'COMPLETADO', fecha_completado = ?, notas = ?
                WHERE cliente_id = ? AND paso = ?
            """, (datetime.now().isoformat(), notas, cliente_id, paso))
            
            self.conn.commit()
            
            # Verificar si todos los pasos están completados
            self._verificar_onboarding_completo(cliente_id)
            
            logger.info(f"Paso {paso} completado para cliente {cliente_id}")
            return True
        except Exception as e:
            logger.error(f"Error al completar paso: {e}")
            return False
            
    def _verificar_onboarding_completo(self, cliente_id: str):
        """Verifica si el onboarding está completo."""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM onboarding_pasos
                WHERE cliente_id = ? AND estado != 'COMPLETADO'
            """, (cliente_id,))
            
            pendientes = self.cursor.fetchone()[0]
            
            if pendientes == 0:
                # Marcar onboarding como completo
                self.cursor.execute("""
                    UPDATE clientes SET estado = 'ACTIVO' WHERE cliente_id = ?
                """, (cliente_id,))
                self.conn.commit()
                logger.info(f"Onboarding completado para cliente {cliente_id}")
        except Exception as e:
            logger.error(f"Error al verificar onboarding completo: {e}")
            
    def asignar_bot_challenge(self, cliente_id: str, bot_id: str, tipo_bot: str,
                             cuenta_asignada: str = None, propfirm: str = None,
                             tipo_challenge: str = None, configuracion: dict = None) -> int:
        """
        Asigna un bot de challenge a un cliente.
        
        Args:
            cliente_id: ID del cliente
            bot_id: ID del bot
            tipo_bot: Tipo de bot
            cuenta_asignada: Cuenta asignada
            propfirm: Propfirm
            tipo_challenge: Tipo de challenge
            configuracion: Configuración del bot (dict)
            
        Returns:
            ID de la asignación
        """
        try:
            configuracion_json = json.dumps(configuracion) if configuracion else None
            
            self.cursor.execute("""
                INSERT INTO asignaciones_bot
                (cliente_id, bot_id, tipo_bot, cuenta_asignada, propfirm,
                 tipo_challenge, estado, configuracion)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
            """, (cliente_id, bot_id, tipo_bot, cuenta_asignada, propfirm,
                  tipo_challenge, configuracion_json))
            
            self.conn.commit()
            asignacion_id = self.cursor.lastrowid
            
            # Marcar paso como completado
            self.completar_paso(cliente_id, 'BOT_ASIGNADO')
            
            logger.info(f"Bot asignado - ID: {asignacion_id} - Cliente: {cliente_id}")
            return asignacion_id
        except Exception as e:
            logger.error(f"Error al asignar bot: {e}")
            raise
            
    def subir_documento(self, cliente_id: str, tipo_documento: str, url_documento: str) -> int:
        """
        Registra un documento del cliente.
        
        Args:
            cliente_id: ID del cliente
            tipo_documento: Tipo de documento
            url_documento: URL del documento
            
        Returns:
            ID del documento registrado
        """
        try:
            self.cursor.execute("""
                INSERT INTO documentos_cliente
                (cliente_id, tipo_documento, url_documento, estado)
                VALUES (?, ?, ?, 'PENDIENTE_VERIFICACION')
            """, (cliente_id, tipo_documento, url_documento))
            
            self.conn.commit()
            doc_id = self.cursor.lastrowid
            logger.info(f"Documento subido - ID: {doc_id} - Tipo: {tipo_documento}")
            return doc_id
        except Exception as e:
            logger.error(f"Error al subir documento: {e}")
            raise
            
    def verificar_documento(self, doc_id: int, verificado: bool, notas: str = None) -> bool:
        """
        Verifica un documento del cliente.
        
        Args:
            doc_id: ID del documento
            verificado: Si está verificado
            notas: Notas de verificación
            
        Returns:
            True si se verificó correctamente
        """
        try:
            self.cursor.execute("""
                UPDATE documentos_cliente
                SET estado = ?, verificado = ?
                WHERE id = ?
            """, ('VERIFICADO' if verificado else 'RECHAZADO', verificado, doc_id))
            
            self.conn.commit()
            
            # Si verificado, marcar paso de documentación
            if verificado:
                self.cursor.execute("""
                    SELECT cliente_id FROM documentos_cliente WHERE id = ?
                """, (doc_id,))
                cliente_id = self.cursor.fetchone()[0]
                self.completar_paso(cliente_id, 'DOCUMENTACION_VERIFICADA', notas)
            
            logger.info(f"Documento {doc_id} verificado: {verificado}")
            return True
        except Exception as e:
            logger.error(f"Error al verificar documento: {e}")
            return False
            
    def obtener_cliente(self, cliente_id: str) -> Optional[Dict]:
        """
        Obtiene información de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Diccionario con información o None
        """
        try:
            self.cursor.execute("""
                SELECT * FROM clientes WHERE cliente_id = ?
            """, (cliente_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'id': result[0], 'cliente_id': result[1], 'nombre': result[2],
                    'email': result[3], 'telefono': result[4], 'telegram_id': result[5],
                    'fecha_registro': result[6], 'estado': result[7],
                    'propfirm_preferida': result[8], 'tipo_cuenta_deseado': result[9],
                    'presupuesto': result[10], 'observaciones': result[11],
                    'metadata': json.loads(result[12]) if result[12] else None
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener cliente: {e}")
            return None
            
    def obtener_pasos_onboarding(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene los pasos de onboarding de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de pasos
        """
        try:
            self.cursor.execute("""
                SELECT * FROM onboarding_pasos WHERE cliente_id = ? ORDER BY id ASC
            """, (cliente_id,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cliente_id': r[1], 'paso': r[2],
                'estado': r[3], 'fecha_inicio': r[4], 'fecha_completado': r[5],
                'notas': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener pasos onboarding: {e}")
            return []
            
    def obtener_asignaciones_bot(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene las asignaciones de bot de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de asignaciones
        """
        try:
            self.cursor.execute("""
                SELECT * FROM asignaciones_bot WHERE cliente_id = ? ORDER BY fecha_asignacion DESC
            """, (cliente_id,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cliente_id': r[1], 'bot_id': r[2], 'tipo_bot': r[3],
                'cuenta_asignada': r[4], 'propfirm': r[5], 'tipo_challenge': r[6],
                'fecha_asignacion': r[7], 'estado': r[8],
                'configuracion': json.loads(r[9]) if r[9] else None
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener asignaciones bot: {e}")
            return []
            
    def obtener_documentos(self, cliente_id: str) -> List[Dict]:
        """
        Obtiene los documentos de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de documentos
        """
        try:
            self.cursor.execute("""
                SELECT * FROM documentos_cliente WHERE cliente_id = ? ORDER BY fecha_subida DESC
            """, (cliente_id,))
            
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cliente_id': r[1], 'tipo_documento': r[2],
                'url_documento': r[3], 'estado': r[4], 'fecha_subida': r[5],
                'verificado': r[6]
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener documentos: {e}")
            return []
            
    def obtener_progreso_onboarding(self, cliente_id: str) -> Dict:
        """
        Obtiene el progreso de onboarding de un cliente.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Diccionario con progreso
        """
        try:
            pasos = self.obtener_pasos_onboarding(cliente_id)
            
            total = len(pasos)
            completados = sum(1 for p in pasos if p['estado'] == 'COMPLETADO')
            pendientes = total - completados
            porcentaje = (completados / total * 100) if total > 0 else 0
            
            return {
                'cliente_id': cliente_id,
                'total_pasos': total,
                'pasos_completados': completados,
                'pasos_pendientes': pendientes,
                'porcentaje_completado': round(porcentaje, 2),
                'estado_global': 'COMPLETO' if pendientes == 0 else 'EN_PROGRESO'
            }
        except Exception as e:
            logger.error(f"Error al obtener progreso onboarding: {e}")
            return {}
            
    def obtener_todos_clientes(self, estado: str = None) -> List[Dict]:
        """
        Obtiene todos los clientes, opcionalmente filtrados por estado.
        
        Args:
            estado: Estado para filtrar (opcional)
            
        Returns:
            Lista de clientes
        """
        try:
            if estado:
                self.cursor.execute("""
                    SELECT * FROM clientes WHERE estado = ? ORDER BY fecha_registro DESC
                """, (estado,))
            else:
                self.cursor.execute("""
                    SELECT * FROM clientes ORDER BY fecha_registro DESC
                """)
                
            results = self.cursor.fetchall()
            return [{
                'id': r[0], 'cliente_id': r[1], 'nombre': r[2],
                'email': r[3], 'telefono': r[4], 'telegram_id': r[5],
                'fecha_registro': r[6], 'estado': r[7],
                'propfirm_preferida': r[8], 'tipo_cuenta_deseado': r[9],
                'presupuesto': r[10], 'observaciones': r[11],
                'metadata': json.loads(r[12]) if r[12] else None
            } for r in results]
        except Exception as e:
            logger.error(f"Error al obtener todos los clientes: {e}")
            return []
            
    def actualizar_cliente(self, cliente_id: str, nombre: str = None, email: str = None,
                         telefono: str = None, telegram_id: str = None,
                         estado: str = None, observaciones: str = None) -> bool:
        """
        Actualiza información de un cliente.
        
        Args:
            cliente_id: ID del cliente
            nombre: Nuevo nombre
            email: Nuevo email
            telefono: Nuevo teléfono
            telegram_id: Nuevo ID de Telegram
            estado: Nuevo estado
            observaciones: Nuevas observaciones
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            updates = []
            values = []
            
            if nombre:
                updates.append("nombre = ?")
                values.append(nombre)
            if email:
                updates.append("email = ?")
                values.append(email)
            if telefono:
                updates.append("telefono = ?")
                values.append(telefono)
            if telegram_id:
                updates.append("telegram_id = ?")
                values.append(telegram_id)
            if estado:
                updates.append("estado = ?")
                values.append(estado)
            if observaciones:
                updates.append("observaciones = ?")
                values.append(observaciones)
                
            if not updates:
                return False
                
            values.append(cliente_id)
            
            query = f"UPDATE clientes SET {', '.join(updates)} WHERE cliente_id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logger.info(f"Cliente {cliente_id} actualizado")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar cliente: {e}")
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
    
    agente = AgenteOnboardingCliente()
    
    # Ejemplo: registrar cliente
    cliente_id = agente.registrar_cliente(
        cliente_id="CLI001",
        nombre="Juan Pérez",
        email="juan@example.com",
        telefono="+1234567890",
        telegram_id="123456789",
        propfirm_preferida="FTMO",
        tipo_cuenta_deseado="10k",
        presupuesto=500,
        metadata={"fuente": "Instagram", "campaign": "QH2026"}
    )
    
    print(f"Cliente registrado - ID: {cliente_id}")
    
    # Ejemplo: asignar bot
    asignacion_id = agente.asignar_bot_challenge(
        cliente_id="CLI001",
        bot_id="BOT001",
        tipo_bot="challenge_bot",
        cuenta_asignada="123456",
        propfirm="FTMO",
        tipo_challenge="10k",
        configuracion={"risk_per_trade": 0.02, "max_drawdown": 5}
    )
    
    print(f"Bot asignado - ID: {asignacion_id}")
    
    # Ejemplo: obtener progreso
    progreso = agente.obtener_progreso_onboarding("CLI001")
    print(f"Progreso onboarding: {progreso}")
    
    # Ejemplo: subir documento
    doc_id = agente.subir_documento("CLI001", "IDENTIDAD", "https://example.com/doc.pdf")
    print(f"Documento subido - ID: {doc_id}")
    
    # Ejemplo: verificar documento
    agente.verificar_documento(doc_id, True, "Documento válido")
    
    agente.cerrar()

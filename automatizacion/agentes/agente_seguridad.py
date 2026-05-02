"""
Agente Seguridad — QuantumHive
Gestiona todas las credenciales, claves API y datos confidenciales con encriptación.
Solo entrega credenciales con aprobación explícita de Sergio (CEO Fundador).
"""

import os
import json
import logging
import hashlib
import sqlite3
from typing import Dict, Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from base64 import b64encode, b64decode
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AgenteSeguridad:
    """Agente de seguridad para gestión de credenciales encriptadas."""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Inicializa el agente de seguridad.
        
        Args:
            master_key: Clave maestra para encriptación (si no se proporciona, usa SECURITY_MASTER_KEY de env)
        """
        self.master_key = master_key or os.getenv('SECURITY_MASTER_KEY', '')
        if not self.master_key:
            logger.warning("SECURITY_MASTER_KEY no configurada - usando clave por defecto (NO RECOMENDADO)")
            self.master_key = "quantumhive-security-default-key-change-in-production"
        
        self.cipher_suite = self._crear_cipher_suite()
        self.vault_path = "security_vault.json"
        self.solicitudes_path = "security_requests.json"
        self.db_path = "accesos_credenciales.db"
        
        self.cargar_vault()
        self.cargar_solicitudes()
        self._inicializar_db_accesos()
        
        logger.info("AgenteSeguridad inicializado")
    
    def _crear_cipher_suite(self) -> Fernet:
        """Crea suite de encriptación Fernet desde la clave maestra."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'quantumhive-salt',
            iterations=100000,
        )
        key = kdf.derive(self.master_key.encode())
        fernet_key = b64encode(key)
        return Fernet(fernet_key)
    
    def encriptar(self, dato: str) -> str:
        """Encripta un dato usando Fernet."""
        if not dato:
            return ""
        encriptado = self.cipher_suite.encrypt(dato.encode())
        return encriptado.decode()
    
    def desencriptar(self, dato_encriptado: str) -> str:
        """Desencripta un dato usando Fernet."""
        if not dato_encriptado:
            return ""
        desencriptado = self.cipher_suite.decrypt(dato_encriptado.encode())
        return desencriptado.decode()
    
    def cargar_vault(self):
        """Carga el vault de seguridad desde archivo."""
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, 'r') as f:
                    self.vault = json.load(f)
                logger.info(f"Vault cargado: {len(self.vault)} credenciales")
            except Exception as e:
                logger.error(f"Error cargando vault: {e}")
                self.vault = {}
        else:
            self.vault = {}
            logger.info("Vault creado (nuevo)")
    
    def guardar_vault(self):
        """Guarda el vault de seguridad en archivo."""
        try:
            with open(self.vault_path, 'w') as f:
                json.dump(self.vault, f, indent=2)
            logger.info("Vault guardado")
        except Exception as e:
            logger.error(f"Error guardando vault: {e}")
    
    def cargar_solicitudes(self):
        """Carga las solicitudes pendientes desde archivo."""
        if os.path.exists(self.solicitudes_path):
            try:
                with open(self.solicitudes_path, 'r') as f:
                    self.solicitudes = json.load(f)
                logger.info(f"Solicitudes cargadas: {len(self.solicitudes)} pendientes")
            except Exception as e:
                logger.error(f"Error cargando solicitudes: {e}")
                self.solicitudes = {}
        else:
            self.solicitudes = {}
    
    def guardar_solicitudes(self):
        """Guarda las solicitudes pendientes en archivo."""
        try:
            with open(self.solicitudes_path, 'w') as f:
                json.dump(self.solicitudes, f, indent=2)
            logger.info("Solicitudes guardadas")
        except Exception as e:
            logger.error(f"Error guardando solicitudes: {e}")
    
    def agregar_credencial(self, nombre: str, valor: str, categoria: str = "general") -> bool:
        """
        Agrega una credencial al vault (encriptada).
        
        Args:
            nombre: Nombre de la credencial (ej: TELEGRAM_TOKEN)
            valor: Valor de la credencial
            categoria: Categoría (telegram, render, anthropic, etc.)
        """
        try:
            credencial = {
                'valor_encriptado': self.encriptar(valor),
                'categoria': categoria,
                'fecha_agregado': datetime.now().isoformat(),
                'ultimo_acceso': None,
                'accesos': 0
            }
            self.vault[nombre] = credencial
            self.guardar_vault()
            logger.info(f"Credencial {nombre} agregada (encriptada)")
            return True
        except Exception as e:
            logger.error(f"Error agregando credencial {nombre}: {e}")
            return False
    
    def obtener_credencial(self, nombre: str, solicitante: str, razon: str) -> Optional[str]:
        """
        Obtiene una credencial (solo si está aprobada).
        
        Args:
            nombre: Nombre de la credencial
            solicitante: Nombre del agente solicitante
            razon: Razón de la solicitud
        
        Returns:
            Valor desencriptado de la credencial si está aprobada, None si no
        """
        # Verificar si hay solicitud aprobada
        solicitud_id = f"{nombre}_{solicitante}"
        solicitud = self.solicitudes.get(solicitud_id)
        
        if solicitud and solicitud.get('estado') == 'aprobado':
            # Credencial aprobada, devolver valor
            credencial = self.vault.get(nombre)
            if credencial:
                valor = self.desencriptar(credencial['valor_encriptado'])
                # Actualizar estadísticas
                credencial['ultimo_acceso'] = datetime.now().isoformat()
                credencial['accesos'] += 1
                self.guardar_vault()
                
                # Registrar acceso
                logger.info(f"Credencial {nombre} entregada a {solicitante} (aprobada)")
                
                # Eliminar solicitud después de uso
                del self.solicitudes[solicitud_id]
                self.guardar_solicitudes()
                
                return valor
        
        # No hay solicitud aprobada, crear solicitud pendiente
        self.crear_solicitud(nombre, solicitante, razon)
        logger.warning(f"Credencial {nombre} requiere aprobación de Sergio")
        return None
    
    def crear_solicitud(self, nombre: str, solicitante: str, razon: str) -> str:
        """
        Crea una solicitud de credencial pendiente de aprobación.
        
        Returns:
            ID de la solicitud
        """
        solicitud_id = f"{nombre}_{solicitante}"
        solicitud = {
            'id': solicitud_id,
            'credencial': nombre,
            'solicitante': solicitante,
            'razon': razon,
            'fecha_solicitud': datetime.now().isoformat(),
            'estado': 'pendiente',
            'aprobado_por': None,
            'fecha_aprobacion': None
        }
        self.solicitudes[solicitud_id] = solicitud
        self.guardar_solicitudes()
        logger.info(f"Solicitud creada: {solicitud_id} - Pendiente aprobación de Sergio")
        return solicitud_id
    
    def aprobar_solicitud(self, solicitud_id: str, aprobado_por: str = "Sergio") -> bool:
        """
        Aprueba una solicitud de credencial.
        
        Args:
            solicitud_id: ID de la solicitud
            aprobado_por: Quién aprueba (debería ser Sergio)
        """
        solicitud = self.solicitudes.get(solicitud_id)
        if solicitud:
            solicitud['estado'] = 'aprobado'
            solicitud['aprobado_por'] = aprobado_por
            solicitud['fecha_aprobacion'] = datetime.now().isoformat()
            self.guardar_solicitudes()
            logger.info(f"Solicitud {solicitud_id} aprobada por {aprobado_por}")
            return True
        return False
    
    def rechazar_solicitud(self, solicitud_id: str, rechazado_por: str = "Sergio") -> bool:
        """
        Rechaza una solicitud de credencial.
        """
        solicitud = self.solicitudes.get(solicitud_id)
        if solicitud:
            solicitud['estado'] = 'rechazado'
            solicitud['rechazado_por'] = rechazado_por
            solicitud['fecha_rechazo'] = datetime.now().isoformat()
            self.guardar_solicitudes()
            logger.info(f"Solicitud {solicitud_id} rechazada por {rechazado_por}")
            return True
        return False
    
    def listar_solicitudes_pendientes(self) -> List[Dict]:
        """Lista todas las solicitudes pendientes de aprobación."""
        pendientes = [
            s for s in self.solicitudes.values() 
            if s.get('estado') == 'pendiente'
        ]
        return pendientes
    
    def listar_credenciales(self) -> List[str]:
        """Lista nombres de todas las credenciales (sin valores)."""
        return list(self.vault.keys())
    
    def eliminar_credencial(self, nombre: str) -> bool:
        """Elimina una credencial del vault."""
        if nombre in self.vault:
            del self.vault[nombre]
            self.guardar_vault()
            logger.info(f"Credencial {nombre} eliminada")
            return True
        return False
    
    def _inicializar_db_accesos(self):
        """Inicializa la tabla SQLite de accesos a credenciales."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accesos_credenciales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    agente_solicitante TEXT,
                    clave_solicitada TEXT,
                    motivo TEXT,
                    aprobado INTEGER,
                    aprobado_por TEXT,
                    ttl_segundos INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Tabla accesos_credenciales inicializada")
        except Exception as e:
            logger.error(f"Error inicializando DB de accesos: {e}")
    
    def log_acceso(self, agente: str, clave: str, accion: str, resultado: str, aprobado_por: Optional[str] = None, ttl: int = 60):
        """
        Registra un acceso a credenciales en SQLite.
        
        Args:
            agente: Agente solicitante
            clave: Clave solicitada
            accion: Acción realizada (solicitud, aprobación, rechazo, entrega)
            resultado: Resultado de la acción
            aprobado_por: Quién aprobó (si aplica)
            ttl: Tiempo de vida en segundos de la aprobación
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            aprobado = 1 if accion in ['aprobación', 'entrega'] else 0
            
            cursor.execute('''
                INSERT INTO accesos_credenciales 
                (timestamp, agente_solicitante, clave_solicitada, motivo, aprobado, aprobado_por, ttl_segundos)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), agente, clave, accion, aprobado, aprobado_por, ttl))
            
            conn.commit()
            conn.close()
            logger.info(f"Acceso registrado: {agente} - {clave} - {accion}")
        except Exception as e:
            logger.error(f"Error registrando acceso: {e}")
    
    def revocar_credencial_activa(self, nombre_clave: str) -> bool:
        """
        Revoca una credencial activa (elimina todas las aprobaciones pendientes).
        
        Args:
            nombre_clave: Nombre de la credencial a revocar
        """
        try:
            # Eliminar todas las solicitudes pendientes para esta credencial
            solicitudes_a_eliminar = [
                sol_id for sol_id, sol in self.solicitudes.items()
                if sol.get('credencial') == nombre_clave and sol.get('estado') == 'aprobado'
            ]
            
            for sol_id in solicitudes_a_eliminar:
                del self.solicitudes[sol_id]
            
            if solicitudes_a_eliminar:
                self.guardar_solicitudes()
                logger.info(f"Credencial {nombre_clave} revocada ({len(solicitudes_a_eliminar)} aprobaciones eliminadas)")
                return True
            
            logger.warning(f"No se encontraron aprobaciones activas para {nombre_clave}")
            return False
        except Exception as e:
            logger.error(f"Error revocando credencial {nombre_clave}: {e}")
            return False
    
    def reporte_estado(self) -> str:
        """Genera un reporte del estado del agente de seguridad."""
        reporte = "=== REPORTE AGENTE SEGURIDAD ===\n\n"
        reporte += f"🔒 Credenciales almacenadas: {len(self.vault)}\n"
        reporte += f"📋 Solicitudes pendientes: {len(self.listar_solicitudes_pendientes())}\n"
        
        reporte += "\n📊 Credenciales por categoría:\n"
        categorias = {}
        for cred in self.vault.values():
            cat = cred.get('categoria', 'general')
            categorias[cat] = categorias.get(cat, 0) + 1
        
        for cat, count in categorias.items():
            reporte += f"  • {cat}: {count}\n"
        
        reporte += "\n🔐 Solicitudes pendientes:\n"
        pendientes = self.listar_solicitudes_pendientes()
        if pendientes:
            for sol in pendientes[:5]:  # Mostrar primeras 5
                reporte += f"  • {sol['credencial']} - {sol['solicitante']}: {sol['razon']}\n"
        else:
            reporte += "  (Ninguna)\n"
        
        return reporte


# Instancia global
agente_seguridad = AgenteSeguridad()


# Función de conveniencia para otros agentes
def solicitar_credencial(nombre: str, solicitante: str, razon: str) -> Optional[str]:
    """
    Función de conveniencia para que otros agentes soliciten credenciales.
    
    Args:
        nombre: Nombre de la credencial solicitada
        solicitante: Nombre del agente solicitante
        razon: Razón de la solicitud
    
    Returns:
        Valor de la credencial si está aprobada, None si requiere aprobación
    """
    return agente_seguridad.obtener_credencial(nombre, solicitante, razon)


if __name__ == "__main__":
    print("=== AGENTE SEGURIDAD - QUANTUMHIVE ===\n")
    
    agente = AgenteSeguridad()
    
    # Reporte de estado
    print(agente.reporte_estado())
    
    # Ejemplo de uso
    print("\n🔧 EJEMPLOS DE USO:")
    
    # Agregar credencial
    print("\n1. Agregar credencial:")
    agente.agregar_credencial("TELEGRAM_TOKEN", "1234567890:ABC", "telegram")
    agente.agregar_credencial("GROQ_API_KEY", "gsk_test_key", "llm")
    
    # Solicitar credencial (sin aprobación)
    print("\n2. Solicitar credencial (sin aprobación):")
    resultado = agente.obtener_credencial("TELEGRAM_TOKEN", "agente_render", "Deploy en Render")
    print(f"Resultado: {resultado}")  # Debería ser None
    
    # Listar solicitudes pendientes
    print("\n3. Solicitudes pendientes:")
    pendientes = agente.listar_solicitudes_pendientes()
    for sol in pendientes:
        print(f"  - {sol['id']}: {sol['razon']}")
    
    # Aprobar solicitud
    print("\n4. Aprobar solicitud:")
    if pendientes:
        agente.aprobar_solicitud(pendientes[0]['id'])
    
    # Solicitar credencial (ahora con aprobación)
    print("\n5. Solicitar credencial (con aprobación):")
    resultado = agente.obtener_credencial("TELEGRAM_TOKEN", "agente_render", "Deploy en Render")
    print(f"Resultado: {resultado[:20]}...")  # Debería mostrar el valor
    
    # Reporte final
    print("\n" + agente.reporte_estado())

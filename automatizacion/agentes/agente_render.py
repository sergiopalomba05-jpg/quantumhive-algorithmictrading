"""
Agente Render — QuantumHive
Automatiza tareas de deploy, configuración y monitoreo en Render.
Usa KeysVault para gestión centralizada de credenciales.
"""

import os
import sys
from pathlib import Path
import requests
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Agregar path al directorio padre para importar agi_core
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

# Importar KeysVault
try:
    from agi_core.keys_vault import keys_vault
    KEYSVAULT_AVAILABLE = True
    logger.info("KeysVault disponible para gestión de credenciales")
except ImportError as e:
    KEYSVAULT_AVAILABLE = False
    logger.warning(f"KeysVault no disponible: {e}")

# Render API Configuration
if KEYSVAULT_AVAILABLE:
    render_creds = keys_vault.obtener_render()
    RENDER_API_KEY = render_creds.get('api_key', '')
    RENDER_SERVICE_ID = render_creds.get('service_id', '')
else:
    RENDER_API_KEY = os.getenv('RENDER_API_KEY', '')
    RENDER_SERVICE_ID = os.getenv('RENDER_SERVICE_ID', '')

RENDER_API_BASE = 'https://api.render.com/v1'

# Headers para autenticación
headers = {
    'Authorization': f'Bearer {RENDER_API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


class AgenteRender:
    """Agente para automatizar tareas de Render."""
    
    def __init__(self):
        self.api_key = RENDER_API_KEY
        self.service_id = RENDER_SERVICE_ID
        logger.info("AgenteRender inicializado")
    
    def verificar_api_key(self) -> bool:
        """Verifica que la API key de Render esté configurada."""
        if not self.api_key or len(self.api_key) < 10:
            logger.error("RENDER_API_KEY no configurada o inválida")
            return False
        logger.info("RENDER_API_KEY configurada correctamente")
        return True
    
    def obtener_servicio(self) -> Optional[Dict]:
        """Obtiene información del servicio de Render."""
        try:
            url = f"{RENDER_API_BASE}/services/{self.service_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                servicio = response.json()
                logger.info(f"Servicio obtenido: {servicio.get('name', 'desconocido')}")
                return servicio
            else:
                logger.error(f"Error obteniendo servicio: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo servicio: {e}")
            return None
    
    def agregar_variable_entorno(self, key: str, value: str) -> bool:
        """Agrega o actualiza una variable de entorno en el servicio."""
        try:
            servicio = self.obtener_servicio()
            if not servicio:
                return False
            
            # Obtener variables actuales
            env_vars = servicio.get('envVars', [])
            
            # Verificar si ya existe
            for var in env_vars:
                if var.get('key') == key:
                    logger.info(f"Variable {key} ya existe, actualizando...")
                    # Actualizar valor
                    url = f"{RENDER_API_BASE}/services/{self.service_id}/env-vars/{var.get('id')}"
                    response = requests.patch(url, headers=headers, json={'value': value}, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Variable {key} actualizada correctamente")
                        return True
                    else:
                        logger.error(f"Error actualizando variable: {response.status_code}")
                        return False
            
            # Si no existe, crear nueva
            logger.info(f"Creando variable {key}...")
            url = f"{RENDER_API_BASE}/services/{self.service_id}/env-vars"
            response = requests.post(url, headers=headers, json={'key': key, 'value': value}, timeout=10)
            
            if response.status_code == 201:
                logger.info(f"Variable {key} creada correctamente")
                return True
            else:
                logger.error(f"Error creando variable: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error agregando variable de entorno: {e}")
            return False
    
    def agregar_variables_groq(self) -> bool:
        """Agrega las variables de entorno necesarias para Groq."""
        if KEYSVAULT_AVAILABLE:
            groq_creds = keys_vault.obtener_groq()
            groq_api_key = groq_creds.get('api_key', '')
        else:
            groq_api_key = os.getenv('GROQ_API_KEY', '')
        
        if not groq_api_key:
            logger.error("GROQ_API_KEY no configurada")
            return False
        
        # Agregar LLM_ENGINE
        if not self.agregar_variable_entorno('LLM_ENGINE', 'groq'):
            return False
        
        # Agregar GROQ_API_KEY
        if not self.agregar_variable_entorno('GROQ_API_KEY', groq_api_key):
            return False
        
        logger.info("Variables de Groq configuradas correctamente")
        return True
    
    def obtener_variables_entorno(self) -> List[Dict]:
        """Obtiene todas las variables de entorno del servicio."""
        try:
            servicio = self.obtener_servicio()
            if not servicio:
                return []
            
            env_vars = servicio.get('envVars', [])
            logger.info(f"Variables de entorno obtenidas: {len(env_vars)}")
            return env_vars
        except Exception as e:
            logger.error(f"Error obteniendo variables de entorno: {e}")
            return []
    
    def hacer_deploy_manual(self) -> bool:
        """Trigger manual deploy del servicio."""
        try:
            url = f"{RENDER_API_BASE}/services/{self.service_id}/deploys"
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 201:
                deploy = response.json()
                logger.info(f"Deploy iniciado: {deploy.get('id', 'desconocido')}")
                return True
            else:
                logger.error(f"Error iniciando deploy: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error haciendo deploy: {e}")
            return False
    
    def obtener_estado_deploy(self) -> Optional[Dict]:
        """Obtiene el estado del deploy más reciente."""
        try:
            url = f"{RENDER_API_BASE}/services/{self.service_id}/deploys"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                deploys = response.json()
                if deploys:
                    deploy_mas_reciente = deploys[0]
                    estado = deploy_mas_reciente.get('status', 'unknown')
                    logger.info(f"Estado deploy más reciente: {estado}")
                    return deploy_mas_reciente
            return None
        except Exception as e:
            logger.error(f"Error obteniendo estado del deploy: {e}")
            return None
    
    def obtener_logs(self, limit: int = 100) -> List[str]:
        """Obtiene logs del servicio."""
        try:
            url = f"{RENDER_API_BASE}/services/{self.service_id}/logs"
            params = {'limit': limit}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                logs = response.json()
                logger.info(f"Logs obtenidos: {len(logs)} líneas")
                return logs
            else:
                logger.error(f"Error obteniendo logs: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []
    
    def obtener_errores_logs(self) -> List[str]:
        """Filtra logs para encontrar errores."""
        logs = self.obtener_logs(limit=500)
        errores = []
        
        for log in logs:
            log_str = str(log)
            if 'ERROR' in log_str or 'Exception' in log_str or 'Traceback' in log_str:
                errores.append(log_str)
        
        logger.info(f"Errores encontrados en logs: {len(errores)}")
        return errores
    
    def reiniciar_servicio(self) -> bool:
        """Reinicia el servicio."""
        try:
            url = f"{RENDER_API_BASE}/services/{self.service_id}/restart"
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("Servicio reiniciado correctamente")
                return True
            else:
                logger.error(f"Error reiniciando servicio: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error reiniciando servicio: {e}")
            return False
    
    def obtener_estado_servicio(self) -> Optional[Dict]:
        """Obtiene el estado actual del servicio."""
        try:
            servicio = self.obtener_servicio()
            if not servicio:
                return None
            
            estado = {
                'nombre': servicio.get('name', 'desconocido'),
                'estado': servicio.get('status', 'unknown'),
                'suspended': servicio.get('suspended', False),
                'ultimo_deploy': servicio.get('deploy', {}).get('createdAt', 'unknown'),
                'url': servicio.get('service', {}).get('url', 'unknown')
            }
            
            logger.info(f"Estado servicio: {estado}")
            return estado
        except Exception as e:
            logger.error(f"Error obteniendo estado del servicio: {e}")
            return None
    
    def diagnosticar_problemas(self) -> Dict:
        """Diagnostica problemas comunes en el servicio."""
        diagnosticos = {
            'api_key_configurada': self.verificar_api_key(),
            'servicio_activo': False,
            'variables_groq_configuradas': False,
            'errores_logs': [],
            'estado_deploy': None
        }
        
        # Verificar servicio activo
        estado = self.obtener_estado_servicio()
        if estado:
            diagnosticos['servicio_activo'] = estado.get('estado') == 'live'
        
        # Verificar variables Groq
        env_vars = self.obtener_variables_entorno()
        has_llm_engine = any(var.get('key') == 'LLM_ENGINE' for var in env_vars)
        has_groq_key = any(var.get('key') == 'GROQ_API_KEY' for var in env_vars)
        diagnosticos['variables_groq_configuradas'] = has_llm_engine and has_groq_key
        
        # Verificar errores en logs
        diagnosticos['errores_logs'] = self.obtener_errores_logs()
        
        # Verificar estado deploy
        diagnosticos['estado_deploy'] = self.obtener_estado_deploy()
        
        return diagnosticos


# Instancia global
agente_render = AgenteRender()


if __name__ == "__main__":
    print("=== AGENTE RENDER - QUANTUMHIVE ===")
    
    agente = AgenteRender()
    
    # Verificar API key
    if not agente.verificar_api_key():
        print("❌ RENDER_API_KEY no configurada")
        print("Agrega al .env: RENDER_API_KEY=tu_api_key_render")
        exit(1)
    
    # Diagnóstico
    print("\n🔍 DIAGNÓSTICO DEL SERVICIO:")
    diagnosticos = agente.diagnosticar_problemas()
    
    print(f"✅ API Key configurada: {diagnosticos['api_key_configurada']}")
    print(f"✅ Servicio activo: {diagnosticos['servicio_activo']}")
    print(f"✅ Variables Groq configuradas: {diagnosticos['variables_groq_configuradas']}")
    print(f"❌ Errores en logs: {len(diagnosticos['errores_logs'])}")
    
    if diagnosticos['estado_deploy']:
        print(f"📊 Estado deploy: {diagnosticos['estado_deploy'].get('status', 'unknown')}")
    
    # Si no tiene variables Groq, ofrecer agregarlas
    if not diagnosticos['variables_groq_configuradas']:
        print("\n⚠️ Variables Groq no configuradas")
        respuesta = input("¿Deseas agregarlas? (s/n): ")
        if respuesta.lower() == 's':
            if agente.agregar_variables_groq():
                print("✅ Variables Groq agregadas correctamente")
                print("🔄 Redeploy necesario para aplicar cambios")
            else:
                print("❌ Error agregando variables Groq")
    
    # Opciones adicionales
    print("\n📋 OPCIONES:")
    print("1. Hacer deploy manual")
    print("2. Reiniciar servicio")
    print("3. Ver logs")
    print("4. Ver errores en logs")
    print("5. Salir")
    
    opcion = input("\nSelecciona una opción (1-5): ")
    
    if opcion == '1':
        if agente.hacer_deploy_manual():
            print("✅ Deploy iniciado")
        else:
            print("❌ Error iniciando deploy")
    elif opcion == '2':
        if agente.reiniciar_servicio():
            print("✅ Servicio reiniciado")
        else:
            print("❌ Error reiniciando servicio")
    elif opcion == '3':
        logs = agente.obtener_logs(limit=50)
        for log in logs[-10:]:  # Últimos 10 logs
            print(log)
    elif opcion == '4':
        errores = agente.obtener_errores_logs()
        for error in errores[-10:]:  # Últimos 10 errores
            print(error)
    else:
        print("👋 Saliendo...")

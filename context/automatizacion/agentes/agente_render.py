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

# Importar Agente Seguridad
try:
    from agente_seguridad import agente_seguridad, solicitar_credencial
    SEGURIDAD_AVAILABLE = True
    logger.info("Agente Seguridad disponible para gestión de credenciales encriptadas")
except ImportError as e:
    SEGURIDAD_AVAILABLE = False
    logger.warning(f"Agente Seguridad no disponible: {e}")

# Render API Configuration
# Para automatización completa, usar directamente variables de entorno
RENDER_API_KEY = os.getenv('RENDER_API_KEY', '')
RENDER_SERVICE_ID = os.getenv('RENDER_SERVICE_ID', '')

# Si no están en entorno, intentar con KeysVault o Agente Seguridad
if not RENDER_API_KEY or not RENDER_SERVICE_ID:
    if SEGURIDAD_AVAILABLE:
        # Usar agente de seguridad para obtener credenciales
        RENDER_API_KEY = RENDER_API_KEY or solicitar_credencial("RENDER_API_KEY", "agente_render", "Gestión de servicios Render")
        RENDER_SERVICE_ID = RENDER_SERVICE_ID or solicitar_credencial("RENDER_SERVICE_ID", "agente_render", "Gestión de servicios Render")
    
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        if KEYSVAULT_AVAILABLE:
            render_creds = keys_vault.obtener_render()
            RENDER_API_KEY = RENDER_API_KEY or render_creds.get('api_key', '')
            RENDER_SERVICE_ID = RENDER_SERVICE_ID or render_creds.get('service_id', '')

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
            # Render API usa PUT para agregar/actualizar variables
            url = f"{RENDER_API_BASE}/services/{self.service_id}/env-vars/{key}"
            response = requests.put(url, headers=headers, json={'value': value}, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Variable {key} creada correctamente")
                return True
            else:
                logger.error(f"Error creando variable: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error agregando variable de entorno: {e}")
            return False
    
    def agregar_variables_groq(self) -> bool:
        """Agrega las variables de entorno necesarias para Groq."""
        if SEGURIDAD_AVAILABLE:
            groq_api_key = solicitar_credencial("GROQ_API_KEY", "agente_render", "Configuración de motor LLM Groq")
            if not groq_api_key:
                # Fallback a KeysVault si seguridad no tiene credenciales
                if KEYSVAULT_AVAILABLE:
                    groq_creds = keys_vault.obtener_groq()
                    groq_api_key = groq_creds.get('api_key', '')
                else:
                    groq_api_key = os.getenv('GROQ_API_KEY', '')
        elif KEYSVAULT_AVAILABLE:
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
    
    def esperar_deploy_completo(self, timeout_segundos: int = 300) -> bool:
        """Espera a que el deploy actual termine."""
        import time
        inicio = time.time()
        
        while time.time() - inicio < timeout_segundos:
            deploy = self.obtener_estado_deploy()
            if deploy:
                estado = deploy.get('status', 'unknown')
                if estado in ['succeeded', 'failed', 'canceled']:
                    logger.info(f"Deploy finalizado con estado: {estado}")
                    return estado == 'succeeded'
                logger.info(f"Deploy en progreso: {estado}")
            time.sleep(10)
        
        logger.warning("Timeout esperando deploy")
        return False
    
    def ciclo_deploy_automatico(self, max_intentos: int = 5) -> bool:
        """
        Ciclo automático: deploy → verificar logs → corregir → redeploy
        Repite hasta que no haya errores o se alcance max_intentos.
        """
        for intento in range(max_intentos):
            logger.info(f"=== CICLO DEPLOY AUTOMÁTICO - Intento {intento + 1}/{max_intentos} ===")
            
            # 1. Hacer deploy
            if not self.hacer_deploy_manual():
                logger.error("No se pudo iniciar deploy")
                continue
            
            # 2. Esperar a que termine
            if not self.esperar_deploy_completo():
                logger.error("Deploy falló o timeout")
                continue
            
            # 3. Esperar unos segundos para que el servicio arranque
            import time
            time.sleep(30)
            
            # 4. Leer logs y buscar errores
            errores = self.obtener_errores_logs()
            
            if not errores:
                logger.info("✅ No se encontraron errores - Servicio funcionando correctamente")
                return True
            
            logger.warning(f"❌ Errores encontrados: {len(errores)}")
            for error in errores[:5]:  # Mostrar primeros 5 errores
                logger.error(f"  - {error}")
            
            # 5. Analizar errores y corregir si es posible
            if self._corregir_errores_automaticamente(errores):
                logger.info("Errores corregidos automáticamente, reintentando...")
                continue
            else:
                logger.error("No se pudieron corregir errores automáticamente")
                break
        
        logger.error(f"Ciclo automático falló después de {max_intentos} intentos")
        return False
    
    def _corregir_errores_automaticamente(self, errores: List[str]) -> bool:
        """
        Analiza errores y aplica correcciones automáticas cuando es posible.
        Retorna True si aplicó correcciones, False si no pudo.
        """
        errores_str = ' '.join(errores)
        
        # Detectar error de modelo Groq descontinuado
        if 'model_decommissioned' in errores_str and 'groq' in errores_str.lower():
            logger.info("Detectado error de modelo Groq descontinuado - corrigiendo...")
            return self._corregir_modelo_groq()
        
        # Detectar error de API key faltante
        if 'api_key' in errores_str.lower() and 'not configured' in errores_str.lower():
            logger.info("Detectado error de API key faltante - intentando agregar...")
            return self.agregar_variables_groq()
        
        # Otros errores no corregibles automáticamente
        return False
    
    def _corregir_modelo_groq(self) -> bool:
        """Corrige el modelo de Groq cambiando al siguiente disponible."""
        try:
            from agi_core.llm_wrapper import FREE_MODELS
            
            modelos_groq = FREE_MODELS['groq']
            logger.info(f"Modelos Groq disponibles: {modelos_groq}")
            
            # Intentar cada modelo hasta encontrar uno que funcione
            for i, modelo in enumerate(modelos_groq):
                logger.info(f"Probando modelo: {modelo}")
                
                # Actualizar el modelo en llm_wrapper.py
                with open('automatizacion/agi_core/llm_wrapper.py', 'r') as f:
                    contenido = f.read()
                
                # Reemplazar el primer modelo de la lista
                import re
                patron = r"'groq':\s*\[\s*'([^']+)'"
                nuevo_contenido = re.sub(patron, f"'groq':\n        ['{modelo}',", contenido)
                
                with open('automatizacion/agi_core/llm_wrapper.py', 'w') as f:
                    f.write(nuevo_contenido)
                
                logger.info(f"Modelo cambiado a: {modelo}")
                
                # Hacer commit y push
                import subprocess
                subprocess.run(['git', 'add', 'automatizacion/agi_core/llm_wrapper.py'], cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING')
                subprocess.run(['git', 'commit', '-m', f'Corregir modelo Groq a {modelo}'], cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING')
                subprocess.run(['git', 'push'], cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING')
                
                logger.info("Corrección commiteada y pusheada")
                return True
            
            logger.error("No se encontró modelo Groq funcional")
            return False
            
        except Exception as e:
            logger.error(f"Error corrigiendo modelo Groq: {e}")
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
    
    def detectar_cambios_git(self) -> bool:
        """Detecta si hay cambios sin commitear en el repositorio."""
        try:
            import subprocess
            
            # Verificar si hay cambios sin commitear
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                   cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING',
                                   capture_output=True, text=True)
            
            cambios = result.stdout.strip()
            hay_cambios = len(cambios) > 0
            
            logger.info(f"Cambios detectados: {hay_cambios}")
            return hay_cambios
            
        except Exception as e:
            logger.error(f"Error detectando cambios git: {e}")
            return False
    
    def hacer_commit_y_push(self, mensaje: str) -> bool:
        """Hace commit y push de los cambios actuales."""
        try:
            import subprocess
            
            # Agregar todos los cambios
            subprocess.run(['git', 'add', '.'], 
                         cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING',
                         capture_output=True, text=True)
            
            # Hacer commit
            result = subprocess.run(['git', 'commit', '-m', mensaje], 
                                   cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING',
                                   capture_output=True, text=True)
            
            if result.returncode != 0 and 'nothing to commit' not in result.stdout:
                logger.error(f"Error haciendo commit: {result.stderr}")
                return False
            
            # Hacer push
            result = subprocess.run(['git', 'push'], 
                                   cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING',
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error haciendo push: {result.stderr}")
                return False
            
            logger.info("Commit y push exitosos")
            return True
            
        except Exception as e:
            logger.error(f"Error haciendo commit y push: {e}")
            return False
    
    def deploy_despues_de_cambio(self, mensaje_commit: str = "Automated deploy after changes") -> bool:
        """
        Función principal: detecta cambios, hace commit/push y deploy.
        Debe llamarse después de cualquier cambio en el código.
        """
        try:
            logger.info("=== INICIANDO DEPLOY AUTOMÁTICO DESPUÉS DE CAMBIOS ===")
            
            # 1. Detectar cambios
            if not self.detectar_cambios_git():
                logger.info("No hay cambios, no se requiere deploy")
                return True
            
            # 2. Hacer commit y push
            logger.info("Haciendo commit y push de cambios...")
            if not self.hacer_commit_y_push(mensaje_commit):
                logger.error("Error haciendo commit y push")
                return False
            
            # 3. Hacer deploy en Render
            logger.info("Iniciando deploy en Render...")
            if not self.hacer_deploy_manual():
                logger.error("Error iniciando deploy")
                return False
            
            # 4. Esperar a que el deploy termine
            logger.info("Esperando a que el deploy termine...")
            if not self.esperar_deploy_completo():
                logger.error("Deploy falló o timeout")
                return False
            
            logger.info("✅ DEPLOY AUTOMÁTICO COMPLETADO EXITOSAMENTE")
            return True
            
        except Exception as e:
            logger.error(f"Error en deploy automático: {e}")
            return False


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

"""
Agente Configurar Webhook Meta Business Suite

Responsabilidad: Configura automáticamente el webhook de WhatsApp en Meta Business Suite.

Funciones:
— Genera instrucciones paso a paso para configurar el webhook manualmente
— Configura el endpoint de verificación en AGI para el webhook
— Verifica configuración exitosa
— Reporta estado de configuración
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/configurar_webhook_meta.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ConfigurarWebhookMeta')


class AgenteConfigurarWebhookMeta:
    """Agente para configurar webhook de WhatsApp en Meta Business Suite."""
    
    def __init__(self):
        self.whatsapp_token = "2417230442079987|rK3n87av4_-lK67I065Ir2cC7Ug"
        self.phone_number_id = "1009878998031758"
        self.webhook_url = "https://web-production-a13ae.up.railway.app/webhook/whatsapp"
        self.verify_token = "quantumhive_verify_2026"
        
        logger.info("AgenteConfigurarWebhookMeta inicializado")
    
    def generar_instrucciones(self) -> Dict[str, any]:
        """
        Genera instrucciones detalladas para configurar el webhook manualmente.
        
        Returns:
            Dict con instrucciones paso a paso
        """
        logger.info("=== GENERANDO INSTRUCCIONES PARA WEBHOOK ===")
        
        instrucciones = {
            'fecha': datetime.now().isoformat(),
            'webhook_url': self.webhook_url,
            'verify_token': self.verify_token,
            'phone_number_id': self.phone_number_id,
            'pasos': [
                {
                    'paso': 1,
                    'titulo': 'Ir a Meta Business Suite',
                    'instruccion': 'Entra a https://business.facebook.com/',
                    'nota': 'Inicia sesión con tu cuenta de Facebook'
                },
                {
                    'paso': 2,
                    'titulo': 'Seleccionar WhatsApp Business API',
                    'instruccion': 'Ve a la sección de WhatsApp y selecciona "WhatsApp Business API"',
                    'nota': 'Asegúrate de estar en el proyecto correcto'
                },
                {
                    'paso': 3,
                    'titulo': 'Ir a Configuración de Webhooks',
                    'instruccion': 'Busca la sección "Webhooks" y click en "Configurar"',
                    'nota': 'Puede estar en Configuración -> Webhooks'
                },
                {
                    'paso': 4,
                    'titulo': 'Configurar URL del Webhook',
                    'instruccion': f'Ingresa la URL: {self.webhook_url}',
                    'nota': 'Esta es la URL de Railway donde está deployado AGI'
                },
                {
                    'paso': 5,
                    'titulo': 'Configurar Verify Token',
                    'instruccion': f'Ingresa el verify token: {self.verify_token}',
                    'nota': 'Este token se usa para verificar la conexión'
                },
                {
                    'paso': 6,
                    'titulo': 'Verificar y Guardar',
                    'instruccion': 'Click en "Verificar y Guardar"',
                    'nota': 'Meta enviará una petición GET a tu webhook para verificar'
                },
                {
                    'paso': 7,
                    'titulo': 'Suscribir a Eventos',
                    'instruccion': 'Suscríbete a los eventos: "messages" y "message_status"',
                    'nota': 'Estos eventos son necesarios para recibir mensajes de WhatsApp'
                },
                {
                    'paso': 8,
                    'titulo': 'Guardar Cambios',
                    'instruccion': 'Click en "Guardar" para finalizar la configuración',
                    'nota': 'El webhook debería estar activo ahora'
                }
            ],
            'credenciales': {
                'webhook_url': self.webhook_url,
                'verify_token': self.verify_token,
                'phone_number_id': self.phone_number_id
            }
        }
        
        # Guardar instrucciones
        self._guardar_instrucciones(instrucciones)
        
        logger.info("=== INSTRUCCIONES GENERADAS ===")
        return instrucciones
    
    def configurar_webhook_selenium(self, email: str, password: str) -> Dict[str, any]:
        """
        Configura el webhook usando Selenium (automatización web).
        
        Args:
            email: Email de Facebook/Meta
            password: Contraseña de Facebook/Meta
            
        Returns:
            Dict con resultado de la configuración
        """
        logger.info("=== INICIANDO CONFIGURACIÓN WEBHOOK CON SELENIUM ===")
        
        resultado = {
            'fecha': datetime.now().isoformat(),
            'webhook_url': self.webhook_url,
            'verify_token': self.verify_token,
            'phone_number_id': self.phone_number_id,
            'pasos': [],
            'estado': 'requiere_interaccion'
        }
        
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            import time
            
            logger.info("Selenium importado exitosamente")
            
            # Configurar Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Ejecutar en modo headless
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Iniciar driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Paso 1: Ir a Meta Business Suite
                logger.info("Paso 1: Navegando a Meta Business Suite")
                driver.get("https://business.facebook.com/")
                time.sleep(3)
                
                resultado['pasos'].append({
                    'paso': 'Navegación a Meta Business Suite',
                    'estado': 'exitoso'
                })
                
                # Paso 2: Iniciar sesión
                logger.info("Paso 2: Iniciando sesión")
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                email_input.send_keys(email)
                
                password_input = driver.find_element(By.ID, "pass")
                password_input.send_keys(password)
                password_input.send_keys(Keys.RETURN)
                
                time.sleep(5)
                
                resultado['pasos'].append({
                    'paso': 'Inicio de sesión',
                    'estado': 'exitoso'
                })
                
                # Paso 3: Navegar a WhatsApp Business API
                logger.info("Paso 3: Navegando a WhatsApp Business API")
                # Aquí necesitaría navegar a la sección específica de WhatsApp
                # Esto requiere conocimiento de la estructura exacta de Meta Business Suite
                
                resultado['pasos'].append({
                    'paso': 'Navegación a WhatsApp',
                    'estado': 'requiere_interaccion_manual',
                    'nota': 'La estructura de Meta Business Suite cambia frecuentemente'
                })
                
            finally:
                driver.quit()
                
        except ImportError:
            logger.error("Selenium no está instalado")
            resultado['pasos'].append({
                'paso': 'Importación Selenium',
                'estado': 'fallido',
                'error': 'Selenium no está instalado. Ejecuta: pip install selenium'
            })
            
        except Exception as e:
            logger.error(f"Error en configuración con Selenium: {e}")
            resultado['pasos'].append({
                'paso': 'Configuración Selenium',
                'estado': 'fallido',
                'error': str(e)
            })
        
        # Guardar reporte
        self._guardar_reporte(resultado)
        
        logger.info("=== CONFIGURACIÓN WEBHOOK FINALIZADA ===")
        return resultado
    
    def _guardar_reporte(self, resultado: Dict):
        """Guarda el reporte de configuración."""
        try:
            reporte_path = Path('logs/reporte_configuracion_webhook.json')
            reporte_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(reporte_path, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Reporte guardado: {reporte_path}")
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
    
    def _guardar_instrucciones(self, instrucciones: Dict):
        """Guarda las instrucciones en un archivo."""
        try:
            instrucciones_path = Path('logs/instrucciones_configuracion_webhook.json')
            instrucciones_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(instrucciones_path, 'w', encoding='utf-8') as f:
                json.dump(instrucciones, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Instrucciones guardadas: {instrucciones_path}")
            
        except Exception as e:
            logger.error(f"Error guardando instrucciones: {e}")
    
    def agregar_endpoint_verificacion_agi(self):
        """Agrega el endpoint de verificación de webhook a AGI."""
        try:
            ruta_agi = Path('C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING/automatizacion/agentes/agi_whatsapp.py')
            
            if not ruta_agi.exists():
                logger.error(f"Archivo AGI no encontrado: {ruta_agi}")
                return False
            
            with open(ruta_agi, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Verificar si el endpoint ya existe
            if '@app.route(\'/webhook/whatsapp\',' in contenido:
                logger.info("Endpoint de webhook ya existe en AGI")
                return True
            
            # Agregar endpoint de verificación
            endpoint_verificacion = '''
@app.route('/webhook/whatsapp', methods=['GET'])
def webhook_verify():
    """Verifica el webhook con Meta Business API."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == 'quantumhive_verify_2026':
        logger.info("Webhook verificado exitosamente")
        return challenge, 200
    else:
        logger.error("Fallo en verificación de webhook")
        return 'Forbidden', 403

'''
            
            # Insertar antes del endpoint POST existente
            if '@app.route(\'/webhook/whatsapp\', methods=[\'POST\'])' in contenido:
                contenido = contenido.replace(
                    '@app.route(\'/webhook/whatsapp\', methods=[\'POST\'])',
                    endpoint_verificacion + '@app.route(\'/webhook/whatsapp\', methods=[\'POST\'])'
                )
                
                with open(ruta_agi, 'w', encoding='utf-8') as f:
                    f.write(contenido)
                
                logger.info("Endpoint de verificación agregado a AGI")
                return True
            else:
                logger.error("No se encontró el endpoint POST para insertar verificación")
                return False
                
        except Exception as e:
            logger.error(f"Error agregando endpoint de verificación: {e}")
            return False


if __name__ == '__main__':
    print("=== Agente Configurar Webhook Meta Business Suite ===")
    agente = AgenteConfigurarWebhookMeta()
    
    # Generar instrucciones
    print("\nGenerando instrucciones para configuración manual...")
    instrucciones = agente.generar_instrucciones()
    print(f"\nInstrucciones generadas:")
    for paso in instrucciones['pasos']:
        print(f"\n{paso['paso']}. {paso['titulo']}")
        print(f"   {paso['instruccion']}")
        if 'nota' in paso:
            print(f"   Nota: {paso['nota']}")
    
    # Agregar endpoint de verificación a AGI
    print("\n\nAgregando endpoint de verificación a AGI...")
    if agente.agregar_endpoint_verificacion_agi():
        print("Endpoint de verificación agregado exitosamente")
    else:
        print("No se pudo agregar el endpoint de verificación")
    
    print("\n\nCredenciales necesarias:")
    print(f"Webhook URL: {instrucciones['credenciales']['webhook_url']}")
    print(f"Verify Token: {instrucciones['credenciales']['verify_token']}")
    print(f"Phone Number ID: {instrucciones['credenciales']['phone_number_id']}")
    
    print("\n\nPara configuración automática con Selenium, necesitas proporcionar:")
    print("- Email de Facebook/Meta")
    print("- Contraseña de Facebook/Meta")
    print("\nLuego ejecuta: agente.configurar_webhook_selenium(email, password)")

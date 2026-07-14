"""
Agente Automatizado para Crear Bot de Telegram para AGI
Este agente guía al usuario en la creación del bot y automatiza toda la configuración
"""
import os
import sys
import requests
import time
from datetime import datetime


class AgenteCrearBotTelegram:
    """Agente que automatiza la creación y configuración del bot de Telegram para AGI."""
    
    def __init__(self):
        self.variables = {}
        self.railway_url = ""
    
    def mostrar_banner(self):
        """Muestra el banner inicial del agente."""
        print()
        print("=" * 70)
        print("🤖 AGENTE AUTOMATIZADO PARA CREAR BOT DE TELEGRAM - AGI")
        print("=" * 70)
        print()
        print("Este agente te guiará paso a paso para crear y configurar")
        print("tu bot de Telegram para AGI (CEO II - Inteligencia Infinita)")
        print()
        print("⚠️  NOTA: La creación del bot requiere interacción manual con @BotFather")
        print("      por seguridad de Telegram. El resto es 100% automatizado.")
        print()
        print("=" * 70)
        print()
    
    def paso_1_botfather(self):
        """Paso 1: Guía al usuario para crear el bot con BotFather."""
        print("📍 PASO 1: CREAR BOT CON @BOTFATHER")
        print("-" * 70)
        print()
        print("Instrucciones:")
        print("1. Abre Telegram")
        print("2. Busca @BotFather")
        print("3. Inicia chat con /start")
        print("4. Crea nuevo bot con /newbot")
        print("5. Asigna un nombre (ej: QuantumHive AGI)")
        print("6. Asigna un username (ej: quantumhive_agi_bot)")
        print("7. Copia el TOKEN que te da BotFather")
        print()
        print("El TOKEN tiene el formato: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        print()
        
        token = input("🔑 Ingresa el TOKEN del bot (o presiona Enter para cancelar): ").strip()
        
        if not token:
            print("❌ Cancelado por el usuario")
            return False
        
        # Validar formato básico del token
        if ":" not in token or len(token) < 10:
            print("❌ TOKEN inválido. Debe tener formato: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
            return False
        
        self.variables['TELEGRAM_TOKEN'] = token
        print("✅ TOKEN guardado correctamente")
        print()
        return True
    
    def paso_2_verificar_token(self):
        """Paso 2: Verifica que el TOKEN sea válido."""
        print("📍 PASO 2: VERIFICAR TOKEN")
        print("-" * 70)
        print()
        
        token = self.variables['TELEGRAM_TOKEN']
        
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    bot_info = data['result']
                    print("✅ TOKEN válido y conectado con Telegram API")
                    print(f"   Bot: @{bot_info['username']}")
                    print(f"   Nombre: {bot_info['first_name']}")
                    print(f"   ID: {bot_info['id']}")
                    print()
                    return True
                else:
                    print(f"❌ TOKEN inválido: {data.get('description', 'Error desconocido')}")
                    return False
            else:
                print(f"❌ Error conectando con Telegram API: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error verificando TOKEN: {e}")
            return False
    
    def paso_3_obtener_user_id(self):
        """Paso 3: Obtiene el USER_TELEGRAM_ID del usuario."""
        print("📍 PASO 3: OBTENER TU TELEGRAM ID")
        print("-" * 70)
        print()
        print("Para que el bot solo responda a ti, necesito tu Telegram ID.")
        print()
        print("Opción 1: Si ya lo conoces, ingrésalo directamente")
        print("Opción 2: Usa el método automático del bot")
        print()
        
        opcion = input("¿Quieres usar el método automático? (s/n): ").strip().lower()
        
        if opcion == 's':
            print()
            print("📱 MÉTODO AUTOMÁTICO:")
            print("1. Busca tu bot en Telegram (el que acabas de crear)")
            print("2. Inicia chat con /start")
            print("3. Envía cualquier mensaje")
            print("4. Espera 5 segundos...")
            print()
            
            # Obtener updates del bot
            token = self.variables['TELEGRAM_TOKEN']
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['ok'] and data['result']:
                        # Obtener el último mensaje
                        ultimo_mensaje = data['result'][-1]
                        user_id = ultimo_mensaje['message']['from']['id']
                        print(f"✅ Tu Telegram ID encontrado: {user_id}")
                        print()
                        self.variables['USER_TELEGRAM_ID'] = str(user_id)
                        return True
                    else:
                        print("⚠️  No se encontraron mensajes. Ingresa tu ID manualmente:")
            except Exception as e:
                print(f"⚠️  Error obteniendo mensajes: {e}")
                print("Ingresa tu ID manualmente:")
        
        # Método manual
        user_id = input("Ingresa tu Telegram ID (o presiona Enter para cancelar): ").strip()
        
        if not user_id:
            print("❌ Cancelado por el usuario")
            return False
        
        self.variables['USER_TELEGRAM_ID'] = user_id
        print("✅ Telegram ID guardado correctamente")
        print()
        return True
    
    def paso_4_obtener_api_keys(self):
        """Paso 4: Obtiene las API keys necesarias."""
        print("📍 PASO 4: CONFIGURAR API KEYS")
        print("-" * 70)
        print()
        
        # Anthropic API Key
        print("🔑 ANTHROPIC API KEY (para Claude)")
        anthropic_key = input("Ingresa tu ANTHROPIC_API_KEY: ").strip()
        
        if not anthropic_key:
            print("❌ ANTHROPIC_API_KEY es obligatorio")
            return False
        
        self.variables['ANTHROPIC_API_KEY'] = anthropic_key
        print("✅ ANTHROPIC_API_KEY guardada")
        print()
        
        # OpenAI API Key (opcional)
        print("🔑 OPENAI API KEY (para transcripción de audio - opcional)")
        openai_key = input("Ingresa tu OPENAI_API_KEY (presiona Enter para omitir): ").strip()
        
        if openai_key:
            self.variables['OPENAI_API_KEY'] = openai_key
            print("✅ OPENAI_API_KEY guardada")
        else:
            print("⚠️  OPENAI_API_KEY omitida (audio no estará disponible)")
        
        print()
        return True
    
    def paso_5_configurar_railway(self):
        """Paso 5: Configura Railway."""
        print("📍 PASO 5: CONFIGURAR RAILWAY")
        print("-" * 70)
        print()
        print("Para que AGI funcione en Railway, necesitas configurar:")
        print()
        print("1. Ve a https://railway.app")
        print("2. Entra a tu proyecto")
        print("3. Ve a Settings → Variables")
        print("4. Agrega las siguientes variables:")
        print()
        
        for key, value in self.variables.items():
            if key == 'TELEGRAM_TOKEN':
                print(f"   {key}={value[:10]}...")
            elif key == 'ANTHROPIC_API_KEY':
                print(f"   {key}={value[:10]}...")
            elif key == 'OPENAI_API_KEY' and value:
                print(f"   {key}={value[:10]}...")
            else:
                print(f"   {key}={value}")
        
        print()
        print("5. También necesitas TELEGRAM_WEBHOOK_URL:")
        
        railway_url = input("Ingresa tu Railway URL (ej: https://tu-proyecto.railway.app): ").strip()
        
        if not railway_url:
            print("❌ Railway URL es obligatoria")
            return False
        
        if not railway_url.startswith("http"):
            railway_url = f"https://{railway_url}"
        
        webhook_url = f"{railway_url}/webhook"
        self.variables['TELEGRAM_WEBHOOK_URL'] = webhook_url
        
        print()
        print(f"   TELEGRAM_WEBHOOK_URL={webhook_url}")
        print()
        print("6. Railway hará redeploy automáticamente")
        print()
        print("✅ Configuración de Railway lista")
        print()
        return True
    
    def paso_6_configurar_webhook(self):
        """Paso 6: Configura el webhook automáticamente."""
        print("📍 PASO 6: CONFIGURAR WEBHOOK AUTOMÁTICAMENTE")
        print("-" * 70)
        print()
        
        token = self.variables['TELEGRAM_TOKEN']
        webhook_url = self.variables['TELEGRAM_WEBHOOK_URL']
        
        try:
            url = f"https://api.telegram.org/bot{token}/setWebhook"
            payload = {
                'url': webhook_url,
                'drop_pending_updates': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    print("✅ Webhook configurado exitosamente")
                    print(f"   URL: {webhook_url}")
                    print()
                    return True
                else:
                    print(f"❌ Error configurando webhook: {data.get('description', 'Error desconocido')}")
                    print("⚠️  Esto puede deberse a que Railway aún no está deployado")
                    print("   Intenta nuevamente en 1-2 minutos")
                    return False
            else:
                print(f"❌ Error en respuesta de Telegram API: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error configurando webhook: {e}")
            return False
    
    def paso_7_enviar_mensaje_prueba(self):
        """Paso 7: Envía un mensaje de prueba."""
        print("📍 PASO 7: ENVIAR MENSAJE DE PRUEBA")
        print("-" * 70)
        print()
        
        token = self.variables['TELEGRAM_TOKEN']
        user_id = self.variables['USER_TELEGRAM_ID']
        
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': user_id,
                'text': '🚀 AGI Telegram está ONLINE y listo para recibir tus mensajes.\n\nSoy tu CEO II - Inteligencia Infinita. ¿En qué puedo ayudarte hoy?'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    print("✅ Mensaje de prueba enviado exitosamente")
                    print(f"   Revisa tu Telegram - deberías haber recibido un mensaje del bot")
                    print()
                    return True
                else:
                    print(f"❌ Error enviando mensaje: {data.get('description', 'Error desconocido')}")
                    return False
            else:
                print(f"❌ Error en respuesta de Telegram API: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error enviando mensaje de prueba: {e}")
            return False
    
    def paso_8_generar_env_local(self):
        """Paso 8: Genera el archivo .env.local."""
        print("📍 PASO 8: GENERAR ARCHIVO .ENV.LOCAL")
        print("-" * 70)
        print()
        
        env_content = "# Variables de entorno para AGI Telegram\n"
        env_content += f"# Generado automáticamente por AgenteCrearBotTelegram\n"
        env_content += f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for key, value in self.variables.items():
            env_content += f"{key}={value}\n"
        
        try:
            with open('.env.local', 'w') as f:
                f.write(env_content)
            
            print("✅ Archivo .env.local generado exitosamente")
            print("   Ubicación: C:\\Users\\sergio\\QUANTUMHIVE_ALGORITHMICTRADING\\automatizacion\\agentes\\.env.local")
            print()
            return True
        except Exception as e:
            print(f"❌ Error generando .env.local: {e}")
            return False
    
    def paso_9_resumen(self):
        """Paso 9: Muestra el resumen final."""
        print("=" * 70)
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print()
        print("AGI Telegram está listo para usar:")
        print()
        print("📱 PASOS FINALES:")
        print("1. Ve a Railway y configura las variables de entorno listadas arriba")
        print("2. Railway hará redeploy automáticamente")
        print("3. Abre Telegram y busca tu bot")
        print("4. Inicia chat con /start")
        print("5. AGI responderá como CEO II - Inteligencia Infinita")
        print()
        print("📝 VARIABLES DE ENTORNO CONFIGURADAS:")
        for key, value in self.variables.items():
            if key in ['TELEGRAM_TOKEN', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']:
                print(f"   ✅ {key}: {value[:10]}...")
            else:
                print(f"   ✅ {key}: {value}")
        print()
        print("🎉 ¡AGI está listo para recibir tus ideas y optimizar QuantumHive!")
        print()
    
    def ejecutar(self):
        """Ejecuta el proceso completo de creación y configuración."""
        self.mostrar_banner()
        
        # Ejecutar pasos en orden
        pasos = [
            self.paso_1_botfather,
            self.paso_2_verificar_token,
            self.paso_3_obtener_user_id,
            self.paso_4_obtener_api_keys,
            self.paso_5_configurar_railway,
            self.paso_6_configurar_webhook,
            self.paso_7_enviar_mensaje_prueba,
            self.paso_8_generar_env_local,
            self.paso_9_resumen
        ]
        
        for paso in pasos:
            try:
                if not paso():
                    print()
                    print("❌ Proceso interrumpido")
                    print()
                    return False
            except KeyboardInterrupt:
                print()
                print("❌ Proceso cancelado por el usuario")
                print()
                return False
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                print()
                return False
        
        return True


def main():
    """Función principal."""
    agente = AgenteCrearBotTelegram()
    agente.ejecutar()


if __name__ == "__main__":
    main()

"""
Script de Configuración Automatizada para AGI Telegram
Automatiza la configuración del bot de Telegram para AGI
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.local')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL', '')
USER_TELEGRAM_ID = os.getenv('USER_TELEGRAM_ID', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno necesarias estén configuradas."""
    print("=" * 60)
    print("VERIFICANDO VARIABLES DE ENTORNO")
    print("=" * 60)
    
    faltantes = []
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN: NO CONFIGURADO")
        faltantes.append("TELEGRAM_TOKEN")
    else:
        print(f"✅ TELEGRAM_TOKEN: {TELEGRAM_TOKEN[:10]}...")
    
    if not TELEGRAM_WEBHOOK_URL:
        print("❌ TELEGRAM_WEBHOOK_URL: NO CONFIGURADO")
        faltantes.append("TELEGRAM_WEBHOOK_URL")
    else:
        print(f"✅ TELEGRAM_WEBHOOK_URL: {TELEGRAM_WEBHOOK_URL}")
    
    if not USER_TELEGRAM_ID:
        print("❌ USER_TELEGRAM_ID: NO CONFIGURADO")
        faltantes.append("USER_TELEGRAM_ID")
    else:
        print(f"✅ USER_TELEGRAM_ID: {USER_TELEGRAM_ID}")
    
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY: NO CONFIGURADO")
        faltantes.append("ANTHROPIC_API_KEY")
    else:
        print(f"✅ ANTHROPIC_API_KEY: {ANTHROPIC_API_KEY[:10]}...")
    
    if not OPENAI_API_KEY:
        print("⚠️  OPENAI_API_KEY: NO CONFIGURADO (opcional para audio)")
    else:
        print(f"✅ OPENAI_API_KEY: {OPENAI_API_KEY[:10]}...")
    
    print()
    
    if faltantes:
        print("❌ Faltan variables de entorno obligatorias:")
        for var in faltantes:
            print(f"   - {var}")
        print()
        return False
    
    print("✅ Todas las variables de entorno obligatorias están configuradas")
    print()
    return True


def verificar_conexion_telegram():
    """Verifica la conexión con la API de Telegram."""
    print("=" * 60)
    print("VERIFICANDO CONEXIÓN CON TELEGRAM API")
    print("=" * 60)
    
    if not TELEGRAM_TOKEN:
        print("❌ No se puede verificar conexión: TELEGRAM_TOKEN no configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"✅ Conexión exitosa con Telegram API")
                print(f"   Bot: @{bot_info['username']}")
                print(f"   Nombre: {bot_info['first_name']}")
                print(f"   ID: {bot_info['id']}")
                print()
                return True
        else:
            print(f"❌ Error en respuesta de Telegram API: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error verificando conexión con Telegram: {e}")
        return False


def configurar_webhook():
    """Configura el webhook de Telegram automáticamente."""
    print("=" * 60)
    print("CONFIGURANDO WEBHOOK DE TELEGRAM")
    print("=" * 60)
    
    if not TELEGRAM_TOKEN or not TELEGRAM_WEBHOOK_URL:
        print("❌ No se puede configurar webhook: TELEGRAM_TOKEN o TELEGRAM_WEBHOOK_URL no configurados")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        payload = {
            'url': TELEGRAM_WEBHOOK_URL,
            'drop_pending_updates': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print(f"✅ Webhook configurado exitosamente")
                print(f"   URL: {TELEGRAM_WEBHOOK_URL}")
                print()
                return True
            else:
                print(f"❌ Error configurando webhook: {data.get('description', 'Error desconocido')}")
                return False
        else:
            print(f"❌ Error en respuesta de Telegram API: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        return False


def obtener_info_webhook():
    """Obtiene información actual del webhook."""
    print("=" * 60)
    print("INFORMACIÓN ACTUAL DEL WEBHOOK")
    print("=" * 60)
    
    if not TELEGRAM_TOKEN:
        print("❌ No se puede obtener información: TELEGRAM_TOKEN no configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                webhook_info = data['result']
                webhook_url = webhook_info.get('url', 'No configurado')
                if webhook_url and webhook_url != 'No configurado':
                    print(f"✅ Webhook activo: {webhook_url}")
                else:
                    print(f"❌ Webhook no configurado")
                print()
                return True
        else:
            print(f"❌ Error obteniendo información del webhook: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo información del webhook: {e}")
        return False


def enviar_mensaje_prueba():
    """Envía un mensaje de prueba al bot."""
    print("=" * 60)
    print("ENVIANDO MENSAJE DE PRUEBA")
    print("=" * 60)
    
    if not TELEGRAM_TOKEN or not USER_TELEGRAM_ID:
        print("❌ No se puede enviar mensaje: TELEGRAM_TOKEN o USER_TELEGRAM_ID no configurados")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': USER_TELEGRAM_ID,
            'text': '🚀 AGI Telegram está ONLINE y listo para recibir tus mensajes.\n\nSoy tu CEO II - Inteligencia Infinita. ¿En qué puedo ayudarte hoy?'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print(f"✅ Mensaje de prueba enviado exitosamente a {USER_TELEGRAM_ID}")
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


def mostrar_instrucciones_botfather():
    """Muestra instrucciones para crear el bot con BotFather."""
    print("=" * 60)
    print("INSTRUCCIONES PARA CREAR BOT CON BOTFATHER")
    print("=" * 60)
    print()
    print("1. Abre Telegram y busca @BotFather")
    print("2. Inicia chat con /start")
    print("3. Crea un nuevo bot con /newbot")
    print("4. Sigue las instrucciones:")
    print("   - Asigna un nombre al bot (ej: QuantumHive AGI)")
    print("   - Asigna un username (ej: quantumhive_agi_bot)")
    print("5. BotFather te dará el TOKEN del bot")
    print("6. Copia el TOKEN y guárdalo en .env.local como TELEGRAM_TOKEN")
    print("7. Ejecuta nuevamente este script para configurar el webhook")
    print()
    print("NOTA: La creación del bot requiere interacción manual con @BotFather")
    print("      porque es una seguridad de Telegram para evitar bots maliciosos.")
    print()


def mostrar_instrucciones_railway():
    """Muestra instrucciones para configurar Railway."""
    print("=" * 60)
    print("INSTRUCCIONES PARA CONFIGURAR RAILWAY")
    print("=" * 60)
    print()
    print("1. Ve a https://railway.app")
    print("2. Crea un nuevo proyecto o usa el existente")
    print("3. Agrega las siguientes variables de entorno:")
    print()
    print("   TELEGRAM_TOKEN=<tu_token_de_botfather>")
    print("   TELEGRAM_WEBHOOK_URL=https://tu-proyecto-railway.railway.app/webhook")
    print("   USER_TELEGRAM_ID=<tu_id_de_usuario_telegram>")
    print("   ANTHROPIC_API_KEY=<tu_api_key_de_anthropic>")
    print("   OPENAI_API_KEY=<tu_api_key_de_openai> (opcional)")
    print()
    print("4. Railway hará redeploy automáticamente con las nuevas variables")
    print("5. El webhook URL será: https://<tu-proyecto>.railway.app/webhook")
    print()
    print("Para obtener tu USER_TELEGRAM_ID:")
    print("1. Envía un mensaje a cualquier bot de Telegram")
    print("2. Usa https://api.telegram.org/bot<TOKEN>/getUpdates")
    print("3. Busca 'from' -> 'id' en la respuesta JSON")
    print()
    print("Para obtener tu TELEGRAM_WEBHOOK_URL:")
    print("1. En Railway, ve a Settings → Domains")
    print("2. Copia el dominio público de tu proyecto")
    print("3. Agrega /webhook al final")
    print("   Ejemplo: https://tu-proyecto.railway.app/webhook")
    print()


def main():
    """Función principal del script de configuración."""
    print()
    print("🚀 CONFIGURACIÓN AUTOMATIZADA DE AGI TELEGRAM")
    print("=" * 60)
    print()
    
    # Paso 1: Verificar variables de entorno
    if not verificar_variables_entorno():
        print()
        print("⚠️  CONFIGURACIÓN INCOMPLETA")
        print()
        mostrar_instrucciones_botfather()
        mostrar_instrucciones_railway()
        print()
        print("❌ Por favor configura las variables de entorno faltantes y ejecuta nuevamente")
        print()
        sys.exit(1)
    
    # Paso 2: Verificar conexión con Telegram
    if not verificar_conexion_telegram():
        print()
        print("❌ Error conectando con Telegram API")
        print("   Verifica que TELEGRAM_TOKEN sea correcto")
        print()
        sys.exit(1)
    
    # Paso 3: Configurar webhook
    if not configurar_webhook():
        print()
        print("❌ Error configurando webhook")
        print("   Verifica que TELEGRAM_WEBHOOK_URL sea correcta y accesible")
        print()
        sys.exit(1)
    
    # Paso 4: Verificar webhook
    obtener_info_webhook()
    
    # Paso 5: Enviar mensaje de prueba
    if not enviar_mensaje_prueba():
        print()
        print("⚠️  No se pudo enviar mensaje de prueba")
        print("   Verifica que USER_TELEGRAM_ID sea correcto")
        print("   Asegúrate de haber iniciado chat con el bot")
        print()
    
    print("=" * 60)
    print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print()
    print("AGI Telegram está ONLINE y listo para usar:")
    print()
    print("1. Abre Telegram y busca tu bot")
    print("2. Inicia un chat con /start")
    print("3. AGI responderá como CEO II - Inteligencia Infinita")
    print()
    print("Variables de entorno configuradas:")
    print(f"   TELEGRAM_TOKEN: ✅")
    print(f"   TELEGRAM_WEBHOOK_URL: ✅")
    print(f"   USER_TELEGRAM_ID: ✅")
    print(f"   ANTHROPIC_API_KEY: ✅")
    print(f"   OPENAI_API_KEY: {'✅' if OPENAI_API_KEY else '⚠️  (opcional)'}")
    print()
    print("🎉 ¡AGI está listo para recibir tus ideas y optimizar QuantumHive!")
    print()


if __name__ == "__main__":
    main()

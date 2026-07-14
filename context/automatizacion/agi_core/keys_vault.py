"""
KeysVault — QuantumHive
Gestor centralizado de APIs, tokens y credenciales.
Almacena y recupera credenciales de forma segura.
"""

import os
import json
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

logger = logging.getLogger(__name__)


class KeysVault:
    """Gestor centralizado de credenciales de QuantumHive."""
    
    def __init__(self):
        self.credenciales = self._cargar_credenciales()
        logger.info("KeysVault inicializado")
    
    def _cargar_credenciales(self) -> Dict:
        """Carga credenciales desde variables de entorno y archivo vault."""
        credenciales = {}
        
        # Cargar desde variables de entorno
        credenciales.update({
            # Telegram
            'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN', ''),
            'USER_TELEGRAM_ID': os.getenv('USER_TELEGRAM_ID', ''),
            'TELEGRAM_WEBHOOK_URL': os.getenv('TELEGRAM_WEBHOOK_URL', ''),
            
            # Anthropic (Claude)
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
            
            # OpenAI
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            
            # Groq
            'GROQ_API_KEY': os.getenv('GROQ_API_KEY', ''),
            
            # OpenRouter
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
            
            # Render
            'RENDER_API_KEY': os.getenv('RENDER_API_KEY', ''),
            'RENDER_SERVICE_ID': os.getenv('RENDER_SERVICE_ID', ''),
            
            # Supabase
            'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
            'SUPABASE_KEY': os.getenv('SUPABASE_KEY', ''),
            
            # PropFirms (ejemplos)
            'FTMO_API_KEY': os.getenv('FTMO_API_KEY', ''),
            'FUNDINGPIPS_API_KEY': os.getenv('FUNDINGPIPS_API_KEY', ''),
            'APEX_API_KEY': os.getenv('APEX_API_KEY', ''),
            
            # Trading
            'TRADINGVIEW_API_KEY': os.getenv('TRADINGVIEW_API_KEY', ''),
            'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY', ''),
            'BINANCE_SECRET': os.getenv('BINANCE_SECRET', ''),
            
            # Email
            'GMAIL_API_KEY': os.getenv('GMAIL_API_KEY', ''),
            'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD', ''),
            
            # WhatsApp
            'WHATSAPP_API_KEY': os.getenv('WHATSAPP_API_KEY', ''),
            'WHATSAPP_PHONE_ID': os.getenv('WHATSAPP_PHONE_ID', ''),
            
            # Instagram
            'INSTAGRAM_ACCESS_TOKEN': os.getenv('INSTAGRAM_ACCESS_TOKEN', ''),
            
            # Stripe (Pagos)
            'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY', ''),
            'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY', ''),
        })
        
        # Cargar desde archivo vault.json si existe
        vault_path = Path(__file__).parent.parent / 'vault.json'
        if vault_path.exists():
            try:
                with open(vault_path, 'r') as f:
                    vault_data = json.load(f)
                    credenciales.update(vault_data)
                    logger.info(f"Credenciales cargadas desde vault.json: {len(vault_data)}")
            except Exception as e:
                logger.warning(f"Error cargando vault.json: {e}")
        
        return credenciales
    
    def obtener(self, key: str, default: str = '') -> str:
        """Obtiene una credencial por su clave."""
        valor = self.credenciales.get(key, default)
        if not valor:
            logger.warning(f"Credencial {key} no encontrada")
        return valor
    
    def verificar(self, key: str) -> bool:
        """Verifica si una credencial existe y no está vacía."""
        valor = self.credenciales.get(key, '')
        return bool(valor and len(valor) > 5)
    
    def obtener_telegram(self) -> Dict:
        """Obtiene todas las credenciales de Telegram."""
        return {
            'token': self.obtener('TELEGRAM_TOKEN'),
            'user_id': self.obtener('USER_TELEGRAM_ID'),
            'webhook_url': self.obtener('TELEGRAM_WEBHOOK_URL')
        }
    
    def obtener_anthropic(self) -> Dict:
        """Obtiene credenciales de Anthropic."""
        return {
            'api_key': self.obtener('ANTHROPIC_API_KEY')
        }
    
    def obtener_groq(self) -> Dict:
        """Obtiene credenciales de Groq."""
        return {
            'api_key': self.obtener('GROQ_API_KEY')
        }
    
    def obtener_render(self) -> Dict:
        """Obtiene credenciales de Render."""
        return {
            'api_key': self.obtener('RENDER_API_KEY'),
            'service_id': self.obtener('RENDER_SERVICE_ID')
        }
    
    def obtener_supabase(self) -> Dict:
        """Obtiene credenciales de Supabase."""
        return {
            'url': self.obtener('SUPABASE_URL'),
            'key': self.obtener('SUPABASE_KEY')
        }
    
    def obtener_propfirms(self) -> Dict:
        """Obtiene credenciales de PropFirms."""
        return {
            'ftmo': self.obtener('FTMO_API_KEY'),
            'fundingpips': self.obtener('FUNDINGPIPS_API_KEY'),
            'apex': self.obtener('APEX_API_KEY')
        }
    
    def obtener_trading(self) -> Dict:
        """Obtiene credenciales de trading."""
        return {
            'tradingview': self.obtener('TRADINGVIEW_API_KEY'),
            'binance_api': self.obtener('BINANCE_API_KEY'),
            'binance_secret': self.obtener('BINANCE_SECRET')
        }
    
    def obtener_pagos(self) -> Dict:
        """Obtiene credenciales de pagos (Stripe)."""
        return {
            'stripe_secret': self.obtener('STRIPE_SECRET_KEY'),
            'stripe_publishable': self.obtener('STRIPE_PUBLISHABLE_KEY')
        }
    
    def verificar_todas(self) -> Dict[str, bool]:
        """Verifica el estado de todas las credenciales importantes."""
        estado = {
            'telegram': self.verificar('TELEGRAM_TOKEN'),
            'anthropic': self.verificar('ANTHROPIC_API_KEY'),
            'groq': self.verificar('GROQ_API_KEY'),
            'render': self.verificar('RENDER_API_KEY'),
            'render_service': self.verificar('RENDER_SERVICE_ID'),
            'supabase': self.verificar('SUPABASE_URL') and self.verificar('SUPABASE_KEY'),
        }
        return estado
    
    def reporte_estado(self) -> str:
        """Genera un reporte del estado de las credenciales."""
        estado = self.verificar_todas()
        reporte = "=== REPORTE KEYSVAULT ===\n\n"
        
        for servicio, configurado in estado.items():
            icono = "✅" if configurado else "❌"
            reporte += f"{icono} {servicio.upper()}: {'Configurado' if configurado else 'No configurado'}\n"
        
        return reporte
    
    def guardar_vault_json(self, ruta: Optional[str] = None):
        """Guarda las credenciales en un archivo JSON (para backup)."""
        vault_path = Path(ruta) if ruta else Path(__file__).parent.parent / 'vault.json'
        
        # Filtrar credenciales vacías
        vault_data = {k: v for k, v in self.credenciales.items() if v}
        
        try:
            with open(vault_path, 'w') as f:
                json.dump(vault_data, f, indent=2)
            logger.info(f"Vault guardado en {vault_path}")
        except Exception as e:
            logger.error(f"Error guardando vault: {e}")


# Instancia global
keys_vault = KeysVault()


if __name__ == "__main__":
    print("=== KEYSVAULT - QUANTUMHIVE ===\n")
    
    vault = KeysVault()
    
    # Reporte de estado
    print(vault.reporte_estado())
    
    # Ejemplos de uso
    print("\n📋 EJEMPLOS DE USO:")
    print(f"Telegram Token: {vault.obtener('TELEGRAM_TOKEN')[:20]}...")
    print(f"Groq API Key: {vault.obtener('GROQ_API_KEY')[:20]}...")
    print(f"Render API Key: {vault.obtener('RENDER_API_KEY')[:20]}...")
    
    # Guardar backup
    print("\n💾 Guardando backup en vault.json...")
    vault.guardar_vault_json()
    print("✅ Backup guardado")

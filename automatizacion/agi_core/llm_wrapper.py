"""
LLM Wrapper — QuantumHive AGI
Wrapper universal para motores IA (Groq, OpenRouter, Ollama)
Permite cambiar de motor IA sin modificar la estructura AGI ni el system prompt.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Importar agente LLM Manager para cambio automático de motores
try:
    from automatizacion.agentes.agente_llm_manager import report_llm_success, report_llm_error, get_current_llm_engine
    LLM_MANAGER_AVAILABLE = True
except ImportError:
    LLM_MANAGER_AVAILABLE = False
    logger.warning("Agente LLM Manager no disponible - cambio automático de motores deshabilitado")

# Configuración de motores IA
LLM_ENGINE = os.getenv('LLM_ENGINE', 'groq').lower()  # 'groq', 'openrouter', 'ollama'
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

# Modelos gratuitos recomendados
FREE_MODELS = {
    'openrouter': [
        'meta-llama/llama-3-8b-instruct:free',
        'mistralai/mistral-7b-instruct:free',
        'google/gemma-7b-it:free',
    ],
    'groq': [
        'llama-3.3-70b-versatile',
        'llama-3.1-8b-instant',
        'qwen/qwen3-32b',
    ],
    'ollama': [
        'llama3:8b',
        'mistral:7b',
        'gemma:7b',
    ]
}


@dataclass
class LLMMessage:
    """Mensaje estandarizado para cualquier motor IA."""
    role: str  # 'user', 'assistant', 'system'
    content: str


class LLMWrapper:
    """Wrapper universal para motores IA."""
    
    def __init__(self, engine: str = LLM_ENGINE):
        self.engine = engine
        self.client = None
        self._inicializar_cliente()
        
    def _inicializar_cliente(self):
        """Inicializa el cliente según el motor seleccionado: Groq (Principal) → OpenRouter (Backup) → Error Real."""
        try:
            if self.engine == 'groq':
                self._inicializar_groq()
            elif self.engine == 'openrouter':
                self._inicializar_openrouter()
            elif self.engine == 'ollama':
                self._inicializar_ollama()
            else:
                logger.warning(f"Motor IA desconocido: {self.engine}. Usando Groq como principal.")
                self._inicializar_groq()
        except Exception as e:
            logger.error(f"Error inicializando motor IA {self.engine}: {e}")
            logger.info("Intentando fallback a OpenRouter...")
            self._inicializar_openrouter()
    
    def _inicializar_groq(self):
        """Inicializa cliente Groq (motor principal - muy rápido, modelos gratuitos)."""
        try:
            from groq import Groq
            if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
                self.client = Groq(api_key=GROQ_API_KEY)
                self.engine = 'groq'
                self.model = FREE_MODELS['groq'][0]  # Primer modelo gratuito
                logger.info(f"✅ Motor IA: Groq ({self.model}) - GRATUITO - PRINCIPAL")
            else:
                raise ValueError("GROQ_API_KEY no configurada")
        except Exception as e:
            logger.warning(f"Groq no disponible: {e}")
            # Fallback a OpenRouter
            logger.info("Intentando fallback a OpenRouter...")
            self._inicializar_openrouter()
    
    def _inicializar_openrouter(self):
        """Inicializa cliente OpenRouter (motor backup - modelos gratuitos)."""
        try:
            from openai import OpenAI
            if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 10:
                self.client = OpenAI(
                    api_key=OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1"
                )
                self.engine = 'openrouter'
                self.model = FREE_MODELS['openrouter'][0]  # Primer modelo gratuito
                logger.info(f"✅ Motor IA: OpenRouter ({self.model}) - GRATUITO - BACKUP")
            else:
                raise ValueError("OPENROUTER_API_KEY no configurada")
        except Exception as e:
            logger.error(f"OpenRouter no disponible: {e}")
            raise RuntimeError("No se pudo inicializar ningún motor LLM (Groq y OpenRouter fallaron)")
    
    def _inicializar_ollama(self):
        """Inicializa cliente Ollama (local, totalmente gratuito)."""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=OLLAMA_BASE_URL,
                api_key="ollama"  # Ollama no requiere API key
            )
            self.engine = 'ollama'
            self.model = FREE_MODELS['ollama'][0]  # Primer modelo
            logger.info(f"✅ Motor IA: Ollama ({self.model}) - LOCAL GRATUITO")
        except Exception as e:
            logger.error(f"Ollama no disponible: {e}")
            raise RuntimeError("Ollama no disponible - no se pudo inicializar motor LLM")
    
    def messages_create(self, messages: List[LLMMessage], **kwargs) -> str:
        """
        Envía mensajes al motor IA (Groq/OpenRouter/Ollama) y retorna la respuesta.
        """
        if not self.client:
            raise RuntimeError("No hay cliente IA disponible")
        
        try:
            if self.engine in ['openrouter', 'groq', 'ollama']:
                response = self._openai_compatible_create(messages, **kwargs)
            else:
                raise ValueError(f"Motor no soportado: {self.engine}")
            
            # Reportar éxito al agente LLM Manager
            if LLM_MANAGER_AVAILABLE:
                report_llm_success(self.engine)
            
            return response
        except Exception as e:
            error_str = str(e)
            is_rate_limit = 'rate limit' in error_str.lower() or '429' in error_str
            
            # Reportar error al agente LLM Manager
            if LLM_MANAGER_AVAILABLE:
                report_llm_error(self.engine, error_str, is_rate_limit=is_rate_limit)
            
            logger.error(f"Error en messages_create: {e}")
            raise
    
    def _openai_compatible_create(self, messages: List[LLMMessage], **kwargs) -> str:
        """Usa API compatible con OpenAI (OpenRouter, Groq, Ollama)."""
        # Convertir LLMMessage a formato OpenAI
        openai_messages = []
        
        for msg in messages:
            openai_messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        model = kwargs.get('model', getattr(self, 'model', 'llama3-8b-8192'))
        
        response = self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            max_tokens=kwargs.get('max_tokens', 4096),
            temperature=kwargs.get('temperature', 0.7)
        )
        
        return response.choices[0].message.content
    
    def cambiar_motor(self, nuevo_motor: str):
        """Cambia el motor IA en tiempo de ejecución."""
        logger.info(f"Cambiando motor IA de {self.engine} a {nuevo_motor}")
        self.engine = nuevo_motor.lower()
        self._inicializar_cliente()


# Instancia global
llm_wrapper = LLMWrapper()

# Función de compatibilidad para código existente
def get_llm_client():
    """Retorna el cliente IA configurado (compatible con código existente)."""
    return llm_wrapper.client


def get_llm_engine():
    """Retorna el motor IA actual."""
    return llm_wrapper.engine


def is_free_engine():
    """Verifica si el motor actual es gratuito."""
    return llm_wrapper.engine in ['openrouter', 'groq', 'ollama']


if __name__ == "__main__":
    # Test del wrapper
    print("=== TEST LLM WRAPPER ===")
    print(f"Motor actual: {llm_wrapper.engine}")
    print(f"Es gratuito: {is_free_engine()}")
    
    # Test de mensaje
    test_messages = [
        LLMMessage(role='system', content='Eres un asistente útil.'),
        LLMMessage(role='user', content='Hola, ¿cómo estás?')
    ]
    
    try:
        respuesta = llm_wrapper.messages_create(test_messages)
        print(f"\nRespuesta: {respuesta}")
    except Exception as e:
        print(f"\nError en test: {e}")

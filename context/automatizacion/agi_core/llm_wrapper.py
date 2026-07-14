"""
LLM Wrapper — QuantumHive AGI
Wrapper universal para motores IA (Groq, Gemini, OpenRouter, Ollama)
Rotacion automatica: Groq -> Gemini -> OpenRouter -> Ollama
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

try:
    from automatizacion.agentes.agente_llm_manager import report_llm_success, report_llm_error, get_current_llm_engine
    LLM_MANAGER_AVAILABLE = True
except ImportError:
    LLM_MANAGER_AVAILABLE = False

# Motores IA
LLM_ENGINE = os.getenv('LLM_ENGINE', 'gemini').lower()
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

FREE_MODELS = {
    'groq': ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'qwen/qwen3-32b'],
    'gemini': ['gemini-2.5-flash', 'gemini-2.5-flash-lite'],
    'openrouter': ['meta-llama/llama-3.1-8b-instruct:free', 'mistralai/mistral-7b-instruct:free', 'google/gemma-7b-it:free'],
    'ollama': ['llama3:8b', 'mistral:7b', 'gemma:7b'],
}


@dataclass
class LLMMessage:
    role: str
    content: str


class LLMWrapper:
    def __init__(self, engine: str = None):
        self.engine = os.getenv('LLM_ENGINE', 'gemini').lower() if engine is None else engine.lower()
        self.client = None
        self.model = None
        self.gemini_api_key = GEMINI_API_KEY
        self._inicializar_cliente()

    def _inicializar_cliente(self):
        engines = ['groq', 'gemini', 'openrouter', 'ollama']
        if self.engine in engines:
            engines = [self.engine] + [e for e in engines if e != self.engine]

        for eng in engines:
            try:
                if eng == 'groq':
                    self._inicializar_groq()
                elif eng == 'gemini':
                    self._inicializar_gemini()
                elif eng == 'openrouter':
                    self._inicializar_openrouter()
                elif eng == 'ollama':
                    self._inicializar_ollama()
                self.engine = eng
                return
            except Exception as e:
                logger.warning(f"Motor {eng} no disponible: {e}")
                continue
        raise RuntimeError("Ningun motor LLM disponible")

    def _inicializar_groq(self):
        from groq import Groq
        if not GROQ_API_KEY or len(GROQ_API_KEY) < 10:
            raise ValueError("GROQ_API_KEY no configurada")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = FREE_MODELS['groq'][0]
        logger.info(f"Motor IA: Groq ({self.model}) - GRATUITO")

    def _inicializar_gemini(self):
        if not self.gemini_api_key or len(self.gemini_api_key) < 10:
            raise ValueError("GEMINI_API_KEY no configurada")
        self.model = FREE_MODELS['gemini'][0]
        logger.info(f"Motor IA: Gemini ({self.model}) - GRATUITO")

    def _inicializar_openrouter(self):
        from openai import OpenAI
        if not OPENROUTER_API_KEY or len(OPENROUTER_API_KEY) < 10:
            raise ValueError("OPENROUTER_API_KEY no configurada")
        self.client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        self.model = FREE_MODELS['openrouter'][0]
        logger.info(f"Motor IA: OpenRouter ({self.model}) - GRATUITO")

    def _inicializar_ollama(self):
        from openai import OpenAI
        self.client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        self.model = FREE_MODELS['ollama'][0]
        logger.info(f"Motor IA: Ollama ({self.model}) - LOCAL")

    def messages_create(self, messages: List[LLMMessage], **kwargs) -> str:
        engines = ['groq', 'gemini', 'openrouter', 'ollama']
        start_idx = engines.index(self.engine) if self.engine in engines else 0
        last_error = None

        for i in range(len(engines)):
            idx = (start_idx + i) % len(engines)
            eng = engines[idx]

            if eng != self.engine:
                try:
                    logger.warning(f"Rotando motor: {self.engine} -> {eng}")
                    self.cambiar_motor(eng)
                except Exception as e:
                    last_error = e
                    continue

            try:
                if eng == 'gemini':
                    return self._gemini_create(messages, **kwargs)
                return self._openai_compatible_create(messages, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Motor {eng} falló: {e}")
                continue

        raise last_error or RuntimeError("Ningun motor LLM disponible")

    def _gemini_create(self, messages: List[LLMMessage], **kwargs) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.gemini_api_key)

        system_text = ""
        gemini_history = []

        for msg in messages:
            if msg.role == 'system':
                system_text = msg.content
            elif msg.role == 'user':
                gemini_history.append({"role": "user", "text": msg.content})
            elif msg.role == 'assistant':
                gemini_history.append({"role": "model", "text": msg.content})

        last_user = gemini_history.pop() if gemini_history else {"role": "user", "text": ""}

        hist_contents = []
        i = 0
        while i < len(gemini_history) - 1:
            if gemini_history[i]['role'] == 'user' and gemini_history[i+1]['role'] == 'model':
                hist_contents.append(types.Content(
                    role="user", parts=[types.Part.from_text(gemini_history[i]['text'])]
                ))
                hist_contents.append(types.Content(
                    role="model", parts=[types.Part.from_text(gemini_history[i+1]['text'])]
                ))
                i += 2
            else:
                i += 1

        model_name = kwargs.get('model', self.model)
        config = types.GenerateContentConfig(
            system_instruction=system_text or None,
            max_output_tokens=kwargs.get('max_tokens', 4096),
            temperature=kwargs.get('temperature', 0.7),
        )

        chat = client.chats.create(model=model_name, history=hist_contents, config=config)
        response = chat.send_message(last_user['text'])
        return response.text

    def _openai_compatible_create(self, messages: List[LLMMessage], **kwargs) -> str:
        openai_messages = [{'role': m.role, 'content': m.content} for m in messages]
        model = kwargs.get('model', self.model or 'llama-3.3-70b-versatile')

        response = self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            max_tokens=kwargs.get('max_tokens', 4096),
            temperature=kwargs.get('temperature', 0.7),
        )
        return response.choices[0].message.content

    def messages_create_with_images(self, messages: List[LLMMessage], images: List[str] = None, **kwargs) -> str:
        """Envia mensajes con soporte de imagenes (usa Gemini si el motor no soporta vision)."""
        if images and self.engine != 'gemini':
            old_engine = self.engine
            try:
                self.engine = 'gemini'
                return self._gemini_create_with_images(messages, images, **kwargs)
            finally:
                self.engine = old_engine
        return self.messages_create(messages, **kwargs)

    def _gemini_create_with_images(self, messages: List[LLMMessage], image_paths: List[str], **kwargs) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.gemini_api_key)

        system_text = ""
        for msg in messages:
            if msg.role == 'system':
                system_text = msg.content

        parts = []
        for img_path in image_paths:
            import PIL.Image
            img = PIL.Image.open(img_path)
            parts.append(img)

        last_content = messages[-1].content if messages else ""
        parts.append(last_content)

        config = types.GenerateContentConfig(
            system_instruction=system_text or None,
            max_output_tokens=kwargs.get('max_tokens', 4096),
        )

        response = client.models.generate_content(
            model=kwargs.get('model', self.model),
            contents=parts,
            config=config,
        )
        return response.text

    def cambiar_motor(self, nuevo_motor: str):
        logger.info(f"Cambiando a motor: {nuevo_motor}")
        self.engine = nuevo_motor.lower()
        self._inicializar_cliente()


llm_wrapper = LLMWrapper()


def get_llm_client():
    return llm_wrapper.client


def get_llm_engine():
    return llm_wrapper.engine


def is_free_engine():
    return llm_wrapper.engine in ['groq', 'gemini', 'openrouter', 'ollama']

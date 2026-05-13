"""
Voice Processor — QuantumHive AGI
Procesamiento de voz usando Groq para Whisper (STT) y OpenAI para TTS.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Procesador de voz STT/TTS (Groq + OpenAI)."""

    def __init__(self):
        # Groq para Transcripción (Whisper)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY no configurada. Transcripción deshabilitada.")
        else:
            logger.info(f"GROQ_API_KEY cargada: {self.groq_api_key[:6]}...{self.groq_api_key[-4:]}")
        
        self.groq_client = OpenAI(
            api_key=self.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        ) if self.groq_api_key else None

        # OpenAI para TTS (Speech)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY no configurada. TTS deshabilitado.")
        else:
            logger.info(f"OPENAI_API_KEY cargada: {self.openai_api_key[:6]}...{self.openai_api_key[-4:]}")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        logger.info(f"VoiceProcessor inicializado — groq_client={'SI' if self.groq_client else 'NO'} | openai_client={'SI' if self.openai_client else 'NO'}")

    def transcribir_audio(self, ruta_audio: str, idioma: str = "es") -> Optional[str]:
        """Transcribe audio con Whisper-large-v3 de Groq."""
        if not self.groq_client:
            logger.error("Cliente Groq no inicializado para transcripción")
            return None
        
        try:
            file_size = os.path.getsize(ruta_audio)
            logger.info(f"DIAG: Llamando Groq Whisper con archivo: {ruta_audio} | tamaño: {file_size} bytes")
            
            with open(ruta_audio, "rb") as audio_file:
                resp = self.groq_client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    language=idioma,
                )
            
            logger.info(f"DIAG: Respuesta Groq Whisper raw: {resp}")
            texto = (resp.text or "").strip()
            logger.info(f"DIAG: Texto extraído: '{texto}' (longitud: {len(texto)})")
            if texto:
                return texto
            logger.warning("DIAG: Groq devolvió texto vacío")
            return None
        except Exception as e:
            logger.error(f"DIAG: Error en transcribir_audio (Groq): {e}", exc_info=True)
            return None

    def texto_a_voz(self, texto: str, ruta_salida: Optional[str] = None) -> Optional[str]:
        """Genera audio MP3 con TTS de OpenAI."""
        if not self.openai_client:
            logger.error("Cliente OpenAI no inicializado para TTS")
            return None
            
        try:
            if not ruta_salida:
                temp_dir = Path(tempfile.gettempdir())
                ruta_salida = str(temp_dir / "agi_tts_response.mp3")

            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=texto,
            )
            response.stream_to_file(ruta_salida)
            logger.info(f"Audio TTS generado: {ruta_salida}")
            return ruta_salida
        except Exception as e:
            logger.error(f"Error en texto_a_voz (OpenAI): {e}")
            return None

    def procesar_audio_completo(self, ruta_audio: str, respuesta_texto: str, idioma: str = "es") -> Tuple[Optional[str], Optional[str]]:
        """Transcribe entrada y genera audio de salida."""
        texto_transcrito = self.transcribir_audio(ruta_audio, idioma=idioma)
        audio_respuesta = self.texto_a_voz(respuesta_texto) if respuesta_texto else None
        return texto_transcrito, audio_respuesta


voice_processor = VoiceProcessor()


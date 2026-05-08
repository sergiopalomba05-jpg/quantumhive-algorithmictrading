"""
Voice Processor — QuantumHive AGI
Procesamiento de voz usando exclusivamente OpenAI API.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Procesador de voz STT/TTS con OpenAI API."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada para VoiceProcessor")
        self.client = OpenAI(api_key=api_key)
        logger.info("VoiceProcessor inicializado con OpenAI API")

    def transcribir_audio(self, ruta_audio: str, idioma: str = "es") -> Optional[str]:
        """Transcribe audio con Whisper-1 de OpenAI."""
        try:
            with open(ruta_audio, "rb") as audio_file:
                resp = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=idioma,
                )
            texto = (resp.text or "").strip()
            logger.info("Audio transcrito con OpenAI Whisper-1")
            return texto or None
        except Exception as e:
            logger.error(f"Error en transcribir_audio (OpenAI): {e}")
            return None

    def texto_a_voz(self, texto: str, ruta_salida: Optional[str] = None) -> Optional[str]:
        """Genera audio MP3 con TTS de OpenAI."""
        try:
            if not ruta_salida:
                temp_dir = Path(tempfile.gettempdir())
                ruta_salida = str(temp_dir / "agi_tts_response.mp3")

            response = self.client.audio.speech.create(
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


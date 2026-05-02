"""
Voice Processor — QuantumHive AGI
Procesamiento de voz bidireccional: STT (Speech-to-Text) y TTS (Text-to-Speech).
"""

import os
import logging
import tempfile
from typing import Optional
from gtts import gTTS
import whisper

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Procesador de voz para STT y TTS."""
    
    def __init__(self, modelo_whisper: str = "base"):
        """
        Inicializa el procesador de voz.
        
        Args:
            modelo_whisper: Modelo de Whisper a usar (tiny, base, small, medium, large)
        """
        self.modelo_whisper = modelo_whisper
        self.whisper_model = None
        self._cargar_whisper()
        logger.info(f"VoiceProcessor inicializado con modelo {modelo_whisper}")
    
    def _cargar_whisper(self):
        """Carga el modelo de Whisper."""
        try:
            self.whisper_model = whisper.load_model(self.modelo_whisper)
            logger.info(f"Modelo Whisper {self.modelo_whisper} cargado")
        except Exception as e:
            logger.error(f"Error cargando modelo Whisper: {e}")
            self.whisper_model = None
    
    def transcribir_audio(self, ruta_audio: str, idioma: str = "es") -> Optional[str]:
        """
        Transcribe audio a texto usando Whisper.
        
        Args:
            ruta_audio: Ruta al archivo de audio
            idioma: Idioma del audio (es, en, etc.)
        
        Returns:
            Texto transcrito o None si hay error
        """
        if not self.whisper_model:
            logger.error("Modelo Whisper no disponible")
            return None
        
        try:
            resultado = self.whisper_model.transcribe(ruta_audio, language=idioma)
            texto = resultado["text"]
            logger.info(f"Audio transcrito: {len(texto)} caracteres")
            return texto
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {e}")
            return None
    
    def texto_a_voz(self, texto: str, idioma: str = "es", ruta_salida: Optional[str] = None) -> Optional[str]:
        """
        Convierte texto a audio usando gTTS.
        
        Args:
            texto: Texto a convertir
            idioma: Idioma del texto (es, en, etc.)
            ruta_salida: Ruta donde guardar el audio (si es None, usa archivo temporal)
        
        Returns:
            Ruta del archivo de audio generado o None si hay error
        """
        try:
            if ruta_salida is None:
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    ruta_salida = f.name
            
            tts = gTTS(text=texto, lang=idioma, slow=False)
            tts.save(ruta_salida)
            
            logger.info(f"Audio generado: {ruta_salida}")
            return ruta_salida
        except Exception as e:
            logger.error(f"Error generando audio: {e}")
            return None
    
    def procesar_audio_completo(self, ruta_audio: str, respuesta_texto: str, idioma: str = "es") -> tuple[Optional[str], Optional[str]]:
        """
        Procesa audio completo: transcribe y genera respuesta en voz.
        
        Args:
            ruta_audio: Ruta al archivo de audio de entrada
            respuesta_texto: Texto de respuesta a convertir a voz
            idioma: Idioma del audio
        
        Returns:
            (texto_transcrito, ruta_audio_respuesta)
        """
        # Transcribir audio de entrada
        texto_transcrito = self.transcribir_audio(ruta_audio, idioma)
        
        # Generar audio de respuesta
        ruta_audio_respuesta = self.texto_a_voz(respuesta_texto, idioma) if respuesta_texto else None
        
        return texto_transcrito, ruta_audio_respuesta


# Instancia global del procesador de voz
voice_processor = VoiceProcessor()


if __name__ == "__main__":
    # Test del voice processor
    print("=== VOICE PROCESSOR - TEST ===\n")
    
    processor = VoiceProcessor()
    
    # Test TTS
    print("Generando audio de prueba...")
    audio_prueba = processor.texto_a_voz("Hola, esto es una prueba de voz.", "es")
    if audio_prueba:
        print(f"Audio generado: {audio_prueba}")

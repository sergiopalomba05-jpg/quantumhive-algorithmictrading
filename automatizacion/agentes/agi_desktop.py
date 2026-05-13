"""
AGI Desktop - Interfaz visual para AGI (Gradio).
Misma memoria persistente, mismos motores LLM, mismo contexto que AGI Telegram.
Comparte SQLite (agi_memoria_telegram.db) con AGI Telegram y AGI Local.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import gradio as gr

try:
    from agi_core.llm_wrapper import llm_wrapper, LLMMessage, get_llm_engine, is_free_engine
    LLM_AVAILABLE = True
except Exception as e:
    llm_wrapper = None
    LLM_AVAILABLE = False
    logger.error(f"LLM Wrapper no disponible: {e}")

from agi_core.supabase_client import supabase_memory
from dotenv import load_dotenv
load_dotenv()

import sqlite3
from datetime import datetime

DB_PATH = Path(__file__).parent / "agi_memoria_telegram.db"

SYSTEM_PROMPT = """Eres el CEO I de QuantumHive. Hablas como un ingeniero senior. Respuestas de maximo 5 lineas."""

def guardar_en_historial(rol: str, contenido: str):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            "INSERT INTO conversaciones (fecha, rol, contenido) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), rol, contenido)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error guardando historial: {e}")

def obtener_historial(limite: int = 10) -> List[dict]:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rol, contenido FROM conversaciones ORDER BY id DESC LIMIT ?",
            (limite,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    except Exception as e:
        logger.error(f"Error leyendo historial: {e}")
        return []

def responder(message: str, history: list, image_path: Optional[str] = None) -> str:
    if not LLM_AVAILABLE or not llm_wrapper:
        return "LLM Wrapper no disponible. Verifica instalacion."

    try:
        system_msg = LLMMessage(role="system", content=SYSTEM_PROMPT)

        historial = obtener_historial(limite=10)
        llm_messages = [system_msg]
        for msg in historial:
            llm_messages.append(LLMMessage(role=msg["role"], content=msg["content"]))
        llm_messages.append(LLMMessage(role="user", content=message))

        if image_path:
            logger.info(f"Procesando con imagen: {image_path}")
            respuesta = llm_wrapper.messages_create_with_images(
                llm_messages, images=[image_path]
            )
        else:
            respuesta = llm_wrapper.messages_create(llm_messages)

        guardar_en_historial("user", message)
        guardar_en_historial("assistant", respuesta)

        return respuesta
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {e}"

def chat_respond(message, history):
    if isinstance(message, dict):
        text = message.get("text", "")
        files = message.get("files", [])
        img = files[0] if files else None
    else:
        text = message
        img = None
    return responder(text, history, image_path=img)

with gr.Blocks(
    title="AGI Desktop - QuantumHive",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container { max-width: 800px; margin: auto; }
    footer { display: none !important; }
    """
) as demo:
    gr.Markdown(
        f"""# AGI Desktop — QuantumHive
Motor activo: **{get_llm_engine().upper() if LLM_AVAILABLE else 'NO DISPONIBLE'}**
Comparte memoria con AGI Telegram y AGI Local."""
    )

    gr.ChatInterface(
        fn=chat_respond,
        title="",
        multimodal=True,
        description="Chateá con AGI. Subí imágenes para que las analice con Gemini vision.",
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)

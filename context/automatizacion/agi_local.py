"""
AGI Local — QuantumHive
CLI para interactuar con AGI desde la PC.
Misma memoria que AGI Telegram (SQLite compartido).
Soporta archivos (@file), imagenes (@img), sin limite de caracteres.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agentes"))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "agentes" / "agi_memoria_telegram.db"

SYSTEM_PROMPT = "Eres AGI, la Inteligencia General Artificial de QuantumHive. Sos la mano derecha de Sergio. Hablas como socio estrategico senior. Conciso, directo."

try:
    from agi_core.llm_wrapper import llm_wrapper, LLMMessage
    LLM_OK = True
except ImportError as e:
    print(f"Error importando LLM Wrapper: {e}")
    LLM_OK = False


def obtener_historial(limite=10):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT rol, contenido FROM conversaciones ORDER BY fecha DESC LIMIT ?", (limite * 2,))
        msgs = list(reversed(c.fetchall()))
        conn.close()
        return [{"role": r, "content": t} for r, t in msgs]
    except Exception:
        return []


def guardar_historial(rol, contenido):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("INSERT INTO conversaciones (rol, contenido, tipo_mensaje) VALUES (?, ?, ?)",
                  (rol, contenido, "texto"))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Error guardando historial: {e}")


def leer_archivo(path):
    p = Path(path)
    if not p.exists():
        return f"ERROR: Archivo no encontrado: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return p.read_text(encoding="latin-1")
        except Exception:
            return f"ERROR: No se pudo leer el archivo: {path}"


def conversar(texto, archivos=None, imagenes=None):
    historial = obtener_historial(limite=10)
    messages = [LLMMessage(role="system", content=SYSTEM_PROMPT)]
    for msg in historial:
        messages.append(LLMMessage(role=msg["role"], content=msg["content"]))
    messages.append(LLMMessage(role="user", content=texto))

    try:
        if imagenes:
            respuesta = llm_wrapper.messages_create_with_images(messages, images=imagenes)
        else:
            respuesta = llm_wrapper.messages_create(messages)
    except Exception as e:
        respuesta = f"Error: {e}"

    guardar_historial("user", texto)
    guardar_historial("assistant", respuesta)
    return respuesta


def main():
    print(f"\n{'='*60}")
    print("  AGI Local — QuantumHive")
    print(f"  Motor: {llm_wrapper.engine} | DB: {DB_PATH.name}")
    print(f"  Comandos: @file <ruta> | @img <ruta> | salir")
    print(f"{'='*60}\n")

    while True:
        try:
            user_input = input("Tu > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChau.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            print("Chau.")
            break

        archivos = []
        imagenes = []

        if user_input.startswith("@file "):
            path = user_input[6:].strip()
            contenido = leer_archivo(path)
            user_input = f"[ARCHIVO: {path}]\n\n{contenido}"
            print(f"  (Archivo cargado: {path}, {len(contenido)} chars)")

        elif user_input.startswith("@img "):
            path = user_input[5:].strip()
            p = Path(path)
            if not p.exists():
                print(f"  ERROR: Archivo no encontrado: {path}")
                continue
            imagenes.append(str(p))
            user_input = f"[IMAGEN: {path}]\n\nDescribe esta imagen."
            print(f"  (Imagen cargada: {path})")

        print("  (Procesando...)")
        respuesta = conversar(user_input, archivos=archivos, imagenes=imagenes)
        print(f"\nAGI > {respuesta}\n")


if __name__ == "__main__":
    if not LLM_OK:
        sys.exit(1)
    main()

"""
AGI Desktop — Interfaz visual para AGI (Gradio).
MISMA inteligencia, memoria, contexto y persistencia que AGI Telegram.
Comparte SQLite, Event Bus, GitHub Memory, Agente Cerebro y todos los módulos v2.0.
"""
import os, sys, json, logging, sqlite3, base64, tempfile
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import gradio as gr
import requests

load_dotenv()
ROOT_DIR = Path(__file__).resolve().parents[2]
QUANTUM_ESTADO_PATH = ROOT_DIR / "QUANTUM_ESTADO.md"
DB_PATH = Path(__file__).parent / "agi_memoria_telegram.db"

SYSTEM_PROMPT = """Eres el CEO I de QuantumHive. Hablas como un ingeniero senior. Respuestas directas y naturales, sin prefijos ni etiquetas. Cuando el usuario te envie una IMAGEN, vos podes verla y analizarla."""

# ─── LLM Wrapper ───
try:
    from agi_core.llm_wrapper import llm_wrapper, LLMMessage, get_llm_engine, is_free_engine
    LLM_WRAPPER_AVAILABLE = True
except Exception as e:
    llm_wrapper = None; LLM_WRAPPER_AVAILABLE = False
    logger.warning(f"LLM Wrapper no disponible: {e}")

# ─── Voice Processor ───
try:
    from agi_core.voice_processor import voice_processor
    VOICE_PROCESSOR_AVAILABLE = True
except Exception as e:
    voice_processor = None; VOICE_PROCESSOR_AVAILABLE = False

# ─── AGI v2 Modules ───
try:
    from agi_memory.intent_classifier import IntentClassifier as NewIntentClassifier
    from agi_memory.challenge_mode import ChallengeMode
    from agi_memory.memory_manager import MemoryManager
    from agi_core.approval_gate import ApprovalGate
    from agi_core.action_router import ActionRouter
    from agi_core.agent_bus import AgentBus
    from agi_autonomous.heartbeat_monitor import HeartbeatMonitor
    from agi_autonomous.briefing_generator import BriefingGenerator
    from agi_autonomous.proactive_alerts import ProactiveAlerts
    from agi_autonomous.action_executor import ActionExecutor
    from agi_autonomous.trigger_system import TriggerSystem
    from agi_autonomous.agi_autonomous import AGIAutonomous
    AGI_V2_AVAILABLE = True
except Exception as e:
    logger.warning(f"AGI v2 no disponible: {e}")
    NewIntentClassifier = ChallengeMode = MemoryManager = None
    ApprovalGate = ActionRouter = AgentBus = None
    HeartbeatMonitor = BriefingGenerator = ProactiveAlerts = None
    ActionExecutor = TriggerSystem = AGIAutonomous = None
    AGI_V2_AVAILABLE = False

# ─── Supabase ───
try:
    from agi_core.supabase_client import supabase_memory
except Exception as e:
    supabase_memory = None
    logger.warning(f"Supabase no disponible: {e}")

# ─── GitHub Memory ───
try:
    from agi_memory.github_memory import github_memory
except Exception as e:
    github_memory = None

# ─── Event Bus ───
try:
    from event_bus import event_bus
    from handlers_colmena import registrar_suscriptores, Eventos
    registrar_suscriptores(event_bus)
    event_bus.iniciar()
    EVENT_BUS_AVAILABLE = True
except Exception as e:
    event_bus = None; EVENT_BUS_AVAILABLE = False
    logger.warning(f"Event Bus no disponible: {e}")

# ─── Agente Cerebro ───
try:
    from agente_cerebro import agente_cerebro
    CEREBRO_DISPONIBLE = True
except Exception as e:
    agente_cerebro = None; CEREBRO_DISPONIBLE = False

# ─── Scheduler ───
try:
    from scheduler import scheduler_qh
    scheduler_qh.iniciar()
    SCHEDULER_AVAILABLE = True
except Exception as e:
    scheduler_qh = None; SCHEDULER_AVAILABLE = False

if LLM_WRAPPER_AVAILABLE and llm_wrapper:
    llm_client = llm_wrapper
    try:
        llm_client.cambiar_motor("groq")
    except:
        pass

# ─── Inicializar módulos v2 ───
new_intent_classifier = NewIntentClassifier() if NewIntentClassifier else None
challenge_mode = ChallengeMode() if ChallengeMode else None
memory_manager = MemoryManager() if MemoryManager else None
approval_gate = ApprovalGate() if ApprovalGate else None
action_router = ActionRouter() if ActionRouter else None
agent_bus = AgentBus() if AgentBus else None
heartbeat_monitor = HeartbeatMonitor() if HeartbeatMonitor else None
briefing_generator = BriefingGenerator() if BriefingGenerator else None
proactive_alerts = ProactiveAlerts() if ProactiveAlerts else None
action_executor = ActionExecutor() if ActionExecutor else None
trigger_system = TriggerSystem() if TriggerSystem else None
agi_autonomous = AGIAutonomous() if AGIAutonomous else None

# ─── Memoria SQLite ───
@dataclass
class MensajeMemoria:
    id: Optional[int] = None
    timestamp: str = ""
    tipo: str = ""
    contenido: str = ""
    respuesta: str = ""
    guardado_en_vision: bool = False
    score_viabilidad: Optional[float] = None

class MemoriaSQLite:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._inicializar_db()
    def _inicializar_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS conversaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, rol TEXT, contenido TEXT, tipo_mensaje TEXT DEFAULT 'texto')")
        conn.commit(); conn.close()

memoria = MemoriaSQLite()
conn = sqlite3.connect(memoria.db_path)
conn.execute("DELETE FROM conversaciones WHERE contenido LIKE '%No pude transcribir el audio%' OR contenido LIKE '%Error procesando audio%'")
conn.commit(); conn.close()

# ─── Clasificador de intención legacy ───
clasificador_intencion = None
if NewIntentClassifier:
    new_intent_classifier = NewIntentClassifier()
else:
    new_intent_classifier = None

# ─── Funciones de contexto (idénticas a AGI Telegram) ───

def obtener_historial_conversacion(db_path: str, limite: int = 10) -> list:
    try:
        if supabase_memory:
            historial = supabase_memory.obtener_historial(limite=limite)
            if historial:
                return historial
    except Exception as e:
        logger.warning(f"Supabase falló, fallback SQLite: {e}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT rol, contenido FROM conversaciones ORDER BY fecha DESC LIMIT ?", (limite * 2,))
    mensajes = cursor.fetchall()
    conn.close()
    mensajes = list(reversed(mensajes))
    return [{"role": r[0], "content": r[1]} for r in mensajes]

def guardar_en_historial(db_path: str, rol: str, contenido: str, tipo: str = "texto"):
    try:
        if supabase_memory:
            registro_id = supabase_memory.guardar_conversacion(rol, contenido, tipo)
            if registro_id != -1:
                return
    except Exception as e:
        logger.warning(f"Supabase falló, fallback SQLite: {e}")
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO conversaciones (rol, contenido, tipo_mensaje) VALUES (?, ?, ?)", (rol, contenido, tipo))
    conn.commit(); conn.close()

def limpiar_historial_antiguo(db_path: str, mantener: int = 100):
    try:
        if supabase_memory:
            supabase_memory.limpiar_historial_antiguo(mantener=mantener)
            return
    except: pass
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM conversaciones WHERE id NOT IN (SELECT id FROM conversaciones ORDER BY fecha DESC LIMIT ?)", (mantener,))
    conn.commit(); conn.close()

def construir_contexto_dinamico(db_conn, tipo_mensaje: str) -> str:
    contexto = []
    if tipo_mensaje == "estado":
        cursor = db_conn.cursor()
        cursor.execute("SELECT nombre, valor, unidad FROM metricas ORDER BY fecha DESC LIMIT 10")
        metricas = cursor.fetchall()
        cursor.execute("SELECT descripcion, severidad FROM alertas WHERE estado='activa' LIMIT 5")
        alertas = cursor.fetchall()
        cursor.execute("SELECT nombre FROM agentes WHERE estado='cuarentena'")
        cuarentena = cursor.fetchall()
        if metricas: contexto.append(f"METRICAS ACTUALES: {metricas}")
        if alertas: contexto.append(f"ALERTAS ACTIVAS: {alertas}")
        if cuarentena: contexto.append(f"AGENTES EN CUARENTENA: {cuarentena}")
    elif tipo_mensaje == "idea":
        cursor = db_conn.cursor()
        cursor.execute("SELECT titulo, score, estado FROM ideas WHERE estado != 'completada' ORDER BY fecha DESC LIMIT 5")
        ideas = cursor.fetchall()
        if ideas: contexto.append(f"IDEAS EN CURSO: {ideas}")
    elif tipo_mensaje == "trading":
        cursor = db_conn.cursor()
        cursor.execute("SELECT nombre, valor, unidad FROM metricas WHERE categoria='trading' ORDER BY fecha DESC LIMIT 5")
        trading = cursor.fetchall()
        if trading: contexto.append(f"ESTADO TRADING: {trading}")
    return "\n".join(contexto) if contexto else ""

def _leer_quantum_estado() -> str:
    try:
        if QUANTUM_ESTADO_PATH.exists():
            return QUANTUM_ESTADO_PATH.read_text(encoding="utf-8").strip()
        return "No tengo conexion al sensor QUANTUM_ESTADO.md"
    except: return "No tengo conexion al sensor QUANTUM_ESTADO.md"

def _leer_ultimos_errores_procesos(db_path: str, limite: int = 5) -> str:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM errores_procesos ORDER BY id DESC LIMIT {limite}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        if not rows: return "No hay registros en errores_procesos"
        return json.dumps([dict(zip(columns, row)) for row in rows], ensure_ascii=False, indent=2)
    except Exception as e:
        return "No tengo conexion al sensor errores_procesos"

def _construir_contexto_realidad(texto: str, tipo_mensaje: str) -> str:
    estado = _leer_quantum_estado()
    errores = _leer_ultimos_errores_procesos(memoria.db_path, limite=5)
    return f"\n\n---\n## BUS DE REALIDAD\n### QUANTUM_ESTADO\n{estado}\n\n### ERRORES_PROCESOS (ultimos 5)\n{errores}"

def construir_mensaje_sistema(db_conn, tipo_mensaje: str) -> str:
    partes = [SYSTEM_PROMPT]
    if github_memory:
        try:
            ctx = github_memory.obtener_contexto_para_claude()
            if ctx: partes.append(f"\n\n---\n## MEMORIA PERSISTENTE (GitHub)\n{ctx}")
        except Exception as e: logger.error(f"GitHub Memory: {e}")
    if memory_manager:
        try:
            ctx = memory_manager.obtener_contexto_para_claude()
            if ctx: partes.append(f"\n\n---\n## MEMORIA PERSISTENTE (AGI UPGRADE)\n{ctx}")
        except Exception as e: logger.error(f"MemoryManager: {e}")
    ctx_dinamico = construir_contexto_dinamico(db_conn, tipo_mensaje)
    if ctx_dinamico: partes.append(f"\n\n---\n## ESTADO ACTUAL DEL SISTEMA\n{ctx_dinamico}")
    if CEREBRO_DISPONIBLE and agente_cerebro:
        try:
            briefing = agente_cerebro.generar_briefing_para_agi()
            if tipo_mensaje in ["general", "estado"]: agente_cerebro.marcar_leidos()
            partes.append(f"\n\n---\n## NOVEDADES DE LA COLMENA (TIEMPO REAL)\n{briefing}")
        except Exception as e: logger.error(f"Agente Cerebro: {e}")
    return "\n".join(partes)

# ─── Procesar mensaje con AGI ───

def procesar_mensaje_con_llm(message_text, image_paths: List[str] = None) -> str:
    if not llm_client:
        return "LLM Wrapper no disponible."
    try:
        if github_memory:
            github_memory.actualizar_perfil_sergio(message_text, "general")

        conn = sqlite3.connect(memoria.db_path)
        system_prompt = construir_mensaje_sistema(conn, "general")
        conn.close()
        system_prompt += _construir_contexto_realidad(message_text, "general")

        historial = obtener_historial_conversacion(memoria.db_path, limite=10)
        messages = historial.copy()
        messages.append({"role": "user", "content": message_text})

        llm_messages = [LLMMessage(role="system", content=system_prompt)]
        for msg in messages:
            llm_messages.append(LLMMessage(role=msg["role"], content=msg["content"]))

        if image_paths:
            respuesta = llm_client.messages_create_with_images(llm_messages, images=image_paths)
        else:
            respuesta = llm_client.messages_create(llm_messages)

        guardar_en_historial(memoria.db_path, "user", message_text)
        guardar_en_historial(memoria.db_path, "assistant", respuesta)
        limpiar_historial_antiguo(memoria.db_path, mantener=100)
        return respuesta
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error procesando mensaje: {e}"

def leer_archivo(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists(): return f"Archivo no encontrado: {path}"
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error leyendo archivo: {e}"

def procesar_mensaje(text, image_paths: List[str] = None) -> str:
    if not text.strip() and not image_paths:
        return "Escribi un mensaje o adjunta una imagen."

    text_limpio = text.strip()

    if text_limpio.startswith("@file "):
        path = text_limpio.replace("@file ", "", 1).strip()
        contenido = leer_archivo(path)
        return procesar_mensaje_con_llm(f"Archivo {path}:\n\n{contenido}")

    if text_limpio.startswith("@img ") and not image_paths:
        path = text_limpio.replace("@img ", "", 1).strip()
        if Path(path).exists():
            image_paths = [path]
            text_limpio = "Analiza esta imagen."
        else:
            return f"Archivo de imagen no encontrado: {path}"

    return procesar_mensaje_con_llm(text_limpio, image_paths=image_paths)

def chat_respond(message, history):
    if isinstance(message, dict):
        text = message.get("text", "")
        files = message.get("files", [])
        img = files[0] if files else None
    else:
        text = message
        img = None
    return procesar_mensaje(text, image_paths=[img] if img else None)

# ─── Interfaz Gradio ───
with gr.Blocks(title="AGI Desktop - QuantumHive", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"""# AGI Desktop — QuantumHive
**Motor:** {get_llm_engine().upper() if LLM_WRAPPER_AVAILABLE else 'NO DISPONIBLE'}
Memoria persistente | Event Bus | GitHub Memory | Agente Cerebro
Comandos: `@file <ruta>` · `@img <ruta>`
> Comparte datos con AGI Telegram, AGI Local y Cascade (Arquitecto)
""")

    chatbot = gr.ChatInterface(
        fn=chat_respond,
        multimodal=True,
        title="",
        description="Chatea con AGI. Subi imagenes para que las analice con Gemini vision.",
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)

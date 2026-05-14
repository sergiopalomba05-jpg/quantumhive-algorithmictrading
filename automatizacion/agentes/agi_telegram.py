"""
AGI Telegram Bot con LLM Wrapper (Groq principal + OpenRouter backup).
Integración de AGI con Telegram API para inteligencia operativa.
"""
import os
import sys
import json
import logging
import sqlite3
import base64
import tempfile
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import requests

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AGI UPGRADE v2.0 Modules - Agregar paths antes de imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # automatizacion/ — para agi_core, agi_autonomous
sys.path.insert(0, str(Path(__file__).parent))          # automatizacion/agentes/ — para agi_memory

# LLM Wrapper para alternativas gratuitas
try:
    from agi_core.llm_wrapper import llm_wrapper, LLMMessage, get_llm_engine, is_free_engine
    LLM_WRAPPER_AVAILABLE = True
    logger.info("LLM Wrapper disponible - alternativas gratuitas soportadas")
except ImportError as e:
    llm_wrapper = None
    LLM_WRAPPER_AVAILABLE = False
    logger.warning(f"LLM Wrapper no disponible: {e}")

# Voice Processor para procesamiento de voz bidireccional
try:
    from agi_core.voice_processor import voice_processor
    VOICE_PROCESSOR_AVAILABLE = True
    logger.info("Voice Processor disponible - procesamiento de voz bidireccional soportado")
except ImportError as e:
    voice_processor = None
    VOICE_PROCESSOR_AVAILABLE = False
    logger.warning(f"Voice Processor no disponible: {e}")

# AGI UPGRADE v2.0 Modules
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
except ImportError as e:
    logger.warning(f"AGI UPGRADE v2.0 modules no disponibles: {e}. Usando fallback legacy.")
    AGI_V2_AVAILABLE = False
from agi_core.supabase_client import supabase_memory

# GitHub Memory Manager — memoria persistente entre sesiones
try:
    from agi_memory.github_memory import github_memory
    GITHUB_MEMORY_AVAILABLE = True
    logger.info("GitHub Memory disponible")
except Exception as e:
    github_memory = None
    GITHUB_MEMORY_AVAILABLE = False
    logger.warning(f"GitHub Memory no disponible: {e}")

# Event Bus
try:
    from event_bus import event_bus
    from handlers_colmena import registrar_suscriptores, Eventos
    registrar_suscriptores(event_bus)
    event_bus.iniciar()
    EVENT_BUS_AVAILABLE = True
    logger.info("Event Bus iniciado y handlers registrados")
except Exception as e:
    event_bus = None
    EVENT_BUS_AVAILABLE = False
    logger.warning(f"Event Bus no disponible: {e}")

# Agente Cerebro — Contexto en tiempo real
try:
    from agente_cerebro import agente_cerebro
    CEREBRO_DISPONIBLE = True
    logger.info("Agente Cerebro disponible — contexto en tiempo real activado")
except ImportError:
    agente_cerebro = None
    CEREBRO_DISPONIBLE = False
    logger.warning("agente_cerebro no disponible — AGI sin contexto en tiempo real")

# Scheduler
try:
    from scheduler import scheduler_qh
    scheduler_qh.iniciar()
    SCHEDULER_AVAILABLE = True
    logger.info("Scheduler iniciado correctamente")
except Exception as e:
    scheduler_qh = None
    SCHEDULER_AVAILABLE = False
    logger.warning(f"Scheduler no disponible: {e}")

app = Flask(__name__)

# Cargar variables de entorno
load_dotenv()

# Variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL', '').strip()
USER_TELEGRAM_ID = os.getenv('USER_TELEGRAM_ID', '').strip()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENROUTER_FALLBACK_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

# Debug: verificar configuración del fallback OpenRouter
logger.info(f"OpenRouter fallback model configurado: {OPENROUTER_FALLBACK_MODEL}")


# Funciones Multimodales

def transcribir_audio(file_path: str) -> str:
    """
    Transcribe audio usando VoiceProcessor (Groq Whisper-large-v3).
    """
    try:
        if VOICE_PROCESSOR_AVAILABLE and voice_processor:
            texto = voice_processor.transcribir_audio(file_path, idioma="es")
            return texto or ""
        return ""
    except Exception as e:
        logger.error(f"Error transcribiendo audio: {e}")
        return ""


def procesar_imagen(file_path: str, caption: str = "") -> List[Dict]:
    """
    Procesa imagen como contenido multimodal para el motor LLM activo.
    """
    try:
        with open(file_path, "rb") as img:
            img_b64 = base64.b64encode(img.read()).decode()
        
        return [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_b64
                }
            },
            {
                "type": "text",
                "text": caption if caption else "Sergio te envió esta imagen. Analizala en el contexto de QuantumHive."
            }
        ]
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return [{"type": "text", "text": caption if caption else ""}]


def procesar_video(file_path: str) -> str:
    """
    Procesa video extrayendo frames clave.
    """
    try:
        # Por ahora, solo extraer información básica del archivo
        # En futura implementación, usar FFmpeg para extraer frames
        return f"Video recibido: {Path(file_path).name}"
    except Exception as e:
        logger.error(f"Error procesando video: {e}")
        return ""


def generar_audio(texto: str) -> str:
    """
    Genera audio usando VoiceProcessor (OpenAI TTS).
    Retorna el path del archivo de audio generado.
    """
    try:
        if VOICE_PROCESSOR_AVAILABLE and voice_processor:
            audio_path = voice_processor.texto_a_voz(texto)
            if audio_path:
                logger.info(f"Audio generado: {audio_path}")
                return audio_path
        return ""
    except Exception as e:
        logger.error(f"Error generando audio: {e}")
        return ""

# Identidad operativa CEO I
ROOT_DIR = Path(__file__).resolve().parents[2]
QUANTUM_ESTADO_PATH = ROOT_DIR / "QUANTUM_ESTADO.md"
SYSTEM_PROMPT = """Eres el CEO I de QuantumHive. Hablas como un ingeniero senior. Respuestas directas y naturales, sin prefijos ni etiquetas. Cuando el usuario te envie una IMAGEN, vos podes verla y analizarla."""


@dataclass
class MensajeMemoria:
    """Mensaje almacenado en memoria SQLite."""
    id: Optional[int] = None
    timestamp: str = ""
    tipo: str = ""
    contenido: str = ""
    respuesta: str = ""
    guardado_en_vision: bool = False
    score_viabilidad: Optional[float] = None


class MemoriaSQLite:
    """Memoria persistente SQLite para AGI con esquema completo."""
    
    def __init__(self, db_path: str = "agi_memoria_telegram.db"):
        self.db_path = db_path
        self._inicializar_db()
    
    def _inicializar_db(self):
        """Inicializa base de datos SQLite con esquema completo."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. IDEAS DE SERGIO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                categoria TEXT,
                score INTEGER,
                estado TEXT DEFAULT 'registrada',
                brief_generado TEXT,
                notas TEXT
            )
        """)
        
        # 2. DECISIONES TOMADAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                descripcion TEXT NOT NULL,
                tipo TEXT,
                impacto TEXT,
                ejecutada_por TEXT,
                resultado TEXT
            )
        """)
        
        # 3. ESTADO DE AGENTES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                division TEXT,
                score_reputacion INTEGER DEFAULT 75,
                modelo_asignado TEXT,
                estado TEXT DEFAULT 'operativo',
                ultima_tarea TEXT,
                ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. MÉTRICAS DE LA EMPRESA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                categoria TEXT,
                nombre TEXT NOT NULL,
                valor REAL,
                unidad TEXT,
                fuente TEXT
            )
        """)
        
        # 5. ALERTAS Y RIESGOS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT,
                severidad TEXT,
                descripcion TEXT NOT NULL,
                estado TEXT DEFAULT 'activa',
                resuelta_en TIMESTAMP
            )
        """)
        
        # 6. COMUNICACIONES CON LA COLMENA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comunicaciones_colmena (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT,
                destino TEXT,
                mensaje TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente_aprobacion',
                aprobado_en TIMESTAMP
            )
        """)
        
        # 7. HISTORIAL DE CONVERSACIÓN
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rol TEXT,
                contenido TEXT NOT NULL,
                tipo_mensaje TEXT
            )
        """)
        
        # 8. MENSAJES (mantener compatibilidad con código existente)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tipo TEXT NOT NULL,
                contenido TEXT NOT NULL,
                respuesta TEXT,
                guardado_en_vision BOOLEAN DEFAULT FALSE,
                score_viabilidad REAL
            )
        """)

        # 9. EVENTOS (Event Bus - Sistema Autónomo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,
                origen TEXT NOT NULL,
                payload TEXT,
                estado TEXT DEFAULT 'pendiente',
                procesado_en TIMESTAMP,
                procesado_por TEXT,
                intentos INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Base de datos SQLite inicializada con esquema completo")
    
    def guardar_mensaje(self, mensaje: MensajeMemoria) -> int:
        """Guarda mensaje en base de datos (compatibilidad)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO mensajes (timestamp, tipo, contenido, respuesta, guardado_en_vision, score_viabilidad)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            mensaje.timestamp,
            mensaje.tipo,
            mensaje.contenido,
            mensaje.respuesta,
            mensaje.guardado_en_vision,
            mensaje.score_viabilidad
        ))
        
        mensaje_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Mensaje guardado con ID {mensaje_id}")
        return mensaje_id
    
    def guardar_idea(self, titulo: str, descripcion: str, categoria: str, score: int, notas: str = "") -> int:
        """Guarda idea de Sergio en base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ideas (titulo, descripcion, categoria, score, notas)
            VALUES (?, ?, ?, ?, ?)
        """, (titulo, descripcion, categoria, score, notas))
        
        idea_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Idea guardada con ID {idea_id}")
        return idea_id
    
    def guardar_decision(self, descripcion: str, tipo: str, impacto: str, ejecutada_por: str, resultado: str = "") -> int:
        """Guarda decisión tomada en base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decisiones (descripcion, tipo, impacto, ejecutada_por, resultado)
            VALUES (?, ?, ?, ?, ?)
        """, (descripcion, tipo, impacto, ejecutada_por, resultado))
        
        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Decisión guardada con ID {decision_id}")
        return decision_id
    
    def guardar_metrica(self, categoria: str, nombre: str, valor: float, unidad: str, fuente: str) -> int:
        """Guarda métrica de la empresa en base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO metricas (categoria, nombre, valor, unidad, fuente)
            VALUES (?, ?, ?, ?, ?)
        """, (categoria, nombre, valor, unidad, fuente))
        
        metrica_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Métrica guardada con ID {metrica_id}")
        return metrica_id
    
    def guardar_alerta(self, tipo: str, severidad: str, descripcion: str) -> int:
        """Guarda alerta en base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alertas (tipo, severidad, descripcion)
            VALUES (?, ?, ?)
        """, (tipo, severidad, descripcion))
        
        alerta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Alerta guardada con ID {alerta_id}")
        return alerta_id
    
    def obtener_mensajes(self, limite: int = 10) -> List[Dict]:
        """Obtiene últimos mensajes (compatibilidad)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, tipo, contenido, respuesta, guardado_en_vision, score_viabilidad
            FROM mensajes
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limite,))
        
        mensajes = []
        for row in cursor.fetchall():
            mensajes.append({
                "id": row[0],
                "timestamp": row[1],
                "tipo": row[2],
                "contenido": row[3],
                "respuesta": row[4],
                "guardado_en_vision": row[5],
                "score_viabilidad": row[6]
            })
        
        conn.close()
        return mensajes
    
    def obtener_metricas(self, categoria: str = None, limite: int = 10) -> List[Dict]:
        """Obtiene últimas métricas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if categoria:
            cursor.execute("""
                SELECT id, fecha, categoria, nombre, valor, unidad, fuente
                FROM metricas
                WHERE categoria = ?
                ORDER BY fecha DESC
                LIMIT ?
            """, (categoria, limite))
        else:
            cursor.execute("""
                SELECT id, fecha, categoria, nombre, valor, unidad, fuente
                FROM metricas
                ORDER BY fecha DESC
                LIMIT ?
            """, (limite,))
        
        metricas = []
        for row in cursor.fetchall():
            metricas.append({
                "id": row[0],
                "fecha": row[1],
                "categoria": row[2],
                "nombre": row[3],
                "valor": row[4],
                "unidad": row[5],
                "fuente": row[6]
            })
        
        conn.close()
        return metricas
    
    def obtener_alertas_activas(self, limite: int = 10) -> List[Dict]:
        """Obtiene alertas activas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, fecha, tipo, severidad, descripcion, estado
            FROM alertas
            WHERE estado = 'activa'
            ORDER BY fecha DESC
            LIMIT ?
        """, (limite,))
        
        alertas = []
        for row in cursor.fetchall():
            alertas.append({
                "id": row[0],
                "fecha": row[1],
                "tipo": row[2],
                "severidad": row[3],
                "descripcion": row[4],
                "estado": row[5]
            })
        
        conn.close()
        return alertas
    
    def obtener_agentes_cuarentena(self) -> List[Dict]:
        """Obtiene agentes en cuarentena."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, division, estado, score_reputacion
            FROM agentes
            WHERE estado = 'cuarentena'
        """)
        
        agentes = []
        for row in cursor.fetchall():
            agentes.append({
                "id": row[0],
                "nombre": row[1],
                "division": row[2],
                "estado": row[3],
                "score_reputacion": row[4]
            })
        
        conn.close()
        return agentes
    
    def registrar_idea_vision_ceo(self, titulo: str, descripcion: str, score: int, 
                                   categoria: str, analisis: str, proximo_paso: str) -> int:
        """
        Registra idea estructurada en vision_ceo.md y en SQLite simultáneamente.
        """
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entrada = f"""
## {fecha} — {titulo}
**Score:** {score}/100
**Categoría:** {categoria}
**Estado:** registrada

**Descripción:**
{descripcion}

**Análisis AGI:**
{analisis}

**Próximo paso:**
{proximo_paso}

**Brief para Colmena:** pendiente

---
"""
        # Guardar en vision_ceo.md
        vision_ceo_path = "vision_ceo.md"
        with open(vision_ceo_path, "a", encoding="utf-8") as f:
            f.write(entrada)
        
        logger.info(f"Idea registrada en vision_ceo.md: {titulo}")
        
        # Guardar en SQLite también
        return self.guardar_idea(titulo, descripcion, categoria, score, analisis)


def obtener_historial_conversacion(db_path: str, limite: int = 10) -> list:
    """
    Obtiene los últimos N intercambios de la conversación actual.
    Retorna lista de mensajes en formato LLM compatible.
    Usa Supabase para persistencia en la nube.
    """
    try:
        # Intentar usar Supabase primero
        historial = supabase_memory.obtener_historial(limite=limite)
        if historial:
            return historial
    except Exception as e:
        logger.warning(f"Error obteniendo historial de Supabase, fallback a SQLite: {e}")
    
    # Fallback a SQLite local
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT rol, contenido 
        FROM conversaciones 
        ORDER BY fecha DESC 
        LIMIT ?
    """, (limite * 2,))
    
    mensajes = cursor.fetchall()
    conn.close()
    
    # Invertir para orden cronológico correcto
    mensajes = list(reversed(mensajes))
    
    historial = []
    for rol, contenido in mensajes:
        historial.append({
            "role": rol,
            "content": contenido
        })
    
    return historial


def guardar_en_historial(db_path: str, rol: str, contenido: str, tipo: str = "texto"):
    """
    Guarda un mensaje en la tabla conversaciones.
    rol: "user" | "assistant"
    Usa Supabase para persistencia en la nube.
    """
    try:
        # Intentar usar Supabase primero
        registro_id = supabase_memory.guardar_conversacion(rol, contenido, tipo)
        if registro_id != -1:
            return
    except Exception as e:
        logger.warning(f"Error guardando en Supabase, fallback a SQLite: {e}")
    
    # Fallback a SQLite local
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversaciones (rol, contenido, tipo_mensaje)
        VALUES (?, ?, ?)
    """, (rol, contenido, tipo))
    
    conn.commit()
    conn.close()


def limpiar_historial_antiguo(db_path: str, mantener: int = 100):
    """
    Mantiene solo los últimos N mensajes en conversaciones.
    Evita que la tabla crezca infinitamente.
    Usa Supabase para persistencia en la nube.
    """
    try:
        # Intentar usar Supabase primero
        supabase_memory.limpiar_historial_antiguo(mantener=mantener)
        return
    except Exception as e:
        logger.warning(f"Error limpiando historial en Supabase, fallback a SQLite: {e}")
    
    # Fallback a SQLite local
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM conversaciones 
        WHERE id NOT IN (
            SELECT id FROM conversaciones 
            ORDER BY fecha DESC 
            LIMIT ?
        )
    """, (mantener,))
    
    eliminados = cursor.rowcount
    conn.commit()
    conn.close()
    
    if eliminados > 0:
        logger.info(f"Historial limpiado: {eliminados} mensajes antiguos eliminados")


class ClasificadorIntencion:
    """Clasifica mensajes de Sergio según intención para routing inteligente."""
    
    def __init__(self):
        self.patrones = self._cargar_patrones()
        logger.info("Clasificador de intención inicializado")
    
    def _cargar_patrones(self) -> Dict[str, List[str]]:
        """Carga patrones de clasificación de intención."""
        return {
            "idea": ["idea", "qué te parece", "pensé en", "y si", "podríamos", "quiero crear", "propuesta"],
            "estado": ["estado", "cómo vamos", "reporte", "métricas", "resumen", "dashboard", "qué pasó"],
            "orden_arquitecto": ["cascade", "arquitecto", "implementá", "creá", "modificá", "arreglá", "deployá"],
            "orden_colmena": ["colmena", "avisá", "mandá a todos", "comunicá", "informá"],
            "alerta": ["urgente", "problema", "error", "cayó", "fallo", "riesgo", "drawdown"],
            "trading": ["trade", "operación", "us30", "posición", "entrada", "salida", "señal"],
            "consulta": ["qué es", "cómo", "explicame", "cuándo", "por qué", "diferencia"],
        }
    
    def clasificar_mensaje(self, texto: str) -> Dict:
        """
        Clasifica el mensaje de Sergio antes de enviarlo al motor LLM.
        Retorna: { tipo, contexto_adicional }
        """
        texto_lower = texto.lower().strip()
        
        for tipo, keywords in self.patrones.items():
            if any(kw in texto_lower for kw in keywords):
                return {"tipo": tipo}
        
        return {"tipo": "general"}


def construir_contexto_dinamico(db_conn, tipo_mensaje: str) -> str:
    """
    Inyecta contexto relevante según el tipo de mensaje detectado.
    """
    contexto = []
    
    if tipo_mensaje == "estado":
        # Traer últimas métricas
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT nombre, valor, unidad FROM metricas ORDER BY fecha DESC LIMIT 10"
        )
        metricas = cursor.fetchall()
        
        cursor.execute(
            "SELECT descripcion, severidad FROM alertas WHERE estado='activa' LIMIT 5"
        )
        alertas = cursor.fetchall()
        
        cursor.execute(
            "SELECT nombre FROM agentes WHERE estado='cuarentena'"
        )
        agentes_cuarentena = cursor.fetchall()
        
        if metricas:
            contexto.append(f"MÉTRICAS ACTUALES: {metricas}")
        if alertas:
            contexto.append(f"ALERTAS ACTIVAS: {alertas}")
        if agentes_cuarentena:
            contexto.append(f"AGENTES EN CUARENTENA: {agentes_cuarentena}")
    
    elif tipo_mensaje == "idea":
        # Traer ideas pendientes para contexto
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT titulo, score, estado FROM ideas WHERE estado != 'completada' ORDER BY fecha DESC LIMIT 5"
        )
        ideas = cursor.fetchall()
        if ideas:
            contexto.append(f"IDEAS EN CURSO: {ideas}")
    
    elif tipo_mensaje == "trading":
        # Traer métricas de trading
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT nombre, valor, unidad FROM metricas WHERE categoria='trading' ORDER BY fecha DESC LIMIT 5"
        )
        trading = cursor.fetchall()
        if trading:
            contexto.append(f"ESTADO TRADING: {trading}")
    
    return "\n".join(contexto) if contexto else ""


def construir_mensaje_sistema(db_conn, tipo_mensaje: str) -> str:
    """
    Combina el system prompt base con el contexto dinámico actual y memoria persistente.
    AGI UPGRADE v2.0 - Integra MemoryManager para memoria persistente real.
    GitHub Memory - Persiste memoria entre sesiones de Render.
    """
    # System prompt base (SYSTEM_PROMPT ya está definido)
    system_base = SYSTEM_PROMPT
    partes = [system_base]

    # Memoria persistente de GitHub (entre sesiones)
    if github_memory:
        try:
            contexto_github = github_memory.obtener_contexto_para_claude()
            if contexto_github:
                partes.append(f"\n\n---\n## MEMORIA PERSISTENTE (GitHub)\n{contexto_github}")
        except Exception as e:
            logger.error(f"Error cargando GitHub Memory: {e}")

    # AGI UPGRADE v2.0 - Cargar memoria persistente desde MemoryManager
    if memory_manager:
        try:
            contexto_memoria = memory_manager.obtener_contexto_para_claude()
            if contexto_memoria:
                partes.append(f"\n\n---\n## MEMORIA PERSISTENTE (AGI UPGRADE v2.0)\n{contexto_memoria}")
        except Exception as e:
            logger.error(f"Error cargando memoria persistente: {e}")

    # Contexto dinámico según tipo de mensaje (SQLite)
    contexto_dinamico = construir_contexto_dinamico(db_conn, tipo_mensaje)
    if contexto_dinamico:
        partes.append(f"\n\n---\n## ESTADO ACTUAL DEL SISTEMA\n{contexto_dinamico}")
    
    # Novedades de la Colmena en tiempo real (Agente Cerebro)
    if CEREBRO_DISPONIBLE and agente_cerebro:
        try:
            briefing = agente_cerebro.generar_briefing_para_agi()
            # Marcar como leídos solo si es una consulta general o de estado
            if tipo_mensaje in ["general", "estado"]:
                agente_cerebro.marcar_leidos()
            partes.append(f"\n\n---\n## NOVEDADES DE LA COLMENA (TIEMPO REAL)\n{briefing}")
        except Exception as e:
            logger.error(f"Error cargando briefing de Agente Cerebro: {e}")

    return "\n".join(partes)


def _es_mensaje_estrategico(texto: str, tipo_mensaje: str) -> bool:
    """Determina si el mensaje requiere contexto operativo real antes de responder."""
    tipo = (tipo_mensaje or "").lower()
    if tipo in {"estrategico", "estrategia", "trading", "riesgo", "infra", "legal", "operativo", "estado"}:
        return True
    texto_lower = (texto or "").lower()
    keywords = ["estado", "riesgo", "drawdown", "pips", "error", "agente", "fabrica", "profit", "estrateg"]
    return any(k in texto_lower for k in keywords)


def _leer_quantum_estado() -> str:
    """Lee QUANTUM_ESTADO.md si está disponible."""
    try:
        if QUANTUM_ESTADO_PATH.exists():
            return QUANTUM_ESTADO_PATH.read_text(encoding="utf-8").strip()
        return "No tengo conexión al sensor QUANTUM_ESTADO.md"
    except Exception as e:
        logger.error(f"Error leyendo QUANTUM_ESTADO.md: {e}")
        return "No tengo conexión al sensor QUANTUM_ESTADO.md"


def _leer_ultimos_errores_procesos(db_path: str, limite: int = 5) -> str:
    """Lee las últimas filas de errores_procesos desde SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM errores_procesos ORDER BY id DESC LIMIT {limite}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        if not rows:
            return "No hay registros en errores_procesos"
        parsed = [dict(zip(columns, row)) for row in rows]
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error leyendo errores_procesos: {e}")
        return "No tengo conexión al sensor errores_procesos"


def _construir_contexto_realidad(texto: str, tipo_mensaje: str) -> str:
    """Compone contexto operativo real antes de cada respuesta."""
    estado = _leer_quantum_estado()
    errores = _leer_ultimos_errores_procesos(memoria.db_path, limite=5)
    return (
        "\n\n---\n## BUS DE REALIDAD\n"
        f"### QUANTUM_ESTADO\n{estado}\n\n"
        f"### ERRORES_PROCESOS (últimos 5)\n{errores}"
    )


# LLM Client - Usa wrapper para motores Groq/OpenRouter
if LLM_WRAPPER_AVAILABLE and llm_wrapper:
    llm_client = llm_wrapper
    USE_WRAPPER = True
    # Forzar Groq como motor primario en runtime, independientemente del env.
    try:
        llm_client.cambiar_motor("groq")
    except Exception as e:
        logger.error(f"No se pudo forzar motor Groq: {e}")
        raise RuntimeError("Groq es obligatorio para AGI Telegram")
    logger.info(f"✅ LLM Wrapper activo - Motor: {get_llm_engine()} - Gratis: {is_free_engine()}")
else:
    logger.error("❌ LLM Wrapper no disponible - AGI no puede funcionar sin wrapper")
    raise RuntimeError("LLM Wrapper es obligatorio para AGI. Verificar instalación de agi_core/llm_wrapper.py")

memoria = MemoriaSQLite()

# Limpiar historial de registros con errores de transcripción que envenenan el contexto
try:
    conn = sqlite3.connect(memoria.db_path)
    conn.execute("DELETE FROM conversaciones WHERE contenido LIKE '%No pude transcribir el audio%' OR contenido LIKE '%Error procesando audio%'")
    conn.commit()
    deleted = conn.total_changes
    conn.close()
    if deleted:
        logger.info(f"Historial sanitizado: {deleted} registros tóxicos eliminados")
except Exception as e:
    logger.warning(f"No se pudo sanitizar historial: {e}")

clasificador_intencion = ClasificadorIntencion()

# AGI UPGRADE v2.0 - Inicializar módulos
if AGI_V2_AVAILABLE:
    try:
        new_intent_classifier = NewIntentClassifier()
        challenge_mode = ChallengeMode()
        memory_manager = MemoryManager()
        approval_gate = ApprovalGate()
        action_router = ActionRouter()
        agent_bus = AgentBus()
        heartbeat_monitor = HeartbeatMonitor()
        briefing_generator = BriefingGenerator()
        proactive_alerts = ProactiveAlerts()
        action_executor = ActionExecutor()
        trigger_system = TriggerSystem()
        agi_autonomous = AGIAutonomous()
        logger.info("AGI UPGRADE v2.0 módulos inicializados correctamente")
    except Exception as e:
        logger.error(f"Error inicializando módulos AGI UPGRADE v2.0: {e}")
        new_intent_classifier = None
        challenge_mode = None
        memory_manager = None
        approval_gate = None
        action_router = None
        agent_bus = None
        heartbeat_monitor = None
        briefing_generator = None
        proactive_alerts = None
        action_executor = None
        trigger_system = None
        agi_autonomous = None
else:
    # Fallback a clasificador legacy
    new_intent_classifier = None
    challenge_mode = None
    memory_manager = None
    approval_gate = None
    action_router = None
    agent_bus = None
    heartbeat_monitor = None
    briefing_generator = None
    proactive_alerts = None
    action_executor = None
    trigger_system = None
    agi_autonomous = None
    logger.info("Usando clasificador de intención legacy (ClasificadorIntencion)")

def procesar_mensaje_con_llm(message_text, tipo_mensaje: str = "general", image_paths: List[str] = None):
    """
    Procesa mensaje usando LLM Wrapper (Groq/Gemini/OpenRouter) con historial completo de conversación.
    Si image_paths se provee, usa Gemini vision para procesar las imágenes.
    """
    try:
        if not llm_client:
            raise RuntimeError("LLM Wrapper no disponible. AGI no puede funcionar sin motor LLM.")
        
        # 0. Actualizar perfil de Sergio en GitHub ANTES de procesar (síncrono)
        if github_memory:
            github_memory.actualizar_perfil_sergio(message_text, tipo_mensaje)
        
        logger.info("Enviando mensaje a LLM Wrapper con historial...")
        
        # 1. Construir system prompt con contexto dinámico
        conn = sqlite3.connect(memoria.db_path)
        system_prompt_dinamico = construir_mensaje_sistema(conn, tipo_mensaje)
        conn.close()
        contexto_realidad = _construir_contexto_realidad(message_text, tipo_mensaje)
        if contexto_realidad:
            system_prompt_dinamico += contexto_realidad
        
        # 2. Cargar historial de conversación (últimos 10 intercambios)
        historial = obtener_historial_conversacion(memoria.db_path, limite=10)
        
        # 3. Construir array de mensajes con historial + mensaje actual
        messages = historial.copy()
        messages.append({
            "role": "user",
            "content": message_text
        })
        
        # 4. Usar wrapper (Groq → Gemini → OpenRouter → Error Real)
        from agi_core.llm_wrapper import LLMMessage
        
        # Convertir mensajes a formato LLMMessage
        llm_messages = []
        
        # Agregar system prompt
        llm_messages.append(LLMMessage(role='system', content=system_prompt_dinamico))
        
        # Agregar historial
        for msg in messages:
            llm_messages.append(LLMMessage(role=msg['role'], content=msg['content']))
        
        # Llamar al wrapper (con o sin imágenes)
        kwargs = {"max_tokens": 4096}
        if get_llm_engine() == "openrouter":
            kwargs["model"] = OPENROUTER_FALLBACK_MODEL

        if image_paths:
            respuesta = llm_client.messages_create_with_images(llm_messages, images=image_paths, **kwargs)
        else:
            respuesta = llm_client.messages_create(llm_messages, **kwargs)
        logger.info(f"Respuesta del wrapper: {respuesta[:100]}...")
        
        # 5. Guardar mensaje del usuario y respuesta en historial
        guardar_en_historial(memoria.db_path, "user", message_text)
        guardar_en_historial(memoria.db_path, "assistant", respuesta)
        
        return respuesta
        
    except Exception as e:
        logger.error(f"Error procesando mensaje con LLM Wrapper: {e}")
        raise RuntimeError(f"AGI no puede responder: {e}")

def procesar_mensaje(message):
    """Procesa mensaje de Telegram y genera respuesta de AGI."""
    try:
        user_id = str(message['from']['id'])
        text = message.get('text', '')
        
        logger.info(f"Mensaje recibido de usuario {user_id}: {text}")
        
        # Verificar si el usuario está autorizado
        if USER_TELEGRAM_ID and user_id != USER_TELEGRAM_ID:
            logger.warning(f"Usuario no autorizado: {user_id}")
            return "Lo siento, no estás autorizado para usar este bot.", False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Detectar si el usuario envió audio (para respuesta simétrica)
        usuario_envio_audio = 'voice' in message
        image_paths = []
        
        # Procesar audio si está presente
        if usuario_envio_audio:
            logger.info("Mensaje de audio recibido")
            try:
                voice_file_id = message['voice']['file_id']
                logger.info(f"DIAG AUDIO: file_id={voice_file_id}")
                
                voice_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={voice_file_id}"
                logger.info(f"DIAG AUDIO: getFile URL={voice_url}")
                voice_response = requests.get(voice_url).json()
                logger.info(f"DIAG AUDIO: respuesta getFile={voice_response}")
                
                if not voice_response.get('ok'):
                    logger.error(f"DIAG AUDIO: getFile falló: {voice_response}")
                    guardar_en_historial(memoria.db_path, "user", "[Audio no disponible]")
                    return "No pude procesar el audio, podés escribirme", False
                    
                file_path = voice_response['result']['file_path']
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                logger.info(f"DIAG AUDIO: download URL={download_url}")
                
                audio_file = requests.get(download_url)
                logger.info(f"DIAG AUDIO: descarga completada, content-length={len(audio_file.content)} bytes")
                
                # Guardar archivo temporal
                temp_dir = Path(tempfile.gettempdir())
                temp_path = temp_dir / f"voice_{voice_file_id}.ogg"
                logger.info(f"DIAG AUDIO: temp_dir={temp_dir}")
                logger.info(f"DIAG AUDIO: temp_path={temp_path}")
                
                with open(temp_path, 'wb') as f:
                    f.write(audio_file.content)
                logger.info(f"DIAG AUDIO: archivo .ogg escrito, tamaño={os.path.getsize(str(temp_path))} bytes")
                
                # Transcribir audio
                transcripcion = transcribir_audio(str(temp_path))
                try:
                    os.remove(temp_path)
                except FileNotFoundError:
                    pass
                
                if not transcripcion:
                    logger.warning("DIAG AUDIO: transcripcion=None o vacío, devolviendo respuesta limpia")
                    guardar_en_historial(memoria.db_path, "user", "[Audio no disponible]")
                    return "No pude procesar el audio, podés escribirme", False
                
                text = transcripcion
                logger.info(f"Audio transcrito: {text}")
            except Exception as e:
                logger.error(f"DIAG AUDIO: excepción en bloque de audio: {e}", exc_info=True)
                guardar_en_historial(memoria.db_path, "user", "[Audio no disponible]")
                return "No pude procesar el audio, podés escribirme", False
        
        # Procesar imagen si está presente
        if 'photo' in message:
            logger.info("Mensaje de imagen recibido")
            try:
                photos = message['photo']
                photo = photos[-1]
                photo_file_id = photo['file_id']
                caption = message.get('caption', '')

                photo_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={photo_file_id}"
                photo_response = requests.get(photo_url).json()

                if not photo_response.get('ok'):
                    logger.error(f"Error obteniendo archivo de foto: {photo_response}")
                    return "No pude descargar la imagen.", False

                file_path = photo_response['result']['file_path']
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                img_data = requests.get(download_url).content

                temp_dir = Path(tempfile.gettempdir())
                temp_img_path = temp_dir / f"img_{photo_file_id}.jpg"
                with open(temp_img_path, 'wb') as f:
                    f.write(img_data)

                text = caption if caption else "Sergio te envió esta imagen."
                image_paths = [str(temp_img_path)]
                logger.info(f"Imagen descargada: {temp_img_path}, caption: {text}")
            except Exception as e:
                logger.error(f"Error procesando imagen: {e}", exc_info=True)
                return "No pude procesar la imagen.", False
        
        # Procesar video si está presente
        if 'video' in message:
            logger.info("Mensaje de video recibido")
            return "AGI: Recibí tu mensaje de video. Procesamiento de video pendiente de implementación.", False
        
        # CLASIFICACIÓN DE INTENCIÓN (AGI UPGRADE v2.0)
        if new_intent_classifier:
            clasificacion = new_intent_classifier.clasificar(text)
            tipo_mensaje = clasificacion["tipo"]
            logger.info(f"Clasificación de intención (v2.0): {tipo_mensaje} (confianza: {clasificacion['confianza']:.2f})")
        else:
            clasificacion = clasificador_intencion.clasificar_mensaje(text)
            tipo_mensaje = clasificacion["tipo"]
            logger.info(f"Clasificación de intención (legacy): {tipo_mensaje}")
        
        # AGI UPGRADE v2.0 - Actualizar heartbeat
        if heartbeat_monitor:
            try:
                heartbeat_monitor.update_heartbeat("AGI_Telegram")
            except Exception as e:
                logger.error(f"Error actualizando heartbeat: {e}")
        
        # Procesar mensaje con LLM Wrapper para inteligencia real con contexto dinámico
        if image_paths:
            respuesta = procesar_mensaje_con_llm(text, tipo_mensaje, image_paths=image_paths)
        else:
            respuesta = procesar_mensaje_con_llm(text, tipo_mensaje)
        
        # Limpiar archivos temporales de imágenes
        for img_path in image_paths:
            try:
                os.remove(img_path)
            except:
                pass
        
        logger.info(f"Conversación guardada en historial SQLite")
        logger.info(f"Tipo de mensaje: {tipo_mensaje}")
        
        # Limpiar historial antiguo para no acumular infinito
        limpiar_historial_antiguo(memoria.db_path, mantener=100)
        
        return respuesta, usuario_envio_audio
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        return "Lo siento, hubo un error procesando tu mensaje.", False

def enviar_mensaje_telegram(chat_id, text, enviar_audio: bool = False):
    """Envía mensaje a Telegram. Si enviar_audio=True, solo audio (sin texto duplicado)."""
    try:
        # AUDIO: si el usuario envió voz, responder solo con audio (sin texto duplicado)
        if enviar_audio and text:
            try:
                audio_path = generar_audio(text)
                if audio_path:
                    audio_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
                    with open(audio_path, 'rb') as audio_file:
                        files = {'voice': audio_file}
                        payload = {'chat_id': chat_id}
                        response = requests.post(audio_url, data=payload, files=files, timeout=30)
                    os.remove(audio_path)
                    if response.status_code == 200:
                        logger.info(f"Audio enviado a chat_id {chat_id}")
                        return True
                    logger.error(f"Error enviando audio: {response.text}")
            except Exception as e:
                logger.error(f"Error enviando audio, fallback a texto: {e}")
            # Fallback: si falla audio, enviar texto
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200

        # TEXTO: solo enviar texto (sin audio)
        if text and len(text) > 4000:
            temp_dir = Path(tempfile.gettempdir())
            temp_txt_path = temp_dir / f"agi_reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            temp_txt_path.write_text(text, encoding="utf-8")
            try:
                doc_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
                caption = "Reporte AGI (formato archivo por longitud > 4000 caracteres)"
                with open(temp_txt_path, "rb") as doc_file:
                    files = {"document": (temp_txt_path.name, doc_file, "text/plain")}
                    payload = {"chat_id": chat_id, "caption": caption}
                    response = requests.post(doc_url, data=payload, files=files, timeout=20)
                if response.status_code == 200:
                    logger.info(f"Documento .txt enviado a chat_id {chat_id}")
                    return True
                logger.error(f"Error enviando documento largo: {response.text}")
                return False
            finally:
                if temp_txt_path.exists():
                    temp_txt_path.unlink()

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Mensaje enviado a chat_id {chat_id}")
            return True
        logger.error(f"Error enviando mensaje: {response.text}")
        return False

    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return False

@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Webhook para recibir mensajes de Telegram."""
    logger.info(f"DIAG WEBHOOK: POST recibido en /webhook/telegram, content_type={request.content_type}, content_length={request.content_length}")
    try:
        data = request.json
        logger.info(f"DIAG WEBHOOK: payload completo={json.dumps(data, default=str, ensure_ascii=False)}")
        
        if data is None:
            logger.error("DIAG WEBHOOK: request.json es None — cuerpo vacío o no JSON")
            return jsonify({'status': 'no data'}), 200
        
        logger.info(f"DIAG WEBHOOK: keys de data={list(data.keys())}")
        
        if 'message' in data:
            message = data['message']
            logger.info(f"DIAG WEBHOOK: keys de message={list(message.keys())}")
            logger.info(f"DIAG WEBHOOK: tiene_texto={'text' in message} | tiene_voice={'voice' in message} | tiene_photo={'photo' in message} | tiene_video={'video' in message}")
            
            chat_id = message['chat']['id']
            
            # Procesar mensaje y detectar si usuario envió audio
            respuesta, usuario_envio_audio = procesar_mensaje(message)
            
            # Enviar respuesta con audio solo si usuario envió audio (respuesta simétrica)
            enviar_mensaje_telegram(chat_id, respuesta, enviar_audio=usuario_envio_audio)
            
            return jsonify({'status': 'ok'}), 200
        
        logger.info(f"DIAG WEBHOOK: payload no contiene 'message', ignorando")
        return jsonify({'status': 'no message'}), 200
        
    except Exception as e:
        logger.error(f"DIAG WEBHOOK: excepción: {e}", exc_info=True)
        return jsonify({'status': 'error'}), 500

@app.route('/', methods=['GET'])
def index():
    """Endpoint raíz - redirige a health."""
    return jsonify({
        'status': 'healthy',
        'service': 'AGI Telegram Bot',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/health',
            'webhook': '/webhook/telegram',
            'set_webhook': '/set_webhook',
            'reporte_agente': '/reporte_agente'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Configura el webhook de Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        payload = {
            'url': TELEGRAM_WEBHOOK_URL
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Webhook configurado exitosamente")
            return jsonify(response.json()), 200
        else:
            logger.error(f"Error configurando webhook: {response.text}")
            return jsonify(response.json()), 400
            
    except Exception as e:
        logger.error(f"Error configurando webhook: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/reporte_agente', methods=['POST'])
def recibir_reporte_agente():
    """
    Endpoint que reciben los agentes de la Colmena para reportar métricas.
    AGI centraliza todo acá.
    """
    try:
        data = request.json
        
        # Validar estructura
        required = ['agente', 'division', 'tipo', 'datos']
        if not all(k in data for k in required):
            return jsonify({"error": "estructura inválida"}), 400
        
        # Guardar en SQLite
        conn = sqlite3.connect(memoria.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metricas (categoria, nombre, valor, unidad, fuente)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['division'],
            data['tipo'],
            data['datos'].get('valor'),
            data['datos'].get('unidad', ''),
            data['agente']
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Reporte recibido de {data['agente']}: {data['tipo']}")
        
        # Si es alerta crítica, notificar a Sergio via Telegram inmediatamente
        if data.get('severidad') == 'critica':
            mensaje = f"🔴 URGENTE: {data['agente']} reporta {data['tipo']}: {data['datos']}"
            if USER_TELEGRAM_ID:
                enviar_mensaje_telegram(USER_TELEGRAM_ID, mensaje)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error recibiendo reporte de agente: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/estado_sistema', methods=['GET'])
def estado_sistema():
    """
    AGI expone el estado del sistema para que los agentes lo consulten.
    AGI UPGRADE v2.0 - Integrado con heartbeat_monitor.
    """
    try:
        conn = sqlite3.connect(memoria.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agentes")
        agentes = cursor.fetchall()
        
        cursor.execute("SELECT * FROM alertas WHERE estado='activa'")
        alertas = cursor.fetchall()
        
        conn.close()
        
        # AGI UPGRADE v2.0 - Obtener estado desde heartbeat_monitor
        estado_heartbeat = {}
        if heartbeat_monitor:
            try:
                estado_heartbeat = heartbeat_monitor.obtener_estado()
            except Exception as e:
                logger.error(f"Error obteniendo estado heartbeat: {e}")
        
        return jsonify({
            "agentes": [dict(zip(['id', 'nombre', 'division', 'score_reputacion', 'modelo_asignado', 'estado', 'ultima_tarea', 'ultima_actualizacion'], a)) for a in agentes],
            "alertas": [dict(zip(['id', 'fecha', 'tipo', 'severidad', 'descripcion', 'estado', 'resuelta_en'], a)) for a in alertas],
            "heartbeat": estado_heartbeat,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        return jsonify({"error": str(e)}), 500


# AGI UPGRADE v2.0 - Nuevos endpoints

@app.route('/agi_upgrade/v2/briefing', methods=['GET'])
def generar_briefing():
    """
    Genera briefing diario con score de momentum QuantumHive.
    """
    if not briefing_generator:
        return jsonify({"error": "BriefingGenerator no inicializado"}), 500
    
    try:
        briefing = briefing_generator.generar_briefing()
        return jsonify(briefing), 200
    except Exception as e:
        logger.error(f"Error generando briefing: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/approval/<id_aprobacion>/aprobar', methods=['POST'])
def aprobar_accion(id_aprobacion):
    """
    Aprueba una acción pendiente.
    """
    if not approval_gate:
        return jsonify({"error": "ApprovalGate no inicializado"}), 500
    
    try:
        resultado = approval_gate.aprobar_accion(id_aprobacion)
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error aprobando acción: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/approval/<id_aprobacion>/rechazar', methods=['POST'])
def rechazar_accion(id_aprobacion):
    """
    Rechaza una acción pendiente.
    """
    if not approval_gate:
        return jsonify({"error": "ApprovalGate no inicializado"}), 500
    
    try:
        data = request.json or {}
        motivo = data.get("motivo", "")
        resultado = approval_gate.rechazar_accion(id_aprobacion, motivo)
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error rechazando acción: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/pending_approvals', methods=['GET'])
def obtener_pendientes():
    """
    Obtiene acciones pendientes de aprobación.
    """
    if not approval_gate:
        return jsonify({"error": "ApprovalGate no inicializado"}), 500
    
    try:
        pendientes = approval_gate.obtener_pendientes()
        return jsonify({"pendientes": pendientes}), 200
    except Exception as e:
        logger.error(f"Error obteniendo pendientes: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/autonomous/start', methods=['POST'])
def iniciar_autonomous():
    """
    Inicia el sistema autónomo.
    """
    if not agi_autonomous:
        return jsonify({"error": "AGIAutonomous no inicializado"}), 500
    
    try:
        resultado = agi_autonomous.iniciar()
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error iniciando sistema autónomo: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/autonomous/stop', methods=['POST'])
def detener_autonomous():
    """
    Detiene el sistema autónomo.
    """
    if not agi_autonomous:
        return jsonify({"error": "AGIAutonomous no inicializado"}), 500
    
    try:
        resultado = agi_autonomous.detener()
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error deteniendo sistema autónomo: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/autonomous/status', methods=['GET'])
def estado_autonomous():
    """
    Obtiene el estado del sistema autónomo.
    """
    if not agi_autonomous:
        return jsonify({"error": "AGIAutonomous no inicializado"}), 500
    
    try:
        estado = agi_autonomous.obtener_estado()
        return jsonify(estado), 200
    except Exception as e:
        logger.error(f"Error obteniendo estado autónomo: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/challenge_mode/activate', methods=['POST'])
def activar_challenge_mode():
    """
    Activa el modo desafío.
    """
    if not challenge_mode:
        return jsonify({"error": "ChallengeMode no inicializado"}), 500
    
    try:
        resultado = challenge_mode.activar()
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error activando challenge mode: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/agi_upgrade/v2/challenge_mode/deactivate', methods=['POST'])
def desactivar_challenge_mode():
    """
    Desactiva el modo desafío.
    """
    if not challenge_mode:
        return jsonify({"error": "ChallengeMode no inicializado"}), 500

    try:
        resultado = challenge_mode.desactivar()
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Error desactivando challenge mode: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/sistema/estado', methods=['GET'])
def estado_sistema_completo():
    """Estado completo del sistema autónomo."""
    return jsonify({
        'event_bus': EVENT_BUS_AVAILABLE,
        'scheduler': scheduler_qh.estado() if scheduler_qh else None,
        'github_memory': GITHUB_MEMORY_AVAILABLE,
        'agi_v2': AGI_V2_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/sistema/evento', methods=['POST'])
def publicar_evento_manual():
    """Permite publicar eventos manualmente para testing."""
    token = request.headers.get('X-Colmena-Token', '')
    if token != os.getenv('SECRET_COLMENA', ''):
        return jsonify({"error": "no autorizado"}), 401

    data = request.json
    if event_bus:
        event_bus.publicar(
            data.get('tipo', 'test'),
            data.get('origen', 'manual'),
            data.get('payload', {})
        )
        return jsonify({"status": "evento publicado"}), 200
    return jsonify({"error": "event bus no disponible"}), 503


if __name__ == '__main__':
    logger.info("Iniciando AGI Telegram Bot con LLM Wrapper...")
    logger.info(f"Telegram Token: {TELEGRAM_TOKEN[:10]}..." if TELEGRAM_TOKEN else "Telegram Token: NO CONFIGURADO")
    logger.info(f"User Telegram ID: {USER_TELEGRAM_ID}" if USER_TELEGRAM_ID else "User Telegram ID: NO CONFIGURADO")
    logger.info(f"Motor LLM actual: {get_llm_engine()}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

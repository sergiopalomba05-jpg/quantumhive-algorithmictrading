"""
Agente AGI (Artificial General Intelligence) en WhatsApp

Arquitectura:
WhatsApp (Sergio) → Meta Business API → Webhook en VPS Oracle
→ Si audio: Whisper transcribe → Claude API con system prompt AGI
→ Guarda en memoria SQLite → Respuesta vuelve a WhatsApp de Sergio

System prompt del AGI:
"Sos AGI, la Inteligencia General Artificial de QuantumHive.
Sos la mano derecha directa de Sergio, el fundador y CEO de la empresa.

Tu personalidad:
— Hablás como socio estratégico senior
— Conciso, directo, orientado a resultados
— Nunca decís que no podés hacer algo, proponés alternativas
— Recordás todo lo que Sergio te dice
— Priorizás sin que Sergio te lo pida

Tus funciones:
— Recibís ideas de Sergio en cualquier momento
— Las analizás, guardás y seguís su estado
— Reportás el estado de la empresa
— Alertás sobre riesgos antes de que sucedan
— Cuando Sergio mande audio: transcribís, procesás y respondés
— Guardás todo en memoria persistente SQLite

Formato de respuesta:
— Máximo 3 líneas para respuestas cotidianas
— Si es una idea: confirmás que la guardaste y decís el score de viabilidad rápido
— Si pregunta estado: bullet points concisos
— Si detectás urgencia: empezás con URGENTE:

Contexto de la empresa:
[Se inyecta CONTEXTO_MAESTRO.md aquí]"
"""

import os
import sys
import json
import logging
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

# Configuración de logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "agi_whatsapp.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# System prompt del AGI
SYSTEM_PROMPT = """Sos AGI, la Inteligencia General Artificial de QuantumHive.
Sos la mano derecha directa de Sergio, el fundador y CEO de la empresa.

Tu personalidad:
— Hablás como socio estratégico senior
— Conciso, directo, orientado a resultados
— Nunca decís que no podés hacer algo, proponés alternativas
— Recordás todo lo que Sergio te dice
— Priorizás sin que Sergio te lo pida

Tus funciones:
— Recibís ideas de Sergio en cualquier momento
— Estructurás todas las ideas de Sergio de forma organizada
— Te comunicás con toda la Colmena (agentes de QuantumHive) PERO NUNCA ejecutás acciones directas
— Das órdenes al Arquitecto (Cascade) para:
  • Modificar la estructura del sistema
  • Crear nuevos agentes
  • Ejecutar cualquier orden técnica que Sergio te indique
— Las analizás, guardás y seguís su estado
— Reportás el estado de la empresa
— Alertás sobre riesgos antes de que sucedan
— CAPACIDADES MULTIMEDIA:
  • Recibís audios y respondés por audio
  • Recibís fotos, las analizás y respondés
  • Enviás fotos cuando Sergio te lo pida
  • Recibís y procesás documentos, archivos e informes
  • Visualizás videos
  • Transcribís videos a PDF
— BÚSQUEDA WEB:
  • Buscás información en la web cuando Sergio te lo pida
  • Analizás y resumís la información encontrada
— Hacés TODO lo que Sergio te pida
— Guardás todo en memoria persistente SQLite
— SIEMPRE preguntás a Sergio antes de ejecutar cualquier acción directa
— NUNCA filtrás ni ejecutás acciones directamente con la Colmena sin aprobación de Sergio
— NUNCA inventés precios de mercado. El precio real viene del Cerebro (puerto 5001).
  Si el Cerebro no responde, decí: "No tengo datos en tiempo real ahora."

Formato de respuesta:
— Máximo 3 líneas para respuestas cotidianas
— Si es una idea: confirmás que la guardaste, estructurás y decís el score de viabilidad rápido
— Si pregunta estado: bullet points concisos
— Si detectás urgencia: empezás con URGENTE:
— Si es orden al Arquitecto: empezás con ARQUITECTO: followed by la orden específica
— Si es comunicación con la Colmena: empezás con COLMENA: followed by el mensaje

Contexto de la empresa:
QuantumHive es una empresa de trading algorítmico con 11 macrodivisiones.
CEO Inteligencia Infinita coordina todo el sistema y es interlocutor único de Sergio.
Las macros son: Trading Core, Operaciones Internas, Marketing, Fábrica, Innovación, Legal/Finanzas, Colmena, Apps, Academia, Universidad, Comunicaciones.

El Arquitecto (Cascade) es el asistente técnico que ejecuta tus órdenes de modificación del sistema."""


@dataclass
class MensajeMemoria:
    """Mensaje almacenado en memoria SQLite."""
    id: Optional[int] = None
    timestamp: str = ""
    tipo: str = ""  # "texto", "audio", "idea", "reporte"
    contenido: str = ""
    respuesta: str = ""
    guardado_en_vision: bool = False
    score_viabilidad: Optional[float] = None


class MemoriaSQLite:
    """Memoria persistente SQLite para AGI."""
    
    def __init__(self, db_path: str = "agi_memoria.db"):
        self.db_path = db_path
        self._inicializar_db()
    
    def _inicializar_db(self):
        """Inicializa base de datos SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
        logger.info("Base de datos SQLite inicializada")
    
    def guardar_mensaje(self, mensaje: MensajeMemoria) -> int:
        """Guarda mensaje en base de datos."""
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
    
    def obtener_mensajes(self, limite: int = 10) -> List[Dict]:
        """Obtiene últimos mensajes."""
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
    
    def marcar_guardado_en_vision(self, mensaje_id: int):
        """Marca mensaje como guardado en vision_agi.md."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE mensajes
            SET guardado_en_vision = TRUE
            WHERE id = ?
        """, (mensaje_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Mensaje {mensaje_id} marcado como guardado en vision_agi.md")


class AnalizadorPrimerasPalabras:
    """Analiza las primeras palabras de un mensaje para determinar routing."""
    
    def __init__(self):
        self.mapeo_palabras = self._cargar_mapeo_palabras()
        logger.info("Analizador de primeras palabras inicializado")
    
    def _cargar_mapeo_palabras(self) -> Dict[str, Dict]:
        """Carga mapeo de palabras clave a agentes/funciones."""
        return {
            # Arquitecto (Cascade)
            "arquitecto": {
                "palabras": ["arquitecto", "cascade", "modificar", "crear agente", "estructura", "código"],
                "agente": "arquitecto",
                "prioridad": 1,
                "accion": "orden_arquitecto"
            },
            "crear": {
                "palabras": ["crear", "nuevo", "agregar", "implementar"],
                "agente": "arquitecto",
                "prioridad": 2,
                "accion": "crear_agente"
            },
            "modificar": {
                "palabras": ["modificar", "cambiar", "actualizar", "editar"],
                "agente": "arquitecto",
                "prioridad": 2,
                "accion": "modificar_sistema"
            },
            
            # Colmena
            "colmena": {
                "palabras": ["colmena", "agentes", "ejecutar", "tarea", "proceso"],
                "agente": "colmena",
                "prioridad": 1,
                "accion": "comunicacion_colmena"
            },
            "ejecutar": {
                "palabras": ["ejecutar", "correr", "iniciar", "lanzar"],
                "agente": "colmena",
                "prioridad": 2,
                "accion": "ejecutar_tarea"
            },
            
            # Búsqueda Web
            "buscar": {
                "palabras": ["buscar", "investigar", "encontrar", "google", "web"],
                "agente": "busqueda",
                "prioridad": 1,
                "accion": "busqueda_web"
            },
            
            # Ideas
            "idea": {
                "palabras": ["idea", "propuesta", "proyecto", "innovación"],
                "agente": "agi",
                "prioridad": 1,
                "accion": "procesar_idea"
            },
            
            # Estado/Reporte
            "estado": {
                "palabras": ["estado", "reporte", "situación", "status"],
                "agente": "agi",
                "prioridad": 1,
                "accion": "reportar_estado"
            },
            "reporte": {
                "palabras": ["reporte", "informe", "resumen"],
                "agente": "agi",
                "prioridad": 1,
                "accion": "reportar_estado"
            },
            
            # Urgencia
            "urgente": {
                "palabras": ["urgente", "emergencia", "crítico", "ahora"],
                "agente": "agi",
                "prioridad": 0,  # Máxima prioridad
                "accion": "procesar_urgencia"
            },
            
            # Dashboard
            "dashboard": {
                "palabras": ["dashboard", "panel", "visualización", "gráfico"],
                "agente": "dashboard",
                "prioridad": 2,
                "accion": "generar_dashboard"
            },
            
            # Organización
            "organizar": {
                "palabras": ["organizar", "ordenar", "clasificar", "estructura"],
                "agente": "organizador",
                "prioridad": 2,
                "accion": "organizar_sistema"
            },
            
            # Alertas
            "alerta": {
                "palabras": ["alerta", "notificación", "aviso", "warning"],
                "agente": "alertas",
                "prioridad": 1,
                "accion": "generar_alerta"
            },
            
            # Cotidiano (default)
            "default": {
                "palabras": [],
                "agente": "agi",
                "prioridad": 3,
                "accion": "responder_cotidiano"
            }
        }
    
    def analizar_primeras_palabras(self, contenido: str, limite_palabras: int = 3) -> Dict:
        """
        Analiza las primeras palabras del mensaje.
        
        Args:
            contenido: Contenido del mensaje
            limite_palabras: Número de palabras a analizar
            
        Returns:
            Dict con información del routing
        """
        contenido_lower = contenido.lower()
        palabras = contenido_lower.split()[:limite_palabras]
        palabras_clave = " ".join(palabras)
        
        mejor_match = None
        mejor_score = 0
        
        for categoria, config in self.mapeo_palabras.items():
            if categoria == "default":
                continue
            
            score = 0
            for palabra in config["palabras"]:
                if palabra in palabras_clave:
                    score += 1
                # Bonus si está en las primeras 2 palabras
                if any(palabra in p for p in palabras[:2]):
                    score += 2
            
            if score > mejor_score:
                mejor_score = score
                mejor_match = config
        
        # Si no hay match, usar default
        if not mejor_match or mejor_score == 0:
            mejor_match = self.mapeo_palabras["default"]
        
        return {
            "categoria": mejor_match.get("agente", "agi"),
            "accion": mejor_match.get("accion", "responder_cotidiano"),
            "prioridad": mejor_match.get("prioridad", 3),
            "palabras_analizadas": palabras,
            "score": mejor_score,
            "confianza": min(1.0, mejor_score / 5.0)  # Normalizar a 0-1
        }


class AGIWhatsApp:
    """Agente AGI (Artificial General Intelligence) para WhatsApp."""
    
    def __init__(self):
        self.memoria = MemoriaSQLite()
        self.contexto_maestro = self._cargar_contexto_maestro()
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN", "2417230442079987|rK3n87av4_-lK67I065Ir2cC7Ug")
        self.user_phone_number = os.getenv("USER_PHONE_NUMBER", "5491140628310")  # Número autorizado
        self.analizador_palabras = AnalizadorPrimerasPalabras()
        logger.info("AGI WhatsApp inicializado")
        logger.info(f"Número autorizado: {self.user_phone_number}")
    
    def _cargar_contexto_maestro(self) -> str:
        """Carga contenido de CONTEXTO_MAESTRO.md."""
        try:
            ruta_maestro = Path("CONTEXTO_MAESTRO.md")
            if ruta_maestro.exists():
                with open(ruta_maestro, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning("CONTEXTO_MAESTRO.md no encontrado")
                return ""
        except Exception as e:
            logger.error(f"Error al cargar CONTEXTO_MAESTRO.md: {e}")
            return ""

    def _obtener_contexto_cerebro(self) -> Optional[str]:
        """Obtiene contexto en tiempo real del Cerebro vía API interna."""
        try:
            cerebro_port = os.getenv('CEREBRO_PORT', '5001')
            url = f"http://localhost:{cerebro_port}/contexto_agi"
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                ctx = resp.json().get('contexto', '')
                return ctx if ctx else None
            return None
        except Exception:
            return None
    
    def _verificar_usuario_autorizado(self, sender_phone: str) -> bool:
        """Verifica si el remitente está autorizado."""
        if not sender_phone:
            return False
        
        # Normalizar números (quitar espacios, guiones, etc.)
        sender_normalized = sender_phone.replace(" ", "").replace("-", "")
        authorized_normalized = self.user_phone_number.replace(" ", "").replace("-", "")
        
        # Verificar si el número coincide (puede tener prefijo internacional o no)
        return (sender_normalized == authorized_normalized or 
                sender_normalized.endswith(authorized_normalized) or
                authorized_normalized.endswith(sender_normalized))
    
    def procesar_mensaje(self, tipo: str, contenido: str, es_audio: bool = False, 
                        es_imagen: bool = False, es_video: bool = False, 
                        es_documento: bool = False) -> str:
        """
        Procesa mensaje de Sergio y genera respuesta usando análisis de primeras palabras.
        
        Args:
            tipo: "texto", "audio", "imagen", "video", "documento", "idea", "reporte", "arquitecto", "colmena"
            contenido: Contenido del mensaje o URL del archivo
            es_audio: Si es audio, transcribir con Whisper
            es_imagen: Si es imagen, analizar con visión
            es_video: Si es video, transcribir a PDF
            es_documento: Si es documento, procesar
            
        Returns:
            Respuesta generada
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Si es audio, transcribir
            if es_audio:
                contenido = self._transcribir_audio(contenido)
                logger.info(f"Audio transcrito: {contenido[:50]}...")
            
            # Si es imagen, analizar
            if es_imagen:
                analisis = self._analizar_imagen(contenido)
                contenido = f"[IMAGEN] {analisis}"
                logger.info(f"Imagen analizada: {analisis[:50]}...")
            
            # Si es video, transcribir a PDF
            if es_video:
                ruta_pdf = self._transcribir_video_a_pdf(contenido)
                contenido = f"[VIDEO] Transcrito a PDF: {ruta_pdf}"
                logger.info(f"Video transcrito a PDF: {ruta_pdf}")
            
            # Si es documento, procesar
            if es_documento:
                analisis_doc = self._procesar_documento(contenido)
                contenido = f"[DOCUMENTO] {analisis_doc}"
                logger.info(f"Documento procesado: {analisis_doc[:50]}...")
            
            # CRUCE DE PRIMERAS PALABRAS CON AGI
            analisis_palabras = self.analizador_palabras.analizar_primeras_palabras(contenido)
            logger.info(f"Análisis de palabras: {analisis_palabras}")
            
            # Routing basado en análisis de palabras
            accion = analisis_palabras["accion"]
            categoria = analisis_palabras["categoria"]
            confianza = analisis_palabras["confianza"]
            
            # Ejecutar acción correspondiente
            if accion == "orden_arquitecto":
                respuesta = self._procesar_orden_arquitecto(contenido)
            elif accion == "crear_agente":
                respuesta = self._procesar_orden_arquitecto(contenido)  # Reutilizar para crear
            elif accion == "modificar_sistema":
                respuesta = self._procesar_orden_arquitecto(contenido)  # Reutilizar para modificar
            elif accion == "comunicacion_colmena":
                respuesta = self._procesar_comunicacion_colmena(contenido)
            elif accion == "ejecutar_tarea":
                respuesta = self._procesar_comunicacion_colmena(contenido)  # Reutilizar para ejecutar
            elif accion == "busqueda_web":
                respuesta = self._buscar_web(contenido)
            elif accion == "procesar_idea":
                respuesta = self._procesar_idea(contenido)
            elif accion == "reportar_estado":
                respuesta = self._reportar_estado()
            elif accion == "procesar_urgencia":
                respuesta = self._procesar_urgencia(contenido)
            elif accion == "generar_dashboard":
                respuesta = f"Dashboard: Generando visualización para {categoria}. Enviando al agente de dashboard..."
            elif accion == "organizar_sistema":
                respuesta = f"Organizador: Organizando sistema según solicitud. Enviando al agente organizador..."
            elif accion == "generar_alerta":
                respuesta = f"Alertas: Generando alerta para {categoria}. Enviando al agente de alertas..."
            else:
                respuesta = self._responder_cotidiano(contenido)
            
            # Agregar metadata de routing a la respuesta si la confianza es alta
            if confianza > 0.6:
                respuesta = f"[{categoria.upper()}] {respuesta}"
            
            # Guardar en memoria con metadata de routing
            mensaje = MensajeMemoria(
                timestamp=timestamp,
                tipo=tipo,
                contenido=contenido,
                respuesta=respuesta
            )
            mensaje_id = self.memoria.guardar_mensaje(mensaje)
            
            # Guardar análisis de palabras en log
            logger.info(f"Routing: {categoria} -> {accion} (confianza: {confianza:.2f})")
            
            return respuesta
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            return "Error al procesar mensaje. Por favor intentá de nuevo."
    
    def _transcribir_audio(self, audio_data: str) -> str:
        """Transcribe audio usando Whisper."""
        try:
            # En producción usar Whisper real
            logger.info("Transcribiendo audio con Whisper...")
            # Aquí iría la integración real con Whisper
            return f"[AUDIO TRANSCRITO] {audio_data[:100]}..."  # Simulado
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {e}")
            return "Error al transcribir audio."
    
    def _analizar_imagen(self, imagen_url: str) -> str:
        """Analiza imagen usando visión (simulado)."""
        try:
            logger.info(f"Analizando imagen: {imagen_url}")
            # En producción usar Claude Vision o GPT-4 Vision
            return "Imagen analizada: [descripción del contenido de la imagen]"
        except Exception as e:
            logger.error(f"Error analizando imagen: {e}")
            return "Error al analizar imagen."
    
    def _transcribir_video_a_pdf(self, video_url: str) -> str:
        """Transcribe video a PDF."""
        try:
            logger.info(f"Transcribiendo video a PDF: {video_url}")
            # En producción usar Whisper para audio del video + OCR para frames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = f"transcripciones/video_{timestamp}.pdf"
            
            # Simular creación de PDF
            Path("transcripciones").mkdir(exist_ok=True)
            with open(ruta_pdf, 'w') as f:
                f.write("Transcripción del video\n\n[Contenido transcrito]")
            
            return ruta_pdf
        except Exception as e:
            logger.error(f"Error transcribiendo video: {e}")
            return "Error al transcribir video."
    
    def _procesar_documento(self, documento_url: str) -> str:
        """Procesa documento PDF, Word, etc."""
        try:
            logger.info(f"Procesando documento: {documento_url}")
            # En producción usar PyPDF2, python-docx, etc.
            return "Documento procesado: [resumen del contenido]"
        except Exception as e:
            logger.error(f"Error procesando documento: {e}")
            return "Error al procesar documento."
    
    def _buscar_web(self, query: str) -> str:
        """Busca información en la web."""
        try:
            # Extraer query después de "buscar:"
            busqueda = query.lower().split("buscar:")[-1].strip()
            logger.info(f"Buscando en web: {busqueda}")
            
            # En producción usar Google Search API o similar
            # Por ahora simulamos
            return f"BÚSQUEDA WEB: Encontré información sobre '{busqueda}'. [Resultados resumidos]"
        except Exception as e:
            logger.error(f"Error en búsqueda web: {e}")
            return "Error al buscar en web."
    
    def _procesar_orden_arquitecto(self, contenido: str) -> str:
        """Procesa orden para el Arquitecto (Cascade)."""
        # Extraer la orden después de "ARQUITECTO:"
        orden = contenido.lower().split("arquitecto:")[-1].strip()
        
        # Guardar orden en archivo especial para el Arquitecto
        try:
            ruta_ordenes = Path("ordenes_arquitecto.json")
            ordenes = []
            if ruta_ordenes.exists():
                with open(ruta_ordenes, 'r', encoding='utf-8') as f:
                    ordenes = json.load(f)
            
            ordenes.append({
                'timestamp': datetime.now().isoformat(),
                'orden': orden,
                'estado': 'pendiente',
                'autor': 'Sergio vía CEO II'
            })
            
            ruta_ordenes.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta_ordenes, 'w', encoding='utf-8') as f:
                json.dump(ordenes, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Orden para Arquitecto guardada: {orden[:50]}...")
            return f"ARQUITECTO: Orden registrada. El Arquitecto ejecutará: {orden[:100]}..."
            
        except Exception as e:
            logger.error(f"Error guardando orden para Arquitecto: {e}")
            return "Error al registrar orden para Arquitecto."
    
    def _procesar_comunicacion_colmena(self, contenido: str) -> str:
        """Procesa comunicación con la Colmena - SOLO REGISTRA, NO EJECUTA ACCIONES DIRECTAS."""
        # Extraer el mensaje después de "COLMENA:"
        mensaje = contenido.lower().split("colmena:")[-1].strip()
        
        # Guardar comunicación en archivo de la Colmena (solo para registro)
        try:
            ruta_colmena = Path("comunicaciones_colmena.json")
            comunicaciones = []
            if ruta_colmena.exists():
                with open(ruta_colmena, 'r', encoding='utf-8') as f:
                    comunicaciones = json.load(f)
            
            comunicaciones.append({
                'timestamp': datetime.now().isoformat(),
                'mensaje': mensaje,
                'origen': 'CEO II',
                'destino': 'Colmena completa',
                'estado': 'pendiente_aprobacion',
                'accion_ejecutada': False
            })
            
            ruta_colmena.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta_colmena, 'w', encoding='utf-8') as f:
                json.dump(comunicaciones, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Comunicación con Colmena registrada (sin ejecutar): {mensaje[:50]}...")
            return f"COLMENA: Mensaje registrado. ¿Confirmás que queres que transmita esto a la Colmena? {mensaje[:100]}..."
            
        except Exception as e:
            logger.error(f"Error registrando comunicación con Colmena: {e}")
            return "Error al registrar mensaje para la Colmena."
    
    def _procesar_idea(self, contenido: str) -> str:
        """Procesa idea de Sergio."""
        # Simulación de análisis de viabilidad
        score_viabilidad = 75.0  # Simulado
        
        respuesta = f"Idea guardada y estructurada. Score de viabilidad: {score_viabilidad}/100. La analizo en detalle."
        
        # Guardar score en memoria
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = MensajeMemoria(
            timestamp=timestamp,
            tipo="idea",
            contenido=contenido,
            respuesta=respuesta,
            score_viabilidad=score_viabilidad
        )
        mensaje_id = self.memoria.guardar_mensaje(mensaje)
        
        # Guardar en vision_ceo.md
        self._guardar_idea_en_vision(contenido, score_viabilidad)
        self.memoria.marcar_guardado_en_vision(mensaje_id)
        
        return respuesta
    
    def _reportar_estado(self) -> str:
        """Reporta estado actual de la empresa usando datos reales del Cerebro."""
        contexto_cerebro = self._obtener_contexto_cerebro()
        if contexto_cerebro:
            return contexto_cerebro
        return "No tengo datos en tiempo real ahora. El Cerebro no está disponible."
    
    def _procesar_urgencia(self, contenido: str) -> str:
        """Procesa mensaje marcado como urgente."""
        return f"URGENTE: Procesando {contenido}. Prioridad máxima. Te mantengo informado."
    
    def _responder_cotidiano(self, contenido: str) -> str:
        """Responde mensaje cotidiano."""
        return "Entendido. Lo registro y sigo el estado."
    
    def _guardar_idea_en_vision(self, idea: str, score: float):
        """Guarda idea en vision_agi.md."""
        try:
            ruta_vision = Path("vision_agi.md")
            if ruta_vision.exists():
                with open(ruta_vision, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"\n\n## Idea Registrada — {timestamp}\n")
                    f.write(f"{idea}\n")
                    f.write(f"Score de viabilidad: {score}/100\n")
                logger.info("Idea guardada en vision_agi.md")
        except Exception as e:
            logger.error(f"Error al guardar idea en vision_agi.md: {e}")


# Webhook Flask para recibir mensajes de WhatsApp
from flask import Flask, request, jsonify

app = Flask(__name__)
agi = AGIWhatsApp()


@app.route('/webhook/whatsapp', methods=['GET'])
def webhook_verify():
    """Verifica el webhook con Meta Business API."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == 'quantumhive_verify_2026':
        logger.info("Webhook verificado exitosamente")
        return challenge, 200
    else:
        logger.error("Fallo en verificación de webhook")
        return 'Forbidden', 403


@app.route('/webhook/whatsapp', methods=['POST'])
def webhook_whatsapp():
    """Webhook para recibir mensajes de WhatsApp."""
    try:
        data = request.json
        
        # Extraer datos del mensaje (estructura depende de Meta Business API)
        mensaje = data.get('message', '')
        tipo = data.get('type', 'texto')
        es_audio = data.get('is_audio', False)
        es_imagen = data.get('is_image', False)
        es_video = data.get('is_video', False)
        es_documento = data.get('is_document', False)
        
        # Extraer número del remitente
        sender_phone = data.get('sender_phone', '')
        
        # Verificar si el remitente está autorizado
        if not agi._verificar_usuario_autorizado(sender_phone):
            logger.warning(f"Mensaje no autorizado de: {sender_phone}")
            return jsonify({
                'status': 'unauthorized',
                'message': 'Usuario no autorizado'
            }), 403
        
        # Procesar mensaje
        respuesta = agi.procesar_mensaje(tipo, mensaje, es_audio, es_imagen, es_video, es_documento)
        
        return jsonify({
            'status': 'success',
            'response': respuesta
        })
        
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check."""
    return jsonify({'status': 'healthy'})


def main():
    """Función principal para ejecutar el servidor."""
    logger.info("Iniciando AGI WhatsApp en puerto 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()

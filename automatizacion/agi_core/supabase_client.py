"""
Supabase Client para AGI Telegram
Gestiona la conexión a Supabase PostgreSQL para memoria persistente.
"""
import os
from supabase import create_client, Client
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Credenciales de Supabase (desde variables de entorno o hardcoded para desarrollo)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fcmerslnpkpraznclkew.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_WW857EjU7KfLaHiva1a6eQ_0VcLNcSP")  # anon key
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "sb_secret_e8mlQ9YoOE6Q9OL_MCo6Vg_ca6fmc7_")  # service role key

class SupabaseMemory:
    """Cliente de memoria Supabase para AGI."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con Supabase."""
        try:
            logger.info(f"Intentando conectar a Supabase: URL={SUPABASE_URL[:20]}...")
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.error("Credenciales de Supabase no configuradas")
                logger.error(f"SUPABASE_URL: {SUPABASE_URL}")
                logger.error(f"SUPABASE_KEY: {SUPABASE_KEY[:10] if SUPABASE_KEY else 'None'}...")
                return
            
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Conexión a Supabase establecida exitosamente")
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {e}")
            logger.error(f"SUPABASE_URL: {SUPABASE_URL}")
            logger.error(f"SUPABASE_KEY: {SUPABASE_KEY[:10] if SUPABASE_KEY else 'None'}...")
    
    def guardar_conversacion(self, rol: str, contenido: str, tipo_mensaje: str = "texto") -> int:
        """
        Guarda un mensaje en la tabla conversaciones.
        rol: "user" | "assistant"
        Retorna el ID del registro insertado.
        """
        try:
            if not self.client:
                logger.error("Cliente Supabase no inicializado")
                return -1
            
            data = {
                "rol": rol,
                "contenido": contenido,
                "tipo_mensaje": tipo_mensaje,
                "fecha": datetime.now().isoformat()
            }
            
            response = self.client.table("conversaciones").insert(data).execute()
            
            if response.data:
                registro_id = response.data[0]["id"]
                logger.info(f"Conversación guardada en Supabase con ID {registro_id}")
                return registro_id
            else:
                logger.error("Error guardando conversación: respuesta vacía")
                return -1
                
        except Exception as e:
            logger.error(f"Error guardando conversación en Supabase: {e}")
            return -1
    
    def obtener_historial(self, limite: int = 10) -> List[Dict]:
        """
        Obtiene los últimos N intercambios de conversación.
        Retorna lista de mensajes en formato Claude API.
        """
        try:
            if not self.client:
                logger.error("Cliente Supabase no inicializado")
                return []
            
            response = self.client.table("conversaciones").select("*").order("fecha", desc=True).limit(limite * 2).execute()
            
            mensajes = response.data if response.data else []
            
            # Invertir para orden cronológico correcto
            mensajes = list(reversed(mensajes))
            
            historial = []
            for msg in mensajes:
                historial.append({
                    "role": msg["rol"],
                    "content": msg["contenido"]
                })
            
            return historial
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de Supabase: {e}")
            return []
    
    def limpiar_historial_antiguo(self, mantener: int = 100):
        """
        Mantiene solo los últimos N mensajes en conversaciones.
        """
        try:
            if not self.client:
                logger.error("Cliente Supabase no inicializado")
                return
            
            # Obtener todos los IDs ordenados por fecha
            response = self.client.table("conversaciones").select("id").order("fecha", desc=True).execute()
            
            if not response.data:
                return
            
            todos_ids = [msg["id"] for msg in response.data]
            
            # Mantener solo los primeros N
            ids_a_eliminar = todos_ids[mantener:]
            
            if ids_a_eliminar:
                # Eliminar en lotes
                for i in range(0, len(ids_a_eliminar), 100):
                    lote = ids_a_eliminar[i:i+100]
                    self.client.table("conversaciones").delete().in_("id", lote).execute()
                
                logger.info(f"Historial limpiado: {len(ids_a_eliminar)} mensajes antiguos eliminados")
                
        except Exception as e:
            logger.error(f"Error limpiando historial antiguo: {e}")
    
    def guardar_idea(self, titulo: str, descripcion: str, categoria: str, score: int, notas: str = "") -> int:
        """Guarda idea de Sergio en Supabase."""
        try:
            if not self.client:
                logger.error("Cliente Supabase no inicializado")
                return -1
            
            data = {
                "titulo": titulo,
                "descripcion": descripcion,
                "categoria": categoria,
                "score": score,
                "notas": notas,
                "fecha": datetime.now().isoformat()
            }
            
            response = self.client.table("ideas").insert(data).execute()
            
            if response.data:
                idea_id = response.data[0]["id"]
                logger.info(f"Idea guardada en Supabase con ID {idea_id}")
                return idea_id
            else:
                logger.error("Error guardando idea: respuesta vacía")
                return -1
                
        except Exception as e:
            logger.error(f"Error guardando idea en Supabase: {e}")
            return -1
    
    def obtener_ideas(self, limite: int = 10) -> List[Dict]:
        """Obtiene últimas ideas."""
        try:
            if not self.client:
                logger.error("Cliente Supabase no inicializado")
                return []
            
            response = self.client.table("ideas").select("*").order("fecha", desc=True).limit(limite).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error obteniendo ideas de Supabase: {e}")
            return []

# Instancia global
supabase_memory = SupabaseMemory()

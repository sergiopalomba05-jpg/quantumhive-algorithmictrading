"""
GOAT BTC — ChatBTC
Modo conversación sobre el mercado BTC/USD usando el LLM Wrapper de QuantumHive.
"""

import logging

logger = logging.getLogger(__name__)


class ChatBTC:

    def __init__(self):
        self.disponible = False
        try:
            from automatizacion.agi_core.llm_wrapper import llm_wrapper, LLMMessage
            self.llm_wrapper = llm_wrapper
            self.LLMMessage = LLMMessage
            self.disponible = True
        except (ImportError, AttributeError):
            logger.warning("LLM Wrapper no disponible, modo conversación desactivado")

    def generar_contexto_mercado(self, snapshot: dict) -> str:
        return (
            f"Precio: {snapshot.get('precio', 'N/A')}\n"
            f"BB Superior: {snapshot.get('bb_superior', 'N/A')}\n"
            f"BB Media: {snapshot.get('bb_media', 'N/A')}\n"
            f"BB Inferior: {snapshot.get('bb_inferior', 'N/A')}\n"
            f"BBW: {snapshot.get('bbw', 'N/A')}\n"
            f"ADX M15: {snapshot.get('adx_m15', 'N/A')}\n"
            f"CVD Corto: {snapshot.get('cvd_corto', 'N/A')}\n"
            f"CVD Largo: {snapshot.get('cvd_largo', 'N/A')}\n"
            f"Régimen: {snapshot.get('regimen', 'N/A')}\n"
            f"Última señal: {snapshot.get('ultima_senal', 'N/A')}\n"
            f"Score: {snapshot.get('score', 'N/A')}\n"
            f"Clasificación: {snapshot.get('clasificacion', 'N/A')}\n"
            f"Confluencias: {snapshot.get('confluencias', [])}\n"
            f"Volumen Relativo: {snapshot.get('vol_relativo', 'N/A')}\n"
            f"Imbalance Book: {snapshot.get('imbalance_book', 'N/A')}\n"
            f"Delta Vela: {snapshot.get('delta_vela', 'N/A')}\n"
            f"Últimas señales: {snapshot.get('historial_reciente', [])}"
        )

    def preguntar(self, pregunta: str, snapshot_mercado: dict) -> str:
        if not self.disponible:
            return "Modo conversación no disponible"
        contexto = self.generar_contexto_mercado(snapshot_mercado)
        system_prompt = (
            "Sos el analista BTC del sistema G.O.A.T Protocol de QuantumHive.\n"
            "Respondé en máximo 3-4 líneas. Sólamente sobre BTC/USD.\n"
            f"Contexto actual del mercado:\n{contexto}"
        )
        messages = [
            self.LLMMessage(role="system", content=system_prompt),
            self.LLMMessage(role="user", content=pregunta),
        ]
        try:
            respuesta = self.llm_wrapper.messages_create(messages, max_tokens=512)
            return respuesta.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return "Error generando respuesta"

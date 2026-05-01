"""
Keep-Alive automático para Render
Mantiene el servicio activo enviando pings cada 5 minutos
"""
import requests
import time
import threading
from datetime import datetime

RENDER_URL = "https://agi-telegram2-0.onrender.com/health"
INTERVALO = 280  # 4 minutos 40 segundos

def ping():
    while True:
        try:
            response = requests.get(RENDER_URL, timeout=10)
            print(f"{datetime.now()} - Ping OK: {response.status_code}")
        except Exception as e:
            print(f"{datetime.now()} - Ping error: {e}")
        time.sleep(INTERVALO)

def iniciar_keep_alive():
    hilo = threading.Thread(target=ping, daemon=True)
    hilo.start()
    print("Keep-alive iniciado")

if __name__ == "__main__":
    iniciar_keep_alive()
    while True:
        time.sleep(60)

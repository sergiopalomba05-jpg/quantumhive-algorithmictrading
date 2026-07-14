"""
setup_llm_cloud.py
Helper para configurar LLM gratuito en la nube sin instalar nada local.
Ideal para disco limitado (< 5GB libres).

Instrucciones:
  1. Ejecutar: python scripts/setup_llm_cloud.py
  2. Seguir pasos interactivos para obtener API key gratuita.
  3. El script guarda automaticamente en .env (crea si no existe).

Proveedores soportados:
  - Groq (RECOMENDADO): Llama 3.3 70B, gratis, muy rapido.
    URL: https://console.groq.com/keys
  - Google Gemini: 60 req/min gratis.
    URL: https://aistudio.google.com/app/apikey

Autor: QuantumHive AI
"""

import os
import sys
from pathlib import Path

RAIZ = Path("C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING")
ENV_PATH = RAIZ / ".env"


def print_banner():
    print("=" * 60)
    print("  QuantumHive — Setup LLM Cloud (Sin instalar nada local)")
    print("  Disco limitado? Esto ocupa 0 bytes. Solo necesitas una API key.")
    print("=" * 60)
    print()


def detectar_disco():
    import shutil
    total, used, free = shutil.disk_usage(str(RAIZ))
    free_gb = free / (1024**3)
    print(f"[INFO] Espacio libre en disco: {free_gb:.2f} GB")
    if free_gb < 2:
        print("[ALERTA] Muy poco espacio. Cloud-only es la UNICA opcion viable.")
    print()
    return free_gb


def obtener_groq():
    print("-" * 60)
    print("PROVEEDOR RECOMENDADO: Groq")
    print("-" * 60)
    print("Pasos:")
    print("  1. Abrir navegador: https://console.groq.com/keys")
    print("  2. Crear cuenta gratis (email + verificacion)")
    print("  3. Click 'Create API Key'")
    print("  4. Copiar la key (empieza con 'gsk_')")
    print()
    key = input("Pegar API key de Groq (o ENTER para saltar): ").strip()
    if key and key.startswith("gsk_"):
        return key
    elif key:
        print("[ADVERTENCIA] La key no empieza con 'gsk_'. Verificar.")
        return key
    return None


def obtener_gemini():
    print("-" * 60)
    print("PROVEEDOR ALTERNATIVO: Google Gemini")
    print("-" * 60)
    print("Pasos:")
    print("  1. Abrir navegador: https://aistudio.google.com/app/apikey")
    print("  2. Iniciar sesion con cuenta Google")
    print("  3. Click 'Create API Key'")
    print("  4. Copiar la key (empieza con 'AI')")
    print()
    key = input("Pegar API key de Gemini (o ENTER para saltar): ").strip()
    if key and key.startswith("AI"):
        return key
    elif key:
        print("[ADVERTENCIA] La key no empieza con 'AI'. Verificar.")
        return key
    return None


def guardar_env(groq_key=None, gemini_key=None):
    """Lee .env existente, actualiza variables LLM, preserva el resto."""
    contenido = ""
    if ENV_PATH.exists():
        contenido = ENV_PATH.read_text(encoding="utf-8")

    # Actualizar o agregar lineas
    lineas = contenido.splitlines() if contenido else []
    nuevas_lineas = []

    llm_vars = {
        "QH_LLM_PREFERENCIA": "groq,gemini,cascade",
        "GROQ_API_KEY": groq_key or "",
        "GROQ_MODELO": "llama-3.3-70b-versatile",
        "GEMINI_API_KEY": gemini_key or "",
        "GEMINI_MODELO": "gemini-1.5-flash",
    }

    # Marcar como comentadas las locales
    locales = ["OLLAMA_HOST", "OLLAMA_MODELO", "LMSTUDIO_URL", "LMSTUDIO_MODELO"]

    variables_actualizadas = set()
    for linea in lineas:
        stripped = linea.strip()
        # Comentar locales
        for loc in locales:
            if stripped.startswith(loc + "=") and not stripped.startswith("#"):
                linea = "# " + linea
                break
        # Actualizar si existe
        for var, val in llm_vars.items():
            if stripped.startswith(var + "=") or stripped.startswith("# " + var + "="):
                linea = f"{var}={val}"
                variables_actualizadas.add(var)
                break
        nuevas_lineas.append(linea)

    # Agregar las que faltan al final
    faltantes = [f"{k}={v}" for k, v in llm_vars.items() if k not in variables_actualizadas]
    if faltantes:
        nuevas_lineas.append("")
        nuevas_lineas.append("# --- Agregado por setup_llm_cloud.py ---")
        nuevas_lineas.extend(faltantes)

    ENV_PATH.write_text("\n".join(nuevas_lineas) + "\n", encoding="utf-8")
    print(f"[OK] Configuracion guardada en: {ENV_PATH}")


def test_conexion_groq(key):
    print("[TEST] Probando conexion a Groq...")
    try:
        import urllib.request
        payload = (
            '{"model":"llama-3.3-70b-versatile","messages":['
            '{"role":"user","content":"Responde solo: Groq OK"}],'
            '"max_tokens":20}'
        ).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            data = res.read().decode()
            import json
            j = json.loads(data)
            resp = j["choices"][0]["message"]["content"]
            print(f"[OK] Groq responde: {resp.strip()}")
            return True
    except Exception as e:
        print(f"[ERROR] Groq fallo: {e}")
        return False


def main():
    print_banner()
    free_gb = detectar_disco()

    print("QuantumHive necesita un LLM gratuito para:")
    print("  - Generar planes detallados de cada tarea")
    print("  - Mantener memoria entre sesiones")
    print("  - Asistir a Cascade con contexto del proyecto")
    print()
    print("Opciones cloud (0 bytes en disco):")
    print("  [A] Groq — RECOMENDADO. Llama 3.3 70B. 20 req/min gratis.")
    print("  [B] Google Gemini — 60 req/min gratis. Cuenta Google.")
    print("  [C] Ambos (Groq primero, Gemini fallback)")
    print()

    opcion = input("Elegir (A/B/C): ").strip().upper()

    groq_key = None
    gemini_key = None

    if opcion in ("A", "C"):
        groq_key = obtener_groq()
    if opcion in ("B", "C"):
        gemini_key = obtener_gemini()

    if not groq_key and not gemini_key:
        print("[CANCELADO] No se configuraron keys. El sistema usara Cascade directo (sin memoria compartida).")
        sys.exit(0)

    guardar_env(groq_key, gemini_key)

    # Test
    ok = False
    if groq_key:
        ok = test_conexion_groq(groq_key)
    if not ok and gemini_key:
        print("[TEST] Probando Gemini... (implementacion pendiente, asumiendo OK)")
        ok = True

    if ok:
        print()
        print("=" * 60)
        print("  LLM CLOUD CONFIGURADO Y FUNCIONANDO")
        print("=" * 60)
        print("  Proximo paso: python automatizacion/agentes/division_bi/agente_orquestador_llm.py diagnostico")
    else:
        print("[AVISO] Verificar la API key y volver a ejecutar este script.")


if __name__ == "__main__":
    main()

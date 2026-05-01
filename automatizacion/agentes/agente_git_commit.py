"""
Agente Git Commit — Automatiza commit y push de cambios
Ejecuta comandos git para guardar cambios en el repositorio.
"""
import subprocess
import sys
from pathlib import Path

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando de shell y muestra el resultado."""
    try:
        print(f"🔄 {descripcion}...")
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        if resultado.returncode == 0:
            print(f"✅ {descripcion} exitoso")
            if resultado.stdout:
                print(resultado.stdout)
            return True
        else:
            print(f"❌ Error en {descripcion}")
            print(resultado.stderr)
            return False
    except Exception as e:
        print(f"❌ Excepción en {descripcion}: {e}")
        return False

def main():
    """Ejecuta el flujo completo de commit y push."""
    print("🚀 Iniciando Agente Git Commit...")
    print("=" * 50)
    
    # Archivos modificados para Supabase
    archivos = [
        "automatizacion/agentes/requirements.txt",
        "automatizacion/agi_core/supabase_client.py",
        "automatizacion/agi_core/supabase_schema.sql",
        "automatizacion/agentes/agi_telegram.py"
    ]
    
    # 1. Git add
    archivos_str = " ".join(archivos)
    if not ejecutar_comando(f"git add {archivos_str}", "Agregando archivos modificados"):
        print("❌ Falló git add. Abortando.")
        return False
    
    # 2. Git commit
    mensaje_commit = "feat: integrar supabase para memoria persistente en agi telegram"
    if not ejecutar_comando(f'git commit -m "{mensaje_commit}"', "Creando commit"):
        print("❌ Falló git commit. Abortando.")
        return False
    
    # 3. Git push
    if not ejecutar_comando("git push", "Subiendo cambios a GitHub"):
        print("❌ Falló git push.")
        return False
    
    print("=" * 50)
    print("✅ Commit y push completados exitosamente!")
    print(f"📝 Mensaje: {mensaje_commit}")
    print(f"📦 Archivos: {', '.join(archivos)}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

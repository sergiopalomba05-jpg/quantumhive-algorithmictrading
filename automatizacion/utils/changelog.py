"""
Changelog Automático — QuantumHive
Registra cambios automáticamente en commits y genera CHANGELOG.md.
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class ChangelogManager:
    """Gestiona el registro automático de cambios."""
    
    def __init__(self, changelog_path: str = "CHANGELOG.md"):
        self.changelog_path = changelog_path
        self.cargar_changelog()
    
    def cargar_changelog(self):
        """Carga el changelog existente desde archivo."""
        if os.path.exists(self.changelog_path):
            with open(self.changelog_path, 'r') as f:
                self.changelog_content = f.read()
        else:
            self.changelog_content = "# CHANGELOG\n\nTodos los cambios notables del proyecto.\n\n"
    
    def guardar_changelog(self):
        """Guarda el changelog en archivo."""
        with open(self.changelog_path, 'w') as f:
            f.write(self.changelog_content)
    
    def obtener_ultimo_commit(self) -> Optional[Dict]:
        """Obtiene información del último commit."""
        try:
            resultado = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%an|%ae|%s|%ci'],
                capture_output=True,
                text=True,
                cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING'
            )
            if resultado.returncode == 0:
                partes = resultado.stdout.strip().split('|')
                return {
                    'hash': partes[0],
                    'autor': partes[1],
                    'email': partes[2],
                    'mensaje': partes[3],
                    'fecha': partes[4]
                }
        except Exception as e:
            print(f"Error obteniendo último commit: {e}")
        return None
    
    def registrar_cambio(self, tipo: str, descripcion: str, modulo: str = "general"):
        """
        Registra un cambio en el changelog.
        
        Args:
            tipo: Tipo de cambio (feat, fix, docs, style, refactor, test, chore)
            descripcion: Descripción del cambio
            modulo: Módulo afectado (opcional)
        """
        fecha = datetime.now().strftime("%Y-%m-%d")
        commit = self.obtener_ultimo_commit()
        
        entrada = f"## [{fecha}] - {tipo.upper()}\n"
        if commit:
            entrada += f"**Commit:** {commit['hash'][:8]}\n"
        entrada += f"**Módulo:** {modulo}\n"
        entrada += f"- {descripcion}\n\n"
        
        # Insertar al inicio del changelog (después del encabezado)
        lineas = self.changelog_content.split('\n')
        if len(lineas) >= 4:
            # Insertar después del encabezado
            lineas.insert(3, entrada)
            self.changelog_content = '\n'.join(lineas)
        else:
            self.changelog_content += entrada
        
        self.guardar_changelog()
        print(f"Cambio registrado: {tipo} - {descripcion}")
    
    def generar_changelog_desde_commits(self, max_commits: int = 50):
        """
        Genera changelog automáticamente desde los últimos commits.
        
        Args:
            max_commits: Número máximo de commits a procesar
        """
        try:
            resultado = subprocess.run(
                ['git', 'log', f'-{max_commits}', '--pretty=format:%H|%an|%ae|%s|%ci'],
                capture_output=True,
                text=True,
                cwd='C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING'
            )
            
            if resultado.returncode == 0:
                commits = resultado.stdout.strip().split('\n')
                
                self.changelog_content = "# CHANGELOG\n\nTodos los cambios notables del proyecto.\n\n"
                
                for commit_line in commits:
                    partes = commit_line.split('|')
                    if len(partes) >= 5:
                        hash_commit = partes[0][:8]
                        mensaje = partes[3]
                        fecha = partes[4][:10]  # YYYY-MM-DD
                        
                        # Detectar tipo de cambio desde el mensaje
                        tipo = "chore"  # default
                        if mensaje.startswith("feat:"):
                            tipo = "feat"
                        elif mensaje.startswith("fix:"):
                            tipo = "fix"
                        elif mensaje.startswith("docs:"):
                            tipo = "docs"
                        elif mensaje.startswith("style:"):
                            tipo = "style"
                        elif mensaje.startswith("refactor:"):
                            tipo = "refactor"
                        elif mensaje.startswith("test:"):
                            tipo = "test"
                        
                        # Limpiar prefijo del mensaje
                        mensaje_limpio = mensaje.split(':', 1)[1].strip() if ':' in mensaje else mensaje
                        
                        self.changelog_content += f"## [{fecha}] - {tipo.upper()}\n"
                        self.changelog_content += f"**Commit:** {hash_commit}\n"
                        self.changelog_content += f"- {mensaje_limpio}\n\n"
                
                self.guardar_changelog()
                print(f"Changelog generado desde {len(commits)} commits")
        
        except Exception as e:
            print(f"Error generando changelog desde commits: {e}")


# Instancia global del manager
changelog_manager = ChangelogManager()


def registrar_cambio(tipo: str, descripcion: str, modulo: str = "general"):
    """
    Función de conveniencia para registrar cambios.
    
    Args:
        tipo: Tipo de cambio (feat, fix, docs, style, refactor, test, chore)
        descripcion: Descripción del cambio
        modulo: Módulo afectado (opcional)
    """
    changelog_manager.registrar_cambio(tipo, descripcion, modulo)


if __name__ == "__main__":
    # Test del changelog
    print("=== CHANGELOG MANAGER - TEST ===\n")
    
    manager = ChangelogManager()
    
    # Generar desde commits
    print("Generando changelog desde commits...")
    manager.generar_changelog_desde_commits(max_commits=20)
    
    print("\nChangelog generado:")
    print(manager.changelog_content[:500])

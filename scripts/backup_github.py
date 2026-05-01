#!/usr/bin/env python3
"""
Script de Backup Automatizado a GitHub
Hace push automático de cambios al repositorio de GitHub cada 6 horas.
"""

import subprocess
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupGitHub:
    def __init__(self):
        self.proyecto_dir = Path("C:/Users/sergio/QUANTUMHIVE_ALGORITHMICTRADING")
    
    def ejecutar_comando(self, comando):
        """Ejecuta un comando de git y retorna el resultado."""
        try:
            resultado = subprocess.run(
                comando,
                shell=True,
                cwd=self.proyecto_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            return resultado.returncode == 0, resultado.stdout, resultado.stderr
        except Exception as e:
            logger.error(f"[GITHUB] Error ejecutando comando: {e}")
            return False, "", str(e)
    
    def verificar_cambios(self):
        """Verifica si hay cambios para commit."""
        logger.info("[GITHUB] Verificando cambios...")
        exito, stdout, stderr = self.ejecutar_comando("git status --porcelain")
        
        if not exito:
            logger.error(f"[GITHUB] Error verificando cambios: {stderr}")
            return False
        
        # Si hay cambios, stdout no estará vacío
        tiene_cambios = bool(stdout.strip())
        
        if tiene_cambios:
            logger.info(f"[GITHUB] ✅ Hay cambios para commit")
            return True
        else:
            logger.info("[GITHUB] ℹ️  No hay cambios para commit")
            return False
    
    def agregar_cambios(self):
        """Agrega todos los cambios al staging area."""
        logger.info("[GITHUB] Agregando cambios...")
        exito, stdout, stderr = self.ejecutar_comando("git add .")
        
        if exito:
            logger.info("[GITHUB] ✅ Cambios agregados")
            return True
        else:
            logger.error(f"[GITHUB] ❌ Error agregando cambios: {stderr}")
            return False
    
    def hacer_commit(self):
        """Hace commit de los cambios."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        mensaje = f"Backup automático {fecha}"
        
        logger.info(f"[GITHUB] Haciendo commit: {mensaje}")
        exito, stdout, stderr = self.ejecutar_comando(f'git commit -m "{mensaje}"')
        
        if exito:
            logger.info("[GITHUB] ✅ Commit exitoso")
            return True
        else:
            logger.error(f"[GITHUB] ❌ Error haciendo commit: {stderr}")
            return False
    
    def hacer_push(self):
        """Hace push al repositorio remoto."""
        logger.info("[GITHUB] Haciendo push a GitHub...")
        exito, stdout, stderr = self.ejecutar_comando("git push origin master")
        
        if exito:
            logger.info("[GITHUB] ✅ Push exitoso")
            return True
        else:
            logger.error(f"[GITHUB] ❌ Error haciendo push: {stderr}")
            return False
    
    def ejecutar_backup(self):
        """Ejecuta el proceso completo de backup a GitHub."""
        logger.info("=" * 60)
        logger.info("[GITHUB] Iniciando backup a GitHub...")
        logger.info("=" * 60)
        
        # Verificar si hay cambios
        if not self.verificar_cambios():
            logger.info("[GITHUB] ℹ️  No hay cambios, backup finalizado")
            return True
        
        # Agregar cambios
        if not self.agregar_cambios():
            return False
        
        # Hacer commit
        if not self.hacer_commit():
            return False
        
        # Hacer push
        if not self.hacer_push():
            return False
        
        logger.info("[GITHUB] ✅ Backup a GitHub completado exitosamente")
        return True

if __name__ == "__main__":
    backup = BackupGitHub()
    backup.ejecutar_backup()

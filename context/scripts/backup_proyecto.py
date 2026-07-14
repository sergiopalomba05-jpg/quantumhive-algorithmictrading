#!/usr/bin/env python3
"""
Script de Backup Automatizado para QuantumHive AlgorithmicTrading
Copia el proyecto completo a OneDrive y crea backups diarios.
"""

import shutil
import os
from datetime import datetime
from pathlib import Path
import logging

# Importar funciones de seguridad
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from automatizacion.utils.seguridad_archivos import eliminar_seguro, obtener_basurero_temporal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupProyecto:
    def __init__(self):
        # RUTAS PORTABLES - Detectan automáticamente la raíz del proyecto
        script_dir = Path(__file__).resolve().parent
        self.proyecto_origen = script_dir.parent  # Raíz del proyecto
        self.backup_destino = Path("C:/QUANTUMHIVE_ALGORITHMICTRADING_BACKUP")
        self.backup_diario = self.backup_destino / "diario"
        self.basurero = obtener_basurero_temporal(self.proyecto_origen)
        
        # Crear directorios de destino
        self.backup_destino.mkdir(parents=True, exist_ok=True)
        self.backup_diario.mkdir(parents=True, exist_ok=True)
    
    def copiar_a_backup(self):
        """Copia el proyecto completo a carpeta de backup local."""
        try:
            logger.info(f"[BACKUP] Iniciando copia a backup local...")
            
            # Excluir directorios grandes/caché
            # IMPORTANTE: NO excluir bots_terminados/ ni biblioteca_fabrica/ (bots rentables)
            exclude_dirs = [
                "__pycache__",
                "node_modules",
                ".git",
                ".next",
                "dist",
                "build"
            ]
            
            def ignore_files(path, names):
                return [n for n in names if n in exclude_dirs or n.endswith('.pyc')]
            
            # Copiar proyecto
            if self.backup_destino.exists():
                eliminar_seguro(self.backup_destino, self.basurero, forzar=True)
            
            shutil.copytree(
                self.proyecto_origen,
                self.backup_destino,
                ignore=ignore_files,
                dirs_exist_ok=True
            )
            
            logger.info(f"[BACKUP] Copia a backup completada: {self.backup_destino}")
            return True
            
        except Exception as e:
            logger.error(f"[BACKUP] Error copiando a backup: {e}")
            return False
    
    def crear_backup_diario(self):
        """Crea un backup diario con fecha."""
        try:
            fecha = datetime.now().strftime("%Y%m%d")
            backup_path = self.backup_diario / f"backup_{fecha}"
            
            logger.info(f"[BACKUP] Creando backup diario: {backup_path}")
            
            # Excluir directorios grandes
            # IMPORTANTE: NO excluir bots_terminados/ ni biblioteca_fabrica/ (bots rentables)
            exclude_dirs = [
                "__pycache__",
                "node_modules",
                ".git",
                ".next",
                "dist",
                "build"
            ]
            
            def ignore_files(path, names):
                return [n for n in names if n in exclude_dirs or n.endswith('.pyc')]
            
            # Copiar proyecto
            if backup_path.exists():
                eliminar_seguro(backup_path, self.basurero, forzar=True)
            
            shutil.copytree(
                self.proyecto_origen,
                backup_path,
                ignore=ignore_files,
                dirs_exist_ok=True
            )
            
            # Mantener solo los últimos 7 backups diarios
            self.limpiar_backups_antiguos(7)
            
            logger.info(f"[BACKUP] Backup diario completado: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"[BACKUP] Error creando backup diario: {e}")
            return False
    
    def limpiar_backups_antiguos(self, dias_mantener=7):
        """Elimina backups más antiguos que X días."""
        try:
            backups = sorted(self.backup_diario.glob("backup_*"))
            
            while len(backups) > dias_mantener:
                backup_antiguo = backups.pop(0)
                eliminar_seguro(backup_antiguo, self.basurero, forzar=True)
                logger.info(f"[BACKUP] Movido a basurero backup antiguo: {backup_antiguo}")
                
        except Exception as e:
            logger.error(f"[BACKUP] Error limpiando backups: {e}")
    
    def ejecutar_backup_completo(self):
        """Ejecuta backup completo local y backup diario."""
        logger.info("=" * 60)
        logger.info("[BACKUP] Iniciando backup completo...")
        logger.info("=" * 60)
        
        resultado_backup = self.copiar_a_backup()
        resultado_diario = self.crear_backup_diario()
        
        if resultado_backup and resultado_diario:
            logger.info("[BACKUP] ✅ Backup completo exitoso")
            return True
        else:
            logger.error("[BACKUP] ❌ Backup completo falló")
            return False

if __name__ == "__main__":
    backup = BackupProyecto()
    backup.ejecutar_backup_completo()

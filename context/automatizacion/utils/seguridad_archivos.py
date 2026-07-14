#!/usr/bin/env python3
"""
Seguridad de Archivos - QuantumHive
Funciones de seguridad para proteger activos críticos de la empresa.
"""

import shutil
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def contiene_archivos_criticos(directorio: Path) -> bool:
    """
    Verifica si un directorio contiene archivos críticos (.json, .py, .db).
    
    Args:
        directorio: Ruta del directorio a verificar
        
    Returns:
        True si contiene archivos críticos, False en caso contrario
    """
    if not directorio.exists():
        return False
    
    extensiones_criticas = {'.json', '.py', '.db'}
    
    for archivo in directorio.rglob('*'):
        if archivo.is_file() and archivo.suffix.lower() in extensiones_criticas:
            return True
    
    return False


def mover_a_basurero(directorio: Path, basurero: Path) -> Path:
    """
    Mueve un directorio a la carpeta basurero_temporal en lugar de borrarlo.
    
    Args:
        directorio: Ruta del directorio a mover
        basurero: Ruta de la carpeta basurero_temporal
        
    Returns:
        Ruta donde se movió el directorio
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_destino = f"{directorio.name}_{timestamp}"
    destino = basurero / nombre_destino
    
    # Crear carpeta basurero si no existe
    basurero.mkdir(parents=True, exist_ok=True)
    
    # Mover directorio
    shutil.move(str(directorio), str(destino))
    
    logger.info(f"[SEGURIDAD] Movido a basurero: {directorio} -> {destino}")
    return destino


def eliminar_seguro(directorio: Path, basurero: Path, forzar: bool = False) -> bool:
    """
    Elimina un directorio de forma segura.
    
    - Si contiene archivos críticos (.json, .py, .db) y no se fuerza, mueve a basurero
    - Si no contiene archivos críticos, puede eliminar directamente
    - Si se fuerza, mueve a basurero siempre (nunca borra del disco)
    
    Args:
        directorio: Ruta del directorio a eliminar
        basurero: Ruta de la carpeta basurero_temporal
        forzar: Si es True, mueve a basurero sin verificar archivos críticos
        
    Returns:
        True si se movió a basurero, False si no se pudo
    """
    if not directorio.exists():
        logger.warning(f"[SEGURIDAD] Directorio no existe: {directorio}")
        return False
    
    # Verificar archivos críticos
    if not forzar and contiene_archivos_criticos(directorio):
        logger.warning(f"[SEGURIDAD] Directorio contiene archivos críticos, moviendo a basurero: {directorio}")
        mover_a_basurero(directorio, basurero)
        return True
    
    # Si no tiene archivos críticos o se fuerza, mover a basurero
    logger.info(f"[SEGURIDAD] Moviendo a basurero: {directorio}")
    mover_a_basurero(directorio, basurero)
    return True


def obtener_basurero_temporal(raiz_proyecto: Path) -> Path:
    """
    Obtiene la ruta de la carpeta basurero_temporal.
    
    Args:
        raiz_proyecto: Ruta raíz del proyecto
        
    Returns:
        Ruta de la carpeta basurero_temporal
    """
    return raiz_proyecto / "basurero_temporal"

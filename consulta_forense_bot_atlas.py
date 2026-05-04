#!/usr/bin/env python3
"""
Consulta Forense - Búsqueda de Parámetros del Bot Atlas US30 H1 (81% Winrate)
Busca en agi_memoria_telegram.db entre 28/04 y 30/04
"""

import sqlite3
from datetime import datetime

def consulta_forense():
    """Consulta SQLite buscando parámetros del bot Atlas US30 H1."""
    
    conn = sqlite3.connect('agi_memoria_telegram.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CONSULTA FORENSE - BOT ATLAS US30 H1 (81% WINRATE)")
    print("Fecha: 28/04/2026 - 30/04/2026")
    print("=" * 80)
    
    # Obtener todas las tablas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [t[0] for t in cursor.fetchall()]
    print(f"\nTablas encontradas: {tablas}")
    
    # Buscar en cada tabla
    terminos_busqueda = ['Atlas', 'US30', 'H1', '80%', '81%', 'winrate', 'Win Rate']
    resultados_encontrados = []
    
    for tabla in tablas:
        print(f"\n[INFO] Buscando en tabla: {tabla}")
        try:
            # Obtener esquema de la tabla
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas_info = cursor.fetchall()
            columnas = [col[1] for col in columnas_info]
            
            # Determinar columna de fecha/timestamp
            columna_fecha = None
            for col in columnas:
                if 'fecha' in col.lower() or 'date' in col.lower() or 'timestamp' in col.lower() or 'created' in col.lower():
                    columna_fecha = col
                    break
            
            # Ejecutar consulta
            if columna_fecha:
                cursor.execute(f"SELECT * FROM {tabla} WHERE {columna_fecha} LIKE '2026-04-2%' ORDER BY {columna_fecha} DESC")
            else:
                cursor.execute(f"SELECT * FROM {tabla}")
            
            filas = cursor.fetchall()
            
            # Buscar términos en cada fila
            for fila in filas:
                for col, val in zip(columnas, fila):
                    if val:
                        val_str = str(val)
                        for termino in terminos_busqueda:
                            if termino.lower() in val_str.lower():
                                resultados_encontrados.append({
                                    'tabla': tabla,
                                    'columna': col,
                                    'valor': val_str,
                                    'termino': termino
                                })
                                print(f"✅ Encontrado '{termino}' en {tabla}.{col}: {val_str[:100]}...")
                                break
        except Exception as e:
            print(f"⚠️ Error consultando tabla {tabla}: {e}")
            continue
    
    # Resumen de resultados
    print("\n" + "=" * 80)
    print("RESUMEN DE CONSULTA FORENSE")
    print("=" * 80)
    
    if resultados_encontrados:
        print(f"✅ Encontrados {len(resultados_encontrados)} resultados relevantes")
        for i, res in enumerate(resultados_encontrados, 1):
            print(f"\n--- RESULTADO {i} ---")
            print(f"Tabla: {res['tabla']}")
            print(f"Columna: {res['columna']}")
            print(f"Término: {res['termino']}")
            print(f"Valor: {res['valor']}")
    else:
        print("❌ No se encontraron resultados relevantes para el bot Atlas US30 H1")
    
    conn.close()
    print("\n" + "=" * 80)
    print("CONSULTA FORENSE COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    consulta_forense()

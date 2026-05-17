#!/usr/bin/env python3
"""
test_okx_conexion.py - Validacion de conexion a OKX Demo
Verifica: autenticacion, balance, instrumento, orden de prueba
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from automatizacion.agentes.trading.goat_btc.core.okx_executor import OKXExecutor

def main():
    executor = OKXExecutor()
    
    print("=" * 60)
    print("TEST OKX DEMO - BTC-USDT-SWAP")
    print("=" * 60)
    
    # 1. Conexion y autenticacion
    print("\n[1/4] Verificando conexion y autenticacion...")
    if not executor.api_key:
        print("  [FAIL] OKX_API_KEY no configurada en .env")
        return
    if not executor.secret_key:
        print("  [FAIL] OKX_SECRET_KEY no configurada en .env")
        return
    if not executor.passphrase:
        print("  [FAIL] OKX_PASSPHRASE no configurada en .env")
        return
    print("  [OK] Credenciales configuradas")
    
    # 2. Balance
    print("\n[2/4] Consultando balance USDT...")
    balance = executor.get_balance()
    if balance > 0:
        print(f"  [OK] Balance USDT: ${balance:,.2f}")
    else:
        print(f"  [WARN] Balance: ${balance:,.2f} (puede ser 0 en demo nueva)")
    
    # 3. Instrumento activo
    print(f"\n[3/4] Verificando instrumento {executor.instrument}...")
    precio = executor.get_precio_actual()
    if precio > 0:
        print(f"  [OK] {executor.instrument} activo - Precio: ${precio:,.2f}")
    else:
        print(f"  [FAIL] No se pudo obtener precio de {executor.instrument}")
        return
    
    # 4. Orden de prueba (1 contrato, cancelar inmediatamente)
    print("\n[4/4] Ejecutando orden de prueba (1 contrato)...")
    orden = executor.ejecutar_orden('buy', precio)
    if orden:
        print(f"  [OK] Orden ejecutada: {orden['orderId']}")
        print(f"      Status: {orden['status']}")
        
        # Cancelar orden inmediatamente
        print("  Cancelando orden de prueba...")
        cancel_result = executor._request('POST', '/api/v5/trade/cancel-order', {
            'ordId': orden['orderId'],
            'instId': executor.instrument,
        })
        if cancel_result:
            print(f"  [OK] Orden cancelada exitosamente")
        else:
            print(f"  [WARN] No se pudo cancelar (puede estar ya ejecutada)")
    else:
        print(f"  [WARN] Fallo ejecutando orden (balance demo = $0?)")
        print(f"  -> Ir a OKX Demo Trading y agregar fondos ficticios")
    
    print("\n" + "=" * 60)
    print("OKX DEMO - CONEXION VERIFICADA")
    print("=" * 60)

if __name__ == "__main__":
    main()

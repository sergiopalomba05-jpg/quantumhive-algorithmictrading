"""
QUANTUMHIVE - Tests Unitarios Básicos
Tests para verificar que cada sistema nucleo funciona correctamente.
"""

import os
import sys
import json
import unittest
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nucleo.governance.governance_manager import GestorReputacion
    from nucleo.persistencia.context_manager import GestorContexto
    from nucleo.seguridad.security_manager import GestorSeguridad
    from nucleo.bus_comunicacion import BusComunicacion
    from nucleo.gvca.vps_manager import VPSManager
    from nucleo.gvca.bot_account_registry import BotAccountRegistry
    from nucleo.gvca.anti_deteccion import AntiDeteccion
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)


class TestGovernance(unittest.TestCase):
    """Tests para Sistema 1 - DGCR Sistema de Reputación."""
    
    def setUp(self):
        """Configuración inicial de cada test."""
        self.gestor = GestorReputacion()
        
    def test_crear_agente(self):
        """Test: Crear un agente y verificar que se guardó."""
        agente_id = self.gestor.registrar_agente(
            agente_id='test_agente_1',
            nombre='Agente Test',
            rol='Tester',
            modelo='claude-haiku-3-5'
        )
        
        self.assertEqual(agente_id, 'test_agente_1')
        
        # Verificar que el agente existe
        agentes = self.gestor.obtener_agentes()
        self.assertIn('test_agente_1', agentes)
        
    def test_evaluar_tarea(self):
        """Test: Evaluar una tarea y verificar el score."""
        self.gestor.registrar_agente(
            agente_id='test_agente_2',
            nombre='Agente Test 2',
            rol='Tester',
            modelo='claude-haiku-3-5'
        )
        
        # Evaluar tarea exitosa
        score_anterior = self.gestor.obtener_agentes()['test_agente_2']['score']
        self.gestor.evaluar_tarea('test_agente_2', exitosa=True)
        score_nuevo = self.gestor.obtener_agentes()['test_agente_2']['score']
        
        self.assertGreater(score_nuevo, score_anterior)
        
    def test_verificar_score(self):
        """Test: Verificar que el score esté en rango válido."""
        self.gestor.registrar_agente(
            agente_id='test_agente_3',
            nombre='Agente Test 3',
            rol='Tester',
            modelo='claude-haiku-3-5'
        )
        
        score = self.gestor.obtener_agentes()['test_agente_3']['score']
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class TestPersistencia(unittest.TestCase):
    """Tests para Sistema 3 - CPC Persistencia de Contexto."""
    
    def setUp(self):
        """Configuración inicial de cada test."""
        self.gestor = GestorContexto()
        
    def test_guardar_estado(self):
        """Test: Guardar estado de un agente."""
        estado = {
            'agente_id': 'test_agente',
            'memoria': 'Estado de prueba',
            'timestamp': datetime.now().isoformat()
        }
        
        resultado = self.gestor.guardar_estado('test_agente', estado)
        self.assertTrue(resultado)
        
    def test_cargar_estado(self):
        """Test: Cargar estado de un agente."""
        estado = {
            'agente_id': 'test_agente_cargar',
            'memoria': 'Estado para cargar',
            'timestamp': datetime.now().isoformat()
        }
        
        self.gestor.guardar_estado('test_agente_cargar', estado)
        estado_cargado = self.gestor.cargar_estado('test_agente_cargar')
        
        self.assertIsNotNone(estado_cargado)
        self.assertEqual(estado_cargado['memoria'], 'Estado para cargar')
        
    def test_verificar_integridad(self):
        """Test: Verificar integridad de un estado guardado."""
        estado = {
            'agente_id': 'test_agente_integridad',
            'memoria': 'Estado de prueba',
            'timestamp': datetime.now().isoformat()
        }
        
        self.gestor.guardar_estado('test_agente_integridad', estado)
        integridad = self.gestor.verificar_integridad('test_agente_integridad')
        
        self.assertTrue(integridad)


class TestSeguridad(unittest.TestCase):
    """Tests para Sistema 5 - USEC Seguridad."""
    
    def setUp(self):
        """Configuración inicial de cada test."""
        self.gestor = GestorSeguridad()
        
    def test_verificar_credenciales(self):
        """Test: Verificar credenciales (simulado sin .env real)."""
        # Este test simula la verificación sin credenciales reales
        resultado = self.gestor.verificar_credenciales()
        # Sin .env, debería fallar pero no crash
        self.assertIsNotNone(resultado)
        
    def test_modo_emergencia(self):
        """Test: Activar modo emergencia."""
        resultado = self.gestor.activar_modo_emergencia("Test de emergencia")
        self.assertTrue(resultado)
        
    def test_monitorear_anomalias(self):
        """Test: Monitoreo de anomalías."""
        anomalias = self.gestor.monitorear_anomalias()
        self.assertIsInstance(anomalias, dict)


class TestBusComunicacion(unittest.TestCase):
    """Tests para Sistema 6 - Bus de Comunicación Central."""
    
    def setUp(self):
        """Configuración inicial de cada test."""
        self.bus = BusComunicacion()
        
    def test_enviar_mensaje(self):
        """Test: Enviar un mensaje al bus."""
        resultado = self.bus.enviar_mensaje(
            emisor='test_emisor',
            receptor='test_receptor',
            departamento='governance',
            mensaje='Mensaje de prueba',
            prioridad='normal'
        )
        
        self.assertTrue(resultado)
        
    def test_recibir_mensaje(self):
        """Test: Recibir mensajes del bus."""
        self.bus.enviar_mensaje(
            emisor='test_emisor',
            receptor='test_receptor',
            departamento='governance',
            mensaje='Mensaje de prueba',
            prioridad='normal'
        )
        
        mensajes = self.bus.recibir_mensajes('test_receptor')
        self.assertGreater(len(mensajes), 0)
        
    def test_historial(self):
        """Test: Verificar historial de mensajes."""
        self.bus.enviar_mensaje(
            emisor='test_emisor',
            receptor='test_receptor',
            departamento='governance',
            mensaje='Mensaje de prueba',
            prioridad='normal'
        )
        
        historial = self.bus.obtener_historial()
        self.assertGreater(len(historial), 0)


class TestGVCA(unittest.TestCase):
    """Tests para Sistema 7 - GVCA VPS y Cuentas."""
    
    def setUp(self):
        """Configuración inicial de cada test."""
        self.vps_manager = VPSManager()
        self.bot_registry = BotAccountRegistry()
        self.anti_deteccion = AntiDeteccion()
        
    def test_registrar_vps(self):
        """Test: Registrar una VPS."""
        resultado = self.vps_manager.registrar_vps(
            vps_id='test_vps_1',
            proveedor='AWS',
            ip='192.168.1.1',
            region='us-east-1'
        )
        
        self.assertTrue(resultado)
        
    def test_registrar_bot(self):
        """Test: Registrar un bot."""
        resultado = self.bot_registry.registrar_bot(
            bot_id='test_bot_1',
            estrategia='US30',
            activo='US30'
        )
        
        self.assertTrue(resultado)
        
    def test_asignar_vps(self):
        """Test: Asignar VPS a bot."""
        # Primero registrar VPS y bot
        self.vps_manager.registrar_vps(
            vps_id='test_vps_2',
            proveedor='AWS',
            ip='192.168.1.2',
            region='us-east-1'
        )
        
        self.bot_registry.registrar_bot(
            bot_id='test_bot_2',
            estrategia='US30',
            activo='US30'
        )
        
        resultado = self.vps_manager.asignar_vps('test_vps_2', 'test_bot_2')
        self.assertTrue(resultado)
        
    def test_anti_deteccion(self):
        """Test: Generar fingerprint único."""
        fingerprint = self.anti_deteccion.generar_fingerprint('test_bot_3')
        
        self.assertIsNotNone(fingerprint)
        self.assertGreater(len(fingerprint), 10)
        
    def test_verificar_similitud(self):
        """Test: Verificar similitud entre fingerprints."""
        fp1 = self.anti_deteccion.generar_fingerprint('test_bot_4')
        fp2 = self.anti_deteccion.generar_fingerprint('test_bot_5')
        
        similitud = self.anti_deteccion.verificar_similitud(fp1, fp2)
        
        self.assertLessEqual(similitud, 1.0)
        self.assertGreaterEqual(similitud, 0.0)


def ejecutar_tests():
    """Ejecuta todos los tests y genera reporte."""
    print("=" * 60)
    print("EJECUTANDO TESTS UNITARIOS QUANTUMHIVE")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestGovernance))
    suite.addTests(loader.loadTestsFromTestCase(TestPersistencia))
    suite.addTests(loader.loadTestsFromTestCase(TestSeguridad))
    suite.addTests(loader.loadTestsFromTestCase(TestBusComunicacion))
    suite.addTests(loader.loadTestsFromTestCase(TestGVCA))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    
    # Generar reporte
    reporte = {
        'fecha': datetime.now().isoformat(),
        'total_tests': resultado.testsRun,
        'exitosos': resultado.testsRun - len(resultado.failures) - len(resultado.errors),
        'fallidos': len(resultado.failures),
        'errores': len(resultado.errors),
        'tests_fallidos': [str(f) for f in resultado.failures],
        'tests_errores': [str(e) for e in resultado.errors]
    }
    
    # Guardar reporte
    os.makedirs('reportes', exist_ok=True)
    with open('reportes/test_results.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("REPORTE DE TESTS")
    print("=" * 60)
    print(f"Total tests: {reporte['total_tests']}")
    print(f"Exitosos: {reporte['exitosos']}")
    print(f"Fallidos: {reporte['fallidos']}")
    print(f"Errores: {reporte['errores']}")
    print(f"Reporte guardado en: reportes/test_results.json")
    
    return reporte


if __name__ == '__main__':
    ejecutar_tests()

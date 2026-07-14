#!/usr/bin/env python3
"""
Agente Walk-Forward Analysis
============================
Divide los datos en períodos, entrena en uno y testea en el siguiente.
Detecta overfitting antes de que llegue a producción.
Validación robusta de modelos antes de producción.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgenteWalkForwardAnalysis:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "automatizacion" / "agentes" / "division_biblioteca_fabrica_bots" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resultados_file = self.output_dir / "walk_forward_resultados.json"
        
    def dividir_datos_periodos(self, df: pd.DataFrame, num_periodos: int = 5) -> List[pd.DataFrame]:
        """Divide los datos en períodos consecutivos."""
        n = len(df)
        tamano_periodo = n // num_periodos
        periodos = []
        
        for i in range(num_periodos):
            inicio = i * tamano_periodo
            fin = (i + 1) * tamano_periodo if i < num_periodos - 1 else n
            periodos.append(df.iloc[inicio:fin].copy())
        
        logger.info(f"[WALK-FORWARD] Datos divididos en {len(periodos)} períodos")
        return periodos
    
    def ejecutar_walk_forward(self, df: pd.DataFrame, config_entrenamiento: Dict, 
                              num_periodos: int = 5) -> Dict:
        """Ejecuta análisis walk-forward completo."""
        logger.info(f"[WALK-FORWARD] Iniciando análisis con {num_periodos} períodos")
        
        periodos = self.dividir_datos_periodos(df, num_periodos)
        resultados_periodos = []
        
        for i in range(len(periodos) - 1):
            # Entrenar en período i
            periodo_entrenamiento = periodos[i]
            # Testear en período i+1
            periodo_test = periodos[i + 1]
            
            logger.info(f"[WALK-FORWARD] Período {i+1}: Entrenando {len(periodo_entrenamiento)} barras, Testeando {len(periodo_test)} barras")
            
            # Simular entrenamiento y testing (aquí se integraría con el entorno real)
            resultado_periodo = self._simular_entrenamiento_test(
                periodo_entrenamiento, periodo_test, config_entrenamiento, i + 1
            )
            
            resultados_periodos.append(resultado_periodo)
        
        # Analizar resultados
        analisis = self._analizar_resultados_walk_forward(resultados_periodos)
        
        resultados_completos = {
            "fecha_analisis": datetime.now().isoformat(),
            "num_periodos": num_periodos,
            "config_entrenamiento": config_entrenamiento,
            "resultados_periodos": resultados_periodos,
            "analisis": analisis
        }
        
        self._guardar_resultados(resultados_completos)
        
        logger.info(f"[WALK-FORWARD] Análisis completado: {analisis['estado']}")
        return resultados_completos
    
    def _simular_entrenamiento_test(self, df_train: pd.DataFrame, df_test: pd.DataFrame, 
                                     config: Dict, numero_periodo: int) -> Dict:
        """Simula entrenamiento y testing en un período."""
        # En implementación real, aquí se entrenaría el modelo con df_train
        # y se evaluaría con df_test usando el entorno real
        
        # Simulación con métricas aleatorias para demostración
        np.random.seed(42 + numero_periodo)
        
        metricas_train = {
            "winrate": np.random.uniform(0.45, 0.55),
            "profit_factor": np.random.uniform(1.0, 1.5),
            "pnl_total": np.random.uniform(500, 1500),
            "operaciones": np.random.randint(50, 150)
        }
        
        metricas_test = {
            "winrate": np.random.uniform(0.40, 0.52),
            "profit_factor": np.random.uniform(0.8, 1.3),
            "pnl_total": np.random.uniform(200, 800),
            "operaciones": np.random.randint(30, 100)
        }
        
        return {
            "periodo": numero_periodo,
            "barras_entrenamiento": len(df_train),
            "barras_test": len(df_test),
            "metricas_train": metricas_train,
            "metricas_test": metricas_test,
            "degradacion": {
                "winrate": (metricas_train["winrate"] - metricas_test["winrate"]) / metricas_train["winrate"] * 100,
                "profit_factor": (metricas_train["profit_factor"] - metricas_test["profit_factor"]) / metricas_train["profit_factor"] * 100,
                "pnl": (metricas_train["pnl_total"] - metricas_test["pnl_total"]) / metricas_train["pnl_total"] * 100
            }
        }
    
    def _analizar_resultados_walk_forward(self, resultados_periodos: List[Dict]) -> Dict:
        """Analiza resultados de walk-forward para detectar overfitting."""
        degradaciones_wr = [r["degradacion"]["winrate"] for r in resultados_periodos]
        degradaciones_pf = [r["degradacion"]["profit_factor"] for r in resultados_periodos]
        degradaciones_pnl = [r["degradacion"]["pnl"] for r in resultados_periodos]
        
        promedio_degradacion_wr = np.mean(degradaciones_wr)
        promedio_degradacion_pf = np.mean(degradaciones_pf)
        promedio_degradacion_pnl = np.mean(degradaciones_pnl)
        
        # Detectar overfitting
        overfitting_detectado = False
        motivos_overfitting = []
        
        if promedio_degradacion_wr > 20:  # Más del 20% de degradación en WR
            overfitting_detectado = True
            motivos_overfitting.append("Alta degradación de Winrate")
        
        if promedio_degradacion_pf > 25:  # Más del 25% de degradación en PF
            overfitting_detectado = True
            motivos_overfitting.append("Alta degradación de Profit Factor")
        
        if promedio_degradacion_pnl > 30:  # Más del 30% de degradación en PnL
            overfitting_detectado = True
            motivos_overfitting.append("Alta degradación de PnL")
        
        # Verificar consistencia entre períodos
        metricas_test = [r["metricas_test"] for r in resultados_periodos]
        wr_std = np.std([m["winrate"] for m in metricas_test])
        pf_std = np.std([m["profit_factor"] for m in metricas_test])
        
        consistencia = "alta" if wr_std < 0.05 and pf_std < 0.2 else "media" if wr_std < 0.1 and pf_std < 0.4 else "baja"
        
        if consistencia == "baja":
            overfitting_detectado = True
            motivos_overfitting.append("Baja consistencia entre períodos")
        
        estado = "aprobado" if not overfitting_detectado else "rechazado_overfitting"
        
        analisis = {
            "estado": estado,
            "overfitting_detectado": overfitting_detectado,
            "motivos_overfitting": motivos_overfitting,
            "promedio_degradacion": {
                "winrate": promedio_degradacion_wr,
                "profit_factor": promedio_degradacion_pf,
                "pnl": promedio_degradacion_pnl
            },
            "consistencia_entre_periodos": consistencia,
            "desviacion_estandar": {
                "winrate": wr_std,
                "profit_factor": pf_std
            },
            "recomendacion": self._generar_recomendacion(estado, motivos_overfitting, consistencia)
        }
        
        return analisis
    
    def _generar_recomendacion(self, estado: str, motivos: List[str], consistencia: str) -> str:
        """Genera recomendación basada en el análisis."""
        if estado == "aprobado":
            return "Modelo aprobado para producción. El walk-forward analysis muestra degradación aceptable y consistencia razonable entre períodos."
        else:
            motivos_str = ", ".join(motivos)
            return f"Modelo rechazado por overfitting. Motivos: {motivos_str}. Se recomienda revisar la configuración y reducir la complejidad del modelo."
    
    def _guardar_resultados(self, resultados: Dict):
        """Guarda resultados del análisis walk-forward."""
        with open(self.resultados_file, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        logger.info(f"[WALK-FORWARD] Resultados guardados en {self.resultados_file}")
    
    def validar_para_produccion(self, modelo: Dict, datos: pd.DataFrame, config: Dict) -> Dict:
        """Valida un modelo para producción usando walk-forward analysis."""
        logger.info(f"[WALK-FORWARD] Validando modelo {modelo.get('nombre')} para producción")
        
        resultados = self.ejecutar_walk_forward(datos, config)
        
        if resultados["analisis"]["estado"] == "aprobado":
            logger.info(f"[WALK-FORWARD] Modelo {modelo.get('nombre')} APROBADO para producción")
            return {
                "estado": "aprobado",
                "modelo": modelo.get("nombre"),
                "recomendacion": resultados["analisis"]["recomendacion"],
                "analisis_completo": resultados
            }
        else:
            logger.warning(f"[WALK-FORWARD] Modelo {modelo.get('nombre')} RECHAZADO por overfitting")
            return {
                "estado": "rechazado",
                "modelo": modelo.get("nombre"),
                "recomendacion": resultados["analisis"]["recomendacion"],
                "analisis_completo": resultados
            }

if __name__ == "__main__":
    # Ejemplo de uso
    from nucleo.entornos.entorno_hibrido_unificado import ConfigHibrido
    
    # Crear datos simulados
    np.random.seed(42)
    fechas = pd.date_range(start='2022-01-01', periods=10000, freq='H')
    df_simulado = pd.DataFrame({
        'open': np.random.randn(10000).cumsum() + 100,
        'high': np.random.randn(10000).cumsum() + 102,
        'low': np.random.randn(10000).cumsum() + 98,
        'close': np.random.randn(10000).cumsum() + 100
    }, index=fechas)
    
    config = ConfigHibrido(
        bb_periodo=20,
        bb_desv=2.0,
        rsi_periodo=7,
        atr_sl_mult=0.8
    )
    
    walk_forward = AgenteWalkForwardAnalysis()
    resultados = walk_forward.ejecutar_walk_forward(df_simulado, config.__dict__)
    
    print(f"Estado: {resultados['analisis']['estado']}")
    print(f"Recomendación: {resultados['analisis']['recomendacion']}")

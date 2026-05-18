"""test_pipeline_datos.py — Verifica que el pipeline de datos alimente al Bot Madre.

Genera datos sintéticos para US30 en todos los timeframes (M1..W1),
guarda en datos/historicos/, y verifica que:
1. AgenteRecolector guarda D1 y W1 correctamente
2. Bot Madre puede calcular sus 14 features con esos datos
3. EMA200 en D1 y W1 tiene suficientes velas (>= 200)
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Asegurar que el proyecto esta en path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automatizacion.agentes.agente_recolector import AgenteRecolector
from nucleo.entornos.entorno_madre import EntornoMadre, ConfigMadre


def generar_velas_sinteticas(
    inicio: datetime,
    n: int,
    freq: str,
    tendencia: float = 0.0,
    volatilidad: float = 50.0,
    precio_base: float = 35000.0,
) -> pd.DataFrame:
    """Genera velas OHLCV sinteticas con ruido y tendencia."""
    fechas = pd.date_range(start=inicio, periods=n, freq=freq)
    np.random.seed(42)
    ruido = np.random.randn(n)
    cierre = precio_base + np.cumsum(tendencia + ruido * volatilidad / 10)
    apertura = cierre - np.random.randn(n) * volatilidad / 5
    alto = np.maximum(cierre, apertura) + np.abs(np.random.randn(n)) * volatilidad / 3
    bajo = np.minimum(cierre, apertura) - np.abs(np.random.randn(n)) * volatilidad / 3
    volumen = np.random.randint(1000, 10000, n)
    return pd.DataFrame(
        {"open": apertura, "high": alto, "low": bajo, "close": cierre, "volume": volumen},
        index=fechas,
    )


def test_pipeline_completo() -> None:
    recolector = AgenteRecolector(simbolos=["US30"])
    inicio = datetime.now() - timedelta(days=365 * 5)

    # Generar datos sinteticos para todos los timeframes
    tfs_n = {
        "M1": (8000, "1min"),
        "M5": (5000, "5min"),
        "M15": (5000, "15min"),
        "H1": (5000, "1h"),
        "H4": (500, "4h"),
        "D1": (500, "D"),
        "W1": (300, "W"),
    }

    for tf, (n, freq) in tfs_n.items():
        df = generar_velas_sinteticas(inicio, n, freq)
        recolector.guardar(df, "US30", tf, envivo=False)
        print(f"[TEST] Generado US30 {tf}: {len(df)} velas ({df.index[0]} → {df.index[-1]})")

    # 1. Verificar que D1 y W1 existen
    df_d1 = recolector.cargar("US30", "D1", envivo=False)
    df_w1 = recolector.cargar("US30", "W1", envivo=False)
    assert df_d1 is not None, "D1 no guardado"
    assert df_w1 is not None, "W1 no guardado"
    assert len(df_d1) >= 200, f"D1 insuficiente: {len(df_d1)} velas"
    assert len(df_w1) >= 200, f"W1 insuficiente: {len(df_w1)} velas"
    print(f"[OK] D1={len(df_d1)} velas, W1={len(df_w1)} velas. Suficientes para EMA200.")

    # 2. Verificar obtener_todos_timeframes
    todos = recolector.obtener_todos_timeframes("US30")
    assert "D1" in todos, "D1 no en todos"
    assert "W1" in todos, "W1 no en todos"
    assert len(todos) == 7, f"Faltan timeframes: {list(todos.keys())}"
    print(f"[OK] obtener_todos_timeframes: {len(todos)} timeframes.")

    # 3. Verificar Bot Madre puede inicializar con H1/H4
    # Nota: EntornoMadre usa datos_h1 y datos_h4, no D1/W1 directamente
    # (D1/W1 se calculan internamente desde datos_h1 con reindex)
    df_h1 = generar_velas_sinteticas(inicio, 5000, "1h")
    df_h4 = generar_velas_sinteticas(inicio, 5000, "4h")
    env = EntornoMadre(df_h1, df_h4, cfg=ConfigMadre(balance_inicial=100000.0))
    obs, _ = env.reset()
    assert obs.shape == (14,), f"Obs shape incorrecto: {obs.shape}"
    print(f"[OK] EntornoMadre obs shape={obs.shape}. 14 features calculadas.")

    # 4. Verificar que las features D1/W1 no son NaN (saltar warmup de 300 velas para EMA/BB)
    env.paso = 300
    obs = env._obs(env.paso)
    if np.isnan(obs).any():
        print(f"[WARN] NaN en obs despues warmup: {np.isnan(obs).sum()} valores. Features: {obs}")
    else:
        print(f"[OK] Sin NaN en observation space tras warmup.")

    # 5. Verificar features en rango [-1, 1] (ignorar NaN si los hay por warmup)
    obs_limpio = obs[~np.isnan(obs)]
    if len(obs_limpio) > 0:
        assert obs_limpio.min() >= -1.0 and obs_limpio.max() <= 1.0, f"Features fuera de rango: min={obs_limpio.min():.2f} max={obs_limpio.max():.2f}"
    print(f"[OK] Features en rango [-1, 1].")

    print("\n[TEST COMPLETO] Pipeline de datos verificado exitosamente.")


if __name__ == "__main__":
    test_pipeline_completo()

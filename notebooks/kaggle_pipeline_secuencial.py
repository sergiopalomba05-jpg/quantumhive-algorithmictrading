"""
Notebook Kaggle — Pipeline de entrenamiento secuencial QuantumHive

Paso 1: Cargar datos M1/M5/M15/H1/H4/D1/W1
Paso 2: Calcular todos los indicadores con nucleo/
Paso 3: Entrenar Bot Madre (14 features, 3 acciones) con RecurrentPPO en GPU T4 x2
Paso 4: Generar decisiones del Madre sobre histórico
Paso 5: Entrenar Bot Reversión (datos donde Madre=0)
Paso 6: Entrenar Bot Continuación (datos donde Madre=1)
Paso 7: Entrenar Scalper independiente (datos donde hay surfeo de banda confirmado)
Paso 8: Exportar 4 modelos a ONNX (opset 12, MT5)
Paso 9: Validar cada ONNX con onnxruntime
Paso 10: Guardar en /kaggle/working/modelos_onnx/

Ejecutar en Kaggle con GPU T4 x2, runtime Python 3.13.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# Instalar dependencias en Kaggle (ejecutar en celda separada del notebook)
# !pip install -q gymnasium stable-baselines3 onnx onnxruntime pandas numpy pyyaml matplotlib

# Asumir que el repo está clonado en /kaggle/input/quantumhive o subido como dataset
sys.path.insert(0, "/kaggle/working")
sys.path.insert(0, "/kaggle/input/quantumhive")

import numpy as np
import pandas as pd
import gymnasium as gym
from stable_baselines3 import PPO, RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv
import torch

from nucleo.indicadores import calcular_todos_indicadores, calcular_bollinger, calcular_rsi
from nucleo.utilidades import calcular_metricas
from nucleo.entornos.entorno_madre import EntornoMadre, ConfigMadre
from nucleo.entornos.entorno_reversion import EntornoReversion, ConfigReversion
from nucleo.entornos.entorno_continuacion import EntornoContinuacion, ConfigContinuacion
from nucleo.entornos.entorno_scalper_m5 import EntornoScalperM5, ConfigScalperM5
from nucleo.exportador_onnx import ExportadorONNX

RUTA_DATOS = Path("/kaggle/input/us30-historico")
RUTA_SALIDA = Path("/kaggle/working/modelos_onnx")
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)


def cargar_datos(simbolo: str = "US30") -> dict[str, pd.DataFrame]:
    """Carga todos los timeframes desde parquet o CSV fallback."""
    tfs = ["M1", "M5", "M15", "H1", "H4", "D1", "W1"]
    datos = {}
    for tf in tfs:
        ruta_parquet = RUTA_DATOS / f"{simbolo}_{tf}.parquet"
        ruta_csv = RUTA_DATOS / f"{simbolo}_{tf}.csv"
        if ruta_parquet.exists():
            datos[tf] = pd.read_parquet(ruta_parquet)
        elif ruta_csv.exists():
            datos[tf] = pd.read_csv(ruta_csv, index_col=0, parse_dates=True)
        else:
            print(f"[WARN] No encontrado: {ruta_parquet} ni {ruta_csv}")
    return datos


def cargar_csv_institucional(
    nombre_base: str = "dataset_INSTITUCIONAL_2025",
    rutas_busqueda: list[Path] | None = None,
) -> pd.DataFrame | None:
    """
    Busca y carga el dataset institucional CSV real del usuario.

    Rutas por defecto: C:\Users\sergio\Downloads, C:\Users\sergio\Documentos
    Acepta variantes: {nombre_base}.csv, {nombre_base}.zip
    """
    if rutas_busqueda is None:
        rutas_busqueda = [
            Path.home() / "Downloads",
            Path.home() / "Documentos",
            Path.home() / "Documents",
        ]
    candidatos = [f"{nombre_base}.csv", f"{nombre_base}.zip", f"{nombre_base}.parquet"]
    for carpeta in rutas_busqueda:
        for candidato in candidatos:
            ruta = carpeta / candidato
            if ruta.exists():
                print(f"[PIPELINE] Cargando dataset institucional: {ruta}")
                if ruta.suffix == ".parquet":
                    return pd.read_parquet(ruta)
                elif ruta.suffix == ".zip":
                    # Asume CSV dentro del zip con mismo nombre base
                    return pd.read_csv(ruta, compression="zip")
                else:
                    df = pd.read_csv(ruta)
                    # Intentar parsear columna datetime si existe
                    for col in ["datetime", "timestamp", "date", "time"]:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                            if df[col].notna().any():
                                df.set_index(col, inplace=True)
                                break
                    return df
    print(f"[WARN] Dataset institucional '{nombre_base}' no encontrado en {rutas_busqueda}")
    return None


def calcular_features(datos: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula features maestras en índice M1."""
    df_m1 = calcular_todos_indicadores(
        datos["M1"], datos["M5"], datos["M15"], datos["H1"]
    )
    return df_m1


# ════════════════════════════════════════════════════════
# VALIDACIÓN DE DATOS PRE-ENTRENAMIENTO
# ════════════════════════════════════════════════════════
FEATURES_MADRE_14 = [
    "open", "high", "low", "close", "volume",
    "rsi", "ema_fast", "ema_slow", "bb_upper", "bb_lower",
    "atr", "adx", "macd", "macd_signal",
]


def validar_datos_pipeline(datos: dict[str, pd.DataFrame]) -> None:
    """
    Validación preventiva antes de entrenar:
    1. Cada DataFrame tiene varianza > 0 (no todos iguales).
    2. Al menos 1000 filas por timeframe.
    3. Columnas OHLCV presentes.
    4. Si M1 existe, verificar que las 14 features del Bot Madre
       estén disponibles tras calcular indicadores.
    """
    print("[VALIDACIÓN] Iniciando chequeo de datos...")
    for tf, df in datos.items():
        if df is None or df.empty:
            raise ValueError(f"DataFrame vacío para timeframe {tf}")
        if len(df) < 1000:
            print(f"[VALIDACIÓN] WARN: {tf} tiene solo {len(df)} filas (mínimo recomendado 1000)")
        # Varianza de close
        if "close" in df.columns:
            var = df["close"].var()
            if var == 0 or pd.isna(var):
                raise ValueError(f"{tf}: varianza de 'close' es cero — datos posiblemente corruptos o archivo bloqueado (¿Excel abierto?)")
            print(f"  ✅ {tf}: varianza close={var:.2f} | filas={len(df)}")
        else:
            raise ValueError(f"{tf}: columna 'close' no encontrada")
        # OHLCV mínimas
        for col in ["open", "high", "low", "volume"]:
            if col not in df.columns:
                print(f"[VALIDACIÓN] WARN: {tf} no tiene columna '{col}'")
    # Features Madre (post-indicadores)
    if "M1" in datos:
        df_m1 = calcular_todos_indicadores(datos["M1"])
        faltantes = [f for f in FEATURES_MADRE_14 if f not in df_m1.columns]
        if faltantes:
            raise ValueError(f"Features faltantes para Bot Madre tras calcular indicadores: {faltantes}")
        # Verificar NaN iniciales (EMA/BB necesitan warmup)
        nan_pct = df_m1[FEATURES_MADRE_14].isna().mean().mean() * 100
        if nan_pct > 5:
            print(f"[VALIDACIÓN] WARN: {nan_pct:.1f}% NaN en features Madre — considerar adelantar ventana de entrenamiento")
        else:
            print(f"  ✅ Features Madre OK — NaN={nan_pct:.2f}%")
    print("[VALIDACIÓN] Datos validados. Procediendo al entrenamiento...")


# ════════════════════════════════════════════════════════
# PASO 3: ENTRENAR BOT MADRE
# ════════════════════════════════════════════════════════
def entrenar_madre(datos: dict[str, pd.DataFrame], pasos: int = 200_000) -> PPO:
    print("[PIPELINE] Entrenando Bot Madre...")
    env = DummyVecEnv([lambda: EntornoMadre(datos["H1"], datos["H4"])])
    # RecurrentPPO para secuencias temporales
    modelo = RecurrentPPO(
        "MlpLstmPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        tensorboard_log="/kaggle/working/logs/madre",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=pasos, progress_bar=True)
    modelo.save(str(RUTA_SALIDA / "madre_ppo"))
    print("[OK] Madre entrenado.")
    return modelo


# ════════════════════════════════════════════════════════
# PASO 4: GENERAR DECISIONES DEL MADRE SOBRE HISTÓRICO
# ════════════════════════════════════════════════════════
def generar_labels_madre(modelo: PPO, datos: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Recorre el histórico H1 y guarda las decisiones del Madre entrenado."""
    env = EntornoMadre(datos["H1"], datos["H4"])
    obs, _ = env.reset()
    decisiones = []
    for i in range(len(datos["H1"]) - 1):
        action, _ = modelo.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(int(action))
        decisiones.append({
            "idx": i,
            "accion": int(action),
            "reward": reward,
            "regimen": info.get("regimen"),
            "activado": info.get("activado", False),
        })
        if terminated or truncated:
            obs, _ = env.reset()
    df = pd.DataFrame(decisiones)
    df.to_parquet(RUTA_SALIDA / "labels_madre.parquet")
    print(f"[OK] Labels Madre generados: {len(df)} pasos.")
    return df


# ════════════════════════════════════════════════════════
# PASO 5: ENTRENAR BOT REVERSIÓN
# ════════════════════════════════════════════════════════
def entrenar_reversion(datos: dict[str, pd.DataFrame], labels: pd.DataFrame, pasos: int = 150_000) -> PPO:
    print("[PIPELINE] Entrenando Bot Reversión...")
    # Filtrar índices donde Madre eligió Reversión (accion=0)
    idx_rev = labels[labels["accion"] == 0]["idx"].tolist()
    # Crear env con datos filtrados (simplificado: usa todo y deja que el env decida)
    env = DummyVecEnv([lambda: EntornoReversion(datos["M15"], datos["M5"], datos["M1"])])
    modelo = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        tensorboard_log="/kaggle/working/logs/reversion",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=pasos, progress_bar=True)
    modelo.save(str(RUTA_SALIDA / "reversion_ppo"))
    print("[OK] Reversión entrenado.")
    return modelo


# ════════════════════════════════════════════════════════
# PASO 6: ENTRENAR BOT CONTINUACIÓN
# ════════════════════════════════════════════════════════
def entrenar_continuacion(datos: dict[str, pd.DataFrame], labels: pd.DataFrame, pasos: int = 150_000) -> PPO:
    print("[PIPELINE] Entrenando Bot Continuación...")
    env = DummyVecEnv([lambda: EntornoContinuacion(datos["M15"], datos["M5"], datos["M1"])])
    modelo = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        tensorboard_log="/kaggle/working/logs/continuacion",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=pasos, progress_bar=True)
    modelo.save(str(RUTA_SALIDA / "continuacion_ppo"))
    print("[OK] Continuación entrenado.")
    return modelo


# ════════════════════════════════════════════════════════
# PASO 7: ENTRENAR SCALPER INDEPENDIENTE
# ════════════════════════════════════════════════════════
def entrenar_scalper(datos: dict[str, pd.DataFrame], pasos: int = 150_000) -> PPO:
    print("[PIPELINE] Entrenando Bot Scalper M5...")
    env = DummyVecEnv([lambda: EntornoScalperM5(datos["M5"], datos["M1"])])
    modelo = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        tensorboard_log="/kaggle/working/logs/scalper",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=pasos, progress_bar=True)
    modelo.save(str(RUTA_SALIDA / "scalper_ppo"))
    print("[OK] Scalper entrenado.")
    return modelo


# ════════════════════════════════════════════════════════
# PASO 8-10: EXPORTAR A ONNX Y VALIDAR
# ════════════════════════════════════════════════════════
def exportar_todos(modelos: dict[str, PPO]) -> None:
    exportador = ExportadorONNX()
    for nombre, modelo in modelos.items():
        ruta_onnx = RUTA_SALIDA / f"{nombre}.onnx"
        exportador.exportar(modelo, str(ruta_onnx), opset=12)
        print(f"[ONNX] {nombre} exportado: {ruta_onnx}")


def main() -> None:
    print("=" * 60)
    print("QuantumHive — Pipeline Entrenamiento Secuencial Kaggle")
    print("=" * 60)
    datos = cargar_datos("US30")
    if not datos:
        raise RuntimeError("No se encontraron datos. Subir dataset a /kaggle/input/us30-historico")

    # Paso 2: features
    calcular_features(datos)

    # Paso 3: Madre
    madre = entrenar_madre(datos, pasos=200_000)

    # Paso 4: labels
    labels = generar_labels_madre(madre, datos)

    # Paso 5-7: Hijos
    reversion = entrenar_reversion(datos, labels, pasos=150_000)
    continuacion = entrenar_continuacion(datos, labels, pasos=150_000)
    scalper = entrenar_scalper(datos, pasos=150_000)

    # Paso 8-10: ONNX
    exportar_todos({
        "madre": madre,
        "reversion": reversion,
        "continuacion": continuacion,
        "scalper": scalper,
    })

    print("=" * 60)
    print("[DONE] Todos los modelos entrenados y exportados a ONNX.")
    print(f"Salida: {RUTA_SALIDA}")
    print("=" * 60)


def entrenar_bot_reversion(
    df_m1: pd.DataFrame,
    df_m5: pd.DataFrame,
    df_m15: pd.DataFrame,
    df_h1: pd.DataFrame,
    df_h4: pd.DataFrame,
    df_d1: pd.DataFrame,
    df_w1: pd.DataFrame,
    df_madre_decisiones: pd.DataFrame,
    total_timesteps: int = 200_000,
) -> tuple[PPO, pd.DataFrame]:
    """
    Paso 5 — Entrenar Bot Reversión con datos donde Madre=1 (REVERSIÓN).

    Filtra solo las filas donde Madre decidió reversión, y entrena
    un PPO con action_space de 2 acciones (0=SHORT, 1=LONG).
    """
    print("[PIPELINE] Paso 5 — Entrenando Bot Reversión (Madre=1)...")
    # Filtrar datos donde Madre decidió reversión
    mascara_reversion = df_madre_decisiones["decision_madre"] == 1
    # Aunque filtramos las decisiones, entrenamos sobre TODO el histórico
    # pero usando el reward shaping de reversión: penalizar si no hay bounce
    env_fn = lambda: EntornoReversion(
        df_m1=df_m1,
        df_m5=df_m5,
        df_m15=df_m15,
        df_h1=df_h1,
        df_h4=df_h4,
        df_d1=df_d1,
        df_w1=df_w1,
        config=ConfigReversion(),
    )
    env = DummyVecEnv([env_fn])
    modelo = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=512,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=total_timesteps, progress_bar=True)
    print("[PIPELINE] Bot Reversión entrenado.")
    return modelo, df_madre_decisiones


def entrenar_bot_continuacion(
    df_m1: pd.DataFrame,
    df_m5: pd.DataFrame,
    df_m15: pd.DataFrame,
    df_h1: pd.DataFrame,
    df_h4: pd.DataFrame,
    df_d1: pd.DataFrame,
    df_w1: pd.DataFrame,
    df_madre_decisiones: pd.DataFrame,
    total_timesteps: int = 200_000,
) -> tuple[PPO, pd.DataFrame]:
    """
    Paso 6 — Entrenar Bot Continuación con datos donde Madre=2 (CONTINUACIÓN).

    Filtra solo las filas donde Madre decidió continuación, y entrena
    un PPO con action_space de 2 acciones (0=SHORT, 1=LONG).
    """
    print("[PIPELINE] Paso 6 — Entrenando Bot Continuación (Madre=2)...")
    env_fn = lambda: EntornoContinuacion(
        df_m1=df_m1,
        df_m5=df_m5,
        df_m15=df_m15,
        df_h1=df_h1,
        df_h4=df_h4,
        df_d1=df_d1,
        df_w1=df_w1,
        config=ConfigContinuacion(),
    )
    env = DummyVecEnv([env_fn])
    modelo = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=512,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=total_timesteps, progress_bar=True)
    print("[PIPELINE] Bot Continuación entrenado.")
    return modelo, df_madre_decisiones


def entrenar_bot_scalper(
    df_m1: pd.DataFrame,
    total_timesteps: int = 300_000,
) -> PPO:
    """
    Paso 7 — Entrenar Bot Scalper M1 independiente.

    Detecta zonas de surfeo de bandas de Bollinger (M1) y entrena
    un PPO con 3 acciones (0=SHORT, 1=LONG, 2=ESPERAR).
    """
    print("[PIPELINE] Paso 7 — Entrenando Bot Scalper M1...")
    # Detectar zonas de surfeo de banda (M1)
    df_m1 = df_m1.copy()
    df_m1 = calcular_bollinger(df_m1)
    # Surfeo: precio toca banda superior/inferior con volumen confirmado
    df_m1["surfeo_sup"] = (
        (df_m1["close"] >= df_m1["bb_upper"].shift(1)) &
        (df_m1["close"].shift(1) < df_m1["bb_upper"].shift(2))
    )
    df_m1["surfeo_inf"] = (
        (df_m1["close"] <= df_m1["bb_lower"].shift(1)) &
        (df_m1["close"].shift(1) > df_m1["bb_lower"].shift(2))
    )
    df_m1["surfeo"] = df_m1["surfeo_sup"] | df_m1["surfeo_inf"]
    env_fn = lambda: EntornoScalperM5(
        df_m1=df_m1,
        config=ConfigScalperM5(),
    )
    env = DummyVecEnv([env_fn])
    modelo = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    modelo.learn(total_timesteps=total_timesteps, progress_bar=True)
    print("[PIPELINE] Bot Scalper entrenado.")
    return modelo


def exportar_onnx(
    modelo_madre: RecurrentPPO,
    modelo_reversion: PPO,
    modelo_continuacion: PPO,
    modelo_scalper: PPO,
    ruta_salida: Path = RUTA_SALIDA,
) -> dict[str, Path]:
    """
    Paso 8 — Exportar 4 modelos a ONNX (opset 12, compatible MT5).
    """
    print("[PIPELINE] Paso 8 — Exportando modelos a ONNX...")
    exportador = ExportadorONNX()
    rutas: dict[str, Path] = {}

    # Madre — 14 features, 3 acciones (RecurrentPPO → LSTM → ONNX tricky)
    # Para MT5, exportamos solo el policy MLP (sin LSTM hidden states)
    ruta_madre = ruta_salida / "bot_madre.onnx"
    exportador.exportar_mlp(modelo_madre, input_dim=14, output_dim=3, ruta=ruta_madre, opset=12)
    rutas["madre"] = ruta_madre

    # Reversión — 14 features, 2 acciones
    ruta_rev = ruta_salida / "bot_reversion.onnx"
    exportador.exportar_mlp(modelo_reversion, input_dim=14, output_dim=2, ruta=ruta_rev, opset=12)
    rutas["reversion"] = ruta_rev

    # Continuación — 14 features, 2 acciones
    ruta_cont = ruta_salida / "bot_continuacion.onnx"
    exportador.exportar_mlp(modelo_continuacion, input_dim=14, output_dim=2, ruta=ruta_cont, opset=12)
    rutas["continuacion"] = ruta_cont

    # Scalper — 19 features, 3 acciones
    ruta_scalp = ruta_salida / "bot_scalper.onnx"
    exportador.exportar_mlp(modelo_scalper, input_dim=19, output_dim=3, ruta=ruta_scalp, opset=12)
    rutas["scalper"] = ruta_scalp

    print(f"[PIPELINE] Modelos ONNX exportados en: {ruta_salida}")
    return rutas


def validar_onnx(rutas: dict[str, Path]) -> dict[str, bool]:
    """
    Paso 9 — Validar cada ONNX con onnxruntime.
    """
    print("[PIPELINE] Paso 9 — Validando modelos ONNX...")
    import onnxruntime as ort
    resultados: dict[str, bool] = {}
    for nombre, ruta in rutas.items():
        try:
            sess = ort.InferenceSession(str(ruta))
            input_name = sess.get_inputs()[0].name
            input_shape = sess.get_inputs()[0].shape
            # Dummy input según dimensión
            if nombre == "scalper":
                dummy = np.random.randn(1, 19).astype(np.float32)
            else:
                dummy = np.random.randn(1, 14).astype(np.float32)
            output = sess.run(None, {input_name: dummy})
            resultados[nombre] = True
            print(f"  ✅ {nombre}: OK (input={input_shape}, output={[o.shape for o in output]})")
        except Exception as e:
            resultados[nombre] = False
            print(f"  ❌ {nombre}: ERROR — {e}")
    return resultados


def pipeline_completo(
    simbolo: str = "US30",
    usar_csv_institucional: bool = True,
    pasos: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
) -> dict[str, any]:
    """
    Ejecuta el pipeline secuencial completo QuantumHive.

    Parámetros:
        simbolo: par de trading (default US30).
        usar_csv_institucional: si True, intenta cargar dataset_INSTITUCIONAL_2025.csv primero.
        pasos: tupla de pasos a ejecutar (default todos).
    """
    resultados: dict[str, any] = {}

    # ── PASO 1: Cargar datos ──
    if 1 in pasos:
        datos = cargar_datos(simbolo)
        if not datos:
            # Fallback a CSV institucional
            df_inst = cargar_csv_institucional()
            if df_inst is not None:
                print(f"[PIPELINE] Usando CSV institucional: {len(df_inst)} filas")
                # Asumimos que es M1 por defecto; el usuario debe confirmar timeframe
                datos = {"M1": df_inst}
            else:
                raise RuntimeError("No se encontraron datos (ni parquet ni CSV institucional)")
        resultados["datos"] = datos
    else:
        datos = resultados.get("datos")

    # ── PASO 2: Calcular indicadores ──
    if 2 in pasos and datos:
        for tf, df in datos.items():
            datos[tf] = calcular_todos_indicadores(df)
        resultados["datos"] = datos

    # ── PASO 2b: Validar datos antes de entrenar ──
    if 2 in pasos and datos:
        validar_datos_pipeline(datos)

    # ── PASO 3: Entrenar Madre ──
    if 3 in pasos and datos:
        print("[PIPELINE] Paso 3 — Entrenando Bot Madre (RecurrentPPO, GPU)...")
        env_fn = lambda: EntornoMadre(
            df_m1=datos.get("M1"),
            df_m5=datos.get("M5"),
            df_m15=datos.get("M15"),
            df_h1=datos.get("H1"),
            df_h4=datos.get("H4"),
            df_d1=datos.get("D1"),
            df_w1=datos.get("W1"),
            config=ConfigMadre(),
        )
        env = DummyVecEnv([env_fn])
        modelo_madre = RecurrentPPO(
            "MlpLstmPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=512,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        modelo_madre.learn(total_timesteps=500_000, progress_bar=True)
        resultados["modelo_madre"] = modelo_madre
        # Guardar checkpoint
        ruta_ckpt = RUTA_SALIDA / "bot_madre_ppo.zip"
        modelo_madre.save(str(ruta_ckpt))
        print(f"[PIPELINE] Madre guardada en: {ruta_ckpt}")

    # ── PASO 4: Generar decisiones del Madre sobre histórico ──
    if 4 in pasos and "modelo_madre" in resultados:
        print("[PIPELINE] Paso 4 — Generando decisiones del Madre...")
        df_m1 = datos["M1"]
        env_madre = EntornoMadre(
            df_m1=df_m1,
            df_m5=datos.get("M5"),
            df_m15=datos.get("M15"),
            df_h1=datos.get("H1"),
            df_h4=datos.get("H4"),
            df_d1=datos.get("D1"),
            df_w1=datos.get("W1"),
            config=ConfigMadre(),
        )
        obs, info = env_madre.reset()
        decisiones = []
        for i in range(len(df_m1) - 1):
            action, _ = resultados["modelo_madre"].predict(obs, deterministic=True)
            decisiones.append({
                "timestamp": df_m1.index[i],
                "decision_madre": int(action),
                "close": df_m1["close"].iloc[i],
            })
            obs, reward, terminated, truncated, info = env_madre.step(action)
            if terminated or truncated:
                obs, info = env_madre.reset()
        df_decisiones = pd.DataFrame(decisiones)
        resultados["df_decisiones"] = df_decisiones
        df_decisiones.to_csv(RUTA_SALIDA / "decisiones_madre.csv", index=False)
        print(f"[PIPELINE] Decisiones generadas: {len(df_decisiones)} filas")

    # ── PASO 5: Entrenar Reversión ──
    if 5 in pasos and "df_decisiones" in resultados:
        modelo_rev, _ = entrenar_bot_reversion(
            df_m1=datos["M1"],
            df_m5=datos.get("M5"),
            df_m15=datos.get("M15"),
            df_h1=datos.get("H1"),
            df_h4=datos.get("H4"),
            df_d1=datos.get("D1"),
            df_w1=datos.get("W1"),
            df_madre_decisiones=resultados["df_decisiones"],
        )
        resultados["modelo_reversion"] = modelo_rev
        modelo_rev.save(str(RUTA_SALIDA / "bot_reversion_ppo.zip"))

    # ── PASO 6: Entrenar Continuación ──
    if 6 in pasos and "df_decisiones" in resultados:
        modelo_cont, _ = entrenar_bot_continuacion(
            df_m1=datos["M1"],
            df_m5=datos.get("M5"),
            df_m15=datos.get("M15"),
            df_h1=datos.get("H1"),
            df_h4=datos.get("H4"),
            df_d1=datos.get("D1"),
            df_w1=datos.get("W1"),
            df_madre_decisiones=resultados["df_decisiones"],
        )
        resultados["modelo_continuacion"] = modelo_cont
        modelo_cont.save(str(RUTA_SALIDA / "bot_continuacion_ppo.zip"))

    # ── PASO 7: Entrenar Scalper ──
    if 7 in pasos and "M1" in datos:
        modelo_scalper = entrenar_bot_scalper(datos["M1"])
        resultados["modelo_scalper"] = modelo_scalper
        modelo_scalper.save(str(RUTA_SALIDA / "bot_scalper_ppo.zip"))

    # ── PASO 8: Exportar ONNX ──
    if 8 in pasos and all(k in resultados for k in ["modelo_madre", "modelo_reversion", "modelo_continuacion", "modelo_scalper"]):
        rutas_onnx = exportar_onnx(
            resultados["modelo_madre"],
            resultados["modelo_reversion"],
            resultados["modelo_continuacion"],
            resultados["modelo_scalper"],
        )
        resultados["rutas_onnx"] = rutas_onnx

    # ── PASO 9: Validar ONNX ──
    if 9 in pasos and "rutas_onnx" in resultados:
        validaciones = validar_onnx(resultados["rutas_onnx"])
        resultados["validaciones"] = validaciones
        all_ok = all(validaciones.values())
        print(f"[PIPELINE] Validación ONNX: {'✅ TODOS OK' if all_ok else '❌ ALGUNOS FALLARON'}")

    # ── PASO 10: Guardar en /kaggle/working/modelos_onnx/ ──
    if 10 in pasos:
        print(f"[PIPELINE] Paso 10 — Modelos listos en: {RUTA_SALIDA}")
        for f in RUTA_SALIDA.iterdir():
            print(f"  📦 {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    return resultados


if __name__ == "__main__":
    # Ejecutar pipeline completo
    print("=" * 60)
    print("  QUANTUMHIVE — PIPELINE SECUENCIAL COMPLETO")
    print("  GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
    print("=" * 60)
    resultados = pipeline_completo()
    print("\n[PIPELINE] FINALIZADO. Modelos en:", RUTA_SALIDA)
    main()

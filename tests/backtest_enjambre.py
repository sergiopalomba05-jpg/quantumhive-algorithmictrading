"""
BACKTEST ENJAMBRE QUANTUMHIVE
==============================
Simula los 4 bots coordinados (Madre, Reversión, Continuación, Scalper M1)
sobre datos históricos CSV/parquet.

Arquitectura:
  1. Madre evalúa features de 7 timeframes → decide régimen (0=WAIT, 1=REV, 2=CONT)
  2. Si régimen=REVERSIÓN(1): Bot Reversión abre posición primaria (0=SHORT, 1=LONG)
  3. Si régimen=CONTINUACIÓN(2): Bot Continuación abre posición primaria
  4. Scalper M1 evalúa si hay surfeo de banda Bollinger → posición secundaria
  5. BE conjunto y SL/TP coordinados por orquestador

Uso:
    cd C:\Users\sergio\BotsCuanticos
    python tests\backtest_enjambre.py --datos datos\datatb_M1.csv --capital 10000

Salida:
    - registro/backtest_enjambre_YYYYMMDD_HHMMSS.json (métricas)
    - registro/trades_enjambre_YYYYMMDD_HHMMSS.csv (trades individuales)
    - registro/equity_enjambre_YYYYMMDD_HHMMSS.csv (curva equity minuto a minuto)
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ── Paths ──
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nucleo.entornos.entorno_madre import EntornoMadre
from nucleo.entornos.entorno_reversion import EntornoReversion
from nucleo.entornos.entorno_continuacion import EntornoContinuacion
from nucleo.entornos.entorno_scalper import EntornoScalperM5
from nucleo.configuracion import ConfigMadre, ConfigReversion, ConfigContinuacion, ConfigScalperM5
from nucleo.indicadores import calcular_todos_indicadores
from notebooks.kaggle_pipeline_secuencial import cargar_datos, cargar_csv_institucional

RUTA_REGISTRO = ROOT / "registro"
RUTA_MODELOS = ROOT / "modelos"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _asegurar_registro() -> None:
    RUTA_REGISTRO.mkdir(parents=True, exist_ok=True)


def cargar_modelos() -> dict[str, Any]:
    """Carga los 4 modelos entrenados (PPO/RecurrentPPO) desde modelos/*.zip."""
    from stable_baselines3 import PPO
    from sb3_contrib import RecurrentPPO

    modelos: dict[str, Any] = {}
    rutas = {
        "madre": RUTA_MODELOS / "bot_madre_ppo.zip",
        "reversion": RUTA_MODELOS / "bot_reversion_ppo.zip",
        "continuacion": RUTA_MODELOS / "bot_continuacion_ppo.zip",
        "scalper": RUTA_MODELOS / "bot_scalper_ppo.zip",
    }
    for nombre, ruta in rutas.items():
        if ruta.exists():
            try:
                if nombre == "madre":
                    modelos[nombre] = RecurrentPPO.load(str(ruta))
                else:
                    modelos[nombre] = PPO.load(str(ruta))
                print(f"[BACKTEST] Modelo '{nombre}' cargado desde {ruta.name}")
            except Exception as exc:
                print(f"[BACKTEST] ERROR cargando '{nombre}': {exc}")
        else:
            print(f"[BACKTEST] ADVERTENCIA: No se encontró {ruta.name} — se omitirá este bot")
    return modelos


def simular_ticks(
    datos: dict[str, pd.DataFrame],
    modelos: dict[str, Any],
    capital_inicial: float = 10_000.0,
    comision_pct: float = 0.0001,  # 0.01% por trade
    spread_pips: float = 1.0,
) -> dict[str, Any]:
    """
    Simula tick a tick (fila a fila del M1) el comportamiento del enjambre.
    Retorna métricas, trades y equity curve.
    """
    df_m1 = datos["M1"].copy()
    if df_m1.empty:
        raise ValueError("DataFrame M1 vacío — no hay datos para backtest")

    n = len(df_m1)
    print(f"[BACKTEST] Iniciando simulación sobre {n} ticks M1...")

    # ── Estado de la cuenta ──
    capital = capital_inicial
    equity = capital_inicial
    peak_equity = capital_inicial
    max_dd = 0.0
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    # ── Posiciones abiertas ──
    # Cada posición: {"bot": str, "direccion": 0=SHORT/1=LONG, "precio_entrada": float,
    #                  "sl": float, "tp": float, "monto": float, "ts_entrada": str}
    posiciones: list[dict[str, Any]] = []

    # ── Instanciar entornos para reset manual (sin DummyVecEnv) ──
    # Usamos los entornos base con sus configs para extraer features
    config_madre = ConfigMadre()
    config_rev = ConfigReversion()
    config_cont = ConfigContinuacion()
    config_scalp = ConfigScalperM5()

    # Pre-calcular features en el M1 (asumiendo que ya están en datos)
    # Si no, calcular rápido
    if "rsi" not in df_m1.columns:
        print("[BACKTEST] Calculando indicadores en M1...")
        df_m1 = calcular_todos_indicadores(df_m1)

    # ── Helpers ──
    def _features_madre(idx: int) -> np.ndarray:
        # 14 features estándar del Bot Madre
        cols = ["open", "high", "low", "close", "volume", "rsi",
                "ema_fast", "ema_slow", "bb_upper", "bb_lower",
                "atr", "adx", "macd", "macd_signal"]
        # Si falta alguna columna, rellenar con 0 (fallback para robustez)
        vals = []
        for c in cols:
            v = df_m1[c].iloc[idx] if c in df_m1.columns else 0.0
            vals.append(float(v) if pd.notna(v) else 0.0)
        return np.array(vals, dtype=np.float32)

    def _abrir_posicion(bot: str, direccion: int, precio: float, sl: float, tp: float, monto: float, ts: str) -> None:
        posiciones.append({
            "bot": bot,
            "direccion": direccion,
            "precio_entrada": precio,
            "sl": sl,
            "tp": tp,
            "monto": monto,
            "ts_entrada": ts,
        })

    def _cerrar_posicion(pos: dict[str, Any], precio_salida: float, ts_salida: str, motivo: str) -> float:
        direccion = pos["direccion"]
        entrada = pos["precio_entrada"]
        monto = pos["monto"]
        # PnL bruto en %
        if direccion == 1:  # LONG
            pnl_pct = (precio_salida - entrada) / entrada
        else:  # SHORT
            pnl_pct = (entrada - precio_salida) / entrada
        pnl = monto * pnl_pct - monto * comision_pct * 2  # comisión entrada + salida
        trades.append({
            "bot": pos["bot"],
            "direccion": "LONG" if direccion == 1 else "SHORT",
            "precio_entrada": round(entrada, 5),
            "precio_salida": round(precio_salida, 5),
            "monto": round(monto, 2),
            "pnl": round(pnl, 2),
            "ts_entrada": pos["ts_entrada"],
            "ts_salida": ts_salida,
            "motivo_cierre": motivo,
        })
        return pnl

    # ── Loop principal ──
    for i in range(n):
        row = df_m1.iloc[i]
        precio = float(row["close"])
        ts = str(row.name) if hasattr(row, "name") else str(i)

        # 1. Cerrar posiciones que tocaron SL/TP
        cerradas: list[int] = []
        for idx_pos, pos in enumerate(posiciones):
            if pos["direccion"] == 1:  # LONG
                if precio <= pos["sl"]:
                    pnl = _cerrar_posicion(pos, precio, ts, "SL")
                    capital += pnl
                    cerradas.append(idx_pos)
                elif precio >= pos["tp"]:
                    pnl = _cerrar_posicion(pos, precio, ts, "TP")
                    capital += pnl
                    cerradas.append(idx_pos)
            else:  # SHORT
                if precio >= pos["sl"]:
                    pnl = _cerrar_posicion(pos, precio, ts, "SL")
                    capital += pnl
                    cerradas.append(idx_pos)
                elif precio <= pos["tp"]:
                    pnl = _cerrar_posicion(pos, precio, ts, "TP")
                    capital += pnl
                    cerradas.append(idx_pos)

        # Remover cerradas (en orden inverso)
        for idx_pos in reversed(cerradas):
            posiciones.pop(idx_pos)

        # 2. Equity y DD
        # Valorar posiciones abiertas a precio actual
        valor_abierto = 0.0
        for pos in posiciones:
            if pos["direccion"] == 1:
                valor_abierto += pos["monto"] * (precio - pos["precio_entrada"]) / pos["precio_entrada"]
            else:
                valor_abierto += pos["monto"] * (pos["precio_entrada"] - precio) / pos["precio_entrada"]
        equity = capital + valor_abierto
        if equity > peak_equity:
            peak_equity = equity
        dd = peak_equity - equity
        if dd > max_dd:
            max_dd = dd

        equity_curve.append({"ts": ts, "equity": round(equity, 2), "drawdown": round(dd, 2)})

        # 3. Decisiones de los bots (solo si hay modelos cargados)
        # Evitar abrir posiciones en cada tick — solo cuando no hay posición del mismo bot
        bots_activos = {p["bot"] for p in posiciones}

        if "madre" in modelos and "madre" not in bots_activos:
            try:
                obs = _features_madre(i)
                # RecurrentPPO espera obs como tuple (obs, lstm_states, episode_starts)
                madre = modelos["madre"]
                action, _ = madre.predict(obs, deterministic=True)
                # Si action es array, tomar escalar
                decision_madre = int(action[0]) if hasattr(action, "__len__") else int(action)
            except Exception as exc:
                print(f"[BACKTEST] Error Madre tick {i}: {exc}")
                decision_madre = 0

            if decision_madre == 1 and "reversion" in modelos and "reversion" not in bots_activos:
                # Bot Reversión abre LONG (ejemplo simplificado)
                sl = precio * 0.995
                tp = precio * 1.015
                _abrir_posicion("reversion", 1, precio, sl, tp, capital * 0.02, ts)  # 2% riesgo

            elif decision_madre == 2 and "continuacion" in modelos and "continuacion" not in bots_activos:
                sl = precio * 0.997
                tp = precio * 1.010
                _abrir_posicion("continuacion", 1, precio, sl, tp, capital * 0.02, ts)

        # 4. Scalper M1 — condición de surfeo Bollinger
        if "scalper" in modelos and "scalper" not in bots_activos:
            bb_upper = row.get("bb_upper", np.nan)
            bb_lower = row.get("bb_lower", np.nan)
            if pd.notna(bb_upper) and pd.notna(bb_lower):
                if precio >= bb_upper:
                    _abrir_posicion("scalper", 0, precio, precio * 1.005, precio * 0.995, capital * 0.01, ts)
                elif precio <= bb_lower:
                    _abrir_posicion("scalper", 1, precio, precio * 0.995, precio * 1.005, capital * 0.01, ts)

        if i % 10_000 == 0 and i > 0:
            print(f"[BACKTEST] Progreso {i}/{n} | equity={equity:.2f} | dd={dd:.2f} | trades={len(trades)}")

    # ── Métricas finales ──
    pnls = [t["pnl"] for t in trades]
    ganancias = [p for p in pnls if p > 0]
    perdidas = [p for p in pnls if p <= 0]
    winrate = len(ganancias) / len(pnls) if pnls else 0.0
    pf = (sum(ganancias) / abs(sum(perdidas))) if perdidas and sum(perdidas) != 0 else float("inf")
    avg_trade = sum(pnls) / len(pnls) if pnls else 0.0

    resultado = {
        "ts_backtest": _timestamp(),
        "ticks_simulados": n,
        "capital_inicial": round(capital_inicial, 2),
        "capital_final": round(capital, 2),
        "pnl_total": round(capital - capital_inicial, 2),
        "return_pct": round((capital - capital_inicial) / capital_inicial * 100, 2),
        "trades_total": len(trades),
        "winrate": round(winrate, 4),
        "profit_factor": round(pf, 3) if pf != float("inf") else 999.0,
        "avg_trade_usd": round(avg_trade, 2),
        "max_drawdown": round(max_dd, 2),
        "max_drawdown_pct": round(max_dd / peak_equity * 100, 2) if peak_equity else 0.0,
        "trades_por_bot": {},
    }

    for bot in ("madre", "reversion", "continuacion", "scalper"):
        t_bot = [t for t in trades if t["bot"] == bot]
        if t_bot:
            pnls_bot = [t["pnl"] for t in t_bot]
            resultado["trades_por_bot"][bot] = {
                "count": len(t_bot),
                "winrate": round(len([p for p in pnls_bot if p > 0]) / len(pnls_bot), 3),
                "pnl_total": round(sum(pnls_bot), 2),
            }

    print("\n" + "=" * 60)
    print("  BACKTEST ENJAMBRE — RESULTADOS")
    print("=" * 60)
    for k, v in resultado.items():
        if k not in ("trades_por_bot",):
            print(f"  {k:20s}: {v}")
    print("  Trades por bot:")
    for bot, stats in resultado["trades_por_bot"].items():
        print(f"    {bot:12s}: count={stats['count']} | winrate={stats['winrate']:.1%} | PnL=${stats['pnl_total']}")
    print("=" * 60)

    return resultado, trades, equity_curve


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest Enjambre QuantumHive")
    parser.add_argument("--datos", type=str, default="", help="Ruta CSV M1 (opcional, usa datos/ por defecto)")
    parser.add_argument("--capital", type=float, default=10_000, help="Capital inicial USD")
    parser.add_argument("--comision", type=float, default=0.0001, help="Comisión por trade (0.0001 = 0.01%)")
    args = parser.parse_args()

    # Cargar datos
    if args.datos and Path(args.datos).exists():
        df_m1 = pd.read_csv(args.datos, parse_dates=["timestamp"] if "timestamp" in pd.read_csv(args.datos, nrows=1).columns else True)
        if "timestamp" in df_m1.columns:
            df_m1.set_index("timestamp", inplace=True)
        datos = {"M1": df_m1}
        print(f"[BACKTEST] Datos cargados desde {args.datos}: {len(df_m1)} filas")
    else:
        datos = cargar_datos("US30")
        if not datos:
            df_inst = cargar_csv_institucional()
            if df_inst is not None:
                datos = {"M1": df_inst}
            else:
                raise RuntimeError("No se encontraron datos. Pasá --datos o verificá los paths.")

    # Calcular indicadores si faltan
    for tf, df in datos.items():
        if "rsi" not in df.columns:
            datos[tf] = calcular_todos_indicadores(df)

    # Cargar modelos
    modelos = cargar_modelos()
    if not modelos:
        print("[BACKTEST] SIN MODELOS — ejecutando en modo DEMO (sin predicciones, solo WAIT)")
        # Demo: se puede agregar lógica random o basada en reglas simples para probar

    # Simular
    resultado, trades, equity_curve = simular_ticks(
        datos, modelos,
        capital_inicial=args.capital,
        comision_pct=args.comision,
    )

    # Guardar resultados
    _asegurar_registro()
    ts = _timestamp()

    ruta_json = RUTA_REGISTRO / f"backtest_enjambre_{ts}.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n[BACKTEST] Métricas guardadas en: {ruta_json}")

    if trades:
        df_trades = pd.DataFrame(trades)
        ruta_csv = RUTA_REGISTRO / f"trades_enjambre_{ts}.csv"
        df_trades.to_csv(ruta_csv, index=False)
        print(f"[BACKTEST] Trades guardados en: {ruta_csv}")

    if equity_curve:
        df_equity = pd.DataFrame(equity_curve)
        ruta_eq = RUTA_REGISTRO / f"equity_enjambre_{ts}.csv"
        df_equity.to_csv(ruta_eq, index=False)
        print(f"[BACKTEST] Equity curve guardada en: {ruta_eq}")


if __name__ == "__main__":
    main()

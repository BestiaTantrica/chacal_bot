#!/usr/bin/env python3
"""
Diagnóstico Chacal: Fuerza el análisis de un par para ver por qué no entra.
Uso: python3 debug_signal.py
"""
import sys
import json
import pandas as pd
import talib.abstract as ta
from freqtrade.data.history import load_pair_history
from freqtrade.enums import CandleType
from freqtrade.configuration import Configuration
from freqtrade.resolvers import StrategyResolver
from pathlib import Path

# Config
config_path = "/freqtrade/user_data/config_chacal_aws.json"
strategy_name = "EstrategiaChacal"
pair = "BTC/USDT:USDT"
timeframe = "5m"

print(f"--- Diagnóstico Chacal para {pair} ---")

# Cargar configuración
config = Configuration.from_files([config_path])
config['strategy'] = strategy_name
config['data_dir'] = Path(config['user_data_dir']) / 'data' / 'binance'

# Cargar datos
print("Cargando datos...")
candles = load_pair_history(
    pair=pair,
    timeframe=timeframe,
    datadir=config['data_dir'],
    candle_type=CandleType.FUTURES
)
print(f"Datos cargados: {len(candles)} velas. Última: {candles.iloc[-1]['date']}")

# Cargar estrategia
print("Cargando estrategia y parámetros...")
strategy = StrategyResolver.load_strategy(config)

# Poblar indicadores
print("Calculando indicadores...")
df = strategy.populate_indicators(candles, {'pair': pair})

# Evaluar entrada
print("Evaluando Entry Trend...")
df = strategy.populate_entry_trend(df, {'pair': pair})

last_candle = df.iloc[-1]
prev_candle = df.iloc[-2]

# Chequear condiciones una por una (Modo Triple Switch)
print(f"Modo Activo: {strategy.manual_mode.value}")
print(f"EMA 200: {last_candle['ema_200']:.2f}")

if strategy.manual_mode.value == 1:
    print("\n--- ANÁLISIS MODO BULL ---")
    c1 = last_candle['close'] > last_candle['ema_200']
    c2 = last_candle['rsi'] < 45
    c3 = last_candle['volatility_censor']
    print(f"1. Close > EMA200: {'✅' if c1 else '❌'} ({last_candle['close']:.2f} vs {last_candle['ema_200']:.2f})")
    print(f"2. RSI < 45: {'✅' if c2 else '❌'} ({last_candle['rsi']:.2f})")
    print(f"3. Censor Volatilidad: {'✅' if c3 else '❌'}")
elif strategy.manual_mode.value == 2:
    print("\n--- ANÁLISIS MODO BEAR ---")
    c1 = last_candle['close'] < last_candle['ema_200']
    c2 = last_candle['rsi'] > 55
    c3 = last_candle['volatility_censor']
    print(f"1. Close < EMA200: {'✅' if c1 else '❌'} ({last_candle['close']:.2f} vs {last_candle['ema_200']:.2f})")
    print(f"2. RSI > 55: {'✅' if c2 else '❌'} ({last_candle['rsi']:.2f})")
    print(f"3. Censor Volatilidad: {'✅' if c3 else '❌'}")

if 'enter_long' in last_candle and last_candle['enter_long'] == 1:
    print("\n✅ ¡SEÑAL DE COMPRA DETECTADA!")
else:
    print("\n❌ NO HAY SEÑAL DE COMPRA.")

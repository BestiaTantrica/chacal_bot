#!/usr/bin/env python3
"""
ANALISTA - Market Regime Detection V2.0 (Multi-Asset)
-----------------------------------------------------
Analiza el estado actual del mercado (Volatilidad, Tendencia) usando un
Índice Compuesto de los pares en watchlist.

Uso:
    from analista import get_market_regime_timeranges
    regimes = get_market_regime_timeranges()
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob

# Configuración
DATA_DIR = "user_data/data/binance"
TIMEFRAME = "5m"
STATIC_PAIRS_FILE = "user_data/static_pairs.json"

def get_watchlist():
    try:
        with open(STATIC_PAIRS_FILE, 'r', encoding='utf-8') as f:
            pairs = json.load(f)
            # Limitar a Top 5 para el índice general para agilizar
            return pairs[:5] 
    except Exception as e:
        print(f"[!] Error leyendo watchlist: {e}")
        return ["BTC/USDT:USDT", "ETH/USDT:USDT"]

def load_data(pair, timeframe):
    """Carga datos OHLCV desde archivos .feather de Freqtrade."""
    # Normalizar nombre para futuros: BTC/USDT:USDT -> BTC_USDT_USDT
    pair_slug = pair.replace("/", "_").replace(":", "_")
    
    # Path para archivos .feather en carpeta futures
    found_path = os.path.join(DATA_DIR, "futures", f"{pair_slug}-{timeframe}-futures.feather")
    
    if os.path.exists(found_path):
        try:
            # Freqtrade feather format: date, open, high, low, close, volume
            df = pd.read_feather(found_path)
            # print(f"[DEBUG] Loaded {pair} from {found_path}, rows: {len(df)}")
            return df
        except Exception as e:
            print(f"[!] Error leyendo feather {pair}: {e}")
    else:
        print(f"[DEBUG] Archivo NO encontrado: {found_path}")
            
    return None

def calculate_features(df, period=14):
    """Calcula métricas de régimen de mercado para un solo par."""
    df = df.copy()
    
    # 1. Volatilidad (ATR Simplificado)
    df['range'] = (df['high'] - df['low']) / df['close']
    df['volatility'] = df['range'].rolling(window=period*24*12).mean() 
    
    # 2. Tendencia (Precio vs SMA 200 periodos largos ~ 1 semana)
    long_ma = 2016 # 1 semana en velas de 5m
    df['sma_long'] = df['close'].rolling(window=long_ma).mean()
    df['trend_score'] = (df['close'] - df['sma_long']) / df['sma_long']
    
    # 3. Volumen Relativo
    df['vol_ma'] = df['volume'].rolling(window=long_ma).mean()
    df['rel_volume'] = df['volume'] / df['vol_ma']
    
    return df[['date', 'volatility', 'trend_score', 'rel_volume']].dropna()

def build_market_index(pairs):
    """Crea un DataFrame promedio de N monedas para representar 'El Mercado'."""
    print(f"[ANALISTA] Construyendo Índice de Mercado ({len(pairs)} pares)...")
    
    dfs = []
    for pair in pairs:
        raw_df = load_data(pair, TIMEFRAME)
        if raw_df is not None and not raw_df.empty:
            feat_df = calculate_features(raw_df)
            feat_df = feat_df.set_index('date')
            dfs.append(feat_df)
            
    if not dfs:
        return None
        
    # Concatenar y calcular media por fecha (index)
    # Esto nos da el promedio del mercado en cada momento
    combined = pd.concat(dfs)
    market_index = combined.groupby(combined.index).mean()
    market_index = market_index.reset_index()
    
    print(f"[ANALISTA] Índice construido. {len(market_index)} periodos analizados.")
    return market_index

def find_similar_regimes(df, current_window_days=2, lookback_days=180):
    """Encuentra periodos históricos similares EN EL PASADO LEJANO."""
    features = ['volatility', 'trend_score', 'rel_volume']
    
    if df.empty: return []

    # Estado actual (media de los últimos 30 días - CONFIGURACIÓN DE USUARIO)
    current_window_days = 30
    current_end_date = df['date'].iloc[-1]
    current_start_date = current_end_date - timedelta(days=current_window_days)
    
    current_slice = df[(df['date'] >= current_start_date) & 
                       (df['date'] <= current_end_date)]
                       
    if current_slice.empty:
        print("[!] Datos muy antiguos, no se puede determinar régimen actual.")
        return []

    current_params = current_slice[features].mean()
    
    print(f"\n[ANALISTA] Régimen Actual (Últimos {current_window_days} días):")
    print(current_params)
    
    # CAMBIO CRÍTICO: Excluir últimos 60 días para no encontrarnos a nosotros mismos
    history_cutoff_end = current_start_date - timedelta(days=60)
    history_cutoff_start = history_cutoff_end - timedelta(days=lookback_days)
    
    historical_df = df[(df['date'] >= history_cutoff_start) & (df['date'] < history_cutoff_end)]
    
    print(f"[ANALISTA] Buscando espejo entre {history_cutoff_start.strftime('%Y-%m-%d')} y {history_cutoff_end.strftime('%Y-%m-%d')}")
    
    # Resample diario para búsqueda rápida
    df_daily = historical_df.set_index('date').resample('1D')[features].mean().dropna()
    
    # Normalización simple (Z-Score)
    stats = df_daily.describe()
    def normalize(val, col):
        if stats[col]['std'] == 0: return 0
        return (val - stats[col]['mean']) / stats[col]['std']
    
    target_vec = np.array([normalize(current_params[col], col) for col in features])
    
    distances = []
    
    # Búsqueda Rolling (Ventana Deslizante) sobre los datos históricos
    # Iteramos día por día calculando la "distancia" del bloque de 30 días que termina en ese día
    # Esto es computacionalmente más intenso pero exacto para lo que pide el usuario
    
    # Optimización: Usar rolling mean del dataframe histórico
    df_rolling = df_daily.rolling(window=current_window_days).mean().dropna()
    
    for date, row in df_rolling.iterrows():
        hist_vec = np.array([normalize(row[col], col) for col in features])
        dist = np.linalg.norm(target_vec - hist_vec)
        distances.append({'date': date, 'distance': dist})
        
    distances.sort(key=lambda x: x['distance'])
    return distances[:5]

def get_market_regime_timeranges():
    pairs = get_watchlist()
    df_index = build_market_index(pairs)
    
    if df_index is None:
        print("[!] Error crítico: No se pudieron cargar datos.")
        return None
        
    matches = find_similar_regimes(df_index)
    
    timeranges = []
    print("\n[ANALISTA] Periodos Espejo Encontrados:")
    
    used_dates = []
    best_match = None

    for match in matches:
        if len(timeranges) >= 3: break
        
        center_date = match['date']
        
        # Evitar overlap
        overlap = False
        for ud in used_dates:
            if abs((center_date - ud).days) < 25:
                overlap = True
                break
        if overlap: continue
        
        # Lógica de Rango:
        # center_date es el FIN del periodo espejo (porque usamos rolling window que fecha al final)
        # Queremos: [Inicio Espejo] -> [Fin Espejo] + 30 Días Futuros (Validación Histórica)
        # Inicio Espejo = center_date - 30 días
        # Fin Espejo = center_date
        # Fin Total = center_date + 30 días
        
        start_date_obj = center_date - timedelta(days=30)
        end_date_obj = center_date + timedelta(days=30)
        
        start_str = start_date_obj.strftime("%Y%m%d")
        end_str = end_date_obj.strftime("%Y%m%d")
        
        tr = f"{start_str}-{end_str}"
        timeranges.append(tr)
        used_dates.append(center_date)
        
        if best_match is None:
            best_match = {
                "inicio": start_str,
                "fin": end_str,
                "score": match['distance']
            }

        print(f"   > Fecha: {center_date.strftime('%Y-%m-%d')} | Dist: {match['distance']:.4f} --> {tr}")
        
    # Guardar resultado para Comandante
    if best_match:
        regimen_path = "user_data/regimen_actual.json"
        output_data = {
            "periodo_recomendado": {
                "inicio": best_match['inicio'],
                "fin": best_match['fin']
            },
            "regimen": "Espejo Histórico",
            "direccion": "Neutro", # Pendiente: Lógica de tendencia
            "meta": {
                "distance": best_match['score'],
                "generated": datetime.now().isoformat()
            }
        }
        try:
            with open(regimen_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)
            print(f"[ANALISTA] Resultado guardado en {regimen_path}")
        except Exception as e:
            print(f"[!] Error guardando json: {e}")

    return timeranges

if __name__ == "__main__":
    get_market_regime_timeranges()


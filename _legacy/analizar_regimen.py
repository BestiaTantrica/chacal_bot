import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def get_market_regime():
    data_path = "user_data/data/binance/futures/*.feather"
    files = glob.glob(data_path)
    
    if not files:
        return "UNKNOWN"
    
    # Tomamos BTC o ETH como referencia de mercado, o el promedio
    reference_files = [f for f in files if "BTC" in f or "ETH" in f]
    if not reference_files:
        reference_files = files[:3] # Fallback
        
    results = []
    
    for f in reference_files:
        try:
            df = pd.read_feather(f)
            if df.empty: continue
            
            # Calcular EMA 200
            df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
            
            last_close = df['close'].iloc[-1]
            last_ema = df['ema_200'].iloc[-1]
            
            # Determinar tendencia
            diff_pct = (last_close - last_ema) / last_ema
            
            # Determinar volatilidad (ATR simplificado)
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr'] = df['tr'].rolling(window=14).mean()
            df['atr_pct'] = df['atr'] / df['close']
            
            last_vol = df['atr_pct'].iloc[-1]
            
            results.append({
                'trend': 'BEARISH' if last_close < last_ema else 'BULLISH',
                'strength': abs(diff_pct),
                'volatility': last_vol
            })
        except Exception as e:
            print(f"Error analizando {f}: {e}")
            
    if not results:
        return "LATERAL_NORMAL"
        
    # Consenso
    bearish_count = len([r for r in results if r['trend'] == 'BEARISH'])
    avg_vol = np.mean([r['volatility'] for r in results])
    
    regime = ""
    if bearish_count > len(results) / 2:
        regime = "BEARISH_TREND"
    else:
        regime = "BULLISH_TREND"
        
    if avg_vol > 0.02: # Umbral de alta volatilidad
        regime = "ALTA_VOLATILIDAD_NOTICIAS"
    elif avg_vol < 0.005:
        regime = "LATERAL_RANGO_ACUMULACION"
        
    return regime

if __name__ == "__main__":
    print(get_market_regime())

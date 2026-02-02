"""
Análisis de Correlación con BTC - Pares Freqtrade
Seleccionar 6-8 pares óptimos para estrategia Chacal
"""

import sys
import codecs
# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Pares actuales en config
CURRENT_PAIRS = [
    "BTC/USDT:USDT",
    "ETH/USDT:USDT",
    "SOL/USDT:USDT",
    "BNB/USDT:USDT",
    "XRP/USDT:USDT",
    "ADA/USDT:USDT",
    "DOGE/USDT:USDT",
    "AVAX/USDT:USDT",
    "LINK/USDT:USDT",
    "DOT/USDT:USDT"
]

def get_binance_klines(symbol, interval='1d', limit=30):
    """Obtener velas de Binance"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol.replace('/USDT:USDT', 'USDT').replace('/', ''),
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 
        'volume', 'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['quote_volume'] = df['quote_volume'].astype(float)
    
    return df

def analyze_pairs():
    """Analizar todos los pares y calcular métricas"""
    print("🔍 Analizando pares...")
    
    # Obtener datos de BTC como referencia
    btc_data = get_binance_klines("BTCUSDT")
    btc_returns = btc_data['close'].pct_change().dropna()
    
    results = []
    
    for pair in CURRENT_PAIRS:
        if 'BTC' in pair:
            # BTC tiene correlación perfecta consigo mismo
            results.append({
                'pair': pair,
                'correlation': 1.0,
                'avg_volume_24h': btc_data['quote_volume'].mean(),
                'volatility': btc_returns.std(),
                'score': 100
            })
            continue
            
        try:
            symbol = pair.replace('/USDT:USDT', 'USDT').replace('/', '')
            data = get_binance_klines(symbol)
            
            # Calcular retornos
            returns = data['close'].pct_change().dropna()
            
            # Correlación con BTC (últimos 30 días)
            correlation = returns.corr(btc_returns)
            
            # Volumen promedio 24h (en USDT)
            avg_volume = data['quote_volume'].mean()
            
            # Volatilidad
            volatility = returns.std()
            
            # Score compuesto (correlación 70%, volumen 20%, baja volatilidad 10%)
            volume_score = min(avg_volume / 500_000_000, 1.0) * 100  # normalizar a $500M
            volatility_score = max(0, 100 - (volatility * 1000))  # penalizar alta volatilidad
            
            score = (correlation * 70) + (volume_score * 0.20) + (volatility_score * 0.10)
            
            results.append({
                'pair': pair,
                'correlation': round(correlation, 3),
                'avg_volume_24h': round(avg_volume / 1_000_000, 2),  # en millones
                'volatility': round(volatility, 4),
                'score': round(score, 2)
            })
            
            print(f"✅ {pair}: Corr={correlation:.3f}, Vol=${avg_volume/1e6:.0f}M")
            
        except Exception as e:
            print(f"❌ Error con {pair}: {e}")
            results.append({
                'pair': pair,
                'correlation': 0,
                'avg_volume_24h': 0,
                'volatility': 999,
                'score': 0
            })
    
    return pd.DataFrame(results).sort_values('score', ascending=False)

if __name__ == "__main__":
    print("=" * 60)
    print("ANÁLISIS DE PARES - PROTOCOLO DARWIN")
    print("=" * 60)
    print()
    
    df = analyze_pairs()
    
    print("\n" + "=" * 60)
    print("RANKING DE PARES (ordenado por score)")
    print("=" * 60)
    print(df.to_string(index=False))
    
    # Seleccionar top 6-8 con correlación > 0.7
    selected = df[df['correlation'] > 0.7].head(8)
    
    print("\n" + "=" * 60)
    print("PARES SELECCIONADOS (Top 6-8 con correlación >0.7)")
    print("=" * 60)
    print(selected[['pair', 'correlation', 'avg_volume_24h']].to_string(index=False))
    
    print("\n✅ Pares a usar en config:")
    for pair in selected['pair']:
        print(f'    "{pair}",')
    
    print("\n🗑️ Pares descartados:")
    rejected = df[~df['pair'].isin(selected['pair'])]
    for _, row in rejected.iterrows():
        print(f"    {row['pair']} (corr={row['correlation']}, vol=${row['avg_volume_24h']}M)")

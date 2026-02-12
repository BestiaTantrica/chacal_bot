import ccxt
import pandas as pd
from datetime import datetime
import os

def descargar_y_analizar_near():
    print("Descargando data de NEAR de Binance...")
    exchange = ccxt.binance({'options': {'defaultType': 'swap'}})
    symbol = 'NEAR/USDT'
    timeframe = '5m'
    
    # Obtener últimas 1000 velas (~3.5 días)
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=1000)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    # Horas Mágicas (UTC): 08:00-10:00 y 13:30-17:30
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    
    is_magic = (
        ((df['hour'] >= 8) & (df['hour'] < 10)) | 
        ((df['hour'] == 13) & (df['minute'] >= 30)) |
        ((df['hour'] >= 14) & (df['hour'] < 17)) |
        ((df['hour'] == 17) & (df['minute'] <= 30))
    )
    
    magic_df = df[is_magic]
    vol_mean_magic = magic_df['volume'].mean()
    vol_mean_total = df['volume'].mean()
    v_factor_calculado = vol_mean_magic / vol_mean_total if vol_mean_total > 0 else 0
    
    print(f"\nANÁLISIS DE MERCADO REAL (Últimos 3 días):")
    print(f"Símbolo: {symbol}")
    print(f"Volumen Promedio Total: {vol_mean_total:.2f}")
    print(f"Volumen Promedio Horas Mágicas: {vol_mean_magic:.2f}")
    print(f"V_FACTOR IMPLÍCITO (Promedio): {v_factor_calculado:.3f}")
    
    print("\nCONCLUSIÓN TÉCNICA:")
    if v_factor_calculado < 2.0:
        print(f"El v_factor real del promedio ({v_factor_calculado:.2f}) está por debajo de nuestro gatillo (2.772).")
        print("Esto confirma que nuestro v_factor de 2.772 BUSCA SOLO PICOS (Spikes) de volumen.")
    
    # Simulación rápida de gatillo
    spikes = df[df['volume'] > (vol_mean_total * 2.772)]
    print(f"Gatillos detectados con v_factor 2.772: {len(spikes)} en las últimas 1000 velas.")

if __name__ == "__main__":
    descargar_y_analizar_near()

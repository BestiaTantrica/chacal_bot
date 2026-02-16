import ccxt
import pandas as pd
from datetime import datetime, timezone

PAIRS = {
    'BTC/USDT': 4.660,
    'ETH/USDT': 5.769,
    'SOL/USDT': 5.386,
    'BNB/USDT': 3.378,
    'XRP/USDT': 5.133,
    'ADA/USDT': 3.408
}

def analizar_mercado():
    print(f"descargando data de binance para {len(PAIRS)} pares...")
    exchange = ccxt.binance({'options': {'defaultType': 'swap'}})
    
    for symbol, v_factor in PAIRS.items():
        print(f"\n--- ANALIZANDO {symbol} (v_factor: {v_factor}) ---")
        try:
            # Obtener últimas 1000 velas de 5m (~3.5 días)
            ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=1000)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            
            # Calcular media móvil de volumen (20 periodos)
            df['volume_mean'] = df['volume'].rolling(window=20).mean()
            
            # Calcular price_change
            df['price_change'] = (df['close'] - df['open']) / df['open']
            
            # Detectar Spikes
            # Condición: Volumen > Media * v_factor
            spikes = df[df['volume'] > (df['volume_mean'] * v_factor)]
            
            print(f"Total Velas: {len(df)}")
            print(f"Spikes Detectados (Volumen > Media * {v_factor}): {len(spikes)}")
            
            if len(spikes) > 0:
                print("Últimos 5 spikes Detalles:")
                # Mostrar fecha, volumen, media, y cambio de precio (%)
                debug_df = spikes[['date', 'volume', 'volume_mean', 'price_change']].tail(5).copy()
                debug_df['price_change_%'] = debug_df['price_change'] * 100
                print(debug_df[['date', 'volume', 'volume_mean', 'price_change_%']])
                
                # Verificar si alguno cumplió ALSO price_change > 0.4% o < -0.4%
                valid_entries = spikes[abs(spikes['price_change']) > 0.004]
                print(f" -> DE ESTOS, {len(valid_entries)} CUMPLIERON GATILLO DE PRECIO (>0.4%):")
                if len(valid_entries) > 0:
                    print(valid_entries[['date', 'price_change']].tail(5))
            else:
                print(">> NINGÚN SPIKE DETECTADO. El mercado está muy tranquilo o el factor es muy alto.")
                
        except Exception as e:
            print(f"Error analizando {symbol}: {e}")

if __name__ == "__main__":
    analizar_mercado()

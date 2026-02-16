import ccxt
import pandas as pd
from datetime import datetime
import os

# Valores certificados de la auditoría forense
VALORES_CERTIFICADOS = {
    "BTC/USDT": 4.66,
    "ETH/USDT": 5.769,
    "SOL/USDT": 5.386,
    "BNB/USDT": 3.378,
    "XRP/USDT": 5.133,
    "ADA/USDT": 3.408,
    "DOGE/USDT": 5.795,
    "AVAX/USDT": 5.692,
    "LINK/USDT": 5.671,
    "DOT/USDT": 5.671,
    "SUI/USDT": 5.051,
    "NEAR/USDT": 2.772
}

def analizar_flota_completa():
    print("ESCANEO MACRO DE VOLUMEN (BINANCE FUTURES)")
    print("-" * 60)
    exchange = ccxt.binance({'options': {'defaultType': 'swap'}})
    timeframe = '5m'
    
    resultados = []

    for symbol, v_cert in VALORES_CERTIFICADOS.items():
        try:
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
            
            vol_mean_total = df['volume'].mean()
            vol_mean_magic = df[is_magic]['volume'].mean()
            v_ratio_promedio = vol_mean_magic / vol_mean_total if vol_mean_total > 0 else 0
            
            # Detectar cuántas veces se disparó el gatillo real en 3 días
            gatillos = len(df[df['volume'] > (vol_mean_total * v_cert)])
            
            resultados.append({
                "Par": symbol,
                "v_Cert": v_cert,
                "Ratio": round(v_ratio_promedio, 2),
                "Gatillos": gatillos
            })
            print(f"OK {symbol}: Ratio {v_ratio_promedio:.2f} | Gatillos: {gatillos} ({v_cert})")
            
        except Exception as e:
            print(f"ERROR en {symbol}: {str(e)}")

    df_res = pd.DataFrame(resultados)
    print("\n" + "="*60)
    print("RESUMEN DE FLOTA CERTIFICADA")
    print("="*60)
    print(df_res.to_string(index=False))
    print("="*60)

if __name__ == "__main__":
    analizar_flota_completa()

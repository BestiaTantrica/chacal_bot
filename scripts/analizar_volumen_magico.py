import pandas as pd
import os

def analizar_volumen_magico_feather(pair_file):
    futures_path = "c:/Freqtrade/user_data/data/binance/futures"
    data_path = os.path.join(futures_path, pair_file)
    
    if not os.path.exists(data_path):
        print(f"Error: No se encontró data en {data_path}")
        return

    try:
        df = pd.read_feather(data_path)
    except Exception as e:
        print(f"Error leyendo feather: {e}")
        return
    
    # Adaptar nombres de columnas si es necesario (freqtrade feather suele tener date, open, high, low, close, volume)
    # Freqtrade utiliza epoch para date en algunos formatos, convertimos
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
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
    
    print(f"Analizando {pair_file}:")
    print(f"  Volumen Promedio Total: {vol_mean_total:.2f}")
    print(f"  Volumen Promedio Horas Mágicas: {vol_mean_magic:.2f}")
    print(f"  V_FACTOR IMPLÍCITO (Ratio): {v_factor_calculado:.3f}")
    print("-" * 30)

if __name__ == "__main__":
    # Testeando con pares disponibles
    pares_a_testear = [
        "BTC_USDT_USDT-5m-futures.feather",
        "SOL_USDT_USDT-5m-futures.feather",
        "DOT_USDT_USDT-5m-futures.feather",
        "ADA_USDT_USDT-5m-futures.feather"
    ]
    
    for p in pares_a_testear:
        analizar_volumen_magico_feather(p)

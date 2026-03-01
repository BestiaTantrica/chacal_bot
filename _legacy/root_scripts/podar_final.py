import pandas as pd
import pathlib

# --- CONFIGURACIÓN CHACAL V4 ---
# Horas Mágicas (UTC)
MAGIC_HOURS = [
    {"start": (8, 0), "end": (10, 0)},     # Londres
    {"start": (13, 30), "end": (17, 30)}   # NY
]
WARMUP_PERIODS_MINUTES = 60
# Rutas relativas al volumen de Docker/Server
DATA_DIR = pathlib.Path("/home/ec2-user/chacal_bot/user_data/data/binance/futures_backup/futures")
OUTPUT_DIR = pathlib.Path("/home/ec2-user/chacal_bot/user_data/data/binance/futures")

def segmentar():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(DATA_DIR.glob("*-5m-futures.feather"))
    print(f"Procesando {len(files)} archivos en {DATA_DIR}...")
    
    for f in files:
        try:
            df = pd.read_feather(f)
            df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True)
            
            mask = pd.Series(False, index=df.index)
            df_mins = df['date'].dt.hour * 60 + df['date'].dt.minute
            
            for slot in MAGIC_HOURS:
                # Inicio con Warmup
                start_min = slot["start"][0] * 60 + slot["start"][1] - WARMUP_PERIODS_MINUTES
                end_min = slot["end"][0] * 60 + slot["end"][1]
                
                # Mascara de tiempo
                if start_min < 0:
                    mask |= (df_mins >= (1440 + start_min)) | (df_mins <= end_min)
                else:
                    mask |= (df_mins >= start_min) & (df_mins <= end_min)
            
            # Filtro Fin de Semana (Sábado=5, Domingo=6)
            mask &= (df['date'].dt.dayofweek < 5)
            
            df_surgical = df[mask].reset_index(drop=True)
            
            # Guardar en formato Feather para Freqtrade
            output_path = OUTPUT_DIR / f.name
            df_surgical.to_feather(output_path)
            print(f"Done: {f.name} -> {len(df_surgical)} velas.")
        except Exception as e:
            print(f"Error en {f.name}: {e}")

if __name__ == '__main__':
    segmentar()

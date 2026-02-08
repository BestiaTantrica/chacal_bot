import pandas as pd
import pathlib
import datetime

# --- CONFIGURACIÓN DE SEGMENTACIÓN ---
MAGIC_HOURS = [
    {"start": (8, 0), "end": (10, 0)},     # Apertura Londres (05:00-07:00 Local)
    {"start": (13, 30), "end": (17, 30)}   # Apertura NY (10:30-14:30 Local)
]
WARMUP_PERIODS = 60 # 60 minutos de buffer para indicadores antes de la ventana

DATA_DIR = pathlib.Path("user_data/data/binance/futures_backup")
OUTPUT_DIR = pathlib.Path("user_data/data/binance/futures")

def segmentar_moneda(filepath):
    print(f"Segmentando {filepath.name}...")
    df = pd.read_feather(filepath)
    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True)
    
    # Máscara de segmentación
    mask = pd.Series(False, index=df.index)
    
    for slot in MAGIC_HOURS:
        # Convertir a minutos para comparación fácil
        start_min = slot["start"][0] * 60 + slot["start"][1]
        end_min = slot["end"][0] * 60 + slot["end"][1]
        
        # Calcular inicio real con warmup
        warmup_start_min = start_min - WARMUP_PERIODS
        
        df_mins = df['date'].dt.hour * 60 + df['date'].dt.minute
        
        # Caso especial si cruza medianoche (no es nuestro caso pero por robustez)
        if warmup_start_min < 0:
            mask |= (df_mins >= (1440 + warmup_start_min)) | (df_mins <= end_min)
        else:
            mask |= (df_mins >= warmup_start_min) & (df_mins <= end_min)
            
    df_surgical = df[mask].copy()
    
    # Guardar en nuevo directorio
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df_surgical.to_feather(OUTPUT_DIR / filepath.name)
    print(f"Done: {len(df)} -> {len(df_surgical)} velas.")

if __name__ == "__main__":
    for f in DATA_DIR.glob("*-1m-futures.feather"):
        segmentar_moneda(f)

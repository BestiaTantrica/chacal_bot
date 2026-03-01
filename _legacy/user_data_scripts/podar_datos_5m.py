import pandas as pd
import pathlib
import datetime

# --- CONFIGURACIÓN DE SEGMENTACIÓN ---
# PROTOCOLO CHACAL V4: Solo nos interesan las aperturas.
# Las Horas Mágicas son las mismas independientemente del timeframe.
MAGIC_HOURS = [
    {"start": (8, 0), "end": (10, 0)},     # Apertura Londres (05:00-07:00 Local)
    {"start": (13, 30), "end": (17, 30)}   # Apertura NY (10:30-14:30 Local)
]

# BUFFER DE SEGURIDAD
# Para 5m, necesitamos menos velas para el mismo warmup de tiempo, pero mantenemos
# un margen generoso para que los indicadores (EMA, RSI) se estabilicen.
# 60 minutos = 12 velas de 5m.
WARMUP_PERIODS_MINUTES = 60 

DATA_DIR = pathlib.Path("user_data/data/binance/futures_backup")
OUTPUT_DIR = pathlib.Path("user_data/data/binance/futures")

def segmentar_moneda_5m(filepath):
    print(f"Segmentando (5m) {filepath.name}...")
    try:
        df = pd.read_feather(filepath)
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
        return

    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True)
    
    # Máscara de segmentación con lógica booleana vectorial
    mask = pd.Series(False, index=df.index)
    
    for slot in MAGIC_HOURS:
        # 1. Convertir Horas Mágicas a minuto del día (0-1439)
        start_min_day = slot["start"][0] * 60 + slot["start"][1]
        end_min_day = slot["end"][0] * 60 + slot["end"][1]
        
        # 2. Calcular inicio con Warmup
        # Restamos los 60 minutos de warmup al tiempo de inicio
        warmup_start_min_day = start_min_day - WARMUP_PERIODS_MINUTES
        
        # 3. Extraer el minuto del día de cada vela en el DataFrame
        df_mins = df['date'].dt.hour * 60 + df['date'].dt.minute
        
        # 4. Aplicar máscara
        if warmup_start_min_day < 0:
            # Caso cruce de medianoche (ej: si el warmup empujara al día anterior)
            # (1440 + negativo) = hora real del día anterior
            mask |= (df_mins >= (1440 + warmup_start_min_day)) | (df_mins <= end_min_day)
        else:
            # Caso normal
            mask |= (df_mins >= warmup_start_min_day) & (df_mins <= end_min_day)
            
    df_surgical = df[mask].copy()
    
    if df_surgical.empty:
        print(f"ADVERTENCIA: {filepath.name} quedó vacío tras la poda.")
        return

    # Guardar en Directorio Quirúrgico
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Aseguramos que el nombre conserve el formato correcto
    # Freqtrade espera: PAR_TIMEFRAME_TIPOMERCADO.feather
    output_path = OUTPUT_DIR / filepath.name
    
    df_surgical.reset_index(drop=True).to_feather(output_path)
    print(f"Done: {len(df)} -> {len(df_surgical)} velas. Guardado en {output_path}")

if __name__ == "__main__":
    # Buscar solo archivos de 5 minutos
    files = list(DATA_DIR.glob("*-5m-futures.feather"))
    
    if not files:
        print(f"No se encontraron archivos de 5m en {DATA_DIR}")
    else:
        print(f"Procesando {len(files)} archivos de 5m...")
        for f in files:
            segmentar_moneda_5m(f)

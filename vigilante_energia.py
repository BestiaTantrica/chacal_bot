import os
import sqlite3
import time
import subprocess
from datetime import datetime, timezone

# Configuración
CHECK_INTERVAL = 300  # 5 minutos (más preciso)
DBS = [
    '/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite'
]

def has_open_trades():
    for db in DBS:
        if not os.path.exists(db):
            continue
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM trades WHERE is_open=1")
            count = c.fetchone()[0]
            conn.close()
            if count > 0:
                return True
        except Exception as e:
            print(f"Error checking DB {db}: {e}")
            continue
    return False

def log(msg):
    # Log en UTC para coincidir con el server
    print(f"[{datetime.now(timezone.utc)}] [VIGILANTE-ENERGIA] {msg}")

if __name__ == "__main__":
    log("Iniciando Vigilante de Energía v2 (UTC-Mode)...")
    while True:
        now_utc = datetime.now(timezone.utc)
        
        # HORARIOS DE CHEQUEO (UTC)
        # 07:15 ART = 10:15 UTC
        # 14:45 ART = 17:45 UTC
        
        # Ventanas de "Check & Kill":
        # 1. Después de las 10:15 UTC y antes de las 13:25 UTC (Apertura NY)
        # 2. Después de las 17:45 UTC y antes de las 07:55 UTC (Apertura Londres mañana)
        
        is_dead_zone = False
        
        # Rango 1: [10:15 - 13:25] UTC
        if (now_utc.hour == 10 and now_utc.minute >= 15) or (now_utc.hour > 10 and now_utc.hour < 13) or (now_utc.hour == 13 and now_utc.minute < 25):
            is_dead_zone = True
            
        # Rango 2: [17:45 - 07:55] UTC (Pasa por medianoche)
        if (now_utc.hour >= 18) or (now_utc.hour < 7) or (now_utc.hour == 17 and now_utc.minute >= 45) or (now_utc.hour == 7 and now_utc.minute < 55):
            is_dead_zone = True

        if is_dead_zone and not os.path.exists('/tmp/NO_APAGAR'):
            if not has_open_trades():
                log("Cero trades abiertos en zona muerta. Ejecutando APAGADO...")
                # subprocess.run(["sudo", "shutdown", "-h", "now"])
                # Por ahora solo log para no matar la sesión del user si está probando
                log("Comando a ejecutar: sudo shutdown -h now")
            else:
                log("Zona muerta detectada pero hay TRADES ABIERTOS. Manteniendo energía...")
        
        time.sleep(CHECK_INTERVAL)

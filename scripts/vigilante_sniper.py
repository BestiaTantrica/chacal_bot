import os
import sqlite3
import time
import subprocess
from datetime import datetime, timezone

# Protocolo Sniper V4 - Horarios Hyperopt (UTC)
# LONDRES: 08:00 - 10:00 (Apertura y primera volatilidad)
# NEW YORK: 13:30 - 17:30 (Apertura y cierre sesión oficial)

CHECK_INTERVAL = 300
DBS = [
    '/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite'
]

def has_open_trades():
    for db in DBS:
        if not os.path.exists(db): continue
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM trades WHERE is_open=1")
            count = c.fetchone()[0]
            conn.close()
            if count > 0: return True
        except: continue
    return False

def log(msg):
    print(f"[{datetime.now(timezone.utc)}] [VIGILANTE-ENERGIA] {msg}", flush=True)

if __name__ == "__main__":
    log("Vigilante Sniper V4 Activo (Sincronizado con Hyperopt)")
    while True:
        now_utc = datetime.now(timezone.utc)
        
        # DEFINICIÓN DE ZONAS MUERTAS (Fuera de Hyperopt Windows)
        # Horas Mágicas: [08-10] y [13:30-17:30]
        
        is_magic_hour = False
        if (now_utc.hour >= 8 and now_utc.hour < 10):
            is_magic_hour = True
        elif (now_utc.hour == 13 and now_utc.minute >= 30) or (now_utc.hour > 13 and now_utc.hour < 17) or (now_utc.hour == 17 and now_utc.minute <= 30):
            is_magic_hour = True
            
        if not is_magic_hour and not os.path.exists('/tmp/NO_APAGAR'):
            if not has_open_trades():
                log("Zona Muerta Detectada (Sin Trades). Ejecutando apagado de seguridad...")
                subprocess.run(["sudo", "shutdown", "-h", "now"])
            else:
                log("Zona Muerta Detectada pero hay TRADES ABIERTOS. Manteniendo energía.")
        
        time.sleep(CHECK_INTERVAL)

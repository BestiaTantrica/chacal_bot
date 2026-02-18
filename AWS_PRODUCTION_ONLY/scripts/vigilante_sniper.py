import os
import sqlite3
import time
import subprocess
from datetime import datetime, timezone, timedelta

# Protocolo Sniper V4 - Horarios Magicos (UTC)
# LONDRES: 08:00 - 10:00 
# NEW YORK: 13:30 - 17:30

CHECK_INTERVAL = 60 
BUFFER_MINUTES = 30 # Margen estricto solicitado

CONFIGS = [
    '/home/ec2-user/chacal_bot/user_data/config_alpha.json',
    '/home/ec2-user/chacal_bot/user_data/config_beta.json',
    '/home/ec2-user/chacal_bot/user_data/config_gamma.json',
    '/home/ec2-user/chacal_bot/user_data/config_delta.json'
]

DBS = [
    '/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite',
    '/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite'
]

def log(msg):
    log_path = "/home/ec2-user/chacal_bot/user_data/logs/vigilante.log"
    # Asegurar que el directorio existe para evitar el error previo
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"[{datetime.now(timezone.utc)}] [VIGILANTE] {msg}\n")
    print(f"[{datetime.now(timezone.utc)}] [VIGILANTE] {msg}", flush=True)

def has_open_trades():
    count = 0
    for db in DBS:
        if not os.path.exists(db): continue
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM trades WHERE is_open=1")
            res = c.fetchone()
            if res:
                count += res[0]
            conn.close()
        except: continue
    return count > 0

def check_magic_hours():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    minute = now_utc.minute
    
    in_window = False
    
    # Ventana 1: 08:00 - 10:00
    if (hour >= 8 and hour < 10):
        in_window = True
    # Ventana 2: 13:30 - 17:30
    elif (hour == 13 and minute >= 30) or (hour > 13 and hour < 17) or (hour == 17 and minute <= 30):
        in_window = True
        
    return in_window, now_utc

def main():
    log("Vigilante Sniper V4: Iniciando Guardiana Simplificada (Buffer 30min)")
    while True:
        in_window, now_utc = check_magic_hours()
        minute_of_day = now_utc.hour * 60 + now_utc.minute
        
        # Definir limites de cierre (Fin de ventana + Buffer)
        # 10:00 (600 min) + 30 = 630 min (10:30)
        # 17:30 (1050 min) + 30 = 1080 min (18:00)
        
        limit1 = 600 + BUFFER_MINUTES
        limit2 = 1050 + BUFFER_MINUTES
        
        # Determinar si estamos fuera de ventana y excedimos el buffer
        is_late = False
        if minute_of_day >= limit1 and minute_of_day < 810: # Gap entre 10:30 y 13:30
            is_late = True
        elif minute_of_day >= limit2 or minute_of_day < 480: # Despues de las 18:00 o antes de las 08:00
            is_late = True

        if not in_window and is_late:
            if not os.path.exists('/tmp/NO_APAGAR'):
                if has_open_trades():
                    log(f"FUERA DE TIEMPO ({now_utc.strftime('%H:%M')}). CERRANDO TRADES A MERCADO...")
                    
                    for i, config in enumerate(CONFIGS):
                        container = ["chacal_alpha", "chacal_beta", "chacal_gamma", "chacal_delta"][i]
                        subprocess.run(f"docker exec {container} freqtrade exit-positions -c {config}", shell=True)
                    
                    time.sleep(30) # Esperar ejecucion

                # Verificación Final y Apagado
                if not has_open_trades():
                    log("✅ Sistema limpio. Apagando instancia para proteger capital.")
                    subprocess.run(["sudo", "shutdown", "-h", "now"])
                else:
                    log("⚠️ ERROR: No se pudieron cerrar trades. Abortando apagado por seguridad.")
            else:
                log("Detectado /tmp/NO_APAGAR. Manteniendo sistema vivo.")
        
        elif not in_window:
            log(f"En zona de espera buffer ({now_utc.strftime('%H:%M')}). Esperando cierre natural.")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

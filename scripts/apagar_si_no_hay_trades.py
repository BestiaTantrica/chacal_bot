import os
import sqlite3
import subprocess
from datetime import datetime

# Configuración
DB_FILES = [
    "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite",
    "/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite",
    "/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite",
    "/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def check_open_trades():
    open_count = 0
    for db in DB_FILES:
        if os.path.exists(db):
            try:
                conn = sqlite3.connect(db)
                c = conn.cursor()
                c.execute("SELECT count(*) FROM trades WHERE is_open=1")
                count = c.fetchone()[0]
                conn.close()
                open_count += count
            except:
                pass
    return open_count

def main():
    log("Verificando actividad para apagado automático...")
    
    # 1. Chequear bandera manual
    if os.path.exists("/tmp/NO_APAGAR"):
        log("BANDERA MANUAL DETECTADA: Cancelando apagado.")
        return

    # 2. Chequear trades abiertos
    trades = check_open_trades()
    if trades > 0:
        log(f"ACTIVIDAD DETECTADA: {trades} trades abiertos. Cancelando apagado.")
        return

    # 3. Apagar si no hay nada
    log("SISTEMA OCIOSO. Iniciando secuencia de apagado...")
    subprocess.run(["sudo", "shutdown", "-h", "now"])

if __name__ == "__main__":
    main()

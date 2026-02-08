import os
import sqlite3
import time
import json
import urllib.request
from datetime import datetime

# --- CONFIGURACIÓN HUNTERS ---
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha.sqlite",
    "BETA": "user_data/tradesv3_beta.sqlite",
    "GAMMA": "user_data/tradesv3_gamma.sqlite",
    "DELTA": "user_data/tradesv3_delta.sqlite"
}
CONFIG_FILE = "user_data/config_alpha.json"

# Ventanas de APAGADO (Horas UTC donde queremos que el bot descanse si no hay trades)
# Turno 1 termina 11:30 UTC (08:30 ART)
# Turno 2 termina 17:30 UTC (14:30 ART)
OFF_WINDOWS = [11, 12, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4] 

def log(msg):
    print(f"[{datetime.now()}] [SENTINEL PEGASO] {msg}", flush=True)

def get_tg_credentials():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            tg = config.get('telegram', {})
            return tg.get('token'), tg.get('chat_id')
    except: return None, None

def send_telegram(msg):
    token, chat_id = get_tg_credentials()
    if not token: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"🐺 *SENTINELA PEGASO*\n\n{msg}", "parse_mode": "Markdown"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def count_open_trades():
    total_open = 0
    for name, path in DB_FILES.items():
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM trades WHERE is_open=1")
                total_open += c.fetchone()[0]
                conn.close()
            except: pass
    return total_open

def is_weekend():
    # 5 = Sábado, 6 = Domingo
    return datetime.utcnow().weekday() >= 5

def start_sentinel():
    log("Sentinela Pegaso V2.0 Multiventana Activo.")
    
    while True:
        now_utc = datetime.utcnow()
        
        # 1. FIN DE SEMANA = HYPEROPT (No apagar)
        if is_weekend():
            log("Fin de semana: Modo Calibración. Sistemas Online.")
            time.sleep(3600)
            continue

        # 2. EVALUAR VENTANAS DE APAGADO
        if now_utc.hour in OFF_WINDOWS:
            open_count = count_open_trades()
            
            if open_count > 0:
                log(f"Ventana de ahorro activa, pero hay {open_count} trades abiertos. Postergando...")
                # Solo avisar una vez por hora para no spamear
                if now_utc.minute < 10:
                    send_telegram(f"⏳ *Cierre postergado:* {open_count} presas en combate. Esperando a que terminen para ahorrar energía.")
                time.sleep(600) # Re-evaluar en 10 min
            else:
                log("Sin trades abiertos en zona muerta. Iniciando Retirada Segura.")
                send_telegram("💤 *Manada a Cubierto:* Sin trades abiertos. Apagando instancia para maximizar ahorro. Nos vemos en la próxima ventana mágica.")
                time.sleep(5)
                os.system("sudo shutdown -h now")
        
        time.sleep(300) # El pulso del centinela: cada 5 minutos

if __name__ == "__main__":
    start_sentinel()

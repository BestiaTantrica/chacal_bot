import os
import sqlite3
import time
import json
import urllib.request
from datetime import datetime

# --- CONFIGURACIÓN ---
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha.sqlite",
    "BETA": "user_data/tradesv3_beta.sqlite",
    "GAMMA": "user_data/tradesv3_gamma.sqlite",
    "DELTA": "user_data/tradesv3_delta.sqlite"
}
CONFIG_FILE = "user_data/config_alpha.json"
END_HOUR_UTC = 14  # 14:00 UTC es el fin del turno
CHECK_INTERVAL = 900 # Reintentar cada 15 minutos si hay trades abiertos

def log(msg):
    print(f"[{datetime.now()}] [SENTINEL] {msg}", flush=True)

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
    return datetime.utcnow().weekday() >= 5

def start_sentinel():
    log("Sentinela Pegaso activo. Vigilando ventana de cierre...")
    
    while True:
        now_utc = datetime.utcnow()
        
        # El fin de semana NO apagamos (Tiempo de Hyperopt)
        if is_weekend():
            log("Fin de semana detectado: Modo Hyperopt activo. No se apagará el sistema.")
            time.sleep(3600) # Dormir 1 hora
            continue

        # Entre semana, revisar si pasó la hora de cierre
        if now_utc.hour >= END_HOUR_UTC:
            open_count = count_open_trades()
            
            if open_count > 0:
                log(f"Imposible apagar: {open_count} trades abiertos. Reintentando en 15 min.")
                send_telegram(f"⚠️ *Atención:* Hay {open_count} trades abiertos. Postergando apagado para proteger el capital.")
                time.sleep(CHECK_INTERVAL)
            else:
                log("Cierre seguro confirmado. Iniciando apagado de instancia AWS.")
                send_telegram("💤 *Misión Cumplida:* Sin operaciones abiertas. Apagando instancia para ahorro de horas AWS. Nos vemos en el próximo horario mágico.")
                time.sleep(5)
                # COMANDO DE APAGADO (Requiere sudo sin password para shutdown)
                os.system("sudo shutdown -h now")
        
        time.sleep(600) # Revisar cada 10 minutos si todavía no es la hora

if __name__ == "__main__":
    start_sentinel()

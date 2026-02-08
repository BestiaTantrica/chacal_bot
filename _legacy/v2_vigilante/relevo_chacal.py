import os
import time
import sqlite3
import datetime
import subprocess

# --- CONFIGURACIÓN (UTC) ---
# ART (UTC-3)
# 05:00 - 07:00 ART -> 08:00 - 10:00 UTC
# 10:30 - 12:30 ART -> 13:30 - 15:30 UTC

SCHEDULE = [
    {"start": (8, 0), "end": (10, 0)},
    {"start": (13, 30), "end": (15, 30)}
]

BOTS = ["chacal_alpha", "chacal_beta", "chacal_gamma", "chacal_delta"]

def log(msg):
    print(f"[{datetime.datetime.now()}] [RELEVO] {msg}", flush=True)

def is_in_magic_hours():
    now = datetime.datetime.utcnow()
    current_time = (now.hour, now.minute)
    
    for slot in SCHEDULE:
        s = slot["start"]
        e = slot["end"]
        # Convert tuples to minutes
        curr_min = current_time[0] * 60 + current_time[1]
        start_min = s[0] * 60 + s[1]
        end_min = e[0] * 60 + e[1]
        
        if start_min <= curr_min < end_min:
            return True
            
    return False

def has_open_trades(bot_name):
    # Map bot name to db file using standard path structure
    suffix = bot_name.replace("chacal_", "")
    db_path = f"user_data/tradesv3_{suffix}.sqlite"
    
    if not os.path.exists(db_path):
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM trades WHERE is_open=1")
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        log(f"Error checkeando trades de {bot_name}: {e}")
        # Fail safe: if we can't check DB, assume it has trades so we don't kill it
        return True 

def is_container_running(bot_name):
    status_cmd = f"docker inspect -f '{{{{.State.Running}}}}' {bot_name}"
    try:
        out = subprocess.check_output(status_cmd, shell=True).decode().strip()
        return out == 'true'
    except:
        return False

def manage_bots():
    should_entry_period = is_in_magic_hours()
    
    for bot in BOTS:
        running = is_container_running(bot)
        has_trades = has_open_trades(bot)
        
        # LOGIC MATRIX:
        # 1. Magic Hour = YES -> Ensure Running (for entry)
        # 2. Magic Hour = NO  -> 
        #       If Trades = YES -> Ensure Running (for exit)
        #       If Trades = NO  -> Ensure Stopped (save resources)
        
        should_be_up = should_entry_period or has_trades
        
        if should_be_up:
            if not running:
                reason = "Magic Hour" if should_entry_period else "Open Trades Rescue"
                log(f"STARTING {bot} ({reason})")
                os.system(f"docker start {bot}")
        else:
            if running:
                log(f"STOPPING {bot} (Outside window & No trades)")
                os.system(f"docker stop {bot}")

if __name__ == "__main__":
    log("Iniciando Relevo Chacal V3.1 (Rescue Mode Enabled)")
    while True:
        try:
            manage_bots()
        except Exception as e:
            log(f"Error en loop principal: {e}")
        time.sleep(60)

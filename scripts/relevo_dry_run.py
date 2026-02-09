#!/bin/bash
# Relevo Chacal v4 - Dry Run Edition
# Sistema de auto-gestión de bots durante Horas Mágicas

import os
import time
import sqlite3
import datetime
import subprocess

# Horas Mágicas (UTC)
MAGIC_HOURS = [
    {"start": (8, 0), "end": (10, 0)},     # Londres
    {" start": (13, 30), "end": (17, 30)}   # NY
]

BOTS = ["alpha_dry", "beta_dry", "gamma_dry", "delta_dry"]

def log(msg):
    print(f"[{datetime.datetime.now()}] [RELEVO-DRY] {msg}", flush=True)

def is_in_magic_hours():
    now = datetime.datetime.utcnow()
    current_time = (now.hour, now.minute)
    
    for slot in MAGIC_HOURS:
        s = slot["start"]
        e = slot["end"]
        curr_min = current_time[0] * 60 + current_time[1]
        start_min = s[0] * 60 + s[1]
        end_min = e[0] * 60 + e[1]
        
        if start_min <= curr_min < end_min:
            return True
    return False

def has_open_trades(bot_name):
    suffix = bot_name.replace("_dry", "")
    db_path = f"user_data/tradesv3_{suffix}_dry.sqlite"
    
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
        return True  # Fail-safe

def is_container_running(bot_name):
    try:
        out = subprocess.check_output(f"docker inspect -f '{{{{.State.Running}}}}' {bot_name}", shell=True).decode().strip()
        return out == 'true'
    except:
        return False

def manage_bots():
    in_magic_hours = is_in_magic_hours()
    
    for bot in BOTS:
        running = is_container_running(bot)
        has_trades = has_open_trades(bot)
        
        should_be_up = in_magic_hours or has_trades
        
        if should_be_up:
            if not running:
                reason = "Magic Hour" if in_magic_hours else "Open Trades Rescue"
                log(f"STARTING {bot} ({reason})")
                os.system(f"docker start {bot}")
        else:
            if running:
                log(f"STOPPING {bot} (Outside window & No trades)")
                os.system(f"docker stop {bot}")

if __name__ == "__main__":
    log("Iniciando Relevo Chacal v4 (Dry Run Edition)")
    while True:
        try:
            manage_bots()
        except Exception as e:
            log(f"Error en loop principal: {e}")
        time.sleep(60)

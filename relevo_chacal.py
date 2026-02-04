import os
import time
from datetime import datetime
import subprocess

# --- CONFIGURACIÓN DE HORARIOS (UTC) ---
# Hunters: 05:00 a 14:00 UTC
# Vigilantes: 14:00 a 05:00 UTC + Fines de semana
HUNTERS_START = 5
HUNTERS_END = 14

def log(msg):
    print(f"[{datetime.now()}] [RELEVO] {msg}")

def get_current_mode():
    now = datetime.utcnow()
    is_weekend = now.weekday() >= 5 # 5=Sábado, 6=Domingo
    hour = now.hour
    
    if is_weekend:
        return "VIGILANTES" # Fin de semana es 100% Vigilancia
    
    if HUNTERS_START <= hour < HUNTERS_END:
        return "HUNTERS"
    else:
        return "VIGILANTES"

def switch_mode(mode):
    log(f"Cambiando a modo: {mode}")
    if mode == "HUNTERS":
        # Apagar vigilantes, encender hunters
        os.system("docker stop chacal_epsilon chacal_zeta")
        os.system("docker start chacal_alpha chacal_beta chacal_gamma chacal_delta")
    else:
        # Apagar hunters, encender vigilantes
        os.system("docker stop chacal_alpha chacal_beta chacal_gamma chacal_delta")
        os.system("docker start chacal_epsilon chacal_zeta")

if __name__ == "__main__":
    current_mode = None
    log("Iniciando Orquestador de Relevos Chacal...")
    
    while True:
        target_mode = get_current_mode()
        if target_mode != current_mode:
            switch_mode(target_mode)
            current_mode = target_mode
        
        # Revisar cada 5 minutos
        time.sleep(300)

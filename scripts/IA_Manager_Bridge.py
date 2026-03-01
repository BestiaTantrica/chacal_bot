import os
import time
import requests
from datetime import datetime

# CONFIGURACIÓN PEGASO - PC LOCAL
LOG_FILE = "C:/Freqtrade/user_data/logs/freqtrade.log"
TELEGRAM_TOKEN = "8420746376:AAFbY0xOu5kRgOFjYcPwfmQ4_qN3vKoTRx4"
TELEGRAM_CHAT_ID = "6527908321"

KEYWORDS = ["buy", "sell", "exit", "entry", "error", "warning"]

# GLOSARIO TÉCNICO
GLOSSARY = {
    "ROI": "Retorno de Inversión (Target de salida)",
    "v-factor": "Factor de Volumetría (Sensibilidad)",
    "ADX": "Fuerza de Tendencia",
    "RSI": "Sobrecompra/Sobreventa",
    "Stoploss": "Seguro de Pérdida",
    "Long": "Operación al ALZA",
    "Short": "Operación a la BAJA"
}

def translate(text):
    for term, definition in GLOSSARY.items():
        if term in text:
            text = text.replace(term, f"{term} [{definition}]")
    return text

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🦅 [PEGASO IA SUPERVISOR]\n\n{message}"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def monitor_logs():
    print(f"PEGASO IA Bridge Activo - Monitoreando {LOG_FILE}...")
    
    if not os.path.exists(LOG_FILE):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        open(LOG_FILE, 'a').close()

    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            
            line_lower = line.lower()
            # FILTRO ANTI-SPAM RADICAL (PEGASO PRO)
            # Ignorar todo lo que sea ruido técnico de loop o análisis preventivo
            noise_filters = [
                "entry trigger", 
                "loop analysis", 
                "populating exit signals", 
                "populating entry signals",
                "found no enter signals",
                "throttling with",
                "create_trade for pair"
            ]
            
            if any(noise in line_lower for noise in noise_filters):
                continue

            # Solo nos interesan acciones reales o problemas serios
            critical_keywords = ["buy", "sell", "exit", "error", "warning", "order"]
            if any(key in line_lower for key in critical_keywords):
                translated_line = translate(line).strip()
                # Enviar reporte procesado
                send_telegram(translated_line)
                
                with open("C:/Freqtrade/user_data/logs/ia_novedades.log", "a", encoding="utf-8") as out:
                    out.write(f"{datetime.now()} - {translated_line}\n")

if __name__ == "__main__":
    monitor_logs()

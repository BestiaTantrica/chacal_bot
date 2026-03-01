import time
import pickle
import json
import requests
import os
import glob

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8420746376:AAFbY0xOu5kRgOFjYcPwfmQ4_qN3vKoTRx4"
CHAT_ID = "6527908321"
RESULTS_DIR = "/freqtrade/user_data/hyperopt_results/"
CHECK_INTERVAL = 600  # 10 minutos

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram: {e}")

def get_latest_results():
    # Buscar el archivo .fthypt más reciente
    files = glob.glob(os.path.join(RESULTS_DIR, "*.fthypt"))
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        # Freqtrade moderno suele guardar en JSON, pero a veces usa Pickle
        with open(latest_file, 'r') as f:
            data = json.load(f)
        return data
    except:
        try:
            with open(latest_file, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            print(f"Error leyendo {latest_file}: {e}")
            return None

def monitor():
    last_epoch_count = 0
    print("Monitor Chacal V4 iniciado...")
    
    while True:
        data = get_latest_results()
        if data:
            results = data.get('results', [])
            current_count = len(results)
            
            if current_count > last_epoch_count:
                best = data.get('best_result', {})
                loss = data.get('best_loss', 0)
                
                msg = (
                    "🦅 *REPORTE CHACAL V4 - HYPEROPT*\n\n"
                    f"✅ *Épocas:* {current_count}/1000\n"
                    f"🏆 *Best Loss (Sharpe):* {loss:.4f}\n"
                    f"📊 *Trades:* {best.get('total_trades', 'N/A')}\n"
                    f"💰 *Profit:* {best.get('total_profit', 0)*100:.2f}%\n\n"
                    "🧪 *Parámetros Top:*\n"
                    f"• Trend Mult: {best.get('params_dict', {}).get('v_factor_mult_trend', 'N/A')}\n"
                    f"• Sideways Mult: {best.get('params_dict', {}).get('v_factor_mult_sideways', 'N/A')}\n"
                )
                send_telegram(msg)
                last_epoch_count = current_count
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()

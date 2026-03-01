import time
import pickle
import json
import requests
import os
import glob

TELEGRAM_TOKEN = "8420746376:AAFbY0xOu5kRgOFjYcPwfmQ4_qN3vKoTRx4"
RESULTS_DIR = "/freqtrade/user_data/hyperopt_results/"

def get_latest_results():
    files = glob.glob(os.path.join(RESULTS_DIR, "*.fthypt"))
    if not files: return None
    latest_file = max(files, key=os.path.getmtime)
    try:
        with open(latest_file, 'r') as f: return json.load(f)
    except:
        try:
            with open(latest_file, 'rb') as f: return pickle.load(f)
        except: return None

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown",
        "reply_markup": {"keyboard": [[{"text": "/datos"}]], "resize_keyboard": True}
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def handle_updates():
    offset = None
    print("Bot Chacal V4 V2 iniciado...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            if offset: url += f"?offset={offset}"
            r = requests.get(url, timeout=10).json()
            if not r.get("result"):
                time.sleep(2)
                continue
            
            for update in r["result"]:
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id", "")
                
                if text == "/datos" or text == "/start":
                    data = get_latest_results()
                    if not data:
                        send_message(chat_id, "❌ Sin datos aún. Cargando 365 días...")
                        continue
                    
                    best = data.get('best_result', {})
                    results = data.get('results', [])
                    loss = data.get('best_loss', 0)
                    
                    report = (
                        "🦅 *ESTADO CHACAL V4* 🦅\n\n"
                        f"✅ *Épocas:* {len(results)}/1000\n"
                        f"🏆 *Best Sharpe:* {-loss:.4f}\n"
                        f"📊 *Trades:* {best.get('total_trades', 'N/A')}\n"
                        f"💰 *Profit:* {best.get('total_profit', 0)*100:.2f}%\n"
                    )
                    send_message(chat_id, report)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    handle_updates()

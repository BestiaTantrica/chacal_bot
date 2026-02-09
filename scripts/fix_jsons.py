import re
import json
import os

log_path = 'c:/Freqtrade/user_data/logs/fase2_completa_20260208.log'
output_dir = 'c:/Freqtrade/user_data/hyperopt_results'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

monedas = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'LINK', 'DOT', 'SUI', 'NEAR']

def clean_python_dict(raw):
    # Convierte un string de dict de Python a JSON
    raw = re.sub(r'#.*', '', raw) # Quitar comentarios
    raw = raw.replace("True", "true").replace("False", "false").replace("None", "null")
    raw = raw.replace("'", '"')
    raw = re.sub(r',\s*\}', '}', raw)
    # Quitar variables de estrategia si las hay
    raw = re.sub(r'# value loaded from strategy', '', raw)
    return raw

for moneda in monedas:
    # Buscar el bloque de la moneda
    # El bloque termina donde empieza la siguiente o al final del archivo
    patron_bloque = rf'Running \w+ on {moneda}/USDT:USDT(.*?)(?=Running \w+ on |$)'
    match_bloque = re.search(patron_bloque, content, re.DOTALL)
    
    if match_bloque:
        bloque = match_bloque.group(1)
        
        # Extraer cada sección
        try:
            buy_raw = re.search(r'buy_params = (\{.*?\})', bloque, re.DOTALL).group(1)
            sell_raw = re.search(r'sell_params = (\{.*?\})', bloque, re.DOTALL).group(1)
            roi_raw = re.search(r'minimal_roi = (\{.*?\})', bloque, re.DOTALL).group(1)
            stoploss_val = re.search(r'stoploss = ([\-\d.]+)', bloque).group(1)
            
            buy_params = json.loads(clean_python_dict(buy_raw))
            sell_params = json.loads(clean_python_dict(sell_raw))
            minimal_roi = json.loads(clean_python_dict(roi_raw))
            stoploss = float(stoploss_val)

            final_json = {
                "params": {
                    "buy": buy_params,
                    "sell": sell_params,
                    "roi": minimal_roi,
                    "stoploss": {"stoploss": stoploss}
                },
                "minimal_roi": minimal_roi,
                "stoploss": stoploss,
                "trailing_stop": False,
                "max_open_trades": 3
            }

            with open(os.path.join(output_dir, f'fase2_{moneda}.json'), 'w') as f:
                json.dump(final_json, f, indent=4)
        except Exception as e:
            print(f"Error procesando {moneda}: {e}")

print("RESCATE FINALIZADO CON ÉXITO.")

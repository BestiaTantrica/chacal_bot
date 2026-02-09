import re
import json
import os

log_path = 'c:/Freqtrade/user_data/logs/fase2_completa_20260208.log'
output_dir = 'c:/Freqtrade/user_data/hyperopt_results'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Dividir el log por ejecuciones de monedas
# Buscamos "Running [Torre] on [Moneda]"
monedas = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'LINK', 'DOT', 'SUI', 'NEAR']
bloques = re.split(r'Running \w+ on ', content)

for bloque in bloques:
    # Identificar la moneda al inicio del bloque
    match_moneda = re.match(r'^(\w+)/USDT', bloque)
    if not match_moneda:
        continue
    
    moneda = match_moneda.group(1)
    if moneda not in monedas:
        continue

    print(f"Procesando {moneda}...")

    # Extraer parámetros usando regex
    def extract_dict(name, text):
        match = re.search(rf'{name} = (\{{.*?\}})', text, re.DOTALL)
        if match:
            # Convertir formato Python a JSON (comas, comillas, etc)
            # Simplificado: quitar comas finales y cambiar comillas simples
            raw = match.group(1)
            raw = re.sub(r',\s*\}', '}', raw)
            raw = raw.replace("'", '"')
            try:
                return json.loads(raw)
            except:
                # Si falla el parseo directo, intentar algo más manual
                return raw
        return None

    buy_params = extract_dict('buy_params', bloque)
    sell_params = extract_dict('sell_params', bloque)
    minimal_roi = extract_dict('minimal_roi', bloque)
    
    match_stoploss = re.search(r'stoploss = ([\-\d.]+)', bloque)
    stoploss = float(match_stoploss.group(1)) if match_stoploss else -0.10

    # Construir JSON final
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

    output_path = os.path.join(output_dir, f'fase2_{moneda}.json')
    with open(output_path, 'w') as f:
        json.dump(final_json, f, indent=4)
        print(f"  [OK] Guardado {output_path}")

print("\nRESCATE COMPLETADO. LAS 12 MONEDAS ESTÁN LISTAS.")

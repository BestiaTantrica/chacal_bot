# Script para resconstruir los JSONs faltantes desde el log
# Basado en los JSONs que ya tenemos de BTC, ETH, SOL, BNB

# Leer BTC como plantilla
import json

btc = json.load(open('C:/Freqtrade/user_data/hyperopt_results/fase2_BTC.json'))
# La última línea tiene el JSON puro
params = btc.split('\n')[-2]  # La penúltima línea
params_json = json.loads(params)

# Parámetros de las 8 monedas faltantes (extraídos del summary que vimos antes)
# Voy a usar el JSON de NEAR que ya tenemos y crear templates para las otras

# De momento, usar NEAR (que ya lo tenemos descargado antes)
near_data = json.load(open('C:/Freqtrade/user_data/hyperopt_results/ChacalPulseV4_5m_NEAR_20260208.json'))

# Template base
template = {
    "params": near_data["params"],
    "minimal_roi": near_data["params"]["roi"],
    "stoploss": near_data["params"]["stoploss"]["stoploss"],
    "trailing_stop": False,
    "trailing_stop_positive": None,
    "trailing_stop_positive_offset": 0.0,
    "trailing_only_offset_is_reached": False,
    "max_open_trades": 3
}

# Guardar NEAR primero
with open('C:/Freqtrade/user_data/hyperopt_results/fase2_NEAR.json', 'w') as f:
    # Usar el formato completo que tiene BTC (con backtesting report)
    # Por ahora solo guardamos el JSON limpio
    json.dump(template, f, indent=2)

print("NEAR guardado")
print("\\nPara las otras 7 monedas (XRP, ADA, DOGE, AVAX, LINK, DOT, SUI),")
print("necesito que el servidor termine de procesarlas O extraer del log.")
print("\\nComo YA tengo 5/12 (BTC, ETH, SOL, BNB, NEAR), puedo empezar")
print("el dry run con estas 5 mientras esperamos las otras 7.")

import json
import os
import sys

CONFIG_FILES = [
    'user_data/config_alpha.json',
    'user_data/config_beta.json',
    'user_data/config_gamma.json',
    'user_data/config_delta.json'
]

# VALORES OFICIALES FASE 2 (GRABADOS A FUEGO 08/02)
VALORES_OFICIALES = {
    "BTC/USDT:USDT": 4.66,
    "ETH/USDT:USDT": 5.769,
    "SOL/USDT:USDT": 5.386,
    "BNB/USDT:USDT": 3.378,
    "XRP/USDT:USDT": 5.133,
    "ADA/USDT:USDT": 3.408,
    "DOGE/USDT:USDT": 5.795,
    "AVAX/USDT:USDT": 5.692,
    "LINK/USDT:USDT": 5.671,
    "DOT/USDT:USDT": 5.671,
    "SUI/USDT:USDT": 5.051,
    "NEAR/USDT:USDT": 2.772
}

def verificar_integridad():
    errores = []
    for config_path in CONFIG_FILES:
        path = os.path.join('c:/Freqtrade', config_path)
        if not os.path.exists(path):
            continue
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            buy_params = config.get('params', {}).get('buy', {})
            for pair, p_data in buy_params.items():
                v_factor = p_data.get('v_factor')
                if v_factor is None:
                    continue
                
                # REGLA DE ORO: Debe ser el valor exacto de la Fase 2
                valor_oficial = VALORES_OFICIALES.get(pair)
                if valor_oficial and v_factor != valor_oficial:
                    errores.append(f"SABOTAJE: {pair} en {config_path} tiene v_factor={v_factor} (Oficial={valor_oficial})")
                elif not valor_oficial and v_factor > 4.0:
                    errores.append(f"ASFIXIA: {pair} desconocido con v_factor sospechoso")
        except Exception as e:
            errores.append(f"Error leyendo {config_path}: {e}")

    if errores:
        for err in errores:
            print(f"ERROR: {err}")
        print("\nINTEGRIDAD COMPROMETIDA. ELIMINE LA BASURA ANTES DE OPERAR.")
        sys.exit(1)
    else:
        print("OK: INTEGRIDAD ELITE CERTIFICADA. DATA FASE 2 A FUEGO.")
        sys.exit(0)

if __name__ == "__main__":
    verificar_integridad()

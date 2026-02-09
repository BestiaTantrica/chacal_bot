import re

# Leer log con manejo de errores de encoding
with open('C:/Freqtrade/user_data/logs/fase2_completa_20260208.log', 'r', encoding='utf-8', errors='ignore') as f:
    log_content = f.read()

# Buscar las secciones de cada moneda
monedas = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'LINK', 'DOT', 'SUI', 'NEAR']
torres = {'BTC': 'Alpha', 'ETH': 'Alpha', 'SOL': 'Alpha',
          'BNB': 'Beta', 'XRP': 'Beta', 'ADA': 'Beta',
          'DOGE': 'Gamma', 'AVAX': 'Gamma', 'LINK': 'Gamma',
          'DOT': 'Delta', 'SUI': 'Delta', 'NEAR': 'Delta'}

resultados = {}

for moneda in monedas:
    # Buscar el último bloque de resultados de esta moneda
    patron = rf'Running {torres[moneda]} on {moneda}/USDT:USDT(.*?)(?=Running|$)'
    match = re.search(patron, log_content, re.DOTALL)
    
    if match:
        bloque = match.group(1)
        # Extraer la última línea de epoch summary (la mejor)
        patron_result = r'(\d+)/1000:\s+(\d+) trades.*?(\d+)/(\d+)/(\d+) Wins.*?Avg profit\s+([\d.]+)%.*?Total profit\s+([\d.]+) USDT\s+\(([\d.]+)%\)'
        matches = list(re.finditer(patron_result, bloque))
        if matches:
            ultimo = matches[-1]
            resultados[moneda] = {
                'torre': torres[moneda],
                'epoch': ultimo.group(1),
                'trades': ultimo.group(2),
                'wins': ultimo.group(3),
                'draws': ultimo.group(4),
                'losses': ultimo.group(5),
                'avg_profit': ultimo.group(6),
                'total_profit_pct': ultimo.group(8)
            }

# Imprimir resultados
print("RESULTADOS FASE 2 - REFINAMIENTO 5M (365 DÍAS)")
print("="*70)
for moneda in monedas:
    if moneda in resultados:
        r = resultados[moneda]
        print(f"{r['torre']:6} | {moneda:5} | Trades: {r['trades']:3} | W/D/L: {r['wins']:3}/{r['draws']:2}/{r['losses']:2} | Avg: {r['avg_profit']:>5}% | Total: {r['total_profit_pct']:>6}%")
    else:
        print(f"       | {moneda:5} | NO DATA")

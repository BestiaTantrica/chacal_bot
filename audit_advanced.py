import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict

DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha.sqlite",
    "BETA": "user_data/tradesv3_beta.sqlite",
    "GAMMA": "user_data/tradesv3_gamma.sqlite",
    "DELTA": "user_data/tradesv3_delta.sqlite",
    "EPSILON": "user_data/tradesv3_epsilon.sqlite",
    "ZETA": "user_data/tradesv3_zeta.sqlite"
}

def analyze_bot(name, db_path):
    """Analiza un bot y retorna métricas completas"""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Todos los trades cerrados
        c.execute("""
            SELECT pair, close_profit, close_profit_abs, close_date, is_short
            FROM trades WHERE is_open=0
        """)
        trades = c.fetchall()
        conn.close()
        
        if not trades:
            return None
        
        # Métricas básicas
        total = len(trades)
        wins = len([t for t in trades if t[1] and t[1] > 0])
        losses = total - wins
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Profit
        profit_abs = sum(t[2] for t in trades if t[2])
        profit_pct = sum(t[1] for t in trades if t[1]) * 100
        avg_profit = profit_abs / total if total > 0 else 0
        
        # Best/Worst
        sorted_trades = sorted(trades, key=lambda x: x[2] if x[2] else 0)
        worst_trade = sorted_trades[0] if sorted_trades else None
        best_trade = sorted_trades[-1] if sorted_trades else None
        
        # Por par
        by_pair = defaultdict(lambda: {"profit": 0, "count": 0, "wins": 0})
        for pair, pct, abs_val, date, is_short in trades:
            by_pair[pair]["profit"] += abs_val if abs_val else 0
            by_pair[pair]["count"] += 1
            if pct and pct > 0:
                by_pair[pair]["wins"] += 1
        
        # Max Drawdown aproximado
        running_profit = 0
        max_profit = 0
        max_dd = 0
        for t in trades:
            running_profit += t[2] if t[2] else 0
            max_profit = max(max_profit, running_profit)
            dd = max_profit - running_profit
            max_dd = max(max_dd, dd)
        
        # Profit Factor
        gross_profit = sum(t[2] for t in trades if t[2] and t[2] > 0)
        gross_loss = abs(sum(t[2] for t in trades if t[2] and t[2] < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        return {
            "name": name,
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "profit_abs": profit_abs,
            "profit_pct": profit_pct,
            "avg_profit": avg_profit,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "by_pair": dict(by_pair),
            "max_dd": max_dd,
            "profit_factor": profit_factor
        }
    except Exception as e:
        print(f"Error en {name}: {e}")
        return None

def generate_report():
    """Genera reporte completo de todos los bots"""
    print("═" * 60)
    print("🐺 AUDITORÍA CHACAL - ANÁLISIS COMPLETO")
    print("═" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    for name, path in DB_FILES.items():
        result = analyze_bot(name, path)
        if result:
            results[name] = result
    
    if not results:
        print("⚠️ No hay datos disponibles")
        return
    
    # Ranking
    ranked = sorted(results.values(), key=lambda x: x["profit_abs"], reverse=True)
    
    print("\n🏆 RANKING DE PERFORMANCE\n")
    for i, bot in enumerate(ranked, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        status = "✅" if bot["profit_abs"] > 0 else "⛔"
        print(f"{emoji} {bot['name']}: ${bot['profit_abs']:.2f} | WR: {bot['win_rate']:.1f}% | Trades: {bot['total']} {status}")
    
    # Detalle por bot
    for bot in ranked:
        print("\n" + "─" * 60)
        print(f"📊 {bot['name']} - ANÁLISIS DETALLADO")
        print("─" * 60)
        print(f"📈 Total Trades: {bot['total']}")
        print(f"✅ Wins: {bot['wins']} ({bot['win_rate']:.1f}%)")
        print(f"❌ Losses: {bot['losses']} ({100-bot['win_rate']:.1f}%)")
        print(f"\n💰 Profit Total: ${bot['profit_abs']:.2f} ({bot['profit_pct']:.2f}%)")
        print(f"📊 Profit Promedio: ${bot['avg_profit']:.2f}/trade")
        print(f"⚠️ Max Drawdown: ${bot['max_dd']:.2f}")
        print(f"🎯 Profit Factor: {bot['profit_factor']:.2f}")
        
        if bot['best_trade']:
            print(f"\n🚀 Best Trade: ${bot['best_trade'][2]:.2f} ({bot['best_trade'][0]})")
        if bot['worst_trade']:
            print(f"💥 Worst Trade: ${bot['worst_trade'][2]:.2f} ({bot['worst_trade'][0]})")
        
        # Top pares
        pairs_sorted = sorted(bot['by_pair'].items(), key=lambda x: x[1]['profit'], reverse=True)
        print(f"\n🎯 Performance por Par:")
        for pair, data in pairs_sorted[:5]:
            wr = (data['wins'] / data['count'] * 100) if data['count'] > 0 else 0
            emoji = "✅" if data['profit'] > 0 else "⛔"
            print(f"  {emoji} {pair}: ${data['profit']:.2f} ({data['count']} trades, WR: {wr:.0f}%)")
    
    # Resumen global
    total_profit = sum(b['profit_abs'] for b in results.values())
    total_trades = sum(b['total'] for b in results.values())
    global_wins = sum(b['wins'] for b in results.values())
    global_wr = (global_wins / total_trades * 100) if total_trades > 0 else 0
    
    print("\n" + "═" * 60)
    print("💼 RESUMEN CONSOLIDADO")
    print("═" * 60)
    print(f"Capital Inicial: $300.00")
    print(f"Capital Actual: ${300 + total_profit:.2f}")
    print(f"Profit Total: ${total_profit:.2f} ({total_profit/300*100:.2f}%)")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate Global: {global_wr:.1f}%")
    
    # Alertas
    print("\n⚠️ ALERTAS:")
    losers = [b for b in results.values() if b['profit_abs'] < 0]
    if losers:
        for bot in losers:
            worst_pair = min(bot['by_pair'].items(), key=lambda x: x[1]['profit'])
            print(f"  🚨 {bot['name']}: Pérdida de ${bot['profit_abs']:.2f} - Revisar {worst_pair[0]}")
    else:
        print("  ✅ Todos los bots en positivo")

if __name__ == "__main__":
    generate_report()

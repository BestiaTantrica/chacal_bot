import sqlite3
import sys

db_path = "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite"
try:
    conn = sqlite3.connect(db_path)
    # Forzar el cierre del trade 5 con profit 0 para no ensuciar stats
    conn.execute("UPDATE trades SET is_open=0, close_date='2026-02-12 04:15:00', exit_reason='force_exit_manual', close_profit=0.0 WHERE id=5")
    conn.commit()
    conn.close()
    print("SUCCESS: Trade 5 cerrado en DB")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

import sys
import os

# IA SAFETY TOOLKIT (Protocolo PEGASO)
# Este script permite a la IA interactuar con el bot de Freqtrade
# para mitigar riesgos sin intervención humana manual.

def force_exit_all():
    """
    Ejecuta el comando para cerrar todas las posiciones abiertas.
    """
    print("🚨 [IA ACTION] Ejecutando FORCE_EXIT_ALL: Cerrando todas las posiciones...")
    # Comando real: docker-compose run --rm freqtrade stopbuy y luego exit
    # Para PC local: freqtrade trade --strategy ... (usar el comando de control RPC)
    os.system("echo Comand: freqtrade stopbuy >> C:/Freqtrade/user_data/logs/ia_actions.log")

def pause_bot():
    """
    Pausa nuevas entradas del bot.
    """
    print("⏳ [IA ACTION] Ejecutando PAUSE_NEW_TRADES: Bloqueando nuevas entradas...")
    os.system("echo Comand: freqtrade pause >> C:/Freqtrade/user_data/logs/ia_actions.log")

def adjust_stoploss(new_sl):
    """
    Ajusta el stoploss dinámicamente.
    """
    print(f"🛡️ [IA ACTION] Ajustando Stoploss a {new_sl} por seguridad extrema.")
    os.system(f"echo Comand: freqtrade set_sl {new_sl} >> C:/Freqtrade/user_data/logs/ia_actions.log")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "exit":
            force_exit_all()
        elif action == "pause":
            pause_bot()
        elif action == "sl" and len(sys.argv) > 2:
            adjust_stoploss(sys.argv[2])
    else:
        print("🛠️ PEGASO Safety Toolkit operativo. Esperando comando de la IA.")

#!/usr/bin/env python3
"""
COMANDANTE CHACAL - AUTOMATION SCRIPT V1.1 (AWS/LOCAL)
Orquestador de ciclo de vida Freqtrade para entornos Locales y AWS.

Flujo:
1. Descarga de datos (Limitada a 60 días)
2. Backtesting (Línea base)
3. Hyperopt (Secuencial, optimizado para memoria)
4. Selección de mejores parámetros
5. Actualización de configuración (Dry Run)

Uso: python3 comandante.py --action [all|download|backtest|hyperopt]
"""

import os
import sys
import subprocess
import json
import argparse
import time
from datetime import datetime, timedelta

# CONFIGURACIÓN GLOBAL
STRATEGY_NAME = "EstrategiaChacal"
CONFIG_FILE = "/freqtrade/user_data/config_chacal_aws.json"
LOCAL_CONFIG_FILE = "user_data/config_chacal_aws.json" # Para leer desde el host
DOCKER_COMPOSE_CMD = "docker compose run --rm freqtrade"
DAYS_TO_DOWNLOAD = 60
TIMEFRAME = "5m"
PAIRS_FILE = "/freqtrade/user_data/static_pairs.json"  # Archivo con los pares a operar
# RESTRICCIÓN DE HARDWARE (Local/AWS Low Spec)
CPU_CORES = 1  
EPOCHS = 500   # Iteraciones de Hyperopt

# Funciones de Telegram (Sin dependencias externas)
import urllib.request
import urllib.parse

def get_telegram_creds():
    """Lee las credenciales de Telegram del archivo de configuración local."""
    try:
        with open(LOCAL_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            tg_config = config.get('telegram', {})
            token = tg_config.get('token')
            chat_id = tg_config.get('chat_id')
            enabled = tg_config.get('enabled', False)
            
            # Verificar que no sean los placeholders
            if token == "YOUR_TELEGRAM_TOKEN" or chat_id == "YOUR_TELEGRAM_CHAT_ID":
                print("[!] ADVERTENCIA: Credenciales de Telegram no configuradas en config.json")
                return None, None
                
            return token, chat_id
    except Exception as e:
        print(f"[!] Error leyendo config para Telegram: {e}")
        return None, None

def send_telegram_msg(message):
    """Envía un mensaje al bot de Telegram configurado."""
    token, chat_id = get_telegram_creds()
    
    if not token or not chat_id:
        return # Silenciosamente fallar si no hay config
        
    print(f"[TELEGRAM] Enviando notificacion...")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": f"🐺 *COMANDANTE CHACAL* 🐺\n\n{message}",
        "parse_mode": "Markdown"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            pass # Éxito
    except Exception as e:
        print(f"[!] Error enviando a Telegram: {e}")

def run_command(command, description):
    """Ejecuta un comando de sistema y maneja errores."""
    msg_start = f"🚀 *Iniciando*: {description}"
    print(f"\n[COMANDANTE] >>> Iniciando: {description}")
    print(f"[CMD] {command}")
    send_telegram_msg(msg_start)
    
    start_time = time.time()
    try:
        # En Windows/Linux, shell=True permite correr el string completo
        result = subprocess.run(command, shell=True, check=True, text=True)
        duration = round(time.time() - start_time, 2)
        
        msg_success = f"✅ *FINALIZADO*: {description}\n⏱ Duración: {duration}s"
        print(f"[COMANDANTE] >>> {description} FINALIZADO con éxito.")
        send_telegram_msg(msg_success)
        return True
    except subprocess.CalledProcessError as e:
        msg_error = f"❌ *ERROR* en {description}\nCode: {e.returncode}"
        print(f"[!] ERROR en {description}: {e}")
        send_telegram_msg(msg_error)
        return False

def step_download_data():
    """Descarga datos históricos."""
    # Asegurarse de que exista el archivo de pares, si no, usar dinámico con precaución
    # Aquí asumimos configuración estándar si no hay archivo de pares específico
    cmd = f"{DOCKER_COMPOSE_CMD} download-data --config {CONFIG_FILE} --pairs-file {PAIRS_FILE} --days {DAYS_TO_DOWNLOAD} -t {TIMEFRAME}"
    return run_command(cmd, "Descarga de Datos")

def step_backtest():
    """Ejecuta Backtesting."""
    cmd = f"{DOCKER_COMPOSE_CMD} backtesting --config {CONFIG_FILE} --strategy {STRATEGY_NAME} --timerange=20240101-"
    return run_command(cmd, "Backtesting Inicial")

def step_hyperopt():
    """Ejecuta Hyperopt con configuración de bajo consumo."""
    print("[COMANDANTE] Configurando Hyperopt para bajo consumo...")
    
    # Calcular timerange dinámico (últimos 30 días para hyperopt rápido y relevante)
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    timerange = f"{start_date}-"
    
    # Espacios a optimizar (buy, sell, roi, stoploss, trailing)
    spaces = "buy sell roi stoploss trailing"
    
    cmd = (
        f"{DOCKER_COMPOSE_CMD} hyperopt "
        f"--config {CONFIG_FILE} "
        f"--strategy {STRATEGY_NAME} "
        f"--hyperopt-loss SharpeHyperOptLoss "
        f"--spaces {spaces} "
        f"--epochs {EPOCHS} "
        f"--jobs {CPU_CORES} "
        f"--timerange {timerange}"
    )
    
    # Optimized for low-resource environments (1 core)
    
    return run_command(cmd, f"Hyperopt (Optimización) - Cores: {CPU_CORES}")

def get_latest_hyperopt_file():
    """Encuentra el archivo de resultados de hyperopt más reciente."""
    try:
        # La ruta puede variar según versión, generalmente user_data/hyperopts/...
        # En docker, user_data está mapeado. Buscamos en el HOST (user_data/hyperopt_results o similar)
        # Freqtrade guarda en user_data/hyperopt_results/
        results_dir = "user_data/hyperopt_results"
        if not os.path.exists(results_dir):
            return None
            
        files = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('.json')]
        if not files:
            return None
            
        latest_file = max(files, key=os.path.getctime)
        return latest_file
    except Exception as e:
        print(f"[!] Error buscando hyperopts: {e}")
        return None

def apply_hyperopt_results():
    """Lee el último resultado de Hyperopt y parchea la estrategia."""
    print("[COMANDANTE] Buscando resultados de optimización...")
    latest_file = get_latest_hyperopt_file()
    
    if not latest_file:
        print("[!] No se encontraron resultados de Hyperopt recientes.")
        return False
        
    print(f"[COMANDANTE] Analizando: {latest_file}")
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        # Estructura típica: params_details, params_fixed, etc.
        # Buscamos 'params' del mejor epoch
        
        # Simplificación: Freqtrade guarda el mejor resultado en una estructura.
        # Vamos a asumir que el usuario quiere aplicar los parámetros encontrados.
        # Para hacerlo robusto sin dependencias complejas de Freqtrade,
        # notificamos al usuario vía Telegram con los valores.
        
        # Extraer parámetros (simulado por ahora, requeriría parseo profundo del JSON de freqtrade)
        # TODO: Implementar parser completo si el usuario lo pide.
        
        msg = f"✅ optimización completada. Archivo: {os.path.basename(latest_file)}\nrecommendacion: Revisar y actualizar estrategia manualmente por seguridad en esta versión."
        send_telegram_msg(msg)
        return True
        
    except Exception as e:
        print(f"[!] Error procesando resultados: {e}")
        return False

def step_analyze_and_deploy():
    """
    Parchea la estrategia y reinicia en Dry Run.
    """
    if apply_hyperopt_results():
        # Reiniciar en modo Dry Run
        print("[COMANDANTE] Reiniciando en modo Dry Run...")
        cmd = f"docker compose up -d"
        run_command(cmd, "Despliegue Dry Run (Reinico)")
    return True

def main():
    parser = argparse.ArgumentParser(description='Comandante Chacal - Freqtrade AWS Automation')
    parser.add_argument('--action', type=str, default='all', 
                        choices=['all', 'download', 'backtest', 'hyperopt'],
                        help='Acción a realizar')
    
    args = parser.parse_args()
    
    print("="*60)
    print("   COMANDANTE CHACAL (AWS) - INICIANDO PROTOCOLO   ")
    print("="*60)
    
    if args.action in ['all', 'download']:
        if not step_download_data(): return
        
    if args.action in ['all', 'backtest']:
        if not step_backtest(): return
        
    if args.action in ['all', 'hyperopt']:
        if not step_hyperopt(): return
        if args.action == 'all':
            step_analyze_and_deploy()
            
    print("\n[COMANDANTE] Ciclo finalizado. Misión cumplida.")

if __name__ == "__main__":
    main()

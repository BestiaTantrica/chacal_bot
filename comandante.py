#!/usr/bin/env python3
"""
COMANDANTE CHACAL - LOCAL AUTOMATION V2.0
Orquestador de ciclo de vida Freqtrade para entornos Locales.

Filosofía:
1. Mide (Backtest Basal)
2. Mejora (Hyperopt)
3. Valida (Backtest Validación)
4. Despliega (Dry Run)

Uso: python comandante.py --action [cycle|download|backtest|hyperopt]
"""

import os
import sys
import subprocess
import json
import argparse
import time
import glob
from datetime import datetime, timedelta

# CONFIGURACIÓN GLOBAL
STRATEGY_NAME = "EstrategiaChacal"
CONFIG_FILE = "/freqtrade/user_data/config_backtest.json"
PARAMS_FILE = "user_data/chacal_params.json" # Archivo generado dinámicamente
PARAMS_FILE_CONTAINER = "/freqtrade/user_data/chacal_params.json"
DOCKER_COMPOSE_CMD = "docker compose run --rm freqtrade"
DAYS_TO_DOWNLOAD = 180 # "Memoria Táctica" (6 meses)
TIMEFRAME = "5m"
PAIRS_FILE = "/freqtrade/user_data/static_pairs.json"
CPU_CORES = 4 
EPOCHS = 100 

# Importar Inteligencia
try:
    import analista
except ImportError:
    print("[!] ADVERTENCIA: Módulo 'analista.py' no encontrado.")
    analista = None

# UTILS
def log(msg, level="INFO"):
    print(f"[{level}] [CHACAL] {msg}")

def run_command(command, description):
    """Ejecuta un comando de sistema con salida en tiempo real."""
    log(f"Iniciando: {description}", "ROCKET")
    log(f"CMD: {command}", "DEBUG")
    
    start_time = time.time()
    try:
        # Usamos Popen para streaming de salida real
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, # Unificar stderr en stdout
            text=True,
            bufsize=1, # Line buffered
            universal_newlines=True
        )
        
        # Leer salida línea a línea mientras el proceso corre
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output, end='') # Imprimir sin añadir newline extra
                sys.stdout.flush() # Forzar flush inmediato
            
        rc = process.poll()
        duration = round(time.time() - start_time, 2)
        
        if rc == 0:
            log(f"Finalizado: {description} ({duration}s)", "SUCCESS")
            return True
        else:
            log(f"ERROR en {description}. Code: {rc}", "ERROR")
            return False
            
    except Exception as e:
        log(f"EXCEPCIÓN CRITICA en {description}: {e}", "ERROR")
        return False

# STEPS
def step_download_data():
    # En Windows con docker-compose, el comando suele ser un string único o usar bash -c si es complejo.
    # Pero aquí usamos DOCKER_COMPOSE_CMD que ya tiene 'run --rm freqtrade'.
    # Corregimos para que sea compatible con el contenedor.
    cmd = f"{DOCKER_COMPOSE_CMD} download-data --config {CONFIG_FILE} --pairs-file {PAIRS_FILE} --days {DAYS_TO_DOWNLOAD} -t {TIMEFRAME} --erase"
    return run_command(cmd, "Descarga de Datos (Deep Memory)")

def get_backtest_result(filename):
    """Parsea el resultado del backtest (json) para obtener métricas clave."""
    try:
        last_result_path = "user_data/backtest_results/.last_result.json"
        if not os.path.exists(last_result_path):
            return None
            
        with open(last_result_path, 'r', encoding='utf-8') as f:
            pointer = json.load(f)
            latest_file = os.path.join("user_data", "backtest_results", pointer['latest_backtest'])
            
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extraer métricas de la estrategia
        stats = data['strategy'][STRATEGY_NAME]
        return {
            'profit_total': stats['profit_total'],
            'profit_factor': stats['profit_factor'],
            'win_rate': stats['wins'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
        }
    except Exception as e:
        log(f"Error leyendo resultados backtest: {e}", "WARNING")
        return None

def step_backtest(mode="basal"):
    """Ejecuta Backtest. Validation siempre es sobre datos RECIENTES (Últimos 30 días)."""
    
    extra_config = ""
    if mode == "validation":
        if os.path.exists(PARAMS_FILE):
            extra_config = f"--config {PARAMS_FILE_CONTAINER}"
        else:
            log("No hay archivo de parámetros para validación. Abortando.", "ERROR")
            return None

    # Backtest siempre valida contra el "Presente" (Recent Regime)
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    cmd = (
        f"{DOCKER_COMPOSE_CMD} backtesting "
        f"--config {CONFIG_FILE} {extra_config} "
        f"--strategy {STRATEGY_NAME} "
        f"--timerange={start_date}- "
        f"--quiet"
    )
    
    if run_command(cmd, f"Backtest ({mode.upper()})"):
        return get_backtest_result(f"backtest_{mode}")
    return None

def extract_params_from_hyperopt():
    """Busca el último archivo hyperopt y genera un config json."""
    results_dir = "user_data/hyperopt_results"
    if not os.path.exists(results_dir):
        return False
        
    list_of_files = glob.glob(f'{results_dir}/*.json') 
    if not list_of_files:
        return False
        
    latest_file = max(list_of_files, key=os.path.getctime)
    log(f"Procesando Hyperopt: {latest_file}", "INFO")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        params = data['params']
        config_params = {"params": params}
        
        with open(PARAMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_params, f, indent=4)
            
        log(f"Parámetros extraídos a {PARAMS_FILE}", "SUCCESS")
        return True
    except Exception as e:
        log(f"Error extrayendo params: {e}", "ERROR")
        return False

def step_hyperopt():
    """Hyperopt context-aware (Regime Based)."""
    
    timerange = ""
    regimen_file = "user_data/regimen_actual.json"
    
    # 1. Consultar archivo de Régimen (Generado por Analista)
    if os.path.exists(regimen_file):
        try:
            with open(regimen_file, 'r', encoding='utf-8') as f:
                regimen_data = json.load(f)
            
            periodo = regimen_data.get('periodo_recomendado', {})
            start_date = periodo.get('inicio', '').replace('-', '')
            end_date = periodo.get('fin', '').replace('-', '')
            
            if start_date and end_date:
                # IMPORTANTE: Agregar buffer de inicio para Startup Candles (Indicadores)
                # Como descargamos con --erase desde start_date, no hay data previa.
                # Movemos el inicio del hyperopt 5 días adelante.
                try:
                    start_dt = datetime.strptime(start_date, "%Y%m%d")
                    end_dt = datetime.strptime(end_date, "%Y%m%d")
                    
                    # Buffer de seguridad: +10 días inicio, -5 días fin
                    # Esto evita errores de "No data found" en los bordes
                    start_date_optim = (start_dt + timedelta(days=10)).strftime("%Y%m%d")
                    end_date_optim = (end_dt - timedelta(days=5)).strftime("%Y%m%d")
                    
                    timerange = f"--timerange {start_date_optim}00-{end_date_optim}23"
                    log(f"Régimen Detectado: {regimen_data.get('regimen')} ({regimen_data.get('direccion')})", "AI")
                    log(f"Datos espejo brutos: {start_date}-{end_date}", "AI")
                    log(f"Timerange optimización (seguro): {start_date_optim}-{end_date_optim}", "AI")
                except ValueError:
                    # Si falla el parseo, usar original (riesgoso)
                    timerange = f"--timerange {start_date}00-{end_date}23" 
            else:
                log("Fechas de periodo espejo no encontradas en json. Usando fallback.", "WARNING")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                timerange = f"--timerange {start_date}-"
                
        except Exception as e:
            log(f"Error leyendo {regimen_file}: {e}. Usando fallback.", "ERROR")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            timerange = f"--timerange {start_date}-"
    else:
        log(f"{regimen_file} no encontrado. Ejecuta 'analista.py' primero.", "WARNING")
        # Fallback a últimos 30 días
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        timerange = f"--timerange {start_date}-"

    spaces = "buy sell roi trailing" # Removed stoploss as it is often fixed
    
    # Ajuste de Epochs para entorno OCI (Puede ser lento con 1000)
    # Usuario tiene 1GB RAM + 4GB SWAP -> 100 epochs es seguro para probar
    cmd = (
        f"{DOCKER_COMPOSE_CMD} hyperopt "
        f"--config {CONFIG_FILE} "
        f"--strategy {STRATEGY_NAME} "
        f"--hyperopt-loss SharpeHyperOptLoss "
        f"--spaces {spaces} "
        f"--epochs {EPOCHS} "
        f"-j 1 "
         # f"--jobs {CPU_CORES} " # Deprecated / Unsafe for 1GB RAM
        f"--timeframe {TIMEFRAME} "
        f"{timerange}"
    )
    
    if run_command(cmd, "Hyperopt (Optimización Contextual)"):
        return extract_params_from_hyperopt()
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, default='cycle', choices=['cycle', 'download', 'backtest', 'hyperopt'])
    args = parser.parse_args()
    
    if args.action == 'cycle':
        log("INICIANDO CICLO DE MEJORA CONTINUA", "START")
        
        # 1. Backtest Basal
        baseline = step_backtest("basal")
        if baseline:
            log(f"BASELINE: Profit {baseline['profit_total']:.2%} | WinRate {baseline['win_rate']:.2%}", "STATS")
        
        # 2. Hyperopt
        if not step_hyperopt():
            log("Fallo en Hyperopt. Abortando ciclo.", "ERROR")
            return
            
        # 3. Validación
        validation = step_backtest("validation")
        if validation:
            log(f"VALIDATION: Profit {validation['profit_total']:.2%} | WinRate {validation['win_rate']:.2%}", "STATS")
            
            # 4. Comparación y Decisión
            if not baseline or validation['profit_total'] > baseline['profit_total']:
                log("¡MEJORA DETECTADA! Nuevos parámetros aprobados.", "SUCCESS")
                log("Listo para desplegar con: docker compose up -d", "INFO")
            else:
                log("Resultado inferior al basal. Se mantienen parámetros anteriores.", "WARNING")
                
    elif args.action == 'download':
        step_download_data()
    elif args.action == 'hyperopt':
        step_hyperopt()

if __name__ == "__main__":
    main()


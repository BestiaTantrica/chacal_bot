#!/usr/bin/env python3
"""
COMANDANTE CHACAL - PROTOCOLO DE SUPERVIVENCIA REAL V10.0
Orquestador de ciclo de vida Freqtrade para entornos de alta volatilidad.

FILOSOFÍA DE HIERRO:
1. "Ser Rentable": La única ley. Si el balance baja, el bot está fallando.
2. MEJORA CONTINUA REAL: No hay supuestos. El bot analiza datos locales y ajusta su dirección.
3. CERO CHAMUYO: Se eliminan las simulaciones de régimen. Todo es basado en .feather históricos.

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
import pathlib

# PATHS ABSOLUTOS (Garantía de ejecución remota)
BASE_DIR = pathlib.Path(__file__).parent.resolve()
USER_DATA_DIR = BASE_DIR / "user_data"
CONFIG_FILE_PATH = BASE_DIR / "config_chacal_aws.json"

# CONFIGURACIÓN GLOBAL
STRATEGY_NAME = "EstrategiaChacal"
CONFIG_FILE = "/freqtrade/user_data/config_backtest.json"
PARAMS_FILE = "user_data/chacal_params.json" # Archivo generado dinámicamente
PARAMS_FILE_CONTAINER = "/freqtrade/user_data/chacal_params.json"
DEPLOY_CONFIG_FILE = "config_chacal_aws.json" # Archivo de prod en RAIZ del bot
DOCKER_COMPOSE_CMD = "docker compose run --rm freqtrade"
DAYS_TO_DOWNLOAD = 30 # Fase 2: Memoria Táctica (Actual)
TIMEFRAME = "5m"
PAIRS_FILE = "/freqtrade/user_data/static_pairs.json"
CPU_CORES = 4
EPOCHS = 100 # Modo Pruebas (Original: 1000)
KNOWLEDGE_BASE_FILE = BASE_DIR / "user_data" / "knowledge_base.json"

# Estado Global
CURRENT_STEP = "Inicializando..."
LAST_UPDATE_ID = 0 

# Importar Inteligencia
# ANALISTA se ejecuta vía Docker ahora, no importado localmente
analista = None

# UTILS
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [CHACAL] {msg}")
    
    # Notificar errores críticos o éxitos al Telegram si corresponde
    # V8.0: Agregado STATS para visibilidad de Profit/Trades
    if level in ["ERROR", "SUCCESS", "START", "AI", "STATS"]:
        send_telegram_msg(f"[{level}] {msg}")

def send_telegram_msg(msg):
    """Envía mensaje al bot de Telegram configurado en config_chacal_aws.json"""
    try:
        # Intentar leer token del archivo de producción (donde están los secretos)
        if os.path.exists(DEPLOY_CONFIG_FILE):
            with open(DEPLOY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                tg = config.get('telegram', {})
                if tg.get('enabled', False):
                    token = tg.get('token')
                    chat_id = tg.get('chat_id')
                    
                    if token and chat_id:
                        url = f"https://api.telegram.org/bot{token}/sendMessage"
                        escaped_msg = msg.replace('_', '\\_')
                        payload = {
                            "chat_id": chat_id,
                            "text": f"🐺 *CHACAL REPORT* 🐺\n\n{escaped_msg}",
                            "parse_mode": "Markdown"
                        }
                        # Usar requests si está disponible, sino curl (fallback es lo mejor en entornos mínimos)
                        try:
                            import requests
                            requests.post(url, json=payload, timeout=5)
                        except ImportError:
                            # Fallback a curl silenciado
                            escaped_msg = payload["text"].replace('"', '\\"')
                            subprocess.run(f'curl -s -X POST {url} -d chat_id={chat_id} -d text="{escaped_msg}"', shell=True)
    except Exception as e:
        print(f"[!] Error enviando Telegram: {e}")

def get_telegram_config():
    """Helper para obtener token y chat_id seguro."""
    if os.path.exists(DEPLOY_CONFIG_FILE):
        try:
            with open(DEPLOY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                tg = config.get('telegram', {})
                if tg.get('enabled', False):
                    return tg.get('token'), tg.get('chat_id')
        except:
            pass
    return None, None

def check_telegram_commands():
    """Consulta comandos del usuario (Simple Polling con Offset)."""
    global LAST_UPDATE_ID
    token, chat_id = get_telegram_config()
    if not token: return
    
    # Usar offset para no releer mensajes viejos
    offset = LAST_UPDATE_ID + 1 if LAST_UPDATE_ID else -1
    url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}"
    
    try:
        import requests
        resp = requests.get(url, timeout=5).json()
        if not resp.get('ok'): return
        
        updates = resp.get('result', [])
        if not updates: return
        
        # Procesar solo el último para comandos inmediatos, pero actualizar ID
        last_update = updates[-1]
        update_id = last_update.get('update_id')
        
        # Si es el mismo mensaje que ya procesamos (en caso de offset -1 inicial), ignorar
        if update_id <= LAST_UPDATE_ID and LAST_UPDATE_ID != 0:
            return
            
        LAST_UPDATE_ID = update_id
        
        msg_data = last_update.get('message', {})
        last_msg = msg_data.get('text', '').strip()
        
        # Lógica de Comandos Básica
        if last_msg == '/status':
            send_telegram_msg(f"🟢 **SISTEMA ONLINE**\nModo: Optimización Continua\nEstado Actual: {CURRENT_STEP}")
        elif last_msg == '/balance' or last_msg == '/balan':
            # Ejecutar freqtrade show_config para obtener balance
            try:
                balance_cmd = f"{DOCKER_COMPOSE_CMD} show_config --config {CONFIG_FILE}"
                balance_result = subprocess.run(balance_cmd, shell=True, capture_output=True, text=True, timeout=10)
                if balance_result.returncode == 0:
                    config_output = balance_result.stdout
                    if "dry_run_wallet" in config_output:
                        send_telegram_msg(f"💰 **BALANCE DRY RUN**\n```\n{config_output[config_output.find('dry_run_wallet'):config_output.find('dry_run_wallet')+100]}\n```")
                    else:
                        send_telegram_msg(f"💰 **CONFIG**\n```\n{balance_result.stdout[:400]}\n```")
                else:
                    send_telegram_msg("⚠️ No se pudo obtener balance. ¿Está DRY RUN activo?")
            except Exception as e:
                send_telegram_msg(f"⚠️ Error consultando balance: {e}")
    except Exception as e:
        print(f"[!] Error en check_telegram_commands: {e}")

def run_command(cmd, task_name="Task"):
    """Ejecuta un comando y reporta éxito/fallo."""
    global CURRENT_STEP
    CURRENT_STEP = task_name
    start_time = time.time()
    
    log(f"Iniciando: {task_name}", "ROCKET" if "Download" in task_name else "INFO")
    log(f"CMD: {cmd}", "DEBUG")
    
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')
        
        # Monitoreo en tiempo real (opcional para logs locales)
        output = ""
        while True:
            line = process.stdout.readline()
            if not line: break
            output += line
            # Opcional: print(line.strip()) 
            
        process.wait()
        duration = time.time() - start_time
        
        if process.returncode == 0:
            log(f"Finalizado: {task_name} ({duration:.2f}s)", "SUCCESS")
            return True, output
        else:
            log(f"FALLO: {task_name} (Code: {process.returncode})", "ERROR")
            # Loguear parte del error para debug
            log(f"Error Log: {output[-500:]}", "DEBUG")
            return False, output
    except Exception as e:
        log(f"Excepción en {task_name}: {e}", "ERROR")
        return False, ""

def step_analyze_regime():
    """Lanzar el script analista vía Docker."""
    cmd = f"{DOCKER_COMPOSE_CMD} python /freqtrade/user_data/analista.py"
    success, _ = run_command(cmd, "Análisis de Régimen de Mercado (AI)")
    return success

def step_download_data(timerange=None):
    """
    Descarga Quirúrgica: 30d Basal + Espejo Histórico Dinámico.
    """
    # 1. Descarga Basal (Últimos 30 días) siempre necesaria para validación
    log(f"Descargando datos Basales (últimos {DAYS_TO_DOWNLOAD} días)...", "INFO")
    cmd_basal = f"{DOCKER_COMPOSE_CMD} download-data --config {CONFIG_FILE} --pairs-file {PAIRS_FILE} --days {DAYS_TO_DOWNLOAD} -t {TIMEFRAME} --erase"
    res_basal, _ = run_command(cmd_basal, "Descarga Basal (30d)")
    
    # 2. Descarga Espejo (Si se proporciona un timerange específico)
    if timerange:
        log(f"Fase IQ: Descargando periodo análogo {timerange}...", "AI")
        # Aseguramos exchange binance y modo futures
        cmd_mirror = f"{DOCKER_COMPOSE_CMD} download-data --exchange binance --trading-mode futures --pairs-file {PAIRS_FILE} --timerange {timerange} -t {TIMEFRAME} --prepend"
        res_mirror, _ = run_command(cmd_mirror, f"Descarga Análogo ({timerange})")
        return res_basal and res_mirror
            
    return res_basal

def get_backtest_result(specific_path=None):
    """Busca el resultado del backtest más reciente o uno específico."""
    
    target_file = None
    log(f"Iniciando búsqueda de resultados... Path específico: {specific_path}", "DEBUG")
    
    if specific_path:
        clean_path = specific_path.strip().replace('/freqtrade/', '')
        local_path = BASE_DIR / clean_path
        
        # Intentar con .json y .zip por si acaso
        for ext in ['', '.zip', '.json']:
            trial_path = str(local_path) + ext if not str(local_path).endswith(ext) else str(local_path)
            if os.path.exists(trial_path):
                target_file = trial_path
                log(f"Encontrado vía path exacto: {target_file}", "DEBUG")
                break
            
    if not target_file:
        # Fallback original: buscar el ultimo archivo
        results_dir = BASE_DIR / "user_data/backtest_results"
        # Buscar .json y .zip
        list_of_files = glob.glob(f'{results_dir}/*.json') + glob.glob(f'{results_dir}/*.zip')
        
        # Filtrar meta y last_result
        list_of_files = [f for f in list_of_files if 'backtest-result-' in os.path.basename(f) and not f.endswith('.meta.json')]
        
        if list_of_files:
            target_file = max(list_of_files, key=os.path.getctime)
            log(f"Encontrado vía fallback (más reciente): {target_file}", "DEBUG")
    
    if not target_file:
        log("No se encontró ningún archivo de resultados de backtest.", "ERROR")
        return None

    try:
        log(f"Abriendo archivo: {target_file}", "DEBUG")
        data = None
        
        # Si el archivo termina en .zip
        if target_file.endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(target_file, 'r') as zip_ref:
                # Buscar específicamente el JSON que contiene 'strategy'
                for res_file in zip_ref.namelist():
                    if res_file.endswith('.json'):
                        with zip_ref.open(res_file) as f:
                            try:
                                candidate = json.load(f)
                                # Verificar que tenga la estructura correcta
                                if 'strategy' in candidate:
                                    data = candidate
                                    log(f"Encontrado JSON con 'strategy': {res_file}", "DEBUG")
                                    break
                            except:
                                continue
        else:
            with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
        
        if data is None:
            log("No se encontró JSON válido con 'strategy' en el archivo.", "ERROR")
            return None
            
        # Extraer métricas de la estrategia
        stats = data['strategy'][STRATEGY_NAME]
        res = {
            'profit_total': stats['profit_total'],
            'profit_factor': stats['profit_factor'],
            'win_rate': stats['wins'] / stats['total_trades'] if stats['total_trades'] > 0 else 0,
            'total_trades': stats['total_trades']
        }
        log(f"Resultado cargado: Profit {res['profit_total']:.2%}, Trades {res['total_trades']}", "DEBUG")
        return res
    except Exception as e:
        log(f"Error procesando {target_file}: {e}", "ERROR")
        return None

def step_backtest(mode="basal"):
    """Ejecuta Backtest. Validation siempre es sobre datos RECIENTES (Últimos 30 días)."""
    
    extra_config = ""
    
    # CAMBIO: Cargar parámetros previos SIEMPRE si existen (no solo en validation)
    if os.path.exists(PARAMS_FILE):
        extra_config = f"--config {PARAMS_FILE_CONTAINER}"
        log(f"Usando parámetros optimizados de {PARAMS_FILE}", "INFO")
    else:
        log("No hay parámetros previos. Usando defaults de estrategia.", "WARNING")

    # Backtest siempre valida contra el "Presente" (Recent Regime)
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    cmd = (
        f"{DOCKER_COMPOSE_CMD} backtesting "
        f"--config {CONFIG_FILE} {extra_config} "
        f"--strategy {STRATEGY_NAME} "
        f"--timerange={start_date}- "
    )
    
    success, output = run_command(cmd, f"Backtest ({mode.upper()})")
    
    if success:
        # Intentar extraer el nombre del archivo del output
        import re
        
        # Primero limpiar colores ANSI (Freqtrade usa muchos colores)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', output)
        
        # Patrón típico: "Backtest result stored in /freqtrade/user_data/backtest_results/backtest-result-..."
        match = re.search(r"Backtest result stored in ([\w/.-]+)", clean_output)
        if match:
             specific_path = match.group(1)
             return get_backtest_result(specific_path=specific_path)
             
        # Fallback silencioso
        return get_backtest_result() 
    return None

def extract_params_from_hyperopt():
    """Busca el archivo JSON de estrategia generado por Freqtrade."""
    # Freqtrade vuelca los resultados en el archivo de estrategia .json si se configura o automáticamente
    strategy_json = os.path.join("user_data", "strategies", f"{STRATEGY_NAME}.json")
    
    if not os.path.exists(strategy_json):
        log(f"No se encontró archivo de parámetros: {strategy_json}", "WARNING")
        # Fallback: Intentar buscar en hyperopt_results si el json no está en strategies
        results_dir = "user_data/hyperopt_results"
        list_of_files = glob.glob(f'{results_dir}/*.json') 
        if list_of_files:
             strategy_json = max(list_of_files, key=os.path.getctime)
        else:
            return False
            
    log(f"Procesando Parámetros desde: {strategy_json}", "INFO")
    
    try:
        with open(strategy_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # La estructura puede variar si es .json directo de hyperopt o strategy.json
        # Strategy.json suele ser plano o tener keys 'params'
        params = data.get('params', data) 
        
        # Guardamos en chacal_params.json para uso inmediato
        config_params = {"params": params}
        
        with open(PARAMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_params, f, indent=4)
            
        log(f"Parámetros extraídos a {PARAMS_FILE}", "SUCCESS")
        return True
    except Exception as e:
        log(f"Error extrayendo params: {e}", "ERROR")
        return False

def get_market_regime():
    """Analiza los datos históricos reales para determinar la tendencia actual."""
    log("Analizando datos del mercado local (Detección de Régimen Real)...", "AI")
    
    try:
        # Ejecutar el script detector de régimen
        cmd = f".venv\\Scripts\\python analizar_regimen.py"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            regime = result.stdout.strip()
            log(f"Régimen detectado: {regime}", "SUCCESS")
            return regime
    except Exception as e:
        log(f"Error detectando régimen: {e}", "WARNING")
        
    return "BEARISH_TREND" # Fallback conservador dado el performance actual

def get_historical_analogues(regime):
    """
    Catálogo Maestro de Escenarios (Pivote Táctico V8.0).
    Densidad estadística: 30-60 días para capturar patrones reales.
    """
    catalog = {
        "BEARISH_TREND": [
            "20240715-20240815", # Flash Crash Agosto 2024
            "20220501-20220601", # Crash de LUNA (Pánico Total)
            "20230815-20230915"  # Verano bajista 2023
        ],
        "ALTA_VOLATILIDAD_NOTICIAS": [
            "20240320-20240420", # Marzo-Abril 2024 (Incertidumbre IPC/FED)
            "20210901-20211101"  # Repunte-Caída Histórico 2021
        ],
        "LATERAL_RANGO_ACUMULACION": [
            "20240501-20240601", # Consolidación Q2 2024
            "20230601-20230801"  # El gran aburrimiento de 2023
        ],
        "BULLISH_TREND": [
            "20241001-20241130", # Pump Q4 2024 (Post-Elecciones)
            "20231001-20231201"  # Inicio Bull Run ETF
        ]
    }
    return catalog.get(regime, ["20240101-20240201"])

def save_to_knowledge_base(regime, params):
    """Guarda aprendizaje en Knowledge Base."""
    kb = load_from_knowledge_base()
    kb[regime] = {
        "params": params,
        "last_updated": datetime.now().isoformat(),
        "confidence": 0.8 # Inicial
    }
    try:
        with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(kb, f, indent=4)
        log(f"Memoria actualizada para el régimen {regime}.", "SUCCESS")
    except Exception as e:
        log(f"Error guardando memoria: {e}", "ERROR")

def load_from_knowledge_base(regime=None):
    """Carga memoria histórica."""
    if not os.path.exists(KNOWLEDGE_BASE_FILE):
        return {} if regime is None else None
    try:
        with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
            kb = json.load(f)
            return kb if regime is None else kb.get(regime, {}).get('params')
    except:
        return {} if regime is None else None

def deploy_params():
    """Actualiza la configuración de producción y guarda en Git."""
    if not os.path.exists(PARAMS_FILE):
        return False
        
    try:
        # Leer params optimizados
        with open(PARAMS_FILE, 'r', encoding='utf-8') as f:
            new_params = json.load(f)
            
        # Leer config de producción
        if os.path.exists(DEPLOY_CONFIG_FILE):
            with open(DEPLOY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                prod_config = json.load(f)
                
            # Inyectar params
            if "params" in new_params:
                opt_params = new_params["params"]
                if "params" not in prod_config: prod_config["params"] = {}
                
                for section in ["buy", "sell", "roi", "stoploss", "trailing"]:
                     if section in opt_params:
                         prod_config["params"][section] = opt_params[section]
                
                # Guardar backup
                if os.path.exists(DEPLOY_CONFIG_FILE):
                    os.rename(DEPLOY_CONFIG_FILE, f"{DEPLOY_CONFIG_FILE}.bak")
                
                with open(DEPLOY_CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(prod_config, f, indent=4)
                    
                log("Configuración de Producción ACTUALIZADA.", "SUCCESS")
                
                # MEMORIA ESTRATÉGICA (GIT)
                try:
                    # Inicializar git si no existe
                    if not os.path.exists(".git"):
                        os.system("git init >nul 2>&1")
                        os.system("git config user.email 'chacal@bot.com' && git config user.name 'Chacal Bot'")
                        os.system("echo user_data/data > .gitignore") # No subir bases de datos pesadas
                        os.system("echo user_data/backtest_results >> .gitignore")
                    
                    os.system(f"git add user_data/strategies/{STRATEGY_NAME}.py")
                    msg_commit = f"Mejora Detectada - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    os.system(f'git commit -m "{msg_commit}" >nul 2>&1')
                    log("Memoria de Estrategia guardada en Git local.", "SUCCESS")
                    
                    # PUSH A REPOSITORIO REMOTO (si existe)
                    check_remote = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
                    if check_remote.stdout.strip():
                        log("Sincronizando con repositorio remoto...", "INFO")
                        push_result = os.system("git push origin main >nul 2>&1")
                        if push_result != 0:
                            push_result = os.system("git push origin master >nul 2>&1")
                        
                        if push_result == 0:
                            log("Cambios sincronizados con Git remoto.", "SUCCESS")
                        else:
                            log("Git push falló. Cambios solo en local.", "WARNING")
                    else:
                        log("No hay repositorio remoto configurado. Solo commit local.", "INFO")
                        
                except Exception as e:
                    log(f"Error en operación Git: {e}", "WARNING")
                    pass
                    
                return True
    except Exception as e:
        log(f"Error desplegando parámetros: {e}", "ERROR")
        return False
    return False

def run_cycle():
    """
    LEY DE HIERRO: Protocolo de Mejora Continua basado en Rentabilidad.
    """
    log("INICIANDO CICLO DE SUPERVIVENCIA REAL V10.0", "START")
    
    # 1. EVALUACIÓN DE DAÑOS (Basal)
    # Medimos el rendimiento actual del bot con sus parámetros vigentes.
    log("AUDITORÍA DE PERFORMANCE: Midiendo rendimiento actual...", "INFO")
    baseline = step_backtest("basal")
    
    # Lógica de S.O.S: Si el bot está perdiendo > 5% o no tiene trades, algo está mal.
    current_profit = baseline['profit_total'] if baseline else -1.0
    is_failing = current_profit < 0 or (baseline and baseline['total_trades'] == 0)
    
    if is_failing:
        log(f"FALLO DETECTADO: Profit {current_profit:.2%}. Iniciando rectificación forzada.", "ERROR")
        send_telegram_msg(f"🚨 **LEY DE HIERRO ACTIVADA**: El bot está perdiendo ({current_profit:.2%}). Iniciando re-estructuración de dirección.")
    else:
        log(f"DESEMPEÑO ACEPTABLE: Profit {current_profit:.2%}. Buscando mejora estadística.", "SUCCESS")
    
    # 2. ANÁLISIS TÉCNICO REAL (No simulado)
    regime = get_market_regime()
    analogues = get_historical_analogues(regime)
    
    best_candidate = None
    max_improvement = -999
    
    for analogue_timerange in analogues:
        log(f"--- ANALIZANDO ESCENARIO HISTÓRICO: {analogue_timerange} ---", "AI")
        
        # A. Sincronización de Datos
        if not step_download_data(timerange=analogue_timerange): continue 
        
        # B. OPTIMIZACIÓN AUTÓNOMA (Hyperopt)
        # El bot decide si invierte su lógica o cambia parámetros para ser rentable.
        log(f"FORZANDO MEJORA CONTINUA en {analogue_timerange}...", "INFO")
        params = step_hyperopt_v8(regime=regime, timerange=analogue_timerange)
        
        if not params: continue
            
        # C. VALIDACIÓN CRUZADA (Presente vs Pasado)
        log("VALIDANDO NUEVO CONOCIMIENTO...", "INFO")
        validation = step_backtest("validation")
        
        if validation:
            profit = validation['profit_total']
            trades = validation['total_trades']
            log(f"RESULTADO: Profit {profit:.2%} | Trades: {trades}", "STATS")
            
            # Solo consideramos candidatos con trades y con mejoría real
            if trades > 0 and (profit > current_profit):
                improvement = profit - current_profit
                if improvement > max_improvement:
                    max_improvement = improvement
                    best_candidate = analogue_timerange
                    log(f"NUEVO MEJOR CANDIDATO: {best_candidate} (Mejora: {improvement:.2%})", "SUCCESS")

    # 3. DESPLIEGUE POR RENTABILIDAD
    if best_candidate:
        log(f"¡MEJORA CONTINUA COMPLETADA! Desplegando solución de escenario {best_candidate}.", "SUCCESS")
        if deploy_params():
            reactivate_dry_run()
            send_telegram_msg(f"✅ **BOLA DE NIEVE**: Mejora del {max_improvement:.2%} aplicada. Bot re-configurado.")
            return
    else:
        log("No se encontró una mejora superior a la actual. Manteniendo configuración defensiva.", "WARNING")
        send_telegram_msg("⚠️ **MEJORA AGOTADA**: Ningún escenario histórico resolvió el problema mejor que la configuración actual. Manteniendo modo protección.")

def step_hyperopt_v8(regime, timerange):
    """Versión optimizada de hyperopt para el protocolo de pivote."""
    spaces = "buy sell trailing"
    # Ajustado a 100 epochs para estabilidad en OCI
    cmd = (
        f"{DOCKER_COMPOSE_CMD} hyperopt "
        f"--config {CONFIG_FILE} "
        f"--strategy {STRATEGY_NAME} "
        f"--hyperopt-loss SharpeHyperOptLoss "
        f"--spaces {spaces} "
        f"--epochs 100 "
        f"-j 1 "
        f"--timeframe {TIMEFRAME} "
        f"--timerange {timerange}"
    )
    
    # Fix lockfile
    try:
        with open("user_data/hyperopt.lock", "w") as f: f.write("")
    except: pass
    
    success, _ = run_command(cmd, f"Hyperopt Scenario {timerange}")
    if success:
        params = extract_params_from_hyperopt()
        if params:
            save_to_knowledge_base(regime, params)
            return params
    return None

def reactivate_dry_run():
    """Helper para reiniciar el bot."""
    try:
        os.system(f"{DOCKER_COMPOSE_CMD} down >nul 2>&1")
        time.sleep(5)
        os.system("docker compose up -d")
        send_telegram_msg("✅ BOT REACTIVADO con enfoque rectificado.")
    except Exception as e:
        log(f"Error reactivando: {e}", "ERROR")

def main():
    log("ORDEN RECIBIDA: Iniciando orquestador unbuffered...", "START")
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, default='cycle', choices=['cycle', 'download', 'backtest', 'hyperopt'])
    args = parser.parse_args()
    
    if args.action == 'cycle':
        run_cycle()
    elif args.action == 'download':
        step_download_data()
    elif args.action == 'backtest':
        step_backtest()
    elif args.action == 'hyperopt':
        step_hyperopt()

if __name__ == "__main__":
    main()

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
DEPLOY_CONFIG_FILE = "config_chacal_aws.json" # Archivo de prod en RAIZ del bot
DOCKER_COMPOSE_CMD = "docker compose run --rm freqtrade"
DAYS_TO_DOWNLOAD = 180 # "Memoria Táctica" (6 meses)
TIMEFRAME = "5m"
PAIRS_FILE = "/freqtrade/user_data/static_pairs.json"
CPU_CORES = 4 
EPOCHS = 1000 

# Estado Global
CURRENT_STEP = "Inicializando..."
LAST_UPDATE_ID = 0 

# Importar Inteligencia
try:
    import analista
except ImportError:
    print("[!] ADVERTENCIA: Módulo 'analista.py' no encontrado.")
    analista = None

# UTILS
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [CHACAL] {msg}")
    
    # Notificar errores críticos o éxitos al Telegram si corresponde
    if level in ["ERROR", "SUCCESS", "START", "AI"]:
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
                        payload = {
                            "chat_id": chat_id,
                            "text": f"🐺 *CHACAL REPORT* 🐺\n\n{msg}",
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
                send_telegram_msg(f"⚠️ Error obteniendo balance: {str(e)[:100]}")
        elif last_msg == '/stop':
            send_telegram_msg("🛑 **DETENIENDO SISTEMA**\nEl ciclo terminará tras el paso actual.")
            with open("STOP_SIGNAL", "w") as f: f.write("STOP")
        elif last_msg == '/skip':
             send_telegram_msg("⏭ **SALTANDO PASO**\nIntentando abortar proceso actual...")
             with open("SKIP_SIGNAL", "w") as f: f.write("SKIP")
            
    except Exception as e:
        print(f"[!] Error chequeando comandos: {e}")

def run_command(command, description):
    """Ejecuta un comando de sistema con salida en tiempo real."""
    global CURRENT_STEP
    CURRENT_STEP = description
    
    log(f"Iniciando: {description}", "ROCKET")
    log(f"CMD: {command}", "DEBUG")
    
    log(f"CMD: {command}", "DEBUG")
    
    start_time = time.time()
    last_tg_check = time.time()
    try:
        # Usamos Popen para streaming de salida real
        # CRÍTICO: encoding UTF-8 explícito para evitar errores charmap en Windows
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, # Unificar stderr en stdout
            encoding='utf-8',
            errors='replace',  # Reemplazar caracteres no decodificables con '?' en lugar de fallar
            bufsize=1,  # Line buffered
        )
        
        # Leer salida línea a línea mientras el proceso corre
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                try:
                    print(output, end='')  # Imprimir sin añadir newline extra
                    sys.stdout.flush()  # Forzar flush inmediato
                except UnicodeEncodeError:
                    # Fallback para consolas Windows limitadas (charmap)
                    try:
                        print(output.encode('ascii', 'replace').decode('ascii'), end='')
                        sys.stdout.flush()
                    except:
                        pass # Si falla todo, silenciar para no romper el flujo
            
            # CHECKPOINT: Telegram Check durante la ejecución
            # Para no saturar, chequeamos cada X líneas o tiempo. 
            # Simplificación: Chequear siempre que haya output podría ser mucho, 
            # pero dado el buffer, está bien. Mejor usar un timer simple.
            if time.time() - last_tg_check > 10: # Cada 10s
                check_telegram_commands()
                last_tg_check = time.time()
                
                if os.path.exists("SKIP_SIGNAL"):
                    log("Comando SKIP recibido. Terminando proceso actual...", "WARNING")
                    process.terminate()
                    os.remove("SKIP_SIGNAL")
                    break
             
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
    """Descarga datos basados en el régimen detectado + buffer."""
    
    regimen_file = "user_data/regimen_actual.json"
    days_to_download = DAYS_TO_DOWNLOAD  # Default fallback (180)
    
    # Intentar leer régimen para optimizar descarga
    if os.path.exists(regimen_file):
        try:
            with open(regimen_file, 'r', encoding='utf-8') as f:
                regimen_data = json.load(f)
            
            periodo = regimen_data.get('periodo_recomendado', {})
            start_date = periodo.get('inicio', '')
            
            if start_date:
                # Calcular días desde la fecha de inicio del régimen hasta hoy
                start_dt = datetime.strptime(start_date, "%Y%m%d")
                days_diff = (datetime.now() - start_dt).days
                
                # Agregar buffer de 30 días adicionales para seguridad
                days_to_download = days_diff + 30
                log(f"Régimen detectado. Descargando {days_to_download} días (desde {start_date})", "AI")
        except Exception as e:
            log(f"Error leyendo régimen para download: {e}. Usando {days_to_download} días.", "WARNING")
    
    cmd = f"{DOCKER_COMPOSE_CMD} download-data --config {CONFIG_FILE} --pairs-file {PAIRS_FILE} --days {days_to_download} -t {TIMEFRAME} --erase"
    return run_command(cmd, f"Descarga de Datos ({days_to_download} días)")

import zipfile

def get_backtest_result(filename):
    """Parsea el resultado del backtest (json o zip) con reintentos para robustez."""
    max_retries = 3
    for i in range(max_retries):
        try:
            last_result_path = "user_data/backtest_results/.last_result.json"
            if not os.path.exists(last_result_path):
                return None
            
            # Verificar si el archivo tiene contenido
            if os.path.getsize(last_result_path) == 0:
                log(f"Esperando escritura de .last_result.json (Intento {i+1})...", "DEBUG")
                time.sleep(1)
                continue

            with open(last_result_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                if not content:
                    continue
                pointer = json.loads(content)
                res_file = pointer['latest_backtest']
                latest_path = os.path.join("user_data", "backtest_results", res_file)
                
            if not os.path.exists(latest_path) or os.path.getsize(latest_path) == 0:
                 log(f"Esperando archivo de resultados {latest_path}...", "DEBUG")
                 time.sleep(1)
                 continue

            # Manejar formato ZIP (Nuevo en Freqtrade) o JSON directo
            if res_file.endswith('.zip'):
                with zipfile.ZipFile(latest_path, 'r') as zip_ref:
                    # El JSON dentro del ZIP suele tener el mismo nombre base
                    json_filename = res_file.replace('.zip', '.json')
                    if json_filename in zip_ref.namelist():
                        with zip_ref.open(json_filename) as f:
                            data = json.load(f)
                    else:
                        # Si no coincide el nombre, buscar cualquier .json
                        json_files = [f for f in zip_ref.namelist() if f.endswith('.json')]
                        if json_files:
                            with zip_ref.open(json_files[0]) as f:
                                data = json.load(f)
                        else:
                            log(f"No se encontró JSON dentro del ZIP {res_file}", "ERROR")
                            return None
            else:
                with open(latest_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                
            # Extraer métricas de la estrategia
            stats = data['strategy'][STRATEGY_NAME]
            return {
                'profit_total': stats['profit_total'],
                'profit_factor': stats['profit_factor'],
                'win_rate': stats['wins'] / stats['total_trades'] if stats['total_trades'] > 0 else 0,
                'total_trades': stats['total_trades']
            }
        except json.JSONDecodeError:
             log(f"Error decodificando JSON (Intento {i+1})...", "WARNING")
             time.sleep(1)
        except Exception as e:
            log(f"Error leyendo resultados backtest: {e}", "WARNING")
            time.sleep(1)
            
    log("No se pudo leer el resultado del backtest tras varios intentos.", "ERROR")
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
    
    if run_command(cmd, f"Backtest ({mode.upper()})"):
        return get_backtest_result(f"backtest_{mode}")
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

def step_hyperopt():
    """Hyperopt context-aware (Regime Based)."""
    
    timerange = ""
    regimen_file = "user_data/regimen_actual.json"
    
    # DEBUG: Verificar existencia del archivo
    log(f"Verificando archivo de régimen: {regimen_file}", "DEBUG")
    
    # 1. Consultar archivo de Régimen (Generado por Analista)
    if os.path.exists(regimen_file):
        log(f"Archivo {regimen_file} encontrado. Leyendo...", "DEBUG")
        try:
            with open(regimen_file, 'r', encoding='utf-8') as f:
                regimen_data = json.load(f)
            
            log(f"Contenido régimen: {json.dumps(regimen_data, indent=2)}", "DEBUG")
            
            periodo = regimen_data.get('periodo_recomendado', {})
            start_date = periodo.get('inicio', '')
            end_date = periodo.get('fin', '')
            
            log(f"Fechas parseadas - Inicio: {start_date}, Fin: {end_date}", "DEBUG")
            
            if start_date and end_date:
                # IMPORTANTE: Agregar buffer de inicio para Startup Candles (Indicadores)
                try:
                    start_dt = datetime.strptime(start_date, "%Y%m%d")
                    end_dt = datetime.strptime(end_date, "%Y%m%d")
                    
                    # Buffer de seguridad: +10 días inicio, -5 días fin
                    # Esto evita errores de "No data found" en los bordes
                    start_date_optim = (start_dt + timedelta(days=10)).strftime("%Y%m%d")
                    end_date_optim = (end_dt - timedelta(days=5)).strftime("%Y%m%d")
                    
                    timerange = f"--timerange {start_date_optim}-{end_date_optim}"
                    log(f"Régimen Detectado: {regimen_data.get('regimen')} ({regimen_data.get('direccion')})", "AI")
                    log(f"Datos espejo brutos: {start_date}-{end_date}", "AI")
                    log(f"Timerange optimización (seguro): {start_date_optim}-{end_date_optim}", "AI")
                    log(f"Comando timerange construido: {timerange}", "DEBUG")
                except ValueError as ve:
                    log(f"Error parseando fechas: {ve}. Usando fallback.", "ERROR")
                    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                    timerange = f"--timerange {start_date}-"
            else:
                log("Fechas de periodo espejo vacías en JSON. Usando fallback.", "WARNING")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                timerange = f"--timerange {start_date}-"
                
        except Exception as e:
            log(f"Error leyendo {regimen_file}: {e}. Usando fallback.", "ERROR")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            timerange = f"--timerange {start_date}-"
    else:
        log(f"{regimen_file} no encontrado. Usando fallback a últimos 30 días.", "WARNING")
        # Fallback a últimos 30 días
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        timerange = f"--timerange {start_date}-"

    spaces = "buy sell trailing"  # Removed roi and stoploss as they are not defined in strategy
    
    # Ajuste de Epochs para entorno OCI (Puede ser lento con 1000)
    # Usuario tiene 1GB RAM + 4GB SWAP -> 100 epochs es seguro para probar
    # ESTRATEGIA ADAPTATIVA DE ÉPOCAS
    # Intentamos 1000 (Calidad Máxima) -> 500 (Media) -> 100 (Rápida)
    epoch_ladder = [1000, 500, 100]
    
    for i, epochs in enumerate(epoch_ladder):
        log(f"Hyperopt: Intentando con {epochs} épocas...", "AI")
        
        # Reconstruimos comando con las épocas actuales
        cmd = (
            f"{DOCKER_COMPOSE_CMD} hyperopt "
            f"--config {CONFIG_FILE} "
            f"--strategy {STRATEGY_NAME} "
            f"--hyperopt-loss SharpeHyperOptLoss "
            f"--spaces {spaces} "
            f"--epochs {epochs} "
            f"-j 1 "
            f"--timeframe {TIMEFRAME} "
            f"{timerange}"
        )

        # Limpieza agresiva de lockfile
        if os.path.exists("user_data/hyperopt.lock"):
            try:
                os.remove("user_data/hyperopt.lock")
                log("Lockfile eliminado.", "DEBUG")
            except: pass
            
        if run_command(cmd, f"Hyperopt ({epochs} Epochs)"):
            return extract_params_from_hyperopt()
        
        log(f"Fallo en Hyperopt con {epochs} épocas. Esperando 30s...", "WARNING")
        time.sleep(30)
        
        # Intentar matar contenedor zombie
        os.system(f"{DOCKER_COMPOSE_CMD} kill >nul 2>&1")

    # FALLBACK INTELIGENTE: Hyperopt Mini (Low Memory / Low Duration)
    log("ACTIVANDO PROTOCOLO DE EMERGENCIA: Hyperopt Mini.", "WARNING")
    # Reducimos a 10 Epochs y 7 días de datos para minimizar carga
    mini_timerange = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    
    cmd_mini = (
        f"{DOCKER_COMPOSE_CMD} hyperopt "
        f"--config {CONFIG_FILE} "
        f"--strategy {STRATEGY_NAME} "
        f"--hyperopt-loss SharpeHyperOptLoss "
        f"--spaces {spaces} "
        f"--epochs 10 "
        f"-j 1 "
        f"--timeframe {TIMEFRAME} "
        f"--timerange {mini_timerange}-"
    )
    
    if run_command(cmd_mini, "Hyperopt Mini (Emergencia)"):
        log("Hyperopt Mini completado con éxito. Salvamos el ciclo.", "SUCCESS")
        return extract_params_from_hyperopt()
        
    log("Hyperopt Mini también falló.", "ERROR")
    return False

def deploy_params():
    """Actualiza la configuración de producción con los nuevos parámetros."""
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
                    
                    os.system(f"git add {DEPLOY_CONFIG_FILE} user_data/strategies/{STRATEGY_NAME}.py")
                    msg_commit = f"Mejora Detectada - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    os.system(f'git commit -m "{msg_commit}" >nul 2>&1')
                    log("Memoria de Estrategia guardada en Git local.", "SUCCESS")
                    
                    # PUSH A REPOSITORIO REMOTO (si existe)
                    # Verificar si hay remote configurado
                    check_remote = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
                    if check_remote.stdout.strip():  # Si hay remotes configurados
                        log("Sincronizando con repositorio remoto...", "INFO")
                        push_result = os.system("git push origin main >nul 2>&1")  # Intenta main primero
                        if push_result != 0:
                            push_result = os.system("git push origin master >nul 2>&1")  # Fallback a master
                        
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
    """Ejecuta el protocolo completo Chacal."""
    log("INICIANDO CICLO DE MEJORA CONTINUA", "START")
    
    # Limpieza preventiva para evitar "Another running instance"
    log("Limpiando entorno Docker...", "DEBUG")
    os.system(f"{DOCKER_COMPOSE_CMD} down -v >nul 2>&1") 
    
    # Check Comandos antes de empezar
    check_telegram_commands()
    if os.path.exists("STOP_SIGNAL"):
        log("Señal de PARADA detectada. Abortando.", "WARNING")
        return
    
    # 1. Download
    if not step_download_data(): return 
    
    # 2. Backtest Basal
    baseline = step_backtest("basal")
    
    if baseline:
        log(f"BASELINE: Profit {baseline['profit_total']:.2%} | WinRate {baseline['win_rate']:.2%} | Trades: {baseline['total_trades']}", "STATS")
        if baseline['total_trades'] == 0:
            log("ATENCIÓN: 0 trades detectados en el basal.", "WARNING")
    
    # 3. Hyperopt
    check_telegram_commands()
    if os.path.exists("STOP_SIGNAL"): return
    
    hyperopt_success = step_hyperopt()
    
    if not hyperopt_success:
        log("Fallo en Hyperopt. ACTIVANDO PROTOCOLO DE CONTINGENCIA.", "WARNING")
        log("Saltando a Validación con parámetros anteriores...", "AI")
    
    # 4. Validación (Se ejecuta siempre, incluso si falló hyperopt, para mantener trading vivo)
    # Si hyperopt falló, validation usará el config basal o lo que haya en params.json
    validation = step_backtest("validation")
    if validation:
        log(f"VALIDATION: Profit {validation['profit_total']:.2%} | WinRate {validation['win_rate']:.2%} | Trades: {validation['total_trades']}", "STATS")
        
        # 5. Comparación y Decisión
        if not baseline or validation['profit_total'] > baseline['profit_total']:
            log("¡MEJORA DETECTADA! Nuevos parámetros aprobados.", "SUCCESS")
            # Desplegar cambios
            if deploy_params():
                # REACTIVAR DRY RUN AUTOMÁTICAMENTE
                log("Reactivando DRY RUN con nuevos parámetros...", "AI")
                try:
                    # Verificar si hay un proceso dry-run anterior corriendo
                    check_cmd = "docker ps --filter name=freqtrade --filter status=running --quiet"
                    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                    
                    if check_result.stdout.strip():
                        log("Proceso DRY RUN anterior detectado. Reiniciando...", "INFO")
                        os.system(f"{DOCKER_COMPOSE_CMD} down >nul 2>&1")
                        time.sleep(5)
                    
                    # Iniciar DRY RUN en background con configuración actualizada
                    dry_cmd = f"docker compose up -d"
                    result = os.system(dry_cmd)
                    
                    if result == 0:
                        log("DRY RUN ACTIVO con parámetros optimizados.", "SUCCESS")
                        send_telegram_msg("✅ BOT REACTIVADO en DRY RUN con parámetros mejorados.")
                    else:
                        log("Error al iniciar DRY RUN. Revisar Docker.", "ERROR")
                        
                except Exception as e:
                    log(f"Error reactivando DRY RUN: {e}", "ERROR")
                    
                log("Ciclo finalizado con ÉXITO. Sistema esperando siguiente vuelta.", "INFO")
            else:
                log("Fallo en despliegue de parámetros.", "ERROR")
        else:
            log("Resultado inferior al basal o insuficiente mejora. Se mantienen parámetros.", "WARNING")

def main():
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

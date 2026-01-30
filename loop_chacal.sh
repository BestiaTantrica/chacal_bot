#!/bin/bash
# =====================================================
# LOOP CHACAL INFINITO V1.0 - AUTONOMOUS AWS
# =====================================================
# Orquesta la ejecución continua de 'comandante.py'.
# Si falla, espera y reintenta. Si tiene éxito, duerme
# hasta el siguiente ciclo (ej. 24 horas).
# =====================================================

BASE_DIR="$HOME/chacal_bot"
LOG_FILE="$BASE_DIR/loop_activity.log"
PYTHON_CMD="python3"
INTERVAL_SECONDS=86400  # 24 Horas entre ciclos

cd $BASE_DIR || exit 1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [LOOP] $1" | tee -a $LOG_FILE
}

log "🐺 CHACAL AUTONOMOUS LOOP INICIADO 🐺"

while true; do
    log "Iniciando nuevo ciclo de optimización..."
    
    # Ejecutar Comandante con timeout de seguridad (ej. 12 horas máx por ciclo)
    timeout 12h $PYTHON_CMD comandante.py --action cycle
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log "✅ Ciclo completado con éxito."
        log "Durmiendo $INTERVAL_SECONDS segundos..."
        sleep $INTERVAL_SECONDS
    elif [ $EXIT_CODE -eq 124 ]; then
        log "❌ TIMEOUT detectado. El ciclo tardó más de 12 horas."
        # Podríamos notificar a Telegram acá si comandante no pudo
        sleep 3600 # Esperar 1 hora antes de intentar de nuevo
    else
        log "⚠️ Error en ciclo (Exit Code: $EXIT_CODE). Reintentando en 1 hora..."
        sleep 3600
    fi
done

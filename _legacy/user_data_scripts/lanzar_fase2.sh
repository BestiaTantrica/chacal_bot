#!/bin/bash
# LANZADOR AUTOMÁTICO FASE 2: PROTOCOLO CHACAL REFINADO (5m)
# -------------------------------------------------------------
# VERSIÓN "LOW RAM": Ejecución estrictamente secuencial.
# 1. DESCARGA: Una por una.
# 2. PODA: Una vez descargado todo, se procesa (el script python es ligero).
# 3. EJECUCIÓN: Cola secuencial.

# Monedas Elite
COINS=("BTC/USDT:USDT" "ETH/USDT:USDT" "SOL/USDT:USDT" "XRP/USDT:USDT" "ADA/USDT:USDT" "DOT/USDT:USDT" "DOGE/USDT:USDT" "AVAX/USDT:USDT" "LINK/USDT:USDT" "BNB/USDT:USDT" "SUI/USDT:USDT" "NEAR/USDT:USDT")

echo "============================================="
echo "   INICIANDO FASE 2: REFINAMIENTO DE FRANCOTIRADOR"
echo "   MODO: PROTECCIÓN DE RAM (Secuencial)"
echo "============================================="

# PASO 1: DESCARGA DE DATOS (SECUENCIAL)
echo "[1/3] Descargando datos de 5m (365 días)..."

for PAIR in "${COINS[@]}"; do
    NAME=$(echo $PAIR | cut -d'/' -f1)
    echo ">> Bajando datos para: $NAME"
    
    # Descarga individual para evitar picos de memoria
    sudo docker-compose -f docker-compose_relevo.yml run --rm chacal_alpha download-data \
        --pairs "$PAIR" \
        --exchange binance \
        --timeframe 5m \
        --days 365 \
        --data-format-ohlcv feather \
        --dl-path user_data/data/binance/futures_backup > /dev/null 2>&1
        
    if [ $? -ne 0 ]; then
        echo "   [!] Advertencia: Problema descargando $NAME. Continuando..."
    else
        echo "   [OK] $NAME descargado."
    fi
    # Pequeña pausa para dejar respirar a la CPU
    sleep 2
done

echo "Descarga Completada."

# PASO 2: PODA QUIRURGICA (HORAS MÁGICAS)
echo "[2/3] Ejecutando Poda Quirúrgica..."
# El script de python usa Pandas y procesa archivo por archivo.
# El consumo de RAM es bajo (carga 1 archivo a la vez). Safe for t2.micro.
sudo docker-compose -f docker-compose_relevo.yml run --rm chacal_alpha python3 /freqtrade/user_data/podar_datos_5m.py

if [ $? -ne 0 ]; then
    echo "ERROR CRÍTICO: Falló la poda de datos. Abortando."
    exit 1
fi
echo "Poda Completada."

# PASO 3: EJECUCIÓN DE HYPEROPT
echo "[3/3] Lanzando Cola de Hyperopt 5m (1000 épocas)..."
# Usamos el script cola_hyperopt_5m.sh que ya preparamos
chmod +x user_data/cola_hyperopt_5m.sh
./user_data/cola_hyperopt_5m.sh

echo "============================================="
echo "   FASE 2 COMPLETADA CON HONOR"
echo "============================================="

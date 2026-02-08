#!/bin/bash
# Script Quirúrgico de Memoria - MUNDO TRADE
# Obligamos a que lea el archivo de ESTA carpeta, no de la central.

REPO_DIR="$( pwd )"
PROMPT_FILE="$REPO_DIR/memory/PROMPT_LLAVE.md"

echo "📍 REPO ACTUAL: $REPO_DIR"
echo "Buscando actualizaciones en la nube..."
git pull origin main --quiet

if [ -f "$PROMPT_FILE" ]; then
    echo -e "\n--- CONTENIDO DE MEMORIA TRADE ---"
    cat "$PROMPT_FILE"
    echo -e "\n--------------------------------------------------"
    echo -e "      🦅 MEMORIA PEGASO SINCRONIZADA (TRADE)"
    echo -e "--------------------------------------------------"
else
    echo "❌ Error: No se encuentra $PROMPT_FILE"
fi

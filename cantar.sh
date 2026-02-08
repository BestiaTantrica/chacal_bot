#!/bin/bash
# 🦅 CANTAR: Lector de Memoria (Mundo Trade)
# Prohibido leer hilos de otros repositorios.

# Detectamos la ruta real del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROMPT_FILE="$SCRIPT_DIR/memory/PROMPT_LLAVE.md"

echo "Buscando actualizaciones en la nube..."
git -C "$SCRIPT_DIR" pull origin main --quiet

if [ -f "$PROMPT_FILE" ]; then
    echo -e "\n--- CONTEXTO MUNDO TRADE ---"
    cat "$PROMPT_FILE"
    echo -e "\n--------------------------------------------------"
    echo -e "      🦅 PEGASO TRADING SYSTEM (LOCAL)"
    echo -e "--------------------------------------------------"
else
    echo "❌ Error: No se encuentra la memoria en $PROMPT_FILE"
fi

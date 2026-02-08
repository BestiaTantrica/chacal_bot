#!/bin/bash
# 🦅 CANTAR: Lector de Memoria Quirúrgica
# Este script lee la memoria del repositorio actual.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROMPT_FILE="$SCRIPT_DIR/memory/PROMPT_LLAVE.md"

if [ -f "$PROMPT_FILE" ]; then
    echo -e "\n--- [ CONTEXTO MUNDO TRADE ] ---"
    cat "$PROMPT_FILE"
    echo -e "\n--------------------------------------------------"
    echo -e "      🦅 PEGASO TRADING SYSTEM (v3.0.1)"
    echo -e "--------------------------------------------------"
else
    echo "❌ Error: Memoria no encontrada. Tira un 'git pull' o 'git reset --hard origin/main'."
fi

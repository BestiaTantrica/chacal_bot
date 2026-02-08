#!/bin/bash
# Script de lectura de memoria con Auto-Pull
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Buscando actualizaciones en la nube..."
git -C "$REPO_DIR" pull

PROMPT_FILE="$REPO_DIR/memory/PROMPT_LLAVE.md"

if [ -f "$PROMPT_FILE" ]; then
    cat "$PROMPT_FILE"
    echo -e "\n--------------------------------------------------"
    echo -e "      🦅 MEMORIA PEGASO SINCRONIZADA (TERMUX)"
    echo -e "--------------------------------------------------"
else
    echo "❌ Error: No se encuentra el archivo de memoria."
fi

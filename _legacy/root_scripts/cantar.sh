#!/bin/bash
# 🦅 CANTAR: Lector de Memoria Quirúrgica (MUNDO TRADE)
# Sincronización automática con la nube antes de leer.

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Buscando actualizaciones de MUNDO TRADE..."
# Sincronización forzada silenciosa para estar siempre al día
git -C "$REPO_DIR" fetch origin >/dev/null 2>&1
BRANCH=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)
git -C "$REPO_DIR" reset --hard origin/$BRANCH >/dev/null 2>&1

PROMPT_FILE="$REPO_DIR/memory/PROMPT_LLAVE.md"

if [ -f "$PROMPT_FILE" ]; then
    echo -e "\n--- [ CONTEXTO MUNDO TRADE: CHACAL V4 ] ---"
    cat "$PROMPT_FILE"
    echo -e "\n--------------------------------------------------"
    echo -e "      🦅 PEGASO TRADING SYSTEM (Sincronizado)"
    echo -e "--------------------------------------------------"
else
    echo "❌ Error: Memoria de Trading no encontrada."
fi

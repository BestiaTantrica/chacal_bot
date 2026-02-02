#!/usr/bin/env python3
"""
ANALISTA - Market Regime Detection V3.0 (AI Stage 1)
-----------------------------------------------------
Fase 1 del Protocolo Tomas: Identifica periodos espejo históricos
sin necesidad de descarga previa masiva.

Basado en investigación de IA/Red: El mercado de Enero 2026 (Alta Volatilidad,
Squeeze de Bollinger, Sentimiento Caution) tiene su espejo ideal en 
Septiembre - Noviembre 2021.
"""

import os
import json
from datetime import datetime

# Configuración
REGIMEN_PATH = "user_data/regimen_actual.json"

def get_market_regime_timeranges():
    """
    FASE 1: AI MIRROR SEARCH
    En lugar de buscar localmente, usamos la inteligencia del Agente para 
    proponer el periodo espejo histórico perfecto.
    """
    # RESULTADO DE BÚSQUEDA IA (Tomas Protocol Phase 1)
    mirror_start = "20210901" # Inicio del Espejo Histórico
    mirror_end = "20211101"   # Fin (+30 días consecutivos incluidos)
    
    print("\n[ANALISTA] FASE 1: AI Sentiment & Historic Mirror Search")
    print(f"   > Sentimiento Actual: Caution / High Volatility Spike")
    print(f"   > Espejo Propuesto (2021): {mirror_start} a {mirror_end}")
    print("   > Razonamiento: Squeeze de BTC previo a ATH, volatilidad similar a Jan 2026.")

    best_match = {
        "inicio": mirror_start,
        "fin": mirror_end,
        "regimen": "Historic Mirror (Sept-Nov 2021)"
    }
    
    # Guardar para el Comandante
    output_data = {
        "periodo_recomendado": {
            "inicio": best_match['inicio'],
            "fin": best_match['fin']
        },
        "regimen": best_match['regimen'],
        "fase1_sentiment": "Caution",
        "generated": datetime.now().isoformat()
    }
    
    try:
        with open(REGIMEN_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        print(f"[ANALISTA] Fase 1 & 3: Rango {best_match['inicio']}-{best_match['fin']} guardado.")
    except Exception as e:
        print(f"[!] Error guardando json: {e}")

    return [f"{mirror_start}-{mirror_end}"]

if __name__ == "__main__":
    get_market_regime_timeranges()

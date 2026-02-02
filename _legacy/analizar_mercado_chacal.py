#!/usr/bin/env python3
"""
ANALIZADOR DE MERCADO CHACAL
==============================
Propósito: Análisis automatizado de pares de trading para
           selección inteligente basada en métricas cuantitativas

Métricas analizadas:
- Volatilidad (desviación estándar de retornos)
- Volumen promedio (liquidez)
- Sharpe Ratio (retorno ajustado por riesgo)
- Drawdown máximo
- Tendencia (correlación lineal)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import sys

# Asegurar que estamos en el entorno correcto
try:
    from freqtrade.data.history import load_pair_history
    from freqtrade.configuration import Configuration
except ImportError:
    print("❌ Error: Este script debe ejecutarse desde el entorno virtual de Freqtrade")
    print("   Ejecuta: source ~/freqtrade/.venv/bin/activate")
    sys.exit(1)


def calcular_metricas_par(dataframe: pd.DataFrame, par: str) -> dict:
    """
    Calcula métricas cuantitativas para un par de trading
    """
    # Calcular retornos
    df = dataframe.copy()
    df['returns'] = df['close'].pct_change()
    
    # Métricas básicas
    volatilidad = df['returns'].std() * np.sqrt(288)  # Anualizada para 5min candles
    volumen_promedio = df['volume'].mean()
    precio_promedio = df['close'].mean()
    
    # Sharpe Ratio simplificado (asumiendo risk-free rate = 0)
    retorno_promedio = df['returns'].mean() * 288 * 365  # Anualizado
    sharpe = retorno_promedio / volatilidad if volatilidad > 0 else 0
    
    # Drawdown máximo
    cumulative = (1 + df['returns']).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Tendencia (correlación con tiempo)
    x = np.arange(len(df))
    correlacion = np.corrcoef(x, df['close'])[0, 1]
    
    return {
        'par': par,
        'volatilidad': round(volatilidad, 4),
        'volumen_promedio': round(volumen_promedio, 2),
        'precio_promedio': round(precio_promedio, 4),
        'sharpe_ratio': round(sharpe, 3),
        'max_drawdown': round(max_drawdown, 4),
        'tendencia': round(correlacion, 4),
        'score_chacal': 0  # Se calculará después
    }


def calcular_score_chacal(metrica: dict) -> float:
    """
    Calcula un score compuesto para priorizar pares óptimos
    
    Criterios Chacal:
    - Alta liquidez (volumen)
    - Volatilidad moderada (oportunidad sin riesgo extremo)
    - Sharpe positivo
    - Drawdown controlado
    """
    score = 0
    
    # Componente 1: Sharpe Ratio (30% del score)
    if metrica['sharpe_ratio'] > 0:
        score += min(metrica['sharpe_ratio'] * 15, 30)
    
    # Componente 2: Volatilidad óptima (25% del score)
    # Preferir volatilidad entre 0.2 y 0.6 (2% - 6% diario aprox)
    vol = metrica['volatilidad']
    if 0.2 <= vol <= 0.6:
        score += 25
    elif 0.1 <= vol < 0.2 or 0.6 < vol <= 0.8:
        score += 15
    
    # Componente 3: Drawdown controlado (20% del score)
    dd = abs(metrica['max_drawdown'])
    if dd < 0.15:  # Menos de 15% drawdown
        score += 20
    elif dd < 0.25:
        score += 10
    
    # Componente 4: Liquidez (25% del score)
    # Normalizado - asignamos puntos relativos
    score += 25  # Se ajustará después con normalización
    
    return round(score, 2)


def main():
    print("=" * 60)
    print("🐺 ANALIZADOR DE MERCADO CHACAL")
    print("=" * 60)
    print()
    
    # Cargar configuración
    config_path = Path.home() / 'freqtrade' / 'user_data' / 'config_chacal_oci.json'
    
    if not config_path.exists():
        print(f"❌ Error: No se encontró {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Pares a analizar
    pares = [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
        "ADA/USDT", "DOGE/USDT", "MATIC/USDT", "DOT/USDT", "AVAX/USDT",
        "LINK/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "TRX/USDT"
    ]
    
    print(f"📊 Analizando {len(pares)} pares...")
    print()
    
    # Analizar cada par
    resultados = []
    data_dir = Path.home() / 'freqtrade' / 'user_data' / 'data' / 'binance'
    
    for par in pares:
        try:
            # Intentar cargar datos
            df = pd.read_json(
                data_dir / f"{par.replace('/', '_')}-5m.json"
            )
            
            if len(df) < 100:
                print(f"⚠️  {par}: Datos insuficientes, omitiendo...")
                continue
            
            metricas = calcular_metricas_par(df, par)
            resultados.append(metricas)
            print(f"✅ {par}: Análisis completado")
            
        except FileNotFoundError:
            print(f"⚠️  {par}: Datos no encontrados, omitiendo...")
            continue
        except Exception as e:
            print(f"❌ {par}: Error - {str(e)}")
            continue
    
    if not resultados:
        print("\n❌ No se pudo analizar ningún par. Verifica que los datos estén descargados.")
        sys.exit(1)
    
    # Normalizar volumen para el score
    volumenes = [r['volumen_promedio'] for r in resultados]
    vol_max = max(volumenes)
    
    for r in resultados:
        r['score_volumen'] = (r['volumen_promedio'] / vol_max) * 25
        r['score_chacal'] = calcular_score_chacal(r)
        r['score_chacal'] += r['score_volumen']  # Agregar componente de liquidez
    
    # Ordenar por score
    resultados_ordenados = sorted(resultados, key=lambda x: x['score_chacal'], reverse=True)
    
    # Mostrar resultados
    print()
    print("=" * 60)
    print("🏆 RANKING CHACAL (Top 10)")
    print("=" * 60)
    print()
    
    header = f"{'Rank':<6} {'Par':<12} {'Score':<8} {'Sharpe':<8} {'Vol%':<8} {'DD%':<8}"
    print(header)
    print("-" * 60)
    
    top_10 = resultados_ordenados[:10]
    for i, r in enumerate(top_10, 1):
        row = (f"{i:<6} {r['par']:<12} {r['score_chacal']:<8.1f} "
               f"{r['sharpe_ratio']:<8.2f} {r['volatilidad']*100:<8.1f} "
               f"{abs(r['max_drawdown'])*100:<8.1f}")
        print(row)
    
    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path.home() / 'freqtrade' / 'user_data' / f'analisis_chacal_{timestamp}.json'
    
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'top_10_pares': [r['par'] for r in top_10],
            'resultados_completos': resultados_ordenados
        }, f, indent=2)
    
    print()
    print(f"💾 Reporte guardado: {report_path}")
    print()
    print("🎯 RECOMENDACIÓN:")
    print(f"   Usar estos {len(top_10)} pares en config_chacal_oci.json")
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()

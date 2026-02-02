# Análisis de Pares - Protocolo Darwin

## Fecha: 2026-02-01

## Metodología

- **Período analizado**: Últimos 30 días (data diaria)
- **Métrica principal**: Correlación de retornos con BTC
- **Criterios secundarios**: Volumen 24h, volatilidad

## Resultados del Análisis

### Ranking Completo (por score compuesto)

| Posición | Par | Correlación BTC | Volumen 24h | Score |
|----------|-----|-----------------|-------------|-------|
| 1 | **LINK** | 0.941 | $33.8M | 72.32 |
| 2 | **ETH** | 0.935 | $1,096M | 71.69 |
| 3 | **BNB** | 0.926 | $130M | 70.77 |
| 4 | **SOL** | 0.918 | $368M | 70.10 |
| 5 | **ADA** | 0.893 | $46M | 68.56 |
| 6 | **DOGE** | 0.889 | $109M | 68.28 |
| 7 | **AVAX** | 0.880 | $32M | 69.39 |
| 8 | **DOT** | 0.880 | $12M | 68.24 |
| 9 | **XRP** | 0.776 | $226M | 64.63 |
| 10 | **BTC** | 1.000 | $1,414M | 100 |

## Pares Seleccionados (8)

✅ **BTC/USDT** - Referencia (correlación perfecta)
✅ **ETH/USDT** - Correlación 0.935, máxima liquidez
✅ **SOL/USDT** - Correlación 0.918, alta liquidez
✅ **BNB/USDT** - Correlación 0.926, ecosistema Binance
✅ **LINK/USDT** - Correlación 0.941 (la más alta)
✅ **DOGE/USDT** - Correlación 0.889, buena liquidez
✅ **ADA/USDT** - Correlación 0.893
✅ **XRP/USDT** - Correlación 0.776, alta liquidez

## Pares Descartados (2)

❌ **AVAX/USDT** - Correlación 0.880 (buena), pero volumen bajo vs otros
❌ **DOT/USDT** - Correlación 0.880, volumen más bajo ($12M)

## Decisión Final

**8 pares fijos** con correlación BTC >0.77 y balance liquidez/correlación.

### Próximo Paso

Ejecutar **hyperopt secuencial** para cada par:

- Epochs: 100 por par
- Tiempo estimado: ~50 min/par
- Total: ~6-7 horas para los 8 pares

## Observaciones

1. **LINK tiene la correlación más alta** (0.941) - candidato fuerte
2. **ETH y BNB** tienen liquidez masiva - bajo riesgo de slippage
3. **DOGE incluido** a pesar de ser memecoin porque correlación >0.88
4. **XRP el más débil** en correlación (0.776) pero se mantiene por liquidez

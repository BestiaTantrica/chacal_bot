# 🦅 ESTADO ACTUAL: MUNDO TRADE (CHACAL V4)

## ESTRUCTURA DE MEMORIA

- **Mundo**: Trade (Trading & Algos)
- **Proyecto**: Chacal V4 (Freqtrade @ AWS)
- **Estrategia**: `ChacalPulseV4_Hyperopt` (Long/Short)
- **Metodologia**: Hyperopt Secuencial (AWS t2.micro + 4GB SWAP)

---

## 🚀 AVANCE FASE 2 (REFINAMIENTO 5M)

| Torre | Monedas | Info / Dataset | Estado |
| :--- | :--- | :--- | :--- |
| **Alpha** | BTC, ETH, SOL | 365d / 1000 épocas | ✅ COMPLETADO |
| **Beta** | BNB, XRP, ADA | 365d / 1000 épocas | ✅ COMPLETADO |
| **Gamma** | DOGE, AVAX, LINK | 365d / 1000 épocas | ✅ COMPLETADO |
| **Delta** | DOT, SUI, NEAR | 365d / 1000 épocas | 🚀 NEAR (~99%) |

## 📊 AUDITORÍA DE RENTABILIDAD (TOP 5)

1. 🔥 **LINK**: **+196.35%** (La joya de la corona, 15 losses en 1 año).
2. 🔥 **SUI**: **+106.95%** (Agresividad quirúrgica).
3. 🔥 **DOGE**: **+105.29%** (Volumen máximo).
4. 🔥 **AVAX**: **+47.45%** (Calidad por trade alta).
5. 🔥 **BNB**: **+28.88%** (Estabilidad sólida).

## 🛠️ PARÁMETROS DE REGLA (PODA)

- **Dataset**: Binance Futures (USDT).
- **Timeframe**: 5 minutos.
- **Poda Energética**: Filtrado para operar solo en **Londres/NY** (Horas de Volatilidad).
- **RAM Protection**: 1 solo worker (`job-workers 1`) para evitar OOM Crash.

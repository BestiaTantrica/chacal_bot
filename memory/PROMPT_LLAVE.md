# 🦅 MEMORIA PEGASO: MUNDO TRADE (CHACAL V4)

**FECHA DE GENERACION:** 2026-02-08
**ESTADO:** OPERACIONAL (REFINAMIENTO FINAL)

---

# 🚀 INFORME ESTRATÉGICO: FASE 2 (REFINAMIENTO INDUSTRIAL)

Estamos en el cierre de la Fase 2 del Protocolo Chacal V4. El objetivo es consolidar la biblioteca quirúrgica de 12 monedas sobre **velas de 5 minutos** con un dataset de **un año completo (365+ días)** y una optimización bayesiana de **1000 épocas por moneda**.

## 📊 ESTADO DE LAS TORRES

- **ALPHA (BTC, ETH, SOL)**: ✅ Parámetros industriales validados. BTC (+16.7%).
- **BETA (BNB, XRP, ADA)**: ✅ Estabilidad confirmada. BNB (+28%).
- **GAMMA (DOGE, AVAX, LINK)**: ✅ **MÁXIMA RENTABILIDAD**. LINK (+196%), DOGE (+105%).
- **DELTA (DOT, SUI, NEAR)**: ⏳ **NEAR** procesando el último bloque de épocas. SUI validada (+106%).

## 🎯 METODOLOGÍA DEL "CHACAL" (SISTEMA DUAL)

1. **FASE 1: EXPLORACIÓN (1m)**: Primer acercamiento quirúrgico. Se usan velas de 1 minuto sobre 60-120 días para capturar el "Hunter Mode" (reacción rápida). Vital para entender la micro-volatilidad inicial de cada moneda.
2. **FASE 2: REFINAMIENTO (5m)**: Paso a escala industrial (en curso). Velas de 5 minutos sobre **1 año completo**. Objetivo: estabilidad a largo plazo y rentabilidad sostenida.
3. **PODA MÁGICA**: Se aplica en ambas fases. Se elimina el 80% del ruido filtrando solo las horas de alta volatilidad (**Londres/NY**).
4. **MODO FANTASMA**: Ejecución secuencial con 1 worker (`job-workers 1`) para proteger la RAM de 1GB.
5. **LÓGICA DUAL**: Optimización obligatoria para **Long** y **Short**.

## 🛠️ INFRAESTRUCTURA AWS

- Instancia `t2.micro` operando al 95% de CPU de forma estable.
- SWAP de 4GB configurado y persistente.
- Scripts de "Cola" (`cola_hyperopt_5m`) reparados para sintaxis de futuros Binance (:USDT).

---

## 📜 HILOS DE CONOCIMIENTO RECIENTES

### Metodología de Fase 1 y 2

Explicación de por qué pasamos de 1m a 5m. La fase 1 captura la esencia, la fase 2 la robustez industrial. La poda es el filtro de pureza.

### Reparación de Fase 2

Crónica de la recuperación después del fallo de sintaxis. Se regeneraron 12 configs y se limpió el repositorio para evitar basura cruzada.

---
**INSTRUCCION:** Si lees esto, tenés el contexto completo del Mundo Trade. No inventes info de otros mundos.

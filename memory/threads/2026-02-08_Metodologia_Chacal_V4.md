# METODOLOGÍA QUIRÚRGICA: PROTOCOLO CHACAL V4

Fecha: 2026-02-08 22:15:00
Tags: metodología, hyperopt, horas-mágicas, arquitectura

## RESUMEN DE LA CHARLA

Documentación de la metodología de optimización compuesta para el mercado de Binance Futures (USDT). Este proceso está diseñado para maximizar rentabilidad en servidores de bajos recursos (1GB RAM) sin sacrificar robustez estadística.

### 1. PRINCIPIOS FUNDAMENTALES (ORDEN ESTRUCTURAL)

- **Poda de Datos (Horas Mágicas)**: En lugar de procesar 24h de ruido, el sistema trunca los datasets de 1m y 5m para dejar solo las sesiones de Londres y Nueva York (Volatilidad Real). Esto reduce el peso de los datos en un ~80% y enfoca al algoritmo en momentos donde el volumen impulsa la estrategia.
- **Ejecución en 4 Torres**: Segmentación de 12 monedas en 4 grupos (Alpha, Beta, Gamma, Delta) de 3 monedas cada uno. Ejecución **secuencial** (no paralela) para evitar el OOM Killer en instancias AWS Micro.
- **Modo Short**: Activación obligatoria de operaciones en corto (`can_short: True`) para capitalizar tendencias bajistas en cripto.

### 2. FASES DEL DISEÑO DE ESTRATEGIA

- **FASE 1 (Aproximación Quirúrgica)**:
  - Timeframe: **1m**.
  - Datos: 60-120 días.
  - Objetivo: Recuperar parámetros base ("Hunter Mode") y factores de volumen rápidos.
  
- **FASE 2 (Refinamiento Industrial - ESTADO ACTUAL)**:
  - Timeframe: **5m**.
  - Datos: **365+ días (1 año completo)**.
  - Épocas: 1000 por moneda (Optimización Bayesiana).
  - Objetivo: Estabilidad a largo plazo, validación de ciclos Bull/Bear y optimización del Sharpe Ratio.

### 3. FLUJO DE DATOS CORPORATIVO

`Descarga Directa (Futures) -> Poda (Magic Hours) -> Hyperopt Secuencial (Torres) -> Unificación JSON`.

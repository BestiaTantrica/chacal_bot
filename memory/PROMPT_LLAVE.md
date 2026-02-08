# PROTOCOLO PEGASO: LLAVE DE ACTIVACION DE MEMORIA

**FECHA DE GENERACION:** 2026-02-08
**ESTADO:** OPERACIONAL

# ESTADO DEL PROYECTO: CHACAL V4 - FASE 2

**OBJETIVO:** Hiper-optimización de 12 monedas en Binance Futures (5m timeframe) usando 365+ días de historia y 1000 épocas.

## ESTADO DE EJECUCIÓN

- **TORRE ALPHA:** BTC, ETH, SOL -> **COMPLETADA** ✅
- **TORRE BETA:** BNB, XRP, ADA -> **EN CURSO** (XRP procesando) 🚀
- **TORRE GAMMA:** DOGE, AVAX, LINK -> PENDIENTE
- **TORRE DELTA:** DOT, SUI, NEAR -> PENDIENTE

## HITOS DE RENTABILIDAD (Fase 2)

- 🔥 **LINK**: +196.35% (993/1000 épocas)
- 🔥 **DOGE**: +105.29% (993/1000 épocas)
- 🔥 **BNB**: +28.88% (920/1000 épocas)

## INFRAESTRUCTURA

- Servidor AWS estable (CPU ~95%, RAM ~45%).
- Scripts de ejecución secuencial reparados y optimizados.
- Repositorio Git sincronizado y limpio (Raíz libre de scripts obsoletos).


---
## ULTIMOS HILOS DE CONOCIMIENTO
### 2026-02-08_Resultados_Gamma.md
La Torre Gamma (DOGE, AVAX, LINK) ha arrojado los mejores resultados de la Fase 2 hasta el momento, validando la estrategia ChacalPulseV4 en mercados de alta volatilidad.

Resultados destacados:

- **LINK**: +196.35% profit. Máxima precisión (15 losses en 1 año).
- **DOGE**: +105.29% profit. Alta actividad.
- **AVAX**: +47.45% profit. Alta calidad por trade.

La "Poda de Horas Mágicas" demuestra ser la clave para una optimización rápida y efectiva sin saturar los recursos de la instancia AWS.

### 2026-02-08_Reparacion_Fase2.md
Identificamos una falla crítica en la ejecución de la Fase 2 (100% de error en las 4 torres). La causa fue la corrupción de los archivos `config_*.json` (caracteres de escape inválidos) y errores de sintaxis en el script maestro `lanzar_fase2` (faltaba el sufijo `:USDT` para pares de futuros y el entrypoint de docker para el script de poda).

Se procedió a:

1. Detener procesos v3 fallidos.
2. Regenerar localmente los 12 archivos config limpios.
3. Subir `lanzar_fase2_final.sh` con correcciones.
4. Reiniciar la misión.

Estado: Recuperación exitosa y ejecución iniciada.

### 2026-02-08_Metodologia_Chacal_V4.md
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


--- 
**INSTRUCCION:** Continua desde este punto. No repitas lo ya listado arriba.
# MANUAL DE OPERACIONES: PROTOCOLO CHACAL V4 (A FUEGO)

Este documento es el registro inmutable de la arquitectura y procesos del sistema. Ninguna auditoría debe contradecir estos principios sin re-ejecución de la Fase 2.

## 🏗️ ARQUITECTURA DE TORRES (DOCKER)

El sistema opera con **4 TORRES INDEPENDIENTES**:

1. **ALPHA:** BTC, ETH, SOL.
2. **BETA:** BNB, XRP, ADA.
3. **GAMMA:** DOGE, AVAX, LINK.
4. **DELTA:** DOT, SUI, NEAR.

# REGISTRO DE OPERACIONES CHACAL V4

## Sesión 23/02/2026 - Certificación Live Exitosa 🦅

**Estado:** ✅ EXCELENTE PERFORMANCE

1. **NEAR/USDT:USDT** +2.283 USDT (2.77%) - Duración: ~3hs
2. **SUI/USDT:USDT** +2.088 USDT (2.53%)
3. **ETH/USDT:USDT** +2.037 USDT (2.47%)
4. **BTC/USDT:USDT** +1.886 USDT (2.38%)

> [!IMPORTANT]
> Se mantiene el límite de cierre de 4hs. Los resultados demuestran que la paciencia del bot en trades de 3hs (como NEAR) está pagando con profit sólido. NO MODIFICAR.

> [!WARNING]
> El contenedor `chacal_bot` genérico es **OBSOLETO** y causa conflictos de puerto y base de datos. Solo deben estar activos los contenedores `chacal_alpha/beta/gamma/delta`.

## 🛡️ PARÁMETROS DE BLINDAJE (FASE 2)

Los `v_factor` y `pulse_change` son el ADN del sistema. No son genéricos.

- **Pulse Change:** Determina la sensibilidad al gatillo.
  - **Sensibles (0.001):** SOL, DOT, SUI, NEAR.
  - **Robustos (0.004-0.005):** BTC, ETH, y el resto.

## 🛰️ PROCESOS DE INFRAESTRUCTURA

### 1. Arranque (Magic Hours)

- Las torres arrancan vía `docker-compose up -d`.
- El `vigilante_sniper.py` se activa al arranque (`@reboot`) para monitorear el cierre.

### 2. Cierre y Ahorro (Buffer 15min)

- 15 minutos después de la "Hora Mágica", si hay trades abiertos, el `Vigilante` ejecuta `/forceexit` en cada torre.
- Una vez cerrados los trades (o si no hay), el servidor se apaga automáticamente (`shutdown -h now`) para ahorrar crédito AWS.

## 🦅 PROTOCOLO DE AUDITORÍA

Cualquier cambio debe ser verificado por `scripts/verificar_integridad_elite.py`. Si el script da error, el sistema **no está al día** y no debe lanzarse.

**PEGASO 🦅 | Misión: Supervivencia y Profit.**

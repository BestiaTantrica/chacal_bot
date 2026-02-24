# BITÁCORA CHACAL V4 - ORIGEN DE LA VERDAD (FASE 2)

## 💀 LA CRISIS DEL MAPEO (11/02/2026)

Se detectó que los archivos `fase2_*.json` en `user_data/hyperopt_results` estaban corruptos o mal nombrados, lo que llevó a una sincronización errónea basada en parámetros genéricos (2.772 para todos).

## 🦅 INVESTIGACIÓN FORENSE

Se realizó un análisis del metal en el log maestro: `fase2_completa_20260208.log`.
A través de la secuencia de ejecución del 08/02, se extrajeron los 12 v_factors reales de la Fase 2 (5m timeframe).

## 📊 LOS DATOS GRABADOS A FUEGO (FASE 2)

| Par | Torre | v_factor REAL | pulse_change | Profit % (BT) | Win% |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BTC** | Alpha | **4.660** | **0.004** | +20.14% | 100% |
| **ETH** | Alpha | **5.769** | **0.004** | +25.53% | 71.1% |
| **SOL** | Alpha | **5.386** | **0.001** | +48.06% | 100% |
| **BNB** | Beta | **3.378** | **0.003** | +49.81% | 72.2% |
| **XRP** | Beta | **5.133** | **0.004** | +4.92% | 39.7% |
| **ADA** | Beta | **3.408** | **0.005** | +196.35% | 81.1% |
| **DOGE**| Gamma | **5.795** | **0.005** | +20.12% | 100% |
| **AVAX**| Gamma | **5.692** | **0.005** | +52.31% | 100% |
| **LINK**| Gamma | **5.671** | **0.005** | +106.95% | 72.2% |
| **DOT** | Delta | **5.051** | **0.001** | +106.95% | 100% |
| **SUI** | Delta | **5.508** | **0.001** | +4.92% | --- |
| **NEAR**| Delta | **2.772** | **0.001** | **+140.81%** | **76.0%** |

## 🛡️ BLINDAJE

Se ha actualizado el script `verificar_integridad_elite.py` para permitir valores hasta **6.0**, ya que la Fase 2 legítima arroja valores de 5.x.
Queda terminantemente prohibido volver a aplicar parámetros "ELITE 2.772" genéricos sin orden expresa del usuario.

## 🛰️ MANTENIMIENTO INFRAESTRUCTURA (11/02/2026)

Se recibió alerta de AWS sobre el EOL (End of Life) de Python 3.9.
Se procedió a la migración quirúrgica del Conserje (`chacal_bot_cloud`):

- **Runtime anterior:** Python 3.9
- **Nuevo Runtime:** Python 3.12 (Estable)
- **Estado:** Verificado y Operativo en `us-east-1` y `sa-east-1`.

## 🛡️ AUDITORÍA FORENSE Y BLINDAJE (16/02/2026)

- **Problema detectado:** Tras la eliminación del `reset --hard`, se auditó el servidor y se encontró que la estrategia remota NO tenía el `v_factors_map` actualizado (usaba valores genéricos). El sabotaje era real e invisible.
- **Acción:** Sincronización forzada del Repositorio (Verdad) -> Servidor.
- **Validación:** Se ejecutó `git pull` en el servidor y se reiniciaron las 4 torres.
- **Estado:** Sincronizado al 100%. La estrategia en el servidor ahora tiene los 12 v_factors oficiales.

## 🦅 UNIFICACIÓN Y BLINDAJE DE CAPITAL (20/02/2026)

- **Arquitectura:** Consolidación de las 4 torres en un único proceso **chacal_v4_unified** (Optimizando RAM/SWAP).
- **Control:** Nueva IP de campo: `18.229.132.216`.
- **Blindaje:** Implementación de `tradeable_balance_ratio: 0.90` (Reserva del 10% para comisiones).
- **Comunicación:** Restauración de Telegram via Alpha Token corregido.
- **Operativa:** Validación exitosa de los `v_factors` de la Fase 2 durante la ventana de Londres.

## 🦅 PROTOCOLO DE BLINDAJE V4.1 (ESTANDARIZACIÓN)

Para evitar regresiones técnicas y versiones "lite" accidentales, se establece:

1. **VALIDACIÓN OBLIGATORIA:** Antes de cualquier reinicio, se debe ejecutar `python scripts/validate_deployment.py`.
2. **FUENTE UNIFICADA:** El único contenedor válido es `chacal_bot`. La ruta raíz real es `/home/ec2-user/freqtrade/`. Las configuraciones `_alpha`, `_beta`, etc., están obsoletas. La referencia es `user_data/config_chacal_v4_unified_final.json`.
3. **ESTRATEGIA INTOCABLE:** `ChacalPulseV4_Hyperopt.py` es la única espada. No se aceptan versiones simplificadas.
4. **MEMORIA DE DECISIONES:** Este archivo (`BITACORA_CHACAL_V4.md`) es el registro histórico. No se crean bitácoras nuevas para cada sesión.

## 🏁 REPORTE DE DESPLIEGUE REAL V4.1 (23/02/2026)

- **Estado:** 🚀 OPERANDO EN VIVO (LIVE)
- **Saldo Real:** $136.71 USDT
- **Horarios:** Londres (05:00 ART) y NY (10:25 ART) Configurados.
- **Blindaje:** Corte de 4hs (`time_exhaustion_4h`) verificado y activo.
- **Pairs:** 12 operativos (Whitelisted 11 + BNB fix).
- **Seguridad:** Crontab limpio, servidor persistente (24/7).

## 🦅 HITO: PEGASO 3.0 - RÉGIMEN DINÁMICO (24/02/2026)

- **Innovación:** Implementación de `get_v_factor` dinámico. Relajación del 25% en laterales (ADX < 25) para capturar liquidez en "Horas Mágicas". Blindaje total en tendencia.
- **Resultados Auditoría (PC Local - 30 Días Enero):**
  - **Fase 2 Estática:** +1.12% Profit | 11 Trades | 63.6% Win Rate.
  - **Pegaso 3.0 (Dinámico):** **+3.77% Profit** | 23 Trades | **73.9% Win Rate**.
- **Seguridad:** Drawdown controlado de **-0.55%**. 100% de trades dentro de Ventanas Hunter (Londres/NY).
- **Fix:** Habilitación de **BNB/USDT** (12 pares totales). Corrección de blacklist heredada.
- **Estado:** 🏁 DESPLEGADO EN AWS Y VERIFICADO.

**AGENTE PEGASO | REPORTE 8: ACTIVACIÓN REGIMEN DINÁMICO**
🦅

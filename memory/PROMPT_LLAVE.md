# PROTOCOLO PEGASO: LLAVE DE ACTIVACION DE MEMORIA

**FECHA:** 2026-02-09

## 📊 ESTADO ACTUAL: ONLINE (DRY RUN) 🔥

- **Flota**: 4 Torres Activas (12/12 monedas).
- **Energía**: ✅ Vigilante + EventBridge (Auto-Start) operativos.
- **Monitoreo**: Lambda Híbrida (SSM) + Conserje v4.1 Monitor.
- **Reporting**: Reporte unificado vía /status o /reporte (todas las torres).
- **Capital**: $75 USDT/torre ($300 total) para eficiencia de margen.

## 📜 PROTOCOLO DE OPERACIONES (REGLAS Y TÉCNICA)

# 📜 PROTOCOLO DE SUPERVIVENCIA "CHACAL" - REGLAS DE ORO

**ESTE DOCUMENTO ES DE LECTURA OBLIGATORIA PARA EL AGENTE ANTES DE CUALQUIER COMANDO.**

## 1. RESTRICCIONES DE HARDWARE (AWS t2.micro)

- **CONTENEDORES**: Siempre usar **Docker**. No correr procesos pesados nativos.
- **RAM**: 1GB (Saturada). No cargar más de 120-150 días de datos 5m.
- **CPU**: 1 Core. **PROHIBIDO** usar `-j 2`. Siempre usar `-j 1`.
- **SWAP**: 4GB activos. Evitar procesos que lo saturen para no congelar la instancia (Load Average < 2.0 ideal).

## 2. REGLAS DE CONFIGURACIÓN (CRÍTICAS)

- **HARDWARE (t2.micro)**: Limitar a 3 pares para no colapsar la RAM.
- **SINTAXIS FUTURES**: En Binance Futures, los pares DEBEN usar el formato `PAR/USDT:USDT` (no `PAR/USDT`). Esto aplica para configs, whitelists y comandos.
- **RESOLUCIÓN DE CAZA (1m)**: El Hyperopt se ejecuta SIEMPRE a 1 minuto para detectar el gatillo en las Horas Mágicas. El refinado a 5m es solo para el despliegue final.
- **ESTRATEGIA ÚNICA**: Solo `ChacalPulseV4_Hyperopt`.
- **SHORTS OBLIGATORIOS**: Siempre configurar `"can_short": true`.
- **ZOMBIES**: PROHIBIDO dejar contenedores con nombres aleatorios. El despliegue siempre debe ser vía `docker-compose_relevo.yml` para nombres fijos.

## 3. REGLAS DE ESTRATEGIA (CHACAL V4)

- **HORAS MÁGICAS**: Operar exclusivamente en las aperturas: Londres (08-10 UTC / 05-07 Local) y New York (13:30-17:30 UTC / 10:30-14:30 Local).
- **ADAPTACIÓN**: La estrategia DEBE diferenciar entre BULL, BEAR y LATERAL mediante indicadores (ADX/RSI).
- **HYPEROPT**: Optimizar parámetros de salida específicos para cada uno de los 3 estados.

## 4. CICLO DE VIDA Y RECURSOS (CRÍTICO)

- **USO DE TIEMPO**:
  - **Horas Mágicas**: Trading activo (Caza).
  - **Horas Muertas**: Apagar trading y procesar **Hyperopts moneda por moneda** hasta hallar la configuración ganadora.
- **FINES DE SEMANA**: Reservados exclusivamente para **Pruebas y Optimización**. NUNCA dejar bots corriendo a lo loco.
- **PERSISTENCIA**: No dejar procesos "viviendo" sin control. Si no hay estrategia ganadora validada, el bot NO OPERA.

## 5. PROCEDIMIENTO DE HYPEROPT (ESTÁNDAR DE ORO)

1. **Metodología de Refinado (1m -> 5m)**:
   - **Fase 1 (Precisión)**: Uso de **Biblioteca Quirúrgica 1m**.
   - **Fase 2 (Refinado)**: Estabilidad en 5m. Para operar sin que nos maten las comiciones.
2. **Biblioteca Quirúrgica (1m Magic)**:
   - **Segmentación**: Solo se procesan velas de 1m correspondientes a las Horas Mágicas (+warmup).
   - **Capacidad Permanente**: Se mantendrá un repositorio histórico de hasta **7 años** en el directorio `binance_surgical`.
   - **Eficiencia**: 12 pares × 6 horas/día × 1m ≈ 6GB de disco para una década de datos tácticos. Esto evita re-descargas y ahorra ancho de banda.
   - **Mantenimiento**: Cada fin de semana se "poda" la data nueva descargada para integrarla a la Biblioteca Quirúrgica.
3. **Fase 2: Refinamiento (5m - Industrial)**: ✅ **COMPLETADA 2026-02-08**
   - **Objetivo**: Validar robustez de parámetros con horizonte temporal extendido.
   - **Datos**: 365 días @ 5m filtrada por **Horas Mágicas** (Londres + NY).
   - **Intensidad**: 1000 épocas por moneda.
   - **Ejecución**: Secuencial (1 moneda por vez) para evitar OOM en t2.micro.
   - **Resultados Destacados**:
     - LINK: +196.35% (463 trades, 63.5% WR)
     - NEAR: +140.81% (292 trades, 76.0% WR)
     - SUI: +106.95% (268 trades, 70.1% WR)
     - DOGE: +105.29% (281 trades, 70.8% WR)
   - **Script**: `user_data/lanzar_fase2_final.sh`.
   - **Lección Clave**: La combinación 1m (exploración) + 5m (validación) es superior a optimizar directamente en 5m.
4. **Pares (Batallón Elite - 12 Unidades)**:
   - **Selección**: BTC, ETH, SOL, XRP, ADA, DOT, DOGE, AVAX, LINK, BNB, SUI, NEAR.
   - **Criterio**: Monedas de Tier 1/2 con correlación real con BTC y volumen masivo para 1m. SUI y NEAR elegidas por su performance actual en el mercado.
5. **Cola de Ejecución (Secuencial)**:
   - **Problema**: El Hyperopt de 12 monedas es inejecutable en 1GB de RAM de forma simultánea.
   - **Solución**: Se usa el script `user_data/cola_hyperopt.sh` para procesar **una moneda por vez**.
   - **Persistencia**: Se lanza bajo `screen -dmS hyperopt_ELITE` para operar de forma autónoma.
6. **Estructura de Datos (Biblioteca Quirúrgica)**:
   - **Ubicación Nativa**: `user_data/data/binance/futures/`.
   - **Formato**: `feather` (máxima velocidad de lectura).
   - **Injerto**: Para que Freqtrade reconozca los datos segmentados, deben residir en la ruta nativa y estar acompañados de los archivos `funding_rate.feather` y `mark.feather` originales.

## 7. GESTIÓN DE INCIDENCIAS Y RESCATE (REGLAS DE HIERRO)

- **SATURACIÓN**: Si el Load Average > 10.0 o RAM < 50MB, realizar `sudo docker stop $(sudo docker ps -q)` inmediatamente.
- **SABOTAJE DE SHELL**: En PowerShell, los comandos remotos con expansiones `$(...)` deben enviarse entre comillas simples o dobles escapadas para evitar que se ejecuten localmente.
- **RESCATE FORENSE**: Si el servidor se cuelga, el archivo `.fthypt` es la única fuente de verdad; usar `cat` para verificar integridad antes de intentar procesos pesados.
- **BACKUP PREVENTIVO**: Descargar el log (`SCP`) cada 4 monedas procesadas para no depender de la persistencia del servidor al final de la jornada.

## 8. GESTIÓN DE ENERGÍA Y SUPERVIVENCIA (FREE TIER) ✅

- **ENCENDIDO (AWS Scheduler)**:
  - **Londres (04:55 AM ART)**: Regla `Chacal_PowerOn_Londres` (Cron: `55 7 ? * MON-FRI *`).
  - **NY (10:25 AM ART)**: Regla `Chacal_PowerOn_NY` (Cron: `25 13 ? * MON-FRI *`).
  - **Permisos**: IAM Role `ChacalPowerRole` con `AmazonEC2FullAccess`.
- **APAGADO (Vigilante)**:
  - Script `vigilante_energia.py` escaneando los 4 SQLite cada 5 min.
  - Horarios de check críticos: **07:15 ART** y **14:45 ART**.
  - **Lógica**: Si detecta trades abiertos o el archivo `/tmp/NO_APAGAR`, el apagado se **cancela**.
- **DESPLIEGUE MULTI-TORRE (t2.micro)**:
  - **Alpha**: BTC, ETH, SOL | **Beta**: BNB, XRP, ADA
  - **Gamma**: DOGE, AVAX, LINK | **Delta**: DOT, SUI, NEAR
  - **Balance**: $75 USDT por torre para maximizar uso de RAM y margen.
  - **Arranque**: Automático vía `@reboot` y AWS EventBridge llamando a la Lambda.

## 9. ARQUITECTURA TÉCNICA (MANUAL PARA IA/HUMANO) 📕

### Lógica de Trading (ChacalPulseV4)

- **Gate Horario**: El bot calcula indicadores 24/7 pero solo abre la "reja" (`gate_open`) en ventanas de Londres y NY.
- **Modos**: `hunter` (solo ventanas) vs `vigilante` (siempre activo - opcional).
- **Regímenes**: ADX/RSI detectan tendencia. El bot cambia Stoploss y ROI sobre la marcha (Bull/Bear/Lateral).

### Infraestructura (t2.micro - Relevo V4)

- **Lambda Híbrida**: Centro de mando en AWS. Consulta las 4 torres vía SSM.
- **Vigilante Energía**: Script `vigilante_energia.py` sincronizado con Horas Mágicas (No apaga en sesión).
- **Arranque**: `lanzar_torres.sh` relanza el ecosistema post-reboot.
- **Notificador**: Conserje V4.1 pasivo para alertas de trades.

---
**Misión: Recuperar el capital con disciplina y precisión.**

## 📝 BITÁCORA Y ARCHIVO DE HILOS

### ARCHIVO: BITACORA_CHACAL_V4.md

# 🦅 BITÁCORA UNIFICADA: MISIÓN CHACAL V4

*Registro cronológico de la estrategia, incidencias y despliegue.*

## 📊 ESTADO ACTUAL: ONLINE (DRY RUN) 🔥

- **Flota**: 4 Torres Activas (12/12 monedas).
- **Energía**: ✅ Vigilante + AWS Scheduler operativos.
- **Monitoreo**: Conserje v4 activo en Telegram.
- **Profits Destacados**: LINK (+196%), NEAR (+140%), SUI (+106%).

---

## 📅 2026-02-08 | METODOLOGÍA QUIRÚRGICA

**Contexto**: Definición del proceso de optimización compuesta.

### 1. PRINCIPIOS FUNDAMENTALES (ORDEN ESTRUCTURAL)

- **Poda de Datos (Horas Mágicas)**: Dataset truncado a sesiones de Londres y Nueva York. Reducción de ~80% de ruido.
- **Ejecución en 4 Torres**: Segmentación de 12 monedas en Alpha, Beta, Gamma, Delta. Ejecución secuencial obligatoria.
- **Modo Short**: `can_short: True` activo.

### 2. FASES DEL DISEÑO

- **FASE 1 (1m)**: 60-120 días. Recuperación de parámetros base.
- **FASE 2 (5m - Industrial)**: 1 año completo (365+ días). 1000 épocas. Estabilidad y Sharpe Ratio.

---

## 📅 2026-02-08 | REPORTE DE INCIDENCIA: INC-20260208

**Estado**: RESUELTO (Recuperación 100%)

### 🚨 El Kilombo

Asfixia de la instancia AWS (Load > 10.0, RAM < 20MB). Procesos zombis de Docker.

### 🛠️ Rescate Forense

1. Entrada de fuerza SSH con timeout extendido.
2. Purga de contenedores remanentes.
3. Extracción manual de parámetros desde el buffer de `hyperopt-show`.
4. Recuperación total de 12/12 JSONs.

---

## 📅 2026-02-08 | CIERRE FASE 2: REFINAMIENTO INDUSTRIAL

**Estado**: COMPLETADO ✅

| Torre | Moneda | Profit (1 año) | Winrate | Observaciones |
| :--- | :--- | :--- | :--- | :--- |
| **Delta** | **NEAR** | +140.81% | 76.0% | Cierre de campaña |
| **Gamma** | **LINK** | +106.95% | 75.0% | Volatilidad Máxima |
| **Delta** | **SUI** | +52.31% | 72.2% | Sólido |
| **Delta** | **DOT** | +49.16% | 83.0% | Alta precisión |
| **Beta** | **BNB** | +47.45% | 78.1% | Clásica rentable |
| **Alpha** | **BTC** | +16.71% | 67.1% | Base sólida |

---

## 📅 2026-02-09 | PROTOCOLO DE ENERGÍA Y SUPERVIVENCIA ✅

**Misión**: Ahorro de AWS Free Tier y protección de capital.

### 1. ENCENDIDO AUTOMÁTICO (AWS Scheduler)

- **Londres (04:55 AM ART)**: Regla `Chacal_PowerOn_Londres`.
- **NY (10:25 AM ART)**: Regla `Chacal_PowerOn_NY`.
- **IAM**: `ChacalPowerRole` con `AmazonEC2FullAccess`.

### 2. APAGADO INTELIGENTE (Script Vigilante)

- **Script**: `vigilante_energia.py` corriendo en el server.
- **Checks**: 07:15 ART y 14:45 ART.
- **Regla de Oro**: Si hay trades abiertos o bandera `/tmp/NO_APAGAR`, el apagado se bloquea. **El profit manda sobre el ahorro.**

### 3. DESPLIEGUE MULTI-TORRE

- **Torres**: 4 grupos de 3 monedas.
- **Arranque**: Automático vía `@reboot` en crontab calling `lanzar_torres.sh`.
- **Monitoreo**: Conserje v4 activo en Telegram (`/status`).

---

## 📅 2026-02-10 | SEGURIDAD Y PROTOCOLO PEGASO 3.1 ✅

**Misión**: Eliminar secretos expuestos y blindar la memoria del agente.

### 1. SANEAMIENTO DE SECRETOS

- **Scripts**: `scripts/set_webhook_safe.py` actualizado para usar `.env.deployment`.
- **Legacy**: `_legacy/config.json` ofuscado (token removido).
- **Verificación**: `grep` recursivo confirma limpieza total de tokens conocidos.

### 2. PROTOCOLO PEGASO 3.1 (EL BÚNKER)

- **Reglas**: Implementado en `.agent/rules/PEGASO_STRICT.md`.
- **Mandatos**:
  - Revisión obligatoria de hilos pasados y KIs.
  - Prohibición de secretos en texto plano.
  - Raíz limpia: archivos de utilidad movidos a `scripts/`.
  - Actualización constante de esta bitácora.

---
**INSTRUCCION PARA IA:** Has recibido el búnker de información completo. Continúa la misión respetando el ahorro de energía y los horarios de trading (Londres/NY). NO EXPONGAS SECRETOS.

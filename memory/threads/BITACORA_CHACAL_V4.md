# 🦅 BITÁCORA UNIFICADA: MISIÓN CHACAL V4

*Registro cronológico de la estrategia, incidencias y despliegue.*

## 📊 ESTADO ACTUAL: ONLINE (DRY RUN) 🔥

- **Flota**: 4 Torres Activas (12/12 monedas).
- **Energía**: ✅ Vigilante + AWS Scheduler operativos.
- **Monitoreo**: Conserje v4 activo en Telegram (Texto Plano).
- **Profits Destacados**: Historial limpio desde $300 (09/02/2026).

---

## 📅 2026-02-09 | LIMPIEZA TOTAL Y AUTOMATIZACIÓN (LEY CERO)

### 1. REINICIO DE SISTEMA

- **Capital**: Ajustado a **$300 USDT** ($75/bot).
- **Datos**: Inyección Quirúrgica de Hyperopt Fase 2 (LINK, AVAX, DOGE reales).
- **Base de Datos**: Limpieza total de trades viejos/basura.

### 2. AUTOMATIZACIÓN ENERGÉTICA

- **Apagado**: ✅ Script `apagar_si_no_hay_trades.py` activo en Cron (07:15 ART).
  - Status: **EXITOSO** (Instancia apagada a las 07:15 ART).
- **Encendido**: ✅ EventBridge AWS configurado por usuario (10:25 ART).
- **Arranque Bots**: ✅ **RESUELTO (10:35 ART)**.
  - Se ingresó manual (`ssh ... bash lanzar_torres.sh`).
  - Se configuró `@reboot` en Crontab para futuros inicios.
  - Bots operativos: 4 Torres + Conserje.

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

## 📜 PROTOCOLO DE MEMORIA PEGASO 3.1

1. **Unificación**: No más archivos sueltos. Todo se amplía en esta **Bitácora**.
2. **Sincronización**: Git push al terminar cada sesión de trabajo significativa.
3. **Misión**: Continuidad operativa bajo protocolo Chacal V4.

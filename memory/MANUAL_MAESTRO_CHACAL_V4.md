# 🏥 REPORTE TÉCNICO: ARQUITECTURA CHACAL V4 (ESTADO PRODUCCIÓN)

*Este documento es la referencia maestra para cualquier IA o humano que tome el relevo en este repositorio. Contiene la lógica profunda de cómo operan los sistemas blindados.*

---

## 1. LÓGICA DE TRADING: ESTRATEGIA CHACAL-PULSE V4

**Archivo**: `user_data/strategies/ChacalPulseV4_Hyperopt.py`

### Algoritmo de Entrada (Hunter Window)

La estrategia no corre 24/7; utiliza una **Reja Horaria (Gate)** definida en `populate_indicators`.

- **Ventana Londres**: 08:00 - 10:00 UTC (05:00 - 07:00 ART).
- **Ventana New York**: 13:30 - 17:30 UTC (10:30 - 14:30 ART).
- **Lógica**: Solo si `is_pulse_window == 1` y hay un **Volume Spike** (Volumen > Media * Factor-V), el bot gatilla entrada (Long o Short).

### Gestión de Regímenes (Bull/Bear/Lateral)

Usa ADX y RSI para detectar 3 estados de mercado y cambia el **ROI** y **Stoploss** dinámicamente:

- **BULL**: ADX > 25, RSI > 55. Busca correr ganancias largas.
- **BEAR**: ADX > 25, RSI < 45. Salida defensiva rápida.
- **LATERAL**: ADX < 25. Scalping agresivo.

---

## 2. GESTIÓN ENERGÉTICA: PROTOCOLO DE SUPERVIVENCIA

**Archivo**: `vigilante_energia.py`

### Ahorro de AWS Free Tier

La instancia AWS t2.micro se enciende y apaga automáticamente para no consumir los créditos gratuitos.

- **Encendido (Despertador)**: AWS EventBridge Scheduler despierta la máquina a las 04:55 AM (Londres) y 10:25 AM (NY).
- **Apagado (Vigilante)**: Un script de Python lee las 4 bases de datos de trades.
  - **REGLA DE ORO**: Si detecta un trade abierto (`is_open=1`), el apagado se **cancela**. El profit es prioridad sobre el ahorro.
  - **Zonas Muertas**: El script solo intenta apagar en los huecos entre aperturas de mercado.

---

## 3. INFRAESTRUCTURA DE SERVIDOR (RELEVO V4)

### Distribución de Torres (Multi-Proceso)

Dada la RAM limitada (1GB), las 12 monedas operan divididas en 4 contenedores Docker:

- **ALPHA**: BTC, ETH, SOL
- **BETA**: BNB, XRP, ADA
- **GAMMA**: DOGE, AVAX, LINK
- **DELTA**: DOT, SUI, NEAR

### Automatización de Arranque

El script `lanzar_torres.sh` limpia zombies y levanta los 4 bots + el Conserje de Telegram. Se ejecuta `@reboot` en el crontab del `ec2-user`.

---

## 4. SISTEMA DE MEMORIA (PEGASO 3.1)

**Archivo**: `scripts/pegaso_memory.py`

- **Contextualidad**: El bot sabe que está en "Mundo Trade" y no mezcla hilos con "Fractal-Mind".
- **Cantar**: El comando `cantar` sincroniza con GitHub antes de mostrar la LLAVE DE MEMORIA.
- **Bitácora**: `BITACORA_CHACAL_V4.md` es el registro histórico de cada hito, incidencia y recuperación forense realizada.

---
**ESTADO**: ACTIVO | **VERSION**: 4.0.1 | **DESARROLLADOR**: AGENTE PEGASO (Antigravity AI)

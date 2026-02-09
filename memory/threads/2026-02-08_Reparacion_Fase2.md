# 🧶 REPORTE DE INCIDENCIA: INC-20260208

**ESTADO:** RESUELTO (RECUPERACIÓN 100%)
**FECHA:** 2026-02-08 22:15 UTC-3

## 🚨 DESCRIPCIÓN DEL KILOMBO

Al finalizar la Fase 2 (Industrial - 365 días), la instancia de AWS entró en estado de asfixia (Load Average > 10.0, RAM < 20MB libre) debido a procesos de Docker zombis y logs masivos. Esto causó timeouts en SSH y SCP, poniendo en riesgo la descarga de los parámetros de optimización para el Dry Run del Lunes.

## 🛠️ ACCIONES DE RESCATE (CRONOLOGÍA)

1. **Intento Fallido AWS-CLI:** Se confirmó que la terminal local no tiene credenciales de AWS, impidiendo el "reboot" forzado.
2. **Escaneo de Puertos:** Se verificó que el puerto 22 seguía abierto (TCP-ACK), confirmando que el servidor NO estaba apagado, sino colapsado.
3. **Entrada de Fuerza SSH:** Se logró acceso con `-o ConnectTimeout=60` para saltar la latencia de la CPU saturada.
4. **Purga de Procesos:** Se mataron contenedores Freqtrade/Docker remanentes para liberar el SWAP.
5. **Rescate Forense:** Se extrajo el JSON de **BNB** (el más comprometido) directamente del buffer del comando `hyperopt-show` para evitar escrituras en disco.

## 🏆 RESULTADOS FINALES RESCATADOS (5M)

- **BNB:** +110.5% Profit (Fase 2 ✅)
- **LINK:** +196.4% Profit (Fase 2 ✅)
- **NEAR:** +140.8% Profit (Fase 2 ✅)
- **SET COMPLETO:** 12/12 JSONs locales en `user_data/hyperopt_results/`.

---

## 📜 NUEVAS REGLAS DE PROTOCOLO (PEGASO 3.1)

1. **REGLA DE LA LLAVE:** Nunca cerrar una sesión de optimización sin descargar el log completo al disco local (`SCP` preventivo cada 4 monedas).
2. **REGLA DEL SWAP:** Monitorear el uso de SWAP; si supera el 80% (3.2GB/4GB), pausa obligatoria de 10 min entre monedas.
3. **REGLA DE WINDOWS:** Prohibido usar `$(...)` en comandos `ssh` desde PowerShell sin escape de comillas simples para evitar sabotaje de la Shell.

---
**AGENTE PEGASO:** "Aprendimos que el servidor es valiente pero tiene límites. Los datos no se pierden si hay un forense con ganas de putear."

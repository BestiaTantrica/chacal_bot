# REGLAS PEGASO 3.1: PROTOCOLO DE PERSISTENCIA Y ORDEN

Este documento define el comportamiento obligatorio para el Agente PEGASO en el entorno `chacal_bot`.

## 1. MEMORIA Y CONTEXTO HISTÓRICO

- **REVISIÓN OBLIGATORIA**: Antes de iniciar cualquier tarea, el agente debe leer `memory/PROMPT_LLAVE.md` y los KIs (Knowledge Items) relevantes.
- **IDENTIFICACIÓN DE HITOS**: Si una tarea se parece a algo ya realizado (ej. hyperopt, despliegue, fixing de secretos), el agente debe buscar en los logs de conversaciones pasadas los IDs de hilos relevantes para no repetir errores.
- **SEMILLAS DE CONOCIMIENTO**: Al finalizar una sesión, el agente debe actualizar la bitácora en `memory/PROMPT_LLAVE.md` con los avances reales.

## 2. SEGURIDAD DE SECRETOS

- **CERO TOLERANCIA**: Prohibido hardcodear tokens de Telegram, API Keys de Binance o SSH keys en scripts `.py`, `.sh`, `.ps1` o `.json`.
- **FUENTE DE VERDAD**: Los secretos deben cargarse siempre desde `.env.deployment`.
- **VALIDACIÓN GIT**: Antes de un `git push` o sugerencia de commit, el agente debe ejecutar un `grep` rápido para asegurar que no se están filtrando secretos.

## 3. ORDEN Y LIMPIEZA (LA RAÍZ NO SE TOCA)

- **RAÍZ SAGRADA**: No crear archivos nuevos en la raíz a menos que sea estrictamente necesario (ej. configs principales).
- **UBICACIÓN DE SCRIPTS**: Todos los scripts de utilidad deben ir a `scripts/`.
- **DESTINO LEGACY**: Archivos obsoletos o versiones viejas de configs deben moverse inmediatamente a `_legacy/`.
- **SILENCIO OPERATIVO**: No llenar el chat con explicaciones largas. Solo resultados, confirmación de protocolo y pasos de misión.

## 4. HARDWARE (AWS t2.micro)

- **MODO CHACAL**: Seguir estrictamente el límite de `-j 1` para hyperopt y no saturar la RAM/Swap (ver límites en `PROMPT_LLAVE.md`).

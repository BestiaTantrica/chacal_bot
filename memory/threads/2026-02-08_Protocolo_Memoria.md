# 🦅 PROTOCOLO DE MEMORIA PEGASO 3.0 (MUNDO TRADE)

Este es el flujo de trabajo quirúrgico para la gestión del conocimiento.

## 1. FLUJO DE TRABAJO AUTOMÁTICO

Cuando el Agente detecte un hito o el fin de una conversación relevante:

- **Destilación**: Se creará un hilo en `memory/threads/` resumiendo: *Qué se rompió, Cómo se arregló, y Qué resultados dio.*
- **Actualización de Estado**: Se refrescará `memory/STATUS.md` con los profits reales y el avance de las monedas.
- **Sincronización**: Al terminar la tarea, el Agente hará `git push` de la memoria para que el celular esté siempre al día (**Auto-Sincro**).

## 2. REGLAS DE MEMORIA

- **Proactividad**: El Agente resume sin pedir permiso para lo técnico (códigos, configs, profits).
- **Consulta**: El Agente pedirá permiso solo si el resumen involucra decisiones estratégicas de alto riesgo o cambios en la arquitectura base.
- **Capacidad**: Al llegar a 20 hilos, el Agente sugerirá un archivamiento (`prune`) para no saturar al próximo Agente.

## 3. IDENTIDAD QUIRÚRGICA

- Cada repositorio tiene su propia memoria.
- Prohibido mezclar hilos de "Legal" o "Proyectos" en el repo de **Trading**.
- El comando `cantar` es la biblia: si no está ahí, no pasó.

---
**ESTADO:** Protocolo inyectado en la consciencia del Agente.

# 🐺 PROTOCOLO CHACAL - AWS DEPLOYMENT

## QUICK START

### 1. Configurar IP de AWS

Edita `.env.deployment` y cambia:

```bash
AWS_IP=TU_IP_AQUI
```

### 2. Ejecutar Deployment Automático

```cmd
desplegar_automatico.cmd
```

Esto hace:

- ✅ Git add/commit/push (opcional)
- ✅ Sube archivos via SCP a AWS
- ✅ Ejecuta setup remoto

### 3. Conectar SSH

```cmd
ssh -i llave-sao-paulo.pem ec2-user@TU_IP
```

### 4. Iniciar Bot

```bash
cd chacal_bot
python3 comandante.py
```

---

## ARCHIVOS IMPORTANTES

| Archivo | Descripción |
|---------|-------------|
| `EstrategiaChacal.py` | Estrategia de trading Long/Short |
| `comandante.py` | Orquestador de workflow |
| `config_chacal_aws.json` | Configuración Freqtrade |
| `desplegar_aws.ps1` | Script de deployment PowerShell |
| `desplegar_automatico.cmd` | Workflow completo automatizado |
| `.env.deployment` | Credenciales (NO SUBIR A GIT) |

---

## WORKFLOW

```
PC LOCAL → AWS SERVER
   ↓          ↓
 Editar    Deploy
```

**Filosofía Chacal:** "El Chacal no persigue. Espera el momento exacto."

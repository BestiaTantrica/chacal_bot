# 🎯 PROTOCOLO CHACAL - CONFIGURACIÓN DE SERVIDOR

## 📡 AWS EC2 (São Paulo)

| Parámetro | Valor |
|-----------|-------|
| **IP Pública** | `56.125.187.241` |
| **Usuario** | `ec2-user` |
| **Key SSH** | `llave-sao-paulo.pem` |
| **Directorio Remoto** | `/home/ec2-user/chacal_bot` |
| **Región** | São Paulo (sa-east-1) |

### Comando de Conexión SSH

```bash
ssh -i llave-sao-paulo.pem ec2-user@56.125.187.241
```

---

## 🔑 BINANCE API

| Parámetro | Valor |
|-----------|-------|
| **API Key** | `2a9MJaipSfFD0JuraWIdsGxct9VjFXwKe8rCvstV0zvVwSc12vZbTjgQW76bFjkA` |
| **Secret Key** | `BVmyGezpSEIGic7GrFrY2i3R96xJkzMb70mAf077c2G2tx8aIgFiMMpOCCpBJXTs` |

> [!WARNING]
> **TESTNET**: Verificar si estas keys son de producción o testnet antes de operar con capital real.

---

## 🔄 WORKFLOW ESTÁNDAR

### 1️⃣ PC LOCAL
- Editar estrategia: `user_data/strategies/EstrategiaChacal.py`
- Backtest local con Docker
- Hyperopt local (si hay recursos suficientes)

### 2️⃣ GIT
```bash
git add .
git commit -m "mensaje descriptivo"
git push origin main
```

### 3️⃣ AWS DEPLOY
```bash
# Automático
desplegar_automatico.cmd

# Manual
powershell -ExecutionPolicy Bypass -File desplegar_aws.ps1 -Ip 56.125.187.241
```

---

## 🐋 DOCKER LOCAL

### Comandos Base

```bash
# Iniciar contenedor interactivo
docker run -it --rm -v ${PWD}:/freqtrade freqtradeorg/freqtrade:stable bash

# Backtest directo
docker run --rm -v ${PWD}:/freqtrade freqtradeorg/freqtrade:stable backtesting --config config_chacal_aws.json --strategy EstrategiaChacal

# Hyperopt (CUIDADO: Intensivo en recursos)
docker run --rm -v ${PWD}:/freqtrade freqtradeorg/freqtrade:stable hyperopt --config config_chacal_aws.json --hyperopt-loss SharpeHyperOptLoss --strategy EstrategiaChacal --epochs 100 --spaces buy sell
```

---

## 📋 CHECKLIST DE VALIDACIÓN

- [ ] Conexión SSH funcional
- [ ] API Keys validadas en Binance
- [ ] Docker instalado y funcional
- [ ] Estrategia sin errores de sintaxis
- [ ] Config JSON validado
- [ ] Backtest ejecutado exitosamente
- [ ] Hyperopt ejecutado (opcional local, recomendado servidor)
- [ ] Git configurado y sincronizado
- [ ] Deploy automático verificado

---

## 🚨 NOTAS CRÍTICAS

1. **Recursos Locales**: PC puede no soportar Hyperopt largo. Usar servidor AWS para optimizaciones extensas.
2. **SWAP en AWS**: Instancia tiene 4GB SWAP configurado para evitar OOM Killer.
3. **Prioridad**: Primero validar estrategia localmente, después escalar a servidor.

<#
.SYNOPSIS
    Despliegue Automático Protocolo Chacal a AWS
.DESCRIPTION
    Sube scripts y configs a instancia AWS (Amazon Linux) y ejecuta el setup.
.PARAMETER Ip
    Dirección IP Pública de la instancia AWS.
.EXAMPLE
    .\desplegar_aws.ps1 -Ip 12.34.56.78
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Ip
)

$User = "ec2-user"
$Key = "llave-sao-paulo.pem"
$Dest = "/home/ec2-user/chacal_bot"

Write-Host "🐺 INICIANDO DESPLIEGUE REMOTO A AWS [$Ip]" -ForegroundColor Cyan

# 0. Verificar Llave
if (-not (Test-Path $Key)) {
    Write-Error "No encuentro la llave: $Key"
    exit 1
}

# 1. Crear directorio remoto
Write-Host "[1/4] Creando directorio remoto..."
ssh -i $Key -o StrictHostKeyChecking=no $User@$Ip "mkdir -p $Dest/user_data/strategies"

# 2. Preparar Configuración con Secretos (LOCAL TEMPORAL)
Write-Host "[2/4] Preparando configuración con secretos..."
$EnvContent = Get-Content ".env.deployment" -Raw
$BinanceKey = [regex]::Match($EnvContent, "BINANCE_API_KEY=(.*)").Groups[1].Value.Trim()
$BinanceSecret = [regex]::Match($EnvContent, "BINANCE_SECRET_KEY=(.*)").Groups[1].Value.Trim()

# Si no está explícito, buscar el token de Telegram (línea con :)
$TelegramToken = [regex]::Match($EnvContent, "([0-9]{8,10}:[a-zA-Z0-9_-]{35})").Groups[1].Value.Trim()

$ConfigPath = "user_data/config_chacal_aws.json"
$ConfigContent = Get-Content $ConfigPath -Raw
$ConfigContent = $ConfigContent -replace "PLACEHOLDER_BINANCE_KEY", $BinanceKey
$ConfigContent = $ConfigContent -replace "PLACEHOLDER_BINANCE_SECRET", $BinanceSecret
$ConfigContent = $ConfigContent -replace "PLACEHOLDER_TELEGRAM_TOKEN", $TelegramToken

$TempConfig = "user_data/config_chacal_aws.json.tmp"
# FIX: Usar UTF-8 SIN BOM para evitar error de parseo en Freqtrade
$Utf8NoBomEncoding = New-Object System.Text.UTF8Encoding $False
[System.IO.File]::WriteAllText($TempConfig, $ConfigContent, $Utf8NoBomEncoding)

# 3. Subir Archivos (SCP)
Write-Host "[3/4] Subiendo archivos..."
$FilesToAdd = @(
    "setup_aws_chacal.sh", 
    "comandante.py", 
    "docker-compose.yml",
    "loop_chacal.sh",
    "user_data/strategies/EstrategiaChacal.py",
    "user_data/static_pairs.json"
)

# Primero los fijos
foreach ($File in $FilesToAdd) {
    if (Test-Path $File) {
        scp -i $Key $File $User@$Ip`:$Dest/
    }
}

# Subir la config temporal como la real en el destino
scp -i $Key $TempConfig $User@$Ip`:$Dest/$ConfigPath
Remove-Item $TempConfig

# 4. Actualizar Servidor y Permisos
Write-Host "[4/4] Actualizando servidor y ajustando permisos..."
ssh -i $Key $User@$Ip "sudo yum update -y && chmod +x $Dest/setup_aws_chacal.sh"

# 5. Ejecución del Setup
Write-Host "🚀 EJECUTANDO SETUP REMOTO..." -ForegroundColor Yellow
ssh -i $Key $User@$Ip "cd $Dest && sudo bash setup_aws_chacal.sh"

Write-Host "`n✅ PROTOCOLO CHACAL COMPLETADO." -ForegroundColor Green
Write-Host "IP AWS: $Ip"
Write-Host "Para iniciar bot: python3 $Dest/comandante.py"

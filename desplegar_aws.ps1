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
    [Parameter(Mandatory=$true)]
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

# 2. Subir Archivos (SCP)
Write-Host "[2/4] Subiendo archivos..."
$Files = @(
    "setup_aws_chacal.sh", 
    "comandante.py", 
    "docker-compose.yml",
    "user_data/strategies/EstrategiaChacal.py",
    "user_data/config_chacal_aws.json",
    "user_data/static_pairs.json"
)

foreach ($File in $Files) {
    if (Test-Path $File) {
        if ($File -like "user_data/*") {
             scp -i $Key $File $User@$Ip`:$Dest/$File
        } else {
             scp -i $Key $File $User@$Ip`:$Dest/
        }
    } else {
        Write-Warning "Archivo no encontrado para subir: $File"
    }
}

# 3. Permisos de Ejecución
Write-Host "[3/4] Ajustando permisos..."
ssh -i $Key $User@$Ip "chmod +x $Dest/setup_aws_chacal.sh"

# 4. Ejecución del Setup
Write-Host "[4/4] EJECUTANDO SETUP REMOTO (Esto puede tardar)..." -ForegroundColor Yellow
ssh -i $Key $User@$Ip "cd $Dest && sudo bash setup_aws_chacal.sh"

Write-Host "`n✅ DESPLIEGUE FINALIZADO." -ForegroundColor Green
Write-Host "Para conectar: ssh -i $Key $User@$Ip"
Write-Host "Para iniciar bot: python3 $Dest/comandante.py"

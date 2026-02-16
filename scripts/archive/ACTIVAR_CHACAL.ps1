# ==========================================
# SCRIPT DE ARRANQUE MANUAL - CHACAL V4
# ==========================================
# Uso: .\scripts\ACTIVAR_CHACAL.ps1 [IP_NUEVA_OPCIONAL]

param (
    [string]$IP = "chacal-guru.duckdns.org"
)

Write-Host "🦅 INICIANDO PROTOCOLO DE ARRANQUE MANUAL..." -ForegroundColor Cyan
Write-Host "1. PRENDISTE LA INSTANCIA EN AWS? (SI/NO)" -ForegroundColor Yellow
$resp = Read-Host
if ($resp -ne 'SI') {
    Write-Host "❌ ENTRÁ A AWS CONSOLE Y PRENDELA PRIMERO." -ForegroundColor Red
    exit
}

Write-Host "Conectando a IP: $IP ..." -ForegroundColor Cyan

# Intentar conexión SSH y ejecutar script de arranque
$sshCmd = "ssh -i 'llave-sao-paulo.pem' -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$IP 'bash /home/ec2-user/chacal_bot/lanzar_torres.sh'"
Invoke-Expression $sshCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ COMANDO ENVIADO. Los bots deberían estar levantando." -ForegroundColor Green
    Write-Host "Esperando 10 seg para verificar..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    $checkCmd = "ssh -i 'llave-sao-paulo.pem' -o StrictHostKeyChecking=no ec2-user@$IP 'docker ps'"
    Invoke-Expression $checkCmd
} else {
    Write-Host "❌ ERROR DE CONEXIÓN." -ForegroundColor Red
    Write-Host "Posibles causas:"
    Write-Host "1. La instancia todavía está BOOTEANDO (esperá 2 min más)."
    Write-Host "2. La IP cambió y DuckDNS todavía no actualizó."
    Write-Host "3. INTENTO DIRECTO: Si tenés la IP nueva de AWS, ejecutá:"
    Write-Host "   .\scripts\ACTIVAR_CHACAL.ps1 TUPA.IP.NUEVA"
}

Read-Host "Presione Enter para salir"

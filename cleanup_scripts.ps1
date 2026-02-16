$dest = "scripts/archive"
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest }

$files = @(
    "scripts/ACTIVAR_CHACAL.ps1",
    "scripts/analizar_volumen_*.py",
    "scripts/check_lambda_*.py",
    "scripts/fix_*.py",
    "scripts/test_*.py",
    "scripts/set_webhook_*.py",
    "scripts/server_boot.py",
    "scripts/check_ip.py",
    "scripts/check_status_local.py",
    "scripts/check_tags.py",
    "scripts/clean_deploy.py",
    "scripts/conserje_monitor.py",
    "scripts/conserje_v4.py",
    "scripts/debug_offline_brain.py",
    "scripts/deploy_chacal_cloud.py",
    "scripts/disable_tg.py",
    "scripts/emergency_fix.py",
    "scripts/estudio_volumen_ayer.py",
    "scripts/extraer_12_jsons.sh",
    "scripts/get_ip_diagnostic.py",
    "scripts/kill_server_now.py",
    "scripts/lambda_chacal.py",
    "scripts/lanzar_torres.sh",
    "scripts/levantar_reparacion.py",
    "scripts/list_apis.py",
    "scripts/master_tech_report.py",
    "scripts/obtener_ip_aws.py",
    "scripts/recover_infrastructure.py",
    "scripts/safe_start.py",
    "scripts/start_aws_tower.py",
    "scripts/stop_aws_tower.py",
    "scripts/sync_wallets.py",
    "scripts/validador_macro_chacal.py",
    "scripts/verificar_status_aws.py",
    "scripts/verify_webhook.py",
    "scripts/vigilante_energia.py",
    "scripts/avoid_telegram_conflict.py",
    "scripts/check_instance_status.py"
)

foreach ($f in $files) {
    Move-Item -Path $f -Destination $dest -ErrorAction SilentlyContinue
}
Write-Host "Limpieza completada."

@echo off
REM ==============================================
REM PROTOCOLO CHACAL - WORKFLOW AUTOMATICO
REM ==============================================
REM Este script ejecuta: PC -> Git -> Server

echo.
echo ====================================
echo  PROTOCOLO CHACAL - DEPLOY AUTOMATICO
echo ====================================
echo.

REM Cargar configuracion
if not exist .env.deployment (
    echo ERROR: No existe .env.deployment
    echo Ejecuta primero: crear_.env_deployment.cmd
    pause
    exit /b 1
)

REM Parsear IP de AWS del archivo .env.deployment
for /f "tokens=2 delims==" %%i in ('findstr "AWS_IP=" .env.deployment') do set AWS_IP=%%i

if "%AWS_IP%"=="PENDIENTE_BUSCAR_EN_HILO" (
    echo.
    echo =======================================
    echo  ERROR: IP de AWS no configurada
    echo =======================================
    echo.
    echo Edita el archivo .env.deployment
    echo Cambia: AWS_IP=PENDIENTE_BUSCAR_EN_HILO
    echo Por:  AWS_IP=TU_IP_REAL
    echo.
    pause
    exit /b 1
)

echo [1/3] VERIFICANDO CAMBIOS LOCALES...
git status

echo.
echo [2/3] SINCRONIZANDO CON GIT...
set /p COMMIT_MSG="Mensaje del commit (Enter para omitir Git): "

if not "%COMMIT_MSG%"=="" (
    git add .
    git commit -m "%COMMIT_MSG%"
    git push origin main
    echo Git sync completado.
) else (
    echo Git skipped.
)

echo.
echo [3/3] DESPLEGANDO A AWS [%AWS_IP%]...
powershell.exe -ExecutionPolicy Bypass -File desplegar_aws.ps1 -Ip %AWS_IP%

echo.
echo ====================================
echo  DEPLOYMENT FINALIZADO
echo ====================================
echo.
echo Para conectar SSH:
echo ssh -i llave-sao-paulo.pem ec2-user@%AWS_IP%
echo.
pause

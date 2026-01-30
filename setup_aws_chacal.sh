#!/bin/bash
# =====================================================
# PROTOCOLO CHACAL - SETUP AMAZON LINUX (AWS)
# =====================================================
# Propósito: Setup completo en Amazon Linux 2 / 2023
#            - Swap 4GB (Anti-OOM)
#            - Docker Engine
#            - Estructura Freqtrade
# Autor: Agente PEGASO
# =====================================================

set -e

echo "🐺 INICIANDO PROTOCOLO CHACAL (AWS AMAZON LINUX)"
echo "------------------------------------------------"

# 1. VERIFICACIÓN DE OS
if ! command -v yum &> /dev/null; then
    echo "❌ ERROR CRÍTICO: Este script es para Amazon Linux (yum). Se detectó otro sistema."
    echo "ℹ️ Si usa Ubuntu, avise para cambiar el script."
    exit 1
fi

# 2. CONFIGURACIÓN DE SWAP (4GB)
echo -e "\n[1/5] 💾 Configurando SWAP (Memoria Virtual)..."
if [ -f /swapfile ]; then
    echo "✅ Swap ya existe."
else
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap de 4GB creado y activado."
fi
#swappiness
sudo sysctl vm.swappiness=10
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf

# 3. INSTALACIÓN DE DOCKER Y HERRAMIENTAS
echo -e "\n[2/5] 🐳 Instalando Docker & Utils..."
sudo yum update -y
sudo yum install -y python3 python3-pip git htop

# Intentar instalación estándar de docker para AL2023 o AL2
if ! command -v docker &> /dev/null; then
    sudo yum install -y docker || sudo amazon-linux-extras install docker
    sudo service docker start
    sudo systemctl enable docker
    # Agregar usuario actual (ec2-user) al grupo docker
    sudo usermod -a -G docker $(whoami)
    echo "✅ Docker instalado."
else
    echo "✅ Docker ya estaba instalado."
fi

# Docker Compose (Plugin)
mkdir -p ~/.docker/cli-plugins/
if [ ! -f ~/.docker/cli-plugins/docker-compose ]; then
    curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
    echo "✅ Docker Compose instalado."
fi

# 4. PREPARACIÓN DE DIRECTORIO
echo -e "\n[3/5] 📂 Preparando Terreno..."
BASE_DIR="$HOME/chacal_bot"
mkdir -p $BASE_DIR/user_data/strategies $BASE_DIR/user_data/data
cd $BASE_DIR

# 5. INSTALACIÓN DE DEPENDENCIAS PYTHON (Para el Comandante)
echo -e "\n[4/5] 🐍 Comandante Deps..."
pip3 install requests --user

# 6. CONFIGURACIÓN DE SISTEMA AUTÓNOMO (SYSTEMD + LOOP)
echo -e "\n[5/5] ⚙️ Configurando Servicio Autónomo (Chacal Loop)..."

# Copiar loop script y dar permisos
chmod +x $BASE_DIR/loop_chacal.sh

# Crear servicio systemd
cat <<EOF | sudo tee /etc/systemd/system/chacal.service
[Unit]
Description=Chacal Autonomous Trading Loop
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$BASE_DIR
ExecStart=/bin/bash $BASE_DIR/loop_chacal.sh
Restart=always
RestartSec=60
StandardOutput=append:$BASE_DIR/chacal_service.log
StandardError=append:$BASE_DIR/chacal_service.log

[Install]
WantedBy=multi-user.target
EOF

# Recargar daemon y habilitar
sudo systemctl daemon-reload
sudo systemctl enable chacal
echo "✅ Servicio 'chacal' creado y habilitado (Inicio al arrancar)."

echo -e "\n🏁 FINALIZANDO..."
echo "=========================================="
echo "⚠️  IMPORTANTE: CIERRE Y ABRA SESIÓN SSH"
echo "   (Para que los permisos de Docker surtan efecto)"
echo "=========================================="
echo "Instrucciones:"
echo "1. Suba 'comandante.py', 'loop_chacal.sh' y 'docker-compose.yml' a: $BASE_DIR"
echo "2. Suba sus estrategias a: $BASE_DIR/user_data/strategies/"
echo "3. Cierre ssh y reconecte."
echo "4. Ejecute: python3 comandante.py"
echo "=========================================="

#!/bin/bash

# Script de Instalação Automática - SSH INTEL (Versão GitHub)
# Autor: Code Assistant
# Sistema: Ubuntu/Debian

set -e

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}          INSTALADOR AUTOMÁTICO SSH INTEL         ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Por favor, execute como root (sudo bash <(wget...))${NC}"
  exit 1
fi

# 1. Coletar Informações
echo -e "\n${YELLOW}--- Configuração do Ambiente ---${NC}"
read -p "Digite o seu DOMÍNIO (ex: painel.seusite.com): " DOMAIN
read -p "Digite seu E-MAIL para o SSL (Certbot): " EMAIL
read -p "Digite o USUÁRIO Admin desejado [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -p "Digite a SENHA Admin desejada [admin123]: " ADMIN_PASS
ADMIN_PASS=${ADMIN_PASS:-admin123}

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo -e "${RED}Erro: Domínio e E-mail são obrigatórios!${NC}"
    exit 1
fi

# 2. Instalar Dependências do Sistema
echo -e "\n${BLUE}[1/8] Instalando dependências do sistema...${NC}"
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl wget

# 3. Clonar Projeto do GitHub para /root
echo -e "\n${BLUE}[2/8] Clonando projeto do GitHub...${NC}"
INSTALL_DIR="/root/site-ssh-intel"
REPO_URL="https://github.com/BRUNO2024-spec/site-ssh-intel.git"

# Adicionar exceção de diretório seguro para o Git (evita erro de ownership)
git config --global --add safe.directory "$INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Pasta destino já existe. Atualizando código...${NC}"
    cd "$INSTALL_DIR"
    git fetch --all
    git reset --hard origin/main
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 4. Ajustar Permissões
echo -e "\n${BLUE}[3/8] Ajustando permissões...${NC}"
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
# Garantir permissão de escrita no SQLite
touch "$INSTALL_DIR/ssh_intel.db"
chown root:root "$INSTALL_DIR/ssh_intel.db"
chmod 664 "$INSTALL_DIR/ssh_intel.db"

# 5. Configurar Ambiente Virtual
echo -e "\n${BLUE}[4/8] Configurando ambiente virtual e dependências...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Inicializar Banco de Dados
echo -e "\n${BLUE}[*] Inicializando banco de dados...${NC}"
export ADMIN_USERNAME=$ADMIN_USER
export ADMIN_PASSWORD=$ADMIN_PASS
python3 init_db.py
deactivate

# 6. Configurar .env
echo -e "\n${BLUE}[5/8] Gerando arquivo .env...${NC}"
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
cat <<EOF > .env
DATABASE_URL=sqlite:///ssh_intel.db
JWT_SECRET_KEY=$JWT_SECRET
ADMIN_USERNAME=$ADMIN_USER
ADMIN_PASSWORD=$ADMIN_PASS
EOF
chown root:root .env
chmod 600 .env

# 7. Configurar Systemd Service
echo -e "\n${BLUE}[6/8] Configurando serviço systemd...${NC}"
SERVICE_FILE="/etc/systemd/system/ssh-intel.service"
cat <<EOF > $SERVICE_FILE
[Unit]
Description=Gunicorn instance to serve SSH INTEL
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl stop ssh-intel 2>/dev/null || true
systemctl start ssh-intel
systemctl enable ssh-intel

# 8. Configurar Nginx
echo -e "\n${BLUE}[7/8] Configurando Nginx...${NC}"
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
cat <<EOF > $NGINX_CONF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 9. SSL Certbot
echo -e "\n${BLUE}[8/8] Instalando SSL com Certbot...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

# Finalização
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      INSTALAÇÃO CONCLUÍDA COM SUCESSO!           ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "URL do Site: ${YELLOW}https://$DOMAIN${NC}"
echo -e "Usuário Admin: ${ADMIN_USER}"
echo -e "Senha Admin: ${ADMIN_PASS}"
echo -e "Diretório: $INSTALL_DIR"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}DICA: Para ver os logs: sudo journalctl -u ssh-intel${NC}"

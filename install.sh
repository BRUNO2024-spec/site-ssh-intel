#!/bin/bash

# Script de Instalação Automática - SSH INTEL
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
  echo -e "${RED}Por favor, execute como root (sudo ./install.sh)${NC}"
  exit
fi

# 1. Coletar Informações
echo -e "\n${YELLOW}--- Configuração do Ambiente ---${NC}"
read -p "Digite o seu DOMÍNIO (ex: painel.seusite.com): " DOMAIN
read -p "Digite seu E-MAIL para o SSL (Certbot): " EMAIL
read -p "Digite o USUÁRIO Admin desejado [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -p "Digite a SENHA Admin desejada [admin123]: " ADMIN_PASS
ADMIN_PASS=${ADMIN_PASS:-admin123}

# 2. Instalar Dependências do Sistema
echo -e "\n${BLUE}[1/7] Instalando dependências do sistema...${NC}"
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl

# 2.1 Ajustar permissões da pasta para o Nginx
echo -e "\n${BLUE}[1.1/7] Ajustando permissões de diretório...${NC}"
PROJECT_DIR=$(pwd)
chown -R $USER:www-data $PROJECT_DIR
chmod -R 775 $PROJECT_DIR
# Garantir que o diretório pai também seja acessível
chmod o+x /home/$USER || true

# 3. Configurar Ambiente Virtual e Dependências Python
echo -e "\n${BLUE}[2/7] Configurando ambiente virtual e dependências...${NC}"
PROJECT_DIR=$(pwd)
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 4. Configurar Arquivo .env
echo -e "\n${BLUE}[3/7] Gerando arquivo de configuração .env...${NC}"
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
cat <<EOF > .env
DATABASE_URL=sqlite:///ssh_intel.db
JWT_SECRET_KEY=$JWT_SECRET
ADMIN_USERNAME=$ADMIN_USER
ADMIN_PASSWORD=$ADMIN_PASS
EOF

# 5. Configurar Systemd Service
echo -e "\n${BLUE}[4/7] Configurando serviço systemd (Gunicorn)...${NC}"
SERVICE_FILE="/etc/systemd/system/ssh-intel.service"
cat <<EOF > $SERVICE_FILE
[Unit]
Description=Gunicorn instance to serve SSH INTEL
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:ssh-intel.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start ssh-intel
systemctl enable ssh-intel

# 6. Configurar Nginx como Proxy Reverso
echo -e "\n${BLUE}[5/7] Configurando Nginx...${NC}"
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
cat <<EOF > $NGINX_CONF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/ssh-intel.sock;
    }
}
EOF

ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 7. Configurar SSL com Certbot
echo -e "\n${BLUE}[6/7] Instalando Certificado SSL (Let's Encrypt)...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

# 8. Finalização
echo -e "\n${BLUE}[7/7] Verificando status dos serviços...${NC}"
STATUS_APP=$(systemctl is-active ssh-intel)
STATUS_NGINX=$(systemctl is-active nginx)

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      INSTALAÇÃO CONCLUÍDA COM SUCESSO!           ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "URL do Site: ${YELLOW}https://$DOMAIN${NC}"
echo -e "Status App: ${STATUS_APP}"
echo -e "Status Nginx: ${STATUS_NGINX}"
echo -e "Usuário Admin: ${ADMIN_USER}"
echo -e "Senha Admin: ${ADMIN_PASS}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}DICA: Se o site não abrir, verifique se as portas 80 e 443 estão abertas no seu Firewall.${NC}"

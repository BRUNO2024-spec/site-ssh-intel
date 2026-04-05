# 🚀 SSH INTEL - Guia de Instalação (Ubuntu 22.04)

Este guia fornece instruções passo a passo para instalar e executar o painel SSH INTEL em um servidor Ubuntu 22.04.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter acesso root ou privilégios sudo no seu servidor.

## 🛠️ Passo 1: Atualizar o Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

## 🐍 Passo 2: Instalar Python e Dependências

O Ubuntu 22.04 já vem com Python 3.10. Precisamos instalar o gerenciador de pacotes `pip` e o ambiente virtual `venv`.

```bash
sudo apt install python3-pip python3-venv -y
```

## 📂 Passo 3: Clonar ou Enviar o Projeto

Navegue até o diretório onde deseja instalar o projeto (ex: `/var/www/site-ssh-intel`):

```bash
sudo mkdir -p /var/www/site-ssh-intel
sudo chown $USER:$USER /var/www/site-ssh-intel
cd /var/www/site-ssh-intel
```

*(Envie os arquivos do projeto para esta pasta via SFTP ou Git)*

## 📦 Passo 4: Configurar Ambiente Virtual e Instalar Requisitos

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar o ambiente
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ Passo 5: Executar o Aplicativo

Para testar se está funcionando:

```bash
python3 app.py
```

O aplicativo estará rodando na porta `5000`. Você pode acessar via `http://seu-ip:5000`.

---

## 🛡️ Passo 6: Configurar para Rodar em Segundo Plano (Gunicorn + Systemd)

Para que o site continue rodando mesmo após você fechar o terminal, usaremos o **Gunicorn** e o **Systemd**.

1. **Instalar Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Criar o arquivo de serviço:**
   ```bash
   sudo nano /etc/systemd/system/ssh-intel.service
   ```

3. **Cole o seguinte conteúdo (ajuste o caminho se necessário):**
   ```ini
   [Unit]
   Description=Gunicorn instance to serve SSH INTEL
   After=network.target

   [Service]
   User=root
   Group=root
   WorkingDirectory=/root/site-ssh-intel
   Environment="PATH=/root/site-ssh-intel/venv/bin"
   ExecStart=/root/site-ssh-intel/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

4. **Iniciar e habilitar o serviço:**
   ```bash
   sudo systemctl start ssh-intel
   sudo systemctl enable ssh-intel
   sudo systemctl status ssh-intel
   sudo systemctl restart ssh-intel
   systemctl daemon-reload
   ```

## 🌐 Passo 7: Configurar Nginx e HTTPS (Certbot)

Para colocar seu site em produção com um domínio próprio e segurança HTTPS, siga os passos abaixo:

### 1. Instalar Nginx e Certbot
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### 2. Configurar o Bloco de Servidor Nginx
Crie um arquivo de configuração para o seu domínio:
```bash
sudo nano /etc/nginx/sites-available/ssh-intel.intelbrcloud.qzz.io
```

Cole o conteúdo abaixo (substitua `seu-dominio.com` pelo seu domínio real):
```nginx
server {
    listen 80;
    server_name ssh-intel.intelbrcloud.qzz.io www.ssh-intel.intelbrcloud.qzz.io;

    location / {
        include proxy_params;
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ative a configuração e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/ssh-intel.intelbrcloud.qzz.io /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Obter Certificado SSL Gratuito (HTTPS)
O Certbot configurará automaticamente o HTTPS no seu Nginx:
```bash
sudo certbot --nginx -d ssh-intel.intelbrcloud.qzz.io -d www.ssh-intel.intelbrcloud.qzz.io
```
*Siga as instruções na tela e escolha a opção de "Redirect" para forçar todo o tráfego para HTTPS.*

### 4. Renovação Automática do SSL
O Certbot configura um cron job automaticamente, mas você pode testar com:
```bash
sudo certbot renew --dry-run
```

---

## 🛠️ Comandos Úteis

- **Ver logs do site:** `sudo journalctl -u ssh-intel -f`
- **Reiniciar o painel:** `sudo systemctl restart ssh-intel`
- **Verificar status do Nginx:** `sudo systemctl status nginx`

---

## 💡 Dicas de Segurança
- **Firewall (UFW):** Recomenda-se fechar a porta 5000 e permitir apenas 80 (HTTP) e 443 (HTTPS):
  ```bash
  sudo ufw allow 'Nginx Full'
  sudo ufw delete allow 5000
  sudo ufw enable
  ```
- **Banco de Dados:** Faça backups regulares do arquivo `ssh_intel.db`.
- **Ambiente Virtual:** Sempre execute os comandos do Python com o ambiente ativado (`source venv/bin/activate`).

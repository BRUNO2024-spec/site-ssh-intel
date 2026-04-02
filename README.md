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
   Group=www-data
   WorkingDirectory=/var/www/site-ssh-intel
   Environment="PATH=/var/www/site-ssh-intel/venv/bin"
   ExecStart=/var/www/site-ssh-intel/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

4. **Iniciar e habilitar o serviço:**
   ```bash
   sudo systemctl start ssh-intel
   sudo systemctl enable ssh-intel
   ```

## 🌐 Passo 7: (Opcional) Abrir Portas no Firewall

Se você não conseguir acessar o site, verifique se a porta 5000 está aberta:

```bash
sudo ufw allow 5000/tcp
```

---

## 📝 Notas Adicionais
- O arquivo `app.py` está configurado para rodar em `0.0.0.0:5000`.
- Certifique-se de que o `API_TOKEN` em `app.py` está correto.
- Para ver os logs do serviço: `sudo journalctl -u ssh-intel`

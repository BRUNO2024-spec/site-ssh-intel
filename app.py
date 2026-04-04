from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
import requests
import os
import platform
import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from models import db, Admin, ServerCard, AppConfig, XrayLink
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

app = Flask(__name__)

# Configurações do App
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ssh_intel.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sua-chave-secreta-padrao')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db.init_app(app)
jwt = JWTManager(app)

# --- Gerenciadores de Erro JWT ---
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Redireciona para o login quando o token expira."""
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp

@jwt.unauthorized_loader
def unauthorized_callback(callback):
    """Redireciona para o login quando o token está ausente."""
    return redirect(url_for('login'))

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    """Redireciona para o login quando o token é inválido."""
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp

with app.app_context():
    db.create_all()
    # Criar admin padrão se não existir (com tratamento para evitar erro em multi-worker)
    from sqlalchemy.exc import IntegrityError
    try:
        admin_user = os.getenv('ADMIN_USERNAME', 'admin')
        if not Admin.query.filter_by(username=admin_user).first():
            admin = Admin(username=admin_user)
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
    except IntegrityError:
        db.session.rollback()
    except Exception as e:
        print(f"Erro ao inicializar admin: {e}")
        db.session.rollback()

# Configurações da API Externa (Legado - serão substituídas pelo DB)
API_TOKEN = "30cee860e5c348d39c9a057c3b918d01"
API_BASE_URL_CREATE = "http://15.228.12.255:2020/v1"
API_BASE_URL_MONITOR = "http://15.228.12.255:3030/v1"

# Configurações do servidor (exibição no card padrão se não houver no DB)
SERVER_CONFIG = {
    "name": "Servidor BR",
    "ip": "15.228.12.255",
    "ports": ["80", "8080"],
    "protocols": ["WS", "WSS", "BadVPN"]
}

def get_external_online_users(monitor_url=None, token=None):
    """Consulta a API externa para obter o total de usuários online e o status do servidor."""
    try:
        if not monitor_url:
            return 0, "Offline"
            
        url = monitor_url.rstrip('/')
        if not url.endswith('/monitor-onlines'):
            url = f"{url}/monitor-onlines"
            
        auth_token = token if token else API_TOKEN
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("total_onlines", 0), "Online"
        return 0, "Offline"
    except Exception as e:
        return 0, "Offline"

def get_external_server_stats(stats_url=None, token=None):
    """Consulta a API externa para obter estatísticas de usuários (criados/expirados)."""
    try:
        if not stats_url:
            return {"total_usuarios_criados": 0, "total_usuarios_expirados": 0}
            
        url = stats_url.rstrip('/')
        if not url.endswith('/api-registros'):
            url = f"{url}/api-registros"
            
        auth_token = token if token else API_TOKEN
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "total_usuarios_criados": data.get("total_usuarios_criados", 0),
                "total_usuarios_expirados": data.get("total_usuarios_expirados", 0)
            }
        return {"total_usuarios_criados": 0, "total_usuarios_expirados": 0}
    except Exception as e:
        return {"total_usuarios_criados": 0, "total_usuarios_expirados": 0}

@app.route("/")
def index():
    cards = ServerCard.query.all()
    support_link = AppConfig.query.filter_by(key='support_link').first()
    support_link_val = support_link.value if support_link else "#"
    
    if not cards:
        # Se não houver cards no DB, usamos o padrão fixo (apenas para compatibilidade inicial)
        online_users, server_status = get_external_online_users(API_BASE_URL_MONITOR)
        return render_template("index.html", config=SERVER_CONFIG, status=server_status, online_users=online_users, support_link=support_link_val)
    
    # Processa os cards do banco
    cards_data = []
    for card in cards:
        online, server_status = get_external_online_users(card.api_url_monitor, card.api_token)
        cards_data.append({
            "id": card.id,
            "name": card.name,
            "ip": card.ip,
            "flag": f"https://flagcdn.com/{card.flag_code}.svg",
            "ports": card.ports.split(',') if card.ports else [],
            "protocols": card.protocols.split(',') if card.protocols else [],
            "online_users": online,
            "status": server_status,
            "google_ads_enabled": card.google_ads_enabled
        })
    return render_template("index.html", cards=cards_data, support_link=support_link_val)

@app.route("/terms")
def terms():
    terms_config = AppConfig.query.filter_by(key='terms_content').first()
    terms_content = terms_config.value if terms_config else "Defina os termos de uso no painel administrativo."
    return render_template("terms.html", terms_content=terms_content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            access_token = create_access_token(identity=username)
            resp = make_response(redirect(url_for('dashboard')))
            set_access_cookies(resp, access_token)
            return resp
        return render_template("login.html", error="Usuário ou senha inválidos")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp

@app.route("/dashboard")
@jwt_required()
def dashboard():
    cards = ServerCard.query.all()
    cards_count = len(cards)
    
    total_criados = 0
    total_expirados = 0
    total_onlines = 0
    
    for card in cards:
        # Busca usuários online
        online, _ = get_external_online_users(card.api_url_monitor, card.api_token)
        total_onlines += online
        
        # Busca estatísticas (criados/expirados)
        stats = get_external_server_stats(card.api_url_stats, card.api_token)
        total_criados += stats.get("total_usuarios_criados", 0)
        total_expirados += stats.get("total_usuarios_expirados", 0)
        
    return render_template("dashboard.html", 
                         cards_count=cards_count, 
                         total_criados=total_criados, 
                         total_expirados=total_expirados,
                         total_onlines=total_onlines)

@app.route("/card", methods=["GET", "POST"])
@jwt_required()
def manage_cards():
    cards = ServerCard.query.all()
    return render_template("manage_cards.html", cards=cards)

@app.route("/card/save", methods=["POST"])
@jwt_required()
def save_card():
    card_id = request.form.get("id")
    name = request.form.get("name")
    ip = request.form.get("ip")
    flag_code = request.form.get("flag_code")
    ports = request.form.get("ports")
    protocols = request.form.get("protocols")
    api_token = request.form.get("api_token")
    api_url_create = request.form.get("api_url_create")
    api_url_monitor = request.form.get("api_url_monitor")
    api_url_stats = request.form.get("api_url_stats")
    google_ads_enabled = 'google_ads_enabled' in request.form
    google_ads_code = request.form.get("google_ads_code")

    if card_id:
        card = ServerCard.query.get(card_id)
    else:
        card = ServerCard()

    card.name = name
    card.ip = ip
    card.flag_code = flag_code
    card.ports = ports
    card.protocols = protocols
    card.api_token = api_token
    card.api_url_create = api_url_create
    card.api_url_monitor = api_url_monitor
    card.api_url_stats = api_url_stats
    card.google_ads_enabled = google_ads_enabled
    card.google_ads_code = google_ads_code

    if not card_id:
        db.session.add(card)
    
    db.session.commit()
    return redirect(url_for('manage_cards'))

@app.route("/card/delete/<int:id>", methods=["POST"])
@jwt_required()
def delete_card(id):
    card = ServerCard.query.get_or_404(id)
    db.session.delete(card)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/config", methods=["GET", "POST"])
@jwt_required()
def settings():
    username = get_jwt_identity()
    admin = Admin.query.filter_by(username=username).first()
    
    # Obter configurações atuais
    support_link = AppConfig.query.filter_by(key='support_link').first()
    terms_content = AppConfig.query.filter_by(key='terms_content').first()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "security":
            current_password = request.form.get("current_password")
            new_username = request.form.get("new_username")
            new_password = request.form.get("new_password")

            if not admin.check_password(current_password):
                return render_template("settings.html", admin_username=username, 
                                     support_link=support_link.value if support_link else "",
                                     terms_content=terms_content.value if terms_content else "",
                                     error="Senha atual incorreta")

            if new_username and new_username != username:
                if Admin.query.filter_by(username=new_username).first():
                    return render_template("settings.html", admin_username=username, error="Novo usuário já existe")
                admin.username = new_username
                db.session.commit()
                access_token = create_access_token(identity=new_username)
                resp = make_response(render_template("settings.html", admin_username=new_username, 
                                                   support_link=support_link.value if support_link else "",
                                                   terms_content=terms_content.value if terms_content else "",
                                                   success="Configurações salvas com sucesso!"))
                set_access_cookies(resp, access_token)
                return resp

            if new_password:
                if len(new_password) < 8:
                    return render_template("settings.html", admin_username=username, error="A nova senha deve ter pelo menos 8 dígitos")
                admin.set_password(new_password)

            db.session.commit()
            return render_template("settings.html", admin_username=admin.username, 
                                 support_link=support_link.value if support_link else "",
                                 terms_content=terms_content.value if terms_content else "",
                                 success="Configurações de segurança salvas!")

        elif action == "general":
            new_support = request.form.get("support_link")
            new_terms = request.form.get("terms_content")
            
            if not support_link:
                support_link = AppConfig(key='support_link', value=new_support)
                db.session.add(support_link)
            else:
                support_link.value = new_support
                
            if not terms_content:
                terms_content = AppConfig(key='terms_content', value=new_terms)
                db.session.add(terms_content)
            else:
                terms_content.value = new_terms
                
            db.session.commit()
            return render_template("settings.html", admin_username=username, 
                                 support_link=new_support, 
                                 terms_content=new_terms,
                                 success="Configurações gerais salvas!")

    return render_template("settings.html", admin_username=username, 
                         support_link=support_link.value if support_link else "",
                         terms_content=terms_content.value if terms_content else "")

# --- XRAY LINKS CRUD ---
@app.route("/admin/xray")
@jwt_required()
def admin_xray():
    links = XrayLink.query.order_by(XrayLink.created_at.desc()).all()
    return render_template("admin_xray.html", links=links)

@app.route("/api/xray-links", methods=["GET"])
def get_xray_links():
    links = XrayLink.query.filter_by(is_active=True).all()
    return jsonify([{
        "id": l.id,
        "name": l.name,
        "link": l.link
    } for l in links])

@app.route("/admin/xray/save", methods=["POST"])
@jwt_required()
def save_xray_link():
    link_id = request.form.get("id")
    name = request.form.get("name")
    link_text = request.form.get("link")
    is_active = 'is_active' in request.form

    if link_id:
        x_link = XrayLink.query.get(link_id)
    else:
        x_link = XrayLink()
    
    x_link.name = name
    x_link.link = link_text
    x_link.is_active = is_active

    if not link_id:
        db.session.add(x_link)
    
    db.session.commit()
    return redirect(url_for('admin_xray'))

@app.route("/admin/xray/delete/<int:id>", methods=["POST"])
@jwt_required()
def delete_xray_link(id):
    x_link = XrayLink.query.get_or_404(id)
    db.session.delete(x_link)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/admin/xray/toggle/<int:id>", methods=["POST"])
@jwt_required()
def toggle_xray_link(id):
    x_link = XrayLink.query.get_or_404(id)
    x_link.is_active = not x_link.is_active
    db.session.commit()
    return jsonify({"success": True, "is_active": x_link.is_active})

@app.route("/criar/<int:card_id>", methods=["POST"])
def criar_usuario(card_id):
    """Cria um usuário SSH real via API para um card específico."""
    card = ServerCard.query.get_or_404(card_id)
    
    if not card.api_url_create:
        return jsonify({"success": False, "message": "URL da API de criação não configurada para este card."}), 400
    
    try:
        # Fallback para o token global se o do card estiver vazio
        auth_token = card.api_token if card.api_token else API_TOKEN
        headers = {"Authorization": f"Bearer {auth_token}"}
        url = f"{card.api_url_create.rstrip('/')}/criar-usuario"
        
        # Log para depuração (mascarando o token)
        token_preview = f"{auth_token[:4]}***{auth_token[-4:]}" if auth_token else "Nenhum"
        print(f"Chamando API: {url} | Token: {token_preview}")
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            try:
                api_data = response.json()
            except ValueError:
                return jsonify({"success": False, "message": "Resposta da API não é um JSON válido."}), 500
                
            if api_data.get("status") == "success":
                return jsonify({
                    "success": True,
                    "message": "Usuário criado com sucesso!",
                    "credentials": {
                        "ip": card.ip,
                        "username": api_data.get("usuario"),
                        "password": api_data.get("senha"),
                        "uuid": api_data.get("xray_uuid"),
                        "domain": api_data.get("dominio"),
                        "expiry": api_data.get("validade"),
                        "port": card.ports
                    }
                })
            else:
                return jsonify({"success": False, "message": api_data.get("message", "Erro na API externa.")}), 400
        elif response.status_code == 401:
            return jsonify({"success": False, "message": "Token de autorização inválido (401). Verifique o token no Painel Admin."}), 401
        else:
            return jsonify({"success": False, "message": f"Erro na API externa (Status: {response.status_code})"}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "A API externa demorou muito para responder (Timeout)."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"Erro de conexão com a API: {str(e)}"}), 500
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@app.route("/admin/api/stats")
@jwt_required()
def admin_api_stats():
    """Retorna estatísticas agregadas de todos os servidores para a dashboard."""
    cards = ServerCard.query.all()
    
    total_criados = 0
    total_expirados = 0
    total_onlines = 0
    
    for card in cards:
        # Busca usuários online
        online, _ = get_external_online_users(card.api_url_monitor, card.api_token)
        total_onlines += online
        
        # Busca estatísticas (criados/expirados)
        stats = get_external_server_stats(card.api_url_stats, card.api_token)
        total_criados += stats.get("total_usuarios_criados", 0)
        total_expirados += stats.get("total_usuarios_expirados", 0)
        
    return jsonify({
        "total_onlines": total_onlines,
        "total_criados": total_criados,
        "total_expirados": total_expirados
    })

@app.route("/online/all")
def online_status_all():
    """Endpoint para atualização em tempo real de todos os cards."""
    cards = ServerCard.query.all()
    results = {}
    for card in cards:
        online, status = get_external_online_users(card.api_url_monitor, card.api_token)
        results[card.id] = {
            "online": online,
            "status": status
        }
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5340)

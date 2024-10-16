from flask import Flask, render_template, redirect, url_for, request, send_file, jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
    UserMixin,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from flask_migrate import Migrate
from datetime import datetime
import pandas as pd
import pytz
import cloudinary.uploader
import os
import requests
import json
import random
import io
from functools import wraps


app = Flask(__name__)
app.secret_key = "uma_chave_secreta_muito_segura"
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024 * 1024


uri = os.getenv("DATABASE_URL", "sqlite:///local.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri

cloudinary.config(
    cloud_name="hbmghdcte",
    api_key="728847166383671",
    api_secret="PJPwG2x4O2GnsgxVmjfQg8ppJx4",
)

# Configurações do Flask-Mail
app.config["MAIL_SERVER"] = "smtp.hostinger.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Após a configuração do aplicativo
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class FormEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    senar = db.Column(db.String(200), nullable=False)
    formacao_detail = db.Column(db.String(100), nullable=True)
    promocao_detail = db.Column(db.String(100), nullable=True)
    assistencia_detail = db.Column(db.String(100), nullable=True)
    cep = db.Column(db.String(32), nullable=False)
    estado = db.Column(db.String(32), nullable=False)
    telefone = db.Column(db.String(32), nullable=False)
    referencia_video = db.Column(db.String(200), nullable=True)
    formacao = db.Column(db.String(100), nullable=False)
    promocao = db.Column(db.String(100), nullable=True)
    assistencia = db.Column(db.String(100), nullable=True)
    link_arquivo = db.Column(db.String(200), nullable=True)
    link_pdf = db.Column(db.String(200), nullable=True)
    aceite_termos = db.Column(db.String(200), nullable=True)
    aceite_whatsapp = db.Column(db.String(200), nullable=True)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.now)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(32), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # Novo campo

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route("/download_avaliacoes")
@login_required
def download_avaliacoes():
    # Realizando o join entre AvaliacaoEntry e FormEntry para obter dados completos
    avaliacoes = (
        db.session.query(AvaliacaoEntry, FormEntry)
        .join(FormEntry, AvaliacaoEntry.form_entry_id == FormEntry.id)
        .all()
    )

    # Preparando os dados para o DataFrame
    data = [
        {
            "ID Avaliação": avaliacao.id,
            "Nome Avaliador": avaliacao.nome_avaliador,
            "ID Inscrição": inscricao.id,
            "Nome Inscrito": inscricao.nome,
            "Postura": avaliacao.nota_postura,
            "Conteúdo": avaliacao.nota_conteudo,
            "Imagens": avaliacao.nota_imagens,
            "Áudio": avaliacao.nota_audio,
            "Criatividade": avaliacao.nota_criatividade,
            "Pertinência": avaliacao.nota_pertinencia,
            "Contextualização": avaliacao.nota_contextualizacao,
            "Gráficos": avaliacao.nota_graficos,
            "Data Avaliação": avaliacao.data_avaliacao.strftime("%d/%m/%Y %H:%M"),
        }
        for avaliacao, inscricao in avaliacoes
    ]

    # Criando o DataFrame com os dados das avaliações
    df = pd.DataFrame(data)

    # Criando um arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Avaliacoes")
    output.seek(0)

    # Enviando o arquivo Excel como download
    return send_file(
        output,
        as_attachment=True,
        download_name="avaliacoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class AvaliacaoEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_entry_id = db.Column(
        db.Integer, db.ForeignKey("form_entry.id"), nullable=False
    )
    nome_avaliador = db.Column(db.String(100), nullable=False)
    nota_postura = db.Column(db.Integer, nullable=False)
    nota_conteudo = db.Column(db.Integer, nullable=False)
    nota_imagens = db.Column(db.Integer, nullable=False)
    nota_audio = db.Column(db.Integer, nullable=False)
    nota_criatividade = db.Column(db.Integer, nullable=False)
    nota_pertinencia = db.Column(db.Integer, nullable=False)
    nota_contextualizacao = db.Column(db.Integer, nullable=False)
    nota_graficos = db.Column(db.Integer, nullable=False)
    data_avaliacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com FormEntry
    form_entry = db.relationship(
        "FormEntry", backref=db.backref("avaliacoes", lazy=True)
    )


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/public/users", methods=["GET"])
def public_users():
    users = User.query.all()
    users_data = [
        {
            "id": user.id,
            "username": user.username,
            "estado": user.estado,
            "is_admin": user.is_admin,
            # "password_hash": user.password_hash  # Descomente se quiser ver o hash
        }
        for user in users
    ]
    return jsonify(users_data)


from functools import wraps


def public_register_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret = request.args.get("secret")
        if not secret or secret != os.getenv("PUBLIC_REGISTER_SECRET"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/avaliacoes", methods=["GET"])
@login_required
def ver_todas_avaliacoes():
    avaliacoes = (
        db.session.query(AvaliacaoEntry, FormEntry)
        .join(FormEntry, AvaliacaoEntry.form_entry_id == FormEntry.id)
        .all()
    )

    return render_template("todas_avaliacoes.html", avaliacoes=avaliacoes)


@app.route("/inscricoes/<int:inscricao_id>/deletar", methods=["POST"])
@login_required
def deletar_inscricao(inscricao_id):
    inscricao = FormEntry.query.get_or_404(inscricao_id)

    # Verificar permissões
    if not current_user.is_admin and inscricao.estado != current_user.estado:
        return "Acesso negado", 403

    # Excluir as avaliações relacionadas
    AvaliacaoEntry.query.filter_by(form_entry_id=inscricao.id).delete()

    # Excluir a inscrição
    db.session.delete(inscricao)
    db.session.commit()

    return redirect(url_for("listar_inscricoes"))


@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return "Acesso negado", 403

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        return "Você não pode excluir seu próprio usuário.", 400

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("list_users"))


@app.route("/public/register", methods=["GET", "POST"])
def public_register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        estado = request.form.get("estado")
        is_admin = True if request.form.get("is_admin") == "on" else False

        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("public_register.html")

        # Criar novo usuário
        new_user = User(username=username, estado=estado, is_admin=is_admin)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("public_register.html")


@app.route("/referenciar/<int:entry_id>", methods=["POST"])
@login_required
def referenciar_inscricao(entry_id):
    inscricao = FormEntry.query.get_or_404(entry_id)

    # Verificação de permissão (opcional)
    if not current_user.is_admin and inscricao.estado != current_user.estado:
        return "Acesso negado", 403

    # Obtenção dos dados do formulário
    referencia = request.form.get("referencia")
    novo_dado = request.form.get("novo_dado")

    # Validação básica (adapte conforme necessário)
    if not referencia:
        # Você pode adicionar mensagens de erro ou redirecionar com mensagens
        return "Referência é obrigatória", 400

    # Atualização dos campos conforme necessário
    inscricao.referencia_video = referencia  # Exemplo de atualização
    if novo_dado:
        inscricao.assistencia_detail = novo_dado  # Exemplo de atualização

    # Commit das alterações no banco de dados
    db.session.commit()

    # Redireciona de volta para a lista de inscrições com uma mensagem de sucesso
    return redirect(url_for("listar_inscricoes"))


@app.route("/avaliacao/<int:entry_id>", methods=["POST"])
@login_required
def salvar_avaliacao(entry_id):
    form_entry = FormEntry.query.get_or_404(entry_id)

    # Obtenção dos dados do formulário de avaliação
    nome_avaliador = request.form.get("nome_avaliador")
    nota_postura = int(request.form.get("nota_postura"))
    nota_conteudo = int(request.form.get("nota_conteudo"))
    nota_imagens = int(request.form.get("nota_imagens"))
    nota_audio = int(request.form.get("nota_audio"))
    nota_criatividade = int(request.form.get("nota_criatividade"))
    nota_pertinencia = int(request.form.get("nota_pertinencia"))
    nota_contextualizacao = int(request.form.get("nota_contextualizacao"))
    nota_graficos = int(request.form.get("nota_graficos"))

    # Criação de uma nova avaliação
    avaliacao = AvaliacaoEntry(
        form_entry_id=entry_id,
        nome_avaliador=nome_avaliador,
        nota_postura=nota_postura,
        nota_conteudo=nota_conteudo,
        nota_imagens=nota_imagens,
        nota_audio=nota_audio,
        nota_criatividade=nota_criatividade,
        nota_pertinencia=nota_pertinencia,
        nota_contextualizacao=nota_contextualizacao,
        nota_graficos=nota_graficos,
    )

    # Salvar no banco de dados
    db.session.add(avaliacao)
    db.session.commit()

    return redirect(url_for("listar_inscricoes"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        print(f"Tentativa de login com username: {username}")

        user = User.query.filter_by(username=username).first()

        if not user:
            print("Usuário não encontrado.")
        elif not user.check_password(password):
            print("Senha inválida.")
        else:
            login_user(user)
            print(f"Usuário {username} logado com sucesso.")
            return redirect(url_for("listar_inscricoes"))

        return render_template("login.html", error="Usuário ou senha inválidos")

    return render_template("login.html")


@app.route("/inscricoes", methods=["GET"])
@login_required
def listar_inscricoes():
    if current_user.is_admin:
        inscricoes = FormEntry.query.all()
    else:
        inscricoes = FormEntry.query.filter_by(estado=current_user.estado).all()

    for inscricao in inscricoes:
        inscricao.ja_avaliou = any(
            avaliacao.nome_avaliador == current_user.username
            for avaliacao in inscricao.avaliacoes
        )

    return render_template("listar_inscricoes.html", inscricoes=inscricoes)


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if not current_user.is_admin:
        return "Acesso negado", 403

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        estado = request.form["estado"]
        is_admin = "is_admin" in request.form  # Checkbox no formulário

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Usuário já existe")

        new_user = User(username=username, estado=estado, is_admin=is_admin)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("list_users"))
    return render_template("register.html")


@app.route("/users", methods=["GET"])
@login_required
def list_users():
    if not current_user.is_admin:
        return "Acesso negado", 403

    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_data = request.form.to_dict()
        video_url = request.form.get("videoUrl")
        pdf_file = request.files.get("pdfUpload")
        email = request.form.get("email")
        responsavel = request.form.get("nome")

        if not video_url:
            return jsonify({"error": "O link do vídeo é obrigatório."}), 400

        try:
            link_video = video_url  # A URL já foi obtida do frontend

            link_pdf = None
            if pdf_file and pdf_file.filename != "":
                upload_result_pdf = cloudinary.uploader.upload(
                    pdf_file.read(),
                    resource_type="raw",
                    folder="pdf_uploads",
                )
                link_pdf = upload_result_pdf.get("url")

            timezone_bsb = pytz.timezone("America/Sao_Paulo")
            bsb_time = datetime.now(timezone_bsb)

            new_entry = FormEntry(
                nome=form_data.get("nome"),
                cpf=form_data.get("cpf"),
                email=email,
                endereco=form_data.get("endereco"),
                senar=form_data.get("senarSelect"),
                cep=form_data.get("cep"),
                estado=form_data.get("estado"),
                telefone=form_data.get("telefone"),
                referencia_video=form_data.get("referencia_video"),
                formacao=form_data.get("formacao"),
                promocao=form_data.get("promocao"),
                assistencia=form_data.get("assistencia"),
                formacao_detail=form_data.get("detalhesFormacao"),
                promocao_detail=form_data.get("detalhesPromocao"),
                assistencia_detail=form_data.get("detalhesAssistencia"),
                link_arquivo=link_video,
                link_pdf=link_pdf,
                aceite_termos=form_data.get("acceptTerms", "Não"),
                aceite_whatsapp=form_data.get("acceptWhatsApp", "Não"),
                data_envio=bsb_time,
            )
            db.session.add(new_entry)
            db.session.commit()

            html_content = render_template(
                "email_template.html", nome_produtor=responsavel
            )
            send_email(email, "Confirmação de Inscrição", html_content)

            return jsonify(
                {
                    "message": "Inscrição confirmada com sucesso!",
                    "link_arquivo": link_video,
                    "link_pdf": link_pdf or "Nenhum arquivo PDF enviado.",
                }
            )

        except Exception as e:
            return jsonify({"error": f"Erro no processamento: {str(e)}"}), 500

    return render_template("form.html")


def send_email(to_email, subject, html_content):
    with app.app_context():
        msg = Message(subject, recipients=[to_email], html=html_content)
        mail.send(msg)


def enviar_whatsapp(message, celular):
    instance_id = "3CEECDAD20E58068BF148A74AFBCE7F1"
    token = "6D4813ECC30AC60A40EC78DF"
    client_token = "Fd177f367ea084db78008dcb4627e63fdS"

    phone = celular

    conteudo_texto = json.dumps({"phone": phone, "message": message})

    post_url_texto = (
        f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text"
    )

    headers = {"Content-Type": "application/json", "Client-Token": client_token}

    response_texto = requests.post(post_url_texto, headers=headers, data=conteudo_texto)

    try:
        response_texto.raise_for_status()
        data_texto = response_texto.json()
        print("Mensagem de texto enviada com sucesso:", data_texto)
    except requests.exceptions.HTTPError as err:
        print("Erro na requisição de texto:", err)
        print("Resposta:", response_texto.text)


@app.route("/download")
def download():
    entries = FormEntry.query.all()
    data = [
        {column.name: getattr(entry, column.name) for column in entry.__table__.columns}
        for entry in entries
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Entries")
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="entries.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/entries")
def view_entries():
    entries = FormEntry.query.all()
    return render_template("entries.html", entries=entries)


if __name__ == "__main__":
    app.run(debug=True)

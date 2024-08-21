from flask import Flask, request, jsonify, render_template, send_file
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import pytz
import cloudinary.uploader
import os
import requests
import json
import random
import io

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
    link_pdf = db.Column(db.String(200), nullable=False)
    aceite_termos = db.Column(db.String(200), nullable=True)
    aceite_whatsapp = db.Column(db.String(200), nullable=True)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.now)


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_data = request.form.to_dict()

        video_file = request.files.get("videoUpload")
        pdf_file = request.files.get("pdfUpload")
        email = request.form.get("email")
        responsavel = request.form.get("nome")

        # Verifica se o arquivo de vídeo foi enviado
        if not video_file:
            return jsonify({"error": "Arquivo de vídeo é obrigatório."}), 400

        # Verifica se o arquivo de vídeo tem um nome de arquivo válido e uma extensão de vídeo
        if not video_file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            return (
                jsonify(
                    {
                        "error": "O arquivo enviado não é um vídeo válido. Aceitamos formatos .mp4, .avi, .mov, .mkv."
                    }
                ),
                400,
            )

        # Verifica se o arquivo PDF foi enviado e se é um PDF
        if not pdf_file or not pdf_file.filename.lower().endswith(".pdf"):
            return (
                jsonify(
                    {"error": "Arquivo PDF é obrigatório e deve estar no formato PDF."}
                ),
                400,
            )

        try:
            # Tenta fazer o upload do vídeo
            upload_result_video = cloudinary.uploader.upload(
                video_file, resource_type="video", folder="video_uploads"
            )
            link_video = upload_result_video.get("url")

            # Tenta fazer o upload do PDF
            upload_result_pdf = cloudinary.uploader.upload(
                pdf_file, resource_type="raw", folder="pdf_uploads"
            )
            link_pdf = upload_result_pdf.get("url")

            # Obtém o horário de Brasília
            timezone_bsb = pytz.timezone("America/Sao_Paulo")
            bsb_time = datetime.now(timezone_bsb)

            # Cria uma nova entrada no banco de dados
            new_entry = FormEntry(
                nome=form_data.get("nome"),
                cpf=form_data.get("cpf"),
                email=form_data.get("email"),
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

            # Preparando o conteúdo do e-mail utilizando um template HTML
            to_email = email  # Usa o e-mail fornecido pelo usuário
            subject = "Confirmação de Inscrição"

            # Renderiza o template HTML como string, passando a variável 'responsavel' como 'nome_produtor'
            html_content = render_template(
                "email_template.html", nome_produtor=responsavel
            )

            # Dispara o e-mail após salvar a inscrição
            send_email(to_email, subject, html_content)

            return jsonify(
                {
                    "message": "Vídeo e termo de imagem registrados com sucesso!",
                    "link_arquivo": link_video,
                    "link_pdf": link_pdf,
                }
            )

        except cloudinary.exceptions.Error as cloudinary_error:
            return (
                jsonify(
                    {"error": f"Erro ao fazer upload do vídeo: {str(cloudinary_error)}"}
                ),
                500,
            )
        except Exception as e:
            return (
                jsonify(
                    {"error": f"Ocorreu um erro ao processar sua solicitação: {str(e)}"}
                ),
                500,
            )

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


@app.route("/entries")
def view_entries():
    entries = FormEntry.query.all()
    return render_template("entries.html", entries=entries)


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
import cloudinary.uploader
import os

app = Flask(__name__)
app.secret_key = 'uma_chave_secreta_muito_segura'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1 GB

uri = os.getenv("DATABASE_URL", "sqlite:///local.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri

cloudinary.config(
    cloud_name="hbmghdcte",
    api_key="728847166383671",
    api_secret="PJPwG2x4O2GnsgxVmjfQg8ppJx4",
)

db = SQLAlchemy(app)

class FormEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(32), nullable=False, unique=True)
    endereco = db.Column(db.String(200), nullable=False)
    cep = db.Column(db.String(32), nullable=False)
    estado = db.Column(db.String(32), nullable=False)
    telefone = db.Column(db.String(32), nullable=False)
    tema = db.Column(db.String(100), nullable=False)
    referencia_video = db.Column(db.String(200), nullable=True)
    formacao = db.Column(db.String(100), nullable=False)
    promocao = db.Column(db.String(100), nullable=True)
    assistencia = db.Column(db.String(100), nullable=True)
    link_arquivo = db.Column(db.String(200), nullable=True)
    aceite_termos = db.Column(db.String(200), nullable=True)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.now)


with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_data = request.form.to_dict()

        # Upload de vídeo
        video_file = request.files.get("videoUpload")
        if video_file:
            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    video_file,
                    resource_type='video',
                    folder='video_uploads'
                )
                link_video = upload_result.get('url')

                timezone_bsb = pytz.timezone('America/Sao_Paulo')
                bsb_time = datetime.now(timezone_bsb)

                # Salvando no banco de dados
                new_entry = FormEntry(
                    nome=form_data.get('nome'), 
                    cpf=form_data.get('cpf'), 
                    endereco=form_data.get('endereco'), 
                    cep=form_data.get('cep'),
                    estado=form_data.get('estado'), 
                    telefone=form_data.get('telefone'), 
                    tema=form_data.get('tema'),
                    referencia_video=form_data.get('referencia_video'),
                    promocao=form_data.get('promocao'),
                    formacao=form_data.get('formacao'),
                    assistencia=form_data.get('assistencia'),
                    aceite_termos=form_data.get('privacyPolicy'),
                    link_arquivo=link_video,
                    data_envio=bsb_time
                )
                db.session.add(new_entry)
                db.session.commit()

                return jsonify({"message": "Vídeo registrado com sucesso!", "link_arquivo": link_video})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Arquivo de vídeo é obrigatório."}), 400

    return render_template("form.html")

@app.route("/entries")
def view_entries():
    entries = FormEntry.query.all()
    return render_template("entries.html", entries=entries)

if __name__ == "__main__":
    app.run(debug=True)

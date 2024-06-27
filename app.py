from flask import Flask, request, jsonify, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import cloudinary.uploader
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuração do banco de dados
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///local.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


cloudinary.config(
    cloud_name="hbmghdcte",
    api_key="728847166383671",
    api_secret="PJPwG2x4O2GnsgxVmjfQg8ppJx4",
)

db = SQLAlchemy(app)


# Definição do modelo da tabela
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


# Cria a tabela no banco de dados
with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_file = request.files["videoUpload"]
        if video_file:
            filename = secure_filename(video_file.filename)
            upload_result = cloudinary.uploader.upload(
                video_file, resource_type="video"
            )
            video_url = upload_result["url"]

            # Instância para salvar no banco de dados
            new_entry = FormEntry(
                nome=request.form.get("nome"),
                cpf=request.form.get("cpf"),
                endereco=request.form.get("endereco"),
                cep=request.form.get("cep"),
                estado=request.form.get("estado"),
                telefone=request.form.get("telefone"),
                tema=request.form.get("tema"),
                referencia_video=request.form.get("referencia_video"),
                formacao=request.form.get("formacao"),
                promocao=request.form.get("promocao"),
                assistencia=request.form.get("assistencia"),
                link_arquivo=video_url,
            )

            db.session.add(new_entry)
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Vídeo registrado com sucesso!",
                        "video_url": video_url,
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Vídeo não anexado!"}), 400

    return render_template("form.html")


@app.route("/entries")
def view_entries():
    entries = FormEntry.query.all()  # Pega todos os registros do banco de dados
    return render_template("entries.html", entries=entries)


if __name__ == "__main__":
    app.run(debug=True)

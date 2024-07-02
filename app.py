from flask import Flask, request, jsonify, redirect, url_for, render_template, session
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import cloudinary.uploader
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

uri = os.getenv(
    "DATABASE_URL", "sqlite:///local.db"
)  # Default to SQLite for local development
if uri.startswith("postgres://"):
    uri = uri.replace(
        "postgres://", "postgresql://", 1
    )  # Required for SQLAlchemy compatibility

app.config["SQLALCHEMY_DATABASE_URI"] = uri


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
        session["form_data"] = request.form.to_dict()
        session["video_file"] = request.files["videoUpload"]
        return redirect(url_for("termo_aceite"))

    return render_template("form.html")


@app.route("/termo_aceite", methods=["GET", "POST"])
def termo_aceite():
    if request.method == "POST":
        if "aceito" in request.form:
            try:
                video_file = session["video_file"]
                upload_result = cloudinary.uploader.upload(
                    video_file, resource_type="video"
                )
                video_url = upload_result["url"]

                new_entry = FormEntry(**session["form_data"], link_arquivo=video_url)
                db.session.add(new_entry)
                db.session.commit()

                # Limpar a sessão após o uso
                session.pop("form_data", None)
                session.pop("video_file", None)

                return (
                    jsonify(
                        {
                            "message": "Vídeo registrado com sucesso!",
                            "video_url": video_url,
                        }
                    ),
                    200,
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return render_template(
                "termo_aceite.html", error="Você deve aceitar os termos para continuar."
            )

    form_data = session.get("form_data", {})
    return render_template("termo_aceite.html", form_data=form_data)


@app.route("/entries")
def view_entries():
    entries = FormEntry.query.all()
    return render_template("entries.html", entries=entries)


if __name__ == "__main__":
    app.run(debug=True)

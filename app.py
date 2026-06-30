import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.utils import secure_filename

from models import db, Admin, Ebook

# ---------------------------------------------------------------------------
# Configuração da aplicação
# ---------------------------------------------------------------------------

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB por upload

# Banco de dados: usa DATABASE_URL do Render (Postgres) se existir,
# senão usa um arquivo SQLite local para desenvolvimento.
database_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "ebooks.db"))
if database_url.startswith("postgres://"):
    # SQLAlchemy moderno exige "postgresql://"
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "Faça login para acessar o painel administrativo."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage):
    """Salva o arquivo enviado com um nome único e retorna o nome salvo."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        flash("Formato de imagem não suportado. Use PNG, JPG, JPEG, GIF ou WEBP.", "danger")
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(filepath)
    return unique_name


def create_default_admin():
    """Cria o usuário admin padrão se ainda não existir nenhum admin no banco."""
    if Admin.query.first() is None:
        email = os.environ.get("ADMIN_EMAIL", "junior007eai@gmail.com")
        password = os.environ.get("ADMIN_PASSWORD", "senha22dificil08academia14")
        admin = Admin(email=email)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"[setup] Admin padrão criado: {email}")


# ---------------------------------------------------------------------------
# Rotas públicas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    ebooks = Ebook.query.order_by(Ebook.created_at.desc()).all()
    return render_template("index.html", ebooks=ebooks)


# ---------------------------------------------------------------------------
# Autenticação do admin
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash("Login realizado com sucesso!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin_dashboard"))

        flash("E-mail ou senha incorretos.", "danger")

    return render_template("login.html")


@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    flash("Você saiu do painel administrativo.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Painel administrativo (CRUD de ebooks) - tudo protegido por login
# ---------------------------------------------------------------------------

@app.route("/admin")
@login_required
def admin_dashboard():
    ebooks = Ebook.query.order_by(Ebook.created_at.desc()).all()
    return render_template("admin_dashboard.html", ebooks=ebooks)


@app.route("/admin/ebooks/novo", methods=["GET", "POST"])
@login_required
def ebook_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        purchase_link = request.form.get("purchase_link", "").strip()
        image_url = request.form.get("image_url", "").strip()
        image_file = request.files.get("image_file")

        if not title or not description or not purchase_link:
            flash("Preencha pelo menos título, descrição e link de aquisição.", "danger")
            return render_template("ebook_form.html", ebook=None, action="Novo")

        filename = save_uploaded_image(image_file)

        ebook = Ebook(
            title=title,
            description=description,
            price=price or None,
            purchase_link=purchase_link,
            image_filename=filename,
            image_url=image_url or None,
        )
        db.session.add(ebook)
        db.session.commit()
        flash("Ebook cadastrado com sucesso!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("ebook_form.html", ebook=None, action="Novo")


@app.route("/admin/ebooks/<int:ebook_id>/editar", methods=["GET", "POST"])
@login_required
def ebook_edit(ebook_id):
    ebook = Ebook.query.get_or_404(ebook_id)

    if request.method == "POST":
        ebook.title = request.form.get("title", "").strip()
        ebook.description = request.form.get("description", "").strip()
        ebook.price = request.form.get("price", "").strip() or None
        ebook.purchase_link = request.form.get("purchase_link", "").strip()
        ebook.image_url = request.form.get("image_url", "").strip() or None

        image_file = request.files.get("image_file")
        new_filename = save_uploaded_image(image_file)
        if new_filename:
            # remove a imagem antiga, se existir
            if ebook.image_filename:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], ebook.image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            ebook.image_filename = new_filename

        if not ebook.title or not ebook.description or not ebook.purchase_link:
            flash("Preencha pelo menos título, descrição e link de aquisição.", "danger")
            return render_template("ebook_form.html", ebook=ebook, action="Editar")

        db.session.commit()
        flash("Ebook atualizado com sucesso!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("ebook_form.html", ebook=ebook, action="Editar")


@app.route("/admin/ebooks/<int:ebook_id>/excluir", methods=["POST"])
@login_required
def ebook_delete(ebook_id):
    ebook = Ebook.query.get_or_404(ebook_id)

    if ebook.image_filename:
        path = os.path.join(app.config["UPLOAD_FOLDER"], ebook.image_filename)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(ebook)
    db.session.commit()
    flash("Ebook excluído.", "info")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# Inicialização do banco
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()
    create_default_admin()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

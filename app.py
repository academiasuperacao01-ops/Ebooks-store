import os, uuid, json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Admin, Ebook, Lead

basedir      = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
ALLOWED_EXT  = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"]                  = os.environ.get("SECRET_KEY", "troque-em-producao-xK9#mP2")
app.config["UPLOAD_FOLDER"]              = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"]         = 8 * 1024 * 1024

db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "ebooks.db"))
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"]    = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view         = "admin_login"
login_manager.login_message      = "Faça login para acessar o painel."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(uid):
    return Admin.query.get(int(uid))

# ── helpers ────────────────────────────────────────────────────────────────

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def save_image(fs):
    if not fs or fs.filename == "":
        return None
    if not allowed(fs.filename):
        flash("Formato não suportado. Use PNG, JPG, JPEG, GIF ou WEBP.", "danger")
        return None
    ext  = fs.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    fs.save(os.path.join(UPLOAD_FOLDER, name))
    return name

def seed_admin():
    if Admin.query.first() is None:
        a = Admin(email=os.environ.get("ADMIN_EMAIL", "junior007eai@gmail.com"))
        a.set_password(os.environ.get("ADMIN_PASSWORD", "senha22dificil08academia14"))
        db.session.add(a)
        db.session.commit()

# ── rotas públicas ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    ebooks = Ebook.query.order_by(Ebook.created_at.desc()).all()
    return render_template("index.html", ebooks=ebooks)

@app.route("/adquirir/<int:ebook_id>", methods=["POST"])
def adquirir(ebook_id):
    ebook     = Ebook.query.get_or_404(ebook_id)
    name      = request.form.get("name", "").strip()
    email     = request.form.get("email", "").strip()
    whatsapp  = request.form.get("whatsapp", "").strip()
    password  = request.form.get("password", "").strip()
    consented = request.form.get("consent") == "on"

    if not name or not email or not whatsapp or not password:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("index") + f"#ebook-{ebook_id}")

    lead = Lead(ebook_id=ebook_id, name=name, email=email,
                whatsapp=whatsapp, consented=consented)
    lead.set_password(password)
    db.session.add(lead)
    db.session.commit()

    return redirect(ebook.purchase_link)

# ── auth ───────────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        adm = Admin.query.filter_by(email=request.form.get("email","").strip().lower()).first()
        if adm and adm.check_password(request.form.get("password","")):
            login_user(adm)
            return redirect(url_for("admin_dashboard"))
        flash("E-mail ou senha incorretos.", "danger")
    return render_template("login.html")

@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("index"))

# ── admin – ebooks ─────────────────────────────────────────────────────────

@app.route("/admin")
@login_required
def admin_dashboard():
    ebooks = Ebook.query.order_by(Ebook.created_at.desc()).all()
    return render_template("admin_dashboard.html", ebooks=ebooks)

@app.route("/admin/ebooks/novo", methods=["GET", "POST"])
@login_required
def ebook_new():
    if request.method == "POST":
        title         = request.form.get("title","").strip()
        description   = request.form.get("description","").strip()
        price         = request.form.get("price","").strip()
        purchase_link = request.form.get("purchase_link","").strip()
        image_url     = request.form.get("image_url","").strip()
        filename      = save_image(request.files.get("image_file"))
        if not title or not description or not purchase_link:
            flash("Preencha título, descrição e link.", "danger")
            return render_template("ebook_form.html", ebook=None, action="Novo")
        db.session.add(Ebook(title=title, description=description,
                             price=price or None, purchase_link=purchase_link,
                             image_filename=filename, image_url=image_url or None))
        db.session.commit()
        flash("Ebook cadastrado!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("ebook_form.html", ebook=None, action="Novo")

@app.route("/admin/ebooks/<int:eid>/editar", methods=["GET", "POST"])
@login_required
def ebook_edit(eid):
    ebook = Ebook.query.get_or_404(eid)
    if request.method == "POST":
        ebook.title         = request.form.get("title","").strip()
        ebook.description   = request.form.get("description","").strip()
        ebook.price         = request.form.get("price","").strip() or None
        ebook.purchase_link = request.form.get("purchase_link","").strip()
        ebook.image_url     = request.form.get("image_url","").strip() or None
        new_img = save_image(request.files.get("image_file"))
        if new_img:
            if ebook.image_filename:
                old = os.path.join(UPLOAD_FOLDER, ebook.image_filename)
                if os.path.exists(old): os.remove(old)
            ebook.image_filename = new_img
        if not ebook.title or not ebook.description or not ebook.purchase_link:
            flash("Preencha título, descrição e link.", "danger")
            return render_template("ebook_form.html", ebook=ebook, action="Editar")
        db.session.commit()
        flash("Ebook atualizado!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("ebook_form.html", ebook=ebook, action="Editar")

@app.route("/admin/ebooks/<int:eid>/excluir", methods=["POST"])
@login_required
def ebook_delete(eid):
    ebook = Ebook.query.get_or_404(eid)
    if ebook.image_filename:
        p = os.path.join(UPLOAD_FOLDER, ebook.image_filename)
        if os.path.exists(p): os.remove(p)
    db.session.delete(ebook)
    db.session.commit()
    flash("Ebook excluído.", "info")
    return redirect(url_for("admin_dashboard"))

# ── admin – leads ──────────────────────────────────────────────────────────

@app.route("/admin/leads")
@login_required
def admin_leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("admin_leads.html", leads=leads)

@app.route("/admin/leads/<int:lid>/excluir", methods=["POST"])
@login_required
def lead_delete(lid):
    lead = Lead.query.get_or_404(lid)
    db.session.delete(lead)
    db.session.commit()
    flash("Lead excluído.", "info")
    return redirect(url_for("admin_leads"))

# ── init ───────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_admin()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

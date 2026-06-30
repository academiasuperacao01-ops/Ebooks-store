# 📚 Loja de Ebooks

Site simples de venda de ebooks com painel administrativo protegido por senha.
Cada ebook tem: imagem de capa, descrição e link externo de aquisição (ex: link de pagamento, Hotmart, Eduzz, etc).

## Funcionalidades

- Página pública com vitrine de ebooks (imagem + descrição + botão "Adquirir agora" que leva ao link externo).
- Painel `/admin` protegido por login (e-mail + senha).
- Admin pode criar, editar e excluir ebooks (título, descrição, preço, imagem e link).
- Imagem pode ser enviada por upload OU informada como link externo.
- Banco de dados: SQLite localmente, PostgreSQL automaticamente no Render.

## Login do admin (padrão, configurável)

- **E-mail:** junior007eai@gmail.com
- **Senha:** senha22dificil08academia14

> Essas credenciais são criadas automaticamente na primeira execução, lendo as variáveis de ambiente `ADMIN_EMAIL` e `ADMIN_PASSWORD`. Você pode (e deve) trocar a senha depois — veja a seção "Trocar a senha do admin" abaixo.

---

## 1. Rodando localmente

```bash
# 1. Crie um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode a aplicação
python app.py
```

Acesse `http://localhost:5000` para ver a loja e `http://localhost:5000/admin/login` para entrar no painel.

Na primeira execução o banco SQLite (`ebooks.db`) é criado automaticamente e o admin padrão é cadastrado.

---

## 2. Subindo para o GitHub

```bash
git init
git add .
git commit -m "Loja de ebooks inicial"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
git push -u origin main
```

---

## 3. Hospedando no Render.com

Você tem duas opções:

### Opção A — Deploy automático com Blueprint (mais fácil)

1. Faça push do projeto (com o arquivo `render.yaml`) para o GitHub.
2. Acesse [render.com](https://render.com) → **New** → **Blueprint**.
3. Selecione o repositório. O Render vai ler o `render.yaml` e criar automaticamente:
   - O serviço web (Flask + Gunicorn)
   - Um banco PostgreSQL gratuito
   - Um disco persistente para guardar as imagens enviadas (`static/uploads`)
   - As variáveis de ambiente `ADMIN_EMAIL` e `ADMIN_PASSWORD` já preenchidas
4. Clique em **Apply** e aguarde o deploy.

### Opção B — Deploy manual

1. No Render, crie um **PostgreSQL** (New → PostgreSQL) e copie a "Internal Database URL".
2. Crie um **Web Service** (New → Web Service) apontando para o seu repositório GitHub.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
3. Em **Environment**, adicione as variáveis:
   - `DATABASE_URL` → a URL do banco que você copiou
   - `SECRET_KEY` → qualquer string aleatória longa
   - `ADMIN_EMAIL` → junior007eai@gmail.com
   - `ADMIN_PASSWORD` → senha22dificil08academia14
4. (Opcional, mas recomendado) Adicione um **Disk** em Settings → Disks, com mount path `static/uploads`, para que as imagens enviadas por upload não sejam apagadas a cada novo deploy.
5. Clique em **Create Web Service**.

> ⚠️ **Importante sobre imagens:** se você não adicionar o disco persistente, as imagens enviadas por upload serão apagadas a cada novo deploy (o disco do Render é "efêmero" no plano gratuito sem disco). Para evitar isso totalmente, você também pode optar por sempre usar o campo **"link de imagem externa"** no formulário (por exemplo, hospedando as capas no Imgur, Cloudinary, ou em um bucket S3) em vez do upload direto.

---

## 4. Trocar a senha/e-mail do admin

A forma mais simples é trocar as variáveis de ambiente `ADMIN_EMAIL` e `ADMIN_PASSWORD` no Render **antes do primeiro deploy** (elas só são usadas para criar o admin automaticamente quando ainda não existe nenhum admin no banco).

Se o admin já existir e você quiser trocar a senha depois, há duas formas:

**A) Apagar o banco e deixar recriar** (perde os ebooks cadastrados — não recomendado em produção).

**B) Trocar via console do Render (recomendado):**

1. No Render, abra o seu Web Service → aba **Shell**.
2. Rode:

```bash
python
>>> from app import app, db
>>> from models import Admin
>>> with app.app_context():
...     admin = Admin.query.filter_by(email="junior007eai@gmail.com").first()
...     admin.set_password("NOVA_SENHA_AQUI")
...     db.session.commit()
```

---

## Estrutura do projeto

```
ebook-store/
├── app.py                  # Aplicação Flask (rotas e lógica)
├── models.py                # Modelos do banco de dados (Admin e Ebook)
├── requirements.txt         # Dependências Python
├── render.yaml               # Configuração de deploy automático no Render
├── templates/                # Páginas HTML (Jinja2)
│   ├── base.html
│   ├── index.html             # Vitrine pública
│   ├── login.html             # Login do admin
│   ├── admin_dashboard.html   # Lista de ebooks (admin)
│   └── ebook_form.html        # Criar/editar ebook
└── static/
    ├── css/style.css
    └── uploads/               # Imagens enviadas por upload
```

## Tecnologias usadas

- **Flask** — framework web
- **Flask-SQLAlchemy** — ORM / banco de dados
- **Flask-Login** — autenticação do admin
- **PostgreSQL** (produção) / **SQLite** (desenvolvimento local)
- **Gunicorn** — servidor de produção

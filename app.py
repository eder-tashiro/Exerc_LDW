from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('padaria.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            descricao TEXT,
            imagem TEXT  -- Novo campo para armazenar o nome da imagem
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Função para verificar se o usuário está logado como admin
def admin_required(f):
    def wrap(*args, **kwargs):
        if 'admin' not in session:
            flash('Acesso restrito. Faça login como administrador.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__  # Necessário para não quebrar o decorador
    return wrap

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifique o login admin (aqui você pode implementar uma lógica mais robusta)
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            flash('Login bem-sucedido como administrador.')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logout realizado com sucesso.')
    return redirect(url_for('index'))

@app.route('/')
def index():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

@app.route('/create', methods=('GET', 'POST'))
@admin_required
def create():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        imagem = request.files['imagem']

        if not nome or not preco:
            flash('Nome e preço são obrigatórios')
        elif imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = get_db_connection()
            conn.execute('INSERT INTO produtos (nome, preco, descricao, imagem) VALUES (?, ?, ?, ?)',
                         (nome, float(preco), descricao, filename))
            conn.commit()
            conn.close()
            flash('Produto criado com sucesso')
            return redirect(url_for('create'))
        else:
            flash('Arquivo de imagem inválido')
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    
    return render_template('create.html', produtos=produtos)

@app.route('/update/<int:id>', methods=('GET', 'POST'))
@admin_required
def update(id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        imagem = request.files['imagem']

        if not nome or not preco:
            flash('Nome e preço são obrigatórios')
        else:
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                conn.execute('UPDATE produtos SET nome = ?, preco = ?, descricao = ?, imagem = ? WHERE id = ?',
                             (nome, float(preco), descricao, filename, id))
            else:
                conn.execute('UPDATE produtos SET nome = ?, preco = ?, descricao = ? WHERE id = ?',
                             (nome, float(preco), descricao, id))

            conn.commit()
            conn.close()
            flash('Produto atualizado com sucesso')
            return redirect(url_for('create'))
    conn.close()
    return render_template('update.html', produto=produto)

@app.route('/search', methods=['GET', ])
def search():
    termo = request.args.get('termo', '')
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos WHERE nome LIKE ?', ('%' + termo + '%',)).fetchall()
    conn.close()
    return render_template('search.html', produtos=produtos, termo=termo)

@app.route('/delete/<int:id>', methods=('POST', ))
@admin_required
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Produto deletado com sucesso')
    return redirect(url_for('create'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)

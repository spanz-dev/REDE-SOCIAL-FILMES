from flask import Flask, render_template, request, jsonify
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def conectar_banco():
    return psycopg2.connect(DATABASE_URL)


def criar_tabela():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    conexao.commit()
    cursor.close()
    conexao.close()


@app.route("/")
def login_page():
    return render_template("index2.html")


@app.route("/login")
def cadastro_page():
    return render_template("index.html")


@app.route("/api/cadastro", methods=["POST"])
def api_cadastro():
    usuario = request.form["usuario"]
    email = request.form["email"]
    senha = request.form["senha"]

    erros = []

    if usuario.strip() == "":
        erros.append("Usuario obrigatorio")

    if email.strip() == "":
        erros.append("E-mail obrigatorio")

    if "@" not in email:
        erros.append("E-mail invalido")

    if len(senha) < 6:
        erros.append("Senha precisa ter pelo menos 6 caracteres")

    if erros:
        return jsonify({"ok": False, "erros": erros}), 400

    senha_hash = generate_password_hash(senha)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO clientes (usuario, email, senha)
            VALUES (%s, %s, %s)
        """, (usuario, email, senha_hash))

        conexao.commit()
        cursor.close()
        conexao.close()

        return jsonify({"ok": True, "mensagem": "Cliente cadastrado com sucesso"})

    except psycopg2.errors.UniqueViolation:
        return jsonify({"ok": False, "erros": ["E-mail ja cadastrado"]}), 400


@app.route("/api/login", methods=["POST"])
def api_login():
    email = request.form["email"]
    senha = request.form["senha"]

    if email.strip() == "" or senha.strip() == "":
        return jsonify({"ok": False, "erros": ["Preencha email e senha"]}), 400

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, usuario, email, senha
        FROM clientes
        WHERE email = %s
    """, (email,))

    cliente = cursor.fetchone()

    cursor.close()
    conexao.close()

    if cliente is None:
        return jsonify({"ok": False, "erros": ["Email ou senha incorretos"]}), 401

    senha_hash = cliente[3]

    if not check_password_hash(senha_hash, senha):
        return jsonify({"ok": False, "erros": ["Email ou senha incorretos"]}), 401

    return jsonify({
        "ok": True,
        "mensagem": "Login feito com sucesso",
        "cliente": {
            "id": cliente[0],
            "usuario": cliente[1],
            "email": cliente[2]
        }
    })
@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, usuario, email
        FROM clientes
        ORDER BY id
    """)

    clientes = cursor.fetchall()

    cursor.close()
    conexao.close()

    lista = []

    for cliente in clientes:
        lista.append({
            "id": cliente[0],
            "usuario": cliente[1],
            "email": cliente[2]
        })

    return jsonify(lista)

if __name__ == "__main__":
    criar_tabela()
    app.run(debug=True)

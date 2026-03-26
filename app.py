from flask import Flask, render_template, request, redirect, session, url_for, flash
from banco import conectar, criar_tabelas

app = Flask(__name__)
app.secret_key = "chave_secreta_sistema"

criar_tabelas()

def usuario_logado():
    return "usuario" in session

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND senha = ?",
            (usuario, senha)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))
        else:
            flash("Usuário ou senha inválidos.")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM clientes")
    total_clientes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM agenda")
    total_agenda = cursor.fetchone()["total"]

    cursor.execute("SELECT IFNULL(SUM(valor), 0) as total FROM financeiro WHERE tipo = 'entrada'")
    entradas = cursor.fetchone()["total"]

    cursor.execute("SELECT IFNULL(SUM(valor), 0) as total FROM financeiro WHERE tipo = 'saida'")
    saidas = cursor.fetchone()["total"]

    saldo = entradas - saidas

    conn.close()

    return render_template(
        "dashboard.html",
        total_clientes=total_clientes,
        total_agenda=total_agenda,
        entradas=entradas,
        saidas=saidas,
        saldo=saldo
    )

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        empresa = request.form["empresa"]

        if nome.strip() == "":
            flash("O nome do cliente é obrigatório.")
            return redirect(url_for("clientes"))

        cursor.execute("""
            INSERT INTO clientes (nome, telefone, email, empresa)
            VALUES (?, ?, ?, ?)
        """, (nome, telefone, email, empresa))
        conn.commit()
        flash("Cliente cadastrado com sucesso.")
        conn.close()
        return redirect(url_for("clientes"))

    busca = request.args.get("busca", "").strip()

    if busca:
        cursor.execute("SELECT * FROM clientes WHERE nome LIKE ?", (f"%{busca}%",))
    else:
        cursor.execute("SELECT * FROM clientes ORDER BY id DESC")

    lista_clientes = cursor.fetchall()
    conn.close()

    return render_template("clientes.html", clientes=lista_clientes, busca=busca)

@app.route("/editar_cliente/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        empresa = request.form["empresa"]

        cursor.execute("""
            UPDATE clientes
            SET nome = ?, telefone = ?, email = ?, empresa = ?
            WHERE id = ?
        """, (nome, telefone, email, empresa, id))
        conn.commit()
        conn.close()
        flash("Cliente atualizado com sucesso.")
        return redirect(url_for("clientes"))

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    cliente = cursor.fetchone()
    conn.close()

    return render_template("editar_cliente.html", cliente=cliente)

@app.route("/excluir_cliente/<int:id>")
def excluir_cliente(id):
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Cliente excluído com sucesso.")
    return redirect(url_for("clientes"))

@app.route("/financeiro", methods=["GET", "POST"])
def financeiro():
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        tipo = request.form["tipo"]
        descricao = request.form["descricao"]
        valor = request.form["valor"]
        data = request.form["data"]

        try:
            valor = float(valor.replace(",", "."))
        except ValueError:
            flash("Valor inválido.")
            conn.close()
            return redirect(url_for("financeiro"))

        cursor.execute("""
            INSERT INTO financeiro (tipo, descricao, valor, data)
            VALUES (?, ?, ?, ?)
        """, (tipo, descricao, valor, data))
        conn.commit()
        flash("Movimentação cadastrada com sucesso.")
        conn.close()
        return redirect(url_for("financeiro"))

    cursor.execute("SELECT * FROM financeiro ORDER BY id DESC")
    movimentacoes = cursor.fetchall()

    cursor.execute("SELECT IFNULL(SUM(valor), 0) as total FROM financeiro WHERE tipo = 'entrada'")
    entradas = cursor.fetchone()["total"]

    cursor.execute("SELECT IFNULL(SUM(valor), 0) as total FROM financeiro WHERE tipo = 'saida'")
    saidas = cursor.fetchone()["total"]

    saldo = entradas - saidas

    conn.close()

    return render_template(
        "financeiro.html",
        movimentacoes=movimentacoes,
        entradas=entradas,
        saidas=saidas,
        saldo=saldo
    )

@app.route("/agenda", methods=["GET", "POST"])
def agenda():
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        cliente = request.form["cliente"]
        servico = request.form["servico"]
        data = request.form["data"]
        hora = request.form["hora"]

        cursor.execute("""
            INSERT INTO agenda (cliente, servico, data, hora)
            VALUES (?, ?, ?, ?)
        """, (cliente, servico, data, hora))
        conn.commit()
        flash("Agendamento salvo com sucesso.")
        conn.close()
        return redirect(url_for("agenda"))

    cursor.execute("SELECT * FROM agenda ORDER BY data, hora")
    compromissos = cursor.fetchall()
    conn.close()

    return render_template("agenda.html", compromissos=compromissos)

@app.route("/excluir_agenda/<int:id>")
def excluir_agenda(id):
    if not usuario_logado():
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agenda WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Agendamento excluído com sucesso.")
    return redirect(url_for("agenda"))

if __name__ == "__main__":
    app.run(debug=True)

import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "chave-secreta-projeto"

# CONEXÃO SQL - SQLite
engine = create_engine("sqlite:///chamados.db", future=True)

# CONEXÃO NoSQL - MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)

banco_mongo = mongo_client["sistema_suporte"]
historicos = banco_mongo["historicos"]


# CRIAÇÃO DAS TABELAS SQL
def inicializar_banco():
    with engine.begin() as conn:

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                categoria_id INTEGER NOT NULL,
                equipamento TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Aberto',
                criado_em TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            )
        """))

        categorias = ["Hardware", "Software", "Rede/Internet", "Outro"]

        for categoria in categorias:
            conn.execute(
                text("INSERT OR IGNORE INTO categorias (nome) VALUES (:nome)"),
                {"nome": categoria}
            )


# REGISTRAR HISTÓRICO NO MONGODB
def registrar_historico(chamado_id, responsavel, acao, observacoes):
    documento = {
        "chamado_id": int(chamado_id),
        "data": datetime.now().astimezone().isoformat(timespec="seconds"),
        "responsavel": responsavel,
        "acao": acao,
        "observacoes": observacoes
    }

    historicos.insert_one(documento)


# PÁGINA INICIAL - LISTAR CHAMADOS
@app.route("/")
def index():

    with engine.connect() as conn:
        chamados = conn.execute(text("""
            SELECT
                c.id,
                u.nome AS solicitante,
                c.equipamento,
                cat.nome AS categoria,
                c.descricao,
                c.status,
                c.criado_em
            FROM chamados c
            JOIN usuarios u ON u.id = c.usuario_id
            JOIN categorias cat ON cat.id = c.categoria_id
            ORDER BY c.id DESC
        """)).mappings().all()

    return render_template("index.html", chamados=chamados)


# CADASTRAR CHAMADO
@app.route("/novo", methods=["GET", "POST"])
def novo_chamado():

    if request.method == "POST":

        solicitante = request.form.get("solicitante", "").strip()
        equipamento = request.form.get("equipamento", "").strip()
        categoria_id = request.form.get("categoria_id", "").strip()
        descricao = request.form.get("descricao", "").strip()
        responsavel = request.form.get("responsavel", "").strip()

        if not all([solicitante, equipamento, categoria_id, descricao]):
            flash("Preencha todos os campos obrigatórios.", "erro")
            return redirect(url_for("novo_chamado"))

        with engine.begin() as conn:

            usuario = conn.execute(
                text("SELECT id FROM usuarios WHERE nome = :nome"),
                {"nome": solicitante}
            ).first()

            if usuario:
                usuario_id = usuario.id
            else:
                usuario_id = conn.execute(
                    text("INSERT INTO usuarios (nome) VALUES (:nome)"),
                    {"nome": solicitante}
                ).lastrowid

            chamado_id = conn.execute(text("""
                INSERT INTO chamados
                (usuario_id, categoria_id, equipamento, descricao, status, criado_em)
                VALUES
                (:usuario_id, :categoria_id, :equipamento, :descricao, 'Aberto', :criado_em)
            """), {
                "usuario_id": usuario_id,
                "categoria_id": int(categoria_id),
                "equipamento": equipamento,
                "descricao": descricao,
                "criado_em": datetime.now().astimezone().isoformat(timespec="seconds")
            }).lastrowid

        registrar_historico(
            chamado_id,
            responsavel or solicitante,
            "Chamado criado",
            f"Solicitação cadastrada. Equipamento: {equipamento}. Status inicial: Aberto."
        )

        flash("Chamado cadastrado com sucesso!", "sucesso")

        return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))

    with engine.connect() as conn:
        categorias = conn.execute(
            text("SELECT id, nome FROM categorias ORDER BY nome")
        ).mappings().all()

    return render_template("novo.html", categorias=categorias)


# VISUALIZAR DETALHES E HISTÓRICO
@app.route("/chamado/<int:chamado_id>")
def detalhe_chamado(chamado_id):

    with engine.connect() as conn:
        chamado = conn.execute(text("""
            SELECT c.*, u.nome AS solicitante, cat.nome AS categoria
            FROM chamados c
            JOIN usuarios u ON u.id = c.usuario_id
            JOIN categorias cat ON cat.id = c.categoria_id
            WHERE c.id = :id
        """), {"id": chamado_id}).mappings().first()

    if not chamado:
        flash("Chamado não encontrado.", "erro")
        return redirect(url_for("index"))

    historico = list(
        historicos.find(
            {"chamado_id": chamado_id},
            {"_id": 0}
        ).sort("_id", 1)
    )

    return render_template(
        "detalhe.html",
        chamado=chamado,
        historico=historico
    )


# ALTERAR STATUS DO CHAMADO
@app.route("/chamado/<int:chamado_id>/status", methods=["POST"])
def alterar_status(chamado_id):

    novo_status = request.form.get("status", "")
    responsavel = request.form.get("responsavel", "").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if novo_status not in ["Aberto", "Em andamento", "Concluído"]:
        flash("Status inválido.", "erro")
        return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))

    with engine.begin() as conn:
        resultado = conn.execute(
            text("UPDATE chamados SET status = :status WHERE id = :id"),
            {"status": novo_status, "id": chamado_id}
        )

        if resultado.rowcount == 0:
            flash("Chamado não encontrado.", "erro")
            return redirect(url_for("index"))

    registrar_historico(
        chamado_id,
        responsavel or "Equipe de suporte",
        "Status alterado",
        observacoes or f"Status alterado para {novo_status}."
    )

    flash("Status atualizado com sucesso!", "sucesso")

    return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))


# ADICIONAR COMENTÁRIO AO HISTÓRICO
@app.route("/chamado/<int:chamado_id>/comentario", methods=["POST"])
def adicionar_comentario(chamado_id):

    responsavel = request.form.get("responsavel", "").strip()
    comentario = request.form.get("comentario", "").strip()

    if not responsavel or not comentario:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))

    with engine.connect() as conn:
        existe = conn.execute(
            text("SELECT id FROM chamados WHERE id = :id"),
            {"id": chamado_id}
        ).first()

    if not existe:
        flash("Chamado não encontrado.", "erro")
        return redirect(url_for("index"))

    registrar_historico(
        chamado_id,
        responsavel,
        "Comentário",
        comentario
    )

    flash("Comentário adicionado ao histórico!", "sucesso")

    return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))


# INICIAR A APLICAÇÃO
if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)

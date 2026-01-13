from db_config import connect_db
from flask import jsonify, request, Blueprint

produto_bp = Blueprint("produto", __name__)

# Funções auxiliares
def get(tabela: str):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").execute()
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar dados: {str(e)}"}), 500


def get_por_id(tabela: str, id_valor: int):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").eq("id", id_valor).execute()
        if resposta.data:
            return jsonify(resposta.data[0]), 200
        return jsonify({"erro": "Registro não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# Rotas para Produtos (tabela produto)
@produto_bp.route("/produto", methods=["GET"])
def listar_produtos():
    return get("produto")


@produto_bp.route("/produto/<int:id>", methods=["GET"])
def obter_produto(id):
    return get_por_id("produto", id)


@produto_bp.route("/produto", methods=["POST"])
def criar_produto():
    try:
        data = request.get_json()
        nome = data.get("nome")
        preco = data.get("preco")

        if not nome or not preco:
            return jsonify({"erro": "Nome e preço são obrigatórios"}), 400

        supabase = connect_db()
        resposta = supabase.table("produto").insert({
            "nome": nome,
            "preco": float(preco)
        }).execute()

        return jsonify({"mensagem": "Produto criado", "data": resposta.data[0]}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    try:
        data = request.get_json()
        supabase = connect_db()
        resposta = supabase.table("produto").update(data).eq("id", id).execute()
        return jsonify({
            "mensagem": "Produto atualizado",
            "data": resposta.data[0]
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    try:
        supabase = connect_db()
        supabase.table("produto").delete().eq("id", id).execute()
        return jsonify({"mensagem": "Produto removido"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# Rotas para Produtos do Dia (tabela produto_dia)
@produto_bp.route("/produtos_dia", methods=["GET"])
def listar_produtos_dia():
    """Retorna todos os produtos da tabela produto_dia"""
    supabase = connect_db()
    try:
        supabase = connect_db()

        resposta = (
            supabase
            .table("produto")
            .select("id, nome, preco, qtd")
            .order("nome")
            .execute()
        )

        return jsonify(resposta.data or []), 200
    except Exception as e:
        print(f"Erro ao buscar produtos do dia: {str(e)}")  # Debug
        return jsonify({"erro": f"Erro ao buscar produtos do dia: {str(e)}"}), 500

def baixar_estoque_produto(nome_produto: str):
    supabase = connect_db()

    resp = (
        supabase
        .table("produto_dia")
        .select("id, qtd")
        .eq("nome", nome_produto)
        .limit(1)
        .execute()
    )

    if not resp.data:
        return False, "Produto não encontrado"

    produto = resp.data[0]
    qtd_atual = produto["qtd"]

    if qtd_atual <= 0:
        return False, "Produto esgotado"

    nova_qtd = qtd_atual - 1

    supabase.table("produto_dia").update({
        "qtd": nova_qtd
    }).eq("id", produto["id"]).execute()

    return True, nova_qtd



@produto_bp.route("/produto_dia", methods=["POST"])
def adicionar_produto_dia():
    supabase = connect_db()
    data = request.get_json()

    produto_id = data.get("produto_id")
    qtd = data.get("qtd")

    if not produto_id or not qtd or qtd <= 0:
        return jsonify({"erro": "Dados inválidos"}), 400

    try:
        # 1️⃣ Buscar estoque atual
        resp_produto = (
            supabase
            .table("produto")
            .select("qtd")
            .eq("id", produto_id)
            .limit(1)
            .execute()
        )

        if not resp_produto.data:
            return jsonify({"erro": "Produto não encontrado"}), 404

        estoque_atual = resp_produto.data[0]["qtd"]

        if qtd > estoque_atual:
            return jsonify({"erro": "Quantidade maior que o estoque"}), 400

        # 2️⃣ Inserir produto do dia
        supabase.table("produto_dia").insert({
            "produto_id": produto_id,
            "qtd": qtd
        }).execute()

        # 3️⃣ Atualizar estoque
        supabase.table("produto").update({
            "qtd": estoque_atual - qtd
        }).eq("id", produto_id).execute()

        return jsonify({"ok": True}), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto_dia/<int:id>", methods=["DELETE"])
def remover_produto_dia(id):
    try:
        supabase = connect_db()
        supabase.table("produto_dia").delete().eq("id", id).execute()
        return jsonify({"mensagem": "Produto removido do dia"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@produto_bp.route("/produto_cliente", methods=["POST"])
def criar_produto_cliente():
    data = request.get_json()

    if not data or "cliente" not in data or "produto" not in data:
        return jsonify({"erro": "cliente e produto são obrigatórios"}), 400

    supabase = connect_db()

    try:
        novo = {
            "cliente": data["cliente"],
            "produto": data["produto"]
        }

        resposta = supabase.table("produto_cliente").insert(novo).execute()

        return jsonify({
            "mensagem": "Registro criado com sucesso",
            "dados": resposta.data[0]
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@produto_bp.route("/produto_cliente", methods=["GET"])
def listar_produto_cliente():
    supabase = connect_db()
    try:
        resposta = supabase.table("produto_cliente").select("*").execute()
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto_cliente", methods=["DELETE"])
def deletar_produto_cliente():
    supabase = connect_db()
    try:
        resposta = supabase.table("produto_cliente").delete().neq("id", 0).execute()
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

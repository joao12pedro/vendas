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
            "preco": float(preco),
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
        resposta = supabase.table("produto_dia").select("*").execute()
        print(f"Produtos do dia encontrados: {len(resposta.data)}")  # Debug
        return jsonify(resposta.data), 200
    except Exception as e:
        print(f"Erro ao buscar produtos do dia: {str(e)}")  # Debug
        return jsonify({"erro": f"Erro ao buscar produtos do dia: {str(e)}"}), 500


@produto_bp.route("/produto_dia", methods=["POST"])
def adicionar_produto_dia():
    try:
        data = request.get_json()
        print("Recebido:", data)

        if not data or "produto_id" not in data:
            return jsonify({"erro": "produto_id é obrigatório"}), 400

        supabase = connect_db()

        # Verifica se o produto existe
        produto = supabase.table("produto").select("*").eq("id", data["produto_id"]).execute()
        if not produto.data:
            return jsonify({"erro": "Produto não encontrado"}), 404

        produto_info = produto.data[0]

        # Verifica se já está na lista do dia
        existente = supabase.table("produto_dia") \
            .select("*") \
            .eq("id", produto_info["id"]) \
            .execute()

        if existente.data:
            return jsonify({"erro": "Produto já está na lista do dia"}), 400

        # Adiciona à lista do dia
        resposta = supabase.table("produto_dia").insert({
            "id": produto_info["id"],
            "nome": produto_info["nome"],
            "preco": produto_info["preco"]
        }).execute()

        return jsonify({
            "mensagem": "Produto adicionado ao dia",
            "data": resposta.data[0]
        }), 201

    except Exception as e:
        print("Erro interno:", str(e))
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto_dia/<int:id>", methods=["DELETE"])
def remover_produto_dia(id):
    try:
        supabase = connect_db()
        supabase.table("produto_dia").delete().eq("id", id).execute()
        return jsonify({"mensagem": "Produto removido do dia"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
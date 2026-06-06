from flask import Blueprint, jsonify, request
from db_config import connect_db

produto_bp = Blueprint("produto", __name__)

# =====================================================
# 📌 PRODUTO (cadastro base)
# =====================================================

@produto_bp.route("/produto", methods=["GET"])
def listar_produtos():
    supabase = connect_db()
    try:
        resp = supabase.table("produto").select("*").execute()
        return jsonify(resp.data or []), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto", methods=["POST"])
def criar_produto():
    data = request.get_json()

    nome = data.get("nome")
    preco = data.get("preco")

    if not nome or preco is None:
        return jsonify({"erro": "Nome e preço são obrigatórios"}), 400

    supabase = connect_db()

    try:
        resp = supabase.table("produto").insert({
            "nome": nome,
            "preco": float(preco)
        }).execute()

        return jsonify(resp.data[0]), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    supabase = connect_db()
    try:
        supabase.table("produto").delete().eq("id", id).execute()
        return jsonify({"mensagem": "Produto removido"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto_cliente/<int:id>", methods=["DELETE"])
def deletar_produto_cliente(id):
    supabase = connect_db()

    try:
        # Tenta deletar o produto pelo ID
        response = supabase.table("produto_cliente").delete().eq("id", id).execute()

        # Verifica se algum registro foi deletado
        if response.data:
            return jsonify({
                "mensagem": f"Produto {id} excluído com sucesso",
                "deletado": True
            }), 200
        else:
            return jsonify({
                "erro": f"Produto com ID {id} não encontrado",
                "deletado": False
            }), 404

    except Exception as e:
        return jsonify({
            "erro": f"Erro ao excluir produto: {str(e)}",
            "deletado": False
        }), 500


# =====================================================
# 📌 PRODUTO DO DIA (com quantidade)
# =====================================================

@produto_bp.route("/produto_dia", methods=["GET"])
def listar_produtos_dia():
    supabase = connect_db()
    try:
        resp = supabase.table("produto_dia") \
            .select("id, nome, preco, qtd") \
            .order("nome") \
            .execute()

        return jsonify(resp.data or []), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto_dia", methods=["POST"])
def adicionar_produto_dia():
    data = request.get_json()

    nome = data.get("nome")
    preco = data.get("preco")
    qtd = data.get("qtd")

    if not nome or preco is None or not qtd or int(qtd) <= 0:
        return jsonify({"erro": "Dados inválidos"}), 400

    supabase = connect_db()

    try:
        # verifica se o produto já está no dia
        existente = supabase.table("produto_dia") \
            .select("id, qtd") \
            .eq("nome", nome) \
            .execute()

        if existente.data:
            nova_qtd = existente.data[0]["qtd"] + int(qtd)

            supabase.table("produto_dia").update({
                "qtd": nova_qtd
            }).eq("id", existente.data[0]["id"]).execute()
        else:
            supabase.table("produto_dia").insert({
                "nome": nome,
                "preco": float(preco),
                "qtd": int(qtd)
            }).execute()

        return jsonify({"mensagem": "Produto adicionado ao dia"}), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produto_dia/<int:id>", methods=["DELETE"])
def remover_produto_dia(id):
    supabase = connect_db()
    try:
        supabase.table("produto_dia").delete().eq("id", id).execute()
        return jsonify({"mensagem": "Produto do dia removido"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =====================================================
# 🔻 FUNÇÃO AUXILIAR — BAIXAR QUANTIDADE
# =====================================================

def baixar_estoque_produto(nome_produto, quantidade=1):
    supabase = connect_db()

    resp = supabase.table("produto_dia") \
        .select("id, qtd") \
        .eq("nome", nome_produto) \
        .execute()

    if not resp.data:
        return False, "Produto não encontrado no dia"

    produto = resp.data[0]

    if produto["qtd"] < quantidade:
        return False, "Quantidade insuficiente"

    nova_qtd = produto["qtd"] - quantidade

    supabase.table("produto_dia").update({
        "qtd": nova_qtd
    }).eq("id", produto["id"]).execute()

    return True, nova_qtd

@produto_bp.route("/produtos_cliente", methods=["GET"])
def listar_produtos_cliente():
    supabase = connect_db()

    try:
        resp = supabase.table("produto_cliente") \
            .select("*") \
            .order("cliente") \
            .execute()

        return jsonify(resp.data or []), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@produto_bp.route("/produtos_cliente", methods=["POST"])
def criar_produto_cliente():
    data = request.get_json()

    cliente = data.get("cliente")
    produto = data.get("produto")
    qtd = data.get("qtd")
    horario = data.get("horario")

    if not cliente or not produto:
        return jsonify({"erro": "Cliente e produto são obrigatórios"}), 400

    supabase = connect_db()

    try:
        resp = supabase.table("produto_cliente").insert({
            "cliente": cliente,
            "produto": produto,
            "qtd": qtd,
            "horario": horario
        }).execute()

        return jsonify({
            "mensagem": "Registro criado com sucesso",
            "dados": resp.data[0]
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@produto_bp.route("/produto/deletar", methods=["DELETE"])
def deletar_produtos():
    supabase = connect_db()

    try:
        supabase.table("produto_cliente") \
            .delete() \
            .neq("id", 0) \
            .execute()

        return jsonify({"mensagem": "Pedidos finalizados removidos com sucesso"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@produto_bp.route("/produtos_cliente/filtrar", methods=["GET"])
def filtrar_pedidos_finalizados_por_nome():
    supabase = connect_db()

    nome = request.args.get("nome")

    if not nome:
        return jsonify({"erro": "Nome do cliente não informado"}), 400

    try:
        response = supabase.table("produto_cliente") \
            .select("*") \
            .ilike("cliente", f"%{nome}%") \
            .execute()

        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

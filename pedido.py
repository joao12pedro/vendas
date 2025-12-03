from datetime import datetime
from flask import jsonify, request, Blueprint
from db_config import connect_db

pedido_bp = Blueprint("pedido", __name__)

# -------------------------------------------------------------
# 🔧 Função auxiliar para buscar registros
# -------------------------------------------------------------
def get(tabela: str):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").execute()

        if not resposta.data:
            return []

        return resposta.data

    except Exception as e:
        print(f"Erro ao buscar dados da tabela '{tabela}': {e}")
        return []


# -------------------------------------------------------------
# 📌 GET /pedido — LISTAR PEDIDOS ABERTOS
# -------------------------------------------------------------
@pedido_bp.route("/pedido", methods=["GET"])
def listar_pedidos_abertos():
    try:
        pedidos = get("pedido")
        return jsonify(pedidos), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 GET /pedido/<id> — BUSCAR POR ID
# -------------------------------------------------------------
@pedido_bp.route("/pedido/<int:id>", methods=["GET"])
def obter_pedido_por_id(id):
    supabase = connect_db()
    try:
        resposta = supabase.table("pedido").select("*").eq("id", id).execute()
        if resposta.data:
            return jsonify(resposta.data[0]), 200
        return jsonify({"erro": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 POST /pedido — CRIAR NOVO PEDIDO
# -------------------------------------------------------------
@pedido_bp.route("/pedido", methods=["POST"])
def criar_pedido():
    data = request.get_json()

    if not data or "nome_cliente" not in data:
        return jsonify({"erro": "O nome do cliente é obrigatório"}), 400

    supabase = connect_db()

    try:
        novo = {
            "nome_cliente": data["nome_cliente"],
            "valor_total": 0.00,
            "data_pedido": datetime.now().strftime("%Y-%m-%d")
        }

        resposta = supabase.table("pedido").insert(novo).execute()

        return jsonify({
            "mensagem": "Pedido criado com sucesso",
            "dados": resposta.data[0]
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 POST /adicionar — ADICIONAR ITEM AO PEDIDO
# -------------------------------------------------------------
@pedido_bp.route("/adicionar", methods=['POST'])
def adicionar_item_pedido():
    data = request.get_json()

    campos = ["pedido_id", "nome_produto"]
    if not all(c in data for c in campos):
        return jsonify({"erro": "pedido_id e nome_produto são obrigatórios"}), 400

    pedido_id = data["pedido_id"]
    nome_produto = data["nome_produto"]
    quantidade = data.get("quantidade", 1)

    supabase = connect_db()

    try:
        # Verifica pedido
        pedido = supabase.table("pedido").select("*").eq("id", pedido_id).execute()
        if not pedido.data:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        # Busca produto no produto_dia
        produto = (
            supabase.table("produto_dia")
            .select("*")
            .ilike("nome", f"%{nome_produto}%")
            .execute()
        )

        if not produto.data:
            return jsonify({"erro": f"Produto '{nome_produto}' não encontrado"}), 404

        produto = produto.data[0]

        preco_unit = produto["preco"]

        # Inserir item
        novo_item = {
            "pedido_id": pedido_id,
            "produto_id": produto["id"],
            "quantidade": quantidade,
            "preco_unitario": preco_unit
        }

        item = supabase.table("itens_pedido").insert(novo_item).execute()

        # Atualizar valor total
        subtotal = preco_unit * quantidade
        novo_total = pedido.data[0]["valor_total"] + subtotal

        supabase.table("pedido").update({
            "valor_total": novo_total
        }).eq("id", pedido_id).execute()

        return jsonify({
            "mensagem": "Item adicionado com sucesso",
            "item": item.data[0],
            "subtotal": subtotal
        }), 201

    except Exception as e:
        if "duplicate key" in str(e).lower():
            return jsonify({"erro": "Este produto já foi adicionado ao pedido"}), 409
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 PUT /pedido/<id> — ATUALIZAR PEDIDO
# -------------------------------------------------------------
@pedido_bp.route("/pedido/<int:id>", methods=['PUT'])
def atualizar_pedido(id):
    data = request.get_json()

    campos = ["valor_total", "nome_cliente"]
    dados = {c: data[c] for c in campos if c in data}

    if not dados:
        return jsonify({"erro": "Nenhum campo válido enviado"}), 400

    supabase = connect_db()

    try:
        pedido = supabase.table("pedido").select("*").eq("id", id).execute()
        if not pedido.data:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        resposta = supabase.table("pedido").update(dados).eq("id", id).execute()

        return jsonify({
            "mensagem": "Pedido atualizado",
            "dados": resposta.data[0]
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 PUT /finalizar_pedido/<id> — MOVER PARA pedidos_finalizados
# -------------------------------------------------------------
@pedido_bp.route("/finalizar_pedido/<int:id>", methods=['PUT'])
def finalizar_pedido(id):
    try:
        supabase = connect_db()

        pedido = supabase.table("pedido").select("*").eq("id", id).execute()
        if not pedido.data:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        pedido = pedido.data[0]

        # Inserir no pedidos_finalizados
        registro = {
            "nome_cliente": pedido["nome_cliente"],
            "valor_total": pedido["valor_total"],
            "data_pedido": pedido["data_pedido"]
        }

        supabase.table("pedidos_finalizados").insert(registro).execute()

        # Remover itens
        supabase.table("itens_pedido").delete().eq("pedido_id", id).execute()

        # Remover pedido aberto
        supabase.table("pedido").delete().eq("id", id).execute()

        return jsonify({"mensagem": "Pedido finalizado com sucesso"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 DELETE /pedido/<id> — EXCLUIR PEDIDO ABERTO
# -------------------------------------------------------------
@pedido_bp.route("/pedido/<int:id>", methods=["DELETE"])
def excluir_pedido(id):
    supabase = connect_db()
    try:
        pedido = supabase.table("pedido").select("*").eq("id", id).execute()
        if not pedido.data:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        supabase.table("itens_pedido").delete().eq("pedido_id", id).execute()
        supabase.table("pedido").delete().eq("id", id).execute()

        return jsonify({"mensagem": "Pedido excluído"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 DELETE /deletar_pedidos_por_data — INTERVALO DE DATAS
# -------------------------------------------------------------
@pedido_bp.route("/deletar_pedidos_por_data", methods=["DELETE"])
def deletar_pedidos_por_data():
    data = request.get_json()
    di = data.get("data_inicio")
    df = data.get("data_fim")

    if not di or not df:
        return jsonify({"erro": "Envie data_inicio e data_fim"}), 400

    supabase = connect_db()

    try:
        pedidos = (
            supabase.table("pedido")
            .select("id")
            .gte("data_pedido", di)
            .lte("data_pedido", df)
            .execute()
        ).data

        if not pedidos:
            return jsonify({"mensagem": "Nenhum pedido no intervalo"}), 404

        ids = [p["id"] for p in pedidos]

        supabase.table("itens_pedido").delete().in_("pedido_id", ids).execute()
        supabase.table("pedido").delete().in_("id", ids).execute()

        return jsonify({
            "mensagem": f"{len(ids)} pedidos deletados",
            "ids": ids
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 GET /pedidos_finalizados
# -------------------------------------------------------------
@pedido_bp.route("/pedidos_finalizados", methods=["GET"])
def listar_pedidos_finalizados():
    return jsonify(get("pedidos_finalizados")), 200

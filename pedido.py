from datetime import datetime
from flask import jsonify, request, Blueprint
from db_config import connect_db
from produto import baixar_estoque_produto
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

@pedido_bp.route("/pedido/pesquisar", methods=["GET"])
def pesquisar_pedido_por_nome():
    nome = request.args.get("nome")

    if not nome:
        return jsonify({"erro": "Nome não informado"}), 400

    supabase = connect_db()

    try:
        resposta = (
            supabase
            .table("pedido")
            .select("*")
            .ilike("nome_cliente", f"%{nome}%")
            .execute()
        )

        if not resposta.data:
            return jsonify([]), 200

        return jsonify(resposta.data), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# -------------------------------------------------------------
# 📌 POST /pedido — CRIAR NOVO PEDIDO
# -------------------------------------------------------------
@pedido_bp.route("/pedido", methods=["POST"])
def criar_pedido():
    data = request.get_json()

    # ===== VALIDACOES =====
    if not data:
        return jsonify({"erro": "JSON inválido"}), 400

    nome_cliente = data.get("nome_cliente")
    produtos = data.get("produtos")

    if not nome_cliente:
        return jsonify({"erro": "Nome do cliente é obrigatório"}), 400

    if not produtos or not isinstance(produtos, list):
        return jsonify({"erro": "Pedido sem produtos"}), 400

    supabase = connect_db()

    try:
        # ===== CRIA PEDIDO =====
        pedido = supabase.table("pedido").insert({
            "nome_cliente": nome_cliente,
            "valor_total": 0,
            "status": "aberto",
            "data_pedido": datetime.now().strftime("%Y-%m-%d")
        }).execute()

        pedido_id = pedido.data[0]["id"]
        valor_total = 0

        # ===== PROCESSA PRODUTOS =====
        for item in produtos:
            nome_produto = item.get("nome")
            quantidade = int(item.get("quantidade", 1))

            if not nome_produto or quantidade <= 0:
                continue

            # 🔴 BAIXA ESTOQUE
            ok, resultado = baixar_estoque_produto(
                nome_produto, quantidade
            )

            if not ok:
                return jsonify({
                    "erro": f"Estoque insuficiente: {nome_produto}"
                }), 400

            # 🔹 BUSCA PRECO
            prod = supabase.table("produto") \
                .select("preco") \
                .eq("nome", nome_produto) \
                .single() \
                .execute()

            preco = float(prod.data["preco"])
            subtotal = preco * quantidade
            valor_total += subtotal

            # ✅ INSERE ITEM
            supabase.table("pedido_item").insert({
                "pedido_id": pedido_id,
                "produto": nome_produto,
                "quantidade": quantidade,
                "preco_unitario": preco,
                "subtotal": subtotal
            }).execute()

        # ===== ATUALIZA PEDIDO =====
        supabase.table("pedido").update({
            "valor_total": valor_total,
            "status": "finalizado"
        }).eq("id", pedido_id).execute()

        return jsonify({
            "mensagem": "Pedido criado com sucesso",
            "dados": {
                "id": pedido_id,
                "cliente": nome_cliente,
                "valor_total": valor_total
            }
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# -------------------------------------------------------------
# 📌 POST /adicionar — ADICIONAR ITEM AO PEDIDO
# -------------------------------------------------------------
@pedido_bp.route("/adicionar", methods=["POST"])
def adicionar_produto():
    data = request.get_json()

    pedido_id = data.get("pedido_id")
    nome_produto = data.get("nome_produto")
    quantidade = data.get("quantidade", 1)

    if not pedido_id or not nome_produto:
        return jsonify({"erro": "Dados inválidos"}), 400

    # 🔴 BAIXA ESTOQUE PRIMEIRO
    ok, resultado = baixar_estoque_produto(nome_produto)

    if not ok:
        return jsonify({"erro": resultado}), 400

    # ✅ ADICIONA ITEM AO PEDIDO
    supabase = connect_db()
    resp = supabase.table("pedido_item").insert({
        "pedido_id": pedido_id,
        "produto": nome_produto,
        "quantidade": quantidade
    }).execute()

    itens = supabase.table("pedido_item") \
        .select("id") \
        .eq("pedido_id", id) \
        .execute()

    if not itens.data:
        return jsonify({"erro": "Pedido sem itens"}), 400

    supabase.table("pedido").update({
        "status": "finalizado"
    }).eq("id", id).execute()

    return jsonify({
        "mensagem": "Produto adicionado",
        "estoque_restante": resultado,
        "item": resp.data[0]
    }), 201

@pedido_bp.route("/pedido/<int:id>", methods=["POST"])
def finalizar_pedido(id):
    supabase = connect_db()

    itens = supabase.table("pedido_item") \
        .select("id") \
        .eq("pedido_id", id) \
        .execute()

    if not itens.data:
        return jsonify({"erro": "Pedido sem itens"}), 400

    supabase.table("pedido").update({
        "status": "finalizado"
    }).eq("id", id).execute()

    return jsonify({"ok": True})


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




@pedido_bp.route("/pedido/limpar", methods=["DELETE"])
def limpar_pedidos_finalizados():
    try:
        supabase = connect_db()

        # Deleta TODOS os registros da tabela
        supabase.table("pedidos_finalizados").delete().neq("id", 0).execute()

        return jsonify({"mensagem": "Todos os registros foram removidos"}), 200

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

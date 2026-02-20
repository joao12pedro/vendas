from flask import Blueprint, request, jsonify
from datetime import date
from db_config import connect_db

pedido_bp = Blueprint("pedido", __name__)


# --------------------------------------------------
# 📌 POST /pedido — CRIAR PEDIDO (FINAL)
# --------------------------------------------------
@pedido_bp.route("/pedido", methods=["POST"])
def criar_pedido():
    data = request.get_json()

    nome_cliente = data.get("nome_cliente")
    produtos = data.get("produtos")

    if not nome_cliente:
        return jsonify({"erro": "Nome do cliente obrigatório"}), 400

    if not produtos or not isinstance(produtos, list):
        return jsonify({"erro": "Pedido sem produtos"}), 400

    supabase = connect_db()
    valor_total = 0.0

    try:
        # 🔹 CRIA PEDIDO
        pedido = supabase.table("pedido").insert({
            "nome_cliente": nome_cliente,
            "valor_total": 0.00,
            "data_pedido": date.today().isoformat()
        }).execute()

        pedido_id = pedido.data[0]["id"]

        itens = []
        valor_total_calculado = 0.0

        # 🔹 PROCESSA PRODUTOS
        for item in produtos:
            produto_id = item.get("produto_id")
            quantidade = float(item.get("quantidade", 1))

            if not produto_id or quantidade <= 0:
                continue

            prod_dia = (
                supabase
                .table("produto_dia")
                .select("*")
                .eq("id", produto_id)
                .single()
                .execute()
            )

            if not prod_dia.data:
                return jsonify({"erro": "Produto não encontrado"}), 400

            if prod_dia.data["qtd"] < quantidade:
                return jsonify({
                    "erro": f"Estoque insuficiente: {prod_dia.data['nome']}"
                }), 400

            preco = float(prod_dia.data["preco"])
            subtotal = round(preco * quantidade, 2)
            valor_total_calculado = round(valor_total_calculado + subtotal, 2)

            # 🔥 IMPORTANTE: NÃO incluir 'subtotal' aqui!
            itens.append({
                "pedido_id": pedido_id,
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": preco
                # NÃO ADICIONE 'subtotal' - essa coluna não existe!
            })

            # 🔻 BAIXA ESTOQUE
            supabase.table("produto_dia").update({
                "qtd": prod_dia.data["qtd"] - quantidade
            }).eq("id", produto_id).execute()

        if not itens:
            return jsonify({"erro": "Pedido sem itens válidos"}), 400

        # 🔹 INSERE ITENS (sem a coluna subtotal)
        supabase.table("itens_pedido").insert(itens).execute()

        # 🔹 ATUALIZA TOTAL
        supabase.table("pedido").update({
            "valor_total": valor_total_calculado
        }).eq("id", pedido_id).execute()

        # 🔹 INSERE NA TABELA produto_cliente
        for item in produtos:
            produto_id = item.get("produto_id")
            quantidade = float(item.get("quantidade", 1))

            # Busca o nome do produto
            prod_dia = (
                supabase
                .table("produto_dia")
                .select("nome")
                .eq("id", produto_id)
                .single()
                .execute()
            )

            if prod_dia.data:
                supabase.table("produto_cliente").insert({
                    "cliente": nome_cliente,
                    "produto": prod_dia.data["nome"],
                    "qtd": quantidade
                }).execute()

        return jsonify({
            "mensagem": "Pedido criado com sucesso",
            "pedido_id": pedido_id,
            "valor_total": valor_total_calculado,
            "itens": len(itens)
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
# --------------------------------------------------
# 📌 GET /pedido — LISTAR PEDIDOS
# --------------------------------------------------
@pedido_bp.route("/pedidos", methods=["GET"])
def listar_pedidos():
    supabase = connect_db()
    pedidos = supabase.table("pedido").select("*").execute()
    return jsonify(pedidos.data or []), 200


# --------------------------------------------------
# 📌 GET /pedidos_finalizados
# --------------------------------------------------
@pedido_bp.route("/pedidos_finalizados", methods=["GET"])
def listar_finalizados():
    supabase = connect_db()
    dados = supabase.table("pedidos_finalizados").select("*").execute()
    return jsonify(dados.data or []), 200

@pedido_bp.route("/pedidos_finalizados", methods=["POST"])
def criar_pedido_finalizado():
    data = request.get_json()

    nome_cliente = data.get("nome_cliente")
    valor_total = data.get("valor_total")

    # Validação
    if not nome_cliente or valor_total is None:
        return jsonify({"erro": "Nome do cliente e valor total são obrigatórios"}), 400

    supabase = connect_db()

    try:
        resp = supabase.table("pedidos_finalizados").insert({
            "nome_cliente": nome_cliente,
            "valor_total": float(valor_total),
            "data_pedido": date.today().isoformat()
        }).execute()

        return jsonify({
            "mensagem": "Pedido finalizado registrado com sucesso",
            "dados": resp.data[0]
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@pedido_bp.route("/pedido/<int:id>", methods=["DELETE"])
def deletar_pedido(id):
    supabase = connect_db()

    try:
        supabase.table("itens_pedido").delete().eq("pedido_id", id).execute()
        supabase.table("pedido").delete().eq("id", id).execute()
        return jsonify({"mensagem": "Pedido removido com sucesso"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
@pedido_bp.route("/pedido/<int:id>/finalizar", methods=["POST"])
def finalizar_pedido(id):
    supabase = connect_db()

    try:
        # 1️⃣ Buscar pedido
        pedido = (
            supabase
            .table("pedido")
            .select("*")
            .eq("id", id)
            .single()
            .execute()
        )

        if not pedido.data:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        p = pedido.data

        # 2️⃣ Criar em pedidos_finalizados
        supabase.table("pedidos_finalizados").insert({
            "nome_cliente": p["nome_cliente"],
            "valor_total": p["valor_total"],
            "data_pedido": p["data_pedido"]
        }).execute()

        # 3️⃣ Deletar ITENS do pedido
        supabase.table("itens_pedido") \
            .delete() \
            .eq("pedido_id", id) \
            .execute()

        # 4️⃣ Deletar pedido
        supabase.table("pedido") \
            .delete() \
            .eq("id", id) \
            .execute()

        return jsonify({"mensagem": "Pedido finalizado com sucesso"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedido/deletar", methods=["DELETE"])
def deletar_pedidos():
    supabase = connect_db()

    try:
        supabase.table("pedidos_finalizados") \
            .delete() \
            .neq("id", 0) \
            .execute()

        return jsonify({"mensagem": "Pedidos finalizados removidos com sucesso"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@pedido_bp.route("/pedidos_finalizados/filtrar", methods=["GET"])
def filtrar_pedidos_finalizados_por_nome():
    supabase = connect_db()

    nome = request.args.get("nome")

    if not nome:
        return jsonify({"erro": "Nome do cliente não informado"}), 400

    try:
        response = supabase.table("pedidos_finalizados") \
            .select("*") \
            .ilike("nome_cliente", f"%{nome}%") \
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@pedido_bp.route("/pedidos/filtrar", methods=["GET"])
def filtrar_pedidos_por_nome():
    supabase = connect_db()

    nome = request.args.get("nome")

    if not nome:
        return jsonify({"erro": "Nome do cliente não informado"}), 400

    try:
        response = supabase.table("pedido") \
            .select("*") \
            .ilike("nome_cliente", f"%{nome}%") \
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


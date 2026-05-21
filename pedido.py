# pedido.py
from flask import Blueprint, request, jsonify
from datetime import date, datetime
from db_config import connect_db

pedido_bp = Blueprint('pedido', __name__)


# ===== FUNÇÕES AUXILIARES =====

def calcular_preco_coxa_sobrecoxa(pares):
    """
    Calcula o preço da Coxa/Sobrecoxa baseado na quantidade de pares
    Tabela de preços:
    1 par = R$ 10
    2 pares = R$ 20
    3 pares = R$ 25
    4 pares = R$ 35
    5 pares = R$ 40
    6 pares = R$ 50
    A partir de 7 pares = preço do par anterior (6 pares = R$ 50) + R$ 10 por par adicional
    """
    if pares <= 0:
        return 0

    if pares == 1:
        return 10.00
    elif pares == 2:
        return 20.00
    elif pares == 3:
        return 25.00
    elif pares == 4:
        return 35.00
    elif pares == 5:
        return 40.00
    elif pares == 6:
        return 50.00
    elif pares >= 7:
        pares_adicionais = pares - 6
        return 50.00 + (pares_adicionais * 10)


def is_coxa_sobrecoxa(nome_produto):
    """Verifica se o produto é Coxa/Sobrecoxa"""
    if not nome_produto:
        return False
    nome = nome_produto.lower()
    return 'coxa' in nome and 'sobrecoxa' in nome


def obter_horario_atual():
    """Retorna o horário atual no formato TIME (HH:MM:SS)"""
    return datetime.now().time().isoformat()


# ===== ROTAS DE PEDIDOS =====

@pedido_bp.route("/pedido", methods=["POST"])
def criar_pedido():
    """
    Cria um novo pedido
    Espera JSON: {
        "nome_cliente": "NOME",
        "horario": "HH:MM:SS",  # OPCIONAL - se não enviar, usa o atual
        "produtos": [
            {"produto_id": 1, "quantidade": 2},
            ...
        ]
    }
    """
    data = request.get_json()

    nome_cliente = data.get("nome_cliente")
    produtos = data.get("produtos")

    # 🔥 PEGA O HORÁRIO DO JSON OU USA O ATUAL
    horario = data.get("horario")
    if not horario:
        horario = obter_horario_atual()
        print(f"⏰ Horário não enviado, usando atual: {horario}")

    if not nome_cliente:
        return jsonify({"erro": "Nome do cliente obrigatório"}), 400

    if not produtos or not isinstance(produtos, list):
        return jsonify({"erro": "Pedido sem produtos"}), 400

    supabase = connect_db()
    valor_total = 0

    try:
        # 🔹 CRIA PEDIDO (COM HORÁRIO)
        pedido = supabase.table("pedido").insert({
            "nome_cliente": nome_cliente,
            "valor_total": 0.00,
            "data_pedido": date.today().isoformat(),
            "horario": horario  # 🔥 ADICIONADO O HORÁRIO
        }).execute()

        if not pedido.data:
            return jsonify({"erro": "Erro ao criar pedido"}), 500

        pedido_id = pedido.data[0]["id"]
        itens = []
        produtos_cliente = []

        print(f"📦 Criando pedido #{pedido_id} para {nome_cliente} às {horario}")

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
                return jsonify({"erro": f"Produto ID {produto_id} não encontrado"}), 400

            if prod_dia.data["qtd"] < quantidade:
                return jsonify({
                    "erro": f"Estoque insuficiente: {prod_dia.data['nome']}"
                }), 400

            nome_produto = prod_dia.data["nome"]

            if is_coxa_sobrecoxa(nome_produto):
                pares = quantidade
                subtotal = calcular_preco_coxa_sobrecoxa(pares)
                print(f"🔥 Coxa/Sobrecoxa: {pares} pares = R$ {subtotal}")
            else:
                preco = float(prod_dia.data["preco"])
                subtotal = preco * quantidade

            valor_total += subtotal

            itens.append({
                "pedido_id": pedido_id,
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": prod_dia.data["preco"] if not is_coxa_sobrecoxa(nome_produto) else 0
            })

            produtos_cliente.append({
                "cliente": nome_cliente,
                "produto": nome_produto,
                "qtd": quantidade
            })

            supabase.table("produto_dia").update({
                "qtd": prod_dia.data["qtd"] - quantidade
            }).eq("id", produto_id).execute()

        if not itens:
            return jsonify({"erro": "Pedido sem itens válidos"}), 400

        supabase.table("itens_pedido").insert(itens).execute()

        # Agrupa produtos do cliente
        produtos_agrupados = {}
        for pc in produtos_cliente:
            chave = f"{pc['cliente']}|{pc['produto']}"
            if chave in produtos_agrupados:
                produtos_agrupados[chave]["qtd"] += pc["qtd"]
            else:
                produtos_agrupados[chave] = pc

        for pc in produtos_agrupados.values():
            supabase.table("produto_cliente").insert(pc).execute()

        # Atualiza total do pedido
        supabase.table("pedido").update({
            "valor_total": valor_total
        }).eq("id", pedido_id).execute()

        return jsonify({
            "mensagem": "Pedido criado com sucesso",
            "pedido_id": pedido_id,
            "valor_total": valor_total,
            "horario": horario
        }), 201

    except Exception as e:
        print(f"Erro ao criar pedido: {str(e)}")
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_pedidos_abertos():
    """Lista apenas pedidos ABERTOS (sem data_finalizacao)"""
    try:
        supabase = connect_db()
        response = supabase.table("pedido").select("*").is_("data_finalizacao", "null").execute()
        print(f"📋 Pedidos abertos encontrados: {len(response.data)}")
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedidos_finalizados", methods=["GET"])
def listar_pedidos_finalizados():
    """Lista apenas pedidos FINALIZADOS (com data_finalizacao)"""
    try:
        supabase = connect_db()
        response = supabase.table("pedido").select("*").not_.is_("data_finalizacao", "null").execute()
        print(f"📋 Pedidos finalizados encontrados: {len(response.data)}")
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedidos/filtrar", methods=["GET"])
def filtrar_pedidos_abertos():
    """Filtra pedidos abertos por nome do cliente"""
    nome = request.args.get("nome", "").upper()
    if not nome:
        return jsonify({"erro": "Nome não fornecido"}), 400

    try:
        supabase = connect_db()
        response = supabase.table("pedido") \
            .select("*") \
            .is_("data_finalizacao", "null") \
            .ilike("nome_cliente", f"%{nome}%") \
            .execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedidos_finalizados/filtrar", methods=["GET"])
def filtrar_pedidos_finalizados():
    """Filtra pedidos finalizados por nome do cliente"""
    nome = request.args.get("nome", "").upper()
    if not nome:
        return jsonify({"erro": "Nome não fornecido"}), 400

    try:
        supabase = connect_db()
        response = supabase.table("pedido") \
            .select("*") \
            .not_.is_("data_finalizacao", "null") \
            .ilike("nome_cliente", f"%{nome}%") \
            .execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedido/<int:id>/finalizar", methods=["POST"])
def finalizar_pedido(id):
    """Finaliza um pedido (adiciona data de finalização)"""
    data = request.get_json()
    data_finalizacao = data.get("data_finalizacao", date.today().isoformat())

    try:
        supabase = connect_db()
        response = supabase.table("pedido") \
            .update({"data_finalizacao": data_finalizacao}) \
            .eq("id", id) \
            .execute()

        if response.data:
            print(f"✅ Pedido {id} finalizado em {data_finalizacao}")
            return jsonify({"mensagem": "Pedido finalizado com sucesso"}), 200
        else:
            return jsonify({"erro": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedido/<int:id>", methods=["DELETE"])
def deletar_pedido(id):
    """Deleta um pedido e seus itens"""
    try:
        supabase = connect_db()
        supabase.table("itens_pedido").delete().eq("pedido_id", id).execute()
        response = supabase.table("pedido").delete().eq("id", id).execute()

        if response.data:
            print(f"🗑️ Pedido {id} deletado")
            return jsonify({"mensagem": "Pedido deletado com sucesso"}), 200
        else:
            return jsonify({"erro": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/pedido/deletar", methods=["DELETE"])
def deletar_todos_pedidos_finalizados():
    """Deleta todos os pedidos finalizados"""
    try:
        supabase = connect_db()

        # Busca IDs dos pedidos finalizados
        pedidos = supabase.table("pedido") \
            .select("id") \
            .not_.is_("data_finalizacao", "null") \
            .execute()

        ids = [p["id"] for p in pedidos.data]

        if ids:
            # Deleta itens dos pedidos
            supabase.table("itens_pedido").delete().in_("pedido_id", ids).execute()

            # Deleta pedidos
            supabase.table("pedido").delete().in_("id", ids).execute()

        print(f"🗑️ {len(ids)} pedidos finalizados deletados")
        return jsonify({"mensagem": f"{len(ids)} pedidos deletados"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ===== ROTAS DE PRODUTOS DO CLIENTE =====

@pedido_bp.route("/produtos_cliente", methods=["GET"])
def listar_produtos_cliente():
    """Lista todos os produtos do cliente"""
    try:
        supabase = connect_db()
        response = supabase.table("produto_cliente").select("*").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/produtos_cliente", methods=["POST"])
def adicionar_produto_cliente():
    """Adiciona um produto à tabela produto_cliente"""
    data = request.get_json()

    cliente = data.get("cliente")
    produto = data.get("produto")
    qtd = data.get("qtd")

    if not cliente or not produto or qtd is None:
        return jsonify({"erro": "Dados incompletos"}), 400

    try:
        supabase = connect_db()
        response = supabase.table("produto_cliente").insert({
            "cliente": cliente,
            "produto": produto,
            "qtd": qtd
        }).execute()

        return jsonify(response.data[0] if response.data else {}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/produtos_cliente/filtrar", methods=["GET"])
def filtrar_produtos_cliente():
    """Filtra produtos do cliente por nome do cliente"""
    nome = request.args.get("nome", "").upper()
    if not nome:
        return jsonify({"erro": "Nome não fornecido"}), 400

    try:
        supabase = connect_db()
        response = supabase.table("produto_cliente") \
            .select("*") \
            .ilike("cliente", f"%{nome}%") \
            .execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/produto/deletar", methods=["DELETE"])
def deletar_todos_produtos_cliente():
    """Deleta todos os produtos da tabela produto_cliente"""
    try:
        supabase = connect_db()
        supabase.table("produto_cliente").delete().neq("id", 0).execute()
        return jsonify({"mensagem": "Todos produtos deletados"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/produto_cliente/<int:id>", methods=["DELETE"])
def deletar_produto_cliente(id):
    """Deleta um produto específico da tabela produto_cliente"""
    try:
        supabase = connect_db()
        response = supabase.table("produto_cliente").delete().eq("id", id).execute()

        if response.data:
            return jsonify({"mensagem": f"Produto {id} deletado"}), 200
        else:
            return jsonify({"erro": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/produto_dia", methods=["GET"])
def listar_produtos_dia():
    """Lista todos os produtos do dia"""
    try:
        supabase = connect_db()
        response = supabase.table("produto_dia").select("*").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

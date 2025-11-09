from datetime import datetime
from db_config import connect_db
from flask import jsonify, request, Blueprint

pedido_bp = Blueprint("pedido", __name__)


def get(tabela: str):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").execute()

        if not resposta.data:
            print(f"Nenhum registro encontrado na tabela '{tabela}'.")
            return None

        return resposta.data

    except Exception as e:
        print(f"Erro ao buscar dados da tabela '{tabela}': {e}")
        return None


@pedido_bp.route("/pedido", methods=["GET"])
def listar_pedidos():
    return get("pedido")


def get_por_id(tabela: str, id_valor: int):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").eq("id", id_valor).execute()
        if resposta.data:
            return resposta.data[0]
        else:
            return jsonify({"erro": "Pedido não encontrado"}), 400
    except Exception as e:
        return f"Erro ao buscar por ID na tabela '{tabela}': {e}"


@pedido_bp.route("/pedido/<int:id>", methods=["GET"])
def obter_pedido_por_id(id):
    return get_por_id("pedido", id)


@pedido_bp.route("/pedido", methods=["POST"])
def criar_pedido():
    """
    Rota para criar um novo pedido na tabela pedido
    Estrutura do JSON esperado:
    {
        "nome_cliente": "João da Silva"
    }
    """
    data = request.get_json()

    # Validação dos campos obrigatórios
    if not data or 'nome_cliente' not in data:
        return jsonify({"erro": "O nome do cliente é obrigatório"}), 400

    # Valores padrão
    valor_total = 0.00
    nome_cliente = data['nome_cliente']
    data_pedido = datetime.now().strftime('%Y-%m-%d')  # Formato date para o banco

    supabase = connect_db()

    try:
        # Insere o pedido na tabela (SEM a coluna status)
        resposta = supabase.table('pedido').insert({
            'valor_total': valor_total,
            'nome_cliente': nome_cliente,
            'data_pedido': data_pedido
        }).execute()

        return jsonify({
            "mensagem": "Pedido criado com sucesso",
            "dados": resposta.data[0] if resposta.data else None
        }), 201

    except Exception as e:
        print("Erro ao criar pedido:", e)
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/adicionar", methods=['POST'])
def adicionar_item_pedido():
    data = request.get_json()

    # Validação dos campos obrigatórios
    required_fields = ['pedido_id', 'nome_produto']
    if not all(field in data for field in required_fields):
        return jsonify({"erro": "pedido_id e nome_produto são obrigatórios"}), 400

    pedido_id = data['pedido_id']
    nome_produto = data['nome_produto']
    quantidade = data.get('quantidade', 1)  # Default 1 se não informado

    supabase = connect_db()

    try:
        # 1. Verifica se pedido existe
        pedido = supabase.table('pedido').select('id, valor_total').eq('id', pedido_id).execute()
        if not pedido.data:
            return jsonify({"erro": f"Pedido {pedido_id} não encontrado"}), 404

        # 2. Busca produto pelo nome na tabela produto_dia
        produto = supabase.table('produto_dia').select('id, preco, nome').ilike('nome', f'%{nome_produto}%').execute()
        if not produto.data:
            return jsonify({"erro": f"Produto '{nome_produto}' não encontrado"}), 404

        produto_id = produto.data[0]['id']
        preco_unitario = produto.data[0]['preco']

        # 3. Insere na tabela itens_pedido
        novo_item = {
            'pedido_id': pedido_id,
            'produto_id': produto_id,
            'quantidade': quantidade,
            'preco_unitario': preco_unitario
        }

        resposta = supabase.table('itens_pedido').insert(novo_item).execute()

        # 4. Atualiza valor total do pedido
        subtotal = preco_unitario * quantidade
        novo_total = pedido.data[0].get('valor_total', 0) + subtotal

        supabase.table('pedido').update({
            'valor_total': novo_total
        }).eq('id', pedido_id).execute()

        return jsonify({
            "mensagem": "Item adicionado ao pedido com sucesso",
            "item": resposta.data[0] if resposta.data else None,
            "subtotal": subtotal
        }), 201

    except Exception as e:
        # Trata caso de item duplicado (se houver constraint)
        if 'duplicate key' in str(e).lower():
            return jsonify({"erro": "Este produto já foi adicionado ao pedido"}), 409
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route('/pedido/<int:pedido_id>', methods=['PUT'])
def atualizar_pedido(pedido_id):
    try:
        data = request.get_json()

        # Verificar se o pedido existe
        pedido = connect_db().table('pedido').select('*').eq('id', pedido_id).execute()
        if len(pedido.data) == 0:
            return jsonify({'erro': 'Pedido não encontrado'}), 404

        # Campos permitidos para atualização (SEM status)
        campos_permitidos = ['valor_total', 'nome_cliente']
        dados_atualizacao = {}

        for campo in campos_permitidos:
            if campo in data:
                dados_atualizacao[campo] = data[campo]

        if not dados_atualizacao:
            return jsonify({'erro': 'Nenhum campo válido para atualização'}), 400

        # Atualiza o pedido
        supabase = connect_db()
        resposta = supabase.table("pedido").update(dados_atualizacao).eq("id", pedido_id).execute()

        return jsonify({
            'mensagem': 'Pedido atualizado com sucesso',
            'dados': resposta.data[0] if resposta.data else None
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pedido_bp.route("/finalizar_pedido/<int:pedido_id>", methods=['PUT'])
def finalizar_pedido(pedido_id):
    """
    Rota para finalizar um pedido, atualizando apenas o valor total
    """
    try:
        supabase = connect_db()

        # Verifica se o pedido existe
        pedido = supabase.table('pedido').select('*').eq('id', pedido_id).execute()
        if not pedido.data:
            return jsonify({'erro': 'Pedido não encontrado'}), 404

        # Atualiza apenas o valor total (SEM status)
        resposta = supabase.table("pedido").update({
            'valor_total': request.get_json().get('valor_total', 0)
        }).eq("id", pedido_id).execute()

        return jsonify({
            'mensagem': 'Pedido finalizado com sucesso',
            'dados': resposta.data[0] if resposta.data else None
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pedido_bp.route("/pedido/<int:id>", methods=["DELETE"])
def excluir_pedido(id):
    try:
        supabase = connect_db()

        # Verifica se o pedido existe
        pedido = supabase.table("pedido").select("*").eq("id", id).execute()
        if not pedido.data:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        # Deleta os itens do pedido primeiro
        supabase.table("itens_pedido").delete().eq("pedido_id", id).execute()

        # Deleta o pedido
        supabase.table("pedido").delete().eq("id", id).execute()

        return jsonify({"mensagem": "Pedido excluído com sucesso!"}), 200
    except Exception as e:
        print(e)
        return jsonify({"erro": str(e)}), 500


@pedido_bp.route("/deletar_pedidos_por_data", methods=["DELETE"])
def deletar_pedidos_por_data():
    data = request.get_json()
    data_inicio = data.get("data_inicio")
    data_fim = data.get("data_fim")

    if not data_inicio or not data_fim:
        return jsonify({"erro": "É necessário informar data_inicio e data_fim"}), 400

    supabase = connect_db()

    try:
        # 1️⃣ Buscar pedidos que estão dentro do período
        pedidos = (
            supabase.table("pedido")
            .select("id")
            .gte("data_pedido", data_inicio)
            .lte("data_pedido", data_fim)
            .execute()
        ).data

        if not pedidos:
            return jsonify({"mensagem": "Nenhum pedido encontrado no intervalo informado"}), 404

        # 2️⃣ Deletar os itens ligados a esses pedidos
        ids_pedidos = [p["id"] for p in pedidos]
        supabase.table("itens_pedido").delete().in_("pedido_id", ids_pedidos).execute()

        # 3️⃣ Agora sim, deletar os pedidos
        resposta = (
            supabase.table("pedido")
            .delete()
            .in_("id", ids_pedidos)
            .execute()
        )

        return jsonify({
            "mensagem": f"{len(resposta.data)} pedido(s) e seus itens foram deletados com sucesso!",
            "pedidos_deletados": ids_pedidos
        }), 200

    except Exception as e:
        print("Erro ao deletar pedidos por data:", e)
        return jsonify({"erro": str(e)}), 500
from db_config import connect_db
from flask import jsonify, request, Blueprint

usuario_bp = Blueprint("usuario", __name__)

def get_cliente(tabela: str):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").eq("perfil", "cliente").execute()
        if resposta.data:
            return jsonify(resposta.data), 200
        else:
            return jsonify({"erro": "Nenhum cliente encontrado."}), 404
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar clientes na tabela "
                                f"'{tabela}': {str(e)}"}), 400

def get_usuario(tabela: str):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").execute()
        if resposta.data:
            return jsonify(resposta.data), 200
        else:
            return jsonify({"erro": "Nenhum cliente encontrado."}), 404
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar clientes na tabela "
                                f"'{tabela}': {str(e)}"}), 400

@usuario_bp.route("/cliente", methods=["GET"])
def listar_clientes():
    return get_cliente("usuario")

@usuario_bp.route("/usuario", methods=["GET"])
def listar_usuarios():
    return get_usuario("usuario")

def get_por_id(tabela: str, id_valor: int):
    supabase = connect_db()
    try:
        resposta = supabase.table(tabela).select("*").eq("id", id_valor).limit(1).execute()
        if resposta.data:
            return resposta.data[0]  # retorna o primeiro (e único) registro
        else:
            print(f"Nenhum registro encontrado com id={id_valor}.")
            return None
    except Exception as e:
        print(f"Erro ao buscar por ID na tabela '{tabela}': {e}")
        return None

@usuario_bp.route("/usuario/<int:id>", methods=["GET"])
def obter_produto_por_id(id):
    return get_por_id("usuario",id)

def criar_usuario():
    data = request.get_json()  # recebe dados no corpo da requisição
    nome = data.get('nome')
    perfil = data.get('perfil')
    username = data.get("username")
    password = data.get("password")

    if not nome or not perfil or not username or not password:
        return jsonify({"erro": "Algum dado está faltando"}), 400

    supabase = connect_db()

    try:
        resposta = supabase.table("usuario").insert({"nome": nome,
                                                     "perfil": perfil,
                                                     "username": username,
                                                     "password": password}).execute()
        return jsonify({
            "mensagem": "usuario inserido com sucesso!",
            "data": resposta.data
        }), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@usuario_bp.route("/usuario", methods=["POST"])
def nova_usuario():
    return criar_usuario()

def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"erro": "Username e password são obrigatórios"}), 400

    supabase = connect_db()

    try:
        resposta = (
            supabase
            .table("usuario")
            .select("id, username, password")
            .eq("username", username)
            .eq("password", password)
            .limit(1)
            .execute()
        )

        if resposta.data:
            usuario = resposta.data[0]
            return jsonify({
                "mensagem": "Login realizado com sucesso",
                "usuario": {
                    "id": usuario["id"],
                    "username": usuario["username"]
                }
            }), 200
        else:
            return jsonify({"erro": "Username ou senha inválidos"}), 401

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@usuario_bp.route("/usuario/login", methods=["POST"])
def logar():
    return login()


def atualizar_usuario_no_banco(id: int, dados_atualizacao: dict):
    try:
        supabase = connect_db()

        # Verifica se o usuário existe
        usuario_existente = supabase.table("usuario").select("*").eq("id", id).execute()
        if not usuario_existente.data:
            return False, "Usuário não encontrado"

        # Atualiza o usuário
        resposta = supabase.table("usuario").update(dados_atualizacao).eq("id", id).execute()

        return True, {
            "dados_atualizados": dados_atualizacao,
            "usuario_id": id,
            "dados_completos": resposta.data[0] if resposta.data else None
        }

    except Exception as e:
        return False, str(e)


@usuario_bp.route("/usuario/<int:id>", methods=["PUT"])
def atualizar_usuario(id):
    data = request.get_json()

    # Campos que podem ser atualizados
    campos_permitidos = ['nome', 'perfil', 'username', 'password']
    dados_atualizacao = {k: v for k, v in data.items() if k in campos_permitidos}

    if not dados_atualizacao:
        return jsonify({"erro": "Nenhum dado válido fornecido para atualização"}), 400

    sucesso, resposta = atualizar_usuario_no_banco(id, dados_atualizacao)

    if sucesso:
        return jsonify({
            "mensagem": "Usuário atualizado com sucesso",
            **resposta
        }), 200
    else:
        return jsonify({"erro": resposta}), 404 if resposta == "Usuário não encontrado" else 500


def pagamento(id):
    supabase = connect_db()

    try:
        data = request.get_json()
        valor = data.get("pagamento")

        # Buscar o valor_total atual
        resposta = supabase.table("pedido").select("valor_total").eq("id", id).limit(1).execute()

        if not resposta.data:
            return {"erro": f"Nenhum pedido encontrado com id={id}"}, 404

        valor_total = int(resposta.data[0]["valor_total"])

        restante = valor_total - valor
        novo_valor = {"valor_total": restante}

        # Atualizar o valor_total do pedido
        resposta_update = supabase.table("pedido").update(novo_valor).eq("id", id).execute()

        return {"resposta": resposta_update.data[0]}

    except Exception as e:
        return {"erro": f"Erro ao processar o pagamento: {str(e)}"}, 500
@usuario_bp.route("/pagamento/<int:id>", methods=["PUT"])
def pagar(id):
    return pagamento(id)

def delete(id):
    try:
        supabase = connect_db()
        supabase.table("usuario").delete().eq("id", id).execute()

        return jsonify({"message": "excluido!!"}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@usuario_bp.route("/usuario/<int:id>", methods=["DELETE"])
def excluir_usuario(id):
    return delete(id)

def verifica_usuario():
    data = request.get_json()
    username = data.get("username")  # aceita os dois nomes
    nome = data.get("nome")
    perfil = data.get("perfil")
    password = data.get("password")

    if not username or not nome or not perfil or not password:
        return jsonify({"erro": "Todos os campos são obrigatórios"}), 400

    # Normalizar username (remover espaços extras e forçar minúsculo)
    username = username.strip().lower()

    supabase = connect_db()

    try:
        # Verificar se o usuário já existe
        usuario_existente = (
            supabase.table("usuario")
            .select("*")
            .eq("username", username)
            .execute()
        )

        if usuario_existente.data:
            return jsonify({"mensagem": f"O nome de usuário '{username}' já existe."}), 409

        # Criar novo usuário
        novo_usuario = (
            supabase.table("usuario")
            .insert({
                "nome": nome,
                "perfil": perfil,
                "username": username,
                "password": password
            })
            .execute()
        )

        return jsonify({
            "mensagem": f"Usuário '{username}' criado com sucesso!",
            "usuario": novo_usuario.data
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@usuario_bp.route("/verifica_usuario", methods=["POST"])
def usuario_existente():
    return verifica_usuario()



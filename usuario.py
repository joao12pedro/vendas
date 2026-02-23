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
    data = request.get_json()
    print("DATA:", data)

    supabase = connect_db()

    resposta = supabase.table("usuario").insert({
        "nome": data["nome"],
        "perfil": data["perfil"],
        "username": data["username"],
        "password": data["password"]
    }).execute()

    print("RESPOSTA SUPABASE:", resposta.data)  # 👈 DEBUG

    return jsonify({
        "mensagem": "usuario inserido com sucesso!",
        "data": resposta.data
    }), 201


@usuario_bp.route("/usuario", methods=["POST"])
def nova_usuario():
    return criar_usuario()

# Endpoint de login
@usuario_bp.route("/usuario/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"erro": "Usuário e senha são obrigatórios"}), 400

    username = username.strip().lower()

    supabase = connect_db()

    try:
        resultado = (
            supabase.table("usuario")
            .select("*")
            .eq("username", username)
            .eq("password", password)  # Lembre-se: comparar hash!
            .execute()
        )

        if resultado.data:
            return jsonify({
                "mensagem": "Login realizado com sucesso",
                "usuario": resultado.data[0]
            }), 200
        else:
            return jsonify({"erro": "Usuário ou senha inválidos"}), 401

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


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


@usuario_bp.route("/usuario/verificar_disponibilidade/<username>", methods=["GET"])
def verificar_disponibilidade(username):
    """
    Endpoint para verificar se um username está disponível
    Retorna: {"disponivel": true/false, "mensagem": "..."}
    """
    try:
        print(f"🔵 Verificando disponibilidade: {username}")

        supabase = connect_db()

        # Normalizar username
        username = username.strip().lower()

        # Verificar se já existe
        resultado = (
            supabase.table("usuario")
            .select("*")
            .eq("username", username)
            .execute()
        )

        existe = len(resultado.data) > 0

        print(f"🔵 Username '{username}' existe? {existe}")

        return jsonify({
            "disponivel": not existe,
            "mensagem": "Username disponível" if not existe else "Username já existe"
        }), 200

    except Exception as e:
        print(f"🔴 Erro: {e}")
        return jsonify({"erro": str(e)}), 500
@usuario_bp.route("/usuario/verifica_usuario", methods=["POST"])
def verifica_usuario():
    """
    Endpoint para criar usuário (com verificação de duplicidade)
    """
    data = request.get_json()
    username = data.get("username")
    nome = data.get("nome")
    perfil = data.get("perfil")
    password = data.get("password")

    print(f"🔵 Recebido: username={username}, nome={nome}")

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

        print(f"🔵 Usuário existente: {usuario_existente.data}")

        if usuario_existente.data:
            print(f"🟠 Username '{username}' já existe!")
            return jsonify({"mensagem": f"O nome de usuário '{username}' já existe."}), 409

        # Criar novo usuário
        novo_usuario = (
            supabase.table("usuario")
            .insert({
                "nome": nome,
                "perfil": perfil,
                "username": username,
                "password": password  # Lembre-se: fazer hash da senha!
            })
            .execute()
        )

        print(f"🟢 Usuário criado: {novo_usuario.data}")

        return jsonify({
            "mensagem": f"Usuário '{username}' criado com sucesso!",
            "usuario": novo_usuario.data
        }), 201

    except Exception as e:
        print(f"🔴 Erro: {e}")
        return jsonify({"erro": str(e)}), 500




# cliente.py
from flask import Blueprint, request, jsonify
from db_config import connect_db

cliente_bp = Blueprint("cliente", __name__)

@cliente_bp.route("/cliente", methods=["POST"])
def registrar_cliente():
    data = request.get_json()
    nome = data.get("nome")

    if not nome or len(nome.strip()) == 0:
        return jsonify({"erro": "Nome completo é obrigatório"}), 400

    supabase = connect_db()

    try:
        # Verifica se o cliente já existe para não duplicar
        check = supabase.table("usuario") \
            .select("id, nome") \
            .eq("nome", nome) \
            .eq("perfil", "cliente") \
            .execute()

        if check.data:
            # Se já existe, apenas retorna sucesso para liberar o cardápio
            return jsonify({
                "mensagem": "Cliente já registrado",
                "cliente": check.data[0]
            }), 200

        # Se não existe, faz o INSERT
        resp = supabase.table("usuario").insert({
            "nome": nome,
            "perfil": "cliente",
            "username": None,  # Ainda não obrigatório
            "password": None   # Ainda não obrigatório
        }).execute()

        return jsonify({
            "mensagem": "Cliente registrado com sucesso",
            "cliente": resp.data[0]
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
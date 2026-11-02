# cardapio.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from db_config import connect_db

cardapio_bp = Blueprint("cardapio", __name__)

BUCKET = "cardapios"
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "webp", "gif"}


def extensao_valida(nome_arquivo):
    return "." in nome_arquivo and \
           nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS


# =====================================================
# 📌 UPLOAD de cardápio (para o Supabase Storage)
# =====================================================
@cardapio_bp.route("/cardapio/upload", methods=["POST"])
def upload_cardapio():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files["imagem"]

    if arquivo.filename == "":
        return jsonify({"erro": "Nome do arquivo vazio"}), 400

    if not extensao_valida(arquivo.filename):
        return jsonify({
            "erro": "Formato inválido. Use PNG, JPG, JPEG, WEBP ou GIF"
        }), 400

    # Gera nome único
    ext = arquivo.filename.rsplit(".", 1)[1].lower()
    nome_unico = f"cardapio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

    supabase = connect_db()

    try:
        # Lê o conteúdo do arquivo em bytes
        conteudo = arquivo.read()

        # Faz o upload para o bucket
        supabase.storage.from_(BUCKET).upload(
            path=nome_unico,
            file=conteudo,
            file_options={"content-type": arquivo.mimetype}
        )

        # Gera a URL pública
        url_publica = supabase.storage.from_(BUCKET).get_public_url(nome_unico)

        return jsonify({
            "mensagem": "Cardápio enviado com sucesso",
            "arquivo": nome_unico,
            "url": url_publica
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =====================================================
# 📌 Retorna a ÚLTIMA imagem enviada (do Supabase Storage)
# =====================================================
@cardapio_bp.route("/cardapio/ultimo", methods=["GET"])
def ultimo_cardapio():
    supabase = connect_db()

    try:
        # Lista os arquivos do bucket
        arquivos = supabase.storage.from_(BUCKET).list()

        if not arquivos:
            return jsonify({
                "tem_cardapio": False,
                "mensagem": "Nenhum cardápio cadastrado"
            }), 200

        # Ordena pela data de criação (mais recente primeiro)
        arquivos.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

        ultimo = arquivos[0]
        nome = ultimo["name"]

        # Gera a URL pública
        url_publica = supabase.storage.from_(BUCKET).get_public_url(nome)

        # Formata a data
        data_str = ultimo.get("created_at", "")
        if data_str:
            data_formatada = datetime.fromisoformat(
                data_str.replace("Z", "+00:00")
            ).strftime("%d/%m/%Y %H:%M")
        else:
            data_formatada = "-"

        return jsonify({
            "tem_cardapio": True,
            "arquivo": nome,
            "url": url_publica,
            "data_upload": data_formatada
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =====================================================
# 📌 Lista todos os cardápios (opcional, útil para histórico)
# =====================================================
@cardapio_bp.route("/cardapio/lista", methods=["GET"])
def listar_cardapios():
    supabase = connect_db()
    try:
        arquivos = supabase.storage.from_(BUCKET).list()
        lista = []
        for arq in arquivos:
            lista.append({
                "arquivo": arq["name"],
                "url": supabase.storage.from_(BUCKET).get_public_url(arq["name"]),
                "data": arq.get("created_at", "")
            })
        lista.sort(key=lambda x: x["data"], reverse=True)
        return jsonify(lista), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =====================================================
# 📌 Deletar cardápio específico (do Supabase Storage)
# =====================================================
@cardapio_bp.route("/cardapio/<nome_arquivo>", methods=["DELETE"])
def deletar_cardapio(nome_arquivo):
    supabase = connect_db()
    try:
        supabase.storage.from_(BUCKET).remove([nome_arquivo])
        return jsonify({"mensagem": "Cardápio removido"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
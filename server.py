import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from pedido import pedido_bp
from produto import produto_bp
from cardapio import cardapio_bp
from cliente import cliente_bp  # 🆕 IMPORTAÇÃO

# 🔧 Define o caminho absoluto para a pasta static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_STATIC = os.path.join(BASE_DIR, "static")

# Configura o Flask para usar a pasta estática correta
app = Flask(__name__, static_folder=PASTA_STATIC, static_url_path="/static")
CORS(app)

app.register_blueprint(pedido_bp)
app.register_blueprint(produto_bp)
app.register_blueprint(cardapio_bp)
app.register_blueprint(cliente_bp)  # 🆕 REGISTRO

@app.route("/")
def index():
    return send_from_directory(PASTA_STATIC, "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

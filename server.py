from flask import Flask, send_from_directory
from flask_cors import CORS
from produto import produto_bp
from usuario import usuario_bp
from pedido import pedido_bp
import os

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

# REGISTRA OS BLUEPRINTS
app.register_blueprint(produto_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(pedido_bp)

@app.route("/")
def home():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html')

if __name__ == "__main__":
    app.run(debug=True)
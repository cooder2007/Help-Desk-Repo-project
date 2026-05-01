import os
from flask import Flask

from flask_cors import CORS
from flask_jwt_extended import JWTManager

from database import init_db
from chatbot_engine import load_knowledge_base
from routes.auth import auth_bp
from routes.tokens import tokens_bp
from routes.chatbot import chat_bp

app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET", "christ-helpdesk-super-secret-2024"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False

# ✅ Apply CORS globally to ALL routes
CORS(app, origins="*", supports_credentials=True)
JWTManager(app)

@app.route("/")
def home():
    return "Backend is running 🚀"

@app.get("/health")
def health():
    return {"status": "ok"}

app.register_blueprint(auth_bp)
app.register_blueprint(tokens_bp)
app.register_blueprint(chat_bp)

if __name__ == "__main__":
    init_db()
    load_knowledge_base()
    print("🚀  Server running at http://localhost:5000")
    app.run(port=5000, debug=True)
"""
routes/chatbot.py — Chatbot endpoints
  /api/chatbot/         → authenticated (students/staff)
  /api/public/chat      → no auth required (candidates/public)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from chatbot_engine import get_response

chat_bp = Blueprint("chat", __name__)


# ── Health check ─────────────────────────────────────────────
@chat_bp.route("/api/chatbot/", methods=["GET"])
def health():
    return jsonify(status="Chatbot ready"), 200


# ── Authenticated chat (students / staff) ────────────────────
@chat_bp.route("/api/chatbot/", methods=["POST"])
@jwt_required()
def chat():
    d       = request.get_json(silent=True) or {}
    message = (d.get("message") or "").strip()

    if not message:
        return jsonify(error="message is required"), 400

    reply = get_response(message, is_candidate=False)
    return jsonify(reply=reply), 200


# ── Public candidate chat (NO auth required) ─────────────────
@chat_bp.route("/api/public/chat", methods=["POST"])
def public_chat():
    d       = request.get_json(silent=True) or {}
    message = (d.get("message") or "").strip()

    if not message:
        return jsonify(error="message is required"), 400

    if len(message) > 500:
        return jsonify(error="Message too long (max 500 characters)"), 400

    reply = get_response(message, is_candidate=True)
    return jsonify(reply=reply), 200


# ── Public health (for candidate page) ───────────────────────
@chat_bp.route("/api/public/health", methods=["GET"])
def public_health():
    return jsonify(status="ok"), 200
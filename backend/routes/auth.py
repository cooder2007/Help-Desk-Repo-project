"""
routes/auth.py — Register, Login, /me
"""
import json, bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from database import get_conn, row_to_dict

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── helpers ──────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def _check(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def _user_public(u: dict) -> dict:
    """Strip password_hash before sending to client."""
    u.pop("password_hash", None)
    return u


# ── POST /api/auth/register ──────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    d = request.get_json(silent=True) or {}

    required = ["name", "email", "password", "role"]
    for f in required:
        if not d.get(f):
            return jsonify(error=f"'{f}' is required"), 400

    role = d["role"].lower()
    if role not in ("student", "teacher", "admin", "hod"):
        return jsonify(error="role must be student | teacher | admin | hod"), 400

    # Role-specific validation
    if role == "student":
        if not all([d.get("semester"), d.get("class_section"), d.get("department")]):
            return jsonify(error="Students need semester, class_section, department"), 400
    elif role == "teacher":
        if not all([d.get("department"), d.get("subject")]):
            return jsonify(error="Teachers need department and subject"), 400
    elif role == "admin":
        valid_types = {"Dean","Coordinator","Director","Academic Administrator",
                       "Vice-President","Vice-Chancellor","Chancellor"}
        if d.get("admin_type") not in valid_types:
            return jsonify(error="admin_type must be one of: " + ", ".join(valid_types)), 400
    elif role == "hod":
        if not d.get("department"):
            return jsonify(error="HOD must specify department"), 400

    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO users
                   (name, email, password_hash, role, admin_type, department,
                    semester, class_section, subject, classes_taught)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    d["name"].strip(),
                    d["email"].strip().lower(),
                    _hash(d["password"]),
                    role,
                    d.get("admin_type"),
                    d.get("department"),
                    d.get("semester"),
                    d.get("class_section"),
                    d.get("subject"),
                    json.dumps(d.get("classes_taught", [])),
                )
            )
        return jsonify(message="Registered successfully"), 201
    except Exception as e:
        if "UNIQUE" in str(e):
            return jsonify(error="Email already registered"), 409
        return jsonify(error=str(e)), 500


# ── POST /api/auth/login ─────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    email    = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""

    if not email or not password:
        return jsonify(error="email and password required"), 400

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    if not row or not _check(password, row["password_hash"]):
        return jsonify(error="Invalid credentials"), 401

    user = dict(row)
    token = create_access_token(identity=str(user["id"]))
    return jsonify(token=token, user=_user_public(user)), 200


# ── GET /api/auth/me ─────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        return jsonify(error="User not found"), 404
    return jsonify(_user_public(dict(row))), 200

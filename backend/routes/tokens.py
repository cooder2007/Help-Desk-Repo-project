from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_conn, row_to_dict, rows_to_list

tokens_bp = Blueprint("tokens", __name__, url_prefix="/api/tokens")

STAFF_ROLES = ("teacher", "admin", "hod")


# ── CREATE TICKET ────────────────────────────────────────────
@tokens_bp.route("/", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_token():
    d = request.get_json() or {}

    title       = d.get("title")
    description = d.get("description")
    level       = d.get("level", "university")
    department  = d.get("department")

    if not title or not description:
        return jsonify(error="title and description are required"), 400

    user_id = int(get_jwt_identity())

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO tokens (title, description, level, created_by, department)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, level, user_id, department)
        )
        token_id = cur.lastrowid

    return jsonify(id=token_id, message="Ticket created successfully"), 201


# ── GET ALL TICKETS ──────────────────────────────────────────
@tokens_bp.route("/", methods=["GET"], strict_slashes=False)
def get_all_tokens():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tokens ORDER BY created_at DESC"
        ).fetchall()
    return jsonify(rows_to_list(rows)), 200


# ── GET MY TICKETS ───────────────────────────────────────────
@tokens_bp.route("/my", methods=["GET"], strict_slashes=False)
@jwt_required()
def my_tokens():
    user_id = int(get_jwt_identity())
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tokens WHERE created_by=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    return jsonify(rows_to_list(rows)), 200


# ── UPVOTE ───────────────────────────────────────────────────
@tokens_bp.route("/<int:token_id>/upvote", methods=["POST"], strict_slashes=False)
@jwt_required()
def upvote(token_id):
    user_id = int(get_jwt_identity())
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM upvotes WHERE token_id=? AND user_id=?",
            (token_id, user_id)
        ).fetchone()

        if existing:
            conn.execute(
                "DELETE FROM upvotes WHERE token_id=? AND user_id=?",
                (token_id, user_id)
            )
            conn.execute(
                "UPDATE tokens SET upvote_count = MAX(0, upvote_count - 1) WHERE id=?",
                (token_id,)
            )
            return jsonify(message="Upvote removed"), 200
        else:
            conn.execute(
                "INSERT INTO upvotes (token_id, user_id) VALUES (?, ?)",
                (token_id, user_id)
            )
            conn.execute(
                "UPDATE tokens SET upvote_count = upvote_count + 1 WHERE id=?",
                (token_id,)
            )
            return jsonify(message="Upvoted"), 200


# ── GET REPLIES FOR A TICKET ─────────────────────────────────
@tokens_bp.route("/<int:token_id>/replies", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_replies(token_id):
    with get_conn() as conn:
        # Check ticket exists
        ticket = conn.execute(
            "SELECT id FROM tokens WHERE id=?", (token_id,)
        ).fetchone()
        if not ticket:
            return jsonify(error="Ticket not found"), 404

        rows = conn.execute(
            """SELECT r.id, r.message, r.created_at,
                      u.name as author_name, u.role as author_role
               FROM replies r
               JOIN users u ON u.id = r.author_id
               WHERE r.token_id = ?
               ORDER BY r.created_at ASC""",
            (token_id,)
        ).fetchall()

    return jsonify(rows_to_list(rows)), 200


# ── POST A REPLY (staff only) ─────────────────────────────────
@tokens_bp.route("/<int:token_id>/replies", methods=["POST"], strict_slashes=False)
@jwt_required()
def post_reply(token_id):
    user_id = int(get_jwt_identity())

    with get_conn() as conn:
        # Get user role
        user = conn.execute(
            "SELECT role FROM users WHERE id=?", (user_id,)
        ).fetchone()

        if not user:
            return jsonify(error="User not found"), 404

        # ── Role check: only staff can reply ──────────────────
        if user["role"] not in STAFF_ROLES:
            return jsonify(error="Only staff members can reply to tickets"), 403

        # Check ticket exists
        ticket = conn.execute(
            "SELECT id FROM tokens WHERE id=?", (token_id,)
        ).fetchone()
        if not ticket:
            return jsonify(error="Ticket not found"), 404

        d       = request.get_json() or {}
        message = (d.get("message") or "").strip()
        resolve = d.get("resolve", False)   # optional: mark as resolved

        if not message:
            return jsonify(error="message is required"), 400

        # Insert reply
        conn.execute(
            "INSERT INTO replies (token_id, author_id, message) VALUES (?, ?, ?)",
            (token_id, user_id, message)
        )

        # Optionally resolve the ticket
        if resolve:
            conn.execute(
                "UPDATE tokens SET status='resolved', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (token_id,)
            )

    return jsonify(message="Reply posted successfully"), 201


# ── UPDATE TICKET STATUS (staff only) ────────────────────────
@tokens_bp.route("/<int:token_id>/status", methods=["PATCH"], strict_slashes=False)
@jwt_required()
def update_status(token_id):
    user_id = int(get_jwt_identity())

    with get_conn() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id=?", (user_id,)
        ).fetchone()

        if not user or user["role"] not in STAFF_ROLES:
            return jsonify(error="Only staff can update ticket status"), 403

        d      = request.get_json() or {}
        status = d.get("status")

        valid_statuses = ("open", "in_progress", "resolved", "closed")
        if status not in valid_statuses:
            return jsonify(error=f"status must be one of: {', '.join(valid_statuses)}"), 400

        conn.execute(
            "UPDATE tokens SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, token_id)
        )

    return jsonify(message="Status updated"), 200
from flask import Blueprint, abort, jsonify, request

from ..extensions import db
from ..models import User

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.post("")
def create_user():
    """No auth in v1 — a user is just an email, created up front and referenced by id elsewhere."""
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")

    if not email:
        abort(400, description="email is required")

    if User.query.filter_by(email=email).first():
        abort(409, description="a user with this email already exists")

    user = User(email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@users_bp.get("/<int:user_id>")
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())
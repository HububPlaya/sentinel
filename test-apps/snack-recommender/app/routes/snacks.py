from flask import Blueprint, abort, jsonify, request

from ..extensions import db
from ..models import Rating, Snack, User

snacks_bp = Blueprint("snacks", __name__, url_prefix="/snacks")


@snacks_bp.get("")
def list_snacks():
    """Browse snacks, optionally filtered by cuisine, country, or a flavor tag."""
    query = Snack.query

    cuisine = request.args.get("cuisine")
    country = request.args.get("country")
    flavor = request.args.get("flavor")

    if cuisine:
        query = query.filter(Snack.cuisine_type.ilike(cuisine))
    if country:
        query = query.filter(Snack.country_of_origin.ilike(country))
    if flavor:
        query = query.filter(Snack.flavor_tags.ilike(f"%{flavor}%"))

    snacks = query.all()
    return jsonify([s.to_dict(include_avg_rating=True) for s in snacks])


@snacks_bp.get("/<int:snack_id>")
def get_snack(snack_id):
    snack = Snack.query.get_or_404(snack_id)
    return jsonify(snack.to_dict(include_avg_rating=True))


@snacks_bp.post("/<int:snack_id>/rate")
def rate_snack(snack_id):
    """Rate a snack. Re-rating the same snack updates the existing rating rather than duplicating it."""
    snack = Snack.query.get_or_404(snack_id)
    payload = request.get_json(silent=True) or {}

    user_id = payload.get("user_id")
    rating_value = payload.get("rating")
    review_text = payload.get("review_text")

    if not user_id or rating_value is None:
        abort(400, description="user_id and rating are required")

    try:
        rating_value = int(rating_value)
    except (TypeError, ValueError):
        abort(400, description="rating must be an integer between 1 and 5")

    if not (1 <= rating_value <= 5):
        abort(400, description="rating must be between 1 and 5")

    user = User.query.get_or_404(user_id)

    existing = Rating.query.filter_by(user_id=user.id, snack_id=snack.id).first()
    if existing:
        existing.rating = rating_value
        existing.review_text = review_text
    else:
        existing = Rating(
            user_id=user.id,
            snack_id=snack.id,
            rating=rating_value,
            review_text=review_text,
        )
        db.session.add(existing)

    db.session.commit()
    return jsonify(existing.to_dict()), 201
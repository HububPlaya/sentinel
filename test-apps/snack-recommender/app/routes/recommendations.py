from flask import Blueprint, jsonify

from ..extensions import db
from ..models import Rating, Snack, User

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/recommendations")


@recommendations_bp.get("/<int:user_id>")
def get_recommendations(user_id):
    """v1 recommendation logic — deliberately simple, no ML:

    1. Find cuisines this user has rated 4 or higher.
    2. Suggest other snacks from those cuisines they haven't rated yet.
    3. If they have no rating history, fall back to the highest-rated snacks overall.
    """
    User.query.get_or_404(user_id)  # 404 if the user doesn't exist

    liked_cuisines = (
        db.session.query(Snack.cuisine_type)
        .join(Rating, Rating.snack_id == Snack.id)
        .filter(Rating.user_id == user_id, Rating.rating >= 4)
        .distinct()
        .all()
    )
    liked_cuisines = [c[0] for c in liked_cuisines]

    already_rated_ids = (
        db.session.query(Rating.snack_id).filter(Rating.user_id == user_id).subquery()
    )

    if liked_cuisines:
        candidates = (
            Snack.query.filter(Snack.cuisine_type.in_(liked_cuisines))
            .filter(~Snack.id.in_(already_rated_ids))
            .all()
        )
    else:
        candidates = Snack.query.filter(~Snack.id.in_(already_rated_ids)).all()

    ranked = sorted(candidates, key=lambda s: (s.average_rating() or 0), reverse=True)

    return jsonify([s.to_dict(include_avg_rating=True) for s in ranked[:10]])
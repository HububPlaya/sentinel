from datetime import datetime

from .extensions import db


class Snack(db.Model):
    __tablename__ = "snacks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    country_of_origin = db.Column(db.String(80), nullable=False)
    cuisine_type = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text)
    flavor_tags = db.Column(db.String(200))  # comma-separated, e.g. "sweet,spicy,fried"
    image_url = db.Column(db.String(300))

    ratings = db.relationship(
        "Rating", back_populates="snack", cascade="all, delete-orphan"
    )

    def average_rating(self):
        if not self.ratings:
            return None
        return round(sum(r.rating for r in self.ratings) / len(self.ratings), 2)

    def to_dict(self, include_avg_rating=False):
        data = {
            "id": self.id,
            "name": self.name,
            "country_of_origin": self.country_of_origin,
            "cuisine_type": self.cuisine_type,
            "description": self.description,
            "flavor_tags": self.flavor_tags.split(",") if self.flavor_tags else [],
            "image_url": self.image_url,
        }
        if include_avg_rating:
            data["average_rating"] = self.average_rating()
        return data


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings = db.relationship(
        "Rating", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {"id": self.id, "email": self.email}


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    snack_id = db.Column(db.Integer, db.ForeignKey("snacks.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="ratings")
    snack = db.relationship("Snack", back_populates="ratings")

    __table_args__ = (
        db.UniqueConstraint("user_id", "snack_id", name="uq_user_snack_rating"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "snack_id": self.snack_id,
            "rating": self.rating,
            "review_text": self.review_text,
        }
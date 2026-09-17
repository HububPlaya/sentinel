from .extensions import db
from .models import Snack

# Starting dataset — deliberately international, matching the app's focus on foreign snacks.
# Extend this list over time; it's the easiest way to make recommendations feel less repetitive.
SNACKS = [
    {"name": "Pocky (Matcha)", "country_of_origin": "Japan", "cuisine_type": "Japanese",
     "description": "Thin biscuit sticks coated in matcha-flavored chocolate.",
     "flavor_tags": "sweet,matcha,chocolate"},
    {"name": "Kürtőskalács", "country_of_origin": "Hungary", "cuisine_type": "Hungarian",
     "description": "Chimney cake — a spit cake rolled in sugar and cinnamon.",
     "flavor_tags": "sweet,cinnamon,pastry"},
    {"name": "Khachapuri Bites", "country_of_origin": "Georgia", "cuisine_type": "Georgian",
     "description": "Mini cheese-filled bread boats.",
     "flavor_tags": "savory,cheese,bread"},
    {"name": "Turon", "country_of_origin": "Philippines", "cuisine_type": "Filipino",
     "description": "Fried banana and jackfruit spring rolls.",
     "flavor_tags": "sweet,banana,fried"},
    {"name": "Simit", "country_of_origin": "Turkey", "cuisine_type": "Turkish",
     "description": "Circular bread encrusted with sesame seeds.",
     "flavor_tags": "savory,sesame,bread"},
    {"name": "Alfajores", "country_of_origin": "Argentina", "cuisine_type": "Argentinian",
     "description": "Sandwich cookies filled with dulce de leche.",
     "flavor_tags": "sweet,caramel,cookie"},
    {"name": "Bánh Tráng Trộn", "country_of_origin": "Vietnam", "cuisine_type": "Vietnamese",
     "description": "Torn rice paper salad with dried beef, herbs, and chili.",
     "flavor_tags": "savory,spicy,chewy"},
    {"name": "Koeksisters", "country_of_origin": "South Africa", "cuisine_type": "South African",
     "description": "Braided dough, deep-fried and soaked in syrup.",
     "flavor_tags": "sweet,syrup,fried"},
    {"name": "Melomakarona", "country_of_origin": "Greece", "cuisine_type": "Greek",
     "description": "Honey-soaked semolina cookies with walnuts.",
     "flavor_tags": "sweet,honey,walnut"},
    {"name": "Pani Puri", "country_of_origin": "India", "cuisine_type": "Indian",
     "description": "Crisp hollow shells filled with tangy spiced water.",
     "flavor_tags": "savory,spicy,tangy"},
    {"name": "Churros con Cajeta", "country_of_origin": "Mexico", "cuisine_type": "Mexican",
     "description": "Fried dough pastry served with goat's-milk caramel.",
     "flavor_tags": "sweet,caramel,fried"},
    {"name": "Onigiri (Umeboshi)", "country_of_origin": "Japan", "cuisine_type": "Japanese",
     "description": "Rice ball filled with pickled plum.",
     "flavor_tags": "savory,sour,rice"},
    {"name": "Halva", "country_of_origin": "Lebanon", "cuisine_type": "Lebanese",
     "description": "Dense sesame-paste confection.",
     "flavor_tags": "sweet,sesame,dense"},
    {"name": "Prekmurska Gibanica", "country_of_origin": "Slovenia", "cuisine_type": "Slovenian",
     "description": "Layered pastry with poppy seed, walnut, apple, and cheese.",
     "flavor_tags": "sweet,layered,nutty"},
    {"name": "Jian Bing", "country_of_origin": "China", "cuisine_type": "Chinese",
     "description": "Savory crepe filled with egg, herbs, and crispy wonton.",
     "flavor_tags": "savory,crispy,egg"},
]


def seed():
    """Populates the snacks table if it's currently empty. Safe to run repeatedly."""
    if Snack.query.first():
        print("Snacks table already has data — skipping seed.")
        return

    for entry in SNACKS:
        db.session.add(Snack(**entry))
    db.session.commit()
    print(f"Seeded {len(SNACKS)} snacks.")
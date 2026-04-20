from datetime import datetime

from sqlalchemy.orm import Session

from models import Base, Dish, Restaurant

SEED_RESTAURANTS = [
    {
        "place_id": "seed_saravana_bhavan_tnagar",
        "name": "Saravana Bhavan",
        "address": "20, South Usman Road, T. Nagar, Chennai 600017",
        "lat": 13.0790,
        "lng": 80.2650,
        "rating": 4.3,
        "price_level": 2,
        "cuisine_tags": "south-indian,vegetarian",
        "is_open": True,
        "phone": "+91-44-24342224",
        "photo_url": "",
        "dishes": [
            {"name": "Masala Dosa", "price": 120, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Crispy crepe with spiced potato filling, served with chutneys and sambar"},
            {"name": "Idli Sambar", "price": 80, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Steamed rice cakes with aromatic lentil soup"},
            {"name": "Filter Coffee", "price": 50, "category": "Beverages", "is_veg": True, "is_vegan": False, "description": "Traditional South Indian drip coffee with frothy milk"},
            {"name": "Mini Tiffin Combo", "price": 180, "category": "Combos", "is_veg": True, "is_vegan": True, "description": "Idli, vada, dosa, pongal with sambar and chutneys"},
            {"name": "Ghee Pongal", "price": 110, "category": "Breakfast", "is_veg": True, "is_vegan": False, "description": "Creamy rice and lentil dish tempered with ghee and pepper"},
            {"name": "Rava Kesari", "price": 70, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Sweet semolina pudding with cashews and saffron"},
            {"name": "Medu Vada", "price": 60, "category": "Starters", "is_veg": True, "is_vegan": True, "description": "Crispy fried lentil donuts served with chutney"},
            {"name": "Curd Rice", "price": 90, "category": "Main Course", "is_veg": True, "is_vegan": False, "description": "Seasoned yogurt rice with pomegranate and grapes"},
            {"name": "Sambar Rice", "price": 130, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Rice mixed with tangy lentil sambar and vegetables"},
            {"name": "Badam Milk", "price": 80, "category": "Beverages", "is_veg": True, "is_vegan": False, "description": "Chilled almond milk with cardamom and saffron"},
        ],
    },
    {
        "place_id": "seed_anjappar_annanagar",
        "name": "Anjappar Chettinad",
        "address": "15, 2nd Avenue, Anna Nagar, Chennai 600040",
        "lat": 13.0870,
        "lng": 80.2580,
        "rating": 4.1,
        "price_level": 3,
        "cuisine_tags": "chettinad,non-veg,south-indian",
        "is_open": True,
        "phone": "+91-44-26214455",
        "photo_url": "",
        "dishes": [
            {"name": "Chicken Chettinad", "price": 320, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Spicy chicken curry with freshly ground chettinad masala"},
            {"name": "Mutton Biryani", "price": 350, "category": "Biryani", "is_veg": False, "is_vegan": False, "description": "Fragrant basmati rice with tender mutton and spices"},
            {"name": "Chicken 65", "price": 220, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Deep-fried spicy chicken with curry leaves and chillies"},
            {"name": "Mutton Sukka", "price": 380, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Dry roasted mutton with coconut and chettinad spices"},
            {"name": "Egg Kothu Parotta", "price": 160, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Shredded parotta stir-fried with egg and spices"},
            {"name": "Prawn Fry", "price": 290, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Crispy fried prawns with tangy masala coating"},
            {"name": "Chicken Biryani", "price": 280, "category": "Biryani", "is_veg": False, "is_vegan": False, "description": "Aromatic rice layered with spiced chicken"},
            {"name": "Fish Curry", "price": 260, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Tangy fish curry with tamarind and kokum"},
            {"name": "Parotta", "price": 50, "category": "Breads", "is_veg": True, "is_vegan": True, "description": "Flaky layered flatbread, perfect with curry"},
            {"name": "Chettinad Chicken Soup", "price": 120, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Peppery chicken broth with chettinad spices"},
            {"name": "Jigarthanda", "price": 100, "category": "Beverages", "is_veg": True, "is_vegan": False, "description": "Chilled Madurai-style milk drink with almond gum and ice cream"},
            {"name": "Payasam", "price": 80, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Traditional vermicelli kheer with cashews"},
        ],
    },
    {
        "place_id": "seed_murugan_idli_besant",
        "name": "Murugan Idli Shop",
        "address": "77, Besant Avenue Road, Besant Nagar, Chennai 600090",
        "lat": 13.0750,
        "lng": 80.2750,
        "rating": 4.5,
        "price_level": 1,
        "cuisine_tags": "south-indian,vegetarian,breakfast",
        "is_open": True,
        "phone": "+91-44-24913455",
        "photo_url": "",
        "dishes": [
            {"name": "Soft Idli", "price": 60, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Melt-in-mouth steamed rice cakes, their signature dish"},
            {"name": "Ghee Roast Dosa", "price": 100, "category": "Main Course", "is_veg": True, "is_vegan": False, "description": "Extra crispy dosa roasted in pure ghee"},
            {"name": "Podi Idli", "price": 80, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Idli tossed in spicy gunpowder (podi) with sesame oil"},
            {"name": "Onion Uttapam", "price": 90, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Thick rice pancake topped with onions and green chillies"},
            {"name": "Sambar Vada", "price": 70, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Crispy lentil vada dunked in hot sambar"},
            {"name": "Rava Dosa", "price": 110, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Crispy semolina crepe with pepper and cumin"},
            {"name": "Sweet Pongal", "price": 80, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Sweet rice and lentil dish with jaggery, ghee and cashews"},
            {"name": "Buttermilk", "price": 40, "category": "Beverages", "is_veg": True, "is_vegan": False, "description": "Spiced churned yogurt drink, refreshing coolant"},
        ],
    },
    {
        "place_id": "seed_pind_chennai_nungambakkam",
        "name": "Pind Chennai",
        "address": "42, Khader Nawaz Khan Road, Nungambakkam, Chennai 600006",
        "lat": 13.0850,
        "lng": 80.2800,
        "rating": 4.0,
        "price_level": 3,
        "cuisine_tags": "north-indian,mughlai,punjabi",
        "is_open": True,
        "phone": "+91-44-28335566",
        "photo_url": "",
        "dishes": [
            {"name": "Butter Chicken", "price": 340, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Creamy tomato-based chicken curry with butter and cream"},
            {"name": "Dal Makhani", "price": 220, "category": "Main Course", "is_veg": True, "is_vegan": False, "description": "Slow-cooked black lentils with butter and cream"},
            {"name": "Garlic Naan", "price": 70, "category": "Breads", "is_veg": True, "is_vegan": False, "description": "Soft tandoor bread with garlic and butter"},
            {"name": "Paneer Tikka", "price": 260, "category": "Starters", "is_veg": True, "is_vegan": False, "description": "Marinated cottage cheese grilled in tandoor"},
            {"name": "Chicken Tikka", "price": 280, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Juicy chicken chunks marinated in yogurt and spices"},
            {"name": "Mutton Rogan Josh", "price": 380, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Kashmiri-style mutton curry with aromatic spices"},
            {"name": "Chole Bhature", "price": 180, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Spicy chickpea curry with fluffy fried bread"},
            {"name": "Lassi", "price": 90, "category": "Beverages", "is_veg": True, "is_vegan": False, "description": "Thick yogurt drink, sweet or salted"},
            {"name": "Gulab Jamun", "price": 80, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Deep-fried milk dumplings soaked in rose sugar syrup"},
            {"name": "Biryani (Veg)", "price": 220, "category": "Biryani", "is_veg": True, "is_vegan": True, "description": "Fragrant basmati rice with seasonal vegetables and spices"},
        ],
    },
    {
        "place_id": "seed_azzuri_bay_ecr",
        "name": "Azzuri Bay",
        "address": "19/4, East Coast Road, Injambakkam, Chennai 600115",
        "lat": 13.0700,
        "lng": 80.2620,
        "rating": 4.2,
        "price_level": 4,
        "cuisine_tags": "italian,continental,cafe",
        "is_open": True,
        "phone": "+91-44-24491234",
        "photo_url": "",
        "dishes": [
            {"name": "Margherita Pizza", "price": 450, "category": "Pizza", "is_veg": True, "is_vegan": False, "description": "Classic pizza with fresh mozzarella, tomato sauce and basil"},
            {"name": "Penne Arrabiata", "price": 380, "category": "Pasta", "is_veg": True, "is_vegan": True, "description": "Penne in spicy tomato sauce with chili flakes"},
            {"name": "Grilled Chicken Steak", "price": 650, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Herb-marinated chicken breast with grilled vegetables"},
            {"name": "Caesar Salad", "price": 320, "category": "Starters", "is_veg": True, "is_vegan": False, "description": "Romaine lettuce with caesar dressing, croutons and parmesan"},
            {"name": "Fish and Chips", "price": 520, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Beer-battered fish with crispy fries and tartar sauce"},
            {"name": "Tiramisu", "price": 350, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Classic Italian coffee-flavored layered dessert"},
            {"name": "Bruschetta", "price": 280, "category": "Starters", "is_veg": True, "is_vegan": True, "description": "Toasted bread topped with fresh tomatoes, basil and olive oil"},
            {"name": "Seafood Risotto", "price": 580, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Creamy arborio rice with prawns, squid and mussels"},
            {"name": "Cappuccino", "price": 180, "category": "Beverages", "is_veg": True, "is_vegan": False, "description": "Rich espresso with steamed milk foam"},
            {"name": "Chocolate Lava Cake", "price": 320, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Warm chocolate cake with molten center and vanilla ice cream"},
        ],
    },
    {
        "place_id": "seed_nair_mess_mylapore",
        "name": "Nair Mess",
        "address": "21, Kutchery Road, Mylapore, Chennai 600004",
        "lat": 13.0900,
        "lng": 80.2680,
        "rating": 4.4,
        "price_level": 1,
        "cuisine_tags": "kerala,non-veg,home-style",
        "is_open": False,
        "phone": "+91-98412-33456",
        "photo_url": "",
        "dishes": [
            {"name": "Kerala Meals", "price": 130, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Full meals with rice, fish curry, thoran, sambar and payasam"},
            {"name": "Fish Fry (Seer Fish)", "price": 200, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Crispy pan-fried seer fish with Kerala spice marinade"},
            {"name": "Appam with Stew", "price": 120, "category": "Breakfast", "is_veg": False, "is_vegan": False, "description": "Lacy rice pancake with coconut milk chicken stew"},
            {"name": "Prawn Masala", "price": 250, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Prawns in thick coconut and tomato masala"},
            {"name": "Chicken Roast", "price": 220, "category": "Main Course", "is_veg": False, "is_vegan": False, "description": "Dry roasted chicken with Kerala spices and curry leaves"},
            {"name": "Puttu and Kadala", "price": 80, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Steamed rice cake cylinders with black chickpea curry"},
            {"name": "Malabar Parotta", "price": 50, "category": "Breads", "is_veg": True, "is_vegan": True, "description": "Flaky layered Kerala-style flatbread"},
            {"name": "Payasam", "price": 60, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Traditional vermicelli and milk dessert with cardamom"},
        ],
    },
    {
        "place_id": "seed_banana_leaf_adyar",
        "name": "The Banana Leaf",
        "address": "55, LB Road, Adyar, Chennai 600020",
        "lat": 13.0810,
        "lng": 80.2550,
        "rating": 3.9,
        "price_level": 2,
        "cuisine_tags": "south-indian,chinese,multi-cuisine",
        "is_open": True,
        "phone": "+91-44-24456677",
        "photo_url": "",
        "dishes": [
            {"name": "Veg Fried Rice", "price": 160, "category": "Chinese", "is_veg": True, "is_vegan": True, "description": "Wok-tossed rice with mixed vegetables and soy sauce"},
            {"name": "Chicken Fried Rice", "price": 200, "category": "Chinese", "is_veg": False, "is_vegan": False, "description": "Stir-fried rice with chicken, eggs and vegetables"},
            {"name": "Gobi Manchurian", "price": 150, "category": "Chinese", "is_veg": True, "is_vegan": True, "description": "Crispy cauliflower in tangy Indo-Chinese sauce"},
            {"name": "Egg Fried Rice", "price": 150, "category": "Chinese", "is_veg": False, "is_vegan": False, "description": "Simple fried rice with scrambled egg"},
            {"name": "Chilli Chicken", "price": 220, "category": "Chinese", "is_veg": False, "is_vegan": False, "description": "Spicy Indo-Chinese chicken with bell peppers"},
            {"name": "South Indian Thali", "price": 180, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Complete meal with rice, sambar, rasam, kootu and dessert"},
            {"name": "Noodles (Veg)", "price": 140, "category": "Chinese", "is_veg": True, "is_vegan": True, "description": "Hakka noodles with vegetables and Indo-Chinese seasoning"},
            {"name": "Chicken Noodles", "price": 180, "category": "Chinese", "is_veg": False, "is_vegan": False, "description": "Stir-fried noodles with chicken and vegetables"},
            {"name": "Paneer 65", "price": 190, "category": "Starters", "is_veg": True, "is_vegan": False, "description": "Deep-fried spiced paneer cubes with curry leaves"},
            {"name": "Sweet Corn Soup", "price": 100, "category": "Starters", "is_veg": True, "is_vegan": True, "description": "Thick and creamy corn soup Indo-Chinese style"},
            {"name": "Masala Papad", "price": 60, "category": "Starters", "is_veg": True, "is_vegan": True, "description": "Crispy papad topped with onion, tomato and chaat masala"},
            {"name": "Ice Cream Sundae", "price": 120, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Three scoops with chocolate sauce and nuts"},
        ],
    },
    {
        "place_id": "seed_zaitoon_alwarpet",
        "name": "Zaitoon",
        "address": "74, Cathedral Road, Alwarpet, Chennai 600018",
        "lat": 13.0770,
        "lng": 80.2730,
        "rating": 4.2,
        "price_level": 2,
        "cuisine_tags": "biryani,mughlai,kebabs",
        "is_open": True,
        "phone": "+91-44-28112233",
        "photo_url": "",
        "dishes": [
            {"name": "Chicken Biryani", "price": 250, "category": "Biryani", "is_veg": False, "is_vegan": False, "description": "Signature Chennai-style chicken biryani with seeraga samba rice"},
            {"name": "Mutton Biryani", "price": 320, "category": "Biryani", "is_veg": False, "is_vegan": False, "description": "Tender mutton pieces in fragrant spiced rice"},
            {"name": "Prawn Biryani", "price": 380, "category": "Biryani", "is_veg": False, "is_vegan": False, "description": "Juicy prawns layered with aromatic basmati rice"},
            {"name": "Veg Biryani", "price": 180, "category": "Biryani", "is_veg": True, "is_vegan": True, "description": "Mixed vegetable biryani with mint and saffron"},
            {"name": "Chicken Kebab", "price": 200, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Charcoal-grilled chicken kebabs with mint chutney"},
            {"name": "Mutton Seekh Kebab", "price": 280, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Minced mutton kebabs on skewers with spices"},
            {"name": "Chicken Shawarma", "price": 150, "category": "Starters", "is_veg": False, "is_vegan": False, "description": "Rolled pita with grilled chicken, garlic sauce and pickles"},
            {"name": "Raita", "price": 60, "category": "Sides", "is_veg": True, "is_vegan": False, "description": "Cool yogurt with cucumber and mint"},
            {"name": "Phirni", "price": 90, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Creamy rice pudding with cardamom and pistachios"},
            {"name": "Lime Soda", "price": 50, "category": "Beverages", "is_veg": True, "is_vegan": True, "description": "Fresh lime soda, sweet or salted"},
        ],
    },
    {
        "place_id": "seed_green_olive_velachery",
        "name": "Green Olive",
        "address": "12, 100 Feet Road, Velachery, Chennai 600042",
        "lat": 13.0830,
        "lng": 80.2850,
        "rating": 4.0,
        "price_level": 3,
        "cuisine_tags": "vegan,healthy,salads,cafe",
        "is_open": True,
        "phone": "+91-98400-12345",
        "photo_url": "",
        "dishes": [
            {"name": "Buddha Bowl", "price": 320, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Quinoa, roasted veggies, avocado, chickpeas with tahini dressing"},
            {"name": "Avocado Toast", "price": 250, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Sourdough toast with smashed avocado, seeds and microgreens"},
            {"name": "Green Smoothie Bowl", "price": 220, "category": "Breakfast", "is_veg": True, "is_vegan": True, "description": "Spinach, banana, mango blend topped with granola and berries"},
            {"name": "Falafel Wrap", "price": 280, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Crispy falafel in whole wheat wrap with hummus and veggies"},
            {"name": "Mushroom Quinoa Risotto", "price": 350, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Creamy quinoa risotto with wild mushrooms and truffle oil"},
            {"name": "Cold Pressed Juice", "price": 180, "category": "Beverages", "is_veg": True, "is_vegan": True, "description": "Fresh cold pressed juice - orange, carrot, ginger blend"},
            {"name": "Vegan Chocolate Mousse", "price": 200, "category": "Desserts", "is_veg": True, "is_vegan": True, "description": "Rich chocolate mousse made with coconut cream and dates"},
            {"name": "Mediterranean Salad", "price": 260, "category": "Starters", "is_veg": True, "is_vegan": True, "description": "Mixed greens with olives, sun-dried tomatoes and balsamic"},
        ],
    },
    {
        "place_id": "seed_rayars_mess_triplicane",
        "name": "Rayar's Mess",
        "address": "31, Triplicane High Road, Triplicane, Chennai 600005",
        "lat": 13.0860,
        "lng": 80.2710,
        "rating": 4.6,
        "price_level": 1,
        "cuisine_tags": "south-indian,traditional,vegetarian",
        "is_open": True,
        "phone": "+91-44-28441234",
        "photo_url": "",
        "dishes": [
            {"name": "Full Meals (Unlimited)", "price": 100, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Traditional unlimited South Indian thali on banana leaf"},
            {"name": "Curd Rice", "price": 60, "category": "Main Course", "is_veg": True, "is_vegan": False, "description": "Cool tempered yogurt rice, a South Indian staple"},
            {"name": "Sambar Rice", "price": 80, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Rice mixed with home-style sambar"},
            {"name": "Rasam Rice", "price": 70, "category": "Main Course", "is_veg": True, "is_vegan": True, "description": "Rice with tangy pepper-tamarind rasam"},
            {"name": "Paruppu Payasam", "price": 50, "category": "Desserts", "is_veg": True, "is_vegan": False, "description": "Traditional lentil and jaggery dessert"},
            {"name": "Appalam", "price": 20, "category": "Sides", "is_veg": True, "is_vegan": True, "description": "Crispy thin papadum, flame-roasted"},
            {"name": "Mor Kuzhambu Rice", "price": 80, "category": "Main Course", "is_veg": True, "is_vegan": False, "description": "Rice with tangy yogurt-based curry"},
            {"name": "Kootu Curry", "price": 70, "category": "Sides", "is_veg": True, "is_vegan": True, "description": "Lentil and vegetable curry with coconut"},
        ],
    },
]


def seed_database(engine):
    """Seed the database with sample Chennai restaurant data."""
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import Session as SessionClass

    with SessionClass(bind=engine) as db:
        existing = db.query(Restaurant).filter(Restaurant.place_id.startswith("seed_")).first()
        if existing:
            return  # Already seeded

        for restaurant_data in SEED_RESTAURANTS:
            dishes_data = restaurant_data.pop("dishes")
            restaurant = Restaurant(**restaurant_data, cached_at=datetime.utcnow())
            db.add(restaurant)
            db.flush()

            for dish_data in dishes_data:
                dish = Dish(
                    restaurant_place_id=restaurant.place_id,
                    cached_at=datetime.utcnow(),
                    **dish_data,
                )
                db.add(dish)

            # Restore dishes to the dict so it can be re-used
            restaurant_data["dishes"] = dishes_data

        db.commit()
        print(f"[seed] Seeded {len(SEED_RESTAURANTS)} restaurants with dishes.")

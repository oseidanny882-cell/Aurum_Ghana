CATEGORIES = [
    {"slug": "rings", "name": "Rings", "description": "Elegant rings for every occasion",
     "image": "/images/category-rings.jpg", "display_order": 1},
    {"slug": "necklaces", "name": "Necklaces", "description": "Stunning necklaces and pendants",
     "image": "/images/category-necklaces.jpg", "display_order": 2},
    {"slug": "earrings", "name": "Earrings", "description": "Beautiful earrings to complete your look",
     "image": "/images/category-earrings.jpg", "display_order": 3},
    {"slug": "bracelets", "name": "Bracelets", "description": "Graceful bracelets for every wrist",
     "image": "/images/category-bracelets.jpg", "display_order": 4},
    {"slug": "anklets", "name": "Anklets", "description": "Delicate anklets for a touch of charm",
     "image": "/images/category-anklets.jpg", "display_order": 5},
    {"slug": "watches", "name": "Watches", "description": "Luxurious timepieces",
     "image": "/images/category-watches.jpg", "display_order": 6},
    {"slug": "sets", "name": "Jewelry Sets", "description": "Matching sets for the perfect look",
     "image": "/images/category-sets.jpg", "display_order": 7},
]

NAMES = {
    "rings": ["Royal Adinkra Ring", "Golden Kente Ring", "Akoma Ring", "Sankofa Band", "Dwen Gold Ring",
              "Gye Nyame Signet", "Dwennimmen Ring", "Mate Masie Band", "Fawohodie Ring", "Nea Onnim Ring"],
    "necklaces": ["Adinkra Pendant", "Kente Bead Necklace", "Golden Ankh", "Gye Nyame Pendant",
                  "Aya Pendant", "Akoma Chain", "Osrane Pearl", "Dame Dame Chain", "Tabono Necklace", "Epa Pendant"],
    "earrings": ["Adinkra Studs", "Golden Hoops", "Akoma Drop", "Fawohodie Studs",
                 "Kente Bead Earrings", "Gye Nyame Hoops", "Osrane Drop Earrings", "Mate Masie Dangles",
                 "Dwennimmen Studs", "Aya Mini Hoops"],
    "bracelets": ["Adinkra Bangle", "Golden Charm Bracelet", "Akoma Tennis", "Sankofa Cuff",
                  "Kente Bead Bangle", "Dwen Tennis", "Gye Nyame Chain", "Epa Cuff",
                  "Mate Masie Bangle", "Fawohodie Charm"],
    "anklets": ["Golden Charm Anklet", "Adinkra Chain", "Akoma Bead Anklet", "Kente Anklet",
                "Aya Drop Anklet", "Mate Masie Anklet", "Gye Nyame Anklet", "Osrane Anklet",
                "Sankofa Anklet", "Dwen Anklet"],
    "watches": ["Adinkra Gold Watch", "Kente Chronograph", "Akoma Timepiece", "Sankofa Classic",
                "Gye Nyame Diver", "Aya Automatic", "Mate Masie Dress", "Dwen GMT",
                "Osrane Skeleton", "Fawohodie Vintage"],
    "sets": ["Adinkra Bridal Set", "Kente Royal Set", "Akoma Wedding Set", "Gye Nyame Set",
             "Sankofa Gift Set", "Aya Promise Set", "Mate Masie Trio", "Dwen Heritage Set",
             "Osrane Complete", "Fawohodie Premium"],
}

MATERIALS = ["18k Gold-plated", "Sterling Silver", "Brass with Gold finish",
             "Mixed metals", "9k Gold", "Rose Gold-plated", "Vermeil"]
COLORS = ["Gold", "Rose Gold", "Silver", "Mixed", "Antique Gold", "Black Rhodium"]


def seed():
    app = create_app()
    with app.app_context():
        # Apply Alembic migrations to bring the DB schema up to date.
        # For a fresh DB, run: py -3.12 -m flask db upgrade
        # db.create_all() is intentionally omitted -- use migrations going forward.
        print("Ensuring database schema is up to date (via Alembic)...")
        from alembic import command
        from alembic.config import Config
        alembic_cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        print("  Migrations applied. Tables ready.")

        print("Seeding categories...")
        cat_map = {}
        for c in CATEGORIES:
            existing = Category.query.filter_by(slug=c["slug"]).first()
            if existing:
                cat_map[c["slug"]] = existing
                continue
            new_cat = Category(**c)
            db.session.add(new_cat)
            db.session.flush()
            cat_map[c["slug"]] = new_cat
        db.session.commit()

        print("Seeding products...")
        i = 0
        for cat_slug, name_list in NAMES.items():
            cat = cat_map[cat_slug]
            for name in name_list:
                pid = f"sku-{cat_slug}-{i + 1}"
                if Product.query.get(pid):
                    i += 1
                    continue
                price = 80 + (i * 17) % 800 + 0.99
                has_discount = (i % 7 == 0)
                discount_price = round(price * 0.75, 2) if has_discount else None
                stock = 5 + (i % 30)
                product = Product(
                    id=pid,
                    sku=f"AG-{cat_slug.upper()[:3]}-{str(i + 1).zfill(4)}",
                    slug=f"{cat_slug}-{name.lower().replace(' ', '-').replace(chr(38), 'and').replace('/', '-')}",
                    name=name,
                    description=f"Handcrafted {name} - premium Ghanaian jewelry from Aurum. Each piece is meticulously made by skilled local artisans using {MATERIALS[i % len(MATERIALS)]}.",
                    category_id=cat.id,
                    price=price,
                    discount_price=discount_price,
                    currency="GHS",
                    stock=stock,
                    image=f"/images/{cat_slug}-{(i % 10) + 1}.jpg",
                    images=[f"/images/{cat_slug}-{(i % 10) + 1}.jpg", f"/images/{cat_slug}-{(i % 10) + 2}.jpg"],
                    material=MATERIALS[i % len(MATERIALS)],
                    color=COLORS[i % len(COLORS)],
                    is_new=(i < 12),
                    is_best=(i % 5 == 0),
                    is_featured=(i % 4 == 0),
                    is_active=True,
                    tags=[cat_slug, "handmade", "ghana"],
                    rating_avg=round(4.0 + (i % 10) / 10, 2),
                    review_count=(i * 3) % 50,
                )
                db.session.add(product)
                i += 1
        db.session.commit()
        print(f"  Seeded {i} products")

        print("Seeding admin user...")
        from backend.extensions import bcrypt
        admin_email = "admin@aurum-ghana.local"
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                email=admin_email,
                password_hash=bcrypt.generate_password_hash("Admin12345!").decode("utf-8"),
                first_name="Admin", last_name="Aurum",
                role="admin", is_verified=True, is_active=True,
            )
            db.session.add(admin)
            db.session.commit()
            print(f"  Created admin: {admin_email} / Admin12345!")
        else:
            print("  Admin already exists")

        print("\nSeed complete.")


if __name__ == "__main__":
    seed()

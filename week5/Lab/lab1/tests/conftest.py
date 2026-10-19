import pytest
import sys
from pathlib import Path

# Ensure week5/Lab/lab1 is in sys.path
LAB1_DIR = Path(__file__).resolve().parent.parent
if str(LAB1_DIR) not in sys.path:
    sys.path.insert(0, str(LAB1_DIR))

from app import create_app
from models import db, Category, Book
from seed import CATEGORIES_DATA, BOOKS_DATA


@pytest.fixture(scope="function")
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # Seed categories
        cat_map = {}
        for cat_data in CATEGORIES_DATA:
            cat = Category(name=cat_data["name"], slug=cat_data["slug"])
            db.session.add(cat)
            db.session.flush()
            cat_map[cat.slug] = cat

        # Seed books
        for b in BOOKS_DATA:
            cat = cat_map[b["category_slug"]]
            book = Book(
                title=b["title"],
                author=b["author"],
                isbn=b["isbn"],
                price_vnd=b["price"],
                category_id=cat.id,
            )
            db.session.add(book)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

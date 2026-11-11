import pytest

from product_api import create_app
from product_api.extensions import db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "LOG_LEVEL": "WARNING",
    })
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def product_data():
    return {"sku": "BOOK-01", "name": "Sách SOA", "price_cents": 15000, "qty_in_stock": 10}


@pytest.fixture
def product(client, product_data):
    response = client.post("/api/v1/products", json=product_data)
    assert response.status_code == 201
    return response.get_json()

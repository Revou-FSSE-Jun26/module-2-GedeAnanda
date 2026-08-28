import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import User, Category, Product


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def _make_user(email, role):
    user = User(
        username=email.split('@')[0],
        email=email,
        password_hash=generate_password_hash('password123'),
        role=role
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def _token_for(client, email):
    response = client.post('/auth/login', json={
        "email": email,
        "password": "password123"
    })
    return response.get_json()['data']['access_token']


@pytest.fixture
def admin_headers(client, db):
    _make_user('admin@test.com', 'admin')
    token = _token_for(client, 'admin@test.com')
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_headers(client, db):
    _make_user('customer@test.com', 'customer')
    token = _token_for(client, 'customer@test.com')
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_category(db):
    category = Category(name='Electronics', description='Gadgets')
    _db.session.add(category)
    _db.session.commit()
    return category


@pytest.fixture
def sample_product(db, sample_category):
    product = Product(
        category_id=sample_category.id,
        name='Laptop',
        price=1000,
        stock=10
    )
    _db.session.add(product)
    _db.session.commit()
    return product
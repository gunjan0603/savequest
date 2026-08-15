import pytest
from app import create_app
from models import db

@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}", "SECRET_KEY": "test"})
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

from models import db, User

def test_signup_login_logout(client, app):
    response = client.post('/api/auth/signup', json={'name':'Test User','email':'test@example.com','password':'secret123'})
    assert response.status_code == 201
    assert response.json['user']['name'] == 'Test User'
    response = client.post('/api/auth/logout')
    assert response.status_code == 200
    response = client.post('/api/auth/login', json={'email':'test@example.com','password':'secret123'})
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.password_hash != 'secret123'

def test_duplicate_email_rejected(client):
    client.post('/api/auth/signup', json={'name':'Test','email':'test@example.com','password':'secret123'})
    response = client.post('/api/auth/signup', json={'name':'Other','email':'test@example.com','password':'secret123'})
    assert response.status_code == 409

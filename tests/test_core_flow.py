from models import db, User, Friendship

def signup(client, name, email):
    return client.post('/api/auth/signup', json={'name':name,'email':email,'password':'secret123'})

def test_full_core_flow(client, app):
    assert signup(client, 'Aanya', 'aanya@example.com').status_code == 201
    goal = client.post('/api/goals', json={'name':'Laptop','target_amount':30000,'deadline':'2026-12-01'})
    assert goal.status_code == 201
    goal_id = goal.json['goal']['id']
    entry = client.post(f'/api/goals/{goal_id}/savings', json={'amount':500,'date_logged':'2026-08-03','note':'Saved'})
    assert entry.status_code == 201
    assert entry.json['entry']['points_earned'] == 50
    assert entry.json['goal']['saved_amount'] == 500
    points = client.get('/api/points')
    assert points.json['total_points'] == 50
    detail = client.get(f'/api/goals/{goal_id}')
    assert detail.status_code == 200
    assert len(detail.json['entries']) == 1

def test_consistency_bonus(client):
    signup(client, 'Aanya', 'aanya@example.com')
    goal = client.post('/api/goals', json={'name':'Trip','target_amount':1000,'deadline':'2026-12-01'}).json['goal']
    client.post(f"/api/goals/{goal['id']}/savings", json={'amount':300,'date_logged':'2026-08-03'})
    second = client.post(f"/api/goals/{goal['id']}/savings", json={'amount':300,'date_logged':'2026-08-10'})
    assert second.json['entry']['points_earned'] == 55
    assert second.json['entry']['is_streak_bonus'] is True

def test_goal_access_is_isolated(client, app):
    signup(client, 'Aanya', 'aanya@example.com')
    goal = client.post('/api/goals', json={'name':'Private','target_amount':100,'deadline':'2026-12-01'}).json['goal']
    client.post('/api/auth/logout')
    signup(client, 'Rohan', 'rohan@example.com')
    assert client.get(f"/api/goals/{goal['id']}").status_code == 404

def test_leaderboard_includes_self_and_friends(client, app):
    signup(client, 'Aanya', 'aanya@example.com')
    with app.app_context():
        aanya = User.query.filter_by(email='aanya@example.com').first()
        rohan = User(name='Rohan', email='rohan@example.com'); rohan.set_password('secret123'); db.session.add(rohan); db.session.commit()
        db.session.add(Friendship(user_id=aanya.id, friend_id=rohan.id)); db.session.commit()
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    assert len(response.json['leaderboard']) == 2

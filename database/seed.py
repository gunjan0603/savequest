from app import create_app
from models import db, User, Goal, SavingsEntry, Friendship

app = create_app()

with app.app_context():
    if User.query.count() == 0:
        users = [
            ("Aanya Sharma", "aanya@example.com"),
            ("Rohan Mehta", "rohan@example.com"),
            ("Priya Singh", "priya@example.com"),
        ]
        created = []
        for name, email in users:
            user = User(name=name, email=email)
            user.set_password("demo123")
            db.session.add(user)
            created.append(user)
        db.session.flush()

        g1 = Goal(user_id=created[0].id, name="New Laptop", target_amount=30000, deadline="2026-12-01")
        g2 = Goal(user_id=created[0].id, name="Goa Trip", target_amount=8000, deadline="2026-10-15")
        g3 = Goal(user_id=created[1].id, name="Gaming Setup", target_amount=20000, deadline="2026-11-30")
        db.session.add_all([g1, g2, g3])
        db.session.flush()
        db.session.add_all([
            SavingsEntry(goal_id=g1.id, amount=500, date_logged="2026-08-03", points_earned=50),
            SavingsEntry(goal_id=g1.id, amount=300, date_logged="2026-08-10", points_earned=55, is_streak_bonus=True, note="2nd week in a row!"),
            SavingsEntry(goal_id=g3.id, amount=1200, date_logged="2026-08-09", points_earned=120),
        ])
        db.session.add_all([
            Friendship(user_id=created[0].id, friend_id=created[1].id),
            Friendship(user_id=created[0].id, friend_id=created[2].id),
            Friendship(user_id=created[1].id, friend_id=created[0].id),
            Friendship(user_id=created[2].id, friend_id=created[0].id),
        ])
        db.session.commit()
        print("Seeded demo users. Password for all: demo123")
    else:
        print("Database already has users; nothing to seed.")

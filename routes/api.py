from datetime import date
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from models import db, User, Goal, SavingsEntry, Friendship
from points_logic import calculate_goal_progress, calculate_points

api_bp = Blueprint("api", __name__)


def goal_payload(goal):
    progress = calculate_goal_progress(goal)
    return {
        "id": goal.id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "saved_amount": progress["saved_amount"],
        "progress_percentage": progress["percentage"],
        "deadline": goal.deadline,
        "is_completed": progress["is_completed"],
    }


def user_payload(user):
    return {"id": user.id, "name": user.name, "email": user.email}


def total_points(user_id):
    value = db.session.query(db.func.coalesce(db.func.sum(SavingsEntry.points_earned), 0)).join(Goal).filter(Goal.user_id == user_id).scalar()
    return int(value or 0)


@api_bp.post("/auth/signup")
def api_signup():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not name or not email or not password:
        return jsonify(error="Name, email and password are required"), 400
    if len(password) < 6:
        return jsonify(error="Password must be at least 6 characters"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="An account with this email already exists"), 409
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify(message="Account created successfully", user=user_payload(user)), 201


@api_bp.post("/auth/login")
def api_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        return jsonify(error="Email and password are required"), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(error="Invalid email or password"), 401
    login_user(user)
    return jsonify(message="Login successful", user=user_payload(user)), 200


@api_bp.post("/auth/logout")
@login_required
def api_logout():
    logout_user()
    return jsonify(message="Logged out successfully"), 200


@api_bp.get("/goals")
@login_required
def api_goals():
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.deadline.asc()).all()
    return jsonify(goals=[goal_payload(goal) for goal in goals])


@api_bp.post("/goals")
@login_required
def api_create_goal():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    deadline = str(data.get("deadline", "")).strip()
    try:
        target = float(data.get("target_amount"))
    except (TypeError, ValueError):
        target = 0
    if not name or not deadline or target <= 0:
        return jsonify(error="Name, target amount and deadline are required; target amount must be greater than 0"), 400
    try:
        date.fromisoformat(deadline)
    except ValueError:
        return jsonify(error="Invalid deadline"), 400
    goal = Goal(user_id=current_user.id, name=name, target_amount=target, deadline=deadline)
    db.session.add(goal)
    db.session.commit()
    return jsonify(message="Goal created successfully", goal=goal_payload(goal)), 201


@api_bp.get("/goals/<int:goal_id>")
@login_required
def api_goal_detail(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify(error="Goal not found"), 404
    entries = SavingsEntry.query.filter_by(goal_id=goal.id).order_by(SavingsEntry.date_logged.desc(), SavingsEntry.id.desc()).all()
    return jsonify(goal=goal_payload(goal), entries=[{
        "id": e.id, "amount": e.amount, "date_logged": e.date_logged,
        "points_earned": e.points_earned, "is_streak_bonus": bool(e.is_streak_bonus), "note": e.note
    } for e in entries])


@api_bp.post("/goals/<int:goal_id>/savings")
@login_required
def api_log_savings(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify(error="Goal not found"), 404
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        amount = 0
    date_logged = str(data.get("date_logged", date.today().isoformat())).strip()
    note = data.get("note")
    if amount <= 0:
        return jsonify(error="Savings amount must be greater than 0"), 400
    try:
        date.fromisoformat(date_logged)
    except ValueError:
        return jsonify(error="Invalid savings date"), 400
    previous_entries = SavingsEntry.query.filter_by(goal_id=goal.id).all()
    points, streak_bonus = calculate_points(amount, previous_entries, date_logged)
    entry = SavingsEntry(goal_id=goal.id, amount=amount, date_logged=date_logged, points_earned=points, is_streak_bonus=streak_bonus, note=note)
    db.session.add(entry)
    db.session.flush()
    progress = calculate_goal_progress(goal)
    goal.is_completed = progress["is_completed"]
    db.session.commit()
    return jsonify(message="Savings logged successfully", entry={
        "id": entry.id, "amount": entry.amount, "date_logged": entry.date_logged,
        "points_earned": entry.points_earned, "is_streak_bonus": bool(entry.is_streak_bonus)
    }, goal=goal_payload(goal), points={"earned": points, "total": total_points(current_user.id)}), 201


@api_bp.get("/points")
@login_required
def api_points():
    return jsonify(user_id=current_user.id, total_points=total_points(current_user.id))


@api_bp.get("/leaderboard")
@login_required
def api_leaderboard():
    friend_ids = [f.friend_id for f in Friendship.query.filter_by(user_id=current_user.id).all()]
    user_ids = list(dict.fromkeys(friend_ids + [current_user.id]))
    ranking = []
    for user_id in user_ids:
        user = db.session.get(User, user_id)
        if user:
            ranking.append({"user_id": user.id, "name": user.name, "total_points": total_points(user.id)})
    ranking.sort(key=lambda x: (-x["total_points"], x["name"].lower()))
    for i, item in enumerate(ranking, start=1):
        item["rank"] = i
    me = next(item for item in ranking if item["user_id"] == current_user.id)
    return jsonify(leaderboard=ranking, current_user={"rank": me["rank"], "total_points": me["total_points"]})

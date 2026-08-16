from flask import Flask, jsonify, redirect, render_template, request, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from config import Config
from models import db, User, Goal, SavingsEntry, Friendship
from points_logic import calculate_points, calculate_goal_progress, has_previous_week_entry
from routes.api import api_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to continue."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(error="Authentication required"), 401
        return redirect(url_for("login", next=request.path))

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_globals():
        return {"app_name": "SaveQuest"}

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("landing.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or not email or not password:
                flash("Please fill in all fields.", "error")
            elif len(password) < 6:
                flash("Password must be at least 6 characters.", "error")
            elif User.query.filter_by(email=email).first():
                flash("An account with this email already exists.", "error")
            else:
                user = User(name=name, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Welcome to SaveQuest! Your first quest starts now.", "success")
                return redirect(url_for("dashboard"))
        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("dashboard"))
            flash("Invalid email or password.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.is_completed.asc(), Goal.deadline.asc()).all()
        total_points = db.session.query(db.func.coalesce(db.func.sum(SavingsEntry.points_earned), 0)).join(Goal).filter(Goal.user_id == current_user.id).scalar() or 0
        for goal in goals:
            goal.display_progress = calculate_goal_progress(goal)
        return render_template("dashboard.html", goals=goals, total_points=int(total_points))

    @app.route("/goals/new", methods=["GET", "POST"])
    @login_required
    def new_goal():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            deadline = request.form.get("deadline", "").strip()
            try:
                target = float(request.form.get("target_amount", ""))
            except ValueError:
                target = 0
            if not name or not deadline or target <= 0:
                flash("Add a name, valid target amount, and deadline.", "error")
            else:
                goal = Goal(user_id=current_user.id, name=name, target_amount=target, deadline=deadline)
                db.session.add(goal)
                db.session.commit()
                flash("Goal created. Now make your first saving move!", "success")
                return redirect(url_for("goal_detail", goal_id=goal.id))
        return render_template("new_goal.html")

    @app.get("/goals/<int:goal_id>")
    @login_required
    def goal_detail(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
        entries = SavingsEntry.query.filter_by(goal_id=goal.id).order_by(SavingsEntry.date_logged.desc(), SavingsEntry.id.desc()).all()
        progress = calculate_goal_progress(goal)
        total_points = db.session.query(db.func.coalesce(db.func.sum(SavingsEntry.points_earned), 0)).join(Goal).filter(Goal.user_id == current_user.id).scalar() or 0
        return render_template("goal_detail.html", goal=goal, entries=entries, progress=progress, total_points=int(total_points))

    @app.get("/leaderboard")
    @login_required
    def leaderboard():
        rows = []
        friend_ids = [f.friend_id for f in Friendship.query.filter_by(user_id=current_user.id).all()]
        user_ids = list(dict.fromkeys(friend_ids + [current_user.id]))
        for user_id in user_ids:
            user = db.session.get(User, user_id)
            if not user:
                continue
            points = db.session.query(db.func.coalesce(db.func.sum(SavingsEntry.points_earned), 0)).join(Goal).filter(Goal.user_id == user.id).scalar() or 0
            rows.append({"user": user, "points": int(points)})
        rows.sort(key=lambda item: (-item["points"], item["user"].name.lower()))
        for index, row in enumerate(rows, start=1):
            row["rank"] = index
        return render_template("leaderboard.html", leaderboard=rows)

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return jsonify(error="Resource not found"), 404
        return render_template("error.html", code=404, message="We couldn't find that page."), 404

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify(error="Internal server error"), 500
        return render_template("error.html", code=500, message="Something went wrong. Please try again."), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

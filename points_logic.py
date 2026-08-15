from datetime import date, timedelta
from math import floor


def calculate_base_points(amount):
    """PRD-aligned simple formula: 10 points per completed ₹100 saved."""
    return floor(float(amount) / 100) * 10


def _week_key(value):
    return date.fromisoformat(value).isocalendar()[:2]


def has_previous_week_entry(entries, date_logged):
    current = date.fromisoformat(date_logged)
    previous = current - timedelta(days=7)
    target_week = _week_key(previous.isoformat())
    return any(_week_key(entry.date_logged) == target_week for entry in entries)


def calculate_points(amount, previous_entries, date_logged):
    base = calculate_base_points(amount)
    streak = has_previous_week_entry(previous_entries, date_logged)
    bonus = 25 if streak else 0
    return base + bonus, streak


def calculate_goal_progress(goal):
    saved = sum(entry.amount for entry in goal.savings_entries)
    percentage = 0 if goal.target_amount <= 0 else min(100, (saved / goal.target_amount) * 100)
    return {"saved_amount": round(saved, 2), "percentage": round(percentage, 2), "is_completed": saved >= goal.target_amount}

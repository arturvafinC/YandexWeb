from datetime import date, timedelta

from flask import Blueprint, abort, current_app, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import desc, func, or_

from app.db import db
from app.models import Mistake, MistakeType, Subject
from app.utils import status_counts


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    total = Mistake.query.filter_by(user_id=current_user.id).count()
    return render_template("dashboard.html", total=total, counts=status_counts(current_user.id))


@main_bp.route("/review")
@login_required
def review():
    today = date.today()
    mistakes = (
        Mistake.query.filter(Mistake.user_id == current_user.id)
        .filter(or_(Mistake.status == "Нужно повторить", Mistake.repeat_at <= today))
        .order_by(Mistake.repeat_at.asc().nullslast(), Mistake.created_at.desc())
        .all()
    )
    return render_template("review.html", mistakes=mistakes)


@main_bp.route("/review/<int:mistake_id>/postpone", methods=["POST"])
@login_required
def postpone_review(mistake_id):
    mistake = db.session.get(Mistake, mistake_id)
    if not mistake:
        abort(404)
    if mistake.user_id != current_user.id:
        current_app.logger.warning("Forbidden postpone attempt: user=%s mistake=%s", current_user.id, mistake_id)
        abort(403)
    mistake.repeat_at = date.today() + timedelta(days=3)
    if mistake.status == "Нужно повторить":
        mistake.status = "Разобрано"
    db.session.commit()
    current_app.logger.info("Review postponed: user=%s mistake=%s", current_user.id, mistake.id)
    return redirect(url_for("main.review"))


@main_bp.route("/statistics")
@login_required
def statistics():
    total = Mistake.query.filter_by(user_id=current_user.id).count()
    counts = status_counts(current_user.id)
    fixed_percent = round((counts["Исправлено"] / total) * 100, 1) if total else 0
    subjects = (
        db.session.query(Subject.name, func.count(Mistake.id).label("count"))
        .join(Mistake, Mistake.subject_id == Subject.id)
        .filter(Mistake.user_id == current_user.id)
        .group_by(Subject.name)
        .order_by(desc("count"))
        .all()
    )
    types = (
        db.session.query(MistakeType.name, func.count(Mistake.id).label("count"))
        .join(Mistake, Mistake.mistake_type_id == MistakeType.id)
        .filter(Mistake.user_id == current_user.id)
        .group_by(MistakeType.name)
        .order_by(desc("count"))
        .all()
    )
    return render_template(
        "statistics.html",
        total=total,
        counts=counts,
        fixed_percent=fixed_percent,
        subjects=subjects,
        types=types,
        worst_subject=subjects[0].name if subjects else "Нет данных",
        frequent_type=types[0].name if types else "Нет данных",
    )

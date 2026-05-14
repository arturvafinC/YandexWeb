from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.db import db
from app.forms import MistakeForm
from app.models import Mistake, MistakeType, Subject, Tag
from app.utils import save_upload, set_form_choices


mistakes_bp = Blueprint("mistakes", __name__, url_prefix="/mistakes")


def get_owned_mistake_or_abort(mistake_id):
    mistake = db.session.get(Mistake, mistake_id)
    if not mistake:
        abort(404)
    if mistake.user_id != current_user.id:
        current_app.logger.warning("Forbidden mistake access: user=%s mistake=%s", current_user.id, mistake_id)
        abort(403)
    return mistake


@mistakes_bp.route("")
@login_required
def list_mistakes():
    query = Mistake.query.filter_by(user_id=current_user.id)
    subject = request.args.get("subject")
    status = request.args.get("status")
    mistake_type = request.args.get("type")
    if subject:
        query = query.join(Subject).filter(Subject.name == subject)
    if status:
        query = query.filter(Mistake.status == status)
    if mistake_type:
        query = query.join(MistakeType).filter(MistakeType.name == mistake_type)
    mistakes = query.order_by(Mistake.created_at.desc()).all()
    return render_template(
        "mistakes/list.html",
        mistakes=mistakes,
        subjects=Subject.query.order_by(Subject.name).all(),
        types=MistakeType.query.order_by(MistakeType.name).all(),
    )


@mistakes_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_mistake():
    form = MistakeForm()
    set_form_choices(form)
    if form.validate_on_submit():
        try:
            image_path = save_upload(form.image.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("mistakes/create.html", form=form)
        mistake = Mistake(
            user_id=current_user.id,
            subject_id=form.subject_id.data,
            mistake_type_id=form.mistake_type_id.data,
            title=form.title.data.strip(),
            topic=form.topic.data.strip(),
            description=form.description.data,
            wrong_answer=form.wrong_answer.data,
            correct_answer=form.correct_answer.data,
            explanation=form.explanation.data,
            status=form.status.data,
            image_path=image_path,
            repeat_at=form.repeat_at.data,
        )
        mistake.tags = Tag.query.filter(Tag.id.in_(form.tag_ids.data)).all() if form.tag_ids.data else []
        db.session.add(mistake)
        db.session.commit()
        current_app.logger.info("Mistake created: user=%s mistake=%s", current_user.id, mistake.id)
        flash("Ошибка добавлена.", "success")
        return redirect(url_for("mistakes.detail", mistake_id=mistake.id))
    return render_template("mistakes/create.html", form=form)


@mistakes_bp.route("/<int:mistake_id>")
@login_required
def detail(mistake_id):
    mistake = get_owned_mistake_or_abort(mistake_id)
    return render_template("mistakes/detail.html", mistake=mistake)


@mistakes_bp.route("/<int:mistake_id>/edit", methods=["GET", "POST"])
@login_required
def edit(mistake_id):
    mistake = get_owned_mistake_or_abort(mistake_id)
    form = MistakeForm(obj=mistake)
    set_form_choices(form)
    if request.method == "GET":
        form.subject_id.data = mistake.subject_id
        form.mistake_type_id.data = mistake.mistake_type_id
        form.tag_ids.data = [tag.id for tag in mistake.tags]
    if form.validate_on_submit():
        try:
            image_path = save_upload(form.image.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("mistakes/edit.html", form=form, mistake=mistake)
        mistake.subject_id = form.subject_id.data
        mistake.mistake_type_id = form.mistake_type_id.data
        mistake.title = form.title.data.strip()
        mistake.topic = form.topic.data.strip()
        mistake.description = form.description.data
        mistake.wrong_answer = form.wrong_answer.data
        mistake.correct_answer = form.correct_answer.data
        mistake.explanation = form.explanation.data
        mistake.status = form.status.data
        mistake.repeat_at = form.repeat_at.data
        if image_path:
            mistake.image_path = image_path
        mistake.tags = Tag.query.filter(Tag.id.in_(form.tag_ids.data)).all() if form.tag_ids.data else []
        db.session.commit()
        current_app.logger.info("Mistake updated: user=%s mistake=%s", current_user.id, mistake.id)
        flash("Ошибка обновлена.", "success")
        return redirect(url_for("mistakes.detail", mistake_id=mistake.id))
    return render_template("mistakes/edit.html", form=form, mistake=mistake)


@mistakes_bp.route("/<int:mistake_id>/delete", methods=["POST"])
@login_required
def delete(mistake_id):
    mistake = get_owned_mistake_or_abort(mistake_id)
    db.session.delete(mistake)
    db.session.commit()
    current_app.logger.info("Mistake deleted: user=%s mistake=%s", current_user.id, mistake_id)
    flash("Ошибка удалена.", "success")
    return redirect(url_for("mistakes.list_mistakes"))


@mistakes_bp.route("/<int:mistake_id>/fix", methods=["POST"])
@login_required
def mark_fixed(mistake_id):
    mistake = get_owned_mistake_or_abort(mistake_id)
    mistake.status = "Исправлено"
    db.session.commit()
    current_app.logger.info("Mistake marked fixed: user=%s mistake=%s", current_user.id, mistake.id)
    return redirect(url_for("mistakes.detail", mistake_id=mistake.id))

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.db import db
from app.forms import ALLOWED_IMAGE_EXTENSIONS, STATUS_CHOICES
from app.models import Mistake, MistakeType, Subject, Tag


SUBJECTS = ["Математика", "Русский язык", "Информатика", "Английский язык", "Физика", "История"]
MISTAKE_TYPES = ["Невнимательность", "Не знаю правило", "Ошибка в формуле", "Ошибка в логике", "Не понял условие", "Техническая ошибка", "Другое"]
TAGS = ["ЕГЭ", "ОГЭ", "Сложное", "Повторить", "Теория", "Практика"]
STATUSES = [value for value, _label in STATUS_CHOICES]


def seed_reference_data():
    for model, names in ((Subject, SUBJECTS), (MistakeType, MISTAKE_TYPES), (Tag, TAGS)):
        for name in names:
            with db.session.no_autoflush:
                exists = model.query.filter_by(name=name).first()
            if exists:
                continue
            db.session.add(model(name=name))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Недопустимый формат файла")
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    file_storage.save(upload_dir / filename)
    return f"uploads/{filename}"


def set_form_choices(form):
    form.subject_id.choices = [(subject.id, subject.name) for subject in Subject.query.order_by(Subject.name).all()]
    form.mistake_type_id.choices = [(item.id, item.name) for item in MistakeType.query.order_by(MistakeType.name).all()]
    form.tag_ids.choices = [(tag.id, tag.name) for tag in Tag.query.order_by(Tag.name).all()]


def get_or_create(model, name):
    item = model.query.filter_by(name=name).first()
    if item:
        return item
    item = model(name=name)
    db.session.add(item)
    db.session.flush()
    return item


def parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def apply_mistake_json(mistake, data, full_update=False):
    required = ["title", "subject", "topic", "mistake_type", "status"] if full_update else []
    missing = [field for field in required if not data.get(field)]
    if missing:
        return f"Missing fields: {', '.join(missing)}"

    if "title" in data:
        mistake.title = (data.get("title") or "").strip()
    if "subject" in data:
        mistake.subject = get_or_create(Subject, data["subject"].strip())
    if "topic" in data:
        mistake.topic = (data.get("topic") or "").strip()
    if "mistake_type" in data:
        mistake.mistake_type = get_or_create(MistakeType, data["mistake_type"].strip())
    if "status" in data:
        if data["status"] not in STATUSES:
            return "Invalid status"
        mistake.status = data["status"]
    for field in ("description", "wrong_answer", "correct_answer", "explanation"):
        if field in data:
            setattr(mistake, field, data.get(field))
    if "repeat_at" in data:
        mistake.repeat_at = parse_date(data.get("repeat_at"))
    if "tags" in data:
        mistake.tags = [get_or_create(Tag, name.strip()) for name in data.get("tags", []) if name.strip()]

    if not mistake.title or not mistake.subject or not mistake.topic or not mistake.mistake_type or not mistake.status:
        return "Fields title, subject, topic, mistake_type and status are required"
    return None


def status_counts(user_id):
    rows = db.session.query(Mistake.status, func.count(Mistake.id)).filter_by(user_id=user_id).group_by(Mistake.status).all()
    result = {status: 0 for status in STATUSES}
    result.update(dict(rows))
    return result

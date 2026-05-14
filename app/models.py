from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db


mistake_tags = db.Table(
    "mistake_tags",
    db.Column("mistake_id", db.Integer, db.ForeignKey("mistakes.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    mistakes = db.relationship("Mistake", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    mistakes = db.relationship("Mistake", back_populates="subject")


class MistakeType(db.Model):
    __tablename__ = "mistake_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    mistakes = db.relationship("Mistake", back_populates="mistake_type")


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)


class Mistake(db.Model):
    __tablename__ = "mistakes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    mistake_type_id = db.Column(db.Integer, db.ForeignKey("mistake_types.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    wrong_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    status = db.Column(db.String(40), nullable=False, default="Не разобрано")
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    repeat_at = db.Column(db.Date)

    user = db.relationship("User", back_populates="mistakes")
    subject = db.relationship("Subject", back_populates="mistakes")
    mistake_type = db.relationship("MistakeType", back_populates="mistakes")
    tags = db.relationship("Tag", secondary=mistake_tags, backref=db.backref("mistakes", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subject": self.subject.name,
            "topic": self.topic,
            "description": self.description,
            "wrong_answer": self.wrong_answer,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "mistake_type": self.mistake_type.name,
            "status": self.status,
            "image_path": self.image_path,
            "tags": [tag.name for tag in self.tags],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "repeat_at": self.repeat_at.isoformat() if self.repeat_at else None,
        }

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, DateField, EmailField, PasswordField, SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


STATUS_CHOICES = [
    ("Не разобрано", "Не разобрано"),
    ("Разобрано", "Разобрано"),
    ("Нужно повторить", "Нужно повторить"),
    ("Исправлено", "Исправлено"),
]

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


class RegisterForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField("Повтор пароля", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class MistakeForm(FlaskForm):
    title = StringField("Название ошибки", validators=[DataRequired(), Length(max=200)])
    subject_id = SelectField("Предмет", coerce=int, validators=[DataRequired()])
    topic = StringField("Тема", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Описание задания", validators=[Optional()])
    wrong_answer = TextAreaField("Мой неправильный ответ", validators=[Optional()])
    correct_answer = TextAreaField("Правильный ответ", validators=[Optional()])
    explanation = TextAreaField("Объяснение решения", validators=[Optional()])
    mistake_type_id = SelectField("Тип ошибки", coerce=int, validators=[DataRequired()])
    status = SelectField("Статус", choices=STATUS_CHOICES, validators=[DataRequired()])
    image = FileField("Изображение задания", validators=[FileAllowed(ALLOWED_IMAGE_EXTENSIONS, "Разрешены только png, jpg, jpeg, webp")])
    repeat_at = DateField("Дата следующего повторения", validators=[Optional()], format="%Y-%m-%d")
    tag_ids = SelectMultipleField("Теги", coerce=int, validators=[Optional()])
    submit = SubmitField("Сохранить")

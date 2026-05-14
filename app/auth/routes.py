from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.db import db
from app.forms import LoginForm, RegisterForm
from app.models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует.", "danger")
            return render_template("auth/register.html", form=form)
        user = User(name=form.name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        current_app.logger.info("User registered: %s", user.email)
        flash("Регистрация завершена. Теперь войдите.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            current_app.logger.info("User logged in: %s", user.email)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("main.dashboard"))
        flash("Неверный email или пароль.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_app.logger.info("User logged out: %s", current_user.email)
    logout_user()
    return redirect(url_for("main.index"))

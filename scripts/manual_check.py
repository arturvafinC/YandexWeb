import re
import sys
from datetime import UTC, datetime
from io import BytesIO

import requests


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def csrf_token(html):
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    check(match is not None, "CSRF token missing")
    return match.group(1)


def register_and_login(session, base_url, email, password="Pass12345"):
    response = session.get(f"{base_url}/register", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/register",
        data={
            "csrf_token": token,
            "name": email.split("@")[0],
            "email": email,
            "password": password,
            "password_confirm": password,
        },
        allow_redirects=True,
        timeout=5,
    )
    check(response.status_code == 200 and "/login" in response.url, "register failed")
    response = session.get(f"{base_url}/login", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/login",
        data={"csrf_token": token, "email": email, "password": password},
        allow_redirects=True,
        timeout=5,
    )
    check(response.status_code == 200 and "/dashboard" in response.url and "Личный кабинет" in response.text, "login failed")


def create_api_mistake(session, base_url, title, subject="Математика", status="Нужно повторить", mistake_type="Невнимательность"):
    response = session.post(
        f"{base_url}/api/mistakes",
        json={
            "title": title,
            "subject": subject,
            "topic": "Тема",
            "mistake_type": mistake_type,
            "status": status,
            "explanation": "old",
        },
        timeout=5,
    )
    check(response.status_code == 201, f"api create failed: {response.status_code} {response.text[:200]}")
    return response.json()["id"]


def main(base_url):
    base_url = base_url.rstrip("/")
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    password = "Pass12345"

    session = requests.Session()
    response = session.get(f"{base_url}/", timeout=5)
    check(response.status_code == 200 and "Музей ошибок" in response.text and "Зарегистрироваться" in response.text, "home invalid")
    response = session.get(f"{base_url}/dashboard", allow_redirects=False, timeout=5)
    check(response.status_code in (302, 401), "dashboard is not protected")
    response = session.get(f"{base_url}/api/mistakes", timeout=5)
    check(response.status_code == 401 and response.json()["error"] == "Authentication required", "api auth invalid")
    response = session.get(f"{base_url}/missing-page", timeout=5)
    check(response.status_code == 404 and "Страница не найдена" in response.text, "404 invalid")

    email = f"manual-a-{stamp}@example.com"
    register_and_login(session, base_url, email, password)
    session.get(f"{base_url}/logout", timeout=5)

    response = session.get(f"{base_url}/register", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/register",
        data={"csrf_token": token, "name": "Dup", "email": email, "password": password, "password_confirm": password},
        timeout=5,
    )
    check(response.status_code == 200 and "уже существует" in response.text, "duplicate email invalid")

    response = session.get(f"{base_url}/login", timeout=5)
    token = csrf_token(response.text)
    response = session.post(f"{base_url}/login", data={"csrf_token": token, "email": email, "password": "badpass"}, timeout=5)
    check(response.status_code == 200 and "Неверный email или пароль" in response.text, "wrong password invalid")

    register_and_login(session, base_url, f"manual-a2-{stamp}@example.com", password)
    first_title = f"Manual Math {stamp}"
    second_title = f"Manual History {stamp}"
    first_id = create_api_mistake(session, base_url, first_title, "Математика", "Нужно повторить", "Невнимательность")
    second_id = create_api_mistake(session, base_url, second_title, "История", "Разобрано", "Ошибка в логике")

    response = session.get(f"{base_url}/mistakes?subject=Математика", timeout=5)
    check(first_title in response.text and second_title not in response.text, "subject filter invalid")
    response = session.get(f"{base_url}/mistakes?status=Нужно повторить", timeout=5)
    check(first_title in response.text and second_title not in response.text, "status filter invalid")
    response = session.get(f"{base_url}/mistakes?type=Невнимательность", timeout=5)
    check(first_title in response.text and second_title not in response.text, "type filter invalid")

    response = session.get(f"{base_url}/mistakes/{first_id}", timeout=5)
    check(response.status_code == 200 and "Отметить как исправленную" in response.text, "detail invalid")
    response = session.get(f"{base_url}/mistakes/{first_id}/edit", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/mistakes/{first_id}/edit",
        data={
            "csrf_token": token,
            "title": "Алгебра updated",
            "subject_id": "1",
            "topic": "Новая тема",
            "mistake_type_id": "1",
            "status": "Разобрано",
            "explanation": "new",
        },
        allow_redirects=True,
        timeout=5,
    )
    check(response.status_code == 200 and "Алгебра updated" in response.text and "new" in response.text, "edit invalid")
    token = csrf_token(response.text)
    response = session.post(f"{base_url}/mistakes/{first_id}/fix", data={"csrf_token": token}, allow_redirects=True, timeout=5)
    check("Исправлено" in response.text, "mark fixed invalid")

    response = session.get(f"{base_url}/review", timeout=5)
    check(response.status_code == 200, "review invalid")
    response = session.get(f"{base_url}/statistics", timeout=5)
    check(response.status_code == 200 and "Самый проблемный предмет" in response.text and "Процент исправленных" in response.text, "statistics invalid")

    response = session.get(f"{base_url}/mistakes/create", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/mistakes/create",
        data={"csrf_token": token, "title": "Без изображения", "subject_id": "1", "topic": "Форма", "mistake_type_id": "1", "status": "Не разобрано"},
        allow_redirects=True,
        timeout=5,
    )
    check(response.status_code == 200 and "Без изображения" in response.text, "form create without image invalid")

    response = session.get(f"{base_url}/mistakes/create", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/mistakes/create",
        data={"csrf_token": token, "title": "С изображением", "subject_id": "1", "topic": "Форма", "mistake_type_id": "1", "status": "Не разобрано"},
        files={"image": ("task.png", BytesIO(b"\x89PNG\r\n"), "image/png")},
        allow_redirects=True,
        timeout=5,
    )
    check(response.status_code == 200 and "uploads/" in response.text, "form create with image invalid")

    response = session.get(f"{base_url}/mistakes/create", timeout=5)
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/mistakes/create",
        data={"csrf_token": token, "title": "Плохой файл", "subject_id": "1", "topic": "Форма", "mistake_type_id": "1", "status": "Не разобрано"},
        files={"image": ("bad.txt", BytesIO(b"bad"), "text/plain")},
        timeout=5,
    )
    check(response.status_code == 200 and "Разрешены только" in response.text, "invalid upload accepted")

    foreign_id = create_api_mistake(session, base_url, "Чужая ошибка")
    other = requests.Session()
    register_and_login(other, base_url, f"manual-b-{stamp}@example.com", password)
    response = other.get(f"{base_url}/mistakes/{foreign_id}", timeout=5)
    check(response.status_code == 403 and "У вас нет доступа" in response.text, "foreign detail invalid")
    response = other.get(f"{base_url}/mistakes/{foreign_id}/edit", timeout=5)
    check(response.status_code == 403, "foreign edit invalid")
    response = other.get(f"{base_url}/mistakes/create", timeout=5)
    token = csrf_token(response.text)
    response = other.post(f"{base_url}/mistakes/{foreign_id}/delete", data={"csrf_token": token}, timeout=5)
    check(response.status_code == 403, "foreign delete invalid")
    response = other.get(f"{base_url}/api/mistakes/{foreign_id}", timeout=5)
    check(response.status_code == 403 and response.json()["error"] == "Forbidden", "foreign api invalid")

    response = session.delete(f"{base_url}/api/mistakes/{second_id}", timeout=5)
    check(response.status_code == 200, "api delete own invalid")
    response = session.get(f"{base_url}/api/mistakes/{second_id}", timeout=5)
    check(response.status_code == 404, "deleted api not 404")
    print("Manual HTTP scenarios passed")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/manual_check.py http://127.0.0.1:5000", file=sys.stderr)
        sys.exit(2)
    try:
        main(sys.argv[1])
    except Exception as exc:
        print(f"Manual check failed: {exc}", file=sys.stderr)
        sys.exit(1)

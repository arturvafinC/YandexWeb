import re
import sys
import time
from datetime import UTC, datetime

import requests


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def csrf_token(html):
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    if not match:
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert_true(match is not None, "CSRF token not found")
    return match.group(1)


def check_status(response, expected, label):
    assert_true(response.status_code == expected, f"{label}: expected {expected}, got {response.status_code}, body={response.text[:300]}")


def main(base_url):
    base_url = base_url.rstrip("/")
    session = requests.Session()
    unique = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    email = f"smoke-{unique}@example.com"
    password = "StrongPass123"

    response = session.get(f"{base_url}/", timeout=5)
    check_status(response, 200, "home")
    assert_true("Музей ошибок" in response.text, "home page does not contain project title")
    print("OK home")

    response = session.get(f"{base_url}/register", timeout=5)
    check_status(response, 200, "register page")
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/register",
        data={
            "csrf_token": token,
            "name": "Smoke User",
            "email": email,
            "password": password,
            "password_confirm": password,
        },
        allow_redirects=True,
        timeout=5,
    )
    check_status(response, 200, "register submit")
    assert_true("/login" in response.url, "register did not redirect to login")
    print("OK register")

    response = session.get(f"{base_url}/login", timeout=5)
    check_status(response, 200, "login page")
    token = csrf_token(response.text)
    response = session.post(
        f"{base_url}/login",
        data={"csrf_token": token, "email": email, "password": password, "remember": "y"},
        allow_redirects=True,
        timeout=5,
    )
    check_status(response, 200, "login submit")
    assert_true("/dashboard" in response.url and "Личный кабинет" in response.text, "dashboard not reached after login")
    print("OK login dashboard")

    payload = {
        "title": "Smoke API mistake",
        "subject": "Математика",
        "topic": "Квадратные уравнения",
        "mistake_type": "Ошибка в формуле",
        "status": "Нужно повторить",
        "wrong_answer": "x = 3",
        "correct_answer": "x = -3",
        "explanation": "Ошибка при раскрытии скобок",
        "tags": ["ЕГЭ"],
    }
    response = session.post(f"{base_url}/api/mistakes", json=payload, timeout=5)
    check_status(response, 201, "api create mistake")
    mistake_id = response.json()["id"]
    print("OK api create")

    response = session.get(f"{base_url}/api/mistakes", timeout=5)
    check_status(response, 200, "api list mistakes")
    assert_true(any(item["id"] == mistake_id for item in response.json()), "created mistake not in API list")
    print("OK api list")

    response = session.get(f"{base_url}/api/mistakes/{mistake_id}", timeout=5)
    check_status(response, 200, "api get mistake")
    assert_true(response.json()["title"] == payload["title"], "API detail has wrong title")
    print("OK api detail")

    response = session.patch(f"{base_url}/api/mistakes/{mistake_id}", json={"status": "Исправлено"}, timeout=5)
    check_status(response, 200, "api patch mistake")
    assert_true(response.json()["status"] == "Исправлено", "PATCH did not update status")
    print("OK api patch")

    response = session.delete(f"{base_url}/api/mistakes/{mistake_id}", timeout=5)
    check_status(response, 200, "api delete mistake")
    response = session.get(f"{base_url}/api/mistakes/{mistake_id}", timeout=5)
    check_status(response, 404, "api get deleted mistake")
    print("OK api delete")

    other = requests.Session()
    response = other.get(f"{base_url}/api/mistakes", timeout=5)
    check_status(response, 401, "api unauthorized")
    assert_true(response.json()["error"] == "Authentication required", "wrong unauthorized API error")
    print("OK api unauthorized")

    print("Smoke test passed")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/smoke_test.py http://127.0.0.1:5000", file=sys.stderr)
        sys.exit(2)
    try:
        main(sys.argv[1])
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        time.sleep(0.1)
        sys.exit(1)

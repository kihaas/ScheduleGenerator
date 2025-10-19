import asyncio
import requests

BASE_URL = "http://localhost:8000"


def test_auth_flow():
    # Сначала попробуем зарегистрироваться
    reg_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"  # нормальная длина
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    print("Register status:", response.status_code)
    if response.status_code == 200:
        print("Register response:", response.json())
    else:
        print("Register error:", response.json())
        # Если пользователь уже существует, пробуем логин
        if "already exists" in str(response.json()):
            print("User exists, trying login...")

    # Логин
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print("Login status:", response.status_code)
    print("Login response:", response.json())

    if response.status_code == 200:
        token = response.json()["access_token"]

        # Получение данных пользователя
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print("Me status:", response.status_code)
        print("Me response:", response.json())
    else:
        print("Login failed")


if __name__ == "__main__":
    test_auth_flow()
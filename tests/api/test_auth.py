import os
from typing import Dict, Any

from clients.api.api_manager import ApiManager
from faker import Faker

fake = Faker()


class TestAuthApi:
    def test_register_user(self, api_manager: ApiManager, test_user: dict[str, Any]):
        """Тест: Регистрация пользователя"""
        response = api_manager.auth_api.register_user(test_user)
        response_data = response.json()

        assert response_data["email"] == test_user["email"], "Email не совпадает"
        assert "id" in response_data, "ID отсутсвует в теле"
        assert "roles" in response_data, "Роли пользователя отсутсвуют в ответе"
        assert "USER" in response_data["roles"], "Роль USER должна быть у пользователя"

    def test_login_registered_user(
        self, api_manager: ApiManager, registered_user: dict[str, str]
    ):
        """Тест: Авторизация зарегистрированного пользователя"""
        login_data = {
            "email": registered_user["email"],
            "password": registered_user["password"],
        }
        response = api_manager.auth_api.login_user(login_data)
        response_data = response.json()

        assert "accessToken" in response_data, "Токен доступа отсуствует"
        assert (
            response_data["user"]["email"] == registered_user["email"]
        ), "Email не совпадает"
        assert "USER" in response_data["user"]["roles"], "Роль USER не назначена"

    def test_authenticate_set_headers(
        self, api_manager: ApiManager, registered_user: dict[str, str]
    ):
        """Тест: Сохранение токена в заголовках сессии."""
        response = api_manager.auth_api.authenticate(
            email=registered_user["email"], password=registered_user["password"]
        )
        login_response = api_manager.auth_api.login_user(
            {"email": registered_user["email"], "password": registered_user["password"]}
        )
        response_data = login_response.json()
        assert "accessToken" in response_data, "Токен отсуствует"

        access_token = response_data["accessToken"]
        auth_header = api_manager.auth_api.session.headers.get("Authorization")
        assert auth_header == f"Bearer {access_token}", "Токен в заголовке не совпадает"

    def test_login_admin(self, api_manager: ApiManager):
        """Тест: Авторизация пользователя с ролью ADMIN"""
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        login_data = {"email": admin_email, "password": admin_password}

        response = api_manager.auth_api.login_user(login_data)
        roles = response.json()["user"]["roles"]

        assert "ADMIN" in roles, "У админа нет роли Admin"


class TestNegativeAuthApi:

    def test_login_wrong_password(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест: Аторизация с неверным паролем"""
        payload = {"email": registered_user["email"], "password": fake.password()}
        response = api_manager.auth_api.login_user(payload, expected_status=401)

        assert "message" in response.text, "Отсутствует сообщение об ошибке в ответе"

    def test_login_non_existent_email(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест:  авторизация с несуществуещим email"""
        payload = {"email": fake.email(), "password": registered_user["password"]}
        response = api_manager.auth_api.login_user(payload, expected_status=401)

        assert "message" in response.text, "Отсутствует сообщение об ошибке в ответе"

    def test_login_empty_body(self, api_manager: ApiManager):
        """Негативный тест: Авторизации с пустым body"""
        response = api_manager.auth_api.login_user({}, expected_status=401)

        assert "message" in response.text, "Отсутсвует сообщение об ошибке в ответе"

    def test_login_missing_email(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест: Авторизация, email отсуствует"""

        response = api_manager.auth_api.login_user(
            login_data={"password": registered_user["password"]}, expected_status=401
        )

        assert "message" in response.text, "Отсуствует сообщение об ошибке в ответе"

    def test_login_missing_password(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест: Авторизация, пароль отсуствует"""

        response = api_manager.auth_api.login_user(
            login_data={"email": registered_user["email"]}, expected_status=401
        )

        assert "message" in response.text, "Отсуствует сообщение об ошибке в ответе"

    def test_negative_login_unregistered_user(
        self, api_manager: ApiManager, test_user: dict[str, Any]
    ):
        """Негативный тест: Авторизация незарегистрированного пользователя"""
        response = api_manager.auth_api.login_user(test_user, expected_status=401)
        response_data = response.json()

        assert response_data["error"] == "Unauthorized"

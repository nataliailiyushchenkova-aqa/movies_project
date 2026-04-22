import os
import pytest
from typing import Dict, Any


from clients.api.api_manager import ApiManager
from faker import Faker

from conftest import admin_payload, registered_user
from enums.roles import Roles
from resources.user_creds import SuperAdminCreds
from entities.user import User
from models.test_user_model import (
    TestUserData,
    RegisteredUserResponse,
    LoginUserResponse,
)
from utils.data_generator import DataGenerator

fake = Faker()


class TestAuthApi:
    def test_register_user(self, api_manager: ApiManager, test_user: TestUserData):
        """Тест: Регистрация пользователя"""
        payload = test_user.model_dump(mode="json", exclude_unset=True)
        response = api_manager.auth_api.register_user(user_data=payload)
        register_user_response = RegisteredUserResponse(**response.json())

        assert register_user_response.email == test_user.email, "Email не совпадает"

    def test_login_registered_user(
        self, api_manager: ApiManager, registered_user: dict[str, str]
    ):
        """Тест: Авторизация зарегистрированного пользователя"""
        login_data = {
            "email": registered_user.email,
            "password": registered_user.password,
        }
        response = api_manager.auth_api.login_user(login_data)
        response_data = LoginUserResponse(**response.json())

        assert response_data.user.email == registered_user.email, "Email не совпадает"

    @pytest.mark.parametrize(
        "email, password, expected_status",
        [
            (f"{SuperAdminCreds.USERNAME}", f"{SuperAdminCreds.PASSWORD}", 200),
            ("test_login1@email.com", "asdqwe123Q!", 401),
            ("", "password", 401),
        ],
        ids=["Admin login", "Invalid_user", "Empty username"],
    )
    def test_login(self, email, password, expected_status, api_manager):
        login_data = {"email": email, "password": password}
        api_manager.auth_api.login_user(
            login_data=login_data, expected_status=expected_status
        )

    def test_authenticate_set_headers(
        self, api_manager: ApiManager, registered_user: dict[str, str]
    ):
        """Тест: Сохранение токена в заголовках сессии."""
        response = api_manager.auth_api.authenticate(
            email=registered_user.email, password=registered_user.password
        )
        access_token = response.accessToken
        auth_header = api_manager.auth_api.session.headers.get("Authorization")
        assert auth_header == f"Bearer {access_token}", "Токен в заголовке не совпадает"

    def test_login_admin(self, admin: User, admin_payload: dict[str, Any]):
        """Тест: Авторизация пользователя с ролью ADMIN"""
        response = admin.api.auth_api.login_user(
            login_data={
                "email": admin_payload.email,
                "password": admin_payload.password,
            }
        )
        response_data = LoginUserResponse(**response.json())
        assert Roles.ADMIN in response_data.user.roles, "У админа нет роли Admin"


class TestNegativeAuthApi:

    def test_login_wrong_password(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест: Аторизация с неверным паролем"""
        payload = {"email": registered_user.email, "password": fake.password()}
        response = api_manager.auth_api.login_user(payload, expected_status=401)

        assert "message" in response.text, "Отсутствует сообщение об ошибке в ответе"

    def test_login_non_existent_email(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест:  авторизация с несуществуещим email"""
        payload = {"email": fake.email(), "password": registered_user.password}
        response = api_manager.auth_api.login_user(payload, expected_status=401)

        assert "message" in response.text, "Отсутствует сообщение об ошибке в ответе"

    @pytest.mark.xfail(reason="Баг ФР 401, ОР 400")
    def test_login_empty_body(self, api_manager: ApiManager):
        """Негативный тест: Авторизации с пустым body"""
        response = api_manager.auth_api.login_user({}, expected_status=400)

        assert "message" in response.text, "Отсутсвует сообщение об ошибке в ответе"

    def test_login_missing_email(
        self, api_manager: ApiManager, registered_user: dict[str, Any]
    ):
        """Негативный тест: Авторизация, email отсуствует"""

        response = api_manager.auth_api.login_user(
            login_data={"password": registered_user.password}, expected_status=401
        )

        assert "message" in response.text, "Отсуствует сообщение об ошибке в ответе"

    @pytest.mark.xfail(reason="Баг в системе, возвращается 500")
    def test_login_missing_password(
        self, common_user: User, registered_user: dict[str, Any]
    ):
        """Негативный тест: Авторизация, пароль отсуствует"""

        response = common_user.api.auth_api.login_user(
            login_data={"email": registered_user.email}, expected_status=400
        )

        assert "message" in response.text, "Отсуствует сообщение об ошибке в ответе"

    def test_negative_login_unregistered_user(
        self, super_admin: User, test_user: TestUserData
    ):
        """Негативный тест: Авторизация незарегистрированного пользователя"""
        payload = {
            "email": DataGenerator.generate_random_email(),
            "password": DataGenerator.generate_random_password(),
        }
        response = super_admin.api.auth_api.login_user(payload, expected_status=401)
        response_data = response.json()

        assert response_data["error"] == "Unauthorized"

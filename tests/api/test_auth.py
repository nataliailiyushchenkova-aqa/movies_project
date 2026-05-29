import datetime
import os
import pytest
from typing import Dict, Any
import allure
import pytest_check as check
import random

from faker import Faker
from pytest_mock import mocker
from unittest.mock import Mock

from requests import Response

from assertions.auth_assertions import (
    assert_register_response,
    assert_auth_tokens,
    assert_logged_in_user,
)
from clients.api.api_manager import ApiManager
from db_requester.sql_alchemy_client import password
from entities.existing_user import ExistingUser
from enums.roles import Roles
from models.error import ErrorResponse
from resources.user_creds import SuperAdminCreds
from entities.authenticateduser import AuthenticatedUser
from models.test_user_model import (
    UserTestData,
    RegisteredUserResponse,
    LoginUserResponse,
    LoginUserRequest,
)
from utils.data_generator import DataGenerator
from assertions.auth_assertions import assert_register_response
from utils.response_parser import deserialize_response

fake = Faker()


@pytest.mark.api
@pytest.mark.auth
@allure.epic("Auth API")
class TestAuthApi:
    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("POST / register - Регистрация пользователя")
    def test_register_user(
        self, api_manager: ApiManager, test_user: UserTestData
    ) -> None:
        with allure.step("Зарегистрировать пользователя"):
            response = api_manager.auth_api.register_user(test_user)

            registered_user = deserialize_response(response, RegisteredUserResponse)

        with allure.step("Проверить данные зарегистрированного пользователя"):
            assert_register_response(registered_user, test_user)

    @allure.title("Тест регистрации пользователя с помощью Mock")
    @allure.severity(allure.severity_level.MINOR)
    @allure.label("qa_name", "N.I")
    def test_register_user_mock(
        self, api_manager: ApiManager, test_user: UserTestData, mocker
    ):
        with allure.step("Мокаем метод register_user в auth_api"):
            mock_response = RegisteredUserResponse(
                id="id",
                email="email@email.com",
                fullName="fullName",
                verified=True,
                banned=False,
                roles=[Roles.SUPER_ADMIN],
                createdAt=str(datetime.datetime.now()),
            )
        mocker.patch.object(
            api_manager.auth_api, "register_user", return_value=mock_response
        )

        with allure.step("Вызываем метод, который должен быть замокан"):
            registered_user_response = api_manager.auth_api.register_user(test_user)

        with allure.step("Проверяем, что ответ соотвествует ожидаемому"):
            with allure.step("Проверка поля персональных данных"):
                check.equal(
                    registered_user_response.fullName,
                    "fullName",
                    "НЕСОВПАДЕНИЕ fullName",
                )
                check.equal(registered_user_response.email, mock_response.email)
            with allure.step("Проверка поля banned"):
                check.equal(registered_user_response.banned, mock_response.banned)

    @pytest.mark.smoke
    @allure.title("POST /login  Успешная авторизация пользователя")
    def test_login_registered_user(
        self, api_manager: ApiManager, existing_user: ExistingUser
    ) -> None:

        response = api_manager.auth_api.login_user(
            LoginUserRequest(
                email=existing_user.credentials.email,
                password=existing_user.credentials.password,
            )
        )
        logged_in_user = deserialize_response(response, LoginUserResponse)

        with allure.step("Проверить данные авторизированного пользователя"):
            assert_logged_in_user(logged_in_user, existing_user.profile)

        with allure.step("Проверить токены авторизации"):
            assert_auth_tokens(logged_in_user)

    @allure.title("Авторизация пользователя ролевая модель")
    @pytest.mark.parametrize(
        "user",
        [
            pytest.param("common_user", id="role user"),
            pytest.param("admin", id="role admin"),
            pytest.param("super_admin", id="role super_admin"),
        ],
        indirect=["user"],
    )
    def test_login_user_rbac(
        self,
        api_manager: ApiManager,
        user: AuthenticatedUser,
    ) -> None:
        response = api_manager.auth_api.login_user(login_data=user.login_request)

        logged_in_user = deserialize_response(response, LoginUserResponse)

        assert Roles(user.roles[0]) in logged_in_user.user.roles

    def test_authenticate_set_headers(
        self, api_manager: ApiManager, existing_user: ExistingUser
    ) -> None:
        """Тест: Сохранение токена в заголовках сессии."""
        response = api_manager.auth_api.authenticate(existing_user.login_request)
        access_token = response.accessToken
        auth_header = api_manager.auth_api.session.headers.get("Authorization")
        assert auth_header == f"Bearer {access_token}", "Токен в заголовке не совпадает"


class TestNegativeAuthApi:

    @pytest.mark.parametrize(
        "use_registered_email, use_valid_password",
        [
            (True, False),
            (False, True),
            (False, False),
        ],
        ids=["Wrong password", "Wrong email", "Unregistered user"],
    )
    def test_login_with_invalid_creds(
        self,
        api_manager: ApiManager,
        existing_user: ExistingUser,
        use_registered_email: bool,
        use_valid_password: bool,
    ) -> None:
        email = (
            existing_user.credentials.email
            if use_registered_email
            else DataGenerator.generate_random_email()
        )

        password = (
            existing_user.credentials.password
            if use_valid_password
            else DataGenerator.generate_random_password()
        )

        login_request = LoginUserRequest(email=email, password=password)

        response = api_manager.auth_api.login_user(
            login_data=login_request, expected_status=401
        )

        error_response = deserialize_response(response, ErrorResponse)

        assert error_response.message == "Неверный логин или пароль"

    @pytest.mark.parametrize(
        "payload, expected_status",
        [
            pytest.param(
                {},
                400,
                marks=pytest.mark.xfail(reason="Баг: ФР: 401, ОР: 400"),
                id="Empty body",
            ),
            pytest.param({"password": fake.password()}, 401, id="Missing email"),
            pytest.param({"email": fake.email()}, 401, id="Missing password"),
        ],
    )
    def test_loging_with_missing_payload(
        self,
        api_manager: ApiManager,
        payload: dict[str, Any],
        expected_status: int,
    ) -> None:
        response = api_manager.auth_api.login_user(
            login_data=payload, expected_status=expected_status
        )

        error_response = deserialize_response(response, ErrorResponse)

        assert error_response.message == "Неверный логин или пароль"

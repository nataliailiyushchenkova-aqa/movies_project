import uuid
import pytest
import allure
from copy import deepcopy
from typing import Dict, Any

from pyexpat.errors import messages

from assertions.auth_assertions import assert_register_response
from assertions.user_assertions import assert_partial_user_update
from clients.api.api_manager import ApiManager
from entities.authenticateduser import AuthenticatedUser
from fixtures.infrastructure import api_manager
from models.error import ErrorResponse
from models.test_user_model import (
    UserTestData,
    RegisteredUserResponse,
    LoginUserResponse,
    PatchUserResponse,
    PatchUserPayload,
)
from utils.data_generator import DataGenerator
from utils.response_parser import deserialize_response


@pytest.mark.api
@allure.epic("User API")
class TestUserApi:
    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("POST user")
    @allure.title("POST / user - Создание пользователя с дефолтными значениями")
    def test_post_user_default(
        self, super_admin: AuthenticatedUser, user_payload: UserTestData
    ):
        with allure.step("Подготовить данные создания пользователя"):
            payload = user_payload
        response = super_admin.api.user_api.create_user(payload)

        response_data = deserialize_response(response, RegisteredUserResponse)

        assert_register_response(response_data, user_payload)

    @pytest.mark.regression
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("POST user")
    @allure.title("POST / user - Создание пользователя c banned: True")
    def test_post_banned_user(
        self, super_admin: AuthenticatedUser, banned_user_payload: UserTestData
    ):
        response = super_admin.api.user_api.create_user(banned_user_payload)
        response_data = deserialize_response(response, RegisteredUserResponse)
        assert_register_response(response_data, banned_user_payload)

    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("GET user")
    @allure.title("GET / user - Получение пользователя по id/email super_admin")
    def test_get_user_by_locator(
        self, super_admin: AuthenticatedUser, user_payload: UserTestData
    ):
        with allure.step("Создать пользователя для запроса"):
            created_user = deserialize_response(
                super_admin.api.user_api.create_user(user_payload),
                RegisteredUserResponse,
            )

        with allure.step("Получить пользователя по id"):
            get_user_by_id = deserialize_response(
                super_admin.api.user_api.get_user_info(created_user.id),
                RegisteredUserResponse,
            )

        with allure.step("Получить пользователя по email"):
            get_user_by_email = deserialize_response(
                super_admin.api.user_api.get_user_info(created_user.email),
                RegisteredUserResponse,
            )

        with allure.step("Проверить консистентность данных между запросами"):
            assert (
                get_user_by_id == get_user_by_email
            ), "Содержание ответов должно быть идентичным"

        assert_register_response(get_user_by_id, user_payload)

    @pytest.mark.parametrize(
        "user",
        [
            pytest.param("admin", id="admin_can get user"),
            pytest.param("super_admin", id="super_admin can get user"),
        ],
        indirect=["user"],
    )
    @pytest.mark.rbac
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("GET user")
    @allure.title("GET / user - Получение пользователя по id/email ролевая модель")
    def test_get_user_by_locator_rbac(
        self,
        user: AuthenticatedUser,
        super_admin: AuthenticatedUser,
        user_payload: UserTestData,
    ):
        created_user = deserialize_response(
            super_admin.api.user_api.create_user(user_payload),
            RegisteredUserResponse,
        )

        with allure.step("Получить пользователя по id"):
            get_user_by_id = deserialize_response(
                user.api.user_api.get_user_info(created_user.id), RegisteredUserResponse
            )

        with allure.step("Получить пользователя по email"):
            get_user_by_email = deserialize_response(
                user.api.user_api.get_user_info(created_user.email),
                RegisteredUserResponse,
            )

        with allure.step("Проверить консистентность данных между запросами"):
            assert (
                get_user_by_id == get_user_by_email
            ), "Тело ответов должны быть идентичны"

    @pytest.mark.regression
    @allure.story("PATCH user")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("PATCH /user - Изменение пользователя: один параметр")
    def test_patch_user_one_field(
        self,
        super_admin: AuthenticatedUser,
        user_payload: UserTestData,
        existing_user_id: str,
        patch_user_payload_one_field: PatchUserPayload,
    ):

        response = super_admin.api.user_api.patch_user(
            existing_user_id, data=patch_user_payload_one_field
        )
        response_data = deserialize_response(response, PatchUserResponse)

        assert_partial_user_update(
            response=response_data,
            original_user=user_payload,
            patch_payload=patch_user_payload_one_field,
        )

    @pytest.mark.regression
    @allure.story("PATCH user")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("PATCH /user - Изменение пользователя: несколько параметров ")
    def test_patch_user_multiple_field(
        self,
        super_admin: AuthenticatedUser,
        user_payload: UserTestData,
        existing_user_id: str,
        patch_user_payload_multiple_fields: PatchUserPayload,
    ):
        response = super_admin.api.user_api.patch_user(
            existing_user_id, data=patch_user_payload_multiple_fields
        )

        response_data = deserialize_response(response, PatchUserResponse)

        assert_partial_user_update(
            response=response_data,
            original_user=user_payload,
            patch_payload=patch_user_payload_multiple_fields,
        )

    @pytest.mark.smoke
    @allure.story("DELETE user")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("DELETE / user - Успешное удаление пользователя")
    def test_delete_user(self, super_admin: AuthenticatedUser, existing_user_id: str):
        response = super_admin.api.user_api.delete_user(existing_user_id)
        with allure.step("Проверить статус код успешного удаления"):
            assert response.status_code in (200, 204)

        with allure.step("Проверить, что пользователь удалён и недоступен"):
            check_delete_user = super_admin.api.user_api.get_user_info(
                existing_user_id, expected_status=200
            )
            assert check_delete_user.json() == {}


@pytest.mark.api
@pytest.mark.negative
class TestNegativeUserApi:
    @pytest.mark.regression
    @pytest.mark.rbac
    @allure.story("GET user")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title(
        "GET /user Негативный тест. Получение пользователя обычным пользователем"
    )
    def test_negative_get_user_by_id_common_user(
        self, common_user: AuthenticatedUser, existing_user_id: str
    ):
        response = common_user.api.user_api.get_user_info(
            existing_user_id, expected_status=403
        )

        with allure.step("Проверить структуру и содержание ошибки доступа"):
            error_response = deserialize_response(response, ErrorResponse)
            assert "Forbidden" in error_response.message

    @pytest.mark.regression
    @allure.story("POST user")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title(
        "POST / Негативный тест. Создание уже зарегистрированного пользователя"
    )
    def test_negative_post_duplicate_user(
        self,
        super_admin: AuthenticatedUser,
        existing_user_payload: RegisteredUserResponse,
    ):
        with allure.step("Подготовить данные для создания пользователя"):
            duplicate_password = DataGenerator.generate_random_password()

            duplicate_payload = UserTestData(
                email=existing_user_payload.email,
                fullName=existing_user_payload.fullName,
                password=duplicate_password,
                passwordRepeat=duplicate_password,
                roles=existing_user_payload.roles,
                verified=existing_user_payload.verified,
                banned=existing_user_payload.banned,
            )

        response = super_admin.api.user_api.create_user(
            duplicate_payload, expected_status=409
        )

        with allure.step("Проверить структуру и содержание ошибки"):
            response_data = deserialize_response(response, ErrorResponse)
            assert (
                response_data.message
                == "Пользователь с таким email уже зарегистрирован"
            )

    @pytest.mark.regression
    @allure.story("DELETE user")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title(
        "DELETE / user Негативный тест. Удаление несуществующего пользователя."
    )
    def test_negative_delete_nonexisting_user(
        self, super_admin: AuthenticatedUser, unexisting_user_id: str
    ):
        with allure.step("Удалить несуществующего пользователя"):
            response = super_admin.api.user_api.delete_user(
                unexisting_user_id, expected_status=404
            )

        with allure.step("Проверить структуру и содержание ошибки"):
            response_data = deserialize_response(response, ErrorResponse)

            assert response_data.message == "Not Found"

    @pytest.mark.regression
    @allure.story("DELETE user")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title(
        "DELETE / user Негативный тест. Создание пользователя без обязательного email"
    )
    def test_negative_create_user_no_email(
        self, super_admin: AuthenticatedUser, user_payload: UserTestData
    ):
        with allure.step("Подготовить данные для создания пользователя без email"):
            payload = user_payload.model_copy(update={"email": None})

        response = super_admin.api.user_api.create_user(payload, expected_status=400)

        with allure.step("Проверить структуру и содержание ошибки"):
            response_data = deserialize_response(response, ErrorResponse)

            assert "email" in " ".join(response_data.message)
            assert "должно быть строкой" in " ".join(response_data.message)

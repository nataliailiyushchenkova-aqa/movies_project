import uuid
import pytest
from copy import deepcopy
from typing import Dict, Any

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


class TestUserApi:

    def test_post_user_default(
        self, super_admin: AuthenticatedUser, user_payload: UserTestData
    ) -> None:
        """Тест: Создание пользователя с дефолтными значениями"""
        payload = user_payload
        response = super_admin.api.user_api.create_user(payload)
        response_data = deserialize_response(response, RegisteredUserResponse)

        assert_register_response(response_data, user_payload)

    @pytest.mark.smoke
    def test_post_banned_user(
        self, super_admin: AuthenticatedUser, banned_user_payload: UserTestData
    ):
        """Тест: Создание пользователя banned: True"""
        response = super_admin.api.user_api.create_user(banned_user_payload)
        response_data = deserialize_response(response, RegisteredUserResponse)
        assert_register_response(response_data, banned_user_payload)

    @pytest.mark.smoke
    def test_get_user_by_locator(
        self, super_admin: AuthenticatedUser, user_payload: UserTestData
    ):
        """Тест: Получение пользователя по id/email super_admin"""
        created_user = RegisteredUserResponse(
            **super_admin.api.user_api.create_user(user_payload).json()
        )
        get_user_by_id = deserialize_response(
            super_admin.api.user_api.get_user_info(created_user.id),
            RegisteredUserResponse,
        )
        get_user_by_email = deserialize_response(
            super_admin.api.user_api.get_user_info(created_user.email),
            RegisteredUserResponse,
        )

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
    def test_get_user_by_locator_rbac(
        self,
        user: AuthenticatedUser,
        super_admin: AuthenticatedUser,
        user_payload: UserTestData,
    ):
        created_user = deserialize_response(
            super_admin.api.user_api.create_user(user_payload), RegisteredUserResponse
        )
        get_user_by_id = deserialize_response(
            user.api.user_api.get_user_info(created_user.id), RegisteredUserResponse
        )
        get_user_by_email = deserialize_response(
            user.api.user_api.get_user_info(created_user.email), RegisteredUserResponse
        )

        assert get_user_by_id == get_user_by_email, "Тело ответов должны быть идентичны"

    def test_patch_user_one_field(
        self,
        super_admin: AuthenticatedUser,
        user_payload: UserTestData,
        existing_user_id: str,
        patch_user_payload_one_field: PatchUserPayload,
    ):
        """Тест: Изменение пользователя: один параметр"""
        response = super_admin.api.user_api.patch_user(
            existing_user_id, data=patch_user_payload_one_field
        )
        response_data = deserialize_response(response, PatchUserResponse)

        assert_partial_user_update(
            response=response_data,
            original_user=user_payload,
            patch_payload=patch_user_payload_one_field,
        )

    def test_patch_user_multiple_field(
        self,
        super_admin: AuthenticatedUser,
        user_payload: UserTestData,
        existing_user_id: str,
        patch_user_payload_multiple_fields: PatchUserPayload,
    ):
        """Тест: Изменение пользователя: несколько параметров"""
        response = super_admin.api.user_api.patch_user(
            existing_user_id, data=patch_user_payload_multiple_fields
        )

        response_data = deserialize_response(response, PatchUserResponse)

        assert_partial_user_update(
            response=response_data,
            original_user=user_payload,
            patch_payload=patch_user_payload_multiple_fields,
        )

    def test_delete_user(self, super_admin: AuthenticatedUser, existing_user_id: str):
        """Тест: Успешное удаление пользователя"""
        response = super_admin.api.user_api.delete_user(existing_user_id)
        assert response.status_code in (200, 204)

        check_delete_user = super_admin.api.user_api.get_user_info(
            existing_user_id, expected_status=200
        )

        assert check_delete_user.json() == {}


class TestNegativeUserApi:

    def test_negative_get_user_by_id_common_user(
        self, common_user: AuthenticatedUser, existing_user_id: str
    ):
        response = common_user.api.user_api.get_user_info(
            existing_user_id, expected_status=403
        )

        error_response = deserialize_response(response, ErrorResponse)

    def test_negative_post_duplicate_user(
        self,
        super_admin: AuthenticatedUser,
        existing_user_payload: RegisteredUserResponse,
    ):
        """Негативный тест: Создание зарегистрированного пользователя"""

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
        response_data = deserialize_response(response, ErrorResponse)

        assert response_data.message == "Пользователь с таким email уже зарегистрирован"

    def test_negative_delete_nonexisting_user(
        self, super_admin: AuthenticatedUser, unexisting_user_id: str
    ) -> None:
        """Негативный тест: Удаление несуществующего пользователя"""
        response = super_admin.api.user_api.delete_user(
            unexisting_user_id, expected_status=404
        )
        response_data = deserialize_response(response, ErrorResponse)

        assert response_data.message == "Not Found"

    def test_negative_create_user_no_email(
        self, super_admin: AuthenticatedUser, user_payload: UserTestData
    ):
        """Негативный тест: Создание пользователя без обязательного email"""
        payload = user_payload.model_copy(update={"email": None})

        response = super_admin.api.user_api.create_user(payload, expected_status=400)

        response_data = deserialize_response(response, ErrorResponse)

        assert "email" in " ".join(response_data.message)
        assert "должно быть строкой" in " ".join(response_data.message)

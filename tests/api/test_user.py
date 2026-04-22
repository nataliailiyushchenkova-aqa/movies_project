import uuid
import pytest
from copy import deepcopy
from typing import Dict, Any

from clients.api.api_manager import ApiManager
from entities.user import User
from models.test_user_model import (
    TestUserData,
    RegisteredUserResponse,
    LoginUserResponse,
    PatchUserResponse,
)


class TestUserApi:

    def test_post_user_default(self, super_admin: User, user_payload: dict[str, Any]):
        """Тест: Создание пользователя с дефолтными значениями"""
        payload = user_payload
        response = super_admin.api.user_api.create_user(payload)
        response_data = RegisteredUserResponse.model_validate(response.json())

        assert response_data.email == user_payload["email"]
        assert response_data.fullName == user_payload["fullName"]
        assert [role.value for role in response_data.roles] == user_payload["roles"]
        assert response_data.verified == user_payload["verified"]

    @pytest.mark.smoke
    def test_post_banned_user(
        self, super_admin: User, banned_user_payload: TestUserData
    ):
        """Тест: Создание пользователя banned: True"""
        response = super_admin.api.user_api.create_user(banned_user_payload)
        response_data = RegisteredUserResponse.model_validate(response.json())

        assert response_data.email == banned_user_payload["email"]
        assert response_data.verified is True
        assert response_data.banned is True

    @pytest.mark.smoke
    def test_get_user_by_locator(self, super_admin: User, user_payload: dict[str, Any]):
        """Тест: Получение пользователя по id/email super_admin"""
        created_user = RegisteredUserResponse(
            **super_admin.api.user_api.create_user(user_payload).json()
        )
        get_user_by_id = RegisteredUserResponse(
            **super_admin.api.user_api.get_user_info(created_user.id).json()
        )
        get_user_by_email = RegisteredUserResponse(
            **super_admin.api.user_api.get_user_info(created_user.email).json()
        )

        assert (
            get_user_by_id == get_user_by_email
        ), "Содержание ответов должно быть идентичным"
        assert get_user_by_id.email == user_payload["email"]
        assert get_user_by_id.fullName == user_payload["fullName"]
        assert [role.value for role in get_user_by_id.roles] == user_payload["roles"]
        assert get_user_by_id.verified is True

    def test_get_user_by_locator_admin(self, admin: User, user_payload: dict[str, Any]):
        created_user = RegisteredUserResponse(
            **admin.api.user_api.create_user(user_payload).json()
        )
        get_user_by_id = RegisteredUserResponse(
            **admin.api.user_api.get_user_info(created_user.id).json()
        )
        get_user_by_email = RegisteredUserResponse(
            **admin.api.user_api.get_user_info(created_user.email).json()
        )

        assert get_user_by_id == get_user_by_email, "Тело ответов должны быть идентичны"
        assert get_user_by_id.id != "", "ID не должно быть пустым"
        assert get_user_by_id.fullName == user_payload["fullName"]
        assert [role.value for role in get_user_by_id.roles] == user_payload["roles"]
        assert get_user_by_id.verified is True

    def test_patch_user_one_field(
        self,
        super_admin: User,
        user_payload: dict[str, Any],
        get_user_id: str,
        patch_user_payload_one_field: dict[str, Any],
    ):
        """Тест: Изменение пользователя: один параметр"""
        response = PatchUserResponse(
            **super_admin.api.user_api.patch_user(
                get_user_id, data=patch_user_payload_one_field
            ).json()
        )

        assert response.banned == patch_user_payload_one_field["banned"]
        assert response.email == user_payload["email"]
        assert response.fullName == user_payload["fullName"]

    def test_patch_user_multiple_field(
        self,
        super_admin: User,
        user_payload: dict[str, Any],
        get_user_id: str,
        patch_user_payload_multiple_fields: dict[str, Any],
    ):
        """Тест: Изменение пользователя: несколько параметров"""
        response = PatchUserResponse(
            **super_admin.api.user_api.patch_user(
                get_user_id, data=patch_user_payload_multiple_fields
            ).json()
        )

        assert response.banned == patch_user_payload_multiple_fields["banned"]
        assert response.email == patch_user_payload_multiple_fields["email"]
        assert response.verified == patch_user_payload_multiple_fields["verified"]
        assert response.fullName == user_payload["fullName"]

    @pytest.mark.xfail(
        reason="возвращается 200 и пустое тело на запрос GET удаленного Id юзера"
    )
    def test_delete_user(self, super_admin: User, get_user_id: str):
        """Тест: Успешное удаление пользователя"""
        response = super_admin.api.user_api.delete_user(get_user_id)
        assert response.json().get("success") is True
        check_delete_user = super_admin.api.user_api.get_user_info(
            get_user_id, expected_status=404
        )
        check_delete_user_data = check_delete_user.json()

        assert "message" in check_delete_user_data


class TestNegativeUserApi:

    def test_negative_get_user_by_id_common_user(self, common_user):
        common_user.api.user_api.get_user_info(common_user.email, expected_status=403)

    def test_negative_post_duplicate_user(
        self,
        super_admin: User,
        duplicate_registered_user_payload: TestUserData,
    ):
        """Негативный тест: Создание зарегистрированного пользователя"""
        response = super_admin.api.user_api.create_user(
            duplicate_registered_user_payload, expected_status=409
        )
        response_data = response.json()

        assert "message" in response_data, "Отсуствует сообщение об ошибке"

    def test_negative_delete_nonexisting_user(
        self, super_admin: User, unexisting_user_id: uuid.UUID
    ):
        """Негативный тест: Удаление несуществующего пользователя"""
        response = super_admin.api.user_api.delete_user(
            unexisting_user_id, expected_status=404
        )
        response_data = response.json()

        assert "message" in response_data, "Отсутсвует сообщение об ошибке"

    def test_negative_create_user_no_email(
        self, super_admin: User, user_payload: dict[str, Any]
    ):
        """Негативный тест: Создание пользователя без обязательного email"""
        payload = deepcopy(user_payload)
        payload.pop("email")
        response = super_admin.api.user_api.create_user(payload, expected_status=400)
        response_data = response.json()

        assert "message" in response_data, "Отсутвует сообщение об ошибке"

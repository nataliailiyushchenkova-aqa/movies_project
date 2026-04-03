import uuid
from copy import deepcopy
from typing import Dict, Any

from clients.api.api_manager import ApiManager


class TestUserApi:

    def test_post_user_default(
        self, api_manager_admin: ApiManager, user_payload: dict[str, Any]
    ):
        """Тест: Создание пользователя с дефолтными значениями"""
        response = api_manager_admin.user_api.create_user(user_payload)
        response_data = response.json()

        assert "id" in response_data, "id отсутсвует в ответе"
        assert "USER" in response_data["roles"]
        assert response_data["email"] == user_payload["email"]
        assert response_data["verified"] is True
        assert response_data["banned"] is False

    def test_post_banned_user(
        self, api_manager_admin: ApiManager, banned_user_payload: dict[str, Any]
    ):
        """Тест: Создание пользователя banned: True"""
        response = api_manager_admin.user_api.create_user(banned_user_payload)
        response_data = response.json()

        assert "id" in response_data, "ID отсутствует в ответе"
        assert response_data["email"] == banned_user_payload["email"]
        assert response_data["verified"] is True
        assert response_data["banned"] is True

    def test_get_user_by_id(
        self,
        api_manager_admin: ApiManager,
        user_payload: dict[str, Any],
        get_user_id: uuid.UUID,
    ):
        """Тест: Получение пользователя по id"""
        response = api_manager_admin.user_api.get_user_info(get_user_id)
        response_data = response.json()

        assert "id" in response_data, "ID отсуствует в ответе"
        assert response_data["email"] == user_payload["email"]
        assert response_data["fullName"] == user_payload["fullName"]
        assert response_data["verified"] == user_payload["verified"]
        assert response_data["banned"] == user_payload["banned"]

    def test_get_user_by_email(
        self,
        api_manager_admin: ApiManager,
        user_payload: dict[str, Any],
        get_user_email: dict[str, str],
    ):
        """Тест: Получение пользователя по email"""
        response = api_manager_admin.user_api.get_user_info(get_user_email)
        response_data = response.json()

        assert "id" in response_data, "ID отсуствует в ответе"
        assert response_data["email"] == get_user_email
        assert response_data["fullName"] == user_payload["fullName"]
        assert response_data["verified"] == user_payload["verified"]
        assert response_data["banned"] == user_payload["banned"]

    def test_patch_user_one_field(
        self,
        api_manager_admin: ApiManager,
        user_payload: dict[str, Any],
        get_user_id: uuid.UUID,
        patch_user_payload_one_field: dict[str, Any],
    ):
        """Тест: Изменение пользователя: один параметр"""
        response = api_manager_admin.user_api.patch_user(
            get_user_id, data=patch_user_payload_one_field
        )
        response_data = response.json()

        assert response_data["banned"] == patch_user_payload_one_field["banned"]
        assert response_data["email"] == user_payload["email"]
        assert response_data["fullName"] == user_payload["fullName"]

    def test_patch_user_multiple_field(
        self,
        api_manager_admin: ApiManager,
        user_payload: dict[str, Any],
        get_user_id: uuid.UUID,
        patch_user_payload_multiple_fields: dict[str, Any],
    ):
        """Тест: Изменение пользователя: несколько параметров"""
        response = api_manager_admin.user_api.patch_user(
            get_user_id, data=patch_user_payload_multiple_fields
        )
        response_data = response.json()

        assert response_data["banned"] == patch_user_payload_multiple_fields["banned"]
        assert response_data["email"] == patch_user_payload_multiple_fields["email"]
        assert (
            response_data["verified"] == patch_user_payload_multiple_fields["verified"]
        )
        assert response_data["fullName"] == user_payload["fullName"]

    def test_delete_user(self, api_manager_admin: ApiManager, get_user_id: uuid.UUID):
        """Тест: Успешное удаление пользователя"""
        response = api_manager_admin.user_api.delete_user(get_user_id)
        assert response.json().get("success") is True
        check_delete_user = api_manager_admin.user_api.get_user_info(
            get_user_id, expected_status=404
        )
        check_delete_user_data = check_delete_user.json()

        assert (
            "message" in check_delete_user_data
        )  # баг возвращается 200 и пустое тело на запрос GET удаленного Id юзера


class TestNegativeUserApi:

    def test_negative_post_duplicate_user(
        self,
        api_manager_admin: ApiManager,
        duplicate_registered_user_payload: dict[str, Any],
    ):
        """Негативный тест: Создание зарегистрированного пользователя"""
        response = api_manager_admin.user_api.create_user(
            duplicate_registered_user_payload, expected_status=409
        )
        response_data = response.json()

        assert "message" in response_data, "Отсуствует сообщение об ошибке"

    def test_negative_delete_nonexisting_user(
        self, api_manager_admin: ApiManager, unexisting_user_id: uuid.UUID
    ):
        """Негативный тест: Удаление несуществующего пользователя"""
        response = api_manager_admin.user_api.delete_user(
            unexisting_user_id, expected_status=404
        )
        response_data = response.json()

        assert "message" in response_data, "Отсутсвует сообщение об ошибке"

    def test_negative_create_user_no_email(
        self, api_manager_admin: ApiManager, user_payload: dict[str, Any]
    ):
        """Негативный тест: Создание пользователя без обязательного email"""
        payload = deepcopy(user_payload)
        payload.pop("email")
        response = api_manager_admin.user_api.create_user(payload, expected_status=400)
        response_data = response.json()

        assert "message" in response_data, "Отсутвует сообщение об ошибке"

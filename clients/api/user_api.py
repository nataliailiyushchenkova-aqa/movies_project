import requests
import allure
from typing import Dict, Any

from requests import Response

from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL
from models.test_user_model import (
    UserTestData,
    RegisteredUserResponse,
    PatchUserPayload,
    PatchUserResponse,
)


class UserAPI(CustomRequester):
    def __init__(self, session: requests.Session):
        super().__init__(session=session, base_url=BASE_URL)
        self.session = session

    def get_user_info(self, get_user_id: int, expected_status: int = 200) -> Response:
        return self.send_request(
            method="GET",
            endpoint=f"/user/{get_user_id}",
            expected_status=expected_status,
        )

    @allure.step("Удалить пользовователя с id {get_user_id}")
    def delete_user(self, get_user_id: int, expected_status: int = 200) -> Response:
        return self.send_request(
            method="DELETE",
            endpoint=f"/user/{get_user_id}",
            expected_status=expected_status,
        )

    @allure.step("Создать пользователя")
    def create_user(
        self, user_payload: UserTestData, expected_status: int = 201
    ) -> Response:
        return self.send_request(
            method="POST",
            endpoint="/user",
            data=user_payload,
            expected_status=expected_status,
        )

    @allure.step("Изменить пользователя с id {user_id}")
    def patch_user(
        self, user_id: str, data: PatchUserPayload, expected_status: int = 200
    ) -> Response:
        return self.send_request(
            method="PATCH",
            endpoint=f"/user/{user_id}",
            data=data,
            expected_status=expected_status,
            exclude_none=True,
        )

    @allure.step("Очистка пользователя с id {user_id}")
    def clean_up_user(self, user_id: int) -> Response:
        try:
            self.delete_user(user_id, expected_status=200)
            print(f"[Cleanup] Пользователь {user_id} удален")
        except Exception as e:
            print(f"[Cleanup] Не удалось удалить пользователя {user_id}. Ошибка: {e}")

import requests
from typing import Dict, Any

from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL


class UserAPI(CustomRequester):
    def __init__(self, session: requests.Session):
        super().__init__(session=session, base_url=BASE_URL)
        self.session = session

    def get_user_info(self, get_user_id: int, expected_status: int = 200):
        return self.send_request(
            method="GET",
            endpoint=f"/user/{get_user_id}",
            expected_status=expected_status,
        )

    def delete_user(self, get_user_id: int, expected_status: int = 200):
        return self.send_request(
            method="DELETE",
            endpoint=f"/user/{get_user_id}",
            expected_status=expected_status,
        )

    def create_user(
        self, create_user_payload: dict[str, Any], expected_status: int = 201
    ):
        return self.send_request(
            method="POST",
            endpoint="/user",
            data=create_user_payload,
            expected_status=expected_status,
        )

    def patch_user(self, get_user_id, data: Dict[str, Any], expected_status: int = 200):
        return self.send_request(
            method="PATCH",
            endpoint=f"/user/{get_user_id}",
            data=data,
            expected_status=expected_status,
        )

    def clean_up_user(self, get_user_id: int):
        try:
            self.delete_user(get_user_id, expected_status=204)
            print(f"[Cleanup] Пользователь {get_user_id} удален")
        except Exception as e:
            print(
                f"[Cleanup] Не удалось удалить пользователя {get_user_id}. Ошибка: {e}"
            )

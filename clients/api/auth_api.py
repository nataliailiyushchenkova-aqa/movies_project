from typing import Dict
import os

import requests
from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL, LOGIN_ENDPOINT, REGISTER_ENDPOINT


class AuthAPI(CustomRequester):
    def __init__(self, session: requests.Session):
        super().__init__(session=session, base_url=BASE_URL)

    def register_user(self, user_data: dict[str, str], expected_status: int = 201):
        return self.send_request(
            method="POST",
            endpoint=REGISTER_ENDPOINT,
            data=user_data,
            expected_status=expected_status,
        )

    def login_user(self, login_data: dict[str, str], expected_status: int = 200):
        return self.send_request(
            method="POST",
            endpoint=LOGIN_ENDPOINT,
            data=login_data,
            expected_status=expected_status,
        )

    def authenticate(self, email: str, password: str):
        login_data = {"email": email, "password": password}
        response = self.login_user(login_data).json()
        if "accessToken" not in response:
            raise KeyError("Токен отсутсвует!!!!")

        token = response["accessToken"]
        self._update_session_headers(**{"authorization": f"Bearer {token}"})

    def admin_auth(self):
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        self.authenticate(email=admin_email, password=admin_password)

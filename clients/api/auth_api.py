from typing import Dict, Any
import os

import requests
import allure
from requests import Response

from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL, LOGIN_ENDPOINT, REGISTER_ENDPOINT
from models.test_user_model import (
    LoginUserResponse,
    LoginUserRequest,
    UserTestData,
    RegisteredUserResponse,
)
from utils.response_parser import deserialize_response


class AuthAPI(CustomRequester):
    def __init__(self, session: requests.Session):
        super().__init__(session=session, base_url=BASE_URL)

    @allure.step("Зарегистрировать пользователя")
    def register_user(
        self, user_data: UserTestData, expected_status: int = 201
    ) -> Response:
        return self.send_request(
            method="POST",
            endpoint=REGISTER_ENDPOINT,
            data=user_data,
            expected_status=expected_status,
        )

    @allure.step("Отправить запрос на login пользователя")
    def login_user(
        self, login_data: LoginUserRequest | dict[str, Any], expected_status: int = 200
    ) -> Response:
        return self.send_request(
            method="POST",
            endpoint=LOGIN_ENDPOINT,
            data=login_data,
            expected_status=expected_status,
        )

    @allure.step("Аутентифицировать пользователя")
    def authenticate(self, creds: LoginUserRequest) -> LoginUserResponse:
        response = self.login_user(creds)

        login_response = deserialize_response(response, LoginUserResponse)

        self._update_session_headers(
            authorization=f"Bearer {login_response.accessToken}"
        )
        return login_response

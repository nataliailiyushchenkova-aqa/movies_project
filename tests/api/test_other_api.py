import pytest
import requests
from constants import BASE_URL, HEADERS, REGISTER_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from clients.api.api_manager import ApiManager


class TestAuthApi:
	def test_login_user(self, api_manager: ApiManager, registered_user):
		login_data = {
			"email": registered_user["email"],
			"password": registered_user["password"]
		}

		response = api_manager.auth_api.login_user(login_data)
		response_data = response.json()

		assert "accessToken" in response_data, "Токен отсутсвует в ответе"
		assert "USER" in response_data["user"]["roles"], "Роль USER не назначена"
		assert response_data["user"]["email"] == registered_user["email"], "Почта не совпадает"
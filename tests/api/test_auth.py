from typing import Dict, Any

from clients.api.api_manager import ApiManager


class TestAuthApi:
	def test_register_user(self, api_manager: ApiManager, test_user: dict[str, Any]):
		response = api_manager.auth_api.register_user(test_user)
		response_data = response.json()
		#проверки
		assert response_data["email"] == test_user["email"], "Email не совпадает"
		assert "id" in response_data, "ID отсутсвует в теле"
		assert "roles" in response_data, "Роли пользователя отсутсвуют в ответе"
		assert "USER" in response_data["roles"], "Роль USER должна быть у пользователя"

	def test_register_and_login_user(self, api_manager: ApiManager, registered_user: dict[str, str]):
		login_data = {
			"email": registered_user["email"],
			"password": registered_user["password"]
		}
		response = api_manager.auth_api.login_user(login_data)
		response_data = response.json()

		assert "accessToken" in response_data, "Токен доступа отсуствует"
		assert response_data["user"]["email"] == registered_user["email"], "Email не совпадает"
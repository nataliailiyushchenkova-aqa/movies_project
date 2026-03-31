from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL

class UserAPI(CustomRequester):
	def __init__(self, session):
		super().__init__(session=session, base_url=BASE_URL)
		self.session = session

	def get_user_info(self, user_id: int, expected_status: int = 200):
		return self.send_request(
			method="GET",
			endpoint=f"/users/{user_id}",
			expected_status=expected_status
		)

	def delete_user(self, user_id: int, expected_status: int = 204):
		return self.send_request(
			method="DELETE",
			endpoint=f"user/{user_id}",
			expected_status=expected_status
		)

	def clean_up_user(self, user_id: int):
		try:
			self.delete_user(user_id, expected_status=204)
			print(f"[Cleanup] Пользователь {user_id} удален")
		except Exception as e:
			print(f"[Cleanup] Не удалось удалить пользователя {user_id}. Ошибка: {e}")
import pytest
import requests
from constants import BASE_URL, LOGIN_ENDPOINT, MOVIE_ENDPOINT
from models.movies_models import MoviesQweryParams
from models.get_movies_schemas import MovieSchema, GenreSchema, MoviesResponseSchema
from utils.data_generator import DataGenerator, faker
from faker import Faker
from clients.api.api_manager import ApiManager
fake = Faker()


class TestNegativeLogin:

	def test_login_wrong_password(self, api_manager: ApiManager, registered_user):
		"""Негативная проверка авторизации с неверным паролем"""
		payload = {
			"email": registered_user["email"],
			"password": fake.password()
		}
		response = api_manager.auth_api.login_user(payload, expected_status=401)

		assert "message" in response.text, "Отсутствует сообщение об ошибке в ответе"

	def test_login_non_existent_email(self, api_manager:ApiManager, registered_user):
		"""Негативная проверка авторизации с несуществуещим email"""
		payload = {
		"email": fake.email(),
		"password": registered_user["password"]
		}
		response = api_manager.auth_api.login_user(payload, expected_status=401)

		assert "message" in response.text, "Отсутствует сообщение об ошибке в ответе"

	def test_login_empty_body(self, api_manager:ApiManager):
		"""Негативная проверка авторизации с пустым body"""
		response = api_manager.auth_api.login_user({ }, expected_status=401)

		assert "message" in response.text, "Отсутсвует сообщение об ошибке в ответе"

	def test_login_missing_email(self, api_manager:ApiManager, registered_user):
		"""Негативная проверка авторизации, email отсуствует"""

		response = api_manager.auth_api.login_user(login_data={"password": registered_user["password"]}, expected_status=401)

		assert "message" in response.text, "Отсуствует сообщение об ошибке в ответе"

	def test_login_missing_password(self, api_manager:ApiManager, registered_user):
		"""Негативная проверка авторизации, пароль отсуствует"""

		response = api_manager.auth_api.login_user(login_data={"email": registered_user["email"]}, expected_status=401)

		assert "message" in response.text, "Отсуствует сообщение об ошибке в ответе"

	def test_post_movie_duplicate_name(self, api_manager_admin):
		"""Негативная проверка создания фильма с дублирующим названием"""

		unique_name = faker.sentence(nb_words=3)
		movie_data = DataGenerator.generate_movie_data(name=unique_name)

		response1 = api_manager_admin.movies_api.create_movie(movie_data)
		response1_data = response1.json()

		movie_data_same_name = DataGenerator.generate_movie_data(name=unique_name)
		response2 = api_manager_admin.movies_api.create_movie(movie_data_same_name, expected_status=409)
		response2_data = response2.json()
		assert "message" in response2_data, "Отсутвует сообщение об ошибке"

		api_manager_admin.movies_api.delete_movie(response1_data['id'])

	def test_post_movie_no_name(self, api_manager_admin):
		"""Негативная проверка создания фильма без имени"""

		movie_data = DataGenerator.generate_movie_data()
		movie_data.pop("name")

		response = api_manager_admin.movies_api.create_movie(movie_data, expected_status=400)
		response_data = response.json()

		assert "message" in response_data, "Отсутвует сообщение об ошибке"


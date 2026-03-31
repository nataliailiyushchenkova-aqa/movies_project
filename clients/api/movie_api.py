from custom_requester.custom_requester import CustomRequester
from constants import MOVIE_URL, MOVIE_ENDPOINT
from models.movies_models import MoviesQweryParams
from typing import Optional, List, Dict
from utils.data_generator import DataGenerator
from requests import Response

class MoviesAPI(CustomRequester):
	def __init__(self, session):
		super().__init__(session=session, base_url=MOVIE_URL)
		self.session = session

	def get_movie(self, params: Optional[MoviesQweryParams] = None, expected_status: int = 200):
		"""
		Получение списка фильмов.
		:param params: qwery параметры запроса
		:param expected_status: ожидаемый статус код
		:return: response object
		"""
		query_params = params if params is not None else MoviesQweryParams()

		return self.send_request(
			method="GET",
			endpoint=MOVIE_ENDPOINT,
			expected_status=expected_status
		)

	def get_movie_id(self, movie_id: int, expected_staus: int = 200):
		return self.send_request(
			method="GET",
			endpoint=f"{MOVIE_ENDPOINT}/{movie_id}",
			expected_status=expected_staus
		)

	def create_movie(self, movie_data: dict, expected_status: int = 201):
		if movie_data is None:
			movie_data = DataGenerator.generate_movie_data()
		return self.send_request(
			method="POST",
			endpoint=MOVIE_ENDPOINT,
			data=movie_data,
			expected_status=expected_status
		)

	def patch_movie(self, movie_id: int, movie_data: dict, expected_status: int = 200) -> Response:
		"""
		Частичное обновление фильма (PATCH /movies/{id}).
		:param movie_id: ID обновляемого фильма
	    :param movie_data: Словарь с полями для обновления (например, {"price": 500})
	    :param expected_status: Ожидаемый статус код (по умолчанию 200)
	    :return: Response object
	    """
		return self.send_request(
			method="PATCH",
			endpoint=f"{MOVIE_ENDPOINT}/{movie_id}",
			data=movie_data,
			expected_status=expected_status
		)

	def delete_movie(self, movie_id: int, expected_status: int = 200):
		return self.send_request(
			method="DELETE",
			endpoint=f"{MOVIE_ENDPOINT}/{movie_id}",
			expected_status=expected_status
		)

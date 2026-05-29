from typing import Optional, List, Dict, Union
import requests
import allure
from requests import Response


from custom_requester.custom_requester import CustomRequester
from constants import MOVIE_URL, MOVIE_ENDPOINT
from models.movies_models import MoviesQueryParams, MovieData, PatchMovieRequest
from utils.data_generator import DataGenerator


class MoviesAPI(CustomRequester):
    def __init__(self, session: requests.Session):
        super().__init__(session=session, base_url=MOVIE_URL)
        self.session = session

    @allure.step("Получить список фильмов")
    def get_movies(
        self, params: MoviesQueryParams | None = None, expected_status: int = 200
    ) -> Response:
        """
        Получение списка фильмов.
        :param params: qwery параметры запроса
        :param expected_status: ожидаемый статус код
        :return: response object
        """

        if params is None:
            query_params = {}
        elif isinstance(params, MoviesQueryParams):
            query_params = params.to_dict()
        else:
            query_params = params

        return self.send_request(
            method="GET",
            endpoint=MOVIE_ENDPOINT,
            params=query_params,
            expected_status=expected_status,
        )

    @allure.step("Получить фильм по id {movie_id}")
    def get_movie_id(self, movie_id: int, expected_status: int = 200):
        return self.send_request(
            method="GET",
            endpoint=f"{MOVIE_ENDPOINT}/{movie_id}",
            expected_status=expected_status,
        )

    @allure.step("Создать фильм")
    def create_movie(
        self,
        movie_data: Union[MovieData, dict, None] = None,
        expected_status: int = 201,
    ) -> Response:
        if movie_data is None:
            movie_data = DataGenerator.generate_movie_data()
        if isinstance(movie_data, MovieData):
            payload = movie_data.model_dump(mode="json")
        else:
            payload = movie_data

        return self.send_request(
            method="POST",
            endpoint=MOVIE_ENDPOINT,
            data=payload,
            expected_status=expected_status,
        )

    @allure.step("Изменить фильм")
    def patch_movie(
        self,
        movie_id: int,
        movie_data: PatchMovieRequest,
        expected_status: int = 200,
    ) -> Response:
        """
            Частичное обновление фильма (PATCH /movies/{id}).
            :param movie_id: ID обновляемого фильма
        :param movie_data: Словарь с полями для обновления (например, {"price": 500})
        :param expected_status: Ожидаемый статус код (по умолчанию 200)
        :return: Response object
        """
        payload = movie_data.model_dump(mode="json", exclude_none=True)

        return self.send_request(
            method="PATCH",
            endpoint=f"{MOVIE_ENDPOINT}/{movie_id}",
            data=payload,
            expected_status=expected_status,
            exclude_none=True,
        )

    @allure.step("Удалить фильм")
    def delete_movie(
        self, movie_id: int, expected_status: int | None = 200
    ) -> Response:
        return self.send_request(
            method="DELETE",
            endpoint=f"{MOVIE_ENDPOINT}/{movie_id}",
            expected_status=expected_status,
        )

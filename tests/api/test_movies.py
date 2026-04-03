import random
from datetime import datetime
from typing import Dict, Any
import pytest

from clients.api.api_manager import ApiManager
from clients.api.movie_api import MoviesAPI
from constants import MOVIE_URL, MOVIE_ENDPOINT
from models.movies_models import MoviesQweryParams
from models.get_movies_schemas import MovieSchema, GenreSchema, MoviesResponseSchema
from utils.data_generator import DataGenerator, faker
from faker import Faker

fake = Faker()


class TestMovieApi:

    def test_get_movies_no_params_pagination(
        self, api_manager: ApiManager, default_movies_pack: list[int]
    ):
        """Тест: Получение списка фильмов без параметров:
        дефолтная пагинация, структура ответа"""
        response = api_manager.movies_api.get_movie(default_movies_pack)
        response_data = MoviesResponseSchema.model_validate(response.json())

        assert response_data.page == 1
        assert response_data.page_size == 10
        assert response_data.count >= 30
        assert len(response_data.movies) > 0

    def test_get_movies_no_params_published_status(
        self, api_manager: ApiManager, movies_pack_with_status: list[int]
    ):
        """Тест: Получение списка фильмов без параметров: дефолтная выдача published_true"""
        response = api_manager.movies_api.get_movie()
        response_data = response.json()

        for movie in response_data["movies"]:
            assert (
                movie["published"] is True
            ), f"Фильм {movie['name']} статус неопубликован"

    def test_create_and_check_movie(self, api_manager_admin: ApiManager):
        """Тест: Создание фильма, успешное получение по id"""
        movie_data = DataGenerator.generate_movie_data(published=True)

        create_response = api_manager_admin.movies_api.create_movie(movie_data)
        create_response_data = create_response.json()
        movie_id = create_response_data["id"]

        try:
            get_response = api_manager_admin.movies_api.get_movie_id(movie_id)
            get_response_data = MovieSchema.model_validate(get_response.json())

            assert create_response_data["name"] == get_response_data.name
            assert create_response_data["price"] == get_response_data.price

        finally:
            api_manager_admin.movies_api.delete_movie(movie_id)

    def test_get_movies_filter_by_min_price(
        self, api_manager: ApiManager, movies_with_various_prices: list[int]
    ):
        """Тест: Получение списка фильмов с фильтрацией по минимальной цене"""
        min_price = 1
        params = MoviesQweryParams(min_price=min_price)

        response = api_manager.movies_api.get_movie(params=params)
        response_data = response.json()

        for movie in response_data["movies"]:
            assert (
                movie["price"] >= min_price
            ), f"Фильм {movie['id']} цена меньше {min_price}"

    def test_get_movies_filter_by_max_price(
        self, api_manager: ApiManager, movies_with_various_prices: list[int]
    ):
        """Тест: Получение списка фильмов с фильтрацией по максимальной цене"""
        max_price = 1000
        params = MoviesQweryParams(max_price=max_price)

        response = api_manager.movies_api.get_movie(params=params)
        response_data = MoviesResponseSchema.model_validate(response.json())

        test_movies_ids = {m["id"] for m in movies_with_various_prices}
        test_movies = [m for m in response_data.movies if m.id in test_movies_ids]

        for movie in test_movies:
            assert (
                movie["price"] <= max_price
            ), f"Фильм {movie['id']} цена больше {max_price}"

    def test_get_movies_filter_min_max_price(
        self, api_manager: ApiManager, movies_with_various_prices: list[int]
    ):
        """Тест: Получение списка фильмов с фильтрацией по диапазону цен"""
        min_price = 357
        max_price = 999
        params = MoviesQweryParams(min_price=min_price, max_price=max_price)

        response = api_manager.movies_api.get_movie(params=params)
        response_data = MoviesResponseSchema.model_validate(response.json())

        test_movies_ids = {m["id"] for m in movies_with_various_prices}
        test_movies = [m for m in response_data.movies if m.id in test_movies_ids]

        for movie in test_movies:
            assert (
                min_price <= movie["price"] <= max_price
            ), f"Цена фильма {movie['id']} вне диапазона [{min_price}, {max_price}]"

    def test_get_movies_sort_by_created_at_asc(
        self, api_manager: ApiManager, movies_with_controlled_dates: list[int]
    ):
        """Тест: Получение списка фильмов с сортировкой по возрастанию"""
        params = MoviesQweryParams(created_at="asc")

        response = api_manager.movies_api.get_movie(params=params)
        response_data = MoviesResponseSchema.model_validate(response.json())
        test_movies_ids = {m["id"] for m in movies_with_controlled_dates}
        test_movies = [m for m in response_data.movies if m.id in test_movies_ids]

        for i in range(len(test_movies) - 1):
            current_date = datetime.fromisoformat(
                test_movies[i].createdAt.replace("Z", "+00:00")
            )
            next_date = datetime.fromisoformat(
                test_movies[i + 1].createdAt.replace("Z", "+00:00")
            )
            assert (
                current_date <= next_date
            ), f"Нет сортировки по возрастанию {current_date} > {next_date}"

    def test_get_movies_sort_by_created_at_desc(
        self, api_manager: ApiManager, movies_with_controlled_dates: list[int]
    ):
        """Тест: Получение списка фильмов с сортировкой по убыванию"""
        params = MoviesQweryParams(created_at="desc")

        response = api_manager.movies_api.get_movie(params=params)
        response_data = MoviesResponseSchema.model_validate(response.json())
        test_movies_ids = {m["id"] for m in movies_with_controlled_dates}
        test_movies = [m for m in response_data.movies if m.id in test_movies_ids]

        for i in range(len(test_movies) - 1):
            current_date = datetime.fromisoformat(
                test_movies[i].createdAt.replace("Z", "+00:00")
            )
            next_date = datetime.fromisoformat(
                test_movies[i + 1].createdAt.replace("Z", "+00:00")
            )

            assert (
                current_date >= next_date
            ), f"Нет сортировки по возрастанию {current_date} < {next_date}"

    def test_post_movie_movie_schema_validation(self, api_manager_admin: ApiManager):
        """Тест: Соотвествие ответа POST/movie MovieSchema"""
        movie_data = DataGenerator.generate_movie_data()

        response = api_manager_admin.movies_api.create_movie(movie_data)
        response_data = MovieSchema.model_validate(response.json())

        assert response_data.name == movie_data["name"]
        assert response_data.price == movie_data["price"]
        assert response_data.description == movie_data["description"]
        assert response_data.image_url == movie_data["imageUrl"]
        assert response_data.location == movie_data["location"]
        assert response_data.genre_id == movie_data["genreId"]

        api_manager_admin.movies_api.delete_movie(response_data.id)

    def test_patch_movie_singe_field(
        self, api_manager_admin: ApiManager, movie_fixture: dict[str, str]
    ):
        """Тест: PATCH/movie Обновление одного параметра"""
        update_data = {"price": DataGenerator.generate_random_price()}

        response = api_manager_admin.movies_api.patch_movie(
            movie_fixture["id"], update_data
        )
        updated = MovieSchema.model_validate(response.json())

        assert updated.price == update_data["price"]
        assert updated.name == movie_fixture["name"]

    def test_patch_movie_multiple_fields(
        self, api_manager_admin: ApiManager, movie_fixture: dict[str, str]
    ):
        """Тест: PATCH/movie Обновление нескольких параметров"""
        update_data = {
            "name": DataGenerator.generate_random_movie_name(),
            "published": False,
            "location": "MSK",
        }

        response = api_manager_admin.movies_api.patch_movie(
            movie_fixture["id"], update_data
        )
        updated = MovieSchema.model_validate(response.json())

        assert updated.name == update_data["name"]
        assert updated.published == update_data["published"]
        assert updated.location == update_data["location"]
        assert updated.price == movie_fixture["price"]


class TestNegativeMovieAPI:

    def test_negative_post_movie_duplicate_name(self, api_manager_admin: ApiManager):
        """Негативный тест: Создание фильма с дублирующим названием"""
        unique_name = faker.sentence(nb_words=3)
        movie_data = DataGenerator.generate_movie_data(name=unique_name)

        response1 = api_manager_admin.movies_api.create_movie(movie_data)
        response1_data = response1.json()

        movie_data_same_name = DataGenerator.generate_movie_data(name=unique_name)
        response2 = api_manager_admin.movies_api.create_movie(
            movie_data_same_name, expected_status=409
        )
        response2_data = response2.json()
        assert "message" in response2_data, "Отсутвует сообщение об ошибке"

        api_manager_admin.movies_api.delete_movie(response1_data["id"])

    def test_negative_post_movie_no_name(self, api_manager_admin: ApiManager):
        """Негативный тест: Создание фильма без обязательного параметра name"""
        movie_data = DataGenerator.generate_movie_data()
        movie_data.pop("name")

        response = api_manager_admin.movies_api.create_movie(
            movie_data, expected_status=400
        )
        response_data = response.json()

        assert "message" in response_data, "Отсутвует сообщение об ошибке"

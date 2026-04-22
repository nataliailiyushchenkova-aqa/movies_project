import random
from datetime import datetime
from typing import Dict, Any
import pytest

from clients.api.api_manager import ApiManager
from clients.api.movie_api import MoviesAPI
from conftest import default_movies_pack
from constants import MOVIE_URL, MOVIE_ENDPOINT
from models.movies_models import (
    MoviesQueryParams,
    MovieSchema,
    GenreSchema,
    MoviesResponseSchema,
)
from utils.data_generator import DataGenerator, faker
from entities.user import User
from faker import Faker

fake = Faker()


class TestMovieApi:

    def test_get_movies_no_params_pagination(
        self, api_manager: ApiManager, default_movies_pack: list[int]
    ):
        """Тест: Получение списка фильмов без параметров:
        дефолтная пагинация, структура ответа"""
        response = api_manager.movies_api.get_movie()
        response_data = MoviesResponseSchema.model_validate(response.json())

        assert response_data.page == 1
        assert response_data.pageSize == 10
        assert response_data.count >= 30
        assert len(response_data.movies) > 0

    @pytest.mark.parametrize(
        "filter_params, filter_type",
        [
            ({"minPrice": 1, "maxPrice": 1000}, "price"),
            ({"locations": "MSK"}, "location"),
            ({"locations": "SPB"}, "location"),
            ({"genreId": 1}, "genre"),
            ({"genreId": 3}, "genre"),
        ],
        ids=[
            "price_range",
            "location_MSK_filter",
            "location_SPB_filter",
            "genre_filter_1",
            "genre_filter_3",
        ],
    )
    def test_get_movies_filtered(
        self, super_admin: User, filter_params: dict[str, Any], filter_type: str
    ):
        response = super_admin.api.movies_api.get_movie(params=filter_params)
        response_data = MoviesResponseSchema.model_validate(response.json())
        assert (
            len(response_data.movies) > 0
        ), f"По фильтру '{filter_type}' сервер вернул пустой список "

        for movie in response_data.movies:
            if filter_type == "price":
                assert (
                    filter_params["minPrice"]
                    <= movie.price
                    <= filter_params["maxPrice"]
                )
            elif filter_type == "locations":
                assert movie.location.value == filter_params["locations"]
            elif filter_type == "genre":
                assert movie.genreId == filter_params["genreId"]

    def test_get_movies_no_params_published_status(
        self, api_manager: ApiManager, movies_pack_with_status: list[int]
    ):
        """Тест: Получение списка фильмов без параметров: дефолтная выдача published_true"""
        response = api_manager.movies_api.get_movie()
        response_data = MoviesResponseSchema.model_validate(response.json())

        test_movies = {movie["id"] for movie in movies_pack_with_status}

        for movie in response_data.movies:
            if movie.id in test_movies:
                assert (
                    movie.published is True
                ), f"Фильм {movie.name} статус неопубликован"

    def test_create_and_check_movie(self, super_admin: User):
        """Тест: Создание фильма, успешное получение по id роль Super Admin"""
        movie_data = DataGenerator.generate_movie_data(published=True)

        create_response = super_admin.api.movies_api.create_movie(movie_data)
        create_response_data = create_response.json()
        movie_id = create_response_data["id"]

        try:
            get_response = super_admin.api.movies_api.get_movie_id(movie_id)
            get_response_data = MovieSchema.model_validate(get_response.json())

            assert create_response_data["name"] == get_response_data.name
            assert create_response_data["price"] == get_response_data.price

        finally:
            super_admin.api.movies_api.delete_movie(movie_id)

    @pytest.mark.parametrize(
        "minPrice,maxPrice",
        [
            (1, None),
            (None, 1000),
            (357, 999),
        ],
        ids=[
            "filter_by_min_price >=1",
            "filter_by_max_price <= 1000",
            "filter_min_max_price >=357 <=999",
        ],
    )
    def test_get_movie_filter_price(
        self,
        api_manager: ApiManager,
        movies_with_various_prices: list[int],
        minPrice,
        maxPrice,
    ):
        params = MoviesQueryParams(minPrice=minPrice, maxPrice=maxPrice)
        query_dict = params.model_dump(exclude_none=True)

        response = api_manager.movies_api.get_movie(params=query_dict)
        response_data = MoviesResponseSchema.model_validate(response.json())

        test_ids = {movie["id"] for movie in movies_with_various_prices}
        matched_movies = [m for m in response_data.movies if m.id in test_ids]

        for movie in matched_movies:
            if minPrice is not None:
                assert (
                    movie.price >= minPrice
                ), f"Фильм {movie.id}: цена {movie.price} < {minPrice}"
            if maxPrice is not None:
                assert (
                    movie.price <= maxPrice
                ), f"Фильм {movie.id}: цена {movie.price} > {maxPrice}"

    @pytest.mark.parametrize(
        "createdAt,compare",
        [("asc", lambda a, b: a <= b), ("desc", lambda a, b: a >= b)],
        ids=["get_movie_sort_asc", "get_movie_sort_desc"],
    )
    def test_get_movies_sort_by_created_at(
        self,
        api_manager: ApiManager,
        movies_with_controlled_dates: list[int],
        createdAt,
        compare,
    ):
        """Тест: Получение списка фильмов с сортировкой по возрастанию"""
        params = MoviesQueryParams(createdAt=createdAt)

        response = api_manager.movies_api.get_movie(params=params)
        response_data = MoviesResponseSchema.model_validate(response.json())

        test_movies_ids = {m["id"] for m in movies_with_controlled_dates}
        test_movies = [m for m in response_data.movies if m.id in test_movies_ids]

        for i in range(len(test_movies) - 1):
            current_date = test_movies[i].createdAt
            next_date = test_movies[i + 1].createdAt

            assert compare(
                current_date, next_date
            ), f"Неверная сортировка {current_date} и {next_date}"

    @pytest.mark.parametrize(
        "user,expected_status",
        [
            pytest.param("common_user", 403, id="post_movie_user_403"),
            pytest.param("admin", 403, id="post_movie_admin_403"),
            pytest.param("super_admin", 201, id="post_movie_super_admin_201"),
        ],
        indirect=["user"],
    )
    def test_post_movie_movie_schema_validation(self, user: User, expected_status: int):
        """Тест: Соотвествие ответа POST/movie MovieSchema"""
        movie_data = DataGenerator.generate_movie_data()

        response = user.api.movies_api.create_movie(
            movie_data.model_dump(mode="json"), expected_status=expected_status
        )
        if expected_status == 201:
            response_data = MovieSchema.model_validate(response.json())

            assert response_data.name == movie_data.name
            assert response_data.price == movie_data.price
            assert response_data.description == movie_data.description
            assert response_data.imageUrl == movie_data.imageUrl
            assert response_data.location == movie_data.location
            assert response_data.genreId == movie_data.genreId

    @pytest.mark.parametrize(
        "user,expected_status",
        [
            pytest.param("common_user", 403, id="post_movie_user_403"),
            pytest.param("admin", 403, id="post_movie_admin_403"),
            pytest.param("super_admin", 200, id="post_movie_super_admin_201"),
        ],
        indirect=["user"],
    )
    def test_patch_movie_singe_field(
        self, user: User, movie_fixture: dict[str, str], expected_status: int
    ):
        """Тест: PATCH/movie Обновление одного параметра"""
        update_data = {"price": DataGenerator.generate_random_price()}

        response = user.api.movies_api.patch_movie(
            movie_fixture["id"], update_data, expected_status=expected_status
        )

        if expected_status == 200:
            updated = MovieSchema.model_validate(response.json())

            assert updated.price == update_data["price"]
            assert updated.name == movie_fixture["name"]

    @pytest.mark.parametrize(
        ("user", "expected_status"),
        [
            pytest.param("common_user", 403, id="delete_movie_user_403"),
            pytest.param("admin", 403, id="delete_movie_admin_403"),
            pytest.param("super_admin", 200, id="delete_movie_super_admin_200"),
        ],
        indirect=["user"],
    )
    def test_delete_movie_role_model(
        self, movie_fixture: dict[str, Any], user: User, expected_status: int
    ):
        movie_id = movie_fixture["id"]

        response = user.api.movies_api.delete_movie(
            movie_id, expected_status=expected_status
        )
        if expected_status == 200:
            pass

    def test_patch_movie_multiple_fields(
        self, super_admin: User, movie_fixture: dict[str, str]
    ):
        """Тест: PATCH/movie Обновление нескольких параметров"""
        update_data = {
            "name": DataGenerator.generate_random_movie_name(),
            "published": False,
            "location": "MSK",
        }

        response = super_admin.api.movies_api.patch_movie(
            movie_fixture["id"], update_data
        )
        updated = MovieSchema.model_validate(response.json())

        assert updated.name == update_data["name"]
        assert updated.published == update_data["published"]
        assert updated.location.value == update_data["location"]
        assert updated.price == movie_fixture["price"]


class TestNegativeMovieAPI:

    def test_negative_post_movie_duplicate_name(self, super_admin: User):
        """Негативный тест: Создание фильма с дублирующим названием"""
        unique_name = faker.sentence(nb_words=3)
        movie_data = DataGenerator.generate_movie_data(name=unique_name)

        response1 = super_admin.api.movies_api.create_movie(movie_data)
        response1_data = MovieSchema.model_validate(response1.json())

        movie_data_same_name = DataGenerator.generate_movie_data(name=unique_name)
        response2 = super_admin.api.movies_api.create_movie(
            movie_data_same_name, expected_status=409
        )
        response2_data = response2.json()
        assert "message" in response2_data, "Отсутвует сообщение об ошибке"

        super_admin.api.movies_api.delete_movie(response1_data.id)

    def test_negative_post_movie_no_name(self, super_admin: User):
        """Негативный тест: Создание фильма без обязательного параметра name"""
        movie_data = DataGenerator.generate_movie_data().model_dump(exclude={"name"})

        response = super_admin.api.movies_api.create_movie(
            movie_data, expected_status=400
        )
        response_data = response.json()

        assert "message" in response_data, "Отсутвует сообщение об ошибке"

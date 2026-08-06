import uuid

import pytest
import random
import logging
import time
from collections.abc import Generator

from entities.authenticateduser import AuthenticatedUser
from models.movies_models import MovieSchema, MovieFilterInfo
from utils.data_generator import DataGenerator
from utils.response_parser import deserialize_response

logger = logging.getLogger(__name__)


@pytest.fixture
def movie_fixture(super_admin: AuthenticatedUser) -> Generator[MovieSchema, None, None]:
    """Создает фильм для тестов PATCH"""
    random_price = random.randint(100, 1000)
    movie_data = DataGenerator.generate_movie_data(price=random_price)

    response = super_admin.api.movies_api.create_movie(
        movie_data.model_dump(mode="json")
    )
    created_movie = deserialize_response(response, MovieSchema)

    yield created_movie  # передаем данные в тест

    # удаляем фильм
    try:
        delete_response = super_admin.api.movies_api.delete_movie(
            created_movie.id, expected_status=None
        )

        if delete_response.status_code not in (200, 404):
            logger.warning(
                f"Неожиданный статус при удалении фильма "
                f"{created_movie.id}: {delete_response.status_code}"
            )
    except Exception as e:
        logger.warning(f"Не удалось удалить фильм {created_movie.id}. Ошибка {e}")


@pytest.fixture
def default_movies_pack(super_admin) -> Generator[list[MovieSchema], None, None]:
    """Тестовые фильмы для проверки пагинации и базовой структуры"""
    created_movies: list[MovieSchema] = []

    for i in range(31):
        movie_data = DataGenerator.generate_movie_data(
            published=True, price=100 + i * 30
        )

        response = super_admin.api.movies_api.create_movie(movie_data)
        created_movie = deserialize_response(response, MovieSchema)
        created_movies.append(created_movie)

    yield created_movies

    for movie in created_movies:
        try:
            super_admin.api.movies_api.delete_movie(movie.id)
        except Exception as e:
            logger.warning(f"Не удалось удалить фильм {movie.id}. Ошибка {e}")


@pytest.fixture
def movies_pack_with_status(
    super_admin,
) -> Generator[list[MovieFilterInfo], None, None]:
    """Тестовые фильмы с разным статусом.
    Для проверки фильтрации неопубликованных фильмов.
    """
    created_movies = []
    for i in range(31):
        is_published = i % 3 != 0  # 20 опубликованных, 10 нет
        price = 100 + i * 30
        movie_data = DataGenerator.generate_movie_data(
            published=is_published, price=price
        )
        response = super_admin.api.movies_api.create_movie(movie_data)
        movie_response = deserialize_response(response, MovieSchema)
        created_movies.append(
            MovieFilterInfo(
                id=movie_response.id,
                published=movie_response.published,
                price=movie_response.price,
            )
        )

    yield created_movies

    for movie in created_movies:
        try:
            super_admin.api.movies_api.delete_movie(movie.id)
        except Exception as e:
            logger.warning(f"Не удалось удалить фильм {movie.id}: {e}")


@pytest.fixture
def movies_with_valid_prices(
    super_admin: AuthenticatedUser,
) -> Generator[list[MovieSchema], None, None]:
    created_movies: list[MovieSchema] = []
    prices = [100, 357, 999, 1000, 1001]

    try:
        for price in prices:
            movie_data = DataGenerator.generate_movie_data(published=True, price=price)
            response = super_admin.api.movies_api.create_movie(movie_data)
            created_movie = deserialize_response(response, MovieSchema)
            created_movies.append(created_movie)

        yield created_movies

    finally:
        for movie in created_movies:
            try:
                super_admin.api.movies_api.delete_movie(movie.id)
            except Exception as e:
                logger.warning(f"Не удалось удалить фильм {movie.id}: ошибка {e}")


@pytest.fixture
def movies_with_controlled_dates(
    super_admin: AuthenticatedUser,
) -> Generator[tuple[str, list[MovieSchema]], None, None]:
    """Фильмы с контролируемым интервалом между созданием"""
    test_run_id = uuid.uuid4().hex
    created_movies: list[MovieSchema] = []

    try:
        for i in range(10):
            movie_data = DataGenerator.generate_movie_data(
                name=f"sort-test-{test_run_id}-{i}", published=True
            )
            response = super_admin.api.movies_api.create_movie(movie_data)
            created_movies.append(deserialize_response(response, MovieSchema))

        yield test_run_id, created_movies

    finally:
        for movie in created_movies:
            try:
                super_admin.api.movies_api.delete_movie(movie.id)
            except Exception as e:
                logger.warning(f"Не удалось удалить фильм {movie.id}. Ошибка {e}")

from collections.abc import Callable
import allure
from typing import Any
from pytest_check import check
from models.movies_models import MovieSchema, MovieData
from db_models.movie import MovieDBModel
from pydantic import BaseModel


@allure.step("Проверить соответствие данных фильма в ответе")
def assert_movie_response(actual: MovieSchema, expected: MovieData):
    check.greater(actual.id, 0)
    check.equal(actual.name, expected.name)
    check.equal(actual.price, expected.price)
    check.equal(actual.description, expected.description)
    check.equal(actual.imageUrl, expected.imageUrl)
    check.equal(actual.location, expected.location)
    check.equal(actual.published, expected.published)
    check.equal(actual.genreId, expected.genreId)

    check.is_not_none(actual.createdAt)
    check.is_true(isinstance(actual.rating, int))

    check.is_not_none(actual.genre.name)


@allure.step("Проверить параметры фильма в БД")
def assert_movie_in_db(actual: MovieDBModel, expected: MovieData):
    check.is_not_none(actual.id)
    check.equal(actual.name, expected.name)
    check.equal(actual.price, float(expected.price))
    check.equal(actual.image_url, expected.imageUrl)
    check.equal(actual.location, expected.location.value)
    check.equal(actual.published, expected.published)
    check.equal(actual.genre_id, expected.genreId)
    check.is_not_none(actual.created_at)


@allure.step("Проверить корректность частичного обновления фильма")
def assert_partial_movie_update(
    actual: MovieSchema, original: MovieSchema, updated_fields: dict | BaseModel
):
    actual_data = actual.model_dump(mode="json")
    original_data = original.model_dump(mode="json")

    if isinstance(updated_fields, BaseModel):
        updated_fields_data = updated_fields.model_dump(exclude_unset=True, mode="json")
    else:
        updated_fields_data = updated_fields

    for field_name, expected_value in updated_fields_data.items():
        check.equal(
            actual_data[field_name],
            expected_value,
            (
                f"Поле {field_name} не обновилось."
                f" ОР: {expected_value},"
                f" ФР: {actual_data[field_name]}"
            ),
        )

    unchanged_fields = set(original_data.keys()) - set(updated_fields_data.keys())

    ignored_fields = {"updatedAt"}

    unchanged_fields -= ignored_fields

    for field_name in unchanged_fields:
        check.equal(
            actual_data[field_name],
            original_data[field_name],
            (
                f"Поле '{field_name}' незапланированно изменено. "
                f"ОР: {original_data[field_name]}, "
                f"ФР: {actual_data[field_name]}"
            ),
        )


@allure.step("Проверить сортировку фильмов по дате создания")
def assert_movies_sorted_by_created_at(
    movies: list[MovieSchema], comparator: Callable
) -> None:
    assert len(movies) > 1, "Недостаточно фильмов для проверки"

    for current_movie, next_movie in zip(movies, movies[1:]):
        assert comparator(
            current_movie.createdAt, next_movie.createdAt
        ), f"Неверная сортировка. \nTeкущая дата: {current_movie.createdAt}, следующая дата: {next_movie.createdAt}"


@allure.step("Проверить фильтрацию фильмов по цене")
def assert_movie_price_filter(
    movie: MovieSchema, filter_params: dict[str, Any]
) -> None:
    with allure.step(f"Проверка фильтрации цены фильма {movie.id}"):
        assert filter_params["minPrice"] <= movie.price <= filter_params["maxPrice"], (
            f"Цена {movie.price} не входит в диапазон "
            f"[{filter_params['minPrice']}, "
            f"{filter_params['maxPrice']}]"
        )


@allure.step("Проверить фильтрацию фильмов по локации")
def assert_movie_location_filter(
    movie: MovieSchema, filter_params: dict[str, Any]
) -> None:
    with allure.step(f"Проверка фильтрации локации фильма {movie.id}"):
        assert movie.location.value == filter_params["locations"], (
            f"Локация {movie.location.value} "
            f"не совпадает с "
            f"{filter_params['locations']}"
        )


@allure.step("Проверить фильтрацию фильмов по жанру")
def assert_movie_genre_filter(
    movie: MovieSchema, filter_params: dict[str, Any]
) -> None:
    with allure.step(f"Проверка фильтрации жанра фильма {movie.id}"):
        assert movie.genreId == filter_params["genreId"], (
            f"Жанр {movie.genreId} " f"не совпадает с " f"{filter_params['genreId']}"
        )


FILTER_ASSERTIONS: dict[
    str,
    Callable[[MovieSchema, dict[str, Any]], None],
] = {
    "price": assert_movie_price_filter,
    "location": assert_movie_location_filter,
    "genre": assert_movie_genre_filter,
}

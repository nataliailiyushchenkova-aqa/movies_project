from collections.abc import Callable
from typing import Any
from models.movies_models import MovieSchema, MovieData
from db_models.movie import MovieDBModel
from pydantic import BaseModel


def assert_movie_response(actual: MovieSchema, expected: MovieData):
    assert actual.id > 0
    assert actual.name == expected.name
    assert actual.price == expected.price
    assert actual.description == expected.description
    assert actual.imageUrl == expected.imageUrl
    assert actual.location == expected.location
    assert actual.published == expected.published
    assert actual.genreId == expected.genreId

    assert actual.createdAt is not None
    assert isinstance(actual.rating, int)

    assert actual.genre.name


def assert_movie_in_db(actual: MovieDBModel, expected: MovieData):
    assert actual.id is not None
    assert actual.name == expected.name
    assert actual.price == float(expected.price)
    assert actual.image_url == expected.imageUrl
    assert actual.location == expected.location.value
    assert actual.published == expected.published
    assert actual.genre_id == expected.genreId
    assert actual.created_at is not None


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
        assert actual_data[field_name] == expected_value, (
            f"Поле {field_name} не обновилось."
            f" ОР: {expected_value},"
            f" ФР: {actual_data[field_name]}"
        )

    unchanged_fields = set(original_data.keys()) - set(updated_fields_data.keys())

    ignored_fields = {"updatedAt"}

    unchanged_fields -= ignored_fields

    for field_name in unchanged_fields:
        assert actual_data[field_name] == original_data[field_name], (
            f"Поле '{field_name}' незапланированно изменено. "
            f"ОР: {original_data[field_name]}, "
            f"ФР: {actual_data[field_name]}"
        )


def assert_movies_sorted_by_created_at(
    movies: list[MovieSchema], comparator: Callable
) -> None:
    assert len(movies) > 1, "Недостаточно фильмов для проверки"

    for current_movie, next_movie in zip(movies, movies[1:]):
        assert comparator(
            current_movie.createdAt, next_movie.createdAt
        ), f"Неверная сортировка. \nTeкущая дата: {current_movie.createdAt}, следующая дата: {next_movie.createdAt}"


def assert_movie_price_filter(
    movie: MovieSchema, filter_params: dict[str, Any]
) -> None:
    assert filter_params["minPrice"] <= movie.price <= filter_params["maxPrice"], (
        f"Цена {movie.price} не входит в диапазон "
        f"[{filter_params['minPrice']}, "
        f"{filter_params['maxPrice']}]"
    )


def assert_movie_location_filter(
    movie: MovieSchema, filter_params: dict[str, Any]
) -> None:
    assert movie.location.value == filter_params["locations"], (
        f"Локация {movie.location.value} "
        f"не совпадает с "
        f"{filter_params['locations']}"
    )


def assert_movie_genre_filter(
    movie: MovieSchema, filter_params: dict[str, Any]
) -> None:
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

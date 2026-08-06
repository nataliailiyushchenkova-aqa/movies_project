import random
from datetime import datetime
from typing import Dict, Any
import pytest
import allure
from pytest_check import check

from clients.api.api_manager import ApiManager
from clients.api.movie_api import MoviesAPI
from constants import MOVIE_URL, MOVIE_ENDPOINT
from db_requester.db_helpers import DBHelper
from enums.location import Location
from models.error import ErrorResponse
from models.movies_models import (
    MoviesQueryParams,
    MovieSchema,
    GenreSchema,
    MoviesResponseSchema,
    PatchMovieRequest,
    MovieFilterInfo,
)
from models.fixture.movie_fixture_models import CreatedMovieData, CreatedMovieWithDate
from assertions.movie_assertions import (
    assert_movie_response,
    assert_movie_in_db,
    assert_partial_movie_update,
    assert_movies_sorted_by_created_at,
    FILTER_ASSERTIONS,
)
from utils.data_generator import DataGenerator, faker
from utils.comparators import SORT_COMPARATORS
from utils.response_parser import deserialize_response
from enums.sort_order import SortOrder
from entities.authenticateduser import AuthenticatedUser
from sqlalchemy.orm import Session
from db_models.movie import MovieDBModel


@pytest.mark.api
@allure.epic("Movies")
class TestMovieApi:

    @pytest.mark.smoke
    @allure.story("GET movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("GET / movies - Получение списка фильмов без параметров.")
    @allure.description("""
    Проверка:
    - дефолтной страницы
    - размера страницы
    - наличия фильмов
    - корректности структуры ответа
    """)
    def test_get_movies_no_params_pagination(
        self, api_manager: ApiManager, default_movies_pack: list[int]
    ):

        with allure.step("Получить фильмы без параметров"):
            response = api_manager.movies_api.get_movies()

        response_data = deserialize_response(response, MoviesResponseSchema)

        with allure.step("Проверить значения пагинации"):
            with allure.step("Дефолтная страница == 1"):
                check.equal(
                    response_data.page, 1, f"ФР: {response_data.page}. ОР: page 1"
                )
            with allure.step("Вывод фильмов на страницу == 10"):
                check.equal(
                    response_data.pageSize,
                    10,
                    f"ФР:{response_data.pageSize}. ОР: pageSize ==10",
                )
            with allure.step("Количеств фильмов >=30"):
                check.greater_equal(
                    response_data.count,
                    30,
                    f"ФР: {response_data.count}. ОР: больше 30 фильмов",
                )
            with allure.step("Наличие фильмов в выдаче"):
                check.is_true(response_data.movies, "Список фильмов пустой")

    @pytest.mark.smoke
    @allure.story("GET movie")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("GET /movies - фильтрация фильмов по параметрам")
    @allure.description("""
    Проверка фильтрации фильма: 
    - по цене (минимальная, максимальная цена)
    - по локации
    - по жанру
       """)
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
        self,
        super_admin: AuthenticatedUser,
        filter_params: dict[str, Any],
        filter_type: str,
    ):
        with allure.step(f"Получить фильмы с фильтрацией: {filter_type}"):
            response = super_admin.api.movies_api.get_movies(params=filter_params)

        response_data = deserialize_response(response, MoviesResponseSchema)

        with allure.step("Проверить, что список фильмов не пустой"):
            check.is_true(
                len(response_data.movies) > 0
            ), f"По фильтру '{filter_type}' сервер вернул пустой список "

        with allure.step(f"Проверить корректность фильтрации '{filter_type}'"):
            filter_assertion = FILTER_ASSERTIONS[filter_type]

            for movie in response_data.movies:
                filter_assertion(movie, filter_params)

    @pytest.mark.regression
    @allure.story("GET movie")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("GET /movies  Дефолтная выдача опубликованных фильмов")
    def test_get_movies_no_params_published_status(
        self, api_manager: ApiManager, movies_pack_with_status: list[MovieFilterInfo]
    ):
        with allure.step("Получить фильмы без параметров"):
            response = api_manager.movies_api.get_movies()

        response_data = deserialize_response(response, MoviesResponseSchema)

        with allure.step("Подготовить ожидаемые опубликованные фильмы"):
            test_movies = {movie.id for movie in movies_pack_with_status}

        with allure.step("Проверить, что все фильмы опубликованы"):
            for movie in response_data.movies:
                if movie.id in test_movies:
                    assert (
                        movie.published is True
                    ), f"Фильм {movie.name} статус неопубликован"

    @pytest.mark.regression
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("GET movie")
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
    @allure.title(
        "GET /movies Получение фильмов с фильтрацией по цене: minPrice={minPrice} maxPrice={maxPrice}"
    )
    @allure.description("""
    Проверка фильтрации фильма по цене:
         - минимальная цена (1), 
         - максимальная цена (1000), 
         - комбинированные цены (357, 999).
        """)
    def test_get_movies_filter_price(
        self,
        api_manager: ApiManager,
        movies_with_valid_prices: list[MovieSchema],
        minPrice: int | None,
        maxPrice: int | None,
    ):
        with allure.step("Подготовить query параметры"):
            params = MoviesQueryParams(minPrice=minPrice, maxPrice=maxPrice)
            query_dict = params.model_dump(exclude_none=True)

            allure.attach(
                str(query_dict),
                name="Query params",
                attachment_type=allure.attachment_type.JSON,
            )
        with allure.step("Получить список фильмов с фильтрацией"):
            response = api_manager.movies_api.get_movies(params=query_dict)
        allure.attach(
            response.text,
            name="GET response body",
            attachment_type=allure.attachment_type.JSON,
        )

        response_data = deserialize_response(response, MoviesResponseSchema)

        with allure.step("Отфильтровать тестовые фильмы из ответа"):
            test_ids = {movie.id for movie in movies_with_valid_prices}
            matched_movies = [m for m in response_data.movies if m.id in test_ids]
            allure.attach(
                str([movie.id for movie in matched_movies]),
                name="Matched movies ids",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Проверить фильтрацию по цене"):
            for movie in matched_movies:
                if minPrice is not None:
                    assert (
                        movie.price >= minPrice
                    ), f"Фильм {movie.id}: цена {movie.price} < {minPrice}"
                if maxPrice is not None:
                    assert (
                        movie.price <= maxPrice
                    ), f"Фильм {movie.id}: цена {movie.price} > {maxPrice}"

    @pytest.mark.regression
    @pytest.mark.flaky(
        reason="Тест сортировки зависит от ограничечения пагинации "
        "Тестовые фильмы могут не всегда попадать в ответ"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("GET movie")
    @allure.title("GET /movies Сортировка по дате создания")
    @allure.description("""Цель проверить сортировку фильмов по дате создания:
         - по возрастанию
         - по убыванию
         """)
    @pytest.mark.parametrize(
        "createdAt,comparator",
        [
            (SortOrder.ASC, SORT_COMPARATORS[SortOrder.ASC]),
            (SortOrder.DESC, SORT_COMPARATORS[SortOrder.DESC]),
        ],
        ids=["get_movie_sort_asc", "get_movie_sort_desc"],
    )
    def test_get_movies_sort_by_created_at(
        self,
        api_manager: ApiManager,
        createdAt: SortOrder,
        movies_with_controlled_dates: tuple[str, list[MovieSchema]],
        comparator,
    ):
        test_run_id, created_movies = movies_with_controlled_dates

        with allure.step("Подготить квери параметры"):
            params = MoviesQueryParams(createdAt=createdAt, pageSize=20)

        response = api_manager.movies_api.get_movies(params=params)

        response_data = deserialize_response(response, MoviesResponseSchema)

        with allure.step("Отфильтровать тестовые фильмы"):
            controlled_movies = [
                movie for movie in response_data.movies if test_run_id in movie.name
            ]
        with allure.step("Проверить, что все тестовые фильмы попали в ответ"):
            assert len(controlled_movies) == len(created_movies), (
                "Не все тестовые фильмы попали в ответ. "
                "Проблемы может быть в пагинации или глобальных данных."
            )

        with allure.step(f"Проверить сортировку по дате создания {createdAt.value}"):
            assert_movies_sorted_by_created_at(controlled_movies, comparator)

    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("POST movie")
    @allure.title("POST /movie Создание фильма")
    @allure.description("""
    Цель теста:
     - проверить успешное создание фильма
     - структуру ответа
     - проверить успешное получение созданного фильма
        """)
    def test_create_and_check_movie(self, super_admin: AuthenticatedUser):
        movie_data = DataGenerator.generate_movie_data(published=True)

        create_response = super_admin.api.movies_api.create_movie(movie_data)

        create_response_data = deserialize_response(create_response, MovieSchema)

        movie_id = create_response_data.id

        try:
            get_response = super_admin.api.movies_api.get_movie_id(movie_id)
            get_response_data = get_response.json()
            with allure.step("Проверить исходные параметры"):
                check.equal(create_response_data.name, get_response_data["name"])
                check.equal(create_response_data.price, get_response_data["price"])

        finally:
            with allure.step("Удалить тестовый фильм"):
                super_admin.api.movies_api.delete_movie(movie_id)

    @pytest.mark.regression
    @pytest.mark.db
    @pytest.mark.rbac
    @allure.story("POST movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("POST /movie Создание фильма: ролевая модель")
    @allure.description("""Цель теста проверить ролевую модель создания фильма:
    - Super Admin: 201 created
    - Admin: доступ запрещен
    - Common user: доступ запрещен
    """)
    @pytest.mark.parametrize(
        "user, can_create",
        [
            pytest.param("common_user", False, id="user_cannot_create"),
            pytest.param(
                "admin",
                False,
                id="admin_cannot_create",
                marks=pytest.mark.xfail(
                    reason="БАГ: Admin может создать фильм", strict=True
                ),
            ),
            pytest.param("super_admin", True, id="super_admin_can_create"),
        ],
        indirect=["user"],
    )
    def test_post_movie_rbac(
        self, user: AuthenticatedUser, db_helper: DBHelper, can_create: bool
    ):
        expected_status = 201 if can_create else 403

        with allure.step("Подготовить данные для создания фильма"):
            movie_data = DataGenerator.generate_movie_data()

        with allure.step("Проверить возможность создания фильма"):
            response = user.api.movies_api.create_movie(
                movie_data.model_dump(mode="json"), expected_status=expected_status
            )

    @pytest.mark.regression
    @allure.story("POST movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("POST /movie Валидация структуры ответа")
    @allure.description("Цель: проверка структуры ответа создания фильма")
    def test_post_movie_response_schema(self, super_admin: AuthenticatedUser):
        with allure.step("Подготовить данные для создания фильма"):
            movie_data = DataGenerator.generate_movie_data()

        response = super_admin.api.movies_api.create_movie(
            movie_data.model_dump(mode="json")
        )

        response_data = deserialize_response(response, MovieSchema)

        assert_movie_response(response_data, movie_data)

    @pytest.mark.regression
    @pytest.mark.db
    @allure.story("POST movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Проверка сохранения данных фильма в БД")
    @allure.description("Тест проверяет сохранение фильма в БД при вызове POST /movie")
    def test_post_movie_data_in_db(
        self, super_admin: AuthenticatedUser, db_helper: DBHelper
    ):
        with allure.step("Подготовить данные для создания фильма"):
            movie_data = DataGenerator.generate_movie_data()

        response = super_admin.api.movies_api.create_movie(
            movie_data.model_dump(mode="json")
        )

        with allure.step("Извлечь id фильма для проверки в БД"):
            movie = deserialize_response(response, MovieSchema)
            db_helper.db_session.expire_all()
            movie_id_db = db_helper.get_movie_by_id(movie.id)

        assert_movie_in_db(movie_id_db, movie_data)

    @pytest.mark.regression
    @pytest.mark.rbac
    @allure.story("PATCH movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("PATCH /movie Изменение одного поля фильма: ролевая модель")
    @allure.description(
        """Цель теста проверить ролевую модель изменения одного поля фильма:
    - Super Admin: 201 created
    - Admin: доступ запрещен
    - Common user: доступ запрещен
    """
    )
    @pytest.mark.parametrize(
        "user, can_edit",
        [
            pytest.param("common_user", False, id="user_cannot_edit"),
            pytest.param("admin", False, id="admin_cannot_edit"),
            pytest.param("super_admin", True, id="super_admin_can_edit"),
        ],
        indirect=["user"],
    )
    def test_patch_movie_single_field_rbac(
        self, user: AuthenticatedUser, movie_fixture: MovieSchema, can_edit: bool
    ):
        expected_status = 200 if can_edit else 403

        with allure.step("Подготовить данные для изменения одного поля фильма"):
            update_data = PatchMovieRequest(price=DataGenerator.generate_random_price())

        with allure.step(f"Пользователь с ролью {user.roles} пытается изменить фильм"):
            response = user.api.movies_api.patch_movie(
                movie_fixture.id, update_data, expected_status=expected_status
            )

        with allure.step(
            f"Проверить, что доступ {'разрешен' if can_edit else 'запрещен'}"
        ):
            assert response.status_code == expected_status

    @pytest.mark.regression
    @allure.story("PATCH movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("PATCH /movies Обновление одного поля фильма")
    def test_patch_movie_single_field(
        self, super_admin: AuthenticatedUser, movie_fixture: MovieSchema
    ):
        with allure.step("Подготовить данные для изменения одного поля фильма"):
            update_data = PatchMovieRequest(price=DataGenerator.generate_random_price())

        response = super_admin.api.movies_api.patch_movie(movie_fixture.id, update_data)

        updated_movie = deserialize_response(response, MovieSchema)

        assert_partial_movie_update(
            actual=updated_movie, original=movie_fixture, updated_fields=update_data
        )

    @pytest.mark.smoke
    @pytest.mark.rbac
    @allure.story("DELETE movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("DELETE /movie удаление фильма: ролевая модель")
    @allure.description("""Цель теста проверить ролевую модель удаления фильма:
    - Super Admin: 200 успешно
    - Admin: доступ запрещен
    - Common user: доступ запрещен
    """)
    @pytest.mark.parametrize(
        ("user", "can_delete"),
        [
            pytest.param("common_user", False, id="user_cannot_delete"),
            pytest.param(
                "admin",
                False,
                id="admin_cannot_delete",
                marks=pytest.mark.xfail(
                    reason="Баг. Admin может удалить фильм", strict=True
                ),
            ),
            pytest.param("super_admin", True, id="super_admin_can_delete"),
        ],
        indirect=["user"],
    )
    def test_delete_movie_rbac(
        self, movie_fixture: MovieSchema, user: AuthenticatedUser, can_delete: bool
    ):
        expected_status = 200 if can_delete else 403

        response = user.api.movies_api.delete_movie(
            movie_fixture.id, expected_status=expected_status
        )
        with allure.step(
            f"Проверить, что доступ {'разрешен' if can_delete else 'запрещен'}"
        ):
            assert response.status_code == expected_status

    @pytest.mark.regression
    @pytest.mark.db
    @allure.story("DELETE movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("DELETE /movie Удаление фильма в БД")
    def test_delete_movie_in_db(
        self,
        super_admin: AuthenticatedUser,
        db_helper: DBHelper,
        movie_fixture: MovieSchema,
    ):
        movie_id = movie_fixture.id

        with allure.step("Проверить наличие фильма в БД до удаления"):
            movie_before_delete = db_helper.get_movie_by_id(movie_id)
            assert movie_before_delete is not None

        response = super_admin.api.movies_api.delete_movie(movie_id)

        deleted_movie = deserialize_response(response, MovieSchema)

        with allure.step("Проверить данные удаленного фильма"):
            assert deleted_movie.id == movie_fixture.id

        with allure.step("Проверить отсуствие фильма в БД"):
            db_helper.db_session.expire_all()
            movie_after_deleted = db_helper.get_movie_by_id(movie_id)
            assert movie_after_deleted is None

    @pytest.mark.regression
    @allure.story("PATCH movie")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("PATCH /movie/id Обновление нескольких полей фильма")
    def test_patch_movie_multiple_fields(
        self, super_admin: AuthenticatedUser, movie_fixture: MovieSchema
    ):
        with allure.step("Подготовить данные для изменения параметров"):
            update_data = PatchMovieRequest(
                name=DataGenerator.generate_random_movie_name(),
                published=False,
                location=Location.MSK,
            )

        response = super_admin.api.movies_api.patch_movie(movie_fixture.id, update_data)

        updated_movie = deserialize_response(response, MovieSchema)

        assert_partial_movie_update(
            actual=updated_movie, original=movie_fixture, updated_fields=update_data
        )


@pytest.mark.api
@pytest.mark.negative
class TestNegativeMovieAPI:
    @pytest.mark.regression
    @allure.story("POST movie")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title(
        "POST /movies Негативный тест. Создание фильма с дублирующим названием"
    )
    def test_negative_post_movie_duplicate_name(self, super_admin: AuthenticatedUser):
        with allure.step("Подготовить уникальные тестовые данные для фильма"):
            unique_name = DataGenerator.generate_random_movie_name()
            movie_data = DataGenerator.generate_movie_data(name=unique_name)

        with allure.step("Создать исходный фильм"):
            response1 = super_admin.api.movies_api.create_movie(movie_data)
            response1_data = deserialize_response(response1, MovieSchema)

        with allure.step("Подготовить данные второго фильма с тем же названием"):
            movie_data_same_name = DataGenerator.generate_movie_data(name=unique_name)

        with allure.step("Попытаться создать фильм с дублирующим названием"):
            response2 = super_admin.api.movies_api.create_movie(
                movie_data_same_name, expected_status=409
            )

        with allure.step("Проверить сообщение об ошибке в ответе"):
            response2_data = response2.json()
            assert "message" in response2_data, "Отсутвует сообщение об ошибке"

        super_admin.api.movies_api.delete_movie(response1_data.id)

    @pytest.mark.regression
    @allure.story("POST movie")
    @allure.severity(allure.severity_level.MINOR)
    @allure.title("Негативный тест: Создание фильма без обязательного параметра name")
    def test_negative_post_movie_no_name(self, super_admin: AuthenticatedUser):
        with allure.step(
            "Подготовить данные для создания фильма без обязательного name"
        ):
            movie_data = DataGenerator.generate_movie_data().model_dump(
                exclude={"name"}
            )

        response = super_admin.api.movies_api.create_movie(
            movie_data, expected_status=400
        )

        with allure.step("Проверить наличие ошибки в ответе"):
            response_data = deserialize_response(response, ErrorResponse)
            assert any("name" in message for message in response_data.message)

    @pytest.mark.regression
    @allure.story("POST movie")
    @allure.title("Создание фильма с невалидной ценой")
    @pytest.mark.parametrize("price", [0, -1], ids=["price == 0", "price == -1"])
    def test_create_movie_with_invalid_price(
        self, super_admin: AuthenticatedUser, price: int
    ):
        movie_data = DataGenerator.generate_movie_data(price=price)

        response = super_admin.api.movies_api.create_movie(movie_data, 400)

        response_data = deserialize_response(response, ErrorResponse)

        assert any("price" in message for message in response_data.message)

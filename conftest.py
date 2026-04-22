import os
import random
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, Any, Optional, Callable

import requests
import pytest
from dotenv import load_dotenv
from faker import Faker

from clients.api.api_manager import ApiManager
from clients.api.auth_api import AuthAPI
from constants import BASE_URL, HEADERS, REGISTER_ENDPOINT, LOGIN_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from utils.data_generator import DataGenerator
from entities.user import User
from resources.user_creds import SuperAdminCreds
from enums.roles import Roles
from models.test_user_model import TestUserData

fake = Faker()
load_dotenv()
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def requester():
    """Фикстура для создания экзмепляра CustomRequestor"""
    session = requests.Session()
    return CustomRequester(session=session, base_url=BASE_URL)


@pytest.fixture(scope="session")
def session():
    """Фикстура для создания сессии requests.Session"""
    http_session = requests.Session()
    http_session.base_url = BASE_URL
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def auth_api(session):
    """Фикстура для создания экземпляра AuthAPI."""
    return AuthAPI(session)


@pytest.fixture(scope="session")
def api_manager(session):
    """Фикстура для создания API менеджера"""
    return ApiManager(session)


@pytest.fixture(scope="session")
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_session = ApiManager(session)
        user_pool.append(user_session)
        return user_session

    yield _create_user_session

    for user in user_pool:
        user.close_session()


@pytest.fixture
def user(request):
    role_name = request.param  # получаем значение из параметризации
    return request.getfixturevalue(role_name)


@pytest.fixture(scope="session")
def super_admin(user_session):
    new_session = user_session()

    super_admin = User(
        SuperAdminCreds.USERNAME,
        SuperAdminCreds.PASSWORD,
        [Roles.SUPER_ADMIN.value],
        new_session,
    )
    super_admin.api.auth_api.authenticate(*super_admin.creds)
    return super_admin


@pytest.fixture
def admin_payload(test_user: TestUserData):
    """Фикстура данных admin"""
    admin_email = DataGenerator.generate_random_email()
    admin_name = DataGenerator.generate_random_name()
    admin_password = DataGenerator.generate_random_password()

    admin_payload = TestUserData(
        email=admin_email,
        fullName=admin_name,
        password=admin_password,
        passwordRepeat=admin_password,
        roles=[Roles.ADMIN.value],
        verified=True,
        banned=False,
    )
    return admin_payload


@pytest.fixture
def admin(user_session, super_admin: User, admin_payload):

    create_admin = super_admin.api.user_api.create_user(
        admin_payload.model_dump(mode="json")
    )
    admin_id = create_admin.json()["id"]

    patch_admin = super_admin.api.user_api.patch_user(
        admin_id, data={"roles": [Roles.ADMIN.value]}
    )
    if patch_admin.status_code != 200:
        pytest.fail(
            f"Не удалось назначить роль ADMIN. "
            f"PATCH вернул {patch_admin.status_code}: {patch_admin.json()}"
        )

    new_session = user_session()
    admin = User(
        admin_payload.email,
        admin_payload.password,
        [Roles.ADMIN.value],
        new_session,
    )

    admin.api.auth_api.authenticate(*admin.creds)
    return admin


@pytest.fixture
def common_user(user_session, super_admin: User, user_payload: dict[str, Any]):
    new_session = user_session()
    payload = user_payload
    common_user = User(
        user_payload["email"],
        user_payload["password"],
        [Roles.USER.value],
        new_session,
    )

    response = super_admin.api.user_api.create_user(payload)
    user_id = response.json()["id"]
    common_user.id = user_id
    common_user.api.auth_api.authenticate(*common_user.creds)
    yield common_user

    try:
        super_admin.api.user_api.clean_up_user(common_user.id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {common_user.id}: {e}")


@pytest.fixture(scope="session")
def test_user() -> TestUserData:
    """Генерация случайного пользователя для тестов авторизации"""
    random_password = DataGenerator.generate_random_password()
    return TestUserData(
        email=DataGenerator.generate_random_email(),
        fullName=DataGenerator.generate_random_name(),
        password=random_password,
        passwordRepeat=random_password,
        roles=[Roles.USER.value],
    )


@pytest.fixture
def registered_user(super_admin, test_user: TestUserData):
    """Фикстура для создания зарегистрированного пользователя"""
    unique_email = DataGenerator.generate_random_email()
    user_data = TestUserData(
        email=unique_email,
        fullName=test_user.fullName,
        password=test_user.password,
        passwordRepeat=test_user.passwordRepeat,
        roles=test_user.roles,
    )
    payload = user_data.model_dump(mode="json", exclude_unset=True)
    response = super_admin.api.auth_api.register_user(payload, 201)
    response_data = response.json()
    registered_user = user_data.model_copy(update={"id": response_data.get("id")})
    yield registered_user

    try:
        super_admin.api.user_api.clean_up_user(registered_user.id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {registered_user.id}: {e}")


@pytest.fixture
def duplicate_registered_user_payload(super_admin, test_user: TestUserData):
    """Фикстура данных зарегистрированного пользователя для POST/user"""
    unique_email = DataGenerator.generate_random_email()
    user_payload = {
        "email": unique_email,
        "fullName": test_user.fullName,
        "password": test_user.password,
        "passwordRepeat": test_user.passwordRepeat,
        "roles": ["USER"],
        "verified": True,
        "banned": False,
    }
    response = super_admin.api.user_api.create_user(user_payload, expected_status=201)
    user_id = response.json()["id"]

    yield user_payload

    try:
        super_admin.api.user_api.clean_up_user(user_id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {user_id}: {e}")


@pytest.fixture
def user_payload(test_user: TestUserData):
    """Фикстура данных пользователя для POST/user"""
    random_email = DataGenerator.generate_random_email()
    updated_data = test_user.model_copy(
        update={"email": random_email, "verified": True, "banned": False}
    )
    return updated_data.model_dump(mode="json")


@pytest.fixture(scope="function")
def banned_user_payload(test_user: TestUserData):
    """Фикстура данных забаненного пользователя для POST/user"""

    unique_email = DataGenerator.generate_random_email()
    updated_data = test_user.model_copy(
        update={"email": unique_email, "verified": True, "banned": True}
    )
    return updated_data.model_dump(mode="json")


@pytest.fixture
def patch_user_payload_one_field():
    """Фикстура для PATCH/user изменение одного параметра"""
    return {"banned": True}


@pytest.fixture
def patch_user_payload_multiple_fields():
    """Фикстура для PATCH/user изменение нескольких параметров"""
    random_email = DataGenerator.generate_random_email()
    return {"banned": True, "email": random_email, "verified": False}


@pytest.fixture(scope="function")
def get_user_id(super_admin, user_payload):
    """Фикстура получения ID пользователя"""
    response = super_admin.api.user_api.create_user(user_payload)
    user_id = response.json()["id"]

    yield user_id

    try:
        super_admin.api.user_api.delete_user(user_id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {user_id}. Ошибка {e}")


@pytest.fixture(scope="session")
def get_user_email(super_admin, user_payload):
    """Фикстура получения email пользователя для GET/user/{email}"""
    response = super_admin.api.user_api.create_user(user_payload)
    user_email = response.json()["email"]
    user_id = response.json()["id"]

    yield user_email

    try:
        super_admin.api.user_api.delete_user(user_id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {user_id}. Ошибка {e}")


@pytest.fixture(scope="session")
def unexisting_user_id():
    """Фикстура получения несуществующего ID пользователя"""
    return DataGenerator.generate_random_user_id()


@pytest.fixture
def default_movies_pack(super_admin):
    """Тестовые фильмы для проверки пагинации и базовой структуры"""
    created_movies = []

    for i in range(31):
        movie_data = DataGenerator.generate_movie_data(
            published=True, price=100 + i * 30
        )

        response = super_admin.api.movies_api.create_movie(movie_data)
        movie_id = response.json()["id"]
        created_movies.append(movie_id)

    yield created_movies

    for movie_id in created_movies:
        try:
            super_admin.api.movies_api.delete_movie(movie_id)
        except Exception as e:
            print(f"Не удалось удалить фильм {movie_id}. Ошибка {e}")


@pytest.fixture(scope="session")
def movies_pack_with_status(super_admin):
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
        created_movies.append(
            {"id": response.json()["id"], "published": is_published, "price": price}
        )

    yield created_movies

    for movie in created_movies:
        try:
            super_admin.api.movies_api.delete_movie(movie["id"])
        except Exception as e:
            print(f"Не удалось удалить фильм {movie['id']}: {e}")


@pytest.fixture(scope="session")
def movies_with_various_prices(super_admin):
    """Фильмы с разными ценами"""
    created_movies = []
    prices = [0, 100, 357, 999, 1000, 1001]

    for price in prices:
        movie_data = DataGenerator.generate_movie_data(published=True, price=price)
        response = super_admin.api.movies_api.create_movie(movie_data)
        created_movies.append(
            {"id": response.json()["id"], "price": price, "published": True}
        )

    yield created_movies

    for movie in created_movies:
        try:
            super_admin.api.movies_api.delete_movie(movie["id"])
        except Exception as e:
            print(f"Не удалось удалить фильм {movie['id']}: ошибка {e}")


@pytest.fixture(scope="session")
def movies_with_controlled_dates(super_admin):
    """Фильмы с контролируемым интервалом между созданием"""
    created_movies = []
    timestamps = []

    for i in range(10):
        if i > 0:
            time.sleep(1)

        movie_data = DataGenerator.generate_movie_data(published=True)
        response = super_admin.api.movies_api.create_movie(movie_data)
        response_data = response.json()

        created_movies.append(
            {"id": response_data["id"], "createdAt": response_data["createdAt"]}
        )

    yield created_movies

    for movie in created_movies:
        try:
            super_admin.api.movies_api.delete_movie(movie["id"])
        except Exception as e:
            print(f"Не удалось удалить фильм {movie['id']}. Ошибка {e}")


@pytest.fixture(scope="function")
def movie_fixture(super_admin):
    """Создает фильм для тестов PATCH"""
    random_price = random.randint(100, 1000)
    movie_data = DataGenerator.generate_movie_data(price=random_price)

    response = super_admin.api.movies_api.create_movie(movie_data)
    movie = response.json()

    yield movie  # передаем данные в тест

    # удаляем фильм
    try:
        super_admin.api.movies_api.delete_movie(movie["id"])
    except Exception as e:
        print(f"Не удалось удалить фильм {movie['id']}. Ошибка {e}")

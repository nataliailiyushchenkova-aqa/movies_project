import os
import random
from datetime import datetime, timedelta
import time
from typing import Dict, Any

import requests
import pytest
from dotenv import load_dotenv
from faker import Faker

from clients.api.api_manager import ApiManager
from clients.api.auth_api import AuthAPI
from constants import BASE_URL, HEADERS, REGISTER_ENDPOINT, LOGIN_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from utils.data_generator import DataGenerator

fake = Faker()
load_dotenv()


@pytest.fixture(scope="session")
def test_user() -> dict[str, Any]:
    """Генерация случайного пользователя для тестов авторизации"""
    random_email = DataGenerator.generate_random_email()
    random_name = DataGenerator.generate_random_name()
    random_password = DataGenerator.generate_random_password()

    return {
        "email": random_email,
        "fullName": random_name,
        "password": random_password,
        "passwordRepeat": random_password,
        "roles": ["USER"],
    }


@pytest.fixture(scope="session")
def registered_user(requester, test_user: Dict[str, str], api_manager: ApiManager):
    """Фикстура для создания зарегистрированного пользователя"""
    response = requester.send_request(
        method="POST", endpoint=REGISTER_ENDPOINT, data=test_user, expected_status=201
    )
    response_data = response.json()
    registered_user = test_user.copy()
    registered_user["id"] = response_data["id"]
    yield registered_user

    if registered_user.get("id"):
        api_manager.user_api.clean_up_user(registered_user["id"])


@pytest.fixture(scope="session")
def duplicate_registered_user_payload(registered_user: dict[str, Any]):
    """Фикстура данных зарегистрированного пользователя для POST/user"""
    return {
        "fullName": registered_user["fullName"],
        "email": registered_user["email"],
        "password": registered_user["password"],
        "verified": True,
        "banned": False,
    }


@pytest.fixture(scope="session")
def user_payload(api_manager_admin):
    """Фикстура данных пользователя для POST/user"""
    return DataGenerator.generate_user_payload()


@pytest.fixture(scope="session")
def banned_user_payload(api_manager_admin):
    """Фикстура данных забаненного пользователя для POST/user"""
    return DataGenerator.generate_user_payload(banned=True)


@pytest.fixture(scope="session")
def patch_user_payload_one_field(api_manager_admin):
    """Фикстура для PATCH/user изменение одного параметра"""
    return {"banned": True}


@pytest.fixture(scope="session")
def patch_user_payload_multiple_fields(api_manager_admin):
    """Фикстура для PATCH/user изменение нескольких параметров"""
    random_email = DataGenerator.generate_random_email()
    return {"banned": True, "email": random_email, "verified": False}


@pytest.fixture(scope="session")
def get_user_id(api_manager_admin, user_payload):
    """Фикстура получения ID пользователя"""
    response = api_manager_admin.user_api.create_user(user_payload)
    user_id = response.json()["id"]

    yield user_id

    try:
        api_manager_admin.user_api.delete_user(user_id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {user_id}. Ошибка {e}")


@pytest.fixture(scope="session")
def get_user_email(api_manager_admin, user_payload):
    """Фикстура получения email пользователя для GET/user/{email}"""
    response = api_manager_admin.user_api.create_user(user_payload)
    user_email = response.json()["email"]
    user_id = response.json()["id"]

    yield user_email

    try:
        api_manager_admin.user_api.delete_user(user_id)
    except Exception as e:
        print(f"Не удалось удалить пользователя {user_id}. Ошибка {e}")


@pytest.fixture(scope="session")
def unexisting_user_id(api_manager_admin):
    """Фикстура получения несуществующего ID пользователя"""
    return DataGenerator.generate_random_user_id()


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
def admin_session(session, auth_api):
    """Фикстура для создания сессии админа"""
    auth_api.admin_auth()
    return auth_api


@pytest.fixture(scope="session")
def api_manager_admin(session, auth_api):
    """Фикстура для создания API менеджера с правами админа"""
    auth_api.admin_auth()
    return ApiManager(session)


@pytest.fixture(scope="session")
def default_movies_pack(api_manager_admin):
    """Тестовые фильмы для проверки пагинации и базовой структуры"""
    created_movies = []

    for i in range(31):
        movie_data = DataGenerator.generate_movie_data(
            published=True, price=100 + i * 30
        )

        response = api_manager_admin.movies_api.create_movie(movie_data)
        movie_id = response.json()["id"]
        created_movies.append(movie_id)

    yield created_movies

    for movie_id in created_movies:
        try:
            api_manager_admin.movies_api.delete_movie(movie_id)
        except Exception as e:
            print(f"Не удалось удалить фильм {movie_id}. Ошибка {e}")


@pytest.fixture(scope="session")
def movies_pack_with_status(api_manager_admin):
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
        response = api_manager_admin.movies_api.create_movie(movie_data)
        created_movies.append(
            {"id": response.json()["id"], "published": is_published, "price": price}
        )

    yield created_movies

    for movie in created_movies:
        try:
            api_manager_admin.movies_api.delete_movie(movie["id"])
        except Exception as e:
            print(f"Не удалось удалить фильм {movie['id']}: {e}")


@pytest.fixture(scope="session")
def movies_with_various_prices(api_manager_admin):
    """Фильмы с разными ценами"""
    created_movies = []
    prices = [0, 100, 357, 999, 1000, 1001]

    for price in prices:
        movie_data = DataGenerator.generate_movie_data(published=True, price=price)
        response = api_manager_admin.movies_api.create_movie(movie_data)
        created_movies.append(
            {"id": response.json()["id"], "price": price, "published": True}
        )

    yield created_movies

    for movie in created_movies:
        try:
            api_manager_admin.movies_api.delete_movie(movie["id"])
        except Exception as e:
            print(f"Не удалось удалить фильм {movie['id']}: ошибка {e}")


@pytest.fixture(scope="session")
def movies_with_controlled_dates(api_manager_admin):
    """Фильмы с контролируемым интервалом между созданием"""
    created_movies = []
    timestamps = []

    for i in range(10):
        if i > 0:
            time.sleep(1)

        movie_data = DataGenerator.generate_movie_data(published=True)
        response = api_manager_admin.movies_api.create_movie(movie_data)
        response_data = response.json()

        created_movies.append(
            {"id": response_data["id"], "createdAt": response_data["createdAt"]}
        )

    yield created_movies

    for movie in created_movies:
        try:
            api_manager_admin.movies_api.delete_movie(movie["id"])
        except Exception as e:
            print(f"Не удалось удалить фильм {movie['id']}. Ошибка {e}")


@pytest.fixture(scope="session")
def movie_fixture(api_manager_admin):
    """Создает фильм для тестов PATCH"""
    random_price = random.randint(100, 1000)
    movie_data = DataGenerator.generate_movie_data(price=random_price)

    response = api_manager_admin.movies_api.create_movie(movie_data)
    movie = response.json()

    yield movie  # передаем данные в тест

    # удаляем фильм
    try:
        api_manager_admin.movies_api.delete_movie(movie["id"])
    except Exception as e:
        print(f"Не удалось удалить фильм {movie['id']}. Ошибка {e}")

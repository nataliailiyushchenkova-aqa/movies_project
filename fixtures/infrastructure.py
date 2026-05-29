import pytest
import requests
import time
from typing import Any
from collections.abc import Callable, Generator
from requests import Session

from custom_requester.custom_requester import CustomRequester
from constants import BASE_URL
from clients.api.auth_api import AuthAPI
from clients.api.api_manager import ApiManager


@pytest.fixture
def delay_between_retries():
    time.sleep(2)
    yield


@pytest.fixture(scope="session")
def session() -> Generator[Session, None, None]:
    """Фикстура для создания сессии requests.Session"""
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def requester(session: Session) -> CustomRequester:
    """Фикстура для создания экзмепляра CustomRequestor"""
    return CustomRequester(session=session, base_url=BASE_URL)


@pytest.fixture(scope="session")
def auth_api(session: Session) -> AuthAPI:
    """Фикстура для создания экземпляра AuthAPI."""
    return AuthAPI(session)


@pytest.fixture(scope="session")
def api_manager(session: Session) -> ApiManager:
    """Фикстура для создания API менеджера"""
    return ApiManager(session)


@pytest.fixture(scope="session")
def user_session() -> Generator[
    Callable[[], ApiManager],
    None,
    None,
]:
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
def user(request) -> Any:
    role_name = request.param  # получаем значение из параметризации
    return request.getfixturevalue(role_name)

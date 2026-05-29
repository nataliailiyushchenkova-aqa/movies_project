import pytest
import logging

from db_requester.sql_alchemy_client import password
from enums.roles import Roles
from models.test_user_model import (
    UserTestData,
    PatchUserPayload,
    RegisteredUserResponse,
)
from utils.data_generator import DataGenerator
from entities.authenticateduser import AuthenticatedUser
from utils.response_parser import deserialize_response

logger = logging.getLogger(__name__)


@pytest.fixture
def test_user() -> UserTestData:
    """Генерация случайного пользователя для тестов авторизации"""
    random_password = DataGenerator.generate_random_password()
    return UserTestData(
        email=DataGenerator.generate_random_email(),
        fullName=DataGenerator.generate_random_name(),
        password=random_password,
        passwordRepeat=random_password,
        roles=[Roles.USER.value],
    )


@pytest.fixture
def user_payload() -> UserTestData:
    """Фикстура данных пользователя для POST/user"""
    password = DataGenerator.generate_random_password()
    return UserTestData(
        email=DataGenerator.generate_random_email(),
        fullName=DataGenerator.generate_random_name(),
        password=password,
        passwordRepeat=password,
        roles=[Roles.USER.value],
        verified=True,
        banned=False,
    )


@pytest.fixture
def banned_user_payload(test_user: UserTestData) -> UserTestData:
    """Фикстура данных забаненного пользователя для POST/user"""

    unique_email = DataGenerator.generate_random_email()
    return test_user.model_copy(
        update={"email": unique_email, "verified": True, "banned": True}
    )


@pytest.fixture
def patch_user_payload_one_field() -> PatchUserPayload:
    """Фикстура для PATCH/user изменение одного параметра"""
    return PatchUserPayload(banned=True)


@pytest.fixture
def patch_user_payload_multiple_fields() -> PatchUserPayload:
    """Фикстура для PATCH/user изменение нескольких параметров"""
    return PatchUserPayload(banned=True, verified=False)


@pytest.fixture
def existing_user_payload(
    super_admin: AuthenticatedUser, test_user: UserTestData
) -> RegisteredUserResponse:
    """Фикстура данных зарегистрированного пользователя для POST/user"""
    unique_email = DataGenerator.generate_random_email()
    user_payload = UserTestData(
        email=unique_email,
        fullName=test_user.fullName,
        password=test_user.password,
        passwordRepeat=test_user.passwordRepeat,
        roles=["USER"],
        verified=True,
        banned=False,
    )
    response = super_admin.api.user_api.create_user(user_payload, expected_status=201)
    response_data = deserialize_response(response, RegisteredUserResponse)

    yield response_data

    try:
        super_admin.api.user_api.clean_up_user(response_data.id)
    except Exception as e:
        logger.error(f"Не удалось удалить пользователя {response_data.id}: {e}")


@pytest.fixture
def admin_data(test_user: UserTestData) -> UserTestData:
    """Фикстура данных admin"""
    admin_email = DataGenerator.generate_random_email()
    admin_name = DataGenerator.generate_random_name()
    admin_password = DataGenerator.generate_random_password()

    admin_payload = UserTestData(
        email=admin_email,
        fullName=admin_name,
        password=admin_password,
        passwordRepeat=admin_password,
        roles=[Roles.ADMIN.value],
        verified=True,
        banned=False,
    )
    return admin_payload

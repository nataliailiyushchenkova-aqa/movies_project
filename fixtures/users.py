import pytest
import os
import logging
from collections.abc import Callable


from requests import Session

from db_requester.sql_alchemy_client import password
from entities.credentials import Credentials
from entities.existing_user import ExistingUser
from entities.authenticateduser import AuthenticatedUser
from dotenv import load_dotenv
from typing import Any
from enums.roles import Roles
from fixtures.database import created_user
from models.test_user_model import (
    UserTestData,
    PatchUserPayload,
    RegisteredUserResponse,
    LoginUserRequest,
    PatchUserResponse,
)
from resources.user_creds import SuperAdminCreds
from utils.data_generator import DataGenerator
from utils.response_parser import deserialize_response

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def super_admin(user_session: Callable[[], Session]) -> AuthenticatedUser:
    new_session = user_session()

    super_admin = AuthenticatedUser(
        credentials=Credentials(
            email=SuperAdminCreds.USERNAME,
            password=SuperAdminCreds.PASSWORD,
        ),
        roles=[Roles.SUPER_ADMIN.value],
        api=new_session,
    )
    super_admin.api.auth_api.authenticate(super_admin.login_request)

    return super_admin


@pytest.fixture
def admin(
    user_session: Callable[[], Session],
    super_admin: AuthenticatedUser,
    admin_data: UserTestData,
) -> AuthenticatedUser:

    response = super_admin.api.user_api.create_user(admin_data)

    created_admin = deserialize_response(response, RegisteredUserResponse)

    patch_admin_response = super_admin.api.user_api.patch_user(
        created_admin.id, data=PatchUserPayload(roles=[Roles.ADMIN])
    )
    patch_admin = deserialize_response(patch_admin_response, PatchUserResponse)

    assert Roles.ADMIN in patch_admin.roles

    new_session = user_session()
    admin = AuthenticatedUser(
        credentials=Credentials(email=admin_data.email, password=admin_data.password),
        roles=[Roles.ADMIN],
        api=new_session,
    )

    admin.api.auth_api.authenticate(admin.login_request)

    try:
        yield admin

    finally:
        super_admin.api.user_api.clean_up_user(created_admin.id)


@pytest.fixture
def common_user(
    user_session: Callable[[], Session], super_admin: AuthenticatedUser, user_factory
) -> AuthenticatedUser:

    payload = user_factory()

    response = super_admin.api.user_api.create_user(payload)

    created_user = deserialize_response(response, RegisteredUserResponse)

    new_session = user_session()

    common_user = AuthenticatedUser(
        credentials=Credentials(email=payload.email, password=payload.password),
        roles=[Roles.USER.value],
        api=new_session,
    )

    try:
        common_user.api.auth_api.authenticate(common_user.login_request)

        yield common_user

    finally:
        try:
            super_admin.api.user_api.clean_up_user(created_user.id)

        except Exception as error:
            logger.error(f"Не удалось удалить пользователя {created_user.id}: {error}")


@pytest.fixture
def existing_user(
    super_admin: AuthenticatedUser, user_payload: UserTestData
) -> ExistingUser:
    """Фикстура для создания зарегистрированного пользователя"""
    response = super_admin.api.auth_api.register_user(user_payload, 201)
    registered_user = deserialize_response(response, RegisteredUserResponse)

    existing_user = ExistingUser(
        credentials=Credentials(
            email=user_payload.email, password=user_payload.password
        ),
        profile=registered_user,
    )

    yield existing_user

    try:
        super_admin.api.user_api.clean_up_user(existing_user.profile.id)
    except Exception as e:
        logger.warning(
            f"Не удалось удалить пользователя {existing_user.profile.id}: {e}"
        )


@pytest.fixture
def existing_user_id(existing_user: ExistingUser) -> str:
    """Фикстура получения ID пользователя"""
    return existing_user.profile.id


@pytest.fixture
def unexisting_user_id() -> str:
    """Фикстура получения несуществующего ID пользователя"""
    return DataGenerator.generate_random_user_id()

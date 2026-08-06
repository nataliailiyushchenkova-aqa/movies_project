import pytest_check as check
import allure
from entities.existing_user import ExistingUser
from entities.authenticateduser import AuthenticatedUser
from models.test_user_model import RegisteredUserResponse, UserTestData, LoginUserInfo


@allure.step("Проверить данные зарегистрированного пользователя")
def assert_register_response(
    actual: RegisteredUserResponse,
    expected: UserTestData,
) -> None:
    check.is_not_none(actual.id)
    check.equal(actual.email, expected.email)
    check.equal(actual.fullName, expected.fullName)

    check.is_in("USER", actual.roles)
    if expected.verified is not None:
        check.equal(actual.verified, expected.verified)
    else:
        check.is_true(isinstance(actual.verified, bool))
    if expected.banned is not None:
        check.equal(actual.banned, expected.banned)
    else:
        check.is_true(isinstance(actual.banned, bool))


@allure.step("Проверить данные авторизованного пользователя")
def assert_logged_in_user(actual: LoginUserInfo, expected: AuthenticatedUser) -> None:
    check.equal(actual.user.id, expected.id)
    check.equal(actual.user.email, expected.email)
    check.equal(actual.user.fullName, expected.fullName)
    check.equal(actual.user.roles, expected.roles)


@allure.step("Проверить токены авторизации")
def assert_auth_tokens(data) -> None:
    check.is_true(bool(data.accessToken), "accessToken пустой")
    check.is_true(bool(data.refreshToken), "refreshToken пустой")
    check.greater(data.expiresIn, 0, "expiresIn должен быть > 0")

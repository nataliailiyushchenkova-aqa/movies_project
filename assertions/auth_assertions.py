from entities.existing_user import ExistingUser
from entities.authenticateduser import AuthenticatedUser
from models.test_user_model import RegisteredUserResponse, UserTestData, LoginUserInfo


def assert_register_response(
    actual: RegisteredUserResponse,
    expected: UserTestData,
) -> None:
    assert actual.id is not None
    assert actual.email == expected.email
    assert actual.fullName == expected.fullName
    assert "USER" in actual.roles
    if expected.verified is not None:
        assert actual.verified == expected.verified
    else:
        assert isinstance(actual.verified, bool)
    if expected.banned is not None:
        assert actual.banned == expected.banned
    else:
        assert isinstance(actual.banned, bool)


def assert_logged_in_user(actual: LoginUserInfo, expected: AuthenticatedUser) -> None:
    assert actual.user.id == expected.id
    assert actual.user.email == expected.email
    assert actual.user.fullName == expected.fullName
    assert actual.user.roles == expected.roles


def assert_auth_tokens(data):
    assert data.accessToken
    assert data.refreshToken
    assert data.expiresIn > 0

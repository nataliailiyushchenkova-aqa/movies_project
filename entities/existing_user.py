from dataclasses import dataclass

from entities.credentials import Credentials
from models.test_user_model import (
    UserTestData,
    RegisteredUserResponse,
    LoginUserRequest,
)


@dataclass
class ExistingUser:
    """Тестовая сущность зарегистрированного пользователя."""

    credentials: Credentials
    profile: RegisteredUserResponse

    @property
    def login_request(self) -> LoginUserRequest:
        return self.credentials.login_request

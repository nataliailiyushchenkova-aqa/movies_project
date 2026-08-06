from dataclasses import dataclass

from models.test_user_model import LoginUserRequest


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str

    @property
    def login_request(self) -> LoginUserRequest:
        return LoginUserRequest(email=self.email, password=self.password)

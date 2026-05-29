from clients.api.api_manager import ApiManager
from db_requester.sql_alchemy_client import password
from entities.credentials import Credentials
from enums.roles import Roles
from models.test_user_model import LoginUserRequest


class AuthenticatedUser:
    def __init__(
        self,
        credentials: Credentials,
        roles: list[Roles],
        api: ApiManager,
    ):
        self.credentials = credentials
        self.roles = roles
        self.api = api

    @property
    def creds(self):
        """Возращает кортеж (email, password)"""
        return self.email, self.password

    @property
    def login_request(self) -> LoginUserRequest:
        return self.credentials.login_request

import pytest

from enums.roles import Roles
from models.test_user_model import UserTestData
from utils.data_generator import DataGenerator


@pytest.fixture
def user_factory():

    def create_user_data() -> UserTestData:
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

    return create_user_data

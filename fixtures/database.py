import pytest
import allure
import uuid
from collections.abc import Callable, Generator
from sqlalchemy.orm import Session

from db_models.accounts_transaction_template import AccountTransactionTemplate
from db_models.user import UserDBModel
from db_requester.db_helpers import DBHelper
from db_requester.sql_alchemy_client import get_db_session
from utils.data_generator import DataGenerator


@pytest.fixture(scope="module")
def db_session() -> Generator[Session, None, None]:
    db_session = get_db_session()
    yield db_session
    db_session.close()


@pytest.fixture
def db_helper(db_session: Session) -> DBHelper:
    db_helper = DBHelper(db_session)
    return db_helper


@pytest.fixture
def created_user(db_helper: DBHelper) -> Generator[UserDBModel, None, None]:
    user = db_helper.create_test_user(DataGenerator.generate_user_data())
    yield user
    if db_helper.get_user_by_id(user.id):
        db_helper.delete_user(user.id)


@pytest.fixture
def accounts_factory(db_session: Session) -> Generator[
    Callable[[int, int], tuple[AccountTransactionTemplate, AccountTransactionTemplate]],
    None,
    None,
]:
    """Фикстура для создания тестовых счетов с произвольными балансами"""
    created_accounts = []

    def _create(stan_balance: int = 1000, bob_balance: int = 500):
        with allure.step(
            f"Создание счетов: Stan ({stan_balance}), Bob ({bob_balance})"
        ):
            stan = AccountTransactionTemplate(
                user=f"Stan_{uuid.uuid4().hex[:8]}", balance=stan_balance
            )
            bob = AccountTransactionTemplate(
                user=f"Bob_{uuid.uuid4().hex[:8]}", balance=bob_balance
            )
            db_session.add_all([stan, bob])
            db_session.commit()
            created_accounts.extend([stan, bob])
            return stan, bob

    yield _create

    with allure.step("Очистка тестовых счетов"):
        for acc in created_accounts:
            db_session.delete(acc)
            db_session.commit()

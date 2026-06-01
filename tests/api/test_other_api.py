import random

import allure
import pytest
from typing import Any
from sqlalchemy.orm import Session

from db_models.accounts_transaction_template import AccountTransactionTemplate
from db_models.movie import MovieDBModel
from utils.data_generator import DataGenerator
from clients.api.api_manager import ApiManager
from clients.api.movie_api import MoviesAPI
from entities.authenticateduser import AuthenticatedUser


@allure.title("Тест с перезапусками")
@pytest.mark.flaky(reruns=3)
def test_with_retries(delay_between_retries):
    with allure.step("Шаг 1: Проверка случайного значения"):
        result = random.choice([True, False])
        assert result, "Тест упал, потому что False"


@allure.step("Функция перевода денег: transfer_money")
def transfer_money(session: Session, from_account: str, to_account: str, amount: int):
    with allure.step("Получаем счета"):
        from_acc = (
            session.query(AccountTransactionTemplate).filter_by(user=from_account).one()
        )
        to_acc = (
            session.query(AccountTransactionTemplate).filter_by(user=to_account).one()
        )

    with allure.step("Проверяем, достаточно ли средств на счету"):
        if from_acc.balance < amount:
            raise ValueError("Недостаточно средств на счете")

    with allure.step("Выполняем перевод"):
        from_acc.balance -= amount
        to_acc.balance += amount

    with allure.step("Сохраняем изменения"):
        session.commit()


@allure.epic("Тестирование транзаций")
@allure.feature("Тестирование транзакций между двумя счетами")
class TestAccountTransactionTemplate:
    @allure.story("Корректность перевода денег между двумя счетами")
    @allure.description("""
    Тест проверяет happy-path перевода между двумя счетами".
    Шаги:
    1. Создание двух счетов: Stan и Bob.
    2. Перевод 200 единиц от Stan к Bob.
    3. Проверка изменения баланса.
    """)
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("qa_name", "N.I.")
    @allure.title("Тест успешного перевода средств между счетами 200 ед.")
    def test_accounts_transaction(self, db_session: Session, accounts_factory):
        with allure.step("Подготовить тестовые акаунты"):
            stan, bob = accounts_factory()

        with allure.step("Проверить начальные балансы"):
            assert stan.balance == 1000
            assert bob.balance == 500

        with allure.step("Выполнить перевод 200 ед. от stan к bob"):
            transfer_money(
                db_session, from_account=stan.user, to_account=bob.user, amount=200
            )

        db_session.refresh(stan)
        db_session.refresh(bob)

        with allure.step("Проверить изменение баланса"):
            assert stan.balance == 800
            assert bob.balance == 700

    @allure.story("Корректность перевода денег между двумя счетами")
    @allure.description("""
    Тест проверяет корректность перевода денег между двумя счетами при недостатке средств на счете.
    Шаги:
    1. Создание двух счетов: Stan и Bob.
    2. Попытка перевода 200 единиц от Stan к Bob (при балансе Stan = 100).
    3. Проверка, что транзакция отклонена из-за недостатка средств.
    4. Проверка, что балансы не изменились.
    5. Очистка тестовых данных.
    """)
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("qa_name", "N.I.")
    @allure.title("Тест отклонения перевода денег при недостатке средств на счете.")
    def test_account_negative_transaction_not_enough_money(
        self, db_session: Session, accounts_factory
    ):
        with allure.step("Подготовить тестовые акаунты"):
            stan, bob = accounts_factory(stan_balance=100, bob_balance=500)
            initial_stan_balance = stan.balance
            initial_bob_balance = bob.balance

        with allure.step("Попытка перевода 200 ед. при недостатке средств"):
            with pytest.raises(ValueError, match="Недостаточно средств на счете"):
                transfer_money(
                    db_session, from_account=stan.user, to_account=bob.user, amount=200
                )
                db_session.refresh(stan)
                db_session.refresh(bob)

        with allure.step("Проверить изменение баланса"):
            assert stan.balance == initial_stan_balance
            assert bob.balance == initial_bob_balance

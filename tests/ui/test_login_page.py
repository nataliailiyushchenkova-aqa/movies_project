import time
import allure
import pytest
from playwright.sync_api import Page, expect

from entities.existing_user import ExistingUser
from models.page_object_models.home_page import CinescopeHomePage
from models.page_object_models.login_page import CinescopeLoginPage


@allure.epic("Тестирование UI")
@allure.feature("Тестирование страницы Login")
@pytest.mark.ui
class TestLoginPage:
    def test_login_by_ui(
        self, login_page: CinescopeLoginPage, page: Page, existing_user: ExistingUser
    ):
        login_page.login(
            existing_user.profile.email, existing_user.credentials.password
        )
        home_page = CinescopeHomePage(page)
        home_page.assert_user_logged_in()

import allure
from playwright.sync_api import Page, expect

from models.page_object_models.base_page import BasePage
from models.page_object_models.home_page import CinescopeHomePage


class CinescopeLoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page
        self.url = f"{self.home_url}/login"
        self.email_input = page.locator("#email")
        self.password_input = page.locator("[name='password']")

        self.login_button = page.locator("button[data-qa-id='login_submit_button']")
        self.register_button = page.get_by_role("link", name="Зарегистрироваться")

    @allure.step("Открыть страницу авторизации")
    def open(self):
        self.page.goto(self.url)

    @allure.step("Авторизироваться пользователем")
    def login(self, email: str, password: str) -> CinescopeHomePage:
        self.enter_text(self.email_input, email)
        self.enter_text(self.password_input, password)
        self.click_element(self.login_button)
        self.page.wait_for_timeout(30000)
        self.refresh_page()
        self.wait_redirect_for_url(self.home_url)

        return CinescopeHomePage(self.page)

    def assert_redirect_to_home_page(self):
        self.wait_redirect_for_url(self.home_url)

    def assert_allert_was_pop_up(self):
        self.check_pop_up_element_with_text("Вы вошли в аккаунт")

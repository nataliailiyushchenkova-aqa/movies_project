import allure
from playwright.sync_api import Page

from models.page_object_models.base_page import BasePage


class CinescopRegisterPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page
        self.url = f"{self.home_url}register"

        self.full_name_input = page.locator("[data-qa-id='register_full_name_input']")
        self.email_input = page.locator("[data-qa-id='register_email_input']")
        self.password_input = page.locator("[data-qa-id='register_password_input']")
        self.repeat_password_input = page.locator(
            "[data-qa-id='register_password_repeat_input']"
        )
        self.register_button = page.locator("[data-qa-id='register_submit_button']")
        self.sign_button = page.get_by_role("button", name="Войти")

    @allure.step("Открыть страницу регистрации")
    def open(self):
        self.page.goto(self.url)

    @allure.step("Зарегистрировать пользователя")
    def register(
        self, full_name: str, email: str, password: str, confirm_password: str
    ):
        self.enter_text(self.full_name_input, full_name)
        self.enter_text(self.email_input, email)
        self.enter_text(self.password_input, password)
        self.enter_text(self.repeat_password_input, password)

        self.click_element(self.register_button)

    @allure.step("Проверить редирект на страницу авторизации")
    def assert_was_redirect_to_login_page(self):
        self.wait_redirect_for_url(f"{self.home_url}login")

    @allure.step("Проверить отображение поп-ап")
    def assert_alert_was_pop_up(self):
        self.check_pop_up_element_with_text("Подтвердите свою почту")

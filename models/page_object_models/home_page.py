import allure
from playwright.sync_api import Page, expect

from models.page_object_models.base_page import BasePage


class CinescopeHomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.profile_button = page.get_by_role("button", name="Профиль")

    @allure.step("Проверить что пользователь авторизован")
    def assert_user_logged_in(self):
        expect(self.profile_button).to_be_visible()

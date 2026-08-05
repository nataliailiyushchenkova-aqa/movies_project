import allure
from playwright.sync_api import Page

from models.page_object_models.base_page import BasePage


class CinescopeMoviesPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{self.home_url}movies"
        self.more_button = page.locator("[data-qa-id='more_button']")

    @allure.step("Перейти на страницу со всеми фильмами")
    def open_movies_page(self):
        self.go_to_all_movies()

    @allure.step("Открыть первый фильм")
    def open_first_movie(self):
        self.click_element(self.more_button.first)

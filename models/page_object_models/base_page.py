import allure
from playwright.sync_api import Page

from models.page_object_models.page_actions import PageAction


class BasePage(PageAction):
    def __init__(self, page: Page):
        super().__init__(page)
        self.home_url = "https://dev-cinescope.coconutqa.ru/"
        self.home_button = page.get_by_role("link", name="Cinescope")
        self.all_movies_link = page.get_by_role("link", name="Все фильмы")

    @allure.step("Переход на главную страницу из шапки сайта")
    def go_to_home_page(self):
        self.click_element(self.home_button)
        self.wait_redirect_for_url(self.home_url)

    @allure.step("Переход на страницу 'Все фильмы из шапки сайта'")
    def go_to_all_movies(self):
        self.click_element(self.all_movies_link)
        self.wait_redirect_for_url(f"{self.home_url}movies")

    def refresh_page(self):
        self.page.reload(wait_until="load")

import allure

from playwright.sync_api import Page, expect
from models.page_object_models.base_page import BasePage


class CinescopeMoviePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        self.review_input = page.locator("[data-qa-id='movie_review_input']")
        self.rating_dropdown = page.get_by_role("combobox")
        self.submit_button = page.get_by_role("button", name="Отправить")

    @allure.step("Оставить отзыв к фильму")
    def leave_review(self, review_text: str, rating: str):
        self.enter_text(self.review_input, review_text)
        self.select_rating(rating)
        self.click_element(self.submit_button)

    @allure.step("Поставить рейтинг фильму")
    def select_rating(self, rating: str):
        self.rating_dropdown.click()
        self.page.get_by_role("option", name=rating).click()

    @allure.step("Проверить отображение отзыва")
    def assert_review_visible(self, review_text: str):
        expect(self.page.get_by_text(review_text)).to_be_visible()

    @allure.step("Проверить отображение поп-ап")
    def assert_allert_was_pop_up(self):
        self.check_pop_up_element_with_text("Отзыв успешно создан")

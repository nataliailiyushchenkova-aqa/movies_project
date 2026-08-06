import allure
import pytest

from playwright.sync_api import sync_playwright, Page

from entities.existing_user import ExistingUser
from models.page_object_models.home_page import CinescopeHomePage
from models.page_object_models.login_page import CinescopeLoginPage
from models.page_object_models.movie_page import CinescopeMoviePage
from models.page_object_models.movies_page import CinescopeMoviesPage
from utils.data_generator import DataGenerator


@allure.epic("Тестирование UI")
@allure.feature("Тестирование отзыва на фильм")
@pytest.mark.ui
class TestMovieReview:
    @allure.title("Авторизированный пользователь может оставить отзыв")
    def test_existing_user_can_leave_movie_review(
        self, login_page: CinescopeLoginPage, page: Page, existing_user: ExistingUser
    ):
        review_text = DataGenerator.generate_random_review()
        rating = "5"

        login_page.login(
            existing_user.profile.email, existing_user.credentials.password
        )
        home_page = CinescopeHomePage(page)
        home_page.assert_user_logged_in()

        movies_page = CinescopeMoviesPage(page)
        movies_page.go_to_all_movies()
        movies_page.open_first_movie()
        page.screenshot(path="movie_page.png", full_page=True)

        movie_page = CinescopeMoviePage(page)
        movie_page.leave_review(review_text, rating)
        movie_page.assert_review_visible(review_text)
        movie_page.assert_allert_was_pop_up()

import pytest
from playwright.sync_api import sync_playwright, Page

from models.page_object_models.register_page import CinescopRegisterPage
from models.page_object_models.login_page import CinescopeLoginPage


@pytest.fixture(scope="function")
def page() -> Page:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        yield page

        browser.close()


@pytest.fixture(scope="function")
def register_page(page: Page) -> CinescopRegisterPage:
    register_page = CinescopRegisterPage(page)
    register_page.open()
    return register_page


@pytest.fixture(scope="function")
def login_page(page: Page) -> CinescopeLoginPage:
    login_page = CinescopeLoginPage(page)
    login_page.open()
    return login_page

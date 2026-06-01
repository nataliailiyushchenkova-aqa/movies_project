import datetime
import pytz
import requests
from constants import BASE_URL, HEADERS, REGISTER_ENDPOINT, LOGIN_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from clients.api.api_manager import ApiManager
from enums.roles import Roles
from models.test_user_model import RegisteredUserResponse, UserTestData
from pytest_mock import mocker
from unittest.mock import Mock

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from test_services.service_what_is_today import what_is_today


# Модель для ответа сервера wordlclockapi
class WorldClockResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="$id")
    currentDateTime: str
    utcOffset: str
    isDayLightSavingsTime: bool
    dayOfTheWeek: str
    timeZoneName: str
    currentFileTime: int
    ordinalDate: str
    serviceResponse: None


# Модель для запроса к сервису TodayIsHoliday
class DateTimeRequest(BaseModel):
    currentDateTime: str  # Формат: "2025-02-13T21:43Z"


# Модель для ответа от сервиса TodayIsHoliday
class WhatIsTodayResponse(BaseModel):
    message: str


# Функция выолняющая запрос в сервис worldclockapi для получения текущей даты
def get_worldclockap_time() -> WorldClockResponse:
    response = requests.get("http://worldclockapi.com/api/json/utc/now")
    assert response.status_code == 200
    return WorldClockResponse(**response.json())


class TestTodayIsHolidayServiceAPI:
    def test_worldclock(self):
        """Тест получения времени из внешнего API"""
        world_clock_response = get_worldclockap_time()
        # Выводим текущую дату и время
        current_date_time = world_clock_response.currentDateTime
        print(f"Текущая дата и время: {current_date_time}")

        assert current_date_time == datetime.now(pytz.utc).strftime(
            "%Y-%m-%dT%H:%MZ"
        ), "Дата не совпадает"

    def test_what_is_today(self):
        """Интеграционный тест с реальным сервисом"""
        world_clock_response = get_worldclockap_time()

        what_is_today_response = requests.post(
            "http://127.0.0.1:16002/what_is_today",
            json=DateTimeRequest(
                currentDateTime=world_clock_response.currentDateTime
            ).model_dump(),
        )

        assert what_is_today_response.status_code == 200, "Удаленный сервис не отвечает"
        what_is_today_data = WhatIsTodayResponse(**what_is_today_response.json())
        assert (
            what_is_today_data.message == "Сегодня нет праздников в России."
        ), "Сегодня нет праздника!"

    def test_what_is_today_BY_MOCK(self, mocker):
        # Создаем мок для функции get_wordlclockap_time Тест с моком внешней зависимости (изолированный)
        mock_response = Mock(currentDateTime="2025-01-01T00:00Z")
        mocker.patch(
            "test_mock_services.get_worldclockap_time", return_value=mock_response
        )

        world_clock_response = get_worldclockap_time()
        what_is_today_response = requests.post(
            "http://127.0.0.1:16002/what_is_today",
            json=DateTimeRequest(
                currentDateTime=world_clock_response.currentDateTime
            ).model_dump(),
        )
        assert what_is_today_response.status_code == 200, "Удаленный сервис недоступен"
        what_is_today_data = WhatIsTodayResponse(**what_is_today_response.json())
        assert what_is_today_data.message == "Новый год", "ДОЛЖЕН БЫТЬ НОВЫЙ ГОД!"

    def stub_get_worldclockap_time(self):
        class StubWorldCLockResponse:
            def __init__(self):
                self.currentDateTime = (
                    "2025-05-09T00:00Z"  # Фиксированная дата для Stub
                )

        return StubWorldCLockResponse()

    def test_what_is_today_BY_STUB(self, monkeypatch):
        # Подменяем реальную функцию get_worldclockap_time на Stub
        monkeypatch.setattr(
            "test_mock_services.get_worldclockap_time", self.stub_get_worldclockap_time
        )
        world_clock_response = get_worldclockap_time()
        what_is_today_response = requests.post(
            "http://127.0.0.1:16002/what_is_today",
            data=DateTimeRequest(
                currentDateTime=world_clock_response.currentDateTime
            ).model_dump_json(),
            headers={"Content-Type": "application/json"},
        )
        assert what_is_today_response.status_code == 200, "Удаленный сервер не отвечает"
        what_is_today_data = WhatIsTodayResponse(**what_is_today_response.json())
        assert what_is_today_data.message == "День Победы", "ДОЛЖЕН БЫТЬ ДЕНЬ ПОБЕДЫ!"

    def run_wiremock_worldclockap_time(self):
        wiremock_url = "http://localhost:8080/__admin/mappings"
        mapping = {
            "request": {"method": "GET", "url": "/wire/mock/api/json/utc/now"},
            "response": {
                "status": 200,
                "body": """{
                "$id": "1",
                "currentDateTime": "2025-03-08T00:00Z",
                "utcOffset": "00:00",
                "isDayLightSavingsTime": false,
                "dayOfTheWeek": "Wednesday",
                "timeZoneName": "UTC",
                "currentFileTime": 1324567890123,
                "ordinalDate": "2025-1",
                "serviceResponse": null
                }""",
            },
        }
        response = requests.post(wiremock_url, json=mapping)
        assert response.status_code == 201, "Не удалось настроить WireMock"

    def test_what_is_today_BY_WIREMOCK(self):
        self.run_wiremock_worldclockap_time()
        world_clock_response = requests.get(
            "http://localhost:8080/wire/mock/api/json/utc/now"
        )
        assert world_clock_response.status_code == 200
        current_date_time = WorldClockResponse(
            **world_clock_response.json()
        ).currentDateTime

        what_is_today_response = requests.post(
            "http://127.0.0.1:16002/what_is_today",
            data=DateTimeRequest(currentDateTime=current_date_time).model_dump_json(),
            headers={"Content-Type": "application/json"},
        )

        assert what_is_today_response.status_code == 200, "Удаленный сервис не отвечает"
        what_is_today_data = WhatIsTodayResponse(**what_is_today_response.json())
        assert what_is_today_data.message == "Международный женский день", "8 марта же?"


def get_fake_worldclockap_time() -> WorldClockResponse:
    response = requests.get("http://127.0.0.1:16001/fake/worldclock/api/json/utc/now")
    assert response.status_code == 200, "Удаленный сервер недоступен"
    return WorldClockResponse(**response.json())


class TestTodayIsHolidayServiceAPI:
    def test_fake_worldclockap(self):
        world_clock_response = get_fake_worldclockap_time()
        current_date_time = world_clock_response.currentDateTime
        print(f"Текущая дата и время: {current_date_time=}")

        assert current_date_time == datetime.now(pytz.utc).strftime(
            "%Y-%m-%dT%H:%MZ"
        ), "Дата не совпадает"

    def test_fake_what_is_today(self):
        world_clock_response = get_fake_worldclockap_time()
        what_is_today_response = requests.post(
            "http://127.0.0.1:16002/what_is_today",
            json=DateTimeRequest(
                currentDateTime=world_clock_response.currentDateTime
            ).model_dump(),
        )

        assert what_is_today_response.status_code == 200, "Удаленный сервис недоступен"

        what_is_today_data = WhatIsTodayResponse(**what_is_today_response.json())

        assert (
            what_is_today_data.message == "Сегодня нет праздников в России."
        ), "Сегодня нет праздника!"

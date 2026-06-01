import os
import allure
from typing import Dict, Any, Union
import logging
import json
import requests
from requests import Response
from pydantic import BaseModel
from typing import Literal

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class CustomRequester:
    """Кастомный класс для стандартизации и упрощения отправки HTTP запросов"""

    base_headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, session: requests.Session, base_url: str):
        """Инициализация кастомного реквестора

        :param session: Обьект requests.Session
        :param base_url: Базовый url api
        """
        self.session: requests.Session = session
        self.base_url: str = base_url
        self.headers: dict[str, str] = self.base_headers.copy()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def send_request(
        self,
        method: HttpMethod,
        endpoint: str,
        data: BaseModel | dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expected_status: int = 200,
        need_logging: bool = True,
        exclude_none: bool = False,
    ) -> Response:
        url: str = f"{self.base_url}{endpoint}"

        with allure.step("Подготовка запроса"):
            serialized_data = data

        if isinstance(data, BaseModel):
            serialized_data = data.model_dump(mode="json", exclude_none=exclude_none)

        with allure.step("Формирование данных запроса"):
            if serialized_data:
                allure.attach(
                    json.dumps(serialized_data, indent=4, ensure_ascii=False),
                    name="Request payload",
                    attachment_type=allure.attachment_type.JSON,
                )

            if params:
                allure.attach(
                    json.dumps(params, indent=4, ensure_ascii=False),
                    name="Query params",
                    attachment_type=allure.attachment_type.JSON,
                )
        with allure.step(f"Отправка запроса {method} {endpoint}"):
            response = self.session.request(
                method=method,
                url=url,
                json=serialized_data,
                params=params,
                headers=self.headers,
            )

        with allure.step("Формирование данных ответа"):
            allure.attach(
                str(response.status_code),
                name="Response status code",
                attachment_type=allure.attachment_type.TEXT,
            )

        try:
            formatted_response = json.dumps(
                response.json(), indent=4, ensure_ascii=False
            )
        except Exception:
            formatted_response = response.text

        allure.attach(
            formatted_response,
            name="Response body",
            attachment_type=allure.attachment_type.JSON,
        )

        if need_logging:
            with allure.step("Логирование ответа"):
                self.log_request_and_response(response)

        assert response.status_code == expected_status, (
            f"Неожиданный статус код {response.status_code} "
            f"Ожидалось: {expected_status} "
            f"Тело ответа: {response.text}"
        )

        return response

    def _update_session_headers(self, **kwargs):
        self.headers.update(kwargs)
        self.session.headers.update(self.headers)

    def log_request_and_response(self, response):
        try:
            request = response.request
            GREEN = "\033[32m"
            RED = "\033[31m"
            RESET = "\033[0m"
            headers = "\\\n".join(
                [f"-H '{header}: {value}'" for header, value in request.headers.items()]
            )
            full_test_name = f"pytest {os.environ.get('PYTEST_CURRENT_TEST', '').replace('(call)', '')}"

            body = ""
            if hasattr(request, "body") and request.body is not None:
                if isinstance(request.body, bytes):
                    body = request.body.decode("utf-8")
                body = f"-d '{body}' \n" if body != "{}" else ""

            self.logger.info(f"\n{'=' * 40}) REQUEST {'=' * 40})")
            self.logger.info(
                f"{GREEN} {full_test_name} {RESET}\n"
                f"curl -X {request.method} '{request.url} \\\n'"
                f"{headers} \\\n"
                f"{body}"
            )

            response_status = response.status_code
            is_success = response.ok
            response_data = response.text

            try:
                response_data = json.dumps(
                    json.loads(response.text), indent=4, ensure_ascii=False
                )
            except json.JSONDecodeError:
                pass

            self.logger.info(f"\n{'=' * 40} RESPONSE {'=' * 40}")
            if not is_success:
                self.logger.info(
                    f"\tSTATUS_CODE: {RED} {response_status} {RESET}\n"
                    f"\tDATA:\n{response_data}"
                )
            else:
                self.logger.info(
                    f"\tSTATUS_CODE: {GREEN} {response_status} {RESET}\n"
                    f"\tDATA:\n{response_data}"
                )
            self.logger.info(f"{'=' * 80}\n")
        except Exception as e:
            self.logger.error(f"\nLogging falied: {type(e)} - {e}")

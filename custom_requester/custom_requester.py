import os
from typing import Optional, Dict, Any, Union

import logging
import json
import requests


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
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        need_logging: bool = True,
    ):
        """
        Универсальный метод для отправки запросов.
        :param method: HTTP метод (GET, POST, PUT, DELETE и т.д.).
        :param endpoint: Эндпоинт (например, "/login").
        :param data: Тело запроса (JSON-данные).
        :param params: Параметры запроса qwery params
        :param expected_status: Ожидаемый статус-код (по умолчанию 200).
        :param need_logging: Флаг для логирования (по умолчанию True).
        :return: Объект ответа requests.Response.

        """
        url: str = f"{self.base_url}{endpoint}"
        response = self.session.request(
            method, url, json=data, params=params, headers=self.headers
        )
        if need_logging:
            self.log_request_and_response(response)

        if response.status_code != expected_status:
            raise ValueError(
                f"Unexpected status code {response.status_code}. Expected: {expected_status}"
            )
        return response

    def _update_session_headers(self, **kwargs):
        """
        Обновление заголовков сессии.
        :param kwargs: Дополнительные заголовки.
        """
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

                # Логируем запрос
            self.logger.info(f"\n{'=' * 40}) REQUEST {'=' * 40})")
            self.logger.info(
                f"{GREEN} {full_test_name} {RESET}\n"
                f"curl -X {request.method} '{request.url} \\\n'"
                f"{headers} \\\n"
                f"{body}"
            )

            # обрабатываем ответ

            response_status = response.status_code
            is_success = response.ok
            response_data = response.text

            # Попытка сформировать JSON

            try:
                response_data = json.dumps(
                    json.loads(response.text), indent=4, ensure_ascii=False
                )
            except json.JSONDecodeError:
                pass  # оставляем текст если это не json

            # Логируем ответ
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

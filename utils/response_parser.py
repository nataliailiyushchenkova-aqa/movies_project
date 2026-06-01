import allure
from typing import TypeVar, Type
from pydantic import BaseModel
from requests import Response

T = TypeVar("T", bound=BaseModel)


@allure.step("Преобразовать ответ в модель {model}")
def deserialize_response(response: Response, model: Type[T]) -> T:
    try:
        response_data = response.json()
    except ValueError as error:
        raise AssertionError("Ответ сервера содержит невалидный JSON") from error

    return model.model_validate(response_data)

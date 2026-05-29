from typing import Union

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: Union[str, list[str]]
    error: str | None = None
    statusCode: int | None = None

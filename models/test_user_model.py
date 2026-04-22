import datetime

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List

from enums.roles import Roles


class TestUserData(BaseModel):
    email: str = Field(..., description="Email пользователя")
    fullName: str = Field(..., description="Имя пользователя")
    password: str = Field(
        ..., min_length=8, max_length=20, description="Пароль пользователя"
    )
    passwordRepeat: str = Field(..., description="Пароли должны совпадать")
    # одно или несколько значений в списке из enum Roles
    roles: list[Roles] = Field(default=[Roles.USER], description="Роль пользователя")
    # опциональное поле banned булево значение
    banned: Optional[bool] = Field(default=None, description="Забанен ли пользоватепь")
    # опциональное поле verified булево значение
    verified: Optional[bool] = Field(
        default=None, description="Подтвержден ли пользовтатель"
    )

    class Config:
        json_encoders = {Roles: lambda v: v.value}

    @field_validator("passwordRepeat")
    @classmethod
    def check_password_repeat(cls, value: str, info) -> str:
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return value


class RegisteredUserResponse(BaseModel):
    id: str
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    fullName: str
    verified: bool
    banned: bool
    roles: List[Roles]
    createdAt: str

    @field_serializer("roles")
    def serialize_roles(self, roles: List[Roles]) -> List[str]:
        return [role.value for role in roles]

    @field_validator("createdAt")
    @classmethod
    def validate_created_at(cls, value: str):
        try:
            datetime.datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(
                "Некоректный формат даты и времени. Ожидается формат ISO 8601."
            )
        return value


class LoginUserInfo(BaseModel):
    id: str
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    fullName: str
    roles: list[Roles]

    @field_serializer("roles")
    def serialize_roles(self, roles: List[Roles]) -> List[str]:
        return [role.value for role in roles]


class LoginUserResponse(BaseModel):
    user: LoginUserInfo
    accessToken: str
    refreshToken: str
    expiresIn: int


class PatchUserResponse(BaseModel):
    id: Optional[str] = None
    email: str
    fullName: str
    verified: bool
    banned: bool
    roles: list[Roles]
    createdAt: str

    @field_serializer("roles")
    def serialize_roles(self, roles: List[Roles]) -> List[str]:
        return [role.value for role in roles]

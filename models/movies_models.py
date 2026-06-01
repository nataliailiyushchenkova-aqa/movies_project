import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_serializer
from typing import Any, List
from enums.location import Location


class MoviesQueryParams(BaseModel):
    """Модель параметров для GET /movies"""

    pageSize: int | None = None
    page: int | None = None
    minPrice: int | None = None
    maxPrice: int | None = None
    locations: list[Location] | None = None
    published: bool | None = None
    genreId: int | None = None
    createdAt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Преобразует в словарь исключая None значения"""
        return self.model_dump(exclude_none=True)


class MovieData(BaseModel):
    # Модель body для POST/movies
    name: str = Field(..., description="Название фильма")
    imageUrl: str | None = Field(default="https://image.url", description="Ссылка")
    price: int = Field(default=100, description="Цена фильма")
    description: str = Field(..., description="Описание фильма")
    location: Location = Field(default=Location.SPB, description="Локация фильма")
    published: bool = Field(default=True, description="Опубликован ли фильм")
    genreId: int = Field(default=1, description="ID жанра фильма")

    @field_serializer("location")
    def serialize_location(self, loc: Location) -> str:
        return loc.value


# Модель для жанра
class GenreSchema(BaseModel):
    name: str


# Модель для фильма
class MovieSchema(BaseModel):
    id: int
    name: str
    price: int
    description: str
    imageUrl: str | None = None
    location: Location
    published: bool
    genreId: int
    genre: GenreSchema
    createdAt: datetime.datetime
    rating: int | None = None


class MovieFilterInfo(BaseModel):
    id: int
    published: bool
    price: int


# Модель ответа
class MoviesResponseSchema(BaseModel):
    movies: list[MovieSchema]
    count: int
    page: int
    pageSize: int
    pageCount: int


class PatchMovieRequest(BaseModel):
    name: str | None = None
    imageUrl: str | None = None
    price: int | None = None
    description: str | None = None
    location: Location | None = None
    published: bool | None = None
    genreId: int | None = None

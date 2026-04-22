import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from enums.location import Location


class MoviesQueryParams(BaseModel):
    """Модель параметров для GET /movies"""

    pageSize: Optional[int] = None
    page: Optional[int] = None
    minPrice: Optional[int] = None
    maxPrice: Optional[int] = None
    locations: Optional[List[Location]] = None
    published: Optional[bool] = None
    genreId: Optional[int] = None
    createdAt: Optional[str] = None

    def to_dict(self):
        """Преобразует в словарь исключая None значения"""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class MovieData(BaseModel):
    # Модель body для POST/movies
    name: str = Field(..., description="Название фильма")
    imageUrl: Optional[str] = Field(default="https://image.url", description="Ссылка")
    price: int = Field(default=100, ge=0, description="Цена фильма")
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
    imageUrl: Optional[str]
    location: Location
    published: bool
    genreId: int
    genre: GenreSchema
    createdAt: datetime.datetime
    rating: int


# Модель ответа
class MoviesResponseSchema(BaseModel):
    movies: list[MovieSchema]
    count: int
    page: int
    pageSize: int
    pageCount: int

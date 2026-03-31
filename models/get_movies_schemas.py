from typing import Optional, List
import datetime

from pydantic import BaseModel, Field

# модель для жанра
class GenreSchema(BaseModel):
	name: str

# модель для фильма
class MovieSchema(BaseModel):
	id: int
	name: str
	description: str
	genre_id: int = Field(alias = "genreId")
	image_url: str | None = Field(alias = "imageUrl", default = None)
	price: int
	rating: int
	location: str
	published: bool
	created_at: datetime.datetime = Field(alias = "createdAt")

	genre: GenreSchema

	class Config:
		populate_by_name = True

# модель ответа
class MoviesResponseSchema(BaseModel):
	movies: list[MovieSchema]
	count: int
	page: int
	page_size: int = Field(alias = "pageSize")
	page_count: int = Field(alias = "pageCount")



from dataclasses import dataclass
import datetime


@dataclass(slots=True)
class CreatedMovieData:
    id: int
    price: int
    published: bool


@dataclass(slots=True)
class CreatedMovieWithDate:
    id: int
    created_at: datetime.datetime

from dataclasses import dataclass
from typing import Optional, List


def to_camel_case(snake_str: str):
	parts = snake_str.split('_')
	return parts[0] + ''.join(part.capitalize() for part in parts[1:])


@dataclass
class MoviesQweryParams:
	"""модель параметров для GET /movies"""
	page_size: Optional[int] = None
	page: Optional[int] = None
	min_price: Optional[int] = None
	max_price: Optional[int] = None
	locations: Optional[List[str]] = None
	published: Optional[bool] = None
	genre_id: Optional[int] = None
	created_at: Optional[str] = None

	def to_params(self) -> dict:
		params = {}
		for key, value in self.__dict__.items():
			if value is not None:
				params[to_camel_case(key)] = value
		return params

from sqlalchemy.orm import Session


from db_models.user import UserDBModel
from db_models.movie import MovieDBModel


class DBHelper:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_test_user(self, user_data: dict) -> UserDBModel:
        user = UserDBModel(**user_data)
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def get_user_by_id(self, user_id: str):
        return (
            self.db_session.query(UserDBModel).filter(UserDBModel.id == user_id).first()
        )

    def get_user_by_email(self, email: str):
        return (
            self.db_session.query(UserDBModel)
            .filter(UserDBModel.email == email)
            .first()
        )

    def user_exists_by_email(self, email: str) -> bool:
        return (
            self.db_session.query(UserDBModel)
            .filter(UserDBModel.email == email)
            .count()
            > 0
        )

    def delete_user(self, user: UserDBModel):
        self.db_session.delete(user)
        self.db_session.commit()

    def create_movie_from_generator(self, movie_data) -> MovieDBModel:
        raw = movie_data.model_dump()
        db_dict = {
            "name": raw["name"],
            "price": float(raw["price"]),
            "description": raw["description"],
            "image_url": raw["imageUrl"],
            "location": (
                raw["location"].value
                if hasattr(raw["location"], "value")
                else str(raw["location"])
            ),
            "published": raw["published"],
            "genre_id": str(raw["genreId"]),
        }

        return self.create_test_movie(db_dict)

    def create_test_movie(self, movie_data: dict) -> MovieDBModel:
        movie = MovieDBModel(**movie_data)
        self.db_session.add(movie)
        self.db_session.commit()
        self.db_session.refresh(movie)
        return movie

    def get_movie_by_id(self, movie_id: str):
        return (
            self.db_session.query(MovieDBModel)
            .filter(MovieDBModel.id == movie_id)
            .first()
        )

    def get_movie_by_name(self, name: str):
        return (
            self.db_session.query(MovieDBModel)
            .filter(MovieDBModel.name == name)
            .first()
        )

    def delete_movie(self, movie: MovieDBModel):
        self.db_session.delete(movie)
        self.db_session.commit()

    def cleanup_test_data(self, objects_to_delete: list):
        for obj in objects_to_delete:
            if obj:
                self.db_session.delete(obj)
        self.db_session.commit()

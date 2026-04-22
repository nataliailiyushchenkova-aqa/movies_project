from clients.api.auth_api import AuthAPI
from clients.api.user_api import UserAPI
from clients.api.movie_api import MoviesAPI


class ApiManager:
    def __init__(self, session):
        self.session = session
        self.auth_api = AuthAPI(session)
        self.user_api = UserAPI(session)
        self.movies_api = MoviesAPI(session)

    def close_session(self):
        self.session.close()

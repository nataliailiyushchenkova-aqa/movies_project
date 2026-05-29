from sqlalchemy import create_engine, Column, String, Boolean, DateTime, text

from resources.db_creds import DbCreds

from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

host = DbCreds.HOST
port = DbCreds.PORT
database_name = DbCreds.DB_NAME
username = DbCreds.USER
password = DbCreds.PASSWORD

engine = create_engine(
    f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database_name}",
    echo=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    # Создает новую сессию
    return SessionLocal()


def sql_alchemy_SQL():
    query = """
    SELECT id, email, full_name, "password", created_at, updated_at, verified, banned, roles
    FROM public.users
    WHERE id = :user_id;
    """
    user_id = "995c7fa5-34b3-4f48-93a6-ffbf7b6dd360"

    with engine.connect() as connection:
        result = connection.execute(text(query), {"user_id": user_id})
        for row in result:
            print(row)


if __name__ == "__main__":
    sql_alchemy_SQL()


def sql_alchemy_OMR():
    # Базовый класс для моделей
    Base = declarative_base()

    # Модель таблицы users
    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        email = Column(String)
        full_name = Column(String)
        password = Column(String)
        created_at = Column(DateTime)
        updated_at = Column(DateTime)
        verified = Column(Boolean)
        banned = Column(Boolean)
        roles = Column(String)

    # Cоздаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    user_id = "ae5f12bf-7aa0-40cc-a8b1-761f76acc253"
    # Выполняем запрос
    user = session.query(User).filter(User.id == user_id).first()

    # выводим результат
    if user:
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Full Name: {user.full_name}")
        print(f"Password: {user.password}")
        print(f"Created At: {user.created_at}")
        print(f"Updated At: {user.updated_at}")
        print(f"Verified: {user.verified}")
        print(f"Banned: {user.banned}")
        print(f"Roles: {user.roles}")
    else:
        print("Пользователь не найден.")


if __name__ == "__main__":
    sql_alchemy_OMR()

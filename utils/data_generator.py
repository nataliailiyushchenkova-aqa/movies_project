import datetime
import allure
import random
import string
import uuid
from faker import Faker

from db_models.user_data import UserDbData
from enums.location import Location
from models.movies_models import MovieData

faker = Faker()


class DataGenerator:
    @staticmethod
    def generate_random_email():
        """Генерация рандомного email"""
        return f"aqa_{uuid.uuid4().hex}@gmail.com"

    @staticmethod
    def generate_random_name():
        """Генерация рандомного fullName"""
        return f"{faker.first_name()} {faker.last_name()}"

    @staticmethod
    @allure.step("Сгенерировать уникальный пароль")
    def generate_random_password():
        """
        Генерация рандомного пароля, соответствующего требованиям:
        - Минимум 1 буква.
        - Минимум 1 цифра.
        - Допустимые символы.
        - Длина от 8 до 20 символов.
        """
        # Гарантируем наличие хотя бы одной буквы и одной цифры
        letters = random.choice(string.ascii_lowercase)
        uppercase = random.choice(string.ascii_uppercase)
        digits = random.choice(string.digits)

        # Дополняем пароль случайными символами из допустимого набора
        special_chars = "?@#$%^&*|:"
        all_chars = string.ascii_letters + string.digits + special_chars
        total_length = random.randint(8, 20)
        remaining_length = total_length - 3
        remaining_length = max(0, remaining_length)
        remaining_chars = "".join(random.choices(all_chars, k=remaining_length))

        # перемешиваем пароль для рандомизации
        password = list(letters + digits + remaining_chars + uppercase)
        random.shuffle(password)

        return "".join(password)

    # @staticmethod
    # def generate_user_payload(verified: bool = True, banned: bool = False):
    #     """Генерация рандомного пользователя для POST/user"""
    #     random_email = DataGenerator.generate_random_email()
    #     random_name = DataGenerator.generate_random_name()
    #     random_password = DataGenerator.generate_random_password()
    #
    #     return {
    #         "fullName": random_name,
    #         "email": random_email,
    #         "password": random_password,
    #         "verified": verified,
    #         "banned": banned,
    #     }

    @staticmethod
    def generate_user_data() -> UserDbData:
        from uuid import uuid4

        return UserDbData(
            id=str(uuid4()),
            email=DataGenerator.generate_random_email(),
            full_name=DataGenerator.generate_random_name(),
            password=DataGenerator.generate_random_password(),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            verified=False,
            banned=False,
            roles="{USER}",
        )

    @staticmethod
    @allure.step("Сформировать тестовые данные для создания фильма")
    def generate_movie_data(
        name: str = None,
        published: bool = True,
        genre_id: int = None,
        price: int = None,
        location: Location = None,
    ):
        """
        Генерация данных для создания фильма.
        Параметры можно переопределить вручную (name, published, genre_id, price),
        если нужны конкретные значения для теста.
        """
        if name is None:
            name = faker.sentence(nb_words=4)
        if genre_id is None:
            genre_id = random.randint(1, 3)

        if price is None:
            price = random.randint(1, 1000)

        if location is None:
            location = random.choice(list(Location))

        return MovieData(
            name=name,
            imageUrl=faker.image_url(),
            price=price,
            description=faker.text(max_nb_chars=80),
            location=location,
            published=published,
            genreId=genre_id,
        )

    @staticmethod
    @allure.step("Сгенерировать рандомную цену")
    def generate_random_price():
        """Генерация рандомной цены для movies"""
        return random.randint(1, 1000)

    @staticmethod
    @allure.step("Сгенерировать рандомный id пользователя")
    def generate_random_user_id():
        """Генерация рандомного id users"""
        return str(uuid.uuid4())

    @staticmethod
    @allure.step("Сгенерировать рандомное имя фильма")
    def generate_random_movie_name(words_count: int = 3):
        return faker.sentence(nb_words=words_count).rstrip(".")

    @staticmethod
    @allure.step("Сгенерировать рандомный отзыв")
    def generate_random_review(words_count: int = 5):
        return faker.sentence(nb_words=words_count).rstrip(".")

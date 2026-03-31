import random
import string
from faker import Faker
faker = Faker()

class DataGenerator:
	@staticmethod
	def generate_random_email():
		random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
		return f"kek{random_string}@gmail.com"

	@staticmethod
	def generate_random_name():
		return f"{faker.first_name()} {faker.last_name()}"

	@staticmethod
	def generate_random_password():
		"""
		        Генерация пароля, соответствующего требованиям:
		        - Минимум 1 буква.
		        - Минимум 1 цифра.
		        - Допустимые символы.
		        - Длина от 8 до 20 символов.
		        """
	# Гарантируем наличие хотя бы одной буквы и одной цифры
		letters = random.choice(string.ascii_lowercase)
		uppercase = random.choice(string.ascii_uppercase)
		digits = random.choice(string.digits)

		#Дополняем пароль случайными символами из допустимого набора
		special_chars = "?@#$%^&*|:"
		all_chars = string.ascii_letters + string.digits + special_chars
		remaining_length = random.randint(6, 18)
		remaining_chars = ''.join(random.choices(all_chars, k=remaining_length))

		#перемешиваем пароль для рандомизации
		password = list(letters + digits + remaining_chars+uppercase)
		random.shuffle(password)

		return ''.join(password)

	@staticmethod
	def generate_movie_data(name: str = None, published: bool = True, genre_id: int = None, price: int = None):
		"""
		       Генерация данных для создания фильма.
		       Параметры можно переопределить вручную (name, published, genre_id, price),
		       если нужны конкретные значения для теста.
		       """
		if name is None:
			name = faker.sentence(nb_words=4)
		if genre_id is None:
			genre_id = random.randint(1, 4)

		if price is None:
			price = random.randint(1, 1000)

		return {
			"name": name,
			"imageUrl": faker.image_url(),
			"price": price,
			"description": faker.text(max_nb_chars=80),
			"location": random.choice(["MSK", "SPB"]),
			"published": published,
			"genreId": genre_id
		}

	@staticmethod
	def generate_random_price():
		return random.randint(1, 1000)

	@staticmethod
	def generate_random_movie_name():
		return faker.sentence(nb_words=3)
import psycopg2
from resources.db_creds import DbCreds


def connect_to_postgres():
    try:
        with psycopg2.connect(
            dbname=DbCreds.DB_NAME,
            user=DbCreds.USER,
            password=DbCreds.PASSWORD,
            host=DbCreds.HOST,
            port=DbCreds.PORT,
        ) as connection:
            with connection.cursor() as cursor:
                print("Подключение успешно установлено")
                print("Информация о сервере PostgreSQL:")
                print(connection.get_dsn_parameters(), "\n")

        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("Вы подключены к - ", record, "\n")

    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL {e}")
    except Exception as e:
        print(f"Произошла ошибка  {e}")


if __name__ == "__main__":
    connect_to_postgres()

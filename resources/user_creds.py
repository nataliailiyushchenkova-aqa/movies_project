import os
from dotenv import load_dotenv
from entities.user import User

load_dotenv()


class SuperAdminCreds(User):
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")

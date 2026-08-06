import os
from dotenv import load_dotenv
from entities.authenticateduser import AuthenticatedUser

load_dotenv()


class SuperAdminCreds(AuthenticatedUser):
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")

from pydantic import BaseModel
from datetime import datetime

from enums.roles import Roles


class UserDbData(BaseModel):
    id: str
    email: str
    full_name: str
    password: str
    created_at: datetime
    updated_at: datetime
    verified: bool
    banned: bool
    roles: list[Roles]

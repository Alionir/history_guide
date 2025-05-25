from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class UserRole(Enum):
    USER = 1
    MODERATOR = 2
    ADMIN = 3

@dataclass
class User:
    user_id: int
    username: str
    email: str
    password_hash: str
    role_id: int
    created_at: datetime
    
    @property
    def role(self) -> UserRole:
        return UserRole(self.role_id)
    
    @property
    def is_admin(self) -> bool:
        return self.role_id == UserRole.ADMIN.value
    
    @property
    def is_moderator(self) -> bool:
        return self.role_id >= UserRole.MODERATOR.value
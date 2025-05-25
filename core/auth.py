import bcrypt
import logging
from typing import Optional
from models.user import User, UserRole
from data_access.user_repository import UserRepository

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.current_user: Optional[User] = None
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            user = self.user_repository.get_by_username(username)
            if user and self.verify_password(password, user.password_hash):
                self.current_user = user
                logger.info(f"User {username} authenticated successfully")
                return user
            logger.warning(f"Authentication failed for user {username}")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Регистрация нового пользователя (исправленный метод)"""
        try:
            # Проверка существования пользователя
            username_exists, email_exists = self.user_repository.check_user_exists(username, email)
            if username_exists:
                logger.warning(f"User {username} already exists")
                raise ValueError(f"Пользователь с именем '{username}' уже существует")
            
            if email_exists:
                logger.warning(f"Email {email} already exists")
                raise ValueError(f"Пользователь с email '{email}' уже существует")
            
            # Хеширование пароля и создание пользователя
            password_hash = self.hash_password(password)
            user = self.user_repository.create(username, email, password_hash, UserRole.USER.value)
            
            if user:
                logger.info(f"User {username} registered successfully")
                return user
            else:
                logger.error(f"Failed to create user {username}")
                raise ValueError("Не удалось создать пользователя")
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise e
    
    def register(self, username: str, email: str, password: str) -> Optional[User]:
        """Регистрация нового пользователя (старый метод для совместимости)"""
        return self.register_user(username, email, password)
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Проверка прав доступа"""
        if not self.current_user:
            return False
        return self.current_user.role_id >= required_role.value
    
    def logout(self):
        """Выход из системы"""
        if self.current_user:
            logger.info(f"User {self.current_user.username} logged out")
            self.current_user = None
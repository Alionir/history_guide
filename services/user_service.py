import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_service import BaseService
from data_access import UserRepository
from core.exceptions import AuthenticationError, ValidationError, DuplicateEntityError, EntityNotFoundError
from core.auth import AuthService
class UserService(BaseService):
    """Сервис для работы с пользователями"""
    
    def __init__(self):
        super().__init__()
        self.user_repo = UserRepository()
        self.auth_service = AuthService()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация пользователя"""
        if not username or not password:
            raise ValidationError("Имя пользователя и пароль обязательны")
        
        user = self.user_repo.get_by_username(username.strip())
        if not user:
            self._log_action(0, 'LOGIN_FAILED', description=f'Неудачная попытка входа: {username}')
            raise AuthenticationError("Неверное имя пользователя или пароль")
        
        # Проверяем пароль
        if not self._verify_password(password, user['password_hash']):
            self._log_action(user['user_id'], 'LOGIN_FAILED', description='Неверный пароль')
            raise AuthenticationError("Неверное имя пользователя или пароль")
        
        # Успешная аутентификация
        self._log_action(user['user_id'], 'LOGIN_SUCCESS', description='Успешный вход в систему')
        
        # Возвращаем данные пользователя без пароля
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'role_id': user['role_id'],
            'role_name': user.get('role_name', ''),
            'created_at': user['created_at']
        }
    
    def register_user(self, username: str, email: str, password: str, 
                     confirm_password: str) -> Dict[str, Any]:
        """Регистрация нового пользователя"""
        # Валидация входных данных
        self._validate_registration_data(username, email, password, confirm_password)
        
        # Проверка существования пользователя
        username_exists, email_exists = self.user_repo.check_user_exists(username.strip(), email.strip())
        
        if username_exists:
            raise DuplicateEntityError("Пользователь с таким именем уже существует")
        if email_exists:
            raise DuplicateEntityError("Пользователь с таким email уже существует")
        
        # Хеширование пароля
        password_hash = self._hash_password(password)
        
        # Создание пользователя
        new_user = self.user_repo.create(
            username=username.strip(),
            email=email.strip(),
            password_hash=password_hash,
            role_id=1  # Обычный пользователь по умолчанию
        )
        
        if not new_user:
            raise ValidationError("Не удалось создать пользователя")
        
        self._log_action(new_user.user_id, 'USER_REGISTERED', 'USER', new_user.user_id,
                        f'Зарегистрирован новый пользователь: {username}')
        
        return {
            'user_id': new_user.user_id,
            'username': new_user.username,
            'email': new_user.email,
            'role_id': new_user.role_id,
            'created_at': new_user.created_at,
            'message': 'Пользователь успешно зарегистрирован'
        }
    
    def update_user_profile(self, user_id: int, email: str, current_password: str = None,
                           new_password: str = None, confirm_password: str = None) -> Dict[str, Any]:
        """Обновление профиля пользователя"""
        # Проверяем существование пользователя
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("Пользователь не найден")
        
        # Валидация email
        if not email or not self._is_valid_email(email):
            raise ValidationError("Некорректный email адрес")
        
        # Если меняется пароль, проверяем текущий пароль
        password_hash = None
        if new_password:
            if not current_password:
                raise ValidationError("Для изменения пароля необходимо указать текущий пароль")
            
            if not self._verify_password(current_password, user['password_hash']):
                raise ValidationError("Неверный текущий пароль")
            
            if new_password != confirm_password:
                raise ValidationError("Новый пароль и подтверждение не совпадают")
            
            if not self._is_strong_password(new_password):
                raise ValidationError("Пароль должен содержать минимум 8 символов, включая буквы и цифры")
            
            password_hash = self._hash_password(new_password)
        
        # Обновляем профиль
        success = self.user_repo.update_profile(user_id, email.strip(), password_hash)
        
        if not success:
            raise ValidationError("Не удалось обновить профиль")
        
        self._log_action(user_id, 'PROFILE_UPDATED', 'USER', user_id, 'Профиль пользователя обновлен')
        
        return {
            'success': True,
            'message': 'Профиль успешно обновлен'
        }
    
    def change_user_role(self, admin_id: int, user_id: int, new_role_id: int) -> Dict[str, Any]:
        """Изменение роли пользователя (только для админов)"""
        # Проверяем права администратора
        self._validate_user_permissions(admin_id, 3)  # Роль администратора
        
        # Проверяем существование пользователя
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("Пользователь не найден")
        
        # Нельзя изменить роль самому себе
        if admin_id == user_id:
            raise ValidationError("Нельзя изменить собственную роль")
        
        # Проверяем валидность новой роли
        roles = self.user_repo.get_all_roles()
        valid_role_ids = [role['role_id'] for role in roles]
        if new_role_id not in valid_role_ids:
            raise ValidationError("Некорректная роль")
        
        # Изменяем роль
        success = self.user_repo.update_user_role(user_id, new_role_id, admin_id)
        
        if not success:
            raise ValidationError("Не удалось изменить роль пользователя")
        
        old_role = next((r['name'] for r in roles if r['role_id'] == user['role_id']), 'Неизвестно')
        new_role = next((r['name'] for r in roles if r['role_id'] == new_role_id), 'Неизвестно')
        
        self._log_action(admin_id, 'USER_ROLE_CHANGED', 'USER', user_id,
                        f'Роль пользователя {user["username"]} изменена с {old_role} на {new_role}')
        
        return {
            'success': True,
            'message': f'Роль пользователя изменена на {new_role}'
        }
    
    def get_users_list(self, admin_id: int, offset: int = 0, limit: int = 50,
                      search_term: str = None, role_filter: int = None) -> List[Dict[str, Any]]:
        """Получение списка пользователей (для админов/модераторов)"""
        # Проверяем права (модератор или админ)
        self._validate_user_permissions(admin_id, 2)
        
        users = self.user_repo.get_all_users(offset, limit, search_term, role_filter)
        
        self._log_action(admin_id, 'USERS_LIST_VIEWED', description='Просмотр списка пользователей')
        
        return users
    
    def _validate_registration_data(self, username: str, email: str, password: str, confirm_password: str) -> None:
        """Валидация данных регистрации"""
        errors = []
        
        if not username or len(username.strip()) < 3:
            errors.append("Имя пользователя должно содержать минимум 3 символа")
        
        if not self._is_valid_email(email):
            errors.append("Некорректный email адрес")
        
        if not self._is_strong_password(password):
            errors.append("Пароль должен содержать минимум 8 символов, включая буквы и цифры")
        
        if password != confirm_password:
            errors.append("Пароль и подтверждение не совпадают")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    def _hash_password(self, password: str) -> str:
        return self.auth_service.hash_password(password)

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        return self.auth_service.verify_password(password, stored_hash)
    
    def _is_valid_email(self, email: str) -> bool:
        """Проверка валидности email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    def _is_strong_password(self, password: str) -> bool:
        """Проверка силы пароля"""
        import re
        if len(password) < 8:
            return False
        if not re.search(r'[a-zA-Z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
from .base_repository import BaseRepository
from models.user import User, UserRole

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по имени"""
        result = self._execute_function('sp_get_user_by_username', (username,))
        return self._map_to_user(result[0]) if result else None
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        result = self._execute_function('sp_get_user_by_id', (user_id,))
        return result[0] if result else None
    
    def create(self, username: str, email: str, password_hash: str, role_id: int = 1) -> Optional[User]:
        """Создание нового пользователя"""
        try:
            # Попробуем сначала с функцией sp_register_user
            result = self._execute_function('sp_register_user', (username, email, password_hash, role_id))
            
            if result and result[0].get('success'):
                return User(
                    user_id=result[0]['user_id'],
                    username=result[0]['username'],
                    email=result[0]['email'],
                    password_hash='',  # Не возвращаем хеш пароля
                    role_id=result[0]['role_id'],
                    created_at=result[0]['created_at']
                )
        except Exception as e:
            logger.error(f"Error with sp_register_user: {e}")
            # Если функция БД не работает, создадим пользователя напрямую
            return self._create_user_direct(username, email, password_hash, role_id)
        
        return None
    
    def _create_user_direct(self, username: str, email: str, password_hash: str, role_id: int = 1) -> Optional[User]:
        """Прямое создание пользователя через SQL (запасной вариант)"""
        try:
            from datetime import datetime
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Вставляем нового пользователя
                    insert_query = """
                        INSERT INTO public.users (username, email, password_hash, role_id, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING user_id, username, email, role_id, created_at
                    """
                    
                    created_at = datetime.now()
                    cursor.execute(insert_query, (username, email, password_hash, role_id, created_at))
                    
                    result = cursor.fetchone()
                    if result:
                        conn.commit()
                        return User(
                            user_id=result[0],
                            username=result[1],
                            email=result[2],
                            password_hash='',  # Не возвращаем хеш пароля
                            role_id=result[3],
                            created_at=result[4]
                        )
                    
        except Exception as e:
            logger.error(f"Error creating user directly: {e}")
            
        return None
    
    def check_user_exists(self, username: str = None, email: str = None) -> Tuple[bool, bool]:
        """Проверка существования пользователя"""
        try:
            result = self._execute_function('sp_check_user_exists', (username, email))
            if result:
                return result[0]['username_exists'], result[0]['email_exists']
        except Exception as e:
            logger.error(f"Error with sp_check_user_exists: {e}")
            # Запасной вариант - прямой SQL запрос
            return self._check_user_exists_direct(username, email)
        
        return False, False
    
    def _check_user_exists_direct(self, username: str = None, email: str = None) -> Tuple[bool, bool]:
        """Прямая проверка существования пользователя"""
        try:
            with self.db.get_cursor() as cursor:
                username_exists = False
                email_exists = False
                
                if username:
                    cursor.execute("SELECT COUNT(*) FROM public.users WHERE username = %s", (username,))
                    username_exists = cursor.fetchone()[0] > 0
                
                if email:
                    cursor.execute("SELECT COUNT(*) FROM public.users WHERE email = %s", (email,))
                    email_exists = cursor.fetchone()[0] > 0
                
                return username_exists, email_exists
                
        except Exception as e:
            logger.error(f"Error checking user existence directly: {e}")
            return False, False
    
    def get_all_users(self, offset: int = 0, limit: int = 50, search_term: str = None, 
                     role_filter: int = None) -> List[Dict[str, Any]]:
        """Получение списка всех пользователей"""
        return self._execute_function('sp_get_all_users', (offset, limit, search_term, role_filter))
    
    def update_user_role(self, user_id: int, new_role_id: int, admin_id: int) -> bool:
        """Изменение роли пользователя"""
        result = self._execute_function('sp_update_user_role', (user_id, new_role_id, admin_id))
        return result[0]['success'] if result else False
    
    def update_profile(self, user_id: int, email: str, password_hash: str = None) -> bool:
        """Обновление профиля пользователя"""
        result = self._execute_function('sp_update_user_profile', (user_id, email, password_hash))
        return result[0]['success'] if result else False
    
    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Получение всех ролей"""
        return self._execute_function('sp_get_all_roles')
    
    def _map_to_user(self, data: Dict[str, Any]) -> User:
        """Преобразование данных БД в объект User"""
        return User(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            role_id=data['role_id'],
            created_at=data['created_at']
        )
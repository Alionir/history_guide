import functools
import time
import logging
from typing import Callable, Any
from core.exceptions import AuthorizationError, ValidationError

logger = logging.getLogger(__name__)

def require_permissions(min_role: int):
    """Декоратор для проверки прав доступа"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Ищем user_id в аргументах
            user_id = None
            if args:
                user_id = args[0]  # Предполагаем, что первый аргумент - user_id
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            elif 'moderator_id' in kwargs:
                user_id = kwargs['moderator_id']
            elif 'admin_id' in kwargs:
                user_id = kwargs['admin_id']
            
            if user_id is None:
                raise ValidationError("User ID не найден в параметрах")
            
            # Проверяем права
            self._validate_user_permissions(user_id, min_role)
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def log_execution_time(func: Callable) -> Callable:
    """Декоратор для логирования времени выполнения"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

def validate_input(validator_class: type, data_field: str = None):
    """Декоратор для валидации входных данных"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Ищем данные для валидации
            data = None
            if data_field and data_field in kwargs:
                data = kwargs[data_field]
            elif len(args) > 1 and isinstance(args[1], dict):
                data = args[1]
            
            if data and hasattr(validator_class, 'validate_person_data'):
                validated_data = validator_class.validate_person_data(data)
                if data_field and data_field in kwargs:
                    kwargs[data_field] = validated_data
                elif len(args) > 1:
                    args = args[:1] + (validated_data,) + args[2:]
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# services/config.py
"""
Конфигурация для бизнес-сервисов
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ServiceConfig:
    """Конфигурация сервисов"""
    
    # Лимиты пагинации
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    MAX_SEARCH_RESULTS: int = 1000
    
    # Лимиты контента
    MAX_BIOGRAPHY_LENGTH: int = 10000
    MAX_DESCRIPTION_LENGTH: int = 5000
    MAX_DOCUMENT_LENGTH: int = 1000000
    MIN_SEARCH_QUERY_LENGTH: int = 2
    
    # Настройки безопасности
    MIN_PASSWORD_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    SESSION_TIMEOUT_HOURS: int = 24
    
    # Настройки экспорта
    MAX_EXPORT_RECORDS: int = 10000
    EXPORT_TIMEOUT_SECONDS: int = 300
    
    # Настройки аналитики
    MAX_ANALYTICS_PERIOD_DAYS: int = 365
    DEFAULT_ANALYTICS_PERIOD_DAYS: int = 30
    
    # Роли пользователей
    ROLES: Dict[str, int] = None
    
    def __post_init__(self):
        if self.ROLES is None:
            self.ROLES = {
                'USER': 1,
                'MODERATOR': 2,
                'ADMIN': 3
            }

# Глобальный экземпляр конфигурации
service_config = ServiceConfig()

# services/cache.py
"""
Простая система кэширования для сервисов
"""

import time
from typing import Any, Dict, Optional
from threading import Lock

class SimpleCache:
    """Простой кэш в памяти с TTL"""
    
    def __init__(self, default_ttl: int = 300):  # 5 минут по умолчанию
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() > entry['expires']:
                del self._cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Сохранение значения в кэш"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }
    
    def delete(self, key: str) -> None:
        """Удаление значения из кэша"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Очистка всего кэша"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Очистка просроченных записей"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if current_time > entry['expires']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        return len(expired_keys)

# Глобальный экземпляр кэша
service_cache = SimpleCache()

# services/notifications.py
"""
Система уведомлений для сервисов
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Типы уведомлений"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class Notification:
    """Класс уведомления"""
    
    def __init__(self, message: str, notification_type: NotificationType = NotificationType.INFO,
                 title: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.type = notification_type
        self.title = title
        self.details = details or {}
        self.timestamp = datetime.now()
        self.id = f"{int(self.timestamp.timestamp())}_{hash(message) % 10000}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'message': self.message,
            'type': self.type.value,
            'title': self.title,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self):
        self._notifications: Dict[int, List[Notification]] = {}
    
    def add_notification(self, user_id: int, message: str, 
                        notification_type: NotificationType = NotificationType.INFO,
                        title: str = None, details: Dict[str, Any] = None) -> str:
        """Добавление уведомления для пользователя"""
        notification = Notification(message, notification_type, title, details)
        
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        
        self._notifications[user_id].append(notification)
        
        # Ограничиваем количество уведомлений на пользователя
        if len(self._notifications[user_id]) > 100:
            self._notifications[user_id] = self._notifications[user_id][-100:]
        
        logger.info(f"Added {notification_type.value} notification for user {user_id}: {message}")
        
        return notification.id
    
    def get_notifications(self, user_id: int, limit: int = 50, 
                         notification_type: NotificationType = None) -> List[Dict[str, Any]]:
        """Получение уведомлений пользователя"""
        if user_id not in self._notifications:
            return []
        
        notifications = self._notifications[user_id]
        
        # Фильтрация по типу
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        
        # Сортировка по времени (новые первые)
        notifications.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Ограничение количества
        notifications = notifications[:limit]
        
        return [n.to_dict() for n in notifications]
    
    def mark_as_read(self, user_id: int, notification_id: str) -> bool:
        """Отметка уведомления как прочитанного"""
        if user_id not in self._notifications:
            return False
        
        for notification in self._notifications[user_id]:
            if notification.id == notification_id:
                notification.details['read'] = True
                return True
        
        return False
    
    def clear_notifications(self, user_id: int, notification_type: NotificationType = None) -> int:
        """Очистка уведомлений пользователя"""
        if user_id not in self._notifications:
            return 0
        
        if notification_type is None:
            count = len(self._notifications[user_id])
            self._notifications[user_id] = []
            return count
        else:
            original_count = len(self._notifications[user_id])
            self._notifications[user_id] = [
                n for n in self._notifications[user_id] 
                if n.type != notification_type
            ]
            return original_count - len(self._notifications[user_id])

# Глобальный экземпляр сервиса уведомлений
notification_service = NotificationService()
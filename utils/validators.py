import re
from typing import Any, Dict, List, Optional
from datetime import date, datetime
from core.exceptions import ValidationError

class BaseValidator:
    """Базовый класс для валидаторов"""
    
    @staticmethod
    def validate_required_string(value: Any, field_name: str, min_length: int = 1, max_length: int = None) -> str:
        """Валидация обязательной строки"""
        if value is None:
            raise ValidationError(f"Поле '{field_name}' обязательно для заполнения")
        
        if not isinstance(value, str):
            raise ValidationError(f"Поле '{field_name}' должно быть строкой")
        
        cleaned_value = value.strip()  # Здесь value уже точно строка
        
        if len(cleaned_value) < min_length:
            raise ValidationError(f"Поле '{field_name}' должно содержать минимум {min_length} символов")
        
        if max_length and len(cleaned_value) > max_length:
            raise ValidationError(f"Поле '{field_name}' не может содержать более {max_length} символов")
        
        return cleaned_value

    @staticmethod
    def validate_optional_string(value: Any, field_name: str, max_length: int = None) -> Optional[str]:
        """Валидация опциональной строки"""
        # ИСПРАВЛЕНО: Добавлена проверка на None
        if value is None:
            return None
        
        if not isinstance(value, str):
            # Если это не строка, но и не None - ошибка
            raise ValidationError(f"Поле '{field_name}' должно быть строкой")
        
        cleaned_value = value.strip()
        
        # Если после очистки пустая строка - возвращаем None
        if not cleaned_value:
            return None
        
        if max_length and len(cleaned_value) > max_length:
            raise ValidationError(f"Поле '{field_name}' не может содержать более {max_length} символов")
        
        return cleaned_value
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email адреса"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.match(pattern, email.strip()) is not None
    
    @staticmethod
    def validate_date_range(start_date: Optional[date], end_date: Optional[date], 
                           allow_future: bool = False) -> None:
        """Валидация диапазона дат"""
        today = date.today()
        
        if start_date and not allow_future and start_date > today:
            raise ValidationError("Начальная дата не может быть в будущем")
        
        if end_date and not allow_future and end_date > today:
            raise ValidationError("Конечная дата не может быть в будущем")
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Начальная дата не может быть позже конечной")
    
    @staticmethod
    def validate_year_range(year_from: Optional[int], year_to: Optional[int]) -> None:
        """Валидация диапазона годов"""
        current_year = datetime.now().year
        
        if year_from and (year_from < 1 or year_from > current_year + 10):
            raise ValidationError(f"Начальный год должен быть от 1 до {current_year + 10}")
        
        if year_to and (year_to < 1 or year_to > current_year + 10):
            raise ValidationError(f"Конечный год должен быть от 1 до {current_year + 10}")
        
        if year_from and year_to and year_from > year_to:
            raise ValidationError("Начальный год не может быть больше конечного")
    
    @staticmethod
    def validate_pagination(offset: int, limit: int, max_limit: int = 100) -> tuple[int, int]:
        """Валидация параметров пагинации"""
        validated_offset = max(0, offset or 0)
        validated_limit = min(max_limit, max(1, limit or 50))
        return validated_offset, validated_limit

class PersonValidator(BaseValidator):
    """Валидатор для персон"""
    
    @classmethod
    def validate_person_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Комплексная валидация данных персоны"""
        validated = {}
        
        # Обязательные поля
        validated['name'] = cls.validate_required_string(data.get('name'), 'Имя', 2, 100)
        
        # Опциональные поля
        validated['surname'] = cls.validate_optional_string(data.get('surname'), 'Фамилия', 100)
        validated['patronymic'] = cls.validate_optional_string(data.get('patronymic'), 'Отчество', 100)
        validated['biography'] = cls.validate_optional_string(data.get('biography'), 'Биография', 10000)
        
        # Даты
        date_of_birth = data.get('date_of_birth')
        date_of_death = data.get('date_of_death')
        
        if date_of_birth and not isinstance(date_of_birth, date):
            raise ValidationError("Дата рождения должна быть объектом date")
        
        if date_of_death and not isinstance(date_of_death, date):
            raise ValidationError("Дата смерти должна быть объектом date")
        
        cls.validate_date_range(date_of_birth, date_of_death, allow_future=False)
        
        validated['date_of_birth'] = date_of_birth
        validated['date_of_death'] = date_of_death
        
        # ID страны
        country_id = data.get('country_id')
        if country_id is not None:
            if not isinstance(country_id, int) or country_id < 1:
                raise ValidationError("ID страны должен быть положительным числом")
        
        validated['country_id'] = country_id
        
        return validated

class EventValidator(BaseValidator):
    """Валидатор для событий"""
    
    @classmethod
    def validate_event_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Комплексная валидация данных события"""
        validated = {}
        
        # Обязательные поля
        validated['name'] = cls.validate_required_string(data.get('name'), 'Название', 3, 200)
        
        # Опциональные поля
        validated['description'] = cls.validate_optional_string(data.get('description'), 'Описание', 5000)
        validated['location'] = cls.validate_optional_string(data.get('location'), 'Местоположение', 200)
        validated['event_type'] = cls.validate_optional_string(data.get('event_type'), 'Тип события', 50)
        
        # Даты
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and not isinstance(start_date, date):
            raise ValidationError("Дата начала должна быть объектом date")
        
        if end_date and not isinstance(end_date, date):
            raise ValidationError("Дата окончания должна быть объектом date")
        
        cls.validate_date_range(start_date, end_date, allow_future=True)
        
        validated['start_date'] = start_date
        validated['end_date'] = end_date
        
        # Родительское событие
        parent_id = data.get('parent_id')
        if parent_id is not None:
            if not isinstance(parent_id, int) or parent_id < 1:
                raise ValidationError("ID родительского события должен быть положительным числом")
        
        validated['parent_id'] = parent_id
        
        return validated

class CountryValidator(BaseValidator):
    """Валидатор для стран"""
    
    @classmethod
    def validate_country_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Комплексная валидация данных страны"""
        validated = {}
        
        # Обязательные поля
        validated['name'] = cls.validate_required_string(data.get('name'), 'Название', 2, 100)
        
        # Опциональные поля
        validated['capital'] = cls.validate_optional_string(data.get('capital'), 'Столица', 100)
        validated['description'] = cls.validate_optional_string(data.get('description'), 'Описание', 5000)
        
        # Даты
        foundation_date = data.get('foundation_date')
        dissolution_date = data.get('dissolution_date')
        
        if foundation_date and not isinstance(foundation_date, date):
            raise ValidationError("Дата основания должна быть объектом date")
        
        if dissolution_date and not isinstance(dissolution_date, date):
            raise ValidationError("Дата роспуска должна быть объектом date")
        
        cls.validate_date_range(foundation_date, dissolution_date, allow_future=False)
        
        validated['foundation_date'] = foundation_date
        validated['dissolution_date'] = dissolution_date
        
        return validated

class DocumentValidator(BaseValidator):
    """Валидатор для документов"""
    
    @classmethod
    def validate_document_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Комплексная валидация данных документа"""
        validated = {}
        
        # Обязательные поля
        validated['name'] = cls.validate_required_string(data.get('name'), 'Название', 3, 200)
        validated['content'] = cls.validate_required_string(data.get('content'), 'Содержимое', 10, 1000000)
        
        # Дата создания
        creating_date = data.get('creating_date')
        if creating_date:
            if not isinstance(creating_date, date):
                raise ValidationError("Дата создания должна быть объектом date")
            
            if creating_date > date.today():
                raise ValidationError("Дата создания не может быть в будущем")
        
        validated['creating_date'] = creating_date
        
        return validated

class SourceValidator(BaseValidator):
    """Валидатор для источников"""
    
    @classmethod
    def validate_source_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Комплексная валидация данных источника"""
        validated = {}
        
        # Обязательные поля
        validated['name'] = cls.validate_required_string(data.get('name'), 'Название', 3, 200)
        
        # Опциональные поля
        validated['author'] = cls.validate_optional_string(data.get('author'), 'Автор', 100)
        validated['type'] = cls.validate_optional_string(data.get('type'), 'Тип', 50)
        
        # URL
        url = data.get('url')
        if url:
            validated_url = cls.validate_optional_string(url, 'URL', 500)
            if validated_url and not cls.validate_url(validated_url):
                raise ValidationError("Некорректный формат URL")
            validated['url'] = validated_url
        else:
            validated['url'] = None
        
        # Дата публикации
        publication_date = data.get('publication_date')
        if publication_date:
            if not isinstance(publication_date, date):
                raise ValidationError("Дата публикации должна быть объектом date")
            
            if publication_date > date.today():
                raise ValidationError("Дата публикации не может быть в будущем")
        
        validated['publication_date'] = publication_date
        
        return validated
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Валидация URL"""
        if not url:
            return False
        
        # Добавляем протокол если отсутствует
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'http://' + url
        
        # Простая проверка формата URL
        url_pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*'
        return re.match(url_pattern, url) is not None

# services/decorators.py
"""
Декораторы для бизнес-сервисов
"""

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
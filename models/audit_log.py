from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class AuditLog:
    log_id: int
    user_id: Optional[int]
    action_type: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    description: Optional[str]
    
    @property
    def action_display(self) -> str:
        """Человекочитаемое описание действия"""
        action_map = {
            'LOGIN_SUCCESS': 'Успешный вход',
            'LOGIN_FAILED': 'Неудачный вход',
            'USER_REGISTERED': 'Регистрация пользователя',
            'PERSON_CREATED': 'Создание персоны',
            'PERSON_UPDATED': 'Обновление персоны',
            'PERSON_DELETED': 'Удаление персоны',
            'COUNTRY_CREATED': 'Создание страны',
            'EVENT_CREATED': 'Создание события',
            'DOCUMENT_CREATED': 'Создание документа',
            'SOURCE_CREATED': 'Создание источника',
        }
        return action_map.get(self.action_type, self.action_type)
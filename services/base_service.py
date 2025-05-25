from abc import ABC
from typing import Dict, Any, Optional, List
import logging
from core.exceptions import ValidationError, AuthorizationError, EntityNotFoundError
from data_access import AuditRepository

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Базовый класс для всех бизнес-сервисов"""
    
    def __init__(self):
        self.audit_repo = AuditRepository()
    
    def _validate_user_permissions(self, user_id: int, required_role: int) -> bool:
        """Проверка прав пользователя"""
        from data_access import UserRepository
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise AuthorizationError("Пользователь не найден")
        
        if user['role_id'] < required_role:
            raise AuthorizationError("Недостаточно прав для выполнения операции")
        
        return True
    
    def _log_action(self, user_id: int, action_type: str, entity_type: str = None,
                   entity_id: int = None, description: str = None,
                   old_values: Dict[str, Any] = None, new_values: Dict[str, Any] = None) -> None:
        """Логирование действий пользователя"""
        try:
            self.audit_repo.log_user_action(
                user_id=user_id,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                old_values=old_values,
                new_values=new_values
            )
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Проверка обязательных полей"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(f"Обязательные поля не заполнены: {', '.join(missing_fields)}")
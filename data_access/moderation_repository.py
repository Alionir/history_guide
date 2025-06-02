from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_repository import BaseRepository

class ModerationRepository(BaseRepository):
    """Репозиторий для работы с системой модерации"""
    
    def create_request(self, user_id: int, entity_type: str, operation_type: str,
                      entity_id: int = None, old_data: Dict[str, Any] = None, 
                      new_data: Dict[str, Any] = None, comment: str = None) -> Dict[str, Any]:
        """Создание заявки на модерацию"""
        import json
        old_json = json.dumps(old_data, default=str) if old_data else None
        new_json = json.dumps(new_data, default=str) if new_data else None
        
        result = self._execute_function('sp_create_moderation_request', (
            user_id, entity_type, operation_type, entity_id, old_json, new_json, comment
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_pending_requests(self, offset: int = 0, limit: int = 50, 
                           entity_type: str = None, status: str = 'PENDING',
                           user_id: int = None) -> List[Dict[str, Any]]:
        """Получение заявок на модерацию"""
        return self._execute_function('sp_get_moderation_requests', (
            offset, limit, entity_type, status, user_id
        ))
    
    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Получение заявки по ID"""
        result = self._execute_function('sp_get_moderation_request_by_id', (request_id,))
        return result[0] if result else None
    
    def approve_request(self, request_id: int, moderator_id: int, comment: str = None) -> Dict[str, Any]:
        """Одобрение заявки на изменение"""
        result = self._execute_function('sp_approve_moderation_request', (request_id, moderator_id, comment))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def reject_request(self, request_id: int, moderator_id: int, comment: str) -> Dict[str, Any]:
        """Отклонение заявки на изменение"""
        result = self._execute_function('sp_reject_moderation_request', (request_id, moderator_id, comment))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_statistics(self, period_days: int = 30) -> Dict[str, Any]:
        """Получение статистики по модерации"""
        result = self._execute_function('sp_get_moderation_statistics', (period_days,))
        return result[0] if result else {}
    
    def get_user_history(self, user_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории модерации для пользователя"""
        return self._execute_function('sp_get_user_moderation_history', (user_id, offset, limit))
    
    def cleanup_old_requests(self, admin_id: int, days_old: int = 90) -> Dict[str, Any]:
        """Очистка старых обработанных заявок"""
        result = self._execute_function('sp_cleanup_old_moderation_requests', (admin_id, days_old))
        return result[0] if result else {'success': False, 'deleted_count': 0, 'message': 'Unknown error'}
    
    # Методы для совместимости со старым кодом
    def create_change_request(self, user_id: int, entity_type: str, operation_type: str,
                             new_data: Dict[str, Any], entity_id: int = None,
                             old_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Создание заявки на изменение (старый метод для совместимости)"""
        return self.create_request(user_id, entity_type, operation_type, entity_id, old_data, new_data)
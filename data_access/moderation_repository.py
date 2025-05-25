from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository

class ModerationRepository(BaseRepository):
    """Репозиторий для работы с системой модерации"""
    
    def create_change_request(self, user_id: int, entity_type: str, operation_type: str,
                             new_data: Dict[str, Any], entity_id: int = None,
                             old_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Создание заявки на изменение"""
        import json
        old_json = json.dumps(old_data) if old_data else None
        new_json = json.dumps(new_data)
        
        result = self._execute_function('sp_create_change_request', (
            user_id, entity_type, operation_type, new_json, entity_id, old_json
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_pending_requests(self, offset: int = 0, limit: int = 50, entity_type: str = None) -> List[Dict[str, Any]]:
        """Получение заявок на модерацию"""
        return self._execute_function('sp_get_pending_change_requests', (offset, limit, entity_type))
    
    def approve_request(self, request_id: int, moderator_id: int, comment: str = None) -> Dict[str, Any]:
        """Одобрение заявки на изменение"""
        result = self._execute_function('sp_approve_change_request', (request_id, moderator_id, comment))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def reject_request(self, request_id: int, moderator_id: int, comment: str) -> Dict[str, Any]:
        """Отклонение заявки на изменение"""
        result = self._execute_function('sp_reject_change_request', (request_id, moderator_id, comment))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
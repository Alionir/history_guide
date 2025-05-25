from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_repository import BaseRepository

class AuditRepository(BaseRepository):
    """Репозиторий для работы с логами и аудитом"""
    
    def log_user_action(self, user_id: int, action_type: str, entity_type: str = None,
                       entity_id: int = None, description: str = None,
                       old_values: Dict[str, Any] = None, new_values: Dict[str, Any] = None,
                       ip_address: str = None, user_agent: str = None) -> None:
        """Логирование действий пользователя"""
        import json
        old_json = json.dumps(old_values) if old_values else None
        new_json = json.dumps(new_values) if new_values else None
        
        self._execute_function('sp_log_user_action', (
            user_id, action_type, entity_type, entity_id, description,
            old_json, new_json, ip_address, user_agent
        ))
    
    def get_audit_logs(self, start_date: datetime = None, end_date: datetime = None,
                      user_id: int = None, action_type: str = None, entity_type: str = None,
                      offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение логов аудита"""
        return self._execute_function('sp_get_audit_logs', (
            start_date, end_date, user_id, action_type, entity_type, offset, limit
        ))
    
    def get_user_activity_stats(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Получение статистики активности пользователей"""
        return self._execute_function('sp_get_user_activity_stats', (start_date, end_date))
    
    def get_person_change_history(self, person_id: int, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение истории изменений персоны"""
        return self._execute_function('sp_get_person_change_history', (person_id, offset, limit))
    
    def get_country_change_history(self, country_id: int, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение истории изменений страны"""
        return self._execute_function('sp_get_country_change_history', (country_id, offset, limit))
    
    def get_document_change_history(self, document_id: int, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение истории изменений документа"""
        return self._execute_function('sp_get_document_change_history', (document_id, offset, limit))
    
    def get_source_change_history(self, source_id: int, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение истории изменений источника"""
        return self._execute_function('sp_get_source_change_history', (source_id, offset, limit))
from typing import List, Dict, Any, Optional
from datetime import date
from .base_repository import BaseRepository

class EventRepository(BaseRepository):
    """Репозиторий для работы с событиями"""
    
    def get_events(self, offset: int = 0, limit: int = 50, search_term: str = None,
                  event_type: str = None, location: str = None,
                  start_year_from: int = None, start_year_to: int = None,
                  end_year_from: int = None, end_year_to: int = None,
                  parent_id: int = None, country_id: int = None, person_id: int = None,
                  only_root_events: bool = False) -> List[Dict[str, Any]]:
        """Получение списка событий с фильтрацией"""
        return self._execute_function('sp_get_events', (
            offset, limit, search_term, event_type, location,
            start_year_from, start_year_to, end_year_from, end_year_to,
            parent_id, country_id, person_id, only_root_events
        ))
    
    def get_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получение события по ID"""
        result = self._execute_function('sp_get_event_by_id', (event_id,))
        return result[0] if result else None
    
    def get_hierarchy(self, parent_id: int = None, max_levels: int = 3) -> List[Dict[str, Any]]:
        """Получение иерархии событий"""
        return self._execute_function('sp_get_events_hierarchy', (parent_id, max_levels))
    
    def request_create(self, user_id: int, name: str, description: str = None,
                      start_date: date = None, end_date: date = None,
                      location: str = None, event_type: str = None,
                      parent_id: int = None) -> Dict[str, Any]:
        """Создание заявки на добавление события"""
        result = self._execute_function('sp_request_create_event', (
            user_id, name, description, start_date, end_date, location, event_type, parent_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def create_direct(self, moderator_id: int, name: str, description: str = None,
                     start_date: date = None, end_date: date = None,
                     location: str = None, event_type: str = None,
                     parent_id: int = None) -> Dict[str, Any]:
        """Прямое создание события (для модераторов)"""
        result = self._execute_function('sp_create_event_direct', (
            moderator_id, name, description, start_date, end_date, location, event_type, parent_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_update(self, user_id: int, event_id: int, name: str, description: str = None,
                      start_date: date = None, end_date: date = None,
                      location: str = None, event_type: str = None,
                      parent_id: int = None) -> Dict[str, Any]:
        """Создание заявки на изменение события"""
        result = self._execute_function('sp_request_update_event', (
            user_id, event_id, name, description, start_date, end_date, location, event_type, parent_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def update_direct(self, moderator_id: int, event_id: int, name: str, description: str = None,
                     start_date: date = None, end_date: date = None,
                     location: str = None, event_type: str = None,
                     parent_id: int = None) -> Dict[str, Any]:
        """Прямое обновление события (для модераторов)"""
        result = self._execute_function('sp_update_event_direct', (
            moderator_id, event_id, name, description, start_date, end_date, location, event_type, parent_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_delete(self, user_id: int, event_id: int, reason: str = None) -> Dict[str, Any]:
        """Создание заявки на удаление события"""
        result = self._execute_function('sp_request_delete_event', (user_id, event_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def delete_direct(self, admin_id: int, event_id: int, reason: str = None) -> Dict[str, Any]:
        """Прямое удаление события (для админов)"""
        result = self._execute_function('sp_delete_event_direct', (admin_id, event_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_child_events(self, parent_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение дочерних событий"""
        return self._execute_function('sp_get_child_events', (parent_id, offset, limit))
    
    def get_event_persons(self, event_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение персон, связанных с событием"""
        return self._execute_function('sp_get_event_persons', (event_id, offset, limit))
    
    def get_event_countries(self, event_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение стран, связанных с событием"""
        return self._execute_function('sp_get_event_countries', (event_id, offset, limit))
    
    def get_event_documents(self, event_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение документов, связанных с событием"""
        return self._execute_function('sp_get_event_documents', (event_id, offset, limit))
    
    def get_event_sources(self, event_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение источников, связанных с событием"""
        return self._execute_function('sp_get_event_sources', (event_id, offset, limit))
    
    def search_fulltext(self, search_text: str, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Полнотекстовый поиск событий"""
        return self._execute_function('sp_search_events_fulltext', (search_text, offset, limit))
    
    def get_timeline(self, year_from: int = None, year_to: int = None,
                    event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение временной линии событий"""
        return self._execute_function('sp_get_events_timeline', (year_from, year_to, event_type, limit))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по событиям"""
        result = self._execute_function('sp_get_events_statistics')
        return result[0] if result else {}
    
    def get_event_types(self) -> List[Dict[str, Any]]:
        """Получение списка типов событий"""
        return self._execute_function('sp_get_event_types')
    
    def get_dropdown_list(self, parent_id: int = None, exclude_event_id: int = None) -> List[Dict[str, Any]]:
        """Получение событий для выпадающих списков"""
        return self._execute_function('sp_get_events_dropdown', (parent_id, exclude_event_id))
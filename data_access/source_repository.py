from typing import List, Dict, Any, Optional
from datetime import date
from .base_repository import BaseRepository

class SourceRepository(BaseRepository):
    """Репозиторий для работы с источниками"""
    
    def get_sources(self, offset: int = 0, limit: int = 50, search_term: str = None,
                   author: str = None, source_type: str = None,
                   publication_year_from: int = None, publication_year_to: int = None,
                   event_id: int = None, has_url: bool = None,
                   sort_by: str = 'date_desc') -> List[Dict[str, Any]]:
        """Получение списка источников с фильтрацией"""
        return self._execute_function('sp_get_sources', (
            offset, limit, search_term, author, source_type,
            publication_year_from, publication_year_to, event_id, has_url, sort_by
        ))
    
    def get_by_id(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Получение источника по ID"""
        result = self._execute_function('sp_get_source_by_id', (source_id,))
        return result[0] if result else None
    
    def request_create(self, user_id: int, name: str, author: str = None,
                      publication_date: date = None, source_type: str = None,
                      url: str = None) -> Dict[str, Any]:
        """Создание заявки на добавление источника"""
        result = self._execute_function('sp_request_create_source', (
            user_id, name, author, publication_date, source_type, url
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def create_direct(self, moderator_id: int, name: str, author: str = None,
                     publication_date: date = None, source_type: str = None,
                     url: str = None) -> Dict[str, Any]:
        """Прямое создание источника (для модераторов)"""
        result = self._execute_function('sp_create_source_direct', (
            moderator_id, name, author, publication_date, source_type, url
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_update(self, user_id: int, source_id: int, name: str, author: str = None,
                      publication_date: date = None, source_type: str = None,
                      url: str = None) -> Dict[str, Any]:
        """Создание заявки на изменение источника"""
        result = self._execute_function('sp_request_update_source', (
            user_id, source_id, name, author, publication_date, source_type, url
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def update_direct(self, moderator_id: int, source_id: int, name: str, author: str = None,
                     publication_date: date = None, source_type: str = None,
                     url: str = None) -> Dict[str, Any]:
        """Прямое обновление источника (для модераторов)"""
        result = self._execute_function('sp_update_source_direct', (
            moderator_id, source_id, name, author, publication_date, source_type, url
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_delete(self, user_id: int, source_id: int, reason: str = None) -> Dict[str, Any]:
        """Создание заявки на удаление источника"""
        result = self._execute_function('sp_request_delete_source', (user_id, source_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def delete_direct(self, admin_id: int, source_id: int, reason: str = None) -> Dict[str, Any]:
        """Прямое удаление источника (для админов)"""
        result = self._execute_function('sp_delete_source_direct', (admin_id, source_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_source_events(self, source_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение событий, связанных с источником"""
        return self._execute_function('sp_get_source_events', (source_id, offset, limit))
    
    def search_fulltext(self, search_text: str, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Полнотекстовый поиск источников"""
        return self._execute_function('sp_search_sources_fulltext', (search_text, offset, limit))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по источникам"""
        result = self._execute_function('sp_get_sources_statistics')
        return result[0] if result else {}
    
    def get_source_types(self) -> List[Dict[str, Any]]:
        """Получение списка типов источников"""
        return self._execute_function('sp_get_source_types')
    
    def get_source_authors(self, min_sources_count: int = 1, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение списка авторов источников"""
        return self._execute_function('sp_get_source_authors', (min_sources_count, offset, limit))
    
    def get_by_author(self, author: str, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение источников по автору"""
        return self._execute_function('sp_get_sources_by_author', (author, offset, limit))
    
    def get_by_type(self, source_type: str, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение источников по типу"""
        return self._execute_function('sp_get_sources_by_type', (source_type, offset, limit))
    
    def get_by_period(self, start_date: date, end_date: date, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение источников по периоду публикации"""
        return self._execute_function('sp_get_sources_by_period', (start_date, end_date, offset, limit))
    
    def check_urls(self) -> List[Dict[str, Any]]:
        """Проверка валидности URL источников"""
        return self._execute_function('sp_check_sources_urls')
    
    def find_duplicates(self) -> List[Dict[str, Any]]:
        """Поиск дублирующихся источников"""
        return self._execute_function('sp_find_duplicate_sources')
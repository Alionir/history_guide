from typing import List, Dict, Any, Optional
from datetime import date
from .base_repository import BaseRepository

class DocumentRepository(BaseRepository):
    """Репозиторий для работы с документами"""
    
    def get_documents(self, offset: int = 0, limit: int = 50, search_term: str = None,
                     creating_year_from: int = None, creating_year_to: int = None,
                     person_id: int = None, event_id: int = None,
                     content_search: str = None, sort_by: str = 'date_desc') -> List[Dict[str, Any]]:
        """Получение списка документов с фильтрацией"""
        return self._execute_function('sp_get_documents', (
            offset, limit, search_term, creating_year_from, creating_year_to,
            person_id, event_id, content_search, sort_by
        ))
    
    def get_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Получение документа по ID"""
        result = self._execute_function('sp_get_document_by_id', (document_id,))
        return result[0] if result else None
    
    def request_create(self, user_id: int, name: str, content: str,
                      creating_date: date = None) -> Dict[str, Any]:
        """Создание заявки на добавление документа"""
        result = self._execute_function('sp_request_create_document', (
            user_id, name, content, creating_date
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def create_direct(self, moderator_id: int, name: str, content: str,
                     creating_date: date = None) -> Dict[str, Any]:
        """Прямое создание документа (для модераторов)"""
        result = self._execute_function('sp_create_document_direct', (
            moderator_id, name, content, creating_date
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_update(self, user_id: int, document_id: int, name: str, content: str,
                      creating_date: date = None) -> Dict[str, Any]:
        """Создание заявки на изменение документа"""
        result = self._execute_function('sp_request_update_document', (
            user_id, document_id, name, content, creating_date
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def update_direct(self, moderator_id: int, document_id: int, name: str, content: str,
                     creating_date: date = None) -> Dict[str, Any]:
        """Прямое обновление документа (для модераторов)"""
        result = self._execute_function('sp_update_document_direct', (
            moderator_id, document_id, name, content, creating_date
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_delete(self, user_id: int, document_id: int, reason: str = None) -> Dict[str, Any]:
        """Создание заявки на удаление документа"""
        result = self._execute_function('sp_request_delete_document', (user_id, document_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def delete_direct(self, admin_id: int, document_id: int, reason: str = None) -> Dict[str, Any]:
        """Прямое удаление документа (для админов)"""
        result = self._execute_function('sp_delete_document_direct', (admin_id, document_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_document_persons(self, document_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение персон, связанных с документом"""
        return self._execute_function('sp_get_document_persons', (document_id, offset, limit))
    
    def get_document_events(self, document_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение событий, связанных с документом"""
        return self._execute_function('sp_get_document_events', (document_id, offset, limit))
    
    def search_fulltext(self, search_text: str, search_in_content: bool = True,
                       offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Полнотекстовый поиск документов"""
        return self._execute_function('sp_search_documents_fulltext', (search_text, search_in_content, offset, limit))
    
    def get_search_snippets(self, document_id: int, search_text: str,
                           snippet_count: int = 3, snippet_length: int = 150) -> List[Dict[str, Any]]:
        """Получение фрагментов текста с выделением найденных слов"""
        return self._execute_function('sp_get_document_search_snippets', (document_id, search_text, snippet_count, snippet_length))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по документам"""
        result = self._execute_function('sp_get_documents_statistics')
        return result[0] if result else {}
    
    def get_by_period(self, start_date: date, end_date: date, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение документов по периоду создания"""
        return self._execute_function('sp_get_documents_by_period', (start_date, end_date, offset, limit))
    
    def get_longest_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение самых длинных документов"""
        return self._execute_function('sp_get_longest_documents', (limit,))
    
    def get_oldest_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение самых старых документов"""
        return self._execute_function('sp_get_oldest_documents', (limit,))
    
    def get_recent_documents(self, days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение недавно добавленных документов"""
        return self._execute_function('sp_get_recent_documents', (days, limit))
    
    def analyze_content(self, document_id: int) -> Dict[str, Any]:
        """Анализ содержимого документа"""
        result = self._execute_function('sp_analyze_document_content', (document_id,))
        return result[0] if result else {}
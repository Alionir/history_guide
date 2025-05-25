from typing import List, Dict, Any, Optional
from datetime import date
from .base_repository import BaseRepository

class CountryRepository(BaseRepository):
    """Репозиторий для работы со странами"""
    
    def get_countries(self, offset: int = 0, limit: int = 50, search_term: str = None,
                     existing_only: bool = False, historical_only: bool = False,
                     foundation_year_from: int = None, foundation_year_to: int = None,
                     dissolution_year_from: int = None, dissolution_year_to: int = None) -> List[Dict[str, Any]]:
        """Получение списка стран с фильтрацией"""
        return self._execute_function('sp_get_countries', (
            offset, limit, search_term, existing_only, historical_only,
            foundation_year_from, foundation_year_to, dissolution_year_from, dissolution_year_to
        ))
    
    def get_by_id(self, country_id: int) -> Optional[Dict[str, Any]]:
        """Получение страны по ID"""
        result = self._execute_function('sp_get_country_by_id', (country_id,))
        return result[0] if result else None
    
    def request_create(self, user_id: int, name: str, capital: str = None,
                      foundation_date: date = None, dissolution_date: date = None,
                      description: str = None) -> Dict[str, Any]:
        """Создание заявки на добавление страны"""
        result = self._execute_function('sp_request_create_country', (
            user_id, name, capital, foundation_date, dissolution_date, description
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def create_direct(self, moderator_id: int, name: str, capital: str = None,
                     foundation_date: date = None, dissolution_date: date = None,
                     description: str = None) -> Dict[str, Any]:
        """Прямое создание страны (для модераторов)"""
        result = self._execute_function('sp_create_country_direct', (
            moderator_id, name, capital, foundation_date, dissolution_date, description
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_update(self, user_id: int, country_id: int, name: str, capital: str = None,
                      foundation_date: date = None, dissolution_date: date = None,
                      description: str = None) -> Dict[str, Any]:
        """Создание заявки на изменение страны"""
        result = self._execute_function('sp_request_update_country', (
            user_id, country_id, name, capital, foundation_date, dissolution_date, description
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def update_direct(self, moderator_id: int, country_id: int, name: str, capital: str = None,
                     foundation_date: date = None, dissolution_date: date = None,
                     description: str = None) -> Dict[str, Any]:
        """Прямое обновление страны (для модераторов)"""
        result = self._execute_function('sp_update_country_direct', (
            moderator_id, country_id, name, capital, foundation_date, dissolution_date, description
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_delete(self, user_id: int, country_id: int, reason: str = None) -> Dict[str, Any]:
        """Создание заявки на удаление страны"""
        result = self._execute_function('sp_request_delete_country', (user_id, country_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def delete_direct(self, admin_id: int, country_id: int, reason: str = None) -> Dict[str, Any]:
        """Прямое удаление страны (для админов)"""
        result = self._execute_function('sp_delete_country_direct', (admin_id, country_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_country_persons(self, country_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение персон из страны"""
        return self._execute_function('sp_get_country_persons', (country_id, offset, limit))
    
    def get_country_events(self, country_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение событий, связанных со страной"""
        return self._execute_function('sp_get_country_events', (country_id, offset, limit))
    
    def get_dropdown_list(self, existing_only: bool = False) -> List[Dict[str, Any]]:
        """Получение списка стран для выпадающих списков"""
        return self._execute_function('sp_get_countries_dropdown', (existing_only,))
    
    def search_fulltext(self, search_text: str, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Полнотекстовый поиск стран"""
        return self._execute_function('sp_search_countries_fulltext', (search_text, offset, limit))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по странам"""
        result = self._execute_function('sp_get_countries_statistics')
        return result[0] if result else {}
    
    def get_timeline(self, year_from: int = None, year_to: int = None) -> List[Dict[str, Any]]:
        """Получение временной линии стран"""
        return self._execute_function('sp_get_countries_timeline', (year_from, year_to))
    
    def get_by_period(self, target_year: int) -> List[Dict[str, Any]]:
        """Получение стран по периоду существования"""
        return self._execute_function('sp_get_countries_by_period', (target_year,))
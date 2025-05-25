from typing import List, Dict, Any, Optional
from datetime import date
from .base_repository import BaseRepository
from models.person import Person

class PersonRepository(BaseRepository):
    """Репозиторий для работы с персонами"""
    
    def get_persons(self, offset: int = 0, limit: int = 50, search_term: str = None,
                   country_id: int = None, birth_year_from: int = None, birth_year_to: int = None,
                   death_year_from: int = None, death_year_to: int = None, 
                   alive_only: bool = False) -> List[Dict[str, Any]]:
        """Получение списка персон с фильтрацией"""
        return self._execute_function('sp_get_persons', (
            offset, limit, search_term, country_id, birth_year_from, birth_year_to,
            death_year_from, death_year_to, alive_only
        ))
    
    def get_by_id(self, person_id: int) -> Optional[Dict[str, Any]]:
        """Получение персоны по ID"""
        result = self._execute_function('sp_get_person_by_id', (person_id,))
        return result[0] if result else None
    
    def request_create(self, user_id: int, name: str, surname: str = None, 
                      patronymic: str = None, date_of_birth: date = None,
                      date_of_death: date = None, biography: str = None,
                      country_id: int = None) -> Dict[str, Any]:
        """Создание заявки на добавление персоны"""
        result = self._execute_function('sp_request_create_person', (
            user_id, name, surname, patronymic, date_of_birth, date_of_death, biography, country_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def create_direct(self, moderator_id: int, name: str, surname: str = None,
                     patronymic: str = None, date_of_birth: date = None,
                     date_of_death: date = None, biography: str = None,
                     country_id: int = None) -> Dict[str, Any]:
        """Прямое создание персоны (для модераторов)"""
        result = self._execute_function('sp_create_person_direct', (
            moderator_id, name, surname, patronymic, date_of_birth, date_of_death, biography, country_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_update(self, user_id: int, person_id: int, name: str, surname: str = None,
                      patronymic: str = None, date_of_birth: date = None,
                      date_of_death: date = None, biography: str = None,
                      country_id: int = None) -> Dict[str, Any]:
        """Создание заявки на изменение персоны"""
        result = self._execute_function('sp_request_update_person', (
            user_id, person_id, name, surname, patronymic, date_of_birth, date_of_death, biography, country_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def update_direct(self, moderator_id: int, person_id: int, name: str, surname: str = None,
                     patronymic: str = None, date_of_birth: date = None,
                     date_of_death: date = None, biography: str = None,
                     country_id: int = None) -> Dict[str, Any]:
        """Прямое обновление персоны (для модераторов)"""
        result = self._execute_function('sp_update_person_direct', (
            moderator_id, person_id, name, surname, patronymic, date_of_birth, date_of_death, biography, country_id
        ))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def request_delete(self, user_id: int, person_id: int, reason: str = None) -> Dict[str, Any]:
        """Создание заявки на удаление персоны"""
        result = self._execute_function('sp_request_delete_person', (user_id, person_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def delete_direct(self, admin_id: int, person_id: int, reason: str = None) -> Dict[str, Any]:
        """Прямое удаление персоны (для админов)"""
        result = self._execute_function('sp_delete_person_direct', (admin_id, person_id, reason))
        return result[0] if result else {'success': False, 'message': 'Unknown error'}
    
    def get_person_events(self, person_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение событий, связанных с персоной"""
        return self._execute_function('sp_get_person_events', (person_id, offset, limit))
    
    def get_person_documents(self, person_id: int, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение документов, связанных с персоной"""
        return self._execute_function('sp_get_person_documents', (person_id, offset, limit))
    
    def search_fulltext(self, search_text: str, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Полнотекстовый поиск персон"""
        return self._execute_function('sp_search_persons_fulltext', (search_text, offset, limit))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по персонам"""
        result = self._execute_function('sp_get_persons_statistics')
        return result[0] if result else {}
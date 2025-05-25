from typing import Dict, Any, List, Optional
from datetime import date
from .base_service import BaseService
from data_access import PersonRepository, CountryRepository, RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError

class PersonService(BaseService):
    """Сервис для работы с персонами"""
    
    def __init__(self):
        super().__init__()
        self.person_repo = PersonRepository()
        self.country_repo = CountryRepository()
        self.rel_repo = RelationshipsRepository()
    
    def get_persons(self, user_id: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Получение списка персон с фильтрацией"""
        filters = filters or {}
        
        # Валидация параметров пагинации
        offset = max(0, filters.get('offset', 0))
        limit = min(100, max(1, filters.get('limit', 50)))
        
        # Валидация фильтров по годам
        birth_year_from = filters.get('birth_year_from')
        birth_year_to = filters.get('birth_year_to')
        
        if birth_year_from and birth_year_to and birth_year_from > birth_year_to:
            raise ValidationError("Начальный год рождения не может быть больше конечного")
        
        death_year_from = filters.get('death_year_from')
        death_year_to = filters.get('death_year_to')
        
        if death_year_from and death_year_to and death_year_from > death_year_to:
            raise ValidationError("Начальный год смерти не может быть больше конечного")
        
        # Получаем данные
        persons = self.person_repo.get_persons(
            offset=offset,
            limit=limit,
            search_term=filters.get('search_term'),
            country_id=filters.get('country_id'),
            birth_year_from=birth_year_from,
            birth_year_to=birth_year_to,
            death_year_from=death_year_from,
            death_year_to=death_year_to,
            alive_only=filters.get('alive_only', False)
        )
        
        self._log_action(user_id, 'PERSONS_LIST_VIEWED', description='Просмотр списка персон')
        
        return {
            'persons': persons,
            'total_count': persons[0]['total_count'] if persons else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_person_details(self, user_id: int, person_id: int) -> Dict[str, Any]:
        """Получение детальной информации о персоне"""
        person = self.person_repo.get_by_id(person_id)
        
        if not person:
            raise EntityNotFoundError("Персона не найдена")
        
        # Получаем связанные данные
        events = self.person_repo.get_person_events(person_id, limit=10)
        documents = self.person_repo.get_person_documents(person_id, limit=10)
        
        # Получаем сводку по связям
        relationships_summary = self.rel_repo.get_entity_relationships_summary('PERSON', person_id)
        
        self._log_action(user_id, 'PERSON_VIEWED', 'PERSON', person_id,
                        f'Просмотр персоны: {person["full_name"]}')
        
        return {
            'person': person,
            'recent_events': events,
            'recent_documents': documents,
            'relationships_summary': relationships_summary
        }
    
    def create_person_request(self, user_id: int, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на добавление персоны"""
        # Валидация данных
        self._validate_person_data(person_data)
        
        # Создаем заявку
        result = self.person_repo.request_create(
            user_id=user_id,
            name=person_data['name'].strip(),
            surname=person_data.get('surname', '').strip() or None,
            patronymic=person_data.get('patronymic', '').strip() or None,
            date_of_birth=person_data.get('date_of_birth'),
            date_of_death=person_data.get('date_of_death'),
            biography=person_data.get('biography', '').strip() or None,
            country_id=person_data.get('country_id')
        )
        
        if result['success']:
            self._log_action(user_id, 'PERSON_CREATE_REQUESTED', 'PERSON', None,
                            f'Создана заявка на добавление персоны: {person_data["name"]}')
        
        return result
    
    def create_person_direct(self, moderator_id: int, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Прямое создание персоны (для модераторов)"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        # Валидация данных
        self._validate_person_data(person_data)
        
        # Создаем персону
        result = self.person_repo.create_direct(
            moderator_id=moderator_id,
            name=person_data['name'].strip(),
            surname=person_data.get('surname', '').strip() or None,
            patronymic=person_data.get('patronymic', '').strip() or None,
            date_of_birth=person_data.get('date_of_birth'),
            date_of_death=person_data.get('date_of_death'),
            biography=person_data.get('biography', '').strip() or None,
            country_id=person_data.get('country_id')
        )
        
        if result['success']:
            self._log_action(moderator_id, 'PERSON_CREATED_DIRECT', 'PERSON', result['person_id'],
                            f'Прямое создание персоны: {person_data["name"]}')
        
        return result
    
    def update_person_request(self, user_id: int, person_id: int, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на изменение персоны"""
        # Проверяем существование персоны
        existing_person = self.person_repo.get_by_id(person_id)
        if not existing_person:
            raise EntityNotFoundError("Персона не найдена")
        
        # Валидация данных
        self._validate_person_data(person_data)
        
        # Создаем заявку на изменение
        result = self.person_repo.request_update(
            user_id=user_id,
            person_id=person_id,
            name=person_data['name'].strip(),
            surname=person_data.get('surname', '').strip() or None,
            patronymic=person_data.get('patronymic', '').strip() or None,
            date_of_birth=person_data.get('date_of_birth'),
            date_of_death=person_data.get('date_of_death'),
            biography=person_data.get('biography', '').strip() or None,
            country_id=person_data.get('country_id')
        )
        
        if result['success']:
            self._log_action(user_id, 'PERSON_UPDATE_REQUESTED', 'PERSON', person_id,
                            f'Создана заявка на изменение персоны: {existing_person["full_name"]}')
        
        return result
    
    def update_person_direct(self, moderator_id: int, person_id: int, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Прямое обновление персоны (для модераторов)"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        # Проверяем существование персоны
        existing_person = self.person_repo.get_by_id(person_id)
        if not existing_person:
            raise EntityNotFoundError("Персона не найдена")
        
        # Валидация данных
        self._validate_person_data(person_data)
        
        # Обновляем персону
        result = self.person_repo.update_direct(
            moderator_id=moderator_id,
            person_id=person_id,
            name=person_data['name'].strip(),
            surname=person_data.get('surname', '').strip() or None,
            patronymic=person_data.get('patronymic', '').strip() or None,
            date_of_birth=person_data.get('date_of_birth'),
            date_of_death=person_data.get('date_of_death'),
            biography=person_data.get('biography', '').strip() or None,
            country_id=person_data.get('country_id')
        )
        
        if result['success']:
            self._log_action(moderator_id, 'PERSON_UPDATED_DIRECT', 'PERSON', person_id,
                            f'Прямое обновление персоны: {existing_person["full_name"]}')
        
        return result
    
    def delete_person_request(self, user_id: int, person_id: int, reason: str = None) -> Dict[str, Any]:
        """Создание заявки на удаление персоны"""
        # Проверяем существование персоны
        existing_person = self.person_repo.get_by_id(person_id)
        if not existing_person:
            raise EntityNotFoundError("Персона не найдена")
        
        # Создаем заявку на удаление
        result = self.person_repo.request_delete(user_id, person_id, reason)
        
        if result['success']:
            self._log_action(user_id, 'PERSON_DELETE_REQUESTED', 'PERSON', person_id,
                            f'Создана заявка на удаление персоны: {existing_person["full_name"]}')
        
        return result
    
    def search_persons(self, user_id: int, search_text: str, offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Полнотекстовый поиск персон"""
        if not search_text or len(search_text.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        # Валидация параметров пагинации
        offset = max(0, offset)
        limit = min(50, max(1, limit))
        
        results = self.person_repo.search_fulltext(search_text.strip(), offset, limit)
        
        self._log_action(user_id, 'PERSONS_SEARCH', description=f'Поиск персон: "{search_text}"')
        
        return {
            'results': results,
            'search_text': search_text.strip(),
            'total_count': results[0]['total_count'] if results else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_person_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики по персонам"""
        stats = self.person_repo.get_statistics()
        
        self._log_action(user_id, 'PERSONS_STATS_VIEWED', description='Просмотр статистики по персонам')
        
        return stats
    
    def _validate_person_data(self, person_data: Dict[str, Any]) -> None:
        """Валидация данных персоны"""
        # Проверка обязательных полей
        self._validate_required_fields(person_data, ['name'])
        
        # Проверка длины имени
        name = person_data['name'].strip()
        if len(name) < 2:
            raise ValidationError("Имя должно содержать минимум 2 символа")
        if len(name) > 100:
            raise ValidationError("Имя не может содержать более 100 символов")
        
        # Проверка фамилии и отчества
        surname = person_data.get('surname', '').strip()
        if surname and len(surname) > 100:
            raise ValidationError("Фамилия не может содержать более 100 символов")
            
        patronymic = person_data.get('patronymic', '').strip()
        if patronymic and len(patronymic) > 100:
            raise ValidationError("Отчество не может содержать более 100 символов")
        
        # Проверка дат
        date_of_birth = person_data.get('date_of_birth')
        date_of_death = person_data.get('date_of_death')
        
        if date_of_birth and date_of_birth > date.today():
            raise ValidationError("Дата рождения не может быть в будущем")
        
        if date_of_death and date_of_death > date.today():
            raise ValidationError("Дата смерти не может быть в будущем")
        
        if date_of_birth and date_of_death and date_of_birth > date_of_death:
            raise ValidationError("Дата рождения не может быть позже даты смерти")
        
        # Проверка биографии
        biography = person_data.get('biography', '').strip()
        if biography and len(biography) > 10000:
            raise ValidationError("Биография не может содержать более 10000 символов")
        
        # Проверка страны
        country_id = person_data.get('country_id')
        if country_id:
            country = self.country_repo.get_by_id(country_id)
            if not country:
                raise ValidationError("Указанная страна не найдена")

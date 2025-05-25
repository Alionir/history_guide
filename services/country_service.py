from typing import Dict, Any, List, Optional
from datetime import date
from .base_service import BaseService
from data_access import CountryRepository, RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError

class CountryService(BaseService):
    """Сервис для работы со странами"""
    
    def __init__(self):
        super().__init__()
        self.country_repo = CountryRepository()
        self.rel_repo = RelationshipsRepository()
    
    def get_countries(self, user_id: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Получение списка стран с фильтрацией"""
        filters = filters or {}
        
        # Валидация параметров пагинации
        offset = max(0, filters.get('offset', 0))
        limit = min(100, max(1, filters.get('limit', 50)))
        
        # Валидация фильтров по годам
        foundation_year_from = filters.get('foundation_year_from')
        foundation_year_to = filters.get('foundation_year_to')
        
        if foundation_year_from and foundation_year_to and foundation_year_from > foundation_year_to:
            raise ValidationError("Начальный год основания не может быть больше конечного")
        
        dissolution_year_from = filters.get('dissolution_year_from')
        dissolution_year_to = filters.get('dissolution_year_to')
        
        if dissolution_year_from and dissolution_year_to and dissolution_year_from > dissolution_year_to:
            raise ValidationError("Начальный год роспуска не может быть больше конечного")
        
        # Получаем данные
        countries = self.country_repo.get_countries(
            offset=offset,
            limit=limit,
            search_term=filters.get('search_term'),
            existing_only=filters.get('existing_only', False),
            historical_only=filters.get('historical_only', False),
            foundation_year_from=foundation_year_from,
            foundation_year_to=foundation_year_to,
            dissolution_year_from=dissolution_year_from,
            dissolution_year_to=dissolution_year_to
        )
        
        self._log_action(user_id, 'COUNTRIES_LIST_VIEWED', description='Просмотр списка стран')
        
        return {
            'countries': countries,
            'total_count': countries[0]['total_count'] if countries else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_country_details(self, user_id: int, country_id: int) -> Dict[str, Any]:
        """Получение детальной информации о стране"""
        country = self.country_repo.get_by_id(country_id)
        
        if not country:
            raise EntityNotFoundError("Страна не найдена")
        
        # Получаем связанные данные
        persons = self.country_repo.get_country_persons(country_id, limit=10)
        events = self.country_repo.get_country_events(country_id, limit=10)
        
        # Получаем сводку по связям
        relationships_summary = self.rel_repo.get_entity_relationships_summary('COUNTRY', country_id)
        
        self._log_action(user_id, 'COUNTRY_VIEWED', 'COUNTRY', country_id,
                        f'Просмотр страны: {country["name"]}')
        
        return {
            'country': country,
            'recent_persons': persons,
            'recent_events': events,
            'relationships_summary': relationships_summary
        }
    
    def create_country_request(self, user_id: int, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на добавление страны"""
        # Валидация данных
        self._validate_country_data(country_data)
        
        # Создаем заявку
        result = self.country_repo.request_create(
            user_id=user_id,
            name=country_data['name'].strip(),
            capital=country_data.get('capital', '').strip() or None,
            foundation_date=country_data.get('foundation_date'),
            dissolution_date=country_data.get('dissolution_date'),
            description=country_data.get('description', '').strip() or None
        )
        
        if result['success']:
            self._log_action(user_id, 'COUNTRY_CREATE_REQUESTED', 'COUNTRY', None,
                            f'Создана заявка на добавление страны: {country_data["name"]}')
        
        return result
    
    def create_country_direct(self, moderator_id: int, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Прямое создание страны (для модераторов)"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        # Валидация данных
        self._validate_country_data(country_data)
        
        # Создаем страну
        result = self.country_repo.create_direct(
            moderator_id=moderator_id,
            name=country_data['name'].strip(),
            capital=country_data.get('capital', '').strip() or None,
            foundation_date=country_data.get('foundation_date'),
            dissolution_date=country_data.get('dissolution_date'),
            description=country_data.get('description', '').strip() or None
        )
        
        if result['success']:
            self._log_action(moderator_id, 'COUNTRY_CREATED_DIRECT', 'COUNTRY', result['country_id'],
                            f'Прямое создание страны: {country_data["name"]}')
        
        return result
    
    def search_countries(self, user_id: int, search_text: str, offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Полнотекстовый поиск стран"""
        if not search_text or len(search_text.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        # Валидация параметров пагинации
        offset = max(0, offset)
        limit = min(50, max(1, limit))
        
        results = self.country_repo.search_fulltext(search_text.strip(), offset, limit)
        
        self._log_action(user_id, 'COUNTRIES_SEARCH', description=f'Поиск стран: "{search_text}"')
        
        return {
            'results': results,
            'search_text': search_text.strip(),
            'total_count': results[0]['total_count'] if results else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_countries_timeline(self, user_id: int, year_from: int = None, year_to: int = None) -> List[Dict[str, Any]]:
        """Получение временной линии стран"""
        if year_from and year_to and year_from > year_to:
            raise ValidationError("Начальный год не может быть больше конечного")
        
        timeline = self.country_repo.get_timeline(year_from, year_to)
        
        self._log_action(user_id, 'COUNTRIES_TIMELINE_VIEWED', 
                        description=f'Просмотр временной линии стран: {year_from or "?"}-{year_to or "?"}')
        
        return timeline
    
    def _validate_country_data(self, country_data: Dict[str, Any]) -> None:
        """Валидация данных страны"""
        # Проверка обязательных полей
        self._validate_required_fields(country_data, ['name'])
        
        # Проверка длины названия
        name = country_data['name'].strip()
        if len(name) < 2:
            raise ValidationError("Название страны должно содержать минимум 2 символа")
        if len(name) > 100:
            raise ValidationError("Название страны не может содержать более 100 символов")
        
        # Проверка столицы
        capital = country_data.get('capital', '').strip()
        if capital and len(capital) > 100:
            raise ValidationError("Название столицы не может содержать более 100 символов")
        
        # Проверка дат
        foundation_date = country_data.get('foundation_date')
        dissolution_date = country_data.get('dissolution_date')
        
        if foundation_date and foundation_date > date.today():
            raise ValidationError("Дата основания не может быть в будущем")
        
        if dissolution_date and dissolution_date > date.today():
            raise ValidationError("Дата роспуска не может быть в будущем")
        
        if foundation_date and dissolution_date and foundation_date > dissolution_date:
            raise ValidationError("Дата основания не может быть позже даты роспуска")
        
        # Проверка описания
        description = country_data.get('description', '').strip()
        if description and len(description) > 5000:
            raise ValidationError("Описание не может содержать более 5000 символов")
from typing import Dict, Any, List, Optional
from datetime import date
from .base_service import BaseService
from data_access import EventRepository, RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError

class EventService(BaseService):
    """Сервис для работы с событиями"""
    
    def __init__(self):
        super().__init__()
        self.event_repo = EventRepository()
        self.rel_repo = RelationshipsRepository()
    
    def get_events(self, user_id: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Получение списка событий с фильтрацией"""
        filters = filters or {}
        
        # Валидация параметров пагинации
        offset = max(0, filters.get('offset', 0))
        limit = min(100, max(1, filters.get('limit', 50)))
        
        # Валидация фильтров по годам
        start_year_from = filters.get('start_year_from')
        start_year_to = filters.get('start_year_to')
        
        if start_year_from and start_year_to and start_year_from > start_year_to:
            raise ValidationError("Начальный год не может быть больше конечного")
        
        # Получаем данные
        events = self.event_repo.get_events(
            offset=offset,
            limit=limit,
            search_term=filters.get('search_term'),
            event_type=filters.get('event_type'),
            location=filters.get('location'),
            start_year_from=start_year_from,
            start_year_to=start_year_to,
            end_year_from=filters.get('end_year_from'),
            end_year_to=filters.get('end_year_to'),
            parent_id=filters.get('parent_id'),
            country_id=filters.get('country_id'),
            person_id=filters.get('person_id'),
            only_root_events=filters.get('only_root_events', False)
        )
        
        self._log_action(user_id, 'EVENTS_LIST_VIEWED', description='Просмотр списка событий')
        
        return {
            'events': events,
            'total_count': events[0]['total_count'] if events else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_event_details(self, user_id: int, event_id: int) -> Dict[str, Any]:
        """Получение детальной информации о событии"""
        event = self.event_repo.get_by_id(event_id)
        
        if not event:
            raise EntityNotFoundError("Событие не найдено")
        
        # Получаем связанные данные
        persons = self.event_repo.get_event_persons(event_id, limit=10)
        countries = self.event_repo.get_event_countries(event_id, limit=10)
        documents = self.event_repo.get_event_documents(event_id, limit=10)
        sources = self.event_repo.get_event_sources(event_id, limit=10)
        child_events = self.event_repo.get_child_events(event_id, limit=10)
        
        # Получаем сводку по связям
        relationships_summary = self.rel_repo.get_entity_relationships_summary('EVENT', event_id)
        
        self._log_action(user_id, 'EVENT_VIEWED', 'EVENT', event_id,
                        f'Просмотр события: {event["name"]}')
        
        return {
            'event': event,
            'related_persons': persons,
            'related_countries': countries,
            'related_documents': documents,
            'related_sources': sources,
            'child_events': child_events,
            'relationships_summary': relationships_summary
        }
    
    def get_events_hierarchy(self, user_id: int, parent_id: int = None, max_levels: int = 3) -> List[Dict[str, Any]]:
        """Получение иерархии событий"""
        if max_levels > 5:
            max_levels = 5  # Ограничиваем глубину для производительности
        
        hierarchy = self.event_repo.get_hierarchy(parent_id, max_levels)
        
        self._log_action(user_id, 'EVENTS_HIERARCHY_VIEWED', description='Просмотр иерархии событий')
        
        return hierarchy
    
    def create_event_request(self, user_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на добавление события"""
        # Валидация данных
        self._validate_event_data(event_data)
        
        # Создаем заявку
        result = self.event_repo.request_create(
            user_id=user_id,
            name=event_data['name'].strip(),
            description=event_data.get('description', '').strip() or None,
            start_date=event_data.get('start_date'),
            end_date=event_data.get('end_date'),
            location=event_data.get('location', '').strip() or None,
            event_type=event_data.get('event_type', '').strip() or None,
            parent_id=event_data.get('parent_id')
        )
        
        if result['success']:
            self._log_action(user_id, 'EVENT_CREATE_REQUESTED', 'EVENT', None,
                            f'Создана заявка на добавление события: {event_data["name"]}')
        
        return result
    
    def create_event_direct(self, moderator_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Прямое создание события (для модераторов)"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        # Валидация данных
        self._validate_event_data(event_data)
        
        # Создаем событие
        result = self.event_repo.create_direct(
            moderator_id=moderator_id,
            name=event_data['name'].strip(),
            description=event_data.get('description', '').strip() or None,
            start_date=event_data.get('start_date'),
            end_date=event_data.get('end_date'),
            location=event_data.get('location', '').strip() or None,
            event_type=event_data.get('event_type', '').strip() or None,
            parent_id=event_data.get('parent_id')
        )
        
        if result['success']:
            self._log_action(moderator_id, 'EVENT_CREATED_DIRECT', 'EVENT', result['event_id'],
                            f'Прямое создание события: {event_data["name"]}')
        
        return result
    
    def get_events_timeline(self, user_id: int, year_from: int = None, year_to: int = None,
                           event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение временной линии событий"""
        if year_from and year_to and year_from > year_to:
            raise ValidationError("Начальный год не может быть больше конечного")
        
        limit = min(500, max(10, limit))  # Ограничиваем количество
        
        timeline = self.event_repo.get_timeline(year_from, year_to, event_type, limit)
        
        self._log_action(user_id, 'EVENTS_TIMELINE_VIEWED', 
                        description=f'Просмотр временной линии событий: {year_from or "?"}-{year_to or "?"}')
        
        return timeline
    
    def _validate_event_data(self, event_data: Dict[str, Any]) -> None:
        """Валидация данных события"""
        # Проверка обязательных полей
        self._validate_required_fields(event_data, ['name'])
        
        # Проверка длины названия
        name = event_data['name'].strip()
        if len(name) < 3:
            raise ValidationError("Название события должно содержать минимум 3 символа")
        if len(name) > 200:
            raise ValidationError("Название события не может содержать более 200 символов")
        
        # Проверка описания
        description = event_data.get('description', '').strip()
        if description and len(description) > 5000:
            raise ValidationError("Описание события не может содержать более 5000 символов")
        
        # Проверка дат
        start_date = event_data.get('start_date')
        end_date = event_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Дата начала не может быть позже даты окончания")
        
        # Проверка местоположения
        location = event_data.get('location', '').strip()
        if location and len(location) > 200:
            raise ValidationError("Местоположение не может содержать более 200 символов")
        
        # Проверка типа события
        event_type = event_data.get('event_type', '').strip()
        if event_type and len(event_type) > 50:
            raise ValidationError("Тип события не может содержать более 50 символов")
        
        # Проверка родительского события
        parent_id = event_data.get('parent_id')
        if parent_id:
            parent_event = self.event_repo.get_by_id(parent_id)
            if not parent_event:
                raise ValidationError("Родительское событие не найдено")
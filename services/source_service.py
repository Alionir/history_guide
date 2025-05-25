import re
from typing import Dict, Any, List, Optional
from datetime import date
from .base_service import BaseService
from data_access import SourceRepository, RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError

class SourceService(BaseService):
    """Сервис для работы с источниками"""
    
    def __init__(self):
        super().__init__()
        self.source_repo = SourceRepository()
        self.rel_repo = RelationshipsRepository()
    
    def get_sources(self, user_id: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Получение списка источников с фильтрацией"""
        filters = filters or {}
        
        # Валидация параметров пагинации
        offset = max(0, filters.get('offset', 0))
        limit = min(100, max(1, filters.get('limit', 50)))
        
        # Валидация фильтров по годам
        publication_year_from = filters.get('publication_year_from')
        publication_year_to = filters.get('publication_year_to')
        
        if publication_year_from and publication_year_to and publication_year_from > publication_year_to:
            raise ValidationError("Начальный год публикации не может быть больше конечного")
        
        # Получаем данные
        sources = self.source_repo.get_sources(
            offset=offset,
            limit=limit,
            search_term=filters.get('search_term'),
            author=filters.get('author'),
            source_type=filters.get('source_type'),
            publication_year_from=publication_year_from,
            publication_year_to=publication_year_to,
            event_id=filters.get('event_id'),
            has_url=filters.get('has_url'),
            sort_by=filters.get('sort_by', 'date_desc')
        )
        
        self._log_action(user_id, 'SOURCES_LIST_VIEWED', description='Просмотр списка источников')
        
        return {
            'sources': sources,
            'total_count': sources[0]['total_count'] if sources else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_source_details(self, user_id: int, source_id: int) -> Dict[str, Any]:
        """Получение детальной информации об источнике"""
        source = self.source_repo.get_by_id(source_id)
        
        if not source:
            raise EntityNotFoundError("Источник не найден")
        
        # Получаем связанные события
        events = self.source_repo.get_source_events(source_id, limit=10)
        
        # Получаем сводку по связям
        relationships_summary = self.rel_repo.get_entity_relationships_summary('SOURCE', source_id)
        
        self._log_action(user_id, 'SOURCE_VIEWED', 'SOURCE', source_id,
                        f'Просмотр источника: {source["name"]}')
        
        return {
            'source': source,
            'related_events': events,
            'relationships_summary': relationships_summary
        }
    
    def create_source_request(self, user_id: int, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на добавление источника"""
        # Валидация данных
        self._validate_source_data(source_data)
        
        # Создаем заявку
        result = self.source_repo.request_create(
            user_id=user_id,
            name=source_data['name'].strip(),
            author=source_data.get('author', '').strip() or None,
            publication_date=source_data.get('publication_date'),
            source_type=source_data.get('source_type', '').strip() or None,
            url=source_data.get('url', '').strip() or None
        )
        
        if result['success']:
            self._log_action(user_id, 'SOURCE_CREATE_REQUESTED', 'SOURCE', None,
                            f'Создана заявка на добавление источника: {source_data["name"]}')
        
        return result
    
    def search_sources(self, user_id: int, search_text: str, offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Полнотекстовый поиск источников"""
        if not search_text or len(search_text.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        # Валидация параметров пагинации
        offset = max(0, offset)
        limit = min(50, max(1, limit))
        
        results = self.source_repo.search_fulltext(search_text.strip(), offset, limit)
        
        self._log_action(user_id, 'SOURCES_SEARCH', description=f'Поиск источников: "{search_text}"')
        
        return {
            'results': results,
            'search_text': search_text.strip(),
            'total_count': results[0]['total_count'] if results else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_source_types(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение списка типов источников"""
        types = self.source_repo.get_source_types()
        
        self._log_action(user_id, 'SOURCE_TYPES_VIEWED', description='Просмотр типов источников')
        
        return types
    
    def get_source_authors(self, user_id: int, min_sources_count: int = 1, 
                          offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Получение списка авторов источников"""
        authors = self.source_repo.get_source_authors(min_sources_count, offset, limit)
        
        self._log_action(user_id, 'SOURCE_AUTHORS_VIEWED', description='Просмотр авторов источников')
        
        return {
            'authors': authors,
            'total_count': authors[0]['total_count'] if authors else 0,
            'offset': offset,
            'limit': limit
        }
    
    def check_sources_urls(self, admin_id: int) -> List[Dict[str, Any]]:
        """Проверка валидности URL источников (для админов)"""
        self._validate_user_permissions(admin_id, 3)
        
        url_issues = self.source_repo.check_urls()
        
        self._log_action(admin_id, 'SOURCES_URL_CHECK', description='Проверка URL источников')
        
        return url_issues
    
    def find_duplicate_sources(self, admin_id: int) -> List[Dict[str, Any]]:
        """Поиск дублирующихся источников (для админов)"""
        self._validate_user_permissions(admin_id, 3)
        
        duplicates = self.source_repo.find_duplicates()
        
        self._log_action(admin_id, 'SOURCES_DUPLICATES_CHECK', description='Поиск дублирующихся источников')
        
        return duplicates
    
    def _validate_source_data(self, source_data: Dict[str, Any]) -> None:
        """Валидация данных источника"""
        # Проверка обязательных полей
        self._validate_required_fields(source_data, ['name'])
        
        # Проверка длины названия
        name = source_data['name'].strip()
        if len(name) < 3:
            raise ValidationError("Название источника должно содержать минимум 3 символа")
        if len(name) > 200:
            raise ValidationError("Название источника не может содержать более 200 символов")
        
        # Проверка автора
        author = source_data.get('author', '').strip()
        if author and len(author) > 100:
            raise ValidationError("Имя автора не может содержать более 100 символов")
        
        # Проверка типа источника
        source_type = source_data.get('source_type', '').strip()
        if source_type and len(source_type) > 50:
            raise ValidationError("Тип источника не может содержать более 50 символов")
        
        # Проверка URL
        url = source_data.get('url', '').strip()
        if url:
            if len(url) > 500:
                raise ValidationError("URL не может содержать более 500 символов")
            
            # Добавляем протокол если отсутствует
            if not url.startswith(('http://', 'https://', 'ftp://')):
                url = 'http://' + url
                source_data['url'] = url
            
            # Простая проверка формата URL
            url_pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*'
            if not re.match(url_pattern, url):
                raise ValidationError("Некорректный формат URL")
        
        # Проверка даты публикации
        publication_date = source_data.get('publication_date')
        if publication_date and publication_date > date.today():
            raise ValidationError("Дата публикации не может быть в будущем")

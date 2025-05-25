from typing import Dict, Any, List, Optional
from datetime import date
from .base_service import BaseService
from data_access import DocumentRepository, RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError

class DocumentService(BaseService):
    """Сервис для работы с документами"""
    
    def __init__(self):
        super().__init__()
        self.document_repo = DocumentRepository()
        self.rel_repo = RelationshipsRepository()
    
    def get_documents(self, user_id: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Получение списка документов с фильтрацией"""
        filters = filters or {}
        
        # Валидация параметров пагинации
        offset = max(0, filters.get('offset', 0))
        limit = min(100, max(1, filters.get('limit', 50)))
        
        # Валидация фильтров по годам
        creating_year_from = filters.get('creating_year_from')
        creating_year_to = filters.get('creating_year_to')
        
        if creating_year_from and creating_year_to and creating_year_from > creating_year_to:
            raise ValidationError("Начальный год создания не может быть больше конечного")
        
        # Получаем данные
        documents = self.document_repo.get_documents(
            offset=offset,
            limit=limit,
            search_term=filters.get('search_term'),
            creating_year_from=creating_year_from,
            creating_year_to=creating_year_to,
            person_id=filters.get('person_id'),
            event_id=filters.get('event_id'),
            content_search=filters.get('content_search'),
            sort_by=filters.get('sort_by', 'date_desc')
        )
        
        self._log_action(user_id, 'DOCUMENTS_LIST_VIEWED', description='Просмотр списка документов')
        
        return {
            'documents': documents,
            'total_count': documents[0]['total_count'] if documents else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_document_details(self, user_id: int, document_id: int) -> Dict[str, Any]:
        """Получение детальной информации о документе"""
        document = self.document_repo.get_by_id(document_id)
        
        if not document:
            raise EntityNotFoundError("Документ не найден")
        
        # Получаем связанные данные
        persons = self.document_repo.get_document_persons(document_id, limit=10)
        events = self.document_repo.get_document_events(document_id, limit=10)
        
        # Получаем сводку по связям
        relationships_summary = self.rel_repo.get_entity_relationships_summary('DOCUMENT', document_id)
        
        self._log_action(user_id, 'DOCUMENT_VIEWED', 'DOCUMENT', document_id,
                        f'Просмотр документа: {document["name"]}')
        
        return {
            'document': document,
            'related_persons': persons,
            'related_events': events,
            'relationships_summary': relationships_summary
        }
    
    def create_document_request(self, user_id: int, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на добавление документа"""
        # Валидация данных
        self._validate_document_data(document_data)
        
        # Создаем заявку
        result = self.document_repo.request_create(
            user_id=user_id,
            name=document_data['name'].strip(),
            content=document_data['content'].strip(),
            creating_date=document_data.get('creating_date')
        )
        
        if result['success']:
            self._log_action(user_id, 'DOCUMENT_CREATE_REQUESTED', 'DOCUMENT', None,
                            f'Создана заявка на добавление документа: {document_data["name"]}')
        
        return result
    
    def search_documents(self, user_id: int, search_text: str, search_in_content: bool = True,
                        offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Полнотекстовый поиск документов"""
        if not search_text or len(search_text.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        # Валидация параметров пагинации
        offset = max(0, offset)
        limit = min(50, max(1, limit))
        
        results = self.document_repo.search_fulltext(search_text.strip(), search_in_content, offset, limit)
        
        self._log_action(user_id, 'DOCUMENTS_SEARCH', description=f'Поиск документов: "{search_text}"')
        
        return {
            'results': results,
            'search_text': search_text.strip(),
            'total_count': results[0]['total_count'] if results else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_document_snippets(self, user_id: int, document_id: int, search_text: str,
                             snippet_count: int = 3, snippet_length: int = 150) -> List[Dict[str, Any]]:
        """Получение фрагментов документа с выделением найденных слов"""
        if not search_text or len(search_text.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        snippets = self.document_repo.get_search_snippets(
            document_id, search_text.strip(), snippet_count, snippet_length
        )
        
        self._log_action(user_id, 'DOCUMENT_SNIPPETS_VIEWED', 'DOCUMENT', document_id,
                        f'Просмотр фрагментов документа для поиска: "{search_text}"')
        
        return snippets
    
    def _validate_document_data(self, document_data: Dict[str, Any]) -> None:
        """Валидация данных документа"""
        # Проверка обязательных полей
        self._validate_required_fields(document_data, ['name', 'content'])
        
        # Проверка длины названия
        name = document_data['name'].strip()
        if len(name) < 3:
            raise ValidationError("Название документа должно содержать минимум 3 символа")
        if len(name) > 200:
            raise ValidationError("Название документа не может содержать более 200 символов")
        
        # Проверка содержимого
        content = document_data['content'].strip()
        if len(content) < 10:
            raise ValidationError("Содержимое документа должно содержать минимум 10 символов")
        if len(content) > 1000000:  # 1MB текста
            raise ValidationError("Содержимое документа не может содержать более 1 млн символов")
        
        # Проверка даты создания
        creating_date = document_data.get('creating_date')
        if creating_date and creating_date > date.today():
            raise ValidationError("Дата создания не может быть в будущем")
# services/moderation_service.py
from typing import Dict, Any, List
from .base_service import BaseService
from data_access import ModerationRepository, PersonRepository, CountryRepository, EventRepository, DocumentRepository, SourceRepository
from core.exceptions import ValidationError, EntityNotFoundError, AuthorizationError
import logging
logger = logging.getLogger(__name__)
class ModerationService(BaseService):
    """Сервис для системы модерации"""
    
    def __init__(self):
        super().__init__()
        self.mod_repo = ModerationRepository()
        self.person_repo = PersonRepository()
        self.country_repo = CountryRepository()
        self.event_repo = EventRepository()
        self.document_repo = DocumentRepository()
        self.source_repo = SourceRepository()
    
    def get_pending_requests(self, moderator_id: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Получение заявок на модерацию"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        filters = filters or {}
        offset = max(0, filters.get('offset', 0))
        limit = min(100, max(1, filters.get('limit', 50)))
        
        requests = self.mod_repo.get_pending_requests(
            offset=offset,
            limit=limit,
            entity_type=filters.get('entity_type')
        )
        
        self._log_action(moderator_id, 'MODERATION_REQUESTS_VIEWED',
                        description='Просмотр заявок на модерацию')
        
        return {
            'requests': requests,
            'total_count': requests[0]['total_count'] if requests else 0,
            'offset': offset,
            'limit': limit
        }
    
    def approve_request(self, moderator_id: int, request_id: int, comment: str = None) -> Dict[str, Any]:
        """Одобрение заявки на изменение"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        # Получаем информацию о заявке
        pending_requests = self.mod_repo.get_pending_requests(limit=1000)  # Получаем все для поиска
        request_info = next((r for r in pending_requests if r['request_id'] == request_id), None)
        
        if not request_info:
            raise EntityNotFoundError("Заявка не найдена или уже обработана")
        
        # Одобряем заявку
        result = self.mod_repo.approve_request(request_id, moderator_id, comment)
        
        if result['success']:
            # Применяем изменения в зависимости от типа сущности и операции
            self._apply_approved_changes(request_info, moderator_id)
            
            self._log_action(moderator_id, 'MODERATION_REQUEST_APPROVED', 
                            request_info['entity_type'], request_info.get('entity_id'),
                            f'Одобрена заявка #{request_id} на {request_info["operation_type"]} {request_info["entity_type"]}')
        
        return result
    
    def reject_request(self, moderator_id: int, request_id: int, comment: str) -> Dict[str, Any]:
        """Отклонение заявки на изменение"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        if not comment or len(comment.strip()) < 5:
            raise ValidationError("Комментарий к отклонению должен содержать минимум 5 символов")
        
        # Получаем информацию о заявке
        pending_requests = self.mod_repo.get_pending_requests(limit=1000)
        request_info = next((r for r in pending_requests if r['request_id'] == request_id), None)
        
        if not request_info:
            raise EntityNotFoundError("Заявка не найдена или уже обработана")
        
        # Отклоняем заявку
        result = self.mod_repo.reject_request(request_id, moderator_id, comment.strip())
        
        if result['success']:
            self._log_action(moderator_id, 'MODERATION_REQUEST_REJECTED',
                            request_info['entity_type'], request_info.get('entity_id'),
                            f'Отклонена заявка #{request_id} на {request_info["operation_type"]} {request_info["entity_type"]}: {comment}')
        
        return result
    
    def _apply_approved_changes(self, request_info: Dict[str, Any], moderator_id: int) -> None:
        """Применение одобренных изменений"""
        entity_type = request_info['entity_type']
        operation_type = request_info['operation_type']
        entity_id = request_info.get('entity_id')
        new_data = request_info['new_data']
        
        try:
            if entity_type == 'PERSON':
                self._apply_person_changes(operation_type, entity_id, new_data, moderator_id)
            elif entity_type == 'COUNTRY':
                self._apply_country_changes(operation_type, entity_id, new_data, moderator_id)
            elif entity_type == 'EVENT':
                self._apply_event_changes(operation_type, entity_id, new_data, moderator_id)
            elif entity_type == 'DOCUMENT':
                self._apply_document_changes(operation_type, entity_id, new_data, moderator_id)
            elif entity_type == 'SOURCE':
                self._apply_source_changes(operation_type, entity_id, new_data, moderator_id)
        except Exception as e:
            logger.error(f"Failed to apply approved changes: {e}")
            # В реальном приложении здесь нужно откатить одобрение заявки
    
    def _apply_person_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для персоны"""
        if operation_type == 'CREATE':
            self.person_repo.create_direct(
                moderator_id=moderator_id,
                name=new_data['name'],
                surname=new_data.get('surname'),
                patronymic=new_data.get('patronymic'),
                date_of_birth=new_data.get('date_of_birth'),
                date_of_death=new_data.get('date_of_death'),
                biography=new_data.get('biography'),
                country_id=new_data.get('country_id')
            )
        elif operation_type == 'UPDATE':
            self.person_repo.update_direct(
                moderator_id=moderator_id,
                person_id=entity_id,
                name=new_data['name'],
                surname=new_data.get('surname'),
                patronymic=new_data.get('patronymic'),
                date_of_birth=new_data.get('date_of_birth'),
                date_of_death=new_data.get('date_of_death'),
                biography=new_data.get('biography'),
                country_id=new_data.get('country_id')
            )
        elif operation_type == 'DELETE':
            # Удаление требует прав администратора
            if moderator_id and self._validate_user_permissions(moderator_id, 3):
                self.person_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_country_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для страны"""
        if operation_type == 'CREATE':
            self.country_repo.create_direct(
                moderator_id=moderator_id,
                name=new_data['name'],
                capital=new_data.get('capital'),
                foundation_date=new_data.get('foundation_date'),
                dissolution_date=new_data.get('dissolution_date'),
                description=new_data.get('description')
            )
        elif operation_type == 'UPDATE':
            self.country_repo.update_direct(
                moderator_id=moderator_id,
                country_id=entity_id,
                name=new_data['name'],
                capital=new_data.get('capital'),
                foundation_date=new_data.get('foundation_date'),
                dissolution_date=new_data.get('dissolution_date'),
                description=new_data.get('description')
            )
        elif operation_type == 'DELETE':
            if moderator_id and self._validate_user_permissions(moderator_id, 3):
                self.country_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_event_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для события"""
        if operation_type == 'CREATE':
            self.event_repo.create_direct(
                moderator_id=moderator_id,
                name=new_data['name'],
                description=new_data.get('description'),
                start_date=new_data.get('start_date'),
                end_date=new_data.get('end_date'),
                location=new_data.get('location'),
                event_type=new_data.get('event_type'),
                parent_id=new_data.get('parent_id')
            )
        elif operation_type == 'UPDATE':
            self.event_repo.update_direct(
                moderator_id=moderator_id,
                event_id=entity_id,
                name=new_data['name'],
                description=new_data.get('description'),
                start_date=new_data.get('start_date'),
                end_date=new_data.get('end_date'),
                location=new_data.get('location'),
                event_type=new_data.get('event_type'),
                parent_id=new_data.get('parent_id')
            )
        elif operation_type == 'DELETE':
            if moderator_id and self._validate_user_permissions(moderator_id, 3):
                self.event_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_document_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для документа"""
        if operation_type == 'CREATE':
            self.document_repo.create_direct(
                moderator_id=moderator_id,
                name=new_data['name'],
                content=new_data['content'],
                creating_date=new_data.get('creating_date')
            )
        elif operation_type == 'UPDATE':
            self.document_repo.update_direct(
                moderator_id=moderator_id,
                document_id=entity_id,
                name=new_data['name'],
                content=new_data['content'],
                creating_date=new_data.get('creating_date')
            )
        elif operation_type == 'DELETE':
            if moderator_id and self._validate_user_permissions(moderator_id, 3):
                self.document_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_source_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для источника"""
        if operation_type == 'CREATE':
            self.source_repo.create_direct(
                moderator_id=moderator_id,
                name=new_data['name'],
                author=new_data.get('author'),
                publication_date=new_data.get('publication_date'),
                source_type=new_data.get('type'),
                url=new_data.get('url')
            )
        elif operation_type == 'UPDATE':
            self.source_repo.update_direct(
                moderator_id=moderator_id,
                source_id=entity_id,
                name=new_data['name'],
                author=new_data.get('author'),
                publication_date=new_data.get('publication_date'),
                source_type=new_data.get('type'),
                url=new_data.get('url')
            )
        elif operation_type == 'DELETE':
            if moderator_id and self._validate_user_permissions(moderator_id, 3):
                self.source_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
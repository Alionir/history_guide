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
    
    def create_moderation_request(self, user_id: int, entity_type: str, operation_type: str,
                                new_data: Dict[str, Any], entity_id: int = None,
                                old_data: Dict[str, Any] = None, comment: str = None) -> Dict[str, Any]:
        """Создание заявки на модерацию"""
        # Валидация входных данных
        if entity_type not in ['PERSON', 'COUNTRY', 'EVENT', 'DOCUMENT', 'SOURCE']:
            raise ValidationError("Некорректный тип сущности")
        
        if operation_type not in ['CREATE', 'UPDATE', 'DELETE']:
            raise ValidationError("Некорректный тип операции")
        
        if operation_type in ['UPDATE', 'DELETE'] and not entity_id:
            raise ValidationError("Для операций UPDATE/DELETE требуется ID сущности")
        
        # Создаем заявку
        result = self.mod_repo.create_request(
            user_id=user_id,
            entity_type=entity_type,
            operation_type=operation_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            comment=comment
        )
        
        if result['success']:
            self._log_action(user_id, 'MODERATION_REQUEST_CREATED', entity_type, entity_id,
                           f'Создана заявка на {operation_type} {entity_type}')
        
        return result
    
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
            entity_type=filters.get('entity_type'),
            status=filters.get('status', 'PENDING'),
            user_id=filters.get('user_id')
        )
        
        self._log_action(moderator_id, 'MODERATION_REQUESTS_VIEWED',
                        description='Просмотр заявок на модерацию')
        
        return {
            'requests': requests,
            'total_count': requests[0]['total_count'] if requests else 0,
            'offset': offset,
            'limit': limit
        }
    
    def get_request_details(self, moderator_id: int, request_id: int) -> Dict[str, Any]:
        """Получение детальной информации о заявке"""
        self._validate_user_permissions(moderator_id, 2)
        
        request_info = self.mod_repo.get_request_by_id(request_id)
        
        if not request_info:
            raise EntityNotFoundError("Заявка не найдена")
        
        # Добавляем информацию о текущей сущности для операций UPDATE/DELETE
        current_entity = None
        if request_info['operation_type'] in ['UPDATE', 'DELETE'] and request_info['entity_id']:
            current_entity = self._get_current_entity_data(
                request_info['entity_type'], 
                request_info['entity_id']
            )
        
        self._log_action(moderator_id, 'MODERATION_REQUEST_VIEWED', 
                        request_info['entity_type'], request_info.get('entity_id'),
                        f'Просмотр заявки #{request_id}')
        
        return {
            'request': request_info,
            'current_entity': current_entity
        }
    
    def approve_request(self, moderator_id: int, request_id: int, comment: str = None) -> Dict[str, Any]:
        """Одобрение заявки на изменение"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        # Одобряем заявку через хранимую процедуру
        result = self.mod_repo.approve_request(request_id, moderator_id, comment)
        
        if result['success']:
            # Применяем изменения в зависимости от типа сущности и операции
            try:
                self._apply_approved_changes(result, moderator_id)
                self._log_action(moderator_id, 'MODERATION_REQUEST_APPROVED', 
                               result['entity_type'], result.get('entity_id'),
                               f'Одобрена заявка #{request_id}')
            except Exception as e:
                logger.error(f"Failed to apply approved changes for request {request_id}: {e}")
                # В реальном приложении здесь нужно откатить одобрение
                result['message'] += f". Ошибка при применении изменений: {str(e)}"
        
        return result
    
    def reject_request(self, moderator_id: int, request_id: int, comment: str) -> Dict[str, Any]:
        """Отклонение заявки на изменение"""
        # Проверяем права модератора
        self._validate_user_permissions(moderator_id, 2)
        
        if not comment or len(comment.strip()) < 5:
            raise ValidationError("Комментарий к отклонению должен содержать минимум 5 символов")
        
        result = self.mod_repo.reject_request(request_id, moderator_id, comment.strip())
        
        if result['success']:
            self._log_action(moderator_id, 'MODERATION_REQUEST_REJECTED', 
                           description=f'Отклонена заявка #{request_id}: {comment}')
        
        return result
    
    def get_moderation_statistics(self, admin_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Получение статистики по модерации"""
        self._validate_user_permissions(admin_id, 2)
        
        if period_days < 1 or period_days > 365:
            raise ValidationError("Период должен быть от 1 до 365 дней")
        
        stats = self.mod_repo.get_statistics(period_days)
        
        self._log_action(admin_id, 'MODERATION_STATISTICS_VIEWED',
                        description=f'Просмотр статистики модерации за {period_days} дней')
        
        return stats
    
    def get_user_moderation_history(self, user_id: int, requesting_user_id: int, 
                                   offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Получение истории модерации для пользователя"""
        # Пользователь может смотреть только свою историю, модераторы - любую
        if user_id != requesting_user_id:
            self._validate_user_permissions(requesting_user_id, 2)
        
        offset = max(0, offset)
        limit = min(100, max(1, limit))
        
        history = self.mod_repo.get_user_history(user_id, offset, limit)
        
        self._log_action(requesting_user_id, 'USER_MODERATION_HISTORY_VIEWED',
                        description=f'Просмотр истории модерации пользователя {user_id}')
        
        return {
            'history': history,
            'total_count': history[0]['total_count'] if history else 0,
            'offset': offset,
            'limit': limit
        }
    
    def cleanup_old_requests(self, admin_id: int, days_old: int = 90) -> Dict[str, Any]:
        """Очистка старых обработанных заявок"""
        self._validate_user_permissions(admin_id, 3)
        
        if days_old < 30:
            raise ValidationError("Нельзя удалять заявки младше 30 дней")
        
        result = self.mod_repo.cleanup_old_requests(admin_id, days_old)
        
        if result['success']:
            self._log_action(admin_id, 'MODERATION_CLEANUP_PERFORMED',
                           description=f'Очищено {result["deleted_count"]} старых заявок')
        
        return result
    
    def _apply_approved_changes(self, approval_result: Dict[str, Any], moderator_id: int) -> None:
        """Применение одобренных изменений"""
        entity_type = approval_result['entity_type']
        operation_type = approval_result['operation_type']
        entity_id = approval_result.get('entity_id')
        new_data = approval_result['new_data']
        
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
    
    def _apply_person_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для персоны"""
        from datetime import datetime
        
        # Преобразуем строковые даты в объекты date если необходимо
        for date_field in ['date_of_birth', 'date_of_death']:
            if date_field in new_data and isinstance(new_data[date_field], str):
                try:
                    new_data[date_field] = datetime.strptime(new_data[date_field], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    new_data[date_field] = None
        
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
            self._validate_user_permissions(moderator_id, 3)
            self.person_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_country_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для страны"""
        from datetime import datetime
        
        # Преобразуем строковые даты в объекты date если необходимо
        for date_field in ['foundation_date', 'dissolution_date']:
            if date_field in new_data and isinstance(new_data[date_field], str):
                try:
                    new_data[date_field] = datetime.strptime(new_data[date_field], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    new_data[date_field] = None
        
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
            self._validate_user_permissions(moderator_id, 3)
            self.country_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_event_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для события"""
        from datetime import datetime
        
        # Преобразуем строковые даты в объекты date если необходимо
        for date_field in ['start_date', 'end_date']:
            if date_field in new_data and isinstance(new_data[date_field], str):
                try:
                    new_data[date_field] = datetime.strptime(new_data[date_field], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    new_data[date_field] = None
        
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
            self._validate_user_permissions(moderator_id, 3)
            self.event_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_document_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для документа"""
        from datetime import datetime
        
        # Преобразуем строковую дату в объект date если необходимо
        if 'creating_date' in new_data and isinstance(new_data['creating_date'], str):
            try:
                new_data['creating_date'] = datetime.strptime(new_data['creating_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                new_data['creating_date'] = None
        
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
            self._validate_user_permissions(moderator_id, 3)
            self.document_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _apply_source_changes(self, operation_type: str, entity_id: int, new_data: Dict[str, Any], moderator_id: int):
        """Применение изменений для источника"""
        from datetime import datetime
        
        # Преобразуем строковую дату в объект date если необходимо
        if 'publication_date' in new_data and isinstance(new_data['publication_date'], str):
            try:
                new_data['publication_date'] = datetime.strptime(new_data['publication_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                new_data['publication_date'] = None
        
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
            self._validate_user_permissions(moderator_id, 3)
            self.source_repo.delete_direct(moderator_id, entity_id, new_data.get('reason'))
    
    def _get_current_entity_data(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """Получение текущих данных сущности"""
        try:
            if entity_type == 'PERSON':
                return self.person_repo.get_by_id(entity_id)
            elif entity_type == 'COUNTRY':
                return self.country_repo.get_by_id(entity_id)
            elif entity_type == 'EVENT':
                return self.event_repo.get_by_id(entity_id)
            elif entity_type == 'DOCUMENT':
                return self.document_repo.get_by_id(entity_id)
            elif entity_type == 'SOURCE':
                return self.source_repo.get_by_id(entity_id)
        except Exception as e:
            logger.error(f"Error getting current entity data for {entity_type} {entity_id}: {e}")
        
        return None
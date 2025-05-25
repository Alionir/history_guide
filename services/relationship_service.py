from typing import Dict, Any, List, Tuple
from .base_service import BaseService
from data_access import RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError

class RelationshipService(BaseService):
    """Сервис для управления связями между сущностями"""
    
    def __init__(self):
        super().__init__()
        self.rel_repo = RelationshipsRepository()
    
    def link_person_to_event(self, user_id: int, person_id: int, event_id: int) -> Dict[str, Any]:
        """Связывание персоны с событием"""
        if not person_id or not event_id:
            raise ValidationError("ID персоны и события обязательны")
        
        success = self.rel_repo.link_person_to_event(person_id, event_id, user_id)
        
        if success:
            self._log_action(user_id, 'PERSON_EVENT_LINKED', 'PERSON', person_id,
                            f'Персона связана с событием {event_id}')
            return {'success': True, 'message': 'Персона успешно связана с событием'}
        else:
            return {'success': False, 'message': 'Связь уже существует или произошла ошибка'}
    
    def unlink_person_from_event(self, user_id: int, person_id: int, event_id: int) -> Dict[str, Any]:
        """Отвязывание персоны от события"""
        if not person_id or not event_id:
            raise ValidationError("ID персоны и события обязательны")
        
        success = self.rel_repo.unlink_person_from_event(person_id, event_id, user_id)
        
        if success:
            self._log_action(user_id, 'PERSON_EVENT_UNLINKED', 'PERSON', person_id,
                            f'Персона отвязана от события {event_id}')
            return {'success': True, 'message': 'Связь успешно удалена'}
        else:
            return {'success': False, 'message': 'Связь не найдена'}
    
    def link_country_to_event(self, user_id: int, country_id: int, event_id: int) -> Dict[str, Any]:
        """Связывание страны с событием"""
        if not country_id or not event_id:
            raise ValidationError("ID страны и события обязательны")
        
        success = self.rel_repo.link_country_to_event(country_id, event_id, user_id)
        
        if success:
            self._log_action(user_id, 'COUNTRY_EVENT_LINKED', 'COUNTRY', country_id,
                            f'Страна связана с событием {event_id}')
            return {'success': True, 'message': 'Страна успешно связана с событием'}
        else:
            return {'success': False, 'message': 'Связь уже существует или произошла ошибка'}
    
    def unlink_country_from_event(self, user_id: int, country_id: int, event_id: int) -> Dict[str, Any]:
        """Отвязывание страны от события"""
        if not country_id or not event_id:
            raise ValidationError("ID страны и события обязательны")
        
        success = self.rel_repo.unlink_country_from_event(country_id, event_id, user_id)
        
        if success:
            self._log_action(user_id, 'COUNTRY_EVENT_UNLINKED', 'COUNTRY', country_id,
                            f'Страна отвязана от события {event_id}')
            return {'success': True, 'message': 'Связь успешно удалена'}
        else:
            return {'success': False, 'message': 'Связь не найдена'}
    
    def link_document_to_person(self, user_id: int, document_id: int, person_id: int) -> Dict[str, Any]:
        """Связывание документа с персоной"""
        if not document_id or not person_id:
            raise ValidationError("ID документа и персоны обязательны")
        
        success = self.rel_repo.link_document_to_person(document_id, person_id, user_id)
        
        if success:
            self._log_action(user_id, 'DOCUMENT_PERSON_LINKED', 'DOCUMENT', document_id,
                            f'Документ связан с персоной {person_id}')
            return {'success': True, 'message': 'Документ успешно связан с персоной'}
        else:
            return {'success': False, 'message': 'Связь уже существует или произошла ошибка'}
    
    def link_document_to_event(self, user_id: int, document_id: int, event_id: int) -> Dict[str, Any]:
        """Связывание документа с событием"""
        if not document_id or not event_id:
            raise ValidationError("ID документа и события обязательны")
        
        success = self.rel_repo.link_document_to_event(document_id, event_id, user_id)
        
        if success:
            self._log_action(user_id, 'DOCUMENT_EVENT_LINKED', 'DOCUMENT', document_id,
                            f'Документ связан с событием {event_id}')
            return {'success': True, 'message': 'Документ успешно связан с событием'}
        else:
            return {'success': False, 'message': 'Связь уже существует или произошла ошибка'}
    
    def link_event_to_source(self, user_id: int, event_id: int, source_id: int) -> Dict[str, Any]:
        """Связывание события с источником"""
        if not event_id or not source_id:
            raise ValidationError("ID события и источника обязательны")
        
        success = self.rel_repo.link_event_to_source(event_id, source_id, user_id)
        
        if success:
            self._log_action(user_id, 'EVENT_SOURCE_LINKED', 'EVENT', event_id,
                            f'Событие связано с источником {source_id}')
            return {'success': True, 'message': 'Событие успешно связано с источником'}
        else:
            return {'success': False, 'message': 'Связь уже существует или произошла ошибка'}
    
    def batch_link_persons_to_event(self, user_id: int, person_ids: List[int], event_id: int) -> Dict[str, Any]:
        """Массовое связывание персон с событием"""
        if not person_ids or not event_id:
            raise ValidationError("Список ID персон и ID события обязательны")
        
        result = self.rel_repo.batch_link_persons_to_event(person_ids, event_id, user_id)
        
        self._log_action(user_id, 'BATCH_PERSONS_EVENT_LINKED', 'EVENT', event_id,
                        f'Массовое связывание персон с событием: успешно {result["success_count"]}, ошибок {result["failed_count"]}')
        
        return result
    
    def get_entity_relationships(self, user_id: int, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """Получение всех связей сущности"""
        if entity_type not in ['PERSON', 'EVENT', 'COUNTRY', 'DOCUMENT', 'SOURCE']:
            raise ValidationError("Некорректный тип сущности")
        
        summary = self.rel_repo.get_entity_relationships_summary(entity_type, entity_id)
        
        self._log_action(user_id, 'ENTITY_RELATIONSHIPS_VIEWED', entity_type, entity_id,
                        f'Просмотр связей {entity_type}')
        
        return summary
    
    def get_most_connected_entities(self, user_id: int, entity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение самых связанных сущностей"""
        if entity_type not in ['PERSON', 'EVENT', 'COUNTRY', 'DOCUMENT', 'SOURCE']:
            raise ValidationError("Некорректный тип сущности")
        
        limit = min(50, max(1, limit))
        
        entities = self.rel_repo.get_most_connected_entities(entity_type, limit)
        
        self._log_action(user_id, 'MOST_CONNECTED_VIEWED', description=f'Просмотр самых связанных {entity_type}')
        
        return entities
    
    def cleanup_orphaned_relationships(self, admin_id: int) -> Dict[str, int]:
        """Очистка висячих связей (для админов)"""
        self._validate_user_permissions(admin_id, 3)
        
        cleanup_stats = self.rel_repo.cleanup_orphaned_relationships(admin_id)
        
        total_cleaned = sum(cleanup_stats.values())
        self._log_action(admin_id, 'ORPHANED_RELATIONSHIPS_CLEANED', 
                        description=f'Очищено висячих связей: {total_cleaned}')
        
        return cleanup_stats


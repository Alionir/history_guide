from typing import Dict, Any, List, Tuple
from .base_service import BaseService
from data_access import RelationshipsRepository
from core.exceptions import ValidationError, EntityNotFoundError
from datetime import datetime
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
    def unlink_document_from_person(self, user_id: int, document_id: int, person_id: int) -> Dict[str, Any]:
        """Отвязывание документа от персоны"""
        if not document_id or not person_id:
            raise ValidationError("ID документа и персоны обязательны")
        
        success = self.rel_repo.unlink_document_from_person(document_id, person_id, user_id)
        
        if success:
            self._log_action(user_id, 'DOCUMENT_PERSON_UNLINKED', 'DOCUMENT', document_id,
                            f'Документ отвязан от персоны {person_id}')
            return {'success': True, 'message': 'Связь успешно удалена'}
        else:
            return {'success': False, 'message': 'Связь не найдена'}
    
    def unlink_document_from_event(self, user_id: int, document_id: int, event_id: int) -> Dict[str, Any]:
        """Отвязывание документа от события"""
        if not document_id or not event_id:
            raise ValidationError("ID документа и события обязательны")
        
        success = self.rel_repo.unlink_document_from_event(document_id, event_id, user_id)
        
        if success:
            self._log_action(user_id, 'DOCUMENT_EVENT_UNLINKED', 'DOCUMENT', document_id,
                            f'Документ отвязан от события {event_id}')
            return {'success': True, 'message': 'Связь успешно удалена'}
        else:
            return {'success': False, 'message': 'Связь не найдена'}
    
    def unlink_event_from_source(self, user_id: int, event_id: int, source_id: int) -> Dict[str, Any]:
        """Отвязывание события от источника"""
        if not event_id or not source_id:
            raise ValidationError("ID события и источника обязательны")
        
        success = self.rel_repo.unlink_event_from_source(event_id, source_id, user_id)
        
        if success:
            self._log_action(user_id, 'EVENT_SOURCE_UNLINKED', 'EVENT', event_id,
                            f'Событие отвязано от источника {source_id}')
            return {'success': True, 'message': 'Связь успешно удалена'}
        else:
            return {'success': False, 'message': 'Связь не найдена'}
    
    def validate_relationships(self, user_id: int) -> Dict[str, Any]:
        """Проверка целостности связей"""
        try:
            issues = []
            
            # Проверяем висячие связи в events_persons
            with self.rel_repo.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT ep.person_id, ep.event_id 
                    FROM public.events_persons ep
                    LEFT JOIN public.persons p ON ep.person_id = p.person_id
                    LEFT JOIN public.events e ON ep.event_id = e.event_id
                    WHERE p.person_id IS NULL OR e.event_id IS NULL
                """)
                orphaned_events_persons = cursor.fetchall()
                
                for person_id, event_id in orphaned_events_persons:
                    issues.append(f"Висячая связь: персона {person_id} - событие {event_id}")
                
                # Аналогично для других типов связей
                cursor.execute("""
                    SELECT ce.country_id, ce.event_id 
                    FROM public.countries_events ce
                    LEFT JOIN public.countries c ON ce.country_id = c.country_id
                    LEFT JOIN public.events e ON ce.event_id = e.event_id
                    WHERE c.country_id IS NULL OR e.event_id IS NULL
                """)
                orphaned_countries_events = cursor.fetchall()
                
                for country_id, event_id in orphaned_countries_events:
                    issues.append(f"Висячая связь: страна {country_id} - событие {event_id}")
                
                # Проверяем documents_persons
                cursor.execute("""
                    SELECT dp.document_id, dp.person_id 
                    FROM public.documents_persons dp
                    LEFT JOIN public.documents d ON dp.document_id = d.document_id
                    LEFT JOIN public.persons p ON dp.person_id = p.person_id
                    WHERE d.document_id IS NULL OR p.person_id IS NULL
                """)
                orphaned_documents_persons = cursor.fetchall()
                
                for document_id, person_id in orphaned_documents_persons:
                    issues.append(f"Висячая связь: документ {document_id} - персона {person_id}")
                
                # Проверяем documents_events
                cursor.execute("""
                    SELECT de.document_id, de.event_id 
                    FROM public.documents_events de
                    LEFT JOIN public.documents d ON de.document_id = d.document_id
                    LEFT JOIN public.events e ON de.event_id = e.event_id
                    WHERE d.document_id IS NULL OR e.event_id IS NULL
                """)
                orphaned_documents_events = cursor.fetchall()
                
                for document_id, event_id in orphaned_documents_events:
                    issues.append(f"Висячая связь: документ {document_id} - событие {event_id}")
                
                # Проверяем events_sources
                cursor.execute("""
                    SELECT es.event_id, es.source_id 
                    FROM public.events_sources es
                    LEFT JOIN public.events e ON es.event_id = e.event_id
                    LEFT JOIN public.sources s ON es.source_id = s.source_id
                    WHERE e.event_id IS NULL OR s.source_id IS NULL
                """)
                orphaned_events_sources = cursor.fetchall()
                
                for event_id, source_id in orphaned_events_sources:
                    issues.append(f"Висячая связь: событие {event_id} - источник {source_id}")
            
            self._log_action(user_id, 'RELATIONSHIPS_VALIDATED', 
                            description=f'Проверка связей: найдено проблем {len(issues)}')
            
            return {
                'success': True,
                'issues': issues,
                'total_issues': len(issues)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка проверки: {str(e)}',
                'issues': []
            }
    
    def export_relationships(self, user_id: int, filename: str) -> Dict[str, Any]:
        """Экспорт связей в файл"""
        try:
            export_data = {
                'export_date': str(datetime.now()),
                'exported_by': user_id,
                'relationships': {}
            }
            
            with self.rel_repo.db.get_cursor() as cursor:
                # Экспортируем все типы связей
                cursor.execute("SELECT person_id, event_id FROM public.events_persons")
                export_data['relationships']['events_persons'] = [
                    {'person_id': row[0], 'event_id': row[1]} for row in cursor.fetchall()
                ]
                
                cursor.execute("SELECT country_id, event_id FROM public.countries_events")
                export_data['relationships']['countries_events'] = [
                    {'country_id': row[0], 'event_id': row[1]} for row in cursor.fetchall()
                ]
                
                cursor.execute("SELECT document_id, person_id FROM public.documents_persons")
                export_data['relationships']['documents_persons'] = [
                    {'document_id': row[0], 'person_id': row[1]} for row in cursor.fetchall()
                ]
                
                cursor.execute("SELECT document_id, event_id FROM public.documents_events")
                export_data['relationships']['documents_events'] = [
                    {'document_id': row[0], 'event_id': row[1]} for row in cursor.fetchall()
                ]
                
                cursor.execute("SELECT event_id, source_id FROM public.events_sources")
                export_data['relationships']['events_sources'] = [
                    {'event_id': row[0], 'source_id': row[1]} for row in cursor.fetchall()
                ]
            
            # Записываем в файл
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            total_exported = sum(len(rels) for rels in export_data['relationships'].values())
            
            self._log_action(user_id, 'RELATIONSHIPS_EXPORTED', 
                            description=f'Экспорт {total_exported} связей в файл {filename}')
            
            return {
                'success': True,
                'exported_count': total_exported,
                'filename': filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка экспорта: {str(e)}',
                'exported_count': 0
            }
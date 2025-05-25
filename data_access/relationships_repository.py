from typing import List, Dict, Any, Tuple
from .base_repository import BaseRepository

class RelationshipsRepository(BaseRepository):
    """Репозиторий для управления связями many-to-many между сущностями"""
    
    # ========================================
    # УПРАВЛЕНИЕ СВЯЗЯМИ ПЕРСОН И СОБЫТИЙ
    # ========================================
    
    def link_person_to_event(self, person_id: int, event_id: int, user_id: int) -> bool:
        """Связывание персоны с событием"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем, что связь не существует
                    cursor.execute(
                        "SELECT 1 FROM public.events_persons WHERE person_id = %s AND event_id = %s",
                        (person_id, event_id)
                    )
                    if cursor.fetchone():
                        return False  # Связь уже существует
                    
                    # Создаем связь
                    cursor.execute(
                        "INSERT INTO public.events_persons (person_id, event_id) VALUES (%s, %s)",
                        (person_id, event_id)
                    )
                    
                    # Логируем действие
                    cursor.execute(
                        "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                        (user_id, 'PERSON_EVENT_LINKED', 'PERSON', person_id,
                         f'Персона связана с событием {event_id}')
                    )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error linking person {person_id} to event {event_id}: {e}")
            return False
    
    def unlink_person_from_event(self, person_id: int, event_id: int, user_id: int) -> bool:
        """Отвязывание персоны от события"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Удаляем связь
                    cursor.execute(
                        "DELETE FROM public.events_persons WHERE person_id = %s AND event_id = %s",
                        (person_id, event_id)
                    )
                    
                    if cursor.rowcount > 0:
                        # Логируем действие
                        cursor.execute(
                            "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                            (user_id, 'PERSON_EVENT_UNLINKED', 'PERSON', person_id,
                             f'Персона отвязана от события {event_id}')
                        )
                        conn.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error unlinking person {person_id} from event {event_id}: {e}")
            return False
    
    def get_person_events_links(self, person_id: int) -> List[int]:
        """Получение ID событий, связанных с персоной"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT event_id FROM public.events_persons WHERE person_id = %s",
                    (person_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting person {person_id} events links: {e}")
            return []
    
    def get_event_persons_links(self, event_id: int) -> List[int]:
        """Получение ID персон, связанных с событием"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT person_id FROM public.events_persons WHERE event_id = %s",
                    (event_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting event {event_id} persons links: {e}")
            return []
    
    # ========================================
    # УПРАВЛЕНИЕ СВЯЗЯМИ СТРАН И СОБЫТИЙ
    # ========================================
    
    def link_country_to_event(self, country_id: int, event_id: int, user_id: int) -> bool:
        """Связывание страны с событием"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем, что связь не существует
                    cursor.execute(
                        "SELECT 1 FROM public.countries_events WHERE country_id = %s AND event_id = %s",
                        (country_id, event_id)
                    )
                    if cursor.fetchone():
                        return False  # Связь уже существует
                    
                    # Создаем связь
                    cursor.execute(
                        "INSERT INTO public.countries_events (country_id, event_id) VALUES (%s, %s)",
                        (country_id, event_id)
                    )
                    
                    # Логируем действие
                    cursor.execute(
                        "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                        (user_id, 'COUNTRY_EVENT_LINKED', 'COUNTRY', country_id,
                         f'Страна связана с событием {event_id}')
                    )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error linking country {country_id} to event {event_id}: {e}")
            return False
    
    def unlink_country_from_event(self, country_id: int, event_id: int, user_id: int) -> bool:
        """Отвязывание страны от события"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Удаляем связь
                    cursor.execute(
                        "DELETE FROM public.countries_events WHERE country_id = %s AND event_id = %s",
                        (country_id, event_id)
                    )
                    
                    if cursor.rowcount > 0:
                        # Логируем действие
                        cursor.execute(
                            "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                            (user_id, 'COUNTRY_EVENT_UNLINKED', 'COUNTRY', country_id,
                             f'Страна отвязана от события {event_id}')
                        )
                        conn.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error unlinking country {country_id} from event {event_id}: {e}")
            return False
    
    def get_country_events_links(self, country_id: int) -> List[int]:
        """Получение ID событий, связанных со страной"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT event_id FROM public.countries_events WHERE country_id = %s",
                    (country_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting country {country_id} events links: {e}")
            return []
    
    def get_event_countries_links(self, event_id: int) -> List[int]:
        """Получение ID стран, связанных с событием"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT country_id FROM public.countries_events WHERE event_id = %s",
                    (event_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting event {event_id} countries links: {e}")
            return []
    
    # ========================================
    # УПРАВЛЕНИЕ СВЯЗЯМИ ДОКУМЕНТОВ И ПЕРСОН
    # ========================================
    
    def link_document_to_person(self, document_id: int, person_id: int, user_id: int) -> bool:
        """Связывание документа с персоной"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем, что связь не существует
                    cursor.execute(
                        "SELECT 1 FROM public.documents_persons WHERE document_id = %s AND person_id = %s",
                        (document_id, person_id)
                    )
                    if cursor.fetchone():
                        return False  # Связь уже существует
                    
                    # Создаем связь
                    cursor.execute(
                        "INSERT INTO public.documents_persons (document_id, person_id) VALUES (%s, %s)",
                        (document_id, person_id)
                    )
                    
                    # Логируем действие
                    cursor.execute(
                        "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                        (user_id, 'DOCUMENT_PERSON_LINKED', 'DOCUMENT', document_id,
                         f'Документ связан с персоной {person_id}')
                    )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error linking document {document_id} to person {person_id}: {e}")
            return False
    
    def unlink_document_from_person(self, document_id: int, person_id: int, user_id: int) -> bool:
        """Отвязывание документа от персоны"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Удаляем связь
                    cursor.execute(
                        "DELETE FROM public.documents_persons WHERE document_id = %s AND person_id = %s",
                        (document_id, person_id)
                    )
                    
                    if cursor.rowcount > 0:
                        # Логируем действие
                        cursor.execute(
                            "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                            (user_id, 'DOCUMENT_PERSON_UNLINKED', 'DOCUMENT', document_id,
                             f'Документ отвязан от персоны {person_id}')
                        )
                        conn.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error unlinking document {document_id} from person {person_id}: {e}")
            return False
    
    def get_document_persons_links(self, document_id: int) -> List[int]:
        """Получение ID персон, связанных с документом"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT person_id FROM public.documents_persons WHERE document_id = %s",
                    (document_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting document {document_id} persons links: {e}")
            return []
    
    def get_person_documents_links(self, person_id: int) -> List[int]:
        """Получение ID документов, связанных с персоной"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT document_id FROM public.documents_persons WHERE person_id = %s",
                    (person_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting person {person_id} documents links: {e}")
            return []
    
    # ========================================
    # УПРАВЛЕНИЕ СВЯЗЯМИ ДОКУМЕНТОВ И СОБЫТИЙ
    # ========================================
    
    def link_document_to_event(self, document_id: int, event_id: int, user_id: int) -> bool:
        """Связывание документа с событием"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем, что связь не существует
                    cursor.execute(
                        "SELECT 1 FROM public.documents_events WHERE document_id = %s AND event_id = %s",
                        (document_id, event_id)
                    )
                    if cursor.fetchone():
                        return False  # Связь уже существует
                    
                    # Создаем связь
                    cursor.execute(
                        "INSERT INTO public.documents_events (document_id, event_id) VALUES (%s, %s)",
                        (document_id, event_id)
                    )
                    
                    # Логируем действие
                    cursor.execute(
                        "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                        (user_id, 'DOCUMENT_EVENT_LINKED', 'DOCUMENT', document_id,
                         f'Документ связан с событием {event_id}')
                    )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error linking document {document_id} to event {event_id}: {e}")
            return False
    
    def unlink_document_from_event(self, document_id: int, event_id: int, user_id: int) -> bool:
        """Отвязывание документа от события"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Удаляем связь
                    cursor.execute(
                        "DELETE FROM public.documents_events WHERE document_id = %s AND event_id = %s",
                        (document_id, event_id)
                    )
                    
                    if cursor.rowcount > 0:
                        # Логируем действие
                        cursor.execute(
                            "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                            (user_id, 'DOCUMENT_EVENT_UNLINKED', 'DOCUMENT', document_id,
                             f'Документ отвязан от события {event_id}')
                        )
                        conn.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error unlinking document {document_id} from event {event_id}: {e}")
            return False
    
    def get_document_events_links(self, document_id: int) -> List[int]:
        """Получение ID событий, связанных с документом"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT event_id FROM public.documents_events WHERE document_id = %s",
                    (document_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting document {document_id} events links: {e}")
            return []
    
    def get_event_documents_links(self, event_id: int) -> List[int]:
        """Получение ID документов, связанных с событием"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT document_id FROM public.documents_events WHERE event_id = %s",
                    (event_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting event {event_id} documents links: {e}")
            return []
    
    # ========================================
    # УПРАВЛЕНИЕ СВЯЗЯМИ СОБЫТИЙ И ИСТОЧНИКОВ
    # ========================================
    
    def link_event_to_source(self, event_id: int, source_id: int, user_id: int) -> bool:
        """Связывание события с источником"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем, что связь не существует
                    cursor.execute(
                        "SELECT 1 FROM public.events_sources WHERE event_id = %s AND source_id = %s",
                        (event_id, source_id)
                    )
                    if cursor.fetchone():
                        return False  # Связь уже существует
                    
                    # Создаем связь
                    cursor.execute(
                        "INSERT INTO public.events_sources (event_id, source_id) VALUES (%s, %s)",
                        (event_id, source_id)
                    )
                    
                    # Логируем действие
                    cursor.execute(
                        "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                        (user_id, 'EVENT_SOURCE_LINKED', 'EVENT', event_id,
                         f'Событие связано с источником {source_id}')
                    )
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error linking event {event_id} to source {source_id}: {e}")
            return False
    
    def unlink_event_from_source(self, event_id: int, source_id: int, user_id: int) -> bool:
        """Отвязывание события от источника"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Удаляем связь
                    cursor.execute(
                        "DELETE FROM public.events_sources WHERE event_id = %s AND source_id = %s",
                        (event_id, source_id)
                    )
                    
                    if cursor.rowcount > 0:
                        # Логируем действие
                        cursor.execute(
                            "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                            (user_id, 'EVENT_SOURCE_UNLINKED', 'EVENT', event_id,
                             f'Событие отвязано от источника {source_id}')
                        )
                        conn.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error unlinking event {event_id} from source {source_id}: {e}")
            return False
    
    def get_event_sources_links(self, event_id: int) -> List[int]:
        """Получение ID источников, связанных с событием"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT source_id FROM public.events_sources WHERE event_id = %s",
                    (event_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting event {event_id} sources links: {e}")
            return []
    
    def get_source_events_links(self, source_id: int) -> List[int]:
        """Получение ID событий, связанных с источником"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT event_id FROM public.events_sources WHERE source_id = %s",
                    (source_id,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting source {source_id} events links: {e}")
            return []
    
    # ========================================
    # МАССОВЫЕ ОПЕРАЦИИ СО СВЯЗЯМИ
    # ========================================
    
    def batch_link_persons_to_event(self, person_ids: List[int], event_id: int, user_id: int) -> Dict[str, Any]:
        """Массовое связывание персон с событием"""
        success_count = 0
        failed_ids = []
        
        for person_id in person_ids:
            if self.link_person_to_event(person_id, event_id, user_id):
                success_count += 1
            else:
                failed_ids.append(person_id)
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'total_requested': len(person_ids)
        }
    
    def batch_link_countries_to_event(self, country_ids: List[int], event_id: int, user_id: int) -> Dict[str, Any]:
        """Массовое связывание стран с событием"""
        success_count = 0
        failed_ids = []
        
        for country_id in country_ids:
            if self.link_country_to_event(country_id, event_id, user_id):
                success_count += 1
            else:
                failed_ids.append(country_id)
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'total_requested': len(country_ids)
        }
    
    def batch_link_documents_to_person(self, document_ids: List[int], person_id: int, user_id: int) -> Dict[str, Any]:
        """Массовое связывание документов с персоной"""
        success_count = 0
        failed_ids = []
        
        for document_id in document_ids:
            if self.link_document_to_person(document_id, person_id, user_id):
                success_count += 1
            else:
                failed_ids.append(document_id)
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'total_requested': len(document_ids)
        }
    
    def batch_link_sources_to_event(self, source_ids: List[int], event_id: int, user_id: int) -> Dict[str, Any]:
        """Массовое связывание источников с событием"""
        success_count = 0
        failed_ids = []
        
        for source_id in source_ids:
            if self.link_event_to_source(event_id, source_id, user_id):
                success_count += 1
            else:
                failed_ids.append(source_id)
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'total_requested': len(source_ids)
        }
    
    # ========================================
    # АНАЛИЗ СВЯЗЕЙ
    # ========================================
    
    def get_entity_relationships_summary(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """Получение сводки по связям сущности"""
        summary = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'relationships': {}
        }
        
        if entity_type == 'PERSON':
            summary['relationships']['events'] = len(self.get_person_events_links(entity_id))
            summary['relationships']['documents'] = len(self.get_person_documents_links(entity_id))
        
        elif entity_type == 'EVENT':
            summary['relationships']['persons'] = len(self.get_event_persons_links(entity_id))
            summary['relationships']['countries'] = len(self.get_event_countries_links(entity_id))
            summary['relationships']['documents'] = len(self.get_event_documents_links(entity_id))
            summary['relationships']['sources'] = len(self.get_event_sources_links(entity_id))
        
        elif entity_type == 'COUNTRY':
            summary['relationships']['events'] = len(self.get_country_events_links(entity_id))
        
        elif entity_type == 'DOCUMENT':
            summary['relationships']['persons'] = len(self.get_document_persons_links(entity_id))
            summary['relationships']['events'] = len(self.get_document_events_links(entity_id))
        
        elif entity_type == 'SOURCE':
            summary['relationships']['events'] = len(self.get_source_events_links(entity_id))
        
        return summary
    
    def find_related_entities(self, entity_type: str, entity_id: int, relation_type: str) -> List[int]:
        """Поиск связанных сущностей по типу связи"""
        relationships_map = {
            ('PERSON', 'events'): self.get_person_events_links,
            ('PERSON', 'documents'): self.get_person_documents_links,
            ('EVENT', 'persons'): self.get_event_persons_links,
            ('EVENT', 'countries'): self.get_event_countries_links,
            ('EVENT', 'documents'): self.get_event_documents_links,
            ('EVENT', 'sources'): self.get_event_sources_links,
            ('COUNTRY', 'events'): self.get_country_events_links,
            ('DOCUMENT', 'persons'): self.get_document_persons_links,
            ('DOCUMENT', 'events'): self.get_document_events_links,
            ('SOURCE', 'events'): self.get_source_events_links,
        }
        
        func = relationships_map.get((entity_type, relation_type))
        if func:
            return func(entity_id)
        return []
    
    def get_most_connected_entities(self, entity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение самых связанных сущностей"""
        try:
            with self.db.get_cursor() as cursor:
                if entity_type == 'PERSON':
                    cursor.execute("""
                        SELECT p.person_id, p.name, p.surname,
                               COUNT(DISTINCT ep.event_id) as events_count,
                               COUNT(DISTINCT dp.document_id) as documents_count,
                               (COUNT(DISTINCT ep.event_id) + COUNT(DISTINCT dp.document_id)) as total_connections
                        FROM public.persons p
                        LEFT JOIN public.events_persons ep ON p.person_id = ep.person_id
                        LEFT JOIN public.documents_persons dp ON p.person_id = dp.person_id
                        GROUP BY p.person_id, p.name, p.surname
                        ORDER BY total_connections DESC
                        LIMIT %s
                    """, (limit,))
                
                elif entity_type == 'EVENT':
                    cursor.execute("""
                        SELECT e.event_id, e.name,
                               COUNT(DISTINCT ep.person_id) as persons_count,
                               COUNT(DISTINCT ce.country_id) as countries_count,
                               COUNT(DISTINCT de.document_id) as documents_count,
                               COUNT(DISTINCT es.source_id) as sources_count,
                               (COUNT(DISTINCT ep.person_id) + COUNT(DISTINCT ce.country_id) + 
                                COUNT(DISTINCT de.document_id) + COUNT(DISTINCT es.source_id)) as total_connections
                        FROM public.events e
                        LEFT JOIN public.events_persons ep ON e.event_id = ep.event_id
                        LEFT JOIN public.countries_events ce ON e.event_id = ce.event_id
                        LEFT JOIN public.documents_events de ON e.event_id = de.event_id
                        LEFT JOIN public.events_sources es ON e.event_id = es.event_id
                        GROUP BY e.event_id, e.name
                        ORDER BY total_connections DESC
                        LIMIT %s
                    """, (limit,))
                
                elif entity_type == 'COUNTRY':
                    cursor.execute("""
                        SELECT c.country_id, c.name,
                               COUNT(DISTINCT ce.event_id) as events_count,
                               COUNT(DISTINCT p.person_id) as persons_count,
                               (COUNT(DISTINCT ce.event_id) + COUNT(DISTINCT p.person_id)) as total_connections
                        FROM public.countries c
                        LEFT JOIN public.countries_events ce ON c.country_id = ce.country_id
                        LEFT JOIN public.persons p ON c.country_id = p.country_id
                        GROUP BY c.country_id, c.name
                        ORDER BY total_connections DESC
                        LIMIT %s
                    """, (limit,))
                
                elif entity_type == 'DOCUMENT':
                    cursor.execute("""
                        SELECT d.document_id, d.name,
                               COUNT(DISTINCT dp.person_id) as persons_count,
                               COUNT(DISTINCT de.event_id) as events_count,
                               (COUNT(DISTINCT dp.person_id) + COUNT(DISTINCT de.event_id)) as total_connections
                        FROM public.documents d
                        LEFT JOIN public.documents_persons dp ON d.document_id = dp.document_id
                        LEFT JOIN public.documents_events de ON d.document_id = de.document_id
                        GROUP BY d.document_id, d.name
                        ORDER BY total_connections DESC
                        LIMIT %s
                    """, (limit,))
                
                elif entity_type == 'SOURCE':
                    cursor.execute("""
                        SELECT s.source_id, s.name, s.author,
                               COUNT(DISTINCT es.event_id) as events_count,
                               COUNT(DISTINCT es.event_id) as total_connections
                        FROM public.sources s
                        LEFT JOIN public.events_sources es ON s.source_id = es.source_id
                        GROUP BY s.source_id, s.name, s.author
                        ORDER BY total_connections DESC
                        LIMIT %s
                    """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting most connected entities for {entity_type}: {e}")
            return []
    
    def cleanup_orphaned_relationships(self, user_id: int) -> Dict[str, int]:
        """Очистка висячих связей (ссылки на несуществующие сущности)"""
        cleanup_stats = {
            'events_persons_cleaned': 0,
            'countries_events_cleaned': 0,
            'documents_persons_cleaned': 0,
            'documents_events_cleaned': 0,
            'events_sources_cleaned': 0
        }
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Очистка events_persons
                    cursor.execute("""
                        DELETE FROM public.events_persons ep
                        WHERE NOT EXISTS (SELECT 1 FROM public.events e WHERE e.event_id = ep.event_id)
                           OR NOT EXISTS (SELECT 1 FROM public.persons p WHERE p.person_id = ep.person_id)
                    """)
                    cleanup_stats['events_persons_cleaned'] = cursor.rowcount
                    
                    # Очистка countries_events
                    cursor.execute("""
                        DELETE FROM public.countries_events ce
                        WHERE NOT EXISTS (SELECT 1 FROM public.countries c WHERE c.country_id = ce.country_id)
                           OR NOT EXISTS (SELECT 1 FROM public.events e WHERE e.event_id = ce.event_id)
                    """)
                    cleanup_stats['countries_events_cleaned'] = cursor.rowcount
                    
                    # Очистка documents_persons
                    cursor.execute("""
                        DELETE FROM public.documents_persons dp
                        WHERE NOT EXISTS (SELECT 1 FROM public.documents d WHERE d.document_id = dp.document_id)
                           OR NOT EXISTS (SELECT 1 FROM public.persons p WHERE p.person_id = dp.person_id)
                    """)
                    cleanup_stats['documents_persons_cleaned'] = cursor.rowcount
                    
                    # Очистка documents_events
                    cursor.execute("""
                        DELETE FROM public.documents_events de
                        WHERE NOT EXISTS (SELECT 1 FROM public.documents d WHERE d.document_id = de.document_id)
                           OR NOT EXISTS (SELECT 1 FROM public.events e WHERE e.event_id = de.event_id)
                    """)
                    cleanup_stats['documents_events_cleaned'] = cursor.rowcount
                    
                    # Очистка events_sources
                    cursor.execute("""
                        DELETE FROM public.events_sources es
                        WHERE NOT EXISTS (SELECT 1 FROM public.events e WHERE e.event_id = es.event_id)
                           OR NOT EXISTS (SELECT 1 FROM public.sources s WHERE s.source_id = es.source_id)
                    """)
                    cleanup_stats['events_sources_cleaned'] = cursor.rowcount
                    
                    # Логируем очистку
                    total_cleaned = sum(cleanup_stats.values())
                    if total_cleaned > 0:
                        cursor.execute(
                            "SELECT sp_log_user_action(%s, %s, %s, %s, %s)",
                            (user_id, 'RELATIONSHIPS_CLEANUP', 'SYSTEM', None,
                             f'Очищено висячих связей: {total_cleaned}')
                        )
                    
                    conn.commit()
                    return cleanup_stats
                    
        except Exception as e:
            logger.error(f"Error cleaning up orphaned relationships: {e}")
            return cleanup_stats
from typing import Dict, Any, List
from .base_service import BaseService
from data_access import PersonRepository, CountryRepository, EventRepository, DocumentRepository, SourceRepository
from core.exceptions import ValidationError

class SearchService(BaseService):
    """Сервис для глобального поиска по всем сущностям"""
    
    def __init__(self):
        super().__init__()
        self.person_repo = PersonRepository()
        self.country_repo = CountryRepository()
        self.event_repo = EventRepository()
        self.document_repo = DocumentRepository()
        self.source_repo = SourceRepository()
    
    def global_search(self, user_id: int, search_text: str, search_types: List[str] = None,
                     limit_per_type: int = 5) -> Dict[str, Any]:
        """Глобальный поиск по всем типам сущностей"""
        if not search_text or len(search_text.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        search_text = search_text.strip()
        
        # Определяем типы для поиска
        if not search_types:
            search_types = ['persons', 'countries', 'events', 'documents', 'sources']
        
        limit_per_type = min(20, max(1, limit_per_type))
        
        results = {}
        total_found = 0
        
        # Поиск персон
        if 'persons' in search_types:
            persons = self.person_repo.search_fulltext(search_text, 0, limit_per_type)
            results['persons'] = {
                'items': persons,
                'count': len(persons),
                'total_available': persons[0]['total_count'] if persons else 0
            }
            total_found += len(persons)
        
        # Поиск стран
        if 'countries' in search_types:
            countries = self.country_repo.search_fulltext(search_text, 0, limit_per_type)
            results['countries'] = {
                'items': countries,
                'count': len(countries),
                'total_available': countries[0]['total_count'] if countries else 0
            }
            total_found += len(countries)
        
        # Поиск событий
        if 'events' in search_types:
            events = self.event_repo.search_fulltext(search_text, 0, limit_per_type)
            results['events'] = {
                'items': events,
                'count': len(events),
                'total_available': events[0]['total_count'] if events else 0
            }
            total_found += len(events)
        
        # Поиск документов
        if 'documents' in search_types:
            documents = self.document_repo.search_fulltext(search_text, True, 0, limit_per_type)
            results['documents'] = {
                'items': documents,
                'count': len(documents),
                'total_available': documents[0]['total_count'] if documents else 0
            }
            total_found += len(documents)
        
        # Поиск источников
        if 'sources' in search_types:
            sources = self.source_repo.search_fulltext(search_text, 0, limit_per_type)
            results['sources'] = {
                'items': sources,
                'count': len(sources),
                'total_available': sources[0]['total_count'] if sources else 0
            }
            total_found += len(sources)
        
        self._log_action(user_id, 'GLOBAL_SEARCH', description=f'Глобальный поиск: "{search_text}" (найдено: {total_found})')
        
        return {
            'search_text': search_text,
            'total_found': total_found,
            'results': results
        }
    
    def get_search_suggestions(self, user_id: int, search_text: str, limit: int = 10) -> List[str]:
        """Получение подсказок для поиска"""
        if not search_text or len(search_text.strip()) < 2:
            return []
        
        search_text = search_text.strip().lower()
        limit = min(20, max(1, limit))
        
        suggestions = []
        
        # Простая реализация подсказок на основе частых поисков
        # В реальном приложении можно использовать более сложные алгоритмы
        common_terms = [
            "Иван Грозный", "Петр Великий", "Екатерина II", "Александр Пушкин",
            "Отечественная война", "Революция", "Крещение Руси", "Куликовская битва",
            "Российская империя", "СССР", "Москва", "Санкт-Петербург"
        ]
        
        for term in common_terms:
            if search_text in term.lower() and term not in suggestions:
                suggestions.append(term)
                if len(suggestions) >= limit:
                    break
        
        return suggestions
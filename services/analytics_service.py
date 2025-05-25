from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_service import BaseService
from data_access import PersonRepository, CountryRepository, EventRepository, DocumentRepository, SourceRepository, AuditRepository, RelationshipsRepository

class AnalyticsService(BaseService):
    """Сервис для аналитики и статистики"""
    
    def __init__(self):
        super().__init__()
        self.person_repo = PersonRepository()
        self.country_repo = CountryRepository()
        self.event_repo = EventRepository()
        self.document_repo = DocumentRepository()
        self.source_repo = SourceRepository()
        self.audit_repo = AuditRepository()
        self.rel_repo = RelationshipsRepository()
    
    def get_dashboard_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получение основной статистики для дашборда"""
        
        # Базовая статистика по сущностям
        person_stats = self.person_repo.get_statistics()
        country_stats = self.country_repo.get_statistics()
        event_stats = self.event_repo.get_statistics()
        document_stats = self.document_repo.get_statistics()
        source_stats = self.source_repo.get_statistics()
        
        # Статистика активности пользователей за последнюю неделю
        week_ago = datetime.now() - timedelta(days=7)
        activity_stats = self.audit_repo.get_user_activity_stats(week_ago, datetime.now())
        
        # Самые связанные сущности
        top_connected_persons = self.rel_repo.get_most_connected_entities('PERSON', 5)
        top_connected_events = self.rel_repo.get_most_connected_entities('EVENT', 5)
        
        self._log_action(user_id, 'DASHBOARD_VIEWED', description='Просмотр дашборда')
        
        return {
            'entity_counts': {
                'persons': person_stats.get('total_persons', 0),
                'countries': country_stats.get('total_countries', 0),
                'events': event_stats.get('total_events', 0),
                'documents': document_stats.get('total_documents', 0),
                'sources': source_stats.get('total_sources', 0)
            },
            'quality_metrics': {
                'persons_with_biography': person_stats.get('persons_with_biography', 0),
                'events_with_dates': event_stats.get('events_with_dates', 0),
                'sources_with_valid_urls': source_stats.get('sources_with_valid_url', 0),
                'documents_avg_length': document_stats.get('average_content_length', 0)
            },
            'activity_last_week': activity_stats,
            'top_connected': {
                'persons': top_connected_persons,
                'events': top_connected_events
            }
        }
    
    def get_content_quality_report(self, admin_id: int) -> Dict[str, Any]:
        """Отчет о качестве контента (для админов)"""
        self._validate_user_permissions(admin_id, 3)
        
        # Проблемы с источниками
        sources_url_issues = self.source_repo.check_urls()
        invalid_sources = [s for s in sources_url_issues if s['url_status'] != 'VALID']
        
        # Дублирующиеся источники
        duplicate_sources = self.source_repo.find_duplicates()
        
        # Самые старые документы без связей
        all_documents = self.document_repo.get_documents(0, 1000)
        documents_without_links = []
        
        for doc in all_documents:
            if doc['persons_count'] == 0 and doc['events_count'] == 0:
                documents_without_links.append(doc)
        
        # Персоны без биографии
        all_persons = self.person_repo.get_persons(0, 1000)
        persons_without_biography = []
        
        for person in all_persons:
            person_details = self.person_repo.get_by_id(person['person_id'])
            if not person_details.get('biography'):
                persons_without_biography.append(person)
        
        self._log_action(admin_id, 'QUALITY_REPORT_VIEWED', description='Просмотр отчета о качестве контента')
        
        return {
            'sources_issues': {
                'invalid_urls': len(invalid_sources),
                'duplicates': len(duplicate_sources),
                'details': {
                    'invalid_urls': invalid_sources[:10],  # Показываем первые 10
                    'duplicates': duplicate_sources[:10]
                }
            },
            'content_gaps': {
                'documents_without_links': len(documents_without_links),
                'persons_without_biography': len(persons_without_biography),
                'details': {
                    'isolated_documents': documents_without_links[:10],
                    'persons_need_biography': persons_without_biography[:10]
                }
            },
            'recommendations': self._generate_quality_recommendations(
                len(invalid_sources), len(duplicate_sources), 
                len(documents_without_links), len(persons_without_biography)
            )
        }
    
    def get_usage_analytics(self, admin_id: int, days: int = 30) -> Dict[str, Any]:
        """Аналитика использования системы"""
        self._validate_user_permissions(admin_id, 2)
        
        if days > 365:
            days = 365  # Ограничиваем максимальный период
        
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        # Общая статистика активности
        activity_stats = self.audit_repo.get_user_activity_stats(start_date, end_date)
        
        # Логи за период
        recent_logs = self.audit_repo.get_audit_logs(start_date, end_date, limit=1000)
        
        # Анализ по дням
        daily_activity = {}
        for log in recent_logs:
            day = log['created_at'].date()
            if day not in daily_activity:
                daily_activity[day] = 0
            daily_activity[day] += 1
        
        # Самые активные пользователи
        user_activity = {}
        for log in recent_logs:
            user_id = log['user_id']
            if user_id not in user_activity:
                user_activity[user_id] = {'count': 0, 'username': log['username']}
            user_activity[user_id]['count'] += 1
        
        top_users = sorted(user_activity.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        
        self._log_action(admin_id, 'USAGE_ANALYTICS_VIEWED', 
                        description=f'Просмотр аналитики использования за {days} дней')
        
        return {
            'period': {
                'days': days,
                'start_date': start_date.date(),
                'end_date': end_date.date()
            },
            'activity_summary': activity_stats,
            'daily_activity': [
                {'date': str(date), 'count': count} 
                for date, count in sorted(daily_activity.items())
            ],
            'top_users': [
                {'user_id': uid, 'username': data['username'], 'activity_count': data['count']}
                for uid, data in top_users
            ],
            'total_actions': len(recent_logs)
        }
    
    def _generate_quality_recommendations(self, invalid_urls: int, duplicates: int, 
                                        isolated_docs: int, persons_no_bio: int) -> List[str]:
        """Генерация рекомендаций по улучшению качества"""
        recommendations = []
        
        if invalid_urls > 0:
            recommendations.append(f"Исправить {invalid_urls} источников с некорректными URL")
        
        if duplicates > 0:
            recommendations.append(f"Удалить или объединить {duplicates} дублирующихся источников")
        
        if isolated_docs > 10:
            recommendations.append(f"Связать {isolated_docs} документов с персонами или событиями")
        
        if persons_no_bio > 20:
            recommendations.append(f"Добавить биографии для {persons_no_bio} персон")
        
        if not recommendations:
            recommendations.append("Качество контента находится на высоком уровне!")
        
        return recommendations
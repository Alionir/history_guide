import json
import csv
from typing import Dict, Any, List
from datetime import datetime
from .base_service import BaseService
from data_access import PersonRepository, EventRepository, DocumentRepository

class ExportService(BaseService):
    """Сервис для экспорта данных"""
    
    def __init__(self):
        super().__init__()
        self.person_repo = PersonRepository()
        self.event_repo = EventRepository()
        self.document_repo = DocumentRepository()
    
    def export_persons_to_json(self, user_id: int, filters: Dict[str, Any] = None) -> str:
        """Экспорт персон в JSON"""
        self._validate_user_permissions(user_id, 2)  # Модератор и выше
        
        # Получаем данные
        persons = self.person_repo.get_persons(0, 10000, **filters or {})
        
        export_data = {
            'export_info': {
                'type': 'persons',
                'timestamp': datetime.now().isoformat(),
                'exported_by': user_id,
                'total_records': len(persons)
            },
            'data': persons
        }
        
        self._log_action(user_id, 'PERSONS_EXPORTED', description=f'Экспорт {len(persons)} персон в JSON')
        
        return json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
    
    def export_events_timeline_to_csv(self, user_id: int, year_from: int = None, year_to: int = None) -> str:
        """Экспорт временной линии событий в CSV"""
        self._validate_user_permissions(user_id, 2)
        
        # Получаем данные
        events = self.event_repo.get_timeline(year_from, year_to, limit=5000)
        
        # Подготавливаем CSV
        csv_content = []
        csv_content.append(['Название', 'Описание', 'Дата начала', 'Дата окончания', 'Местоположение', 'Тип', 'Длительность (дни)'])
        
        for event in events:
            csv_content.append([
                event.get('name', ''),
                event.get('description', ''),
                str(event.get('start_date', '')),
                str(event.get('end_date', '')),
                event.get('location', ''),
                event.get('event_type', ''),
                str(event.get('duration_days', ''))
            ])
        
        # Конвертируем в строку CSV
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_content)
        csv_string = output.getvalue()
        output.close()
        
        self._log_action(user_id, 'EVENTS_TIMELINE_EXPORTED', 
                        description=f'Экспорт временной линии {len(events)} событий в CSV')
        
        return csv_string
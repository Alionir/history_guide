from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Event:
    event_id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    parent_id: Optional[int] = None
    
    @property
    def period_text(self) -> str:
        """Текстовое представление периода события"""
        if self.start_date and self.end_date:
            if self.start_date == self.end_date:
                return self.start_date.strftime('%d.%m.%Y')
            else:
                return f"{self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}"
        elif self.start_date:
            return f"с {self.start_date.strftime('%d.%m.%Y')}"
        elif self.end_date:
            return f"до {self.end_date.strftime('%d.%m.%Y')}"
        else:
            return "период неизвестен"
    
    @property
    def duration_days(self) -> Optional[int]:
        """Длительность события в днях"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
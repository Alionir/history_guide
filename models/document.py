from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Document:
    document_id: int
    name: str
    content: str
    creating_date: Optional[date] = None
    
    @property
    def content_length(self) -> int:
        """Длина содержимого документа"""
        return len(self.content)
    
    @property
    def content_preview(self) -> str:
        """Краткий предварительный просмотр содержимого"""
        if len(self.content) > 200:
            return self.content[:200] + "..."
        return self.content
    
    @property
    def words_count(self) -> int:
        """Количество слов в документе"""
        return len(self.content.split())
    
    @property
    def age_years(self) -> Optional[int]:
        """Возраст документа в годах"""
        if self.creating_date:
            from datetime import date
            return date.today().year - self.creating_date.year
        return None
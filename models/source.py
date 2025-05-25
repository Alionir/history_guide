from dataclasses import dataclass
from datetime import date
from typing import Optional
import re

@dataclass
class Source:
    source_id: int
    name: str
    author: Optional[str] = None
    publication_date: Optional[date] = None
    type: Optional[str] = None
    url: Optional[str] = None
    
    @property
    def has_valid_url(self) -> bool:
        """Проверка валидности URL"""
        if not self.url:
            return False
        return self.url.startswith(('http://', 'https://'))
    
    @property
    def url_domain(self) -> Optional[str]:
        """Извлечение домена из URL"""
        if not self.has_valid_url:
            return None
        try:
            # Простая реализация извлечения домена
            domain_match = re.search(r'://([^/]+)', self.url)
            return domain_match.group(1) if domain_match else None
        except:
            return None
    
    @property
    def age_years(self) -> Optional[int]:
        """Возраст источника в годах"""
        if self.publication_date:
            from datetime import date
            return date.today().year - self.publication_date.year
        return None
    
    @property
    def author_display(self) -> str:
        """Отображение автора для UI"""
        return self.author or "Автор не указан"
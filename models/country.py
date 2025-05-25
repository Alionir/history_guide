from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Country:
    country_id: int
    name: str
    capital: Optional[str] = None
    foundation_date: Optional[date] = None
    dissolution_date: Optional[date] = None
    description: Optional[str] = None
    
    @property
    def is_existing(self) -> bool:
        """Проверка, существует ли страна в настоящее время"""
        return self.dissolution_date is None
    
    @property
    def existence_period(self) -> str:
        """Период существования в виде строки"""
        if self.foundation_date and self.dissolution_date:
            return f"{self.foundation_date.year} - {self.dissolution_date.year}"
        elif self.foundation_date:
            return f"с {self.foundation_date.year}"
        elif self.dissolution_date:
            return f"до {self.dissolution_date.year}"
        else:
            return "период неизвестен"
    
    @property
    def status(self) -> str:
        """Статус страны"""
        return "существует" if self.is_existing else "историческое"
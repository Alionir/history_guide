from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Person:
    person_id: int
    name: str
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    biography: Optional[str] = None
    country_id: Optional[int] = None
    
    @property
    def full_name(self) -> str:
        """Полное имя персоны"""
        parts = [self.name]
        if self.surname:
            parts.append(self.surname)
        if self.patronymic:
            parts.append(self.patronymic)
        return " ".join(parts)
    
    @property
    def life_years(self) -> str:
        """Годы жизни в формате строки"""
        birth = self.date_of_birth.year if self.date_of_birth else "?"
        death = self.date_of_death.year if self.date_of_death else "?"
        if self.date_of_death:
            return f"{birth} - {death}"
        elif self.date_of_birth:
            return f"{birth} - н.в."
        return "? - ?"
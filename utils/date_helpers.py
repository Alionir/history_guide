from PyQt6.QtCore import QDate
from datetime import date
from typing import Optional, Union

def qdate_to_date(qdate: Optional[QDate]) -> Optional[date]:
    """Преобразование QDate в Python date"""
    if qdate is None or not qdate.isValid():
        return None
    return date(qdate.year(), qdate.month(), qdate.day())

def date_to_qdate(py_date: Optional[date]) -> QDate:
    """Преобразование Python date в QDate"""
    if py_date is None:
        return QDate()
    return QDate(py_date.year, py_date.month, py_date.day)

def safe_date_convert(date_value: Union[QDate, date, None]) -> Optional[date]:
    """Безопасное преобразование различных типов дат в Python date"""
    if date_value is None:
        return None
    
    if isinstance(date_value, QDate):
        return qdate_to_date(date_value)
    elif isinstance(date_value, date):
        return date_value
    else:
        # Попытка преобразовать из строки или других типов
        try:
            if hasattr(date_value, 'year') and hasattr(date_value, 'month') and hasattr(date_value, 'day'):
                return date(date_value.year(), date_value.month(), date_value.day())
        except:
            pass
        return None
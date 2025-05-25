from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import logging
from core.database import DatabaseConnection
from core.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """Базовый класс для всех репозиториев"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def _execute_function(self, function_name: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Безопасное выполнение функции БД с обработкой ошибок"""
        try:
            return self.db.execute_function(function_name, params)
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def _execute_procedure(self, procedure_name: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Безопасное выполнение процедуры БД с обработкой ошибок"""
        try:
            return self.db.execute_procedure(procedure_name, params)
        except Exception as e:
            logger.error(f"Error executing procedure {procedure_name}: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
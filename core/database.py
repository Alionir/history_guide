import psycopg
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional, Union
import logging
from config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Инициализация пула соединений"""
        try:
            connection_string = (
                f"host={DATABASE_CONFIG.host} "
                f"port={DATABASE_CONFIG.port} "
                f"dbname={DATABASE_CONFIG.database} "
                f"user={DATABASE_CONFIG.user} "
                f"password={DATABASE_CONFIG.password}"
            )
            
            self._pool = ConnectionPool(
                connection_string,
                min_size=DATABASE_CONFIG.min_connections,
                max_size=DATABASE_CONFIG.max_connections
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """Контекстный менеджер для получения соединения из пула"""
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        
        connection = None
        try:
            connection = self._pool.getconn()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if connection:
                self._pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self) -> Generator[psycopg.Cursor, None, None]:
        """Контекстный менеджер для получения курсора"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                yield cursor
    
    def execute_procedure(self, procedure_name: str, params: Union[tuple, list] = None) -> List[Dict[str, Any]]:
        """Выполнение хранимой процедуры с возвратом результата"""
        with self.get_cursor() as cursor:
            try:
                if params:
                    cursor.execute(f"CALL {procedure_name}(%s)", params)
                else:
                    cursor.execute(f"CALL {procedure_name}()")
                
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                return []
            except Exception as e:
                logger.error(f"Error executing procedure {procedure_name}: {e}")
                raise
    
    def execute_function(self, function_name: str, params: Union[tuple, list] = None) -> List[Dict[str, Any]]:
        """Выполнение хранимой функции с возвратом результата"""
        with self.get_cursor() as cursor:
            try:
                if params:
                    # Создаем правильное количество плейсхолдеров
                    if isinstance(params, (tuple, list)):
                        placeholders = ', '.join(['%s'] * len(params))
                        query = f"SELECT * FROM {function_name}({placeholders})"
                        cursor.execute(query, params)
                    else:
                        # Если передан один параметр не в кортеже
                        cursor.execute(f"SELECT * FROM {function_name}(%s)", (params,))
                else:
                    cursor.execute(f"SELECT * FROM {function_name}()")
                
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                return []
            except Exception as e:
                logger.error(f"Error executing function {function_name} with params {params}: {e}")
                raise
    
    def close(self):
        """Закрытие пула соединений"""
        if self._pool:
            self._pool.close()
            logger.info("Database connection pool closed")
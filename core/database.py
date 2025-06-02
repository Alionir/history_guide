import psycopg
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional, Union
import logging
import time
from config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    _pool = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_pool()
            self._initialized = True
    
    def _initialize_pool(self):
        """Инициализация пула соединений с улучшенной обработкой ошибок"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                connection_string = (
                    f"host={DATABASE_CONFIG.host} "
                    f"port={DATABASE_CONFIG.port} "
                    f"dbname={DATABASE_CONFIG.database} "
                    f"user={DATABASE_CONFIG.user} "
                    f"password={DATABASE_CONFIG.password} "
                    f"sslmode=prefer "
                    f"connect_timeout=10"
                )
                
                self._pool = ConnectionPool(
                    connection_string,
                    min_size=DATABASE_CONFIG.min_connections,
                    max_size=DATABASE_CONFIG.max_connections,
                    max_idle=300,  # 5 минут максимального простоя
                    check=ConnectionPool.check_connection,
                    configure=self._configure_connection
                )
                
                # Тестируем подключение
                with self.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                        result = cur.fetchone()
                        if result[0] != 1:
                            raise Exception("Database connection test failed")
                
                logger.info("Database connection pool initialized successfully")
                return
                
            except Exception as e:
                logger.error(f"Failed to initialize database pool (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
    
    def _configure_connection(self, conn):
        """Конфигурация нового соединения"""
        try:
            # Временно включаем autocommit для настройки
            old_autocommit = conn.autocommit
            conn.autocommit = True
            
            # Устанавливаем параметры сессии
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '30s'")
                cur.execute("SET idle_in_transaction_session_timeout = '60s'")
                cur.execute("SET lock_timeout = '10s'")
                cur.execute("SET timezone = 'UTC'")
            
            # Возвращаем исходное значение autocommit
            conn.autocommit = old_autocommit
            
            # Устанавливаем уровень изоляции
            conn.isolation_level = psycopg.IsolationLevel.READ_COMMITTED
            
        except Exception as e:
            logger.error(f"Failed to configure connection: {e}")
            # Убеждаемся, что соединение в правильном состоянии
            try:
                if conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS:
                    conn.rollback()
                conn.autocommit = False
            except:
                pass
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """Контекстный менеджер для получения соединения из пула с улучшенной обработкой ошибок"""
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        
        connection = None
        try:
            connection = self._pool.getconn(timeout=30)  # 30 секунд таймаут
            
            # Проверяем состояние соединения
            if connection.closed:
                logger.warning("Connection is closed, getting new one")
                self._pool.putconn(connection, close=True)
                connection = self._pool.getconn(timeout=30)
            
            yield connection
            
            # Если есть активная транзакция, коммитим её
            if connection.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS:
                connection.commit()
                
        except Exception as e:
            if connection and not connection.closed:
                try:
                    # Откатываем транзакцию при ошибке
                    if connection.info.transaction_status == psycopg.pq.TransactionStatus.INERROR:
                        connection.rollback()
                    elif connection.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS:
                        connection.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
            
            logger.error(f"Database error: {e}")
            raise
        finally:
            if connection and self._pool:
                try:
                    # Проверяем состояние соединения перед возвратом в пул
                    if connection.closed:
                        self._pool.putconn(connection, close=True)
                    elif connection.info.transaction_status == psycopg.pq.TransactionStatus.INERROR:
                        # Соединение в состоянии ошибки, откатываем и закрываем
                        connection.rollback()
                        self._pool.putconn(connection, close=True)
                    else:
                        # Убеждаемся, что нет активной транзакции
                        if connection.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS:
                            connection.rollback()
                        self._pool.putconn(connection)
                except Exception as cleanup_error:
                    logger.error(f"Error during connection cleanup: {cleanup_error}")
                    try:
                        self._pool.putconn(connection, close=True)
                    except:
                        pass
    
    @contextmanager
    def get_cursor(self, autocommit: bool = False) -> Generator[psycopg.Cursor, None, None]:
        """Контекстный менеджер для получения курсора"""
        with self.get_connection() as conn:
            if autocommit:
                conn.autocommit = True
            try:
                with conn.cursor() as cursor:
                    yield cursor
            finally:
                if autocommit:
                    conn.autocommit = False
    
    @contextmanager
    def get_transaction(self) -> Generator[psycopg.Connection, None, None]:
        """Контекстный менеджер для управления транзакциями"""
        with self.get_connection() as conn:
            try:
                conn.autocommit = False
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def execute_procedure(self, procedure_name: str, params: Union[tuple, list] = None) -> List[Dict[str, Any]]:
        """Выполнение хранимой процедуры с возвратом результата"""
        with self.get_transaction() as conn:
            with conn.cursor() as cursor:
                try:
                    if params:
                        cursor.execute(f"CALL {procedure_name}({', '.join(['%s'] * len(params))})", params)
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
        with self.get_transaction() as conn:
            with conn.cursor() as cursor:
                try:
                    if params:
                        if isinstance(params, (tuple, list)):
                            placeholders = ', '.join(['%s'] * len(params))
                            query = f"SELECT * FROM {function_name}({placeholders})"
                            cursor.execute(query, params)
                        else:
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
    
    def execute_query(self, query: str, params: Union[tuple, list] = None, fetch_all: bool = True) -> List[Dict[str, Any]]:
        """Выполнение произвольного SQL запроса"""
        with self.get_transaction() as conn:
            with conn.cursor() as cursor:
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        if fetch_all:
                            rows = cursor.fetchall()
                            return [dict(zip(columns, row)) for row in rows]
                        else:
                            row = cursor.fetchone()
                            return [dict(zip(columns, row))] if row else []
                    return []
                except Exception as e:
                    logger.error(f"Error executing query: {e}")
                    raise
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка состояния подключения к базе данных"""
        try:
            start_time = time.time()
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version(), current_database(), current_user, now()")
                    result = cursor.fetchone()
                    
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'database_version': result[0] if result else 'unknown',
                'database_name': result[1] if result else 'unknown',
                'current_user': result[2] if result else 'unknown',
                'server_time': result[3] if result else 'unknown',
                'pool_size': self._pool.get_stats()['pool_size'] if self._pool else 0,
                'pool_available': self._pool.get_stats()['pool_available'] if self._pool else 0
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'pool_size': self._pool.get_stats()['pool_size'] if self._pool else 0,
                'pool_available': self._pool.get_stats()['pool_available'] if self._pool else 0
            }
    
    def close(self):
        """Закрытие пула соединений"""
        if self._pool:
            try:
                self._pool.close()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
            finally:
                self._pool = None
                self._initialized = False


# Улучшенный базовый репозиторий с retry логикой
class ImprovedBaseRepository:
    """Улучшенный базовый класс для всех репозиториев с retry логикой"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.max_retries = 3
        self.retry_delay = 1
    
    def _execute_with_retry(self, operation, *args, **kwargs):
        """Выполнение операции с повторными попытками"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Database operation failed after {self.max_retries} attempts: {e}")
        
        raise last_exception
    
    def _execute_function(self, function_name: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Безопасное выполнение функции БД с обработкой ошибок и retry"""
        return self._execute_with_retry(self.db.execute_function, function_name, params)
    
    def _execute_procedure(self, procedure_name: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Безопасное выполнение процедуры БД с обработкой ошибок и retry"""
        return self._execute_with_retry(self.db.execute_procedure, procedure_name, params)
    
    def _execute_query(self, query: str, params: tuple = None, fetch_all: bool = True) -> List[Dict[str, Any]]:
        """Безопасное выполнение SQL запроса с обработкой ошибок и retry"""
        return self._execute_with_retry(self.db.execute_query, query, params, fetch_all)
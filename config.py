import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 10
    statement_timeout: int = 30
    idle_timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 1
    
    def __post_init__(self):
        required_fields = ['host', 'database', 'user', 'password']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Database {field} must be set in environment variables")
        
        # Валидация числовых параметров
        if self.min_connections < 1:
            self.min_connections = 1
        if self.max_connections < self.min_connections:
            self.max_connections = self.min_connections + 5
        if self.connection_timeout < 5:
            self.connection_timeout = 10

@dataclass
class AppConfig:
    app_name: str = "History Guide"
    version: str = "1.0.0"
    log_level: str = "INFO"
    log_file: str = "history_guide.log"
    items_per_page: int = 50
    debug: bool = False
    
    # Настройки безопасности
    session_timeout_minutes: int = 120
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # Настройки производительности
    cache_enabled: bool = True
    cache_timeout_seconds: int = 300
    max_search_results: int = 1000
    
    # Настройки UI
    theme: str = "light"
    language: str = "ru"
    date_format: str = "%d.%m.%Y"
    datetime_format: str = "%d.%m.%Y %H:%M"

# Создание конфигураций с обработкой ошибок
try:
    DATABASE_CONFIG = DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'history_guide'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '2')),
        max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '10')),
        connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', '10')),
        statement_timeout=int(os.getenv('DB_STATEMENT_TIMEOUT', '30')),
        idle_timeout=int(os.getenv('DB_IDLE_TIMEOUT', '300'))
    )
except (ValueError, TypeError) as e:
    print(f"Database configuration error: {e}")
    print("Please check your .env file and ensure all required database variables are set.")
    print("Required variables: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
    print("Optional variables: DB_PORT, DB_MIN_CONNECTIONS, DB_MAX_CONNECTIONS")
    raise

APP_CONFIG = AppConfig(
    log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    debug=os.getenv('DEBUG', 'False').lower() == 'true',
    items_per_page=int(os.getenv('ITEMS_PER_PAGE', '50')),
    session_timeout_minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', '120')),
    cache_enabled=os.getenv('CACHE_ENABLED', 'True').lower() == 'true',
    cache_timeout_seconds=int(os.getenv('CACHE_TIMEOUT_SECONDS', '300')),
    theme=os.getenv('UI_THEME', 'light'),
    language=os.getenv('UI_LANGUAGE', 'ru')
)

# Функция для валидации конфигурации
def validate_config():
    """Валидация конфигурации приложения"""
    errors = []
    
    # Проверка базы данных
    if not DATABASE_CONFIG.host:
        errors.append("DB_HOST is required")
    if not DATABASE_CONFIG.database:
        errors.append("DB_NAME is required")
    if not DATABASE_CONFIG.user:
        errors.append("DB_USER is required")
    if not DATABASE_CONFIG.password:
        errors.append("DB_PASSWORD is required")
    
    # Проверка логирования
    if APP_CONFIG.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        errors.append("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True

# Выполняем валидацию при импорте
try:
    validate_config()
except ValueError as e:
    print(f"Configuration validation failed: {e}")
    raise

# Вспомогательные функции для работы с конфигурацией
def get_database_url() -> str:
    """Получение URL для подключения к базе данных"""
    return (
        f"postgresql://{DATABASE_CONFIG.user}:{DATABASE_CONFIG.password}"
        f"@{DATABASE_CONFIG.host}:{DATABASE_CONFIG.port}/{DATABASE_CONFIG.database}"
    )

def is_debug_mode() -> bool:
    """Проверка режима отладки"""
    return APP_CONFIG.debug

def get_log_level() -> str:
    """Получение уровня логирования"""
    return APP_CONFIG.log_level

def print_config_summary():
    """Вывод сводки конфигурации (без паролей)"""
    print(f"Application: {APP_CONFIG.app_name} v{APP_CONFIG.version}")
    print(f"Database: {DATABASE_CONFIG.host}:{DATABASE_CONFIG.port}/{DATABASE_CONFIG.database}")
    print(f"User: {DATABASE_CONFIG.user}")
    print(f"Connections: {DATABASE_CONFIG.min_connections}-{DATABASE_CONFIG.max_connections}")
    print(f"Log level: {APP_CONFIG.log_level}")
    print(f"Debug mode: {APP_CONFIG.debug}")
    print(f"Cache enabled: {APP_CONFIG.cache_enabled}")
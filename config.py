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
    min_connections: int = 1
    max_connections: int = 10
    
    def __post_init__(self):

        required_fields = ['host', 'database', 'user', 'password']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Database {field} must be set in environment variables")

@dataclass
class AppConfig:
    app_name: str = "History Guide"
    version: str = "1.0.0"
    log_level: str = "INFO"
    log_file: str = "history_guide.log"
    items_per_page: int = 50
    debug: bool = False

try:
    DATABASE_CONFIG = DatabaseConfig(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
except (ValueError, TypeError) as e:
    print(f"Configuration error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    raise

APP_CONFIG = AppConfig(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    debug=os.getenv('DEBUG', 'False').lower() == 'true'
)
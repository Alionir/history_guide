import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from config import APP_CONFIG

class HistoryGuideLogger:
    """Система логирования для исторического справочника"""
    
    _instance: Optional['HistoryGuideLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            self._initialized = True
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        # Создаем директорию логов если не существует
        log_dir = os.path.dirname(APP_CONFIG.log_file) or '.'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Основной логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, APP_CONFIG.log_level))
        
        # Очищаем существующие обработчики
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Обработчик для файла с ротацией
        file_handler = logging.handlers.RotatingFileHandler(
            APP_CONFIG.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчики
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Специальный логгер для аудита
        audit_logger = logging.getLogger('audit')
        audit_handler = logging.handlers.RotatingFileHandler(
            'audit.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
        
        logging.info("Logging system initialized successfully")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Получение логгера по имени"""
        return logging.getLogger(name)
    
    @staticmethod
    def log_audit(message: str):
        """Логирование аудита"""
        audit_logger = logging.getLogger('audit')
        audit_logger.info(message)


# Инициализируем систему логирования при импорте
_logger_instance = HistoryGuideLogger()


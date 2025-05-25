import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from ui.auth.login_window import LoginWindow
from core.database import DatabaseConnection
from core.auth import AuthService
from config import APP_CONFIG

def setup_logging():
    """Настройка системы логирования"""
    logging.basicConfig(
        level=getattr(logging, APP_CONFIG.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(APP_CONFIG.log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName(APP_CONFIG.app_name)
    app.setApplicationVersion(APP_CONFIG.version)
    
    
    try:
        # Инициализация подключения к БД
        db = DatabaseConnection()
        
        # Инициализация сервиса аутентификации
        auth_service = AuthService()
        
        # Показ окна входа
        login_window = LoginWindow(auth_service)
        if login_window.exec() == login_window.DialogCode.Accepted:
            # Получаем данные пользователя из окна входа
            user_data = login_window.get_current_user()
            
            if user_data:
                logger.info(f"User logged in successfully: {user_data.get('username', 'Unknown')}")
                # При успешном входе показываем главное окно
                main_window = MainWindow(user_data)
                main_window.show()
                
                # Запуск приложения
                return app.exec()
            else:
                logger.error("No user data received from login window")
                return 1
        else:
            logger.info("Login cancelled by user")
            return 0
            
    except Exception as e:
        logger.critical(f"Critical error during application startup: {e}")
        import traceback
        logger.critical(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        # Закрытие подключения к БД
        try:
            if 'db' in locals():
                db.close()
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())
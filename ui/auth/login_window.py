from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.user_service import UserService
from core.exceptions import AuthenticationError, ValidationError

class LoginWindow(QDialog):
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.user_service = UserService()
        self.current_user = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Исторический справочник")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Форма входа
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Введите имя пользователя")
        form_layout.addRow("Пользователь:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Введите пароль")
        form_layout.addRow("Пароль:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Войти")
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setDefault(True)
        buttons_layout.addWidget(self.login_btn)
        
        self.register_btn = QPushButton("Регистрация")
        self.register_btn.clicked.connect(self.show_register)
        buttons_layout.addWidget(self.register_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Обработка Enter
        self.password_edit.returnPressed.connect(self.login)
        self.username_edit.returnPressed.connect(self.login)
    
    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        try:
            # Аутентификация через сервис
            user_data = self.user_service.authenticate_user(username, password)
            
            if user_data:
                self.current_user = user_data
                QMessageBox.information(self, "Успех", f"Добро пожаловать, {username}!")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверные учетные данные")
        
        except (AuthenticationError, ValidationError) as e:
            QMessageBox.warning(self, "Ошибка аутентификации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Системная ошибка", f"Произошла ошибка: {str(e)}")
    
    def show_register(self):
        try:
            from ui.auth.register_window import RegisterWindow
            register_window = RegisterWindow(self.user_service, self)
            if register_window.exec() == QDialog.DialogCode.Accepted:
                # После успешной регистрации можно автоматически войти
                user_data = register_window.get_registered_user()
                if user_data:
                    self.current_user = user_data
                    self.accept()
        except ImportError:
            QMessageBox.information(self, "Информация", "Окно регистрации пока недоступно")
    
    def get_current_user(self):
        return self.current_user
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.user_service import UserService
from core.exceptions import AuthenticationError, ValidationError
class RegisterWindow(QDialog):
    def __init__(self, user_service, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        self.registered_user = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Регистрация")
        self.setFixedSize(400, 350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Регистрация нового пользователя")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        layout.addWidget(title)
        
        # Форма регистрации
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Минимум 3 символа")
        form_layout.addRow("Имя пользователя:", self.username_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@email.com")
        form_layout.addRow("Email:", self.email_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Минимум 8 символов")
        form_layout.addRow("Пароль:", self.password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Повторите пароль")
        form_layout.addRow("Подтверждение:", self.confirm_password_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.register_btn = QPushButton("Зарегистрироваться")
        self.register_btn.clicked.connect(self.register)
        self.register_btn.setDefault(True)
        buttons_layout.addWidget(self.register_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def register(self):
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not all([username, email, password, confirm_password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        try:
            result = self.user_service.register_user(username, email, password, confirm_password)
            
            if result:
                self.registered_user = result
                QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
                self.accept()
        
        except ValidationError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Системная ошибка", f"Произошла ошибка: {str(e)}")
    
    def get_registered_user(self):
        return self.registered_user
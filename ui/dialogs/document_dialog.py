
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
class DocumentDialog(QDialog):
    def __init__(self, user_data, document_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.document_data = document_data
        from services.document_service import DocumentService
        self.document_service = DocumentService()
        self.setup_ui()
        
        if document_data:
            self.populate_form()
    
    def setup_ui(self):
        self.setWindowTitle("Добавить документ" if not self.document_data else "Редактировать документ")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Основная информация
        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout(main_group)
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Обязательное поле (мин. 3 символа)")
        main_layout.addRow("Название:", self.name_edit)
        
        # Дата создания
        date_layout = QHBoxLayout()
        self.date_checkbox = QCheckBox("Указать")
        self.creating_date = QDateEdit()
        self.creating_date.setCalendarPopup(True)
        self.creating_date.setDate(QDate.currentDate())
        self.creating_date.setEnabled(False)
        self.date_checkbox.toggled.connect(self.creating_date.setEnabled)
        date_layout.addWidget(self.date_checkbox)
        date_layout.addWidget(self.creating_date)
        main_layout.addRow("Дата создания:", date_layout)
        
        layout.addWidget(main_group)
        
        # Содержимое
        content_group = QGroupBox("Содержимое документа")
        content_layout = QVBoxLayout(content_group)
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Введите текст документа...")
        content_layout.addWidget(self.content_edit)
        
        # Счетчик символов и кнопки форматирования
        tools_layout = QHBoxLayout()
        
        # Кнопки форматирования
        self.bold_btn = QPushButton("Ж")
        self.bold_btn.setMaximumWidth(30)
        self.bold_btn.clicked.connect(self.toggle_bold)
        tools_layout.addWidget(self.bold_btn)
        
        self.italic_btn = QPushButton("К")
        self.italic_btn.setMaximumWidth(30)
        self.italic_btn.clicked.connect(self.toggle_italic)
        tools_layout.addWidget(self.italic_btn)
        
        tools_layout.addStretch()
        
        # Счетчик символов
        self.content_char_count = QLabel("0 / 1000000 символов")
        self.content_edit.textChanged.connect(self.update_content_char_count)
        tools_layout.addWidget(self.content_char_count)
        
        content_layout.addLayout(tools_layout)
        layout.addWidget(content_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_document)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def populate_form(self):
        """Заполнение формы данными документа"""
        if not self.document_data:
            return
        
        self.name_edit.setText(self.document_data.get('name', ''))
        self.content_edit.setPlainText(self.document_data.get('content', ''))
        
        # Дата создания
        if self.document_data.get('creating_date'):
            self.date_checkbox.setChecked(True)
            creating_date = QDate.fromString(str(self.document_data['creating_date']), "yyyy-MM-dd")
            self.creating_date.setDate(creating_date)
    
    def update_content_char_count(self):
        """Обновление счетчика символов содержимого"""
        text = self.content_edit.toPlainText()
        count = len(text)
        self.content_char_count.setText(f"{count} / 1000000 символов")
        
        if count > 1000000:
            self.content_char_count.setStyleSheet("color: red;")
        elif count < 10:
            self.content_char_count.setStyleSheet("color: orange;")
        else:
            self.content_char_count.setStyleSheet("")
    
    def toggle_bold(self):
        """Переключение жирного текста"""
        cursor = self.content_edit.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontWeight(QFont.Weight.Bold if fmt.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        cursor.setCharFormat(fmt)
        self.content_edit.setTextCursor(cursor)
    
    def toggle_italic(self):
        """Переключение курсива"""
        cursor = self.content_edit.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        cursor.setCharFormat(fmt)
        self.content_edit.setTextCursor(cursor)
    
    def save_document(self):
        """Сохранение документа"""
        # Валидация
        name = self.name_edit.text().strip()
        if not name or len(name) < 3:
            QMessageBox.warning(self, "Ошибка", "Название должно содержать минимум 3 символа")
            return
        
        content = self.content_edit.toPlainText().strip()
        if not content or len(content) < 10:
            QMessageBox.warning(self, "Ошибка", "Содержимое должно содержать минимум 10 символов")
            return
        
        if len(content) > 1000000:
            QMessageBox.warning(self, "Ошибка", "Содержимое не может превышать 1 млн символов")
            return
        
        # Подготовка данных
        document_data = {
            'name': name,
            'content': content
        }
        
        if self.date_checkbox.isChecked():
            document_data['creating_date'] = self.creating_date.date()
        
        try:
            if self.document_data:  # Редактирование
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.document_service.update_document_direct(
                        self.user_data['user_id'],
                        self.document_data['document_id'],
                        document_data
                    )
                else:  # Заявка
                    result = self.document_service.update_document_request(
                        self.user_data['user_id'],
                        self.document_data['document_id'],
                        document_data
                    )
            else:  # Создание
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.document_service.create_document_direct(
                        self.user_data['user_id'],
                        document_data
                    )
                else:  # Заявка
                    result = self.document_service.create_document_request(
                        self.user_data['user_id'],
                        document_data
                    )
            
            if result.get('success'):
                if self.user_data['role_id'] >= 2:
                    QMessageBox.information(self, "Успех", "Документ сохранен")
                else:
                    QMessageBox.information(self, "Успех", "Заявка отправлена на модерацию")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
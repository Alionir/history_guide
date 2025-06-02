from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
class CountryDialog(QDialog):
    def __init__(self, user_data, country_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.country_data = country_data
        from services.country_service import CountryService
        self.country_service = CountryService()
        self.setup_ui()
        
        if country_data:
            self.populate_form()
    
    def setup_ui(self):
        self.setWindowTitle("Добавить страну" if not self.country_data else "Редактировать страну")
        self.setModal(True)
        self.resize(500, 450)
        
        layout = QVBoxLayout(self)
        
        # Основная информация
        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout(main_group)
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Обязательное поле (мин. 2 символа)")
        main_layout.addRow("Название:", self.name_edit)
        
        # Столица
        self.capital_edit = QLineEdit()
        self.capital_edit.setPlaceholderText("Название столицы")
        main_layout.addRow("Столица:", self.capital_edit)
        
        layout.addWidget(main_group)
        
        # Период существования
        period_group = QGroupBox("Период существования")
        period_layout = QFormLayout(period_group)
        
        # Дата основания
        foundation_layout = QHBoxLayout()
        self.foundation_checkbox = QCheckBox("Указать")
        self.foundation_date = QDateEdit()
        self.foundation_date.setCalendarPopup(True)
        self.foundation_date.setDate(QDate(1000, 1, 1))
        self.foundation_date.setEnabled(False)
        self.foundation_checkbox.toggled.connect(self.foundation_date.setEnabled)
        foundation_layout.addWidget(self.foundation_checkbox)
        foundation_layout.addWidget(self.foundation_date)
        period_layout.addRow("Дата основания:", foundation_layout)
        
        # Дата роспуска
        dissolution_layout = QHBoxLayout()
        self.dissolution_checkbox = QCheckBox("Указать")
        self.dissolution_date = QDateEdit()
        self.dissolution_date.setCalendarPopup(True)
        self.dissolution_date.setDate(QDate.currentDate())
        self.dissolution_date.setEnabled(False)
        self.dissolution_checkbox.toggled.connect(self.dissolution_date.setEnabled)
        dissolution_layout.addWidget(self.dissolution_checkbox)
        dissolution_layout.addWidget(self.dissolution_date)
        period_layout.addRow("Дата роспуска:", dissolution_layout)
        
        layout.addWidget(period_group)
        
        # Описание
        desc_group = QGroupBox("Описание")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Историческая информация о стране...")
        self.description_edit.setMaximumHeight(120)
        desc_layout.addWidget(self.description_edit)
        
        # Счетчик символов
        self.desc_char_count = QLabel("0 / 5000 символов")
        self.description_edit.textChanged.connect(self.update_desc_char_count)
        desc_layout.addWidget(self.desc_char_count)
        
        layout.addWidget(desc_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_country)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def populate_form(self):
        """Заполнение формы данными страны"""
        if not self.country_data:
            return
        
        self.name_edit.setText(self.country_data.get('name', ''))
        self.capital_edit.setText(self.country_data.get('capital', '') or '')
        self.description_edit.setPlainText(self.country_data.get('description', '') or '')
        
        # Даты
        if self.country_data.get('foundation_date'):
            self.foundation_checkbox.setChecked(True)
            foundation_date = QDate.fromString(str(self.country_data['foundation_date']), "yyyy-MM-dd")
            self.foundation_date.setDate(foundation_date)
        
        if self.country_data.get('dissolution_date'):
            self.dissolution_checkbox.setChecked(True)
            dissolution_date = QDate.fromString(str(self.country_data['dissolution_date']), "yyyy-MM-dd")
            self.dissolution_date.setDate(dissolution_date)
    
    def update_desc_char_count(self):
        """Обновление счетчика символов описания"""
        text = self.description_edit.toPlainText()
        count = len(text)
        self.desc_char_count.setText(f"{count} / 5000 символов")
        
        if count > 5000:
            self.desc_char_count.setStyleSheet("color: red;")
        else:
            self.desc_char_count.setStyleSheet("")
    
    def save_country(self):
        """Сохранение страны"""
        # Валидация
        name = self.name_edit.text().strip()
        if not name or len(name) < 2:
            QMessageBox.warning(self, "Ошибка", "Название должно содержать минимум 2 символа")
            return
        
        if len(self.description_edit.toPlainText()) > 5000:
            QMessageBox.warning(self, "Ошибка", "Описание не может содержать более 5000 символов")
            return
        
        # Проверка дат
        if (self.foundation_checkbox.isChecked() and self.dissolution_checkbox.isChecked() and
            self.foundation_date.date() > self.dissolution_date.date()):
            QMessageBox.warning(self, "Ошибка", "Дата основания не может быть позже даты роспуска")
            return
        
        # Подготовка данных
        country_data = {
            'name': name,
            'capital': self.capital_edit.text().strip() or None,
            'description': self.description_edit.toPlainText().strip() or None
        }
        
        # Даты
        if self.foundation_checkbox.isChecked():
            country_data['foundation_date'] = self.foundation_date.date()
        
        if self.dissolution_checkbox.isChecked():
            country_data['dissolution_date'] = self.dissolution_date.date()
        
        try:
            if self.country_data:  # Редактирование
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.country_service.update_country_direct(
                        self.user_data['user_id'],
                        self.country_data['country_id'],
                        country_data
                    )
                else:  # Заявка
                    result = self.country_service.update_country_request(
                        self.user_data['user_id'],
                        self.country_data['country_id'],
                        country_data
                    )
            else:  # Создание
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.country_service.create_country_direct(
                        self.user_data['user_id'],
                        country_data
                    )
                else:  # Заявка
                    result = self.country_service.create_country_request(
                        self.user_data['user_id'],
                        country_data
                    )
            
            if result.get('success'):
                if self.user_data['role_id'] >= 2:
                    QMessageBox.information(self, "Успех", "Страна сохранена")
                else:
                    QMessageBox.information(self, "Успех", "Заявка отправлена на модерацию")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
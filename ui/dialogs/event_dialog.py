from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import date
from utils.date_helpers import safe_date_convert
class EventDialog(QDialog):
    def __init__(self, user_data, event_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.event_data = event_data
        from services.event_service import EventService
        self.event_service = EventService()
        self.setup_ui()
        
        if event_data:
            self.populate_form()
    
    def setup_ui(self):
        self.setWindowTitle("Добавить событие" if not self.event_data else "Редактировать событие")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Основная информация
        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout(main_group)
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Обязательное поле (мин. 3 символа)")
        main_layout.addRow("Название:", self.name_edit)
        
        # Тип события
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("Например: битва, договор, основание...")
        main_layout.addRow("Тип события:", self.type_edit)
        
        # Местоположение
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Город, регион, страна...")
        main_layout.addRow("Местоположение:", self.location_edit)
        
        # Родительское событие
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("Нет родительского события", None)
        main_layout.addRow("Родительское событие:", self.parent_combo)
        
        layout.addWidget(main_group)
        
        # Даты
        dates_group = QGroupBox("Период события")
        dates_layout = QFormLayout(dates_group)
        
        # Дата начала
        start_layout = QHBoxLayout()
        self.start_checkbox = QCheckBox("Указать")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate(1000, 1, 1))
        self.start_date.setEnabled(False)
        self.start_checkbox.toggled.connect(self.start_date.setEnabled)
        start_layout.addWidget(self.start_checkbox)
        start_layout.addWidget(self.start_date)
        dates_layout.addRow("Дата начала:", start_layout)
        
        # Дата окончания
        end_layout = QHBoxLayout()
        self.end_checkbox = QCheckBox("Указать")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate(1000, 1, 1))
        self.end_date.setEnabled(False)
        self.end_checkbox.toggled.connect(self.end_date.setEnabled)
        end_layout.addWidget(self.end_checkbox)
        end_layout.addWidget(self.end_date)
        dates_layout.addRow("Дата окончания:", end_layout)
        
        layout.addWidget(dates_group)
        
        # Описание
        desc_group = QGroupBox("Описание")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Подробное описание события...")
        self.description_edit.setMaximumHeight(150)
        desc_layout.addWidget(self.description_edit)
        
        # Счетчик символов
        self.desc_char_count = QLabel("0 / 5000 символов")
        self.description_edit.textChanged.connect(self.update_desc_char_count)
        desc_layout.addWidget(self.desc_char_count)
        
        layout.addWidget(desc_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_event)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def populate_form(self):
        """Заполнение формы данными события"""
        if not self.event_data:
            return
        
        self.name_edit.setText(self.event_data.get('name', ''))
        self.type_edit.setText(self.event_data.get('event_type', '') or '')
        self.location_edit.setText(self.event_data.get('location', '') or '')
        self.description_edit.setPlainText(self.event_data.get('description', '') or '')
        
        # Даты
        if self.event_data.get('start_date'):
            self.start_checkbox.setChecked(True)
            start_date = QDate.fromString(str(self.event_data['start_date']), "yyyy-MM-dd")
            self.start_date.setDate(start_date)
        
        if self.event_data.get('end_date'):
            self.end_checkbox.setChecked(True)
            end_date = QDate.fromString(str(self.event_data['end_date']), "yyyy-MM-dd")
            self.end_date.setDate(end_date)
    
    def update_desc_char_count(self):
        """Обновление счетчика символов описания"""
        text = self.description_edit.toPlainText()
        count = len(text)
        self.desc_char_count.setText(f"{count} / 5000 символов")
        
        if count > 5000:
            self.desc_char_count.setStyleSheet("color: red;")
        else:
            self.desc_char_count.setStyleSheet("")
    
    def validate_form(self):
        """Валидация формы"""
        errors = []
        
        # Проверка названия
        name = self.name_edit.text().strip()
        if not name:
            errors.append("Название события обязательно")
        elif len(name) < 3:
            errors.append("Название должно содержать минимум 3 символа")
        elif len(name) > 200:
            errors.append("Название не может содержать более 200 символов")
        
        # Проверка типа события
        event_type = self.type_edit.text().strip()
        if event_type and len(event_type) > 50:
            errors.append("Тип события не может содержать более 50 символов")
        
        # Проверка местоположения
        location = self.location_edit.text().strip()
        if location and len(location) > 200:
            errors.append("Местоположение не может содержать более 200 символов")
        
        # Проверка описания
        description = self.description_edit.toPlainText().strip()
        if description and len(description) > 5000:
            errors.append("Описание не может содержать более 5000 символов")
        
        # Проверка дат
        start_date = None
        end_date = None
        
        if self.start_checkbox.isChecked():
            start_date = safe_date_convert(self.start_date.date())
        
        if self.end_checkbox.isChecked():
            end_date = safe_date_convert(self.end_date.date())
        
        if start_date and end_date and start_date > end_date:
            errors.append("Дата начала не может быть позже даты окончания")
        
        return errors
    
    def get_form_data(self):
        """Получение данных формы"""
        data = {
            'name': self.name_edit.text().strip(),
            'event_type': self.type_edit.text().strip() or None,
            'location': self.location_edit.text().strip() or None,
            'description': self.description_edit.toPlainText().strip() or None,
            'parent_id': self.parent_combo.currentData()
        }
        
        # Даты
        if self.start_checkbox.isChecked():
            data['start_date'] = safe_date_convert(self.start_date.date())
        else:
            data['start_date'] = None
        
        if self.end_checkbox.isChecked():
            data['end_date'] = safe_date_convert(self.end_date.date())
        else:
            data['end_date'] = None
        
        return data
    
    def save_event(self):
        """Сохранение события"""
        # Валидация
        errors = self.validate_form()
        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return
        
        # Получение данных
        event_data = self.get_form_data()
        
        try:
            # Блокируем кнопку на время сохранения
            self.save_btn.setEnabled(False)
            self.save_btn.setText("Сохранение...")
            
            if self.event_data:
                # Редактирование существующего события
                if self.user_data.get('role_id', 1) >= 2:  # Модератор или админ
                    result = self.event_service.update_event_direct(
                        self.user_data['user_id'],
                        self.event_data['event_id'],
                        event_data
                    )
                else:
                    # Обычный пользователь создает заявку
                    result = self.event_service.update_event_request(
                        self.user_data['user_id'],
                        self.event_data['event_id'],
                        event_data
                    )
            else:
                # Создание нового события
                if self.user_data.get('role_id', 1) >= 2:  # Модератор или админ
                    result = self.event_service.create_event_direct(
                        self.user_data['user_id'],
                        event_data
                    )
                else:
                    # Обычный пользователь создает заявку
                    result = self.event_service.create_event_request(
                        self.user_data['user_id'],
                        event_data
                    )
            
            if result.get('success'):
                if self.user_data.get('role_id', 1) >= 2:
                    message = "Событие успешно сохранено!"
                else:
                    message = "Заявка на создание/изменение события отправлена на модерацию"
                
                QMessageBox.information(self, "Успех", message)
                self.accept()
            else:
                error_msg = result.get('message', 'Неизвестная ошибка')
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить событие:\n{error_msg}")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении:\n{str(e)}")
        
        finally:
            # Разблокируем кнопку
            self.save_btn.setEnabled(True)
            self.save_btn.setText("Сохранить")
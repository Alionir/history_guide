from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLabel, QComboBox, QTextEdit, QLineEdit,
                             QDateEdit, QSpinBox, QGroupBox, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import date
from services import ModerationService
from core.exceptions import ValidationError

class CreateRequestDialog(QDialog):
    """Диалог для создания заявки на модерацию"""
    
    request_created = pyqtSignal()  # Сигнал о создании заявки
    
    def __init__(self, user_data, entity_type=None, operation_type=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.moderation_service = ModerationService()
        
        self.setWindowTitle("Создание заявки на модерацию")
        self.setMinimumSize(600, 700)
        self.resize(800, 800)
        
        # Предустановленные значения
        self.preset_entity_type = entity_type
        self.preset_operation_type = operation_type
        
        self.setup_ui()
        
        # Устанавливаем предустановленные значения
        if entity_type:
            index = self.entity_type_combo.findText(entity_type)
            if index >= 0:
                self.entity_type_combo.setCurrentIndex(index)
                self.on_entity_type_changed()
        
        if operation_type:
            index = self.operation_combo.findText(operation_type)
            if index >= 0:
                self.operation_combo.setCurrentIndex(index)
                self.on_operation_changed()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Создание заявки на модерацию")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Основные параметры заявки
        main_group = QGroupBox("Основные параметры")
        main_layout = QFormLayout(main_group)
        
        # Тип сущности
        self.entity_type_combo = QComboBox()
        self.entity_type_combo.addItems(['PERSON', 'COUNTRY', 'EVENT', 'DOCUMENT', 'SOURCE'])
        self.entity_type_combo.currentTextChanged.connect(self.on_entity_type_changed)
        main_layout.addRow("Тип сущности:", self.entity_type_combo)
        
        # Тип операции
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(['CREATE', 'UPDATE', 'DELETE'])
        self.operation_combo.currentTextChanged.connect(self.on_operation_changed)
        main_layout.addRow("Операция:", self.operation_combo)
        
        # ID существующей сущности (для UPDATE/DELETE)
        self.entity_id_spin = QSpinBox()
        self.entity_id_spin.setRange(1, 999999)
        self.entity_id_spin.setEnabled(False)
        self.entity_id_label = QLabel("ID сущности:")
        main_layout.addRow(self.entity_id_label, self.entity_id_spin)
        
        # Комментарий к заявке
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText("Комментарий к заявке (необязательно)")
        main_layout.addRow("Комментарий:", self.comment_edit)
        
        layout.addWidget(main_group)
        
        # Данные сущности
        self.data_group = QGroupBox("Данные")
        self.data_layout = QFormLayout(self.data_group)
        layout.addWidget(self.data_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.create_button = QPushButton("Создать заявку")
        self.create_button.clicked.connect(self.create_request)
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(self.create_button)
        
        layout.addLayout(buttons_layout)
        
        # Инициализируем форму
        self.on_entity_type_changed()
        self.on_operation_changed()
    
    def on_entity_type_changed(self):
        """Обработка смены типа сущности"""
        entity_type = self.entity_type_combo.currentText()
        
        # Очищаем предыдущие поля
        self.clear_data_fields()
        
        # Создаем поля в зависимости от типа сущности
        if entity_type == 'PERSON':
            self.create_person_fields()
        elif entity_type == 'COUNTRY':
            self.create_country_fields()
        elif entity_type == 'EVENT':
            self.create_event_fields()
        elif entity_type == 'DOCUMENT':
            self.create_document_fields()
        elif entity_type == 'SOURCE':
            self.create_source_fields()
    
    def on_operation_changed(self):
        """Обработка смены типа операции"""
        operation = self.operation_combo.currentText()
        
        # Показываем/скрываем поле ID для UPDATE/DELETE
        show_id = operation in ['UPDATE', 'DELETE']
        self.entity_id_label.setVisible(show_id)
        self.entity_id_spin.setVisible(show_id)
        self.entity_id_spin.setEnabled(show_id)
        
        # Обновляем подсказки
        if operation == 'CREATE':
            self.data_group.setTitle("Данные новой записи")
        elif operation == 'UPDATE':
            self.data_group.setTitle("Новые данные (будут заменены)")
        elif operation == 'DELETE':
            self.data_group.setTitle("Причина удаления")
            self.clear_data_fields()
            
            # Для удаления добавляем только поле причины
            self.reason_edit = QTextEdit()
            self.reason_edit.setMaximumHeight(100)
            self.reason_edit.setPlaceholderText("Укажите причину удаления")
            self.data_layout.addRow("Причина удаления:", self.reason_edit)
    
    def clear_data_fields(self):
        """Очистка полей данных"""
        while self.data_layout.count():
            child = self.data_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_person_fields(self):
        """Создание полей для персоны"""
        if self.operation_combo.currentText() == 'DELETE':
            return
        
        # Имя (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите имя")
        self.data_layout.addRow("Имя*:", self.name_edit)
        
        # Фамилия
        self.surname_edit = QLineEdit()
        self.surname_edit.setPlaceholderText("Введите фамилию")
        self.data_layout.addRow("Фамилия:", self.surname_edit)
        
        # Отчество
        self.patronymic_edit = QLineEdit()
        self.patronymic_edit.setPlaceholderText("Введите отчество")
        self.data_layout.addRow("Отчество:", self.patronymic_edit)
        
        # Дата рождения
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate(1900, 1, 1))
        self.birth_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата рождения:", self.birth_date_edit)
        
        # Дата смерти
        self.death_date_edit = QDateEdit()
        self.death_date_edit.setCalendarPopup(True)
        self.death_date_edit.setDate(QDate(1900, 1, 1))
        self.death_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата смерти:", self.death_date_edit)
        
        # Страна
        self.country_id_spin = QSpinBox()
        self.country_id_spin.setRange(0, 999999)
        self.country_id_spin.setSpecialValueText("Не указано")
        self.data_layout.addRow("ID страны:", self.country_id_spin)
        
        # Биография
        self.biography_edit = QTextEdit()
        self.biography_edit.setMaximumHeight(150)
        self.biography_edit.setPlaceholderText("Введите биографию")
        self.data_layout.addRow("Биография:", self.biography_edit)
    
    def create_country_fields(self):
        """Создание полей для страны"""
        if self.operation_combo.currentText() == 'DELETE':
            return
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название страны")
        self.data_layout.addRow("Название*:", self.name_edit)
        
        # Столица
        self.capital_edit = QLineEdit()
        self.capital_edit.setPlaceholderText("Введите столицу")
        self.data_layout.addRow("Столица:", self.capital_edit)
        
        # Дата основания
        self.foundation_date_edit = QDateEdit()
        self.foundation_date_edit.setCalendarPopup(True)
        self.foundation_date_edit.setDate(QDate(1, 1, 1))
        self.foundation_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата основания:", self.foundation_date_edit)
        
        # Дата роспуска
        self.dissolution_date_edit = QDateEdit()
        self.dissolution_date_edit.setCalendarPopup(True)
        self.dissolution_date_edit.setDate(QDate(1, 1, 1))
        self.dissolution_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата роспуска:", self.dissolution_date_edit)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(150)
        self.description_edit.setPlaceholderText("Введите описание страны")
        self.data_layout.addRow("Описание:", self.description_edit)
    
    def create_event_fields(self):
        """Создание полей для события"""
        if self.operation_combo.currentText() == 'DELETE':
            return
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название события")
        self.data_layout.addRow("Название*:", self.name_edit)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Введите описание события")
        self.data_layout.addRow("Описание:", self.description_edit)
        
        # Дата начала
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate(1, 1, 1))
        self.start_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата начала:", self.start_date_edit)
        
        # Дата окончания
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate(1, 1, 1))
        self.end_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата окончания:", self.end_date_edit)
        
        # Местоположение
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Введите местоположение")
        self.data_layout.addRow("Местоположение:", self.location_edit)
        
        # Тип события
        self.event_type_edit = QLineEdit()
        self.event_type_edit.setPlaceholderText("Введите тип события")
        self.data_layout.addRow("Тип события:", self.event_type_edit)
        
        # Родительское событие
        self.parent_id_spin = QSpinBox()
        self.parent_id_spin.setRange(0, 999999)
        self.parent_id_spin.setSpecialValueText("Не указано")
        self.data_layout.addRow("ID родительского события:", self.parent_id_spin)
    
    def create_document_fields(self):
        """Создание полей для документа"""
        if self.operation_combo.currentText() == 'DELETE':
            return
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название документа")
        self.data_layout.addRow("Название*:", self.name_edit)
        
        # Содержимое (обязательное)
        self.content_edit = QTextEdit()
        self.content_edit.setMinimumHeight(200)
        self.content_edit.setPlaceholderText("Введите содержимое документа")
        self.data_layout.addRow("Содержимое*:", self.content_edit)
        
        # Дата создания
        self.creating_date_edit = QDateEdit()
        self.creating_date_edit.setCalendarPopup(True)
        self.creating_date_edit.setDate(QDate(1, 1, 1))
        self.creating_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата создания:", self.creating_date_edit)
    
    def create_source_fields(self):
        """Создание полей для источника"""
        if self.operation_combo.currentText() == 'DELETE':
            return
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название источника")
        self.data_layout.addRow("Название*:", self.name_edit)
        
        # Автор
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Введите автора")
        self.data_layout.addRow("Автор:", self.author_edit)
        
        # Дата публикации
        self.publication_date_edit = QDateEdit()
        self.publication_date_edit.setCalendarPopup(True)
        self.publication_date_edit.setDate(QDate(1, 1, 1))
        self.publication_date_edit.setSpecialValueText("Не указано")
        self.data_layout.addRow("Дата публикации:", self.publication_date_edit)
        
        # Тип источника
        self.source_type_edit = QLineEdit()
        self.source_type_edit.setPlaceholderText("Введите тип источника")
        self.data_layout.addRow("Тип:", self.source_type_edit)
        
        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Введите URL источника")
        self.data_layout.addRow("URL:", self.url_edit)
    
    def create_request(self):
        """Создание заявки на модерацию"""
        try:
            entity_type = self.entity_type_combo.currentText()
            operation_type = self.operation_combo.currentText()
            comment = self.comment_edit.toPlainText().strip() or None
            
            # Собираем данные в зависимости от операции
            entity_id = None
            new_data = {}
            
            if operation_type in ['UPDATE', 'DELETE']:
                entity_id = self.entity_id_spin.value()
                if entity_id == 0:
                    QMessageBox.warning(self, "Ошибка", "Укажите ID существующей записи")
                    return
            
            if operation_type == 'DELETE':
                # Для удаления собираем только причину
                reason = getattr(self, 'reason_edit', None)
                if reason:
                    reason_text = reason.toPlainText().strip()
                    if not reason_text:
                        QMessageBox.warning(self, "Ошибка", "Укажите причину удаления")
                        return
                    new_data['reason'] = reason_text
            else:
                # Для CREATE/UPDATE собираем все данные
                new_data = self.collect_entity_data(entity_type)
                if not new_data:
                    return  # Ошибка уже показана в collect_entity_data
            
            # Создаем заявку
            result = self.moderation_service.create_moderation_request(
                user_id=self.user_data['user_id'],
                entity_type=entity_type,
                operation_type=operation_type,
                new_data=new_data,
                entity_id=entity_id,
                comment=comment
            )
            
            if result['success']:
                QMessageBox.information(
                    self, "Успех", 
                    f"Заявка #{result['request_id']} успешно создана"
                )
                self.request_created.emit()
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
                
        except ValidationError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заявку: {str(e)}")
    
    def collect_entity_data(self, entity_type):
        """Сбор данных сущности из формы"""
        try:
            data = {}
            
            # Общие поля
            if hasattr(self, 'name_edit'):
                name = self.name_edit.text().strip()
                if not name:
                    QMessageBox.warning(self, "Ошибка", "Название/Имя обязательно для заполнения")
                    return None
                data['name'] = name
            
            if entity_type == 'PERSON':
                # Поля персоны
                if hasattr(self, 'surname_edit'):
                    surname = self.surname_edit.text().strip()
                    data['surname'] = surname if surname else None
                
                if hasattr(self, 'patronymic_edit'):
                    patronymic = self.patronymic_edit.text().strip()
                    data['patronymic'] = patronymic if patronymic else None
                
                if hasattr(self, 'birth_date_edit'):
                    birth_date = self.birth_date_edit.date().toPython()
                    if birth_date != date(1900, 1, 1):
                        data['date_of_birth'] = birth_date.isoformat()
                
                if hasattr(self, 'death_date_edit'):
                    death_date = self.death_date_edit.date().toPython()
                    if death_date != date(1900, 1, 1):
                        data['date_of_death'] = death_date.isoformat()
                
                if hasattr(self, 'country_id_spin'):
                    country_id = self.country_id_spin.value()
                    data['country_id'] = country_id if country_id > 0 else None
                
                if hasattr(self, 'biography_edit'):
                    biography = self.biography_edit.toPlainText().strip()
                    data['biography'] = biography if biography else None
            
            elif entity_type == 'COUNTRY':
                # Поля страны
                if hasattr(self, 'capital_edit'):
                    capital = self.capital_edit.text().strip()
                    data['capital'] = capital if capital else None
                
                if hasattr(self, 'foundation_date_edit'):
                    foundation_date = self.foundation_date_edit.date().toPython()
                    if foundation_date != date(1, 1, 1):
                        data['foundation_date'] = foundation_date.isoformat()
                
                if hasattr(self, 'dissolution_date_edit'):
                    dissolution_date = self.dissolution_date_edit.date().toPython()
                    if dissolution_date != date(1, 1, 1):
                        data['dissolution_date'] = dissolution_date.isoformat()
                
                if hasattr(self, 'description_edit'):
                    description = self.description_edit.toPlainText().strip()
                    data['description'] = description if description else None
            
            elif entity_type == 'EVENT':
                # Поля события
                if hasattr(self, 'description_edit'):
                    description = self.description_edit.toPlainText().strip()
                    data['description'] = description if description else None
                
                if hasattr(self, 'start_date_edit'):
                    start_date = self.start_date_edit.date().toPython()
                    if start_date != date(1, 1, 1):
                        data['start_date'] = start_date.isoformat()
                
                if hasattr(self, 'end_date_edit'):
                    end_date = self.end_date_edit.date().toPython()
                    if end_date != date(1, 1, 1):
                        data['end_date'] = end_date.isoformat()
                
                if hasattr(self, 'location_edit'):
                    location = self.location_edit.text().strip()
                    data['location'] = location if location else None
                
                if hasattr(self, 'event_type_edit'):
                    event_type = self.event_type_edit.text().strip()
                    data['event_type'] = event_type if event_type else None
                
                if hasattr(self, 'parent_id_spin'):
                    parent_id = self.parent_id_spin.value()
                    data['parent_id'] = parent_id if parent_id > 0 else None
            
            elif entity_type == 'DOCUMENT':
                # Поля документа
                if hasattr(self, 'content_edit'):
                    content = self.content_edit.toPlainText().strip()
                    if not content:
                        QMessageBox.warning(self, "Ошибка", "Содержимое документа обязательно")
                        return None
                    data['content'] = content
                
                if hasattr(self, 'creating_date_edit'):
                    creating_date = self.creating_date_edit.date().toPython()
                    if creating_date != date(1, 1, 1):
                        data['creating_date'] = creating_date.isoformat()
            
            elif entity_type == 'SOURCE':
                # Поля источника
                if hasattr(self, 'author_edit'):
                    author = self.author_edit.text().strip()
                    data['author'] = author if author else None
                
                if hasattr(self, 'publication_date_edit'):
                    publication_date = self.publication_date_edit.date().toPython()
                    if publication_date != date(1, 1, 1):
                        data['publication_date'] = publication_date.isoformat()
                
                if hasattr(self, 'source_type_edit'):
                    source_type = self.source_type_edit.text().strip()
                    data['type'] = source_type if source_type else None
                
                if hasattr(self, 'url_edit'):
                    url = self.url_edit.text().strip()
                    data['url'] = url if url else None
            
            return data
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сборе данных: {str(e)}")
            return None
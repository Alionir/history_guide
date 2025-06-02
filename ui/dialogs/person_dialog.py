from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from services.person_service import PersonService
from services.country_service import CountryService

class PersonDialog(QDialog):
    def __init__(self, user_data, person_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.person_data = person_data
        self.person_service = PersonService()
        self.country_service = CountryService()
        self.setup_ui()
        self.load_countries()
        
        if person_data:
            self.populate_form()
    
    def setup_ui(self):
        self.setWindowTitle("Добавить персону" if not self.person_data else "Редактировать персону")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Основная информация
        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout(main_group)
        
        # Имя (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Обязательное поле")
        main_layout.addRow("Имя:", self.name_edit)
        
        # Фамилия
        self.surname_edit = QLineEdit()
        main_layout.addRow("Фамилия:", self.surname_edit)
        
        # Отчество
        self.patronymic_edit = QLineEdit()
        main_layout.addRow("Отчество:", self.patronymic_edit)
        
        # Страна
        self.country_combo = QComboBox()
        self.country_combo.addItem("Не указана", None)
        main_layout.addRow("Страна:", self.country_combo)
        
        layout.addWidget(main_group)
        
        # Даты
        dates_group = QGroupBox("Даты жизни")
        dates_layout = QFormLayout(dates_group)
        
        # Дата рождения
        birth_layout = QHBoxLayout()
        self.birth_checkbox = QCheckBox("Указать")
        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDate(QDate(1900, 1, 1))
        self.birth_date.setEnabled(False)
        self.birth_checkbox.toggled.connect(self.birth_date.setEnabled)
        birth_layout.addWidget(self.birth_checkbox)
        birth_layout.addWidget(self.birth_date)
        dates_layout.addRow("Дата рождения:", birth_layout)
        
        # Дата смерти
        death_layout = QHBoxLayout()
        self.death_checkbox = QCheckBox("Указать")
        self.death_date = QDateEdit()
        self.death_date.setCalendarPopup(True)
        self.death_date.setDate(QDate.currentDate())
        self.death_date.setEnabled(False)
        self.death_checkbox.toggled.connect(self.death_date.setEnabled)
        death_layout.addWidget(self.death_checkbox)
        death_layout.addWidget(self.death_date)
        dates_layout.addRow("Дата смерти:", death_layout)
        
        layout.addWidget(dates_group)
        
        # Биография
        bio_group = QGroupBox("Биография")
        bio_layout = QVBoxLayout(bio_group)
        
        self.biography_edit = QTextEdit()
        self.biography_edit.setPlaceholderText("Биографическая информация...")
        self.biography_edit.setMaximumHeight(150)
        bio_layout.addWidget(self.biography_edit)
        
        # Счетчик символов
        self.char_count_label = QLabel("0 / 10000 символов")
        self.biography_edit.textChanged.connect(self.update_char_count)
        bio_layout.addWidget(self.char_count_label)
        
        layout.addWidget(bio_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_person)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_countries(self):
        """Загрузка списка стран"""
        try:
            countries = self.country_service.get_countries(
                self.user_data['user_id'], 
                {'limit': 1000}
            )
            
            for country in countries['countries']:
                self.country_combo.addItem(country['name'], country['country_id'])
        except Exception as e:
            print(f"Ошибка загрузки стран: {e}")
    
    def populate_form(self):
        """Заполнение формы данными персоны"""
        if not self.person_data:
            return
        
        self.name_edit.setText(self.person_data.get('name', ''))
        self.surname_edit.setText(self.person_data.get('surname', '') or '')
        self.patronymic_edit.setText(self.person_data.get('patronymic', '') or '')
        self.biography_edit.setPlainText(self.person_data.get('biography', '') or '')
        
        # Страна
        country_id = self.person_data.get('country_id')
        if country_id:
            index = self.country_combo.findData(country_id)
            if index >= 0:
                self.country_combo.setCurrentIndex(index)
        
        # Даты
        if self.person_data.get('date_of_birth'):
            self.birth_checkbox.setChecked(True)
            birth_date = QDate.fromString(str(self.person_data['date_of_birth']), "yyyy-MM-dd")
            self.birth_date.setDate(birth_date)
        
        if self.person_data.get('date_of_death'):
            self.death_checkbox.setChecked(True)
            death_date = QDate.fromString(str(self.person_data['date_of_death']), "yyyy-MM-dd")
            self.death_date.setDate(death_date)
    
    def update_char_count(self):
        """Обновление счетчика символов биографии"""
        text = self.biography_edit.toPlainText()
        count = len(text)
        self.char_count_label.setText(f"{count} / 10000 символов")
        
        if count > 10000:
            self.char_count_label.setStyleSheet("color: red;")
        else:
            self.char_count_label.setStyleSheet("")
    
    def save_person(self):
        """Сохранение персоны"""
        # Валидация
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Имя обязательно для заполнения")
            return
        
        if len(self.biography_edit.toPlainText()) > 10000:
            QMessageBox.warning(self, "Ошибка", "Биография не может содержать более 10000 символов")
            return
        
        # Подготовка данных
        person_data = {
            'name': self.name_edit.text().strip(),
            'surname': self.surname_edit.text().strip() or None,
            'patronymic': self.patronymic_edit.text().strip() or None,
            'biography': self.biography_edit.toPlainText().strip() or None,
            'country_id': self.country_combo.currentData()
        }
        
        # Даты
        if self.birth_checkbox.isChecked():
            person_data['date_of_birth'] = self.birth_date.date()
        
        if self.death_checkbox.isChecked():
            person_data['date_of_death'] = self.death_date.date()
        
        try:
            if self.person_data:  # Редактирование
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.person_service.update_person_direct(
                        self.user_data['user_id'],
                        self.person_data['person_id'],
                        person_data
                    )
                else:  # Обычный пользователь - создаем заявку
                    result = self.person_service.update_person_request(
                        self.user_data['user_id'],
                        self.person_data['person_id'],
                        person_data
                    )
            else:  # Создание
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.person_service.create_person_direct(
                        self.user_data['user_id'],
                        person_data
                    )
                else:  # Обычный пользователь
                    result = self.person_service.create_person_request(
                        self.user_data['user_id'],
                        person_data
                    )
            
            if result.get('success'):
                if self.user_data['role_id'] >= 2:
                    QMessageBox.information(self, "Успех", "Источник сохранен")
                else:
                    QMessageBox.information(self, "Успех", "Заявка отправлена на модерацию")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
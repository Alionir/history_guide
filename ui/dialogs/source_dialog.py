from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class SourceDialog(QDialog):
    def __init__(self, user_data, source_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.source_data = source_data
        from services.source_service import SourceService
        self.source_service = SourceService()
        self.setup_ui()
        
        if source_data:
            self.populate_form()
    
    def setup_ui(self):
        self.setWindowTitle("Добавить источник" if not self.source_data else "Редактировать источник")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Основная информация
        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout(main_group)
        
        # Название (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Обязательное поле (мин. 3 символа)")
        main_layout.addRow("Название:", self.name_edit)
        
        # Автор
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Имя автора или организации")
        main_layout.addRow("Автор:", self.author_edit)
        
        # Тип источника
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("Книга, статья, веб-сайт...")
        main_layout.addRow("Тип:", self.type_edit)
        
        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        main_layout.addRow("URL:", self.url_edit)
        
        # Дата публикации
        date_layout = QHBoxLayout()
        self.date_checkbox = QCheckBox("Указать")
        self.publication_date = QDateEdit()
        self.publication_date.setCalendarPopup(True)
        self.publication_date.setDate(QDate.currentDate())
        self.publication_date.setEnabled(False)
        self.date_checkbox.toggled.connect(self.publication_date.setEnabled)
        date_layout.addWidget(self.date_checkbox)
        date_layout.addWidget(self.publication_date)
        main_layout.addRow("Дата публикации:", date_layout)
        
        layout.addWidget(main_group)
        
        # Информационная панель для обычных пользователей
        if self.user_data['role_id'] < 2:
            info_label = QLabel("Ваши изменения будут отправлены на модерацию")
            info_label.setStyleSheet("color: #0066cc; font-style: italic; padding: 5px;")
            layout.addWidget(info_label)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_source)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def populate_form(self):
        """Заполнение формы данными источника"""
        if not self.source_data:
            return
        
        self.name_edit.setText(self.source_data.get('name', ''))
        self.author_edit.setText(self.source_data.get('author', '') or '')
        self.type_edit.setText(self.source_data.get('type', '') or '')
        self.url_edit.setText(self.source_data.get('url', '') or '')
        
        # Дата публикации
        if self.source_data.get('publication_date'):
            self.date_checkbox.setChecked(True)
            pub_date = QDate.fromString(str(self.source_data['publication_date']), "yyyy-MM-dd")
            self.publication_date.setDate(pub_date)
    
    def save_source(self):
        """Сохранение источника"""
        # Валидация
        name = self.name_edit.text().strip()
        if not name or len(name) < 3:
            QMessageBox.warning(self, "Ошибка", "Название должно содержать минимум 3 символа")
            return
        
        # Проверка URL если указан
        url = self.url_edit.text().strip()
        if url and not self.is_valid_url(url):
            reply = QMessageBox.question(
                self, 
                "Некорректный URL", 
                "URL имеет некорректный формат. Продолжить сохранение?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Подготовка данных
        source_data = {
            'name': name,
            'author': self.author_edit.text().strip() or None,
            'source_type': self.type_edit.text().strip() or None,
            'url': url or None
        }
        
        if self.date_checkbox.isChecked():
            source_data['publication_date'] = self.publication_date.date()
        
        try:
            if self.source_data:  # Редактирование
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.source_service.update_source_direct(
                        self.user_data['user_id'],
                        self.source_data['source_id'],
                        source_data
                    )
                else:  # Заявка
                    result = self.source_service.update_source_request(
                        self.user_data['user_id'],
                        self.source_data['source_id'],
                        source_data
                    )
            else:  # Создание
                if self.user_data['role_id'] >= 2:  # Модератор
                    result = self.source_service.create_source_direct(
                        self.user_data['user_id'],
                        source_data
                    )
                else:  # Заявка
                    result = self.source_service.create_source_request(
                        self.user_data['user_id'],
                        source_data
                    )
            
            if result.get('success'):
                if self.user_data['role_id'] >= 2:
                    QMessageBox.information(
                        self, 
                        "Успех", 
                        "Источник успешно сохранен!"
                    )
                else:
                    QMessageBox.information(
                        self, 
                        "Заявка создана", 
                        "Ваша заявка отправлена на модерацию.\nОна будет рассмотрена в ближайшее время."
                    )
                self.accept()
            else:
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    result.get('message', 'Неизвестная ошибка при сохранении')
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла ошибка при сохранении:\n{str(e)}"
            )
    
    def is_valid_url(self, url):
        """Простая проверка корректности URL"""
        import re
        
        # Добавляем протокол если отсутствует
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'http://' + url
        
        # Простая проверка формата URL
        url_pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*'
        return re.match(url_pattern, url) is not None
    
    def get_source_data(self):
        """Получение данных источника из формы"""
        return {
            'name': self.name_edit.text().strip(),
            'author': self.author_edit.text().strip() or None,
            'type': self.type_edit.text().strip() or None,
            'url': self.url_edit.text().strip() or None,
            'publication_date': self.publication_date.date() if self.date_checkbox.isChecked() else None
        }


class SourceSelectionDialog(QDialog):
    """Диалог для выбора источника из списка"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.selected_source = None
        from services.source_service import SourceService
        self.source_service = SourceService()
        self.setup_ui()
        self.load_sources()
    
    def setup_ui(self):
        self.setWindowTitle("Выбор источника")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Название источника или автор...")
        self.search_edit.textChanged.connect(self.filter_sources)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Список источников
        self.sources_list = QListWidget()
        self.sources_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.sources_list)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("Выбрать")
        self.select_btn.clicked.connect(self.accept_selection)
        self.select_btn.setEnabled(False)
        buttons_layout.addWidget(self.select_btn)
        
        self.new_btn = QPushButton("Создать новый")
        self.new_btn.clicked.connect(self.create_new_source)
        buttons_layout.addWidget(self.new_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Соединения
        self.sources_list.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_sources(self):
        """Загрузка списка источников"""
        try:
            result = self.source_service.get_sources(self.user_data['user_id'], {'limit': 100})
            sources = result.get('sources', [])
            
            self.sources_list.clear()
            self.all_sources = sources
            
            for source in sources:
                item = QListWidgetItem()
                item.setText(f"{source['name']} - {source.get('author', 'Автор не указан')}")
                item.setData(Qt.ItemDataRole.UserRole, source)
                self.sources_list.addItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить источники:\n{str(e)}")
    
    def filter_sources(self):
        """Фильтрация источников по поисковому запросу"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.sources_list.count()):
            item = self.sources_list.item(i)
            source = item.data(Qt.ItemDataRole.UserRole)
            
            # Поиск в названии и авторе
            name_match = search_text in source['name'].lower()
            author_match = search_text in (source.get('author', '') or '').lower()
            
            item.setHidden(not (name_match or author_match))
    
    def on_selection_changed(self):
        """Обработка изменения выбора"""
        self.select_btn.setEnabled(len(self.sources_list.selectedItems()) > 0)
    
    def accept_selection(self):
        """Принятие выбранного источника"""
        selected_items = self.sources_list.selectedItems()
        if selected_items:
            self.selected_source = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.accept()
    
    def create_new_source(self):
        """Создание нового источника"""
        dialog = SourceDialog(self.user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_sources()  # Перезагружаем список
    
    def get_selected_source(self):
        """Получение выбранного источника"""
        return self.selected_source
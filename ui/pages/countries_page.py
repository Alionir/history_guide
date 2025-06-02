# ui/pages/countries_page.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.country_service import CountryService
from ui.pages.base_page import BasePage
from ui.dialogs.country_dialog import CountryDialog

class CountriesPage(BasePage):
    def __init__(self, user_data):
        self.country_service = CountryService()
        super().__init__(user_data)
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок и кнопки
        header_layout = QHBoxLayout()
        
        title = QLabel("Страны")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Кнопка добавления
        self.add_btn = QPushButton("Добавить страну")
        self.add_btn.clicked.connect(self.add_country)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Панель фильтров
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout(filters_group)
        
        # Поиск по названию
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию...")
        self.search_edit.textChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Поиск:"), 0, 0)
        filters_layout.addWidget(self.search_edit, 0, 1)
        
        # Фильтр по статусу
        self.status_combo = QComboBox()
        self.status_combo.addItem("Все страны", None)
        self.status_combo.addItem("Существующие", "existing")
        self.status_combo.addItem("Исторические", "historical")
        self.status_combo.currentTextChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Статус:"), 0, 2)
        filters_layout.addWidget(self.status_combo, 0, 3)
        
        # Фильтры по годам основания
        self.foundation_year_from = QSpinBox()
        self.foundation_year_from.setRange(1, 2100)
        self.foundation_year_from.setValue(1)
        self.foundation_year_from.valueChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Основана с:"), 1, 0)
        filters_layout.addWidget(self.foundation_year_from, 1, 1)
        
        self.foundation_year_to = QSpinBox()
        self.foundation_year_to.setRange(1, 2100)
        self.foundation_year_to.setValue(2024)
        self.foundation_year_to.valueChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("по:"), 1, 2)
        filters_layout.addWidget(self.foundation_year_to, 1, 3)
        
        # Кнопка сброса фильтров
        reset_btn = QPushButton("Сбросить фильтры")
        reset_btn.clicked.connect(self.reset_filters)
        filters_layout.addWidget(reset_btn, 2, 0)
        
        layout.addWidget(filters_group)
        
        # Таблица стран
        self.countries_table = QTreeWidget()
        self.countries_table.setHeaderLabels([
            "ID", "Название", "Столица", "Основана", "Распущена", "Статус"
        ])
        self.countries_table.itemDoubleClicked.connect(self.view_country_details)
        
        # Настройка колонок
        header = self.countries_table.header()
        header.resizeSection(0, 50)   # ID
        header.resizeSection(1, 200)  # Название
        header.resizeSection(2, 150)  # Столица
        header.resizeSection(3, 100)  # Основана
        header.resizeSection(4, 100)  # Распущена
        header.resizeSection(5, 120)  # Статус
        
        # Контекстное меню
        self.countries_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.countries_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.countries_table)
        
        # Пагинация
        pagination_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Предыдущая")
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("Страница 1")
        pagination_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Следующая →")
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)
        
        pagination_layout.addStretch()
        
        self.total_label = QLabel("Всего: 0")
        pagination_layout.addWidget(self.total_label)
        
        layout.addLayout(pagination_layout)
        
        # Переменные пагинации
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0
    
    def load_data(self):
        """Загрузка данных о странах"""
        try:
            filters = {
                'offset': self.current_page * self.page_size,
                'limit': self.page_size,
                'search_term': self.search_edit.text() if hasattr(self, 'search_edit') and self.search_edit.text() else None
            }
            
            # Применяем фильтр по статусу
            if hasattr(self, 'status_combo') and self.status_combo.currentData():
                if self.status_combo.currentData() == "existing":
                    filters['existing_only'] = True
                elif self.status_combo.currentData() == "historical":
                    filters['historical_only'] = True
            
            # Применяем фильтры по годам
            if hasattr(self, 'foundation_year_from'):
                filters['foundation_year_from'] = self.foundation_year_from.value()
                filters['foundation_year_to'] = self.foundation_year_to.value()
            
            result = self.country_service.get_countries(self.user_data['user_id'], filters)
            
            self.countries_table.clear()
            self.total_count = result['total_count']
            
            for country in result['countries']:
                # Форматируем даты
                foundation_year = ""
                if country.get('foundation_date'):
                    foundation_year = str(country['foundation_date']).split('-')[0]
                
                dissolution_year = ""
                if country.get('dissolution_date'):
                    dissolution_year = str(country['dissolution_date']).split('-')[0]
                
                # Определяем статус
                status = "Существует"
                if country.get('dissolution_date'):
                    status = "Историческое"
                
                item = QTreeWidgetItem([
                    str(country['country_id']),
                    country['name'],
                    country.get('capital', ''),
                    foundation_year,
                    dissolution_year,
                    status
                ])
                
                # Окрашиваем строки в зависимости от статуса
                if status == "Историческое":
                    for col in range(item.columnCount()):
                        item.setForeground(col, QColor(128, 128, 128))  # Серый цвет
                
                item.setData(0, Qt.ItemDataRole.UserRole, country)
                self.countries_table.addTopLevelItem(item)
            
            # Обновляем пагинацию
            self.update_pagination()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def update_pagination(self):
        """Обновление элементов пагинации"""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        current_page_num = self.current_page + 1
        
        self.page_label.setText(f"Страница {current_page_num} из {total_pages}")
        self.total_label.setText(f"Всего: {self.total_count}")
        
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(current_page_num < total_pages)
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_data()
    
    def next_page(self):
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page + 1 < total_pages:
            self.current_page += 1
            self.load_data()
    
    def filter_data(self):
        """Применение фильтров"""
        self.current_page = 0  # Сброс на первую страницу
        self.load_data()
    
    def reset_filters(self):
        """Сброс всех фильтров"""
        self.search_edit.clear()
        self.status_combo.setCurrentIndex(0)
        self.foundation_year_from.setValue(1)
        self.foundation_year_to.setValue(2024)
        self.filter_data()
    
    def add_country(self):
        """Добавление новой страны"""
        dialog = CountryDialog(self.user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()  # Обновляем список
    
    def view_country_details(self, item):
        """Просмотр деталей страны"""
        country_data = item.data(0, Qt.ItemDataRole.UserRole)
        if country_data:
            from ui.windows.country_details_window import CountryDetailsWindow
            details_window = CountryDetailsWindow(country_data, self.user_data, self)
            details_window.show()
    
    def show_context_menu(self, position):
        """Показ контекстного меню"""
        item = self.countries_table.itemAt(position)
        if item:
            menu = QMenu(self)
            
            view_action = menu.addAction("Просмотр")
            view_action.triggered.connect(lambda: self.view_country_details(item))
            
            if self.user_data['role_id'] >= 2:  # Модератор или админ
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self.edit_country(item))
                
                menu.addSeparator()
                
                # Дополнительные действия
                timeline_action = menu.addAction("Временная линия")
                timeline_action.triggered.connect(lambda: self.show_country_timeline(item))
            
            menu.exec(self.countries_table.mapToGlobal(position))
    
    def edit_country(self, item):
        """Редактирование страны"""
        country_data = item.data(0, Qt.ItemDataRole.UserRole)
        if country_data:
            dialog = CountryDialog(self.user_data, country_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def show_country_timeline(self, item):
        """Показ временной линии страны"""
        country_data = item.data(0, Qt.ItemDataRole.UserRole)
        if country_data:
            try:
                # Получаем временную линию стран
                timeline = self.country_service.get_countries_timeline(
                    self.user_data['user_id']
                )
                
                # Создаем простое окно с временной линией
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Временная линия: {country_data['name']}")
                dialog.resize(600, 400)
                
                layout = QVBoxLayout(dialog)
                
                text_widget = QTextEdit()
                text_widget.setReadOnly(True)
                
                # Формируем HTML контент
                html_content = f"<h2>Временная линия: {country_data['name']}</h2>"
                
                for event in timeline:
                    if event['country_id'] == country_data['country_id']:
                        year = ""
                        if event.get('foundation_date'):
                            year = str(event['foundation_date']).split('-')[0]
                        
                        html_content += f"""
                        <div style='margin: 10px 0; padding: 10px; border-left: 3px solid #007acc;'>
                            <b style='color: #007acc;'>{year}</b> - 
                            <b>Основание: {event['name']}</b><br>
                            <i>Столица: {event.get('capital', 'Не указана')}</i>
                        </div>
                        """
                
                text_widget.setHtml(html_content)
                layout.addWidget(text_widget)
                
                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.exec()
                
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить временную линию: {str(e)}")
    
    def refresh(self):
        """Обновление данных"""
        self.load_data()
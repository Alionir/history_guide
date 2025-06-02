# ui/pages/persons_page.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.person_service import PersonService
from ui.pages.base_page import BasePage
from ui.dialogs.person_dialog import PersonDialog

class PersonsPage(BasePage):
    def __init__(self, user_data):
        self.person_service = PersonService()
        super().__init__(user_data)
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок и кнопки
        header_layout = QHBoxLayout()
        
        title = QLabel("Персоны")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Кнопка добавления
        self.add_btn = QPushButton("Добавить персону")
        self.add_btn.clicked.connect(self.add_person)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Панель фильтров
        filters_group = QGroupBox("Фильтры")
        filters_layout = QHBoxLayout(filters_group)
        
        # Поиск по имени
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по имени...")
        self.search_edit.textChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Поиск:"))
        filters_layout.addWidget(self.search_edit)
        
        # Фильтр по стране
        self.country_combo = QComboBox()
        self.country_combo.addItem("Все страны", None)
        self.country_combo.currentTextChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Страна:"))
        filters_layout.addWidget(self.country_combo)
        
        # Фильтр только живые
        self.alive_checkbox = QCheckBox("Только живые")
        self.alive_checkbox.toggled.connect(self.filter_data)
        filters_layout.addWidget(self.alive_checkbox)
        
        filters_layout.addStretch()
        
        layout.addWidget(filters_group)
        
        # Таблица персон
        self.persons_table = QTreeWidget()
        self.persons_table.setHeaderLabels([
            "ID", "Имя", "Фамилия", "Отчество", "Годы жизни", "Страна"
        ])
        self.persons_table.itemDoubleClicked.connect(self.view_person_details)
        
        # Контекстное меню
        self.persons_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.persons_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.persons_table)
        
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
        """Загрузка данных о персонах"""
        try:
            filters = {
                'offset': self.current_page * self.page_size,
                'limit': self.page_size,
                'search_term': self.search_edit.text() if hasattr(self, 'search_edit') else None,
                'alive_only': self.alive_checkbox.isChecked() if hasattr(self, 'alive_checkbox') else False
            }
            
            if hasattr(self, 'country_combo') and self.country_combo.currentData():
                filters['country_id'] = self.country_combo.currentData()
            
            result = self.person_service.get_persons(self.user_data['user_id'], filters)
            
            self.persons_table.clear()
            self.total_count = result['total_count']
            
            for person in result['persons']:
                item = QTreeWidgetItem([
                    str(person['person_id']),
                    person['name'] or '',
                    person['surname'] or '',
                    person['patronymic'] or '',
                    person.get('life_years', '?'),
                    person.get('country_name', '')
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, person)
                self.persons_table.addTopLevelItem(item)
            
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
    
    def add_person(self):
        """Добавление новой персоны"""
        dialog = PersonDialog(self.user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()  # Обновляем список
    
    def view_person_details(self, item):
        """Просмотр деталей персоны"""
        person_data = item.data(0, Qt.ItemDataRole.UserRole)
        if person_data:
            from ui.windows.person_details_window import PersonDetailsWindow
            details_window = PersonDetailsWindow(person_data, self.user_data, self)
            details_window.show()
    
    def show_context_menu(self, position):
        """Показ контекстного меню"""
        item = self.persons_table.itemAt(position)
        if item:
            menu = QMenu(self)
            
            view_action = menu.addAction("Просмотр")
            view_action.triggered.connect(lambda: self.view_person_details(item))
            
            if self.user_data['role_id'] >= 2:  # Модератор или админ
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self.edit_person(item))
            
            menu.exec(self.persons_table.mapToGlobal(position))
    
    def edit_person(self, item):
        """Редактирование персоны"""
        person_data = item.data(0, Qt.ItemDataRole.UserRole)
        if person_data:
            dialog = PersonDialog(self.user_data, person_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def refresh(self):
        """Обновление данных"""
        self.load_data()
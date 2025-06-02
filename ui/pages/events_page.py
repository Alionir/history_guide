from ui.pages.base_page import *
from services.event_service import EventService

class EventsPage(BasePage):
    def __init__(self, user_data):
        self.event_service = EventService()
        super().__init__(user_data)
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок и кнопки
        header_layout = QHBoxLayout()
        
        title = QLabel("События")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Переключатель представления
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Список", "Иерархия", "Временная линия"])
        self.view_combo.currentTextChanged.connect(self.change_view)
        header_layout.addWidget(QLabel("Вид:"))
        header_layout.addWidget(self.view_combo)
        
        # Кнопка добавления
        self.add_btn = QPushButton("Добавить событие")
        self.add_btn.clicked.connect(self.add_event)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Панель фильтров
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout(filters_group)
        
        # Поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию...")
        self.search_edit.textChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Поиск:"), 0, 0)
        filters_layout.addWidget(self.search_edit, 0, 1)
        
        # Тип события
        self.type_combo = QComboBox()
        self.type_combo.addItem("Все типы", None)
        self.type_combo.currentTextChanged.connect(self.filter_data)
        filters_layout.addWidget(QLabel("Тип:"), 0, 2)
        filters_layout.addWidget(self.type_combo, 0, 3)
        
        layout.addWidget(filters_group)
        
        # Стек виджетов для разных представлений
        self.view_stack = QStackedWidget()
        
        # Список событий
        self.events_table = QTreeWidget()
        self.events_table.setHeaderLabels([
            "ID", "Название", "Тип", "Дата начала", "Дата окончания", "Место"
        ])
        self.events_table.itemDoubleClicked.connect(self.view_event_details)
        self.events_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.events_table.customContextMenuRequested.connect(self.show_context_menu)
        self.view_stack.addWidget(self.events_table)
        
        # Иерархическое представление
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabels(["Название", "Тип", "Период"])
        self.hierarchy_tree.itemDoubleClicked.connect(self.view_event_details)
        self.view_stack.addWidget(self.hierarchy_tree)
        
        # Временная линия (упрощенная)
        self.timeline_widget = QTextEdit()
        self.timeline_widget.setReadOnly(True)
        self.view_stack.addWidget(self.timeline_widget)
        
        layout.addWidget(self.view_stack)
        
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
        
        # Переменные
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0
        self.current_view = "Список"
    
    def load_data(self):
        """Загрузка данных о событиях"""
        try:
            if self.current_view == "Список":
                self.load_events_list()
            elif self.current_view == "Иерархия":
                self.load_events_hierarchy()
            elif self.current_view == "Временная линия":
                self.load_events_timeline()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def load_events_list(self):
        """Загрузка списка событий"""
        filters = {
            'offset': self.current_page * self.page_size,
            'limit': self.page_size,
            'search_term': self.search_edit.text() if self.search_edit.text() else None
        }
        
        if self.type_combo.currentData():
            filters['event_type'] = self.type_combo.currentData()
        
        result = self.event_service.get_events(self.user_data['user_id'], filters)
        
        self.events_table.clear()
        self.total_count = result['total_count']
        
        for event in result['events']:
            item = QTreeWidgetItem([
                str(event['event_id']),
                event['name'],
                event.get('event_type', ''),
                str(event.get('start_date', '')),
                str(event.get('end_date', '')),
                event.get('location', '')
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, event)
            self.events_table.addTopLevelItem(item)
        
        self.update_pagination()
    
    def load_events_hierarchy(self):
        """Загрузка иерархии событий"""
        try:
            hierarchy = self.event_service.get_events_hierarchy(self.user_data['user_id'])
            
            self.hierarchy_tree.clear()
            
            def add_hierarchy_items(items, parent=None):
                for item_data in items:
                    if parent is None:
                        item = QTreeWidgetItem(self.hierarchy_tree)
                    else:
                        item = QTreeWidgetItem(parent)
                    
                    item.setText(0, item_data['name'])
                    item.setText(1, item_data.get('event_type', ''))
                    item.setText(2, item_data.get('period_text', ''))
                    item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                    
                    if 'children' in item_data:
                        add_hierarchy_items(item_data['children'], item)
            
            add_hierarchy_items(hierarchy)
            self.hierarchy_tree.expandAll()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить иерархию: {str(e)}")
    
    def load_events_timeline(self):
        """Загрузка временной линии"""
        try:
            # Для временной линии не используем фильтрацию по годам
            timeline_events = self.event_service.get_events_timeline(
                self.user_data['user_id'],
                limit=100
            )
            
            timeline_html = "<h3>Временная линия событий</h3>"
            
            for event in timeline_events:
                start_year = event.get('start_date', '').split('-')[0] if event.get('start_date') else '?'
                timeline_html += f"""
                <div style='margin: 10px 0; padding: 10px; border-left: 3px solid #007acc;'>
                    <b style='color: #007acc;'>{start_year}</b> - 
                    <b>{event['name']}</b><br>
                    <i>{event.get('description', 'Описание отсутствует')[:100]}...</i>
                </div>
                """
            
            self.timeline_widget.setHtml(timeline_html)
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить временную линию: {str(e)}")
    
    def change_view(self, view_name):
        """Изменение представления"""
        self.current_view = view_name
        
        if view_name == "Список":
            self.view_stack.setCurrentWidget(self.events_table)
        elif view_name == "Иерархия":
            self.view_stack.setCurrentWidget(self.hierarchy_tree)
        elif view_name == "Временная линия":
            self.view_stack.setCurrentWidget(self.timeline_widget)
        
        self.load_data()
    
    def filter_data(self):
        """Применение фильтров"""
        self.current_page = 0
        self.load_data()
    
    def add_event(self):
        """Добавление нового события"""
        from ui.dialogs.event_dialog import EventDialog
        dialog = EventDialog(self.user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
    
    def view_event_details(self, item):
        """Просмотр деталей события"""
        event_data = item.data(0, Qt.ItemDataRole.UserRole)
        if event_data:
            from ui.windows.event_details_window import EventDetailsWindow
            details_window = EventDetailsWindow(event_data, self.user_data, self)
            details_window.show()
    
    def show_context_menu(self, position):
        """Показ контекстного меню"""
        widget = self.view_stack.currentWidget()
        item = widget.itemAt(position)
        if item:
            menu = QMenu(self)
            
            view_action = menu.addAction("Просмотр")
            view_action.triggered.connect(lambda: self.view_event_details(item))
            
            if self.user_data['role_id'] >= 2:
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self.edit_event(item))
            
            menu.exec(widget.mapToGlobal(position))
    
    def edit_event(self, item):
        """Редактирование события"""
        event_data = item.data(0, Qt.ItemDataRole.UserRole)
        if event_data:
            from ui.dialogs.event_dialog import EventDialog
            dialog = EventDialog(self.user_data, event_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def update_pagination(self):
        """Обновление пагинации"""
        if self.current_view == "Список":
            total_pages = (self.total_count + self.page_size - 1) // self.page_size
            current_page_num = self.current_page + 1
            
            self.page_label.setText(f"Страница {current_page_num} из {total_pages}")
            self.total_label.setText(f"Всего: {self.total_count}")
            
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(current_page_num < total_pages)
        else:
            # Скрываем пагинацию для других представлений
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.page_label.setText("")
            self.total_label.setText("")
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_data()
    
    def next_page(self):
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page + 1 < total_pages:
            self.current_page += 1
            self.load_data()
    
    def refresh(self):
        self.load_data()
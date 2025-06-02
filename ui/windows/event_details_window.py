# ui/windows/event_details_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class EventDetailsWindow(QMainWindow):
    def __init__(self, event_data, user_data, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.user_data = user_data
        self.full_event_data = None
        
        from services.event_service import EventService
        from services.relationship_service import RelationshipService
        
        self.event_service = EventService()
        self.relationship_service = RelationshipService()
        
        self.setup_ui()
        self.load_full_data()
    
    def setup_ui(self):
        self.setWindowTitle(f"Событие: {self.event_data['name']}")
        self.resize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title = QLabel(self.event_data['name'])
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title.setWordWrap(True)
        main_layout.addWidget(title)
        
        # Горизонтальный layout для основного содержимого
        content_layout = QHBoxLayout()
        
        # Левая панель
        left_panel = self.create_main_info_panel()
        content_layout.addWidget(left_panel, 2)
        
        # Правая панель
        right_panel = self.create_connections_panel()
        content_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(content_layout)
        
        self.create_menus()
        self.create_toolbar()
    
    def create_main_info_panel(self):
        """Создание основной информационной панели"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Создаем область с прокруткой
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Основная информация
        info_group = QGroupBox("Основная информация")
        info_layout = QFormLayout(info_group)
        
        # Название
        name_label = QLabel(self.event_data.get('name', 'Не указано'))
        name_label.setWordWrap(True)
        info_layout.addRow("Название:", name_label)
        
        # Тип события
        event_type = self.event_data.get('event_type', 'Не указан')
        info_layout.addRow("Тип:", QLabel(event_type))
        
        # Период
        period_text = self.get_period_text()
        info_layout.addRow("Период:", QLabel(period_text))
        
        # Местоположение
        location = self.event_data.get('location', 'Не указано')
        info_layout.addRow("Местоположение:", QLabel(location))
        
        scroll_layout.addWidget(info_group)
        
        # Описание
        desc_group = QGroupBox("Описание")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(200)
        description = self.event_data.get('description', 'Описание отсутствует')
        self.description_text.setPlainText(description)
        desc_layout.addWidget(self.description_text)
        
        scroll_layout.addWidget(desc_group)
        
        # Иерархия событий
        self.hierarchy_group = QGroupBox("Иерархия событий")
        self.hierarchy_layout = QVBoxLayout(self.hierarchy_group)
        
        # Родительское событие
        if self.event_data.get('parent_id'):
            parent_label = QLabel("Загрузка информации о родительском событии...")
            self.hierarchy_layout.addWidget(parent_label)
        
        # Дочерние события
        self.child_events_label = QLabel("Загрузка дочерних событий...")
        self.hierarchy_layout.addWidget(self.child_events_label)
        
        scroll_layout.addWidget(self.hierarchy_group)
        
        # Статистика
        self.stats_group = QGroupBox("Статистика связей")
        self.stats_layout = QFormLayout(self.stats_group)
        scroll_layout.addWidget(self.stats_group)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_connections_panel(self):
        """Создание панели связей"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("Связанные сущности")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Вкладки для разных типов связей
        self.connections_tabs = QTabWidget()
        
        # Вкладка персон
        self.persons_tab = QWidget()
        persons_layout = QVBoxLayout(self.persons_tab)
        
        self.persons_list = QListWidget()
        self.persons_list.itemDoubleClicked.connect(self.open_person_details)
        persons_layout.addWidget(self.persons_list)
        
        self.connections_tabs.addTab(self.persons_tab, "Персоны")
        
        # Вкладка стран
        self.countries_tab = QWidget()
        countries_layout = QVBoxLayout(self.countries_tab)
        
        self.countries_list = QListWidget()
        self.countries_list.itemDoubleClicked.connect(self.open_country_details)
        countries_layout.addWidget(self.countries_list)
        
        self.connections_tabs.addTab(self.countries_tab, "Страны")
        
        # Вкладка документов
        self.documents_tab = QWidget()
        documents_layout = QVBoxLayout(self.documents_tab)
        
        self.documents_list = QListWidget()
        self.documents_list.itemDoubleClicked.connect(self.open_document_details)
        documents_layout.addWidget(self.documents_list)
        
        self.connections_tabs.addTab(self.documents_tab, "Документы")
        
        # Вкладка источников
        self.sources_tab = QWidget()
        sources_layout = QVBoxLayout(self.sources_tab)
        
        self.sources_list = QListWidget()
        self.sources_list.itemDoubleClicked.connect(self.open_source_details)
        sources_layout.addWidget(self.sources_list)
        
        self.connections_tabs.addTab(self.sources_tab, "Источники")
        
        layout.addWidget(self.connections_tabs)
        
        # Кнопки управления связями
        if self.user_data['role_id'] >= 2:  # Модератор и выше
            buttons_layout = QVBoxLayout()
            
            manage_links_btn = QPushButton("Управлять связями")
            manage_links_btn.clicked.connect(self.manage_relationships)
            buttons_layout.addWidget(manage_links_btn)
            
            refresh_btn = QPushButton("Обновить")
            refresh_btn.clicked.connect(self.load_full_data)
            buttons_layout.addWidget(refresh_btn)
            
            layout.addLayout(buttons_layout)
        
        return panel
    
    def create_menus(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        export_action = QAction("Экспорт события", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_event)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("Закрыть", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Меню "Правка" (только для модераторов)
        if self.user_data['role_id'] >= 2:
            edit_menu = menubar.addMenu("Правка")
            
            edit_action = QAction("Редактировать событие", self)
            edit_action.setShortcut("Ctrl+E")
            edit_action.triggered.connect(self.edit_event)
            edit_menu.addAction(edit_action)
            
            edit_menu.addSeparator()
            
            manage_links_action = QAction("Управлять связями", self)
            manage_links_action.setShortcut("Ctrl+L")
            manage_links_action.triggered.connect(self.manage_relationships)
            edit_menu.addAction(manage_links_action)
        
        # Меню "Вид"
        view_menu = menubar.addMenu("Вид")
        
        refresh_action = QAction("Обновить", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_full_data)
        view_menu.addAction(refresh_action)

    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar("Основные действия")
        
        # Кнопка обновления
        refresh_action = QAction("Обновить", self)
        refresh_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_action.triggered.connect(self.load_full_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Кнопка экспорта
        export_action = QAction("Экспорт", self)
        export_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        export_action.triggered.connect(self.export_event)
        toolbar.addAction(export_action)
        
        # Кнопки редактирования (только для модераторов)
        if self.user_data['role_id'] >= 2:
            toolbar.addSeparator()
            
            edit_action = QAction("Редактировать", self)
            edit_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
            edit_action.triggered.connect(self.edit_event)
            toolbar.addAction(edit_action)
            
            links_action = QAction("Связи", self)
            links_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            links_action.triggered.connect(self.manage_relationships)
            toolbar.addAction(links_action)
    
    def get_period_text(self):
        """Получение текстового представления периода"""
        start_date = self.event_data.get('start_date')
        end_date = self.event_data.get('end_date')
        
        if start_date and end_date:
            if start_date == end_date:
                return str(start_date)
            else:
                return f"{start_date} - {end_date}"
        elif start_date:
            return f"с {start_date}"
        elif end_date:
            return f"до {end_date}"
        else:
            return "Период не указан"
    
    def load_full_data(self):
        """Загрузка полных данных события"""
        try:
            # Загружаем подробную информацию
            self.full_event_data = self.event_service.get_event_details(
                self.user_data['user_id'], 
                self.event_data['event_id']
            )
            
            # Обновляем интерфейс
            self.update_hierarchy_info()
            self.update_connections()
            self.update_statistics()
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Ошибка загрузки", 
                f"Не удалось загрузить полную информацию о событии:\n{str(e)}"
            )
    
    def update_hierarchy_info(self):
        """Обновление информации об иерархии"""
        if not self.full_event_data:
            return
        
        # Очищаем предыдущую информацию
        for i in reversed(range(self.hierarchy_layout.count())):
            self.hierarchy_layout.itemAt(i).widget().setParent(None)
        
        # Родительское событие
        if self.event_data.get('parent_id'):
            parent_label = QLabel("Родительское событие:")
            parent_label.setStyleSheet("font-weight: bold;")
            self.hierarchy_layout.addWidget(parent_label)
            
            # Здесь нужно загрузить информацию о родительском событии
            parent_info = QLabel("Загрузка информации о родительском событии...")
            self.hierarchy_layout.addWidget(parent_info)
        
        # Дочерние события
        child_events = self.full_event_data.get('child_events', [])
        if child_events:
            child_label = QLabel("Дочерние события:")
            child_label.setStyleSheet("font-weight: bold;")
            self.hierarchy_layout.addWidget(child_label)
            
            for child in child_events[:5]:  # Показываем первые 5
                child_item = QLabel(f"• {child['name']}")
                child_item.setStyleSheet("margin-left: 20px;")
                self.hierarchy_layout.addWidget(child_item)
            
            if len(child_events) > 5:
                more_label = QLabel(f"... и еще {len(child_events) - 5} событий")
                more_label.setStyleSheet("margin-left: 20px; font-style: italic;")
                self.hierarchy_layout.addWidget(more_label)
        else:
            no_children_label = QLabel("Дочерних событий нет")
            no_children_label.setStyleSheet("font-style: italic; color: gray;")
            self.hierarchy_layout.addWidget(no_children_label)
    
    def update_connections(self):
        """Обновление информации о связях"""
        if not self.full_event_data:
            return
        
        # Персоны
        self.persons_list.clear()
        persons = self.full_event_data.get('related_persons', [])
        for person in persons:
            item = QListWidgetItem(f"{person['name']} {person.get('surname', '')}")
            item.setData(Qt.ItemDataRole.UserRole, person)
            self.persons_list.addItem(item)
        
        if not persons:
            item = QListWidgetItem("Связанных персон нет")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.persons_list.addItem(item)
        
        # Страны
        self.countries_list.clear()
        countries = self.full_event_data.get('related_countries', [])
        for country in countries:
            item = QListWidgetItem(country['name'])
            item.setData(Qt.ItemDataRole.UserRole, country)
            self.countries_list.addItem(item)
        
        if not countries:
            item = QListWidgetItem("Связанных стран нет")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.countries_list.addItem(item)
        
        # Документы
        self.documents_list.clear()
        documents = self.full_event_data.get('related_documents', [])
        for document in documents:
            item = QListWidgetItem(document['name'])
            item.setData(Qt.ItemDataRole.UserRole, document)
            self.documents_list.addItem(item)
        
        if not documents:
            item = QListWidgetItem("Связанных документов нет")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.documents_list.addItem(item)
        
        # Источники
        self.sources_list.clear()
        sources = self.full_event_data.get('related_sources', [])
        for source in sources:
            author_info = f" - {source['author']}" if source.get('author') else ""
            item = QListWidgetItem(f"{source['name']}{author_info}")
            item.setData(Qt.ItemDataRole.UserRole, source)
            self.sources_list.addItem(item)
        
        if not sources:
            item = QListWidgetItem("Связанных источников нет")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.sources_list.addItem(item)
    
    def update_statistics(self):
        """Обновление статистики"""
        if not self.full_event_data:
            return
        
        # Очищаем предыдущую статистику
        for i in reversed(range(self.stats_layout.count())):
            self.stats_layout.itemAt(i).widget().setParent(None)
        
        # Получаем сводку по связям
        relationships_summary = self.full_event_data.get('relationships_summary', {})
        relationships = relationships_summary.get('relationships', {})
        
        self.stats_layout.addRow("Связанных персон:", QLabel(str(relationships.get('persons', 0))))
        self.stats_layout.addRow("Связанных стран:", QLabel(str(relationships.get('countries', 0))))
        self.stats_layout.addRow("Связанных документов:", QLabel(str(relationships.get('documents', 0))))
        self.stats_layout.addRow("Связанных источников:", QLabel(str(relationships.get('sources', 0))))
        
        total_connections = sum(relationships.values())
        self.stats_layout.addRow("Всего связей:", QLabel(str(total_connections)))
    
    def edit_event(self):
        """Редактирование события"""
        try:
            from ui.dialogs.event_dialog import EventDialog
            
            dialog = EventDialog(self.user_data, self.event_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Обновляем данные
                self.load_full_data()
                # Обновляем заголовок окна
                self.setWindowTitle(f"Событие: {self.event_data['name']}")
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось открыть диалог редактирования:\n{str(e)}"
            )
    
    def manage_relationships(self):
        """Управление связями"""
        try:
            from ui.dialogs.relationship_dialog import RelationshipDialog
            
            dialog = RelationshipDialog(
                self.user_data, 
                'EVENT', 
                self.event_data['event_id'],
                self.event_data['name'],
                self
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_full_data()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось открыть диалог управления связями:\n{str(e)}"
            )
    
    def export_event(self):
        """Экспорт события"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт события",
                f"event_{self.event_data['event_id']}.json",
                "JSON Files (*.json);;Text Files (*.txt)"
            )
            
            if filename:
                import json
                
                export_data = {
                    'event': self.event_data,
                    'full_data': self.full_event_data,
                    'export_timestamp': QDateTime.currentDateTime().toString()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    if filename.endswith('.json'):
                        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
                    else:
                        f.write(f"Событие: {self.event_data['name']}\n")
                        f.write(f"Период: {self.get_period_text()}\n")
                        f.write(f"Тип: {self.event_data.get('event_type', 'Не указан')}\n")
                        f.write(f"Местоположение: {self.event_data.get('location', 'Не указано')}\n\n")
                        f.write(f"Описание:\n{self.event_data.get('description', 'Не указано')}\n")
                
                QMessageBox.information(
                    self, 
                    "Экспорт завершен", 
                    f"Событие успешно экспортировано в файл:\n{filename}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка экспорта", 
                f"Не удалось экспортировать событие:\n{str(e)}"
            )
    
    
    def open_person_details(self, item):
        """Открытие деталей персоны"""
        person_data = item.data(Qt.ItemDataRole.UserRole)
        if person_data:
            try:
                from ui.windows.person_details_window import PersonDetailsWindow
                
                details_window = PersonDetailsWindow(person_data, self.user_data, self)
                details_window.show()
                
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    f"Не удалось открыть детали персоны:\n{str(e)}"
                )
    
    def open_country_details(self, item):
        """Открытие деталей страны"""
        country_data = item.data(Qt.ItemDataRole.UserRole)
        if country_data:
            try:
                from ui.windows.country_details_window import CountryDetailsWindow
                
                details_window = CountryDetailsWindow(country_data, self.user_data, self)
                details_window.show()
                
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    f"Не удалось открыть детали страны:\n{str(e)}"
                )
    
    def open_document_details(self, item):
        """Открытие деталей документа"""
        document_data = item.data(Qt.ItemDataRole.UserRole)
        if document_data:
            try:
                from ui.windows.document_details_window import DocumentDetailsWindow
                
                details_window = DocumentDetailsWindow(document_data, self.user_data, self)
                details_window.show()
                
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    f"Не удалось открыть детали документа:\n{str(e)}"
                )
    
    def open_source_details(self, item):
        """Открытие деталей источника"""
        source_data = item.data(Qt.ItemDataRole.UserRole)
        if source_data:
            try:
                from ui.windows.source_details_window import SourceDetailsWindow
                
                details_window = SourceDetailsWindow(source_data, self.user_data, self)
                details_window.show()
                
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    f"Не удалось открыть детали источника:\n{str(e)}"
                )
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Можно добавить проверки на несохраненные изменения
        event.accept()
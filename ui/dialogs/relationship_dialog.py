# ui/dialogs/relationship_dialog.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class RelationshipDialog(QDialog):
    """Диалог для управления связями между сущностями"""
    
    def __init__(self, user_data, entity_type, entity_id, entity_name, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.entity_name = entity_name
        
        from services.relationship_service import RelationshipService
        from services.person_service import PersonService
        from services.event_service import EventService
        from services.document_service import DocumentService
        from services.source_service import SourceService
        from services.country_service import CountryService
        from data_access.relationships_repository import RelationshipsRepository
        
        self.relationship_service = RelationshipService()
        self.person_service = PersonService()
        self.event_service = EventService()
        self.document_service = DocumentService()
        self.source_service = SourceService()
        self.country_service = CountryService()
        self.rel_repo = RelationshipsRepository()
        
        self.setup_ui()
        self.load_current_relationships()
    
    def setup_ui(self):
        self.setWindowTitle(f"Связи: {self.entity_name}")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel(f"Управление связями для: {self.entity_name}")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Вкладки для разных типов связей
        self.tabs = QTabWidget()
        
        # Определяем какие вкладки нужны в зависимости от типа сущности
        if self.entity_type == 'PERSON':
            self.create_events_tab()
            self.create_documents_tab()
        elif self.entity_type == 'EVENT':
            self.create_persons_tab()
            self.create_countries_tab()
            self.create_documents_tab()
            self.create_sources_tab()
        elif self.entity_type == 'COUNTRY':
            self.create_events_tab()
        elif self.entity_type == 'DOCUMENT':
            self.create_persons_tab()
            self.create_events_tab()
        elif self.entity_type == 'SOURCE':
            self.create_events_tab()
        
        layout.addWidget(self.tabs)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.load_current_relationships)
        buttons_layout.addWidget(self.refresh_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_persons_tab(self):
        """Создание вкладки для связей с персонами"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Поиск и добавление
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск персон:"))
        
        self.persons_search = QLineEdit()
        self.persons_search.setPlaceholderText("Введите имя для поиска...")
        self.persons_search.returnPressed.connect(lambda: self.search_entities('persons'))
        search_layout.addWidget(self.persons_search)
        
        self.search_persons_btn = QPushButton("Найти")
        self.search_persons_btn.clicked.connect(lambda: self.search_entities('persons'))
        search_layout.addWidget(self.search_persons_btn)
        
        layout.addLayout(search_layout)
        
        # Горизонтальное разделение
        content_layout = QHBoxLayout()
        
        # Доступные персоны
        available_group = QGroupBox("Доступные персоны")
        available_layout = QVBoxLayout(available_group)
        
        self.available_persons = QListWidget()
        self.available_persons.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        available_layout.addWidget(self.available_persons)
        
        add_persons_btn = QPushButton("Добавить выбранные →")
        add_persons_btn.clicked.connect(lambda: self.add_relationships('persons'))
        available_layout.addWidget(add_persons_btn)
        
        content_layout.addWidget(available_group)
        
        # Связанные персоны
        linked_group = QGroupBox("Связанные персоны")
        linked_layout = QVBoxLayout(linked_group)
        
        self.linked_persons = QListWidget()
        self.linked_persons.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        linked_layout.addWidget(self.linked_persons)
        
        remove_persons_btn = QPushButton("← Удалить выбранные")
        remove_persons_btn.clicked.connect(lambda: self.remove_relationships('persons'))
        linked_layout.addWidget(remove_persons_btn)
        
        content_layout.addWidget(linked_group)
        
        layout.addLayout(content_layout)
        
        self.tabs.addTab(tab, "Персоны")
    
    def create_events_tab(self):
        """Создание вкладки для связей с событиями"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Поиск и добавление
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск событий:"))
        
        self.events_search = QLineEdit()
        self.events_search.setPlaceholderText("Введите название для поиска...")
        self.events_search.returnPressed.connect(lambda: self.search_entities('events'))
        search_layout.addWidget(self.events_search)
        
        self.search_events_btn = QPushButton("Найти")
        self.search_events_btn.clicked.connect(lambda: self.search_entities('events'))
        search_layout.addWidget(self.search_events_btn)
        
        layout.addLayout(search_layout)
        
        # Горизонтальное разделение
        content_layout = QHBoxLayout()
        
        # Доступные события
        available_group = QGroupBox("Доступные события")
        available_layout = QVBoxLayout(available_group)
        
        self.available_events = QListWidget()
        self.available_events.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        available_layout.addWidget(self.available_events)
        
        add_events_btn = QPushButton("Добавить выбранные →")
        add_events_btn.clicked.connect(lambda: self.add_relationships('events'))
        available_layout.addWidget(add_events_btn)
        
        content_layout.addWidget(available_group)
        
        # Связанные события
        linked_group = QGroupBox("Связанные события")
        linked_layout = QVBoxLayout(linked_group)
        
        self.linked_events = QListWidget()
        self.linked_events.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        linked_layout.addWidget(self.linked_events)
        
        remove_events_btn = QPushButton("← Удалить выбранные")
        remove_events_btn.clicked.connect(lambda: self.remove_relationships('events'))
        linked_layout.addWidget(remove_events_btn)
        
        content_layout.addWidget(linked_group)
        
        layout.addLayout(content_layout)
        
        self.tabs.addTab(tab, "События")
    
    def create_countries_tab(self):
        """Создание вкладки для связей со странами"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Поиск и добавление
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск стран:"))
        
        self.countries_search = QLineEdit()
        self.countries_search.setPlaceholderText("Введите название для поиска...")
        self.countries_search.returnPressed.connect(lambda: self.search_entities('countries'))
        search_layout.addWidget(self.countries_search)
        
        self.search_countries_btn = QPushButton("Найти")
        self.search_countries_btn.clicked.connect(lambda: self.search_entities('countries'))
        search_layout.addWidget(self.search_countries_btn)
        
        layout.addLayout(search_layout)
        
        # Горизонтальное разделение
        content_layout = QHBoxLayout()
        
        # Доступные страны
        available_group = QGroupBox("Доступные страны")
        available_layout = QVBoxLayout(available_group)
        
        self.available_countries = QListWidget()
        self.available_countries.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        available_layout.addWidget(self.available_countries)
        
        add_countries_btn = QPushButton("Добавить выбранные →")
        add_countries_btn.clicked.connect(lambda: self.add_relationships('countries'))
        available_layout.addWidget(add_countries_btn)
        
        content_layout.addWidget(available_group)
        
        # Связанные страны
        linked_group = QGroupBox("Связанные страны")
        linked_layout = QVBoxLayout(linked_group)
        
        self.linked_countries = QListWidget()
        self.linked_countries.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        linked_layout.addWidget(self.linked_countries)
        
        remove_countries_btn = QPushButton("← Удалить выбранные")
        remove_countries_btn.clicked.connect(lambda: self.remove_relationships('countries'))
        linked_layout.addWidget(remove_countries_btn)
        
        content_layout.addWidget(linked_group)
        
        layout.addLayout(content_layout)
        
        self.tabs.addTab(tab, "Страны")
    
    def create_documents_tab(self):
        """Создание вкладки для связей с документами"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Поиск и добавление
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск документов:"))
        
        self.documents_search = QLineEdit()
        self.documents_search.setPlaceholderText("Введите название для поиска...")
        self.documents_search.returnPressed.connect(lambda: self.search_entities('documents'))
        search_layout.addWidget(self.documents_search)
        
        self.search_documents_btn = QPushButton("Найти")
        self.search_documents_btn.clicked.connect(lambda: self.search_entities('documents'))
        search_layout.addWidget(self.search_documents_btn)
        
        layout.addLayout(search_layout)
        
        # Горизонтальное разделение
        content_layout = QHBoxLayout()
        
        # Доступные документы
        available_group = QGroupBox("Доступные документы")
        available_layout = QVBoxLayout(available_group)
        
        self.available_documents = QListWidget()
        self.available_documents.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        available_layout.addWidget(self.available_documents)
        
        add_documents_btn = QPushButton("Добавить выбранные →")
        add_documents_btn.clicked.connect(lambda: self.add_relationships('documents'))
        available_layout.addWidget(add_documents_btn)
        
        content_layout.addWidget(available_group)
        
        # Связанные документы
        linked_group = QGroupBox("Связанные документы")
        linked_layout = QVBoxLayout(linked_group)
        
        self.linked_documents = QListWidget()
        self.linked_documents.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        linked_layout.addWidget(self.linked_documents)
        
        remove_documents_btn = QPushButton("← Удалить выбранные")
        remove_documents_btn.clicked.connect(lambda: self.remove_relationships('documents'))
        linked_layout.addWidget(remove_documents_btn)
        
        content_layout.addWidget(linked_group)
        
        layout.addLayout(content_layout)
        
        self.tabs.addTab(tab, "Документы")
    
    def create_sources_tab(self):
        """Создание вкладки для связей с источниками"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Поиск и добавление
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск источников:"))
        
        self.sources_search = QLineEdit()
        self.sources_search.setPlaceholderText("Введите название для поиска...")
        self.sources_search.returnPressed.connect(lambda: self.search_entities('sources'))
        search_layout.addWidget(self.sources_search)
        
        self.search_sources_btn = QPushButton("Найти")
        self.search_sources_btn.clicked.connect(lambda: self.search_entities('sources'))
        search_layout.addWidget(self.search_sources_btn)
        
        layout.addLayout(search_layout)
        
        # Горизонтальное разделение
        content_layout = QHBoxLayout()
        
        # Доступные источники
        available_group = QGroupBox("Доступные источники")
        available_layout = QVBoxLayout(available_group)
        
        self.available_sources = QListWidget()
        self.available_sources.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        available_layout.addWidget(self.available_sources)
        
        add_sources_btn = QPushButton("Добавить выбранные →")
        add_sources_btn.clicked.connect(lambda: self.add_relationships('sources'))
        available_layout.addWidget(add_sources_btn)
        
        content_layout.addWidget(available_group)
        
        # Связанные источники
        linked_group = QGroupBox("Связанные источники")
        linked_layout = QVBoxLayout(linked_group)
        
        self.linked_sources = QListWidget()
        self.linked_sources.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        linked_layout.addWidget(self.linked_sources)
        
        remove_sources_btn = QPushButton("← Удалить выбранные")
        remove_sources_btn.clicked.connect(lambda: self.remove_relationships('sources'))
        linked_layout.addWidget(remove_sources_btn)
        
        content_layout.addWidget(linked_group)
        
        layout.addLayout(content_layout)
        
        self.tabs.addTab(tab, "Источники")
    
    def load_current_relationships(self):
        """Загрузка текущих связей"""
        try:
            # Загружаем связанные сущности в соответствующие списки
            if hasattr(self, 'linked_persons'):
                self.load_linked_entities('persons')
            if hasattr(self, 'linked_events'):
                self.load_linked_entities('events')
            if hasattr(self, 'linked_countries'):
                self.load_linked_entities('countries')
            if hasattr(self, 'linked_documents'):
                self.load_linked_entities('documents')
            if hasattr(self, 'linked_sources'):
                self.load_linked_entities('sources')
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить связи:\n{str(e)}")
    
    def load_linked_entities(self, entity_type):
        """Загрузка связанных сущностей определенного типа"""
        try:
            list_widget = getattr(self, f'linked_{entity_type}')
            list_widget.clear()
            
            # Получаем ID связанных сущностей напрямую из репозитория
            if entity_type == 'persons':
                if self.entity_type == 'EVENT':
                    linked_ids = self.rel_repo.get_event_persons_links(self.entity_id)
                    # Получаем данные персон
                    entities = []
                    for person_id in linked_ids:
                        person = self.person_service.person_repo.get_by_id(person_id)
                        if person:
                            entities.append(person)
                elif self.entity_type == 'DOCUMENT':
                    linked_ids = self.rel_repo.get_document_persons_links(self.entity_id)
                    entities = []
                    for person_id in linked_ids:
                        person = self.person_service.person_repo.get_by_id(person_id)
                        if person:
                            entities.append(person)
                else:
                    entities = []
            
            elif entity_type == 'events':
                if self.entity_type == 'PERSON':
                    linked_ids = self.rel_repo.get_person_events_links(self.entity_id)
                    entities = []
                    for event_id in linked_ids:
                        event = self.event_service.event_repo.get_by_id(event_id)
                        if event:
                            entities.append(event)
                elif self.entity_type == 'COUNTRY':
                    linked_ids = self.rel_repo.get_country_events_links(self.entity_id)
                    entities = []
                    for event_id in linked_ids:
                        event = self.event_service.event_repo.get_by_id(event_id)
                        if event:
                            entities.append(event)
                elif self.entity_type == 'DOCUMENT':
                    linked_ids = self.rel_repo.get_document_events_links(self.entity_id)
                    entities = []
                    for event_id in linked_ids:
                        event = self.event_service.event_repo.get_by_id(event_id)
                        if event:
                            entities.append(event)
                elif self.entity_type == 'SOURCE':
                    linked_ids = self.rel_repo.get_source_events_links(self.entity_id)
                    entities = []
                    for event_id in linked_ids:
                        event = self.event_service.event_repo.get_by_id(event_id)
                        if event:
                            entities.append(event)
                else:
                    entities = []
            
            elif entity_type == 'countries':
                if self.entity_type == 'EVENT':
                    linked_ids = self.rel_repo.get_event_countries_links(self.entity_id)
                    entities = []
                    for country_id in linked_ids:
                        country = self.country_service.country_repo.get_by_id(country_id)
                        if country:
                            entities.append(country)
                else:
                    entities = []
            
            elif entity_type == 'documents':
                if self.entity_type == 'PERSON':
                    linked_ids = self.rel_repo.get_person_documents_links(self.entity_id)
                    entities = []
                    for document_id in linked_ids:
                        document = self.document_service.document_repo.get_by_id(document_id)
                        if document:
                            entities.append(document)
                elif self.entity_type == 'EVENT':
                    linked_ids = self.rel_repo.get_event_documents_links(self.entity_id)
                    entities = []
                    for document_id in linked_ids:
                        document = self.document_service.document_repo.get_by_id(document_id)
                        if document:
                            entities.append(document)
                else:
                    entities = []
            
            elif entity_type == 'sources':
                if self.entity_type == 'EVENT':
                    linked_ids = self.rel_repo.get_event_sources_links(self.entity_id)
                    entities = []
                    for source_id in linked_ids:
                        source = self.source_service.source_repo.get_by_id(source_id)
                        if source:
                            entities.append(source)
                else:
                    entities = []
            
            else:
                entities = []
            
            # Добавляем элементы в список
            for entity in entities:
                item = QListWidgetItem()
                if entity_type == 'persons':
                    name = entity.get('name', '')
                    surname = entity.get('surname', '')
                    display_name = f"{name} {surname}".strip()
                    item.setText(display_name)
                    item.setData(Qt.ItemDataRole.UserRole, entity['person_id'])
                elif entity_type == 'events':
                    item.setText(entity['name'])
                    item.setData(Qt.ItemDataRole.UserRole, entity['event_id'])
                elif entity_type == 'countries':
                    item.setText(entity['name'])
                    item.setData(Qt.ItemDataRole.UserRole, entity['country_id'])
                elif entity_type == 'documents':
                    item.setText(entity['name'])
                    item.setData(Qt.ItemDataRole.UserRole, entity['document_id'])
                elif entity_type == 'sources':
                    name = entity.get('name', '')
                    author = entity.get('author', 'Автор не указан')
                    item.setText(f"{name} - {author}")
                    item.setData(Qt.ItemDataRole.UserRole, entity['source_id'])
                
                list_widget.addItem(item)
                
        except Exception as e:
            print(f"Ошибка загрузки связанных {entity_type}: {e}")
            import traceback
            traceback.print_exc()
    
    def search_entities(self, entity_type):
        """Поиск сущностей для связывания"""
        try:
            search_widget = getattr(self, f'{entity_type}_search')
            available_widget = getattr(self, f'available_{entity_type}')
            
            search_text = search_widget.text().strip()
            if not search_text:
                QMessageBox.information(self, "Информация", "Введите текст для поиска")
                return
            
            available_widget.clear()
            
            if entity_type == 'persons':
                result = self.person_service.search_persons(
                    self.user_data['user_id'], 
                    search_text, 
                    limit=20
                )
                entities = result.get('results', [])
            elif entity_type == 'events':
                result = self.event_service.get_events(
                    self.user_data['user_id'], 
                    {'search_term': search_text, 'limit': 20}
                )
                entities = result.get('events', [])
            elif entity_type == 'countries':
                result = self.country_service.search_countries(
                    self.user_data['user_id'], 
                    search_text, 
                    limit=20
                )
                entities = result.get('results', [])
            elif entity_type == 'documents':
                result = self.document_service.search_documents(
                    self.user_data['user_id'], 
                    search_text, 
                    search_in_content=False,
                    limit=20
                )
                entities = result.get('results', [])
            elif entity_type == 'sources':
                result = self.source_service.search_sources(
                    self.user_data['user_id'], 
                    search_text, 
                    limit=20
                )
                entities = result.get('results', [])
            else:
                entities = []
            
            for entity in entities:
                item = QListWidgetItem()
                if entity_type == 'persons':
                    name = entity.get('name', '')
                    surname = entity.get('surname', '')
                    display_name = f"{name} {surname}".strip()
                    item.setText(display_name)
                    item.setData(Qt.ItemDataRole.UserRole, entity['person_id'])
                elif entity_type == 'events':
                    item.setText(entity['name'])
                    item.setData(Qt.ItemDataRole.UserRole, entity['event_id'])
                elif entity_type == 'countries':
                    item.setText(entity['name'])
                    item.setData(Qt.ItemDataRole.UserRole, entity['country_id'])
                elif entity_type == 'documents':
                    item.setText(entity['name'])
                    item.setData(Qt.ItemDataRole.UserRole, entity['document_id'])
                elif entity_type == 'sources':
                    name = entity.get('name', '')
                    author = entity.get('author', 'Автор не указан')
                    item.setText(f"{name} - {author}")
                    item.setData(Qt.ItemDataRole.UserRole, entity['source_id'])
                
                available_widget.addItem(item)
            
            if not entities:
                QMessageBox.information(self, "Результаты поиска", "Ничего не найдено")
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка поиска", f"Произошла ошибка при поиске:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def add_relationships(self, relationship_type):
        """Добавление связей"""
        try:
            available_widget = getattr(self, f'available_{relationship_type}')
            selected_items = available_widget.selectedItems()
            
            if not selected_items:
                QMessageBox.information(self, "Информация", "Выберите элементы для добавления")
                return
            
            success_count = 0
            error_count = 0
            error_messages = []
            
            for item in selected_items:
                entity_id = item.data(Qt.ItemDataRole.UserRole)
                
                try:
                    result = None
                    
                    if relationship_type == 'persons':
                        if self.entity_type == 'EVENT':
                            result = self.relationship_service.link_person_to_event(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                        elif self.entity_type == 'DOCUMENT':
                            result = self.relationship_service.link_document_to_person(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                    elif relationship_type == 'events':
                        if self.entity_type == 'PERSON':
                            result = self.relationship_service.link_person_to_event(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                        elif self.entity_type == 'COUNTRY':
                            result = self.relationship_service.link_country_to_event(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                        elif self.entity_type == 'DOCUMENT':
                            result = self.relationship_service.link_document_to_event(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                        elif self.entity_type == 'SOURCE':
                            result = self.relationship_service.link_event_to_source(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                    elif relationship_type == 'countries':
                        if self.entity_type == 'EVENT':
                            result = self.relationship_service.link_country_to_event(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                    elif relationship_type == 'documents':
                        if self.entity_type == 'PERSON':
                            result = self.relationship_service.link_document_to_person(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                        elif self.entity_type == 'EVENT':
                            result = self.relationship_service.link_document_to_event(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                    elif relationship_type == 'sources':
                        if self.entity_type == 'EVENT':
                            result = self.relationship_service.link_event_to_source(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                    
                    if result and result.get('success'):
                        success_count += 1
                    else:
                        error_count += 1
                        error_messages.append(result.get('message', 'Неизвестная ошибка') if result else 'Нет результата')
                        
                except Exception as e:
                    error_count += 1
                    error_messages.append(str(e))
                    print(f"Ошибка добавления связи: {e}")
            
            message = f"Успешно добавлено связей: {success_count}"
            if error_count > 0:
                message += f"\nОшибок: {error_count}"
                if error_messages:
                    message += f"\nПримеры ошибок: {'; '.join(error_messages[:3])}"
            
            if success_count > 0:
                QMessageBox.information(self, "Результат", message)
                self.load_current_relationships()
            else:
                QMessageBox.warning(self, "Ошибка", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла ошибка:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def remove_relationships(self, relationship_type):
        """Удаление связей"""
        try:
            linked_widget = getattr(self, f'linked_{relationship_type}')
            selected_items = linked_widget.selectedItems()
            
            if not selected_items:
                QMessageBox.information(self, "Информация", "Выберите элементы для удаления")
                return
            
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить {len(selected_items)} связей?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            success_count = 0
            error_count = 0
            error_messages = []
            
            for item in selected_items:
                entity_id = item.data(Qt.ItemDataRole.UserRole)
                
                try:
                    result = None
                    
                    if relationship_type == 'persons':
                        if self.entity_type == 'EVENT':
                            result = self.relationship_service.unlink_person_from_event(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                        elif self.entity_type == 'DOCUMENT':
                            # Для документов используем прямой вызов репозитория
                            success = self.rel_repo.unlink_document_from_person(
                                self.entity_id, entity_id, self.user_data['user_id']
                            )
                            result = {'success': success}
                    elif relationship_type == 'events':
                        if self.entity_type == 'PERSON':
                            result = self.relationship_service.unlink_person_from_event(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                        elif self.entity_type == 'COUNTRY':
                            result = self.relationship_service.unlink_country_from_event(
                                self.user_data['user_id'], self.entity_id, entity_id
                            )
                        elif self.entity_type == 'DOCUMENT':
                            success = self.rel_repo.unlink_document_from_event(
                                self.entity_id, entity_id, self.user_data['user_id']
                            )
                            result = {'success': success}
                        elif self.entity_type == 'SOURCE':
                            success = self.rel_repo.unlink_event_from_source(
                                entity_id, self.entity_id, self.user_data['user_id']
                            )
                            result = {'success': success}
                    elif relationship_type == 'countries':
                        if self.entity_type == 'EVENT':
                            result = self.relationship_service.unlink_country_from_event(
                                self.user_data['user_id'], entity_id, self.entity_id
                            )
                    elif relationship_type == 'documents':
                        if self.entity_type == 'PERSON':
                            success = self.rel_repo.unlink_document_from_person(
                                entity_id, self.entity_id, self.user_data['user_id']
                            )
                            result = {'success': success}
                        elif self.entity_type == 'EVENT':
                            success = self.rel_repo.unlink_document_from_event(
                                entity_id, self.entity_id, self.user_data['user_id']
                            )
                            result = {'success': success}
                    elif relationship_type == 'sources':
                        if self.entity_type == 'EVENT':
                            success = self.rel_repo.unlink_event_from_source(
                                self.entity_id, entity_id, self.user_data['user_id']
                            )
                            result = {'success': success}
                    
                    if result and result.get('success'):
                        success_count += 1
                    else:
                        error_count += 1
                        error_messages.append(result.get('message', 'Неизвестная ошибка') if result else 'Нет результата')
                        
                except Exception as e:
                    error_count += 1
                    error_messages.append(str(e))
                    print(f"Ошибка удаления связи: {e}")
            
            message = f"Успешно удалено связей: {success_count}"
            if error_count > 0:
                message += f"\nОшибок: {error_count}"
                if error_messages:
                    message += f"\nПримеры ошибок: {'; '.join(error_messages[:3])}"
            
            if success_count > 0:
                QMessageBox.information(self, "Результат", message)
                self.load_current_relationships()
            else:
                QMessageBox.warning(self, "Ошибка", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла ошибка:\n{str(e)}")
            import traceback
            traceback.print_exc()


class BatchRelationshipDialog(QDialog):
    """Диалог для массового управления связями"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        from services.relationship_service import RelationshipService
        self.relationship_service = RelationshipService()
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Массовое управление связями")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Описание
        description = QLabel(
            "Данный инструмент позволяет массово управлять связями между сущностями.\n"
            "Выберите операцию и настройте параметры."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Выбор операции
        operation_group = QGroupBox("Операция")
        operation_layout = QVBoxLayout(operation_group)
        
        self.cleanup_btn = QPushButton("Очистить висячие связи")
        self.cleanup_btn.clicked.connect(self.cleanup_orphaned_relationships)
        operation_layout.addWidget(self.cleanup_btn)
        
        self.validate_btn = QPushButton("Проверить целостность связей")
        self.validate_btn.clicked.connect(self.validate_relationships)
        operation_layout.addWidget(self.validate_btn)
        
        self.export_btn = QPushButton("Экспорт связей")
        self.export_btn.clicked.connect(self.export_relationships)
        operation_layout.addWidget(self.export_btn)
        
        layout.addWidget(operation_group)
        
        # Лог операций
        log_group = QGroupBox("Лог операций")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def cleanup_orphaned_relationships(self):
        """Очистка висячих связей"""
        try:
            self.log_text.append("Начинаем очистку висячих связей...")
            
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы уверены, что хотите удалить все висячие связи?\n"
                "Это действие нельзя отменить.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                self.log_text.append("Операция отменена пользователем.")
                return
            
            result = self.relationship_service.cleanup_orphaned_relationships(
                self.user_data['user_id']
            )
            
            if isinstance(result, dict) and any(result.values()):
                total_cleaned = sum(result.values())
                self.log_text.append(f"Успешно удалено висячих связей: {total_cleaned}")
                self.log_text.append(f"Детали: {result}")
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Очистка завершена. Удалено связей: {total_cleaned}"
                )
            else:
                self.log_text.append("Висячих связей не найдено или произошла ошибка")
                QMessageBox.information(
                    self, 
                    "Результат", 
                    "Висячих связей не найдено"
                )
                
        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            self.log_text.append(error_msg)
            QMessageBox.critical(self, "Ошибка", error_msg)
            import traceback
            traceback.print_exc()
    
    def validate_relationships(self):
        """Проверка целостности связей"""
        try:
            self.log_text.append("Начинаем проверку целостности связей...")
            
            # Простая проверка - подсчитываем связи
            from data_access.relationships_repository import RelationshipsRepository
            rel_repo = RelationshipsRepository()
            
            # Подсчитываем количество различных типов связей
            stats = {
                'events_persons': 0,
                'countries_events': 0,
                'documents_persons': 0,
                'documents_events': 0,
                'events_sources': 0
            }
            
            try:
                with rel_repo.db.get_cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM public.events_persons")
                    stats['events_persons'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM public.countries_events")
                    stats['countries_events'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM public.documents_persons")
                    stats['documents_persons'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM public.documents_events")
                    stats['documents_events'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM public.events_sources")
                    stats['events_sources'] = cursor.fetchone()[0]
                
                total_relationships = sum(stats.values())
                self.log_text.append(f"Общее количество связей: {total_relationships}")
                self.log_text.append(f"Детали по типам:")
                for rel_type, count in stats.items():
                    self.log_text.append(f"  {rel_type}: {count}")
                
                self.log_text.append("Проверка завершена. Подробная валидация не реализована.")
                QMessageBox.information(
                    self, 
                    "Результат проверки", 
                    f"Найдено {total_relationships} связей.\n"
                    "Подробности в логе операций."
                )
                
            except Exception as db_error:
                self.log_text.append(f"Ошибка подключения к БД: {db_error}")
                QMessageBox.warning(self, "Ошибка", f"Ошибка подключения к БД: {db_error}")
                
        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            self.log_text.append(error_msg)
            QMessageBox.critical(self, "Ошибка", error_msg)
            import traceback
            traceback.print_exc()
    
    def export_relationships(self):
        """Экспорт связей в файл"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить экспорт связей",
                "relationships_export.json",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if not filename:
                return
            
            self.log_text.append(f"Экспортируем связи в файл: {filename}")
            
            # Простой экспорт - получаем данные из БД
            from data_access.relationships_repository import RelationshipsRepository
            rel_repo = RelationshipsRepository()
            
            export_data = {
                'export_date': str(QDateTime.currentDateTime().toString()),
                'exported_by': self.user_data.get('username', 'Unknown'),
                'relationships': {}
            }
            
            try:
                with rel_repo.db.get_cursor() as cursor:
                    # Экспортируем связи персон и событий
                    cursor.execute("SELECT person_id, event_id FROM public.events_persons")
                    export_data['relationships']['events_persons'] = [
                        {'person_id': row[0], 'event_id': row[1]} for row in cursor.fetchall()
                    ]
                    
                    # Экспортируем связи стран и событий
                    cursor.execute("SELECT country_id, event_id FROM public.countries_events")
                    export_data['relationships']['countries_events'] = [
                        {'country_id': row[0], 'event_id': row[1]} for row in cursor.fetchall()
                    ]
                    
                    # Экспортируем связи документов и персон
                    cursor.execute("SELECT document_id, person_id FROM public.documents_persons")
                    export_data['relationships']['documents_persons'] = [
                        {'document_id': row[0], 'person_id': row[1]} for row in cursor.fetchall()
                    ]
                    
                    # Экспортируем связи документов и событий
                    cursor.execute("SELECT document_id, event_id FROM public.documents_events")
                    export_data['relationships']['documents_events'] = [
                        {'document_id': row[0], 'event_id': row[1]} for row in cursor.fetchall()
                    ]
                    
                    # Экспортируем связи событий и источников
                    cursor.execute("SELECT event_id, source_id FROM public.events_sources")
                    export_data['relationships']['events_sources'] = [
                        {'event_id': row[0], 'source_id': row[1]} for row in cursor.fetchall()
                    ]
                
                # Записываем в файл
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                total_exported = sum(len(rels) for rels in export_data['relationships'].values())
                self.log_text.append(f"Успешно экспортировано связей: {total_exported}")
                QMessageBox.information(
                    self, 
                    "Экспорт завершен", 
                    f"Связи успешно экспортированы.\n"
                    f"Файл: {filename}\n"
                    f"Количество: {total_exported}"
                )
                
            except Exception as db_error:
                self.log_text.append(f"Ошибка экспорта: {db_error}")
                QMessageBox.warning(self, "Ошибка экспорта", f"Ошибка экспорта: {db_error}")
                
        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            self.log_text.append(error_msg)
            QMessageBox.critical(self, "Ошибка", error_msg)
            import traceback
            traceback.print_exc()
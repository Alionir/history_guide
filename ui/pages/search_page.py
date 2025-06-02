from ui.pages.base_page import *
class SearchPage(BasePage):
    def __init__(self, user_data):
        from services.search_service import SearchService
        self.search_service = SearchService()
        super().__init__(user_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Глобальный поиск")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Панель поиска
        search_group = QGroupBox("Поиск")
        search_layout = QVBoxLayout(search_group)
        
        # Строка поиска
        search_input_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите поисковый запрос...")
        self.search_edit.returnPressed.connect(self.perform_search)
        search_input_layout.addWidget(self.search_edit)
        
        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.perform_search)
        search_input_layout.addWidget(self.search_btn)
        
        search_layout.addLayout(search_input_layout)
        
        # Типы поиска
        types_layout = QHBoxLayout()
        types_layout.addWidget(QLabel("Искать в:"))
        
        self.search_persons = QCheckBox("Персоны")
        self.search_persons.setChecked(True)
        types_layout.addWidget(self.search_persons)
        
        self.search_countries = QCheckBox("Страны")
        self.search_countries.setChecked(True)
        types_layout.addWidget(self.search_countries)
        
        self.search_events = QCheckBox("События")
        self.search_events.setChecked(True)
        types_layout.addWidget(self.search_events)
        
        self.search_documents = QCheckBox("Документы")
        self.search_documents.setChecked(True)
        types_layout.addWidget(self.search_documents)
        
        self.search_sources = QCheckBox("Источники")
        self.search_sources.setChecked(True)
        types_layout.addWidget(self.search_sources)
        
        types_layout.addStretch()
        
        search_layout.addLayout(types_layout)
        layout.addWidget(search_group)
        
        # Результаты поиска
        self.results_tabs = QTabWidget()
        layout.addWidget(self.results_tabs)
        
        # Создаем вкладки для каждого типа
        self.persons_results = QTreeWidget()
        self.persons_results.setHeaderLabels(["ID", "Имя", "Описание"])
        self.results_tabs.addTab(self.persons_results, "Персоны")
        
        self.countries_results = QTreeWidget()
        self.countries_results.setHeaderLabels(["ID", "Название", "Описание"])
        self.results_tabs.addTab(self.countries_results, "Страны")
        
        self.events_results = QTreeWidget()
        self.events_results.setHeaderLabels(["ID", "Название", "Описание"])
        self.results_tabs.addTab(self.events_results, "События")
        
        self.documents_results = QTreeWidget()
        self.documents_results.setHeaderLabels(["ID", "Название", "Фрагмент"])
        self.results_tabs.addTab(self.documents_results, "Документы")
        
        self.sources_results = QTreeWidget()
        self.sources_results.setHeaderLabels(["ID", "Название", "Автор"])
        self.results_tabs.addTab(self.sources_results, "Источники")
        
        # Статистика поиска
        self.stats_label = QLabel("Введите запрос для поиска")
        layout.addWidget(self.stats_label)
    
    def perform_search(self):
        """Выполнение поиска"""
        query = self.search_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите поисковый запрос")
            return
        
        # Определяем типы для поиска
        search_types = []
        if self.search_persons.isChecked():
            search_types.append('persons')
        if self.search_countries.isChecked():
            search_types.append('countries')
        if self.search_events.isChecked():
            search_types.append('events')
        if self.search_documents.isChecked():
            search_types.append('documents')
        if self.search_sources.isChecked():
            search_types.append('sources')
        
        if not search_types:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один тип для поиска")
            return
        
        try:
            # Выполняем поиск
            results = self.search_service.global_search(
                self.user_data['user_id'],
                query,
                search_types,
                limit_per_type=20
            )
            
            # Очищаем предыдущие результаты
            self.clear_results()
            
            # Заполняем результаты
            self.populate_results(results)
            
            # Обновляем статистику
            total_found = results['total_found']
            self.stats_label.setText(f"Найдено результатов: {total_found}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", f"Произошла ошибка: {str(e)}")
    
    def clear_results(self):
        """Очистка результатов поиска"""
        self.persons_results.clear()
        self.countries_results.clear()
        self.events_results.clear()
        self.documents_results.clear()
        self.sources_results.clear()
    
    def populate_results(self, results):
        """Заполнение результатов поиска"""
        # Персоны
        if 'persons' in results['results']:
            for person in results['results']['persons']['items']:
                item = QTreeWidgetItem([
                    str(person['person_id']),
                    person.get('full_name', person['name']),
                    person.get('biography', '')[:100] + '...' if person.get('biography') else ''
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, person)
                self.persons_results.addTopLevelItem(item)
        
        # Страны
        if 'countries' in results['results']:
            for country in results['results']['countries']['items']:
                item = QTreeWidgetItem([
                    str(country['country_id']),
                    country['name'],
                    country.get('description', '')[:100] + '...' if country.get('description') else ''
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, country)
                self.countries_results.addTopLevelItem(item)
        
        # События
        if 'events' in results['results']:
            for event in results['results']['events']['items']:
                item = QTreeWidgetItem([
                    str(event['event_id']),
                    event['name'],
                    event.get('description', '')[:100] + '...' if event.get('description') else ''
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, event)
                self.events_results.addTopLevelItem(item)
        
        # Документы
        if 'documents' in results['results']:
            for document in results['results']['documents']['items']:
                item = QTreeWidgetItem([
                    str(document['document_id']),
                    document['name'],
                    document.get('content', '')[:100] + '...' if document.get('content') else ''
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, document)
                self.documents_results.addTopLevelItem(item)
        
        # Источники
        if 'sources' in results['results']:
            for source in results['results']['sources']['items']:
                item = QTreeWidgetItem([
                    str(source['source_id']),
                    source['name'],
                    source.get('author', '')
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, source)
                self.sources_results.addTopLevelItem(item)
    
    def refresh(self):
        """Обновление - повторный поиск с теми же параметрами"""
        if self.search_edit.text().strip():
            self.perform_search()
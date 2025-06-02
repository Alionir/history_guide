from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.person_service import PersonService
from services.relationship_service import RelationshipService

class PersonDetailsWindow(QMainWindow):
    def __init__(self, person_data, user_data, parent=None):
        super().__init__(parent)
        self.person_data = person_data
        self.user_data = user_data
        self.person_service = PersonService()
        self.relationship_service = RelationshipService()
        self.setup_ui()
        self.load_full_data()
    
    def setup_ui(self):
        self.setWindowTitle(f"Персона: {self.person_data.get('full_name', self.person_data['name'])}")
        self.resize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель - основная информация
        left_panel = self.create_main_info_panel()
        main_layout.addWidget(left_panel, 2)
        
        # Правая панель - связи и дополнительная информация
        right_panel = self.create_connections_panel()
        main_layout.addWidget(right_panel, 1)
        
        # Создаем меню и тулбар
        self.create_menus()
        self.create_toolbar()
    
    def create_main_info_panel(self):
        """Создание панели основной информации о персоне"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Основная информация
        info_group = QGroupBox("Основная информация")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("ID:", QLabel(str(self.person_data['person_id'])))
        info_layout.addRow("Имя:", QLabel(self.person_data['name']))
        
        if self.person_data.get('surname'):
            info_layout.addRow("Фамилия:", QLabel(self.person_data['surname']))
        
        if self.person_data.get('patronymic'):
            info_layout.addRow("Отчество:", QLabel(self.person_data['patronymic']))
        
        # Даты жизни
        birth_text = str(self.person_data.get('date_of_birth', 'Не указана'))
        death_text = str(self.person_data.get('date_of_death', 'Не указана'))
        
        info_layout.addRow("Дата рождения:", QLabel(birth_text))
        info_layout.addRow("Дата смерти:", QLabel(death_text))
        
        # Полное имя
        full_name = self.person_data.get('full_name', self.person_data['name'])
        info_layout.addRow("Полное имя:", QLabel(full_name))
        
        # Страна
        if self.person_data.get('country_name'):
            info_layout.addRow("Страна:", QLabel(self.person_data['country_name']))
        
        layout.addWidget(info_group)
        
        # Биография
        bio_group = QGroupBox("Биография")
        bio_layout = QVBoxLayout(bio_group)
        
        self.biography_text = QTextEdit()
        self.biography_text.setReadOnly(True)
        biography = self.person_data.get('biography', 'Биография не указана')
        self.biography_text.setPlainText(biography)
        bio_layout.addWidget(self.biography_text)
        
        layout.addWidget(bio_group)
        
        return widget
    
    def create_connections_panel(self):
        """Создание панели связей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Статистика
        stats_group = QGroupBox("Связи")
        stats_layout = QVBoxLayout(stats_group)
        
        self.events_count_label = QLabel("События: загрузка...")
        self.documents_count_label = QLabel("Документы: загрузка...")
        
        stats_layout.addWidget(self.events_count_label)
        stats_layout.addWidget(self.documents_count_label)
        
        if self.user_data['role_id'] >= 2:
            manage_btn = QPushButton("Управлять связями")
            manage_btn.clicked.connect(self.manage_relationships)
            stats_layout.addWidget(manage_btn)
        
        layout.addWidget(stats_group)
        
        # Вкладки связей
        tabs = QTabWidget()
        
        # События
        self.events_list = QListWidget()
        self.events_list.itemDoubleClicked.connect(self.open_event_details)
        tabs.addTab(self.events_list, "События")
        
        # Документы
        self.documents_list = QListWidget()
        self.documents_list.itemDoubleClicked.connect(self.open_document_details)
        tabs.addTab(self.documents_list, "Документы")
        
        layout.addWidget(tabs)
        return widget
    
    def create_menus(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        actions_menu = menubar.addMenu('Действия')
        
        if self.user_data['role_id'] >= 2:
            edit_action = actions_menu.addAction('Редактировать', self.edit_person)
            edit_action.setShortcut('Ctrl+E')
        
        refresh_action = actions_menu.addAction('Обновить', self.load_full_data)
        refresh_action.setShortcut('F5')
        
        actions_menu.addSeparator()
        close_action = actions_menu.addAction('Закрыть', self.close)
    
    def create_toolbar(self):
        """Создание тулбара"""
        toolbar = self.addToolBar('Основное')
        
        if self.user_data['role_id'] >= 2:
            edit_action = QAction('Редактировать', self)
            edit_action.triggered.connect(self.edit_person)
            toolbar.addAction(edit_action)
            toolbar.addSeparator()
        
        refresh_action = QAction('Обновить', self)
        refresh_action.triggered.connect(self.load_full_data)
        toolbar.addAction(refresh_action)
    
    def load_full_data(self):
        """Загрузка полных данных персоны"""
        try:
            details = self.person_service.get_person_details(
                self.user_data['user_id'],
                self.person_data['person_id']
            )
            
            self.person_data.update(details['person'])
            
            # Обновляем статистику
            relationships = details['relationships_summary']['relationships']
            self.events_count_label.setText(f"События: {relationships.get('events', 0)}")
            self.documents_count_label.setText(f"Документы: {relationships.get('documents', 0)}")
            
            # Заполняем списки связей
            self.populate_relations_lists(details)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def populate_relations_lists(self, details):
        """Заполнение списков связей"""
        # События
        self.events_list.clear()
        for event in details.get('recent_events', []):
            event_text = event['name']
            if event.get('start_date'):
                event_text += f" ({event['start_date']})"
            
            item = QListWidgetItem(event_text)
            item.setData(Qt.ItemDataRole.UserRole, event)
            self.events_list.addItem(item)
        
        # Документы
        self.documents_list.clear()
        for document in details.get('recent_documents', []):
            doc_text = document['name']
            if document.get('creating_date'):
                doc_text += f" ({document['creating_date']})"
            
            item = QListWidgetItem(doc_text)
            item.setData(Qt.ItemDataRole.UserRole, document)
            self.documents_list.addItem(item)
    
    def edit_person(self):
        """Редактирование персоны"""
        try:
            from ui.dialogs.person_dialog import PersonDialog
            dialog = PersonDialog(self.user_data, self.person_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_full_data()
        except ImportError:
            QMessageBox.information(self, "Информация", "Диалог редактирования пока не реализован")
    
    def manage_relationships(self):
        """Управление связями персоны"""
        try:
            from ui.dialogs.relationship_dialog import RelationshipDialog
            dialog = RelationshipDialog(
                self.user_data,
                'PERSON',
                self.person_data['person_id'],
                self.person_data.get('full_name', self.person_data['name']),
                self
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_full_data()
        except ImportError:
            QMessageBox.information(self, "Информация", "Диалог управления связями пока не реализован")
    
    def open_event_details(self, item):
        """Открытие деталей события"""
        event_data = item.data(Qt.ItemDataRole.UserRole)
        if event_data:
            try:
                from ui.windows.event_details_window import EventDetailsWindow
                details_window = EventDetailsWindow(event_data, self.user_data, self)
                details_window.show()
            except ImportError:
                QMessageBox.information(self, "Информация", "Окно деталей события пока не реализовано")
    
    def open_document_details(self, item):
        """Открытие деталей документа"""
        document_data = item.data(Qt.ItemDataRole.UserRole)
        if document_data:
            try:
                from ui.windows.document_details_window import DocumentDetailsWindow
                details_window = DocumentDetailsWindow(document_data, self.user_data, self)
                details_window.show()
            except ImportError:
                QMessageBox.information(self, "Информация", "Окно деталей документа пока не реализовано")
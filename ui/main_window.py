# ui/main_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services import *

class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setup_ui()
        self.setup_services()
    
    def setup_ui(self):
        self.setWindowTitle("История - Справочник")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель навигации
        nav_panel = self.create_navigation_panel()
        main_layout.addWidget(nav_panel, 1)
        
        # Правая панель контента
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 4)
        
        # Создаем страницы
        self.create_pages()
        
        # Меню и тулбар
        self.create_menus()
        self.create_toolbar()
        
        # Статус бар
        self.statusBar().showMessage(f"Добро пожаловать, {self.user_data['username']}!")
        
        # Уведомления о непрочитанных заявках (для модераторов)
        if self.user_data['role_id'] >= 2:
            self.check_pending_requests()
    
    def create_navigation_panel(self):
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        
        # Заголовок
        title = QLabel("Навигация")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        nav_layout.addWidget(title)
        
        # Кнопки навигации
        nav_buttons = [
            ("Персоны", self.show_persons),
            ("Страны", self.show_countries),
            ("События", self.show_events),
            ("Документы", self.show_documents),
            ("Источники", self.show_sources),
            ("Поиск", self.show_search),
        ]
        
        for text, slot in nav_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn.setMinimumHeight(40)
            nav_layout.addWidget(btn)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        nav_layout.addWidget(separator)
        
        # Кнопки управления (для модераторов/админов)
        if self.user_data['role_id'] >= 2:
            admin_title = QLabel("Управление")
            admin_title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 10px; color: #0066cc;")
            nav_layout.addWidget(admin_title)
            
            admin_buttons = [
                ("Модерация", self.show_moderation, self.user_data['role_id'] >= 2),
                ("Аналитика", self.show_analytics, self.user_data['role_id'] >= 2),
                ("Экспорт", self.show_export, self.user_data['role_id'] >= 2)
            ]
            
            for text, slot, has_permission in admin_buttons:
                if has_permission:
                    btn = QPushButton(text)
                    btn.clicked.connect(slot)
                    btn.setMinimumHeight(40)
                    btn.setStyleSheet("QPushButton { background-color: #e8f4fd; }")
                    
                    # Добавляем индикатор для модерации
                    if text == "Модерация":
                        self.moderation_btn = btn
                        self.update_moderation_indicator()
                    
                    nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        
        # Информация о пользователе
        user_info = QLabel(f"Пользователь: {self.user_data['username']}\nРоль: {self.get_role_name()}")
        user_info.setStyleSheet("font-size: 10px; color: gray; padding: 5px;")
        nav_layout.addWidget(user_info)
        
        return nav_widget
    
    def get_role_name(self):
        """Получение названия роли"""
        roles = {1: "Пользователь", 2: "Модератор", 3: "Администратор"}
        return roles.get(self.user_data['role_id'], "Неизвестно")
    
    def create_pages(self):
        from ui.pages.persons_page import PersonsPage
        from ui.pages.countries_page import CountriesPage
        from ui.pages.events_page import EventsPage
        from ui.pages.documents_page import DocumentsPage
        from ui.pages.sources_page import SourcesPage
        from ui.pages.search_page import SearchPage
        from ui.pages.moderation_page import ModerationPage
        from ui.pages.analytics_page import AnalyticsPage
        
        self.persons_page = PersonsPage(self.user_data)
        self.countries_page = CountriesPage(self.user_data)
        self.events_page = EventsPage(self.user_data)
        self.documents_page = DocumentsPage(self.user_data)
        self.sources_page = SourcesPage(self.user_data)
        self.search_page = SearchPage(self.user_data)
        
        # Страницы для модераторов и админов
        if self.user_data['role_id'] >= 2:
            self.moderation_page = ModerationPage(self.user_data)
            self.analytics_page = AnalyticsPage(self.user_data)
            self.content_stack.addWidget(self.moderation_page)
            self.content_stack.addWidget(self.analytics_page)
        
        self.content_stack.addWidget(self.persons_page)
        self.content_stack.addWidget(self.countries_page)
        self.content_stack.addWidget(self.events_page)
        self.content_stack.addWidget(self.documents_page)
        self.content_stack.addWidget(self.sources_page)
        self.content_stack.addWidget(self.search_page)
        
        # Показываем персон по умолчанию
        self.content_stack.setCurrentWidget(self.persons_page)
    
    def setup_services(self):
        self.person_service = PersonService()
        self.country_service = CountryService()
        self.event_service = EventService()
        self.document_service = DocumentService()
        self.source_service = SourceService()
        self.search_service = SearchService()
        
        if self.user_data['role_id'] >= 2:
            self.moderation_service = ModerationService()
            self.analytics_service = AnalyticsService()
    
    def create_menus(self):
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu('Файл')
        file_menu.addAction('Экспорт данных', self.export_data)
        file_menu.addSeparator()
        file_menu.addAction('Выход', self.close)
        
        # Правка
        edit_menu = menubar.addMenu('Правка')
        edit_menu.addAction('Настройки', self.show_settings)
        
        # Модерация (для модераторов и админов)
        if self.user_data['role_id'] >= 2:
            moderation_menu = menubar.addMenu('Модерация')
            moderation_menu.addAction('Заявки на рассмотрение', self.show_moderation)
            moderation_menu.addAction('История модерации', self.show_moderation_history)
            
            if self.user_data['role_id'] >= 3:  # Только для админов
                moderation_menu.addSeparator()
                moderation_menu.addAction('Управление пользователями', self.show_user_management)
        
        # Справка
        help_menu = menubar.addMenu('Справка')
        help_menu.addAction('О программе', self.show_about)
    
    def create_toolbar(self):
        toolbar = self.addToolBar('Основное')
        
        # Кнопка поиска
        search_action = QAction('Поиск', self)
        search_action.setShortcut('Ctrl+F')
        search_action.triggered.connect(self.show_search)
        toolbar.addAction(search_action)
        
        toolbar.addSeparator()
        
        # Кнопка обновления
        refresh_action = QAction('Обновить', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_current_page)
        toolbar.addAction(refresh_action)
        
        # Кнопки для модераторов
        if self.user_data['role_id'] >= 2:
            toolbar.addSeparator()
            
            moderation_action = QAction('Модерация', self)
            moderation_action.triggered.connect(self.show_moderation)
            toolbar.addAction(moderation_action)
    
    def check_pending_requests(self):
        """Проверка количества ожидающих заявок"""
        try:
            if hasattr(self, 'moderation_service'):
                result = self.moderation_service.get_pending_requests(self.user_data['user_id'])
                pending_count = len([r for r in result['requests'] if r['status'] == 'PENDING'])
                
                if pending_count > 0:
                    self.show_notification(f"У вас {pending_count} заявок на рассмотрение")
        except:
            pass  # Игнорируем ошибки при проверке
    
    def update_moderation_indicator(self):
        """Обновление индикатора модерации"""
        if hasattr(self, 'moderation_btn') and hasattr(self, 'moderation_service'):
            try:
                result = self.moderation_service.get_pending_requests(self.user_data['user_id'])
                pending_count = len([r for r in result['requests'] if r['status'] == 'PENDING'])
                
                if pending_count > 0:
                    self.moderation_btn.setText(f"Модерация ({pending_count})")
                    self.moderation_btn.setStyleSheet("QPushButton { background-color: #fff3cd; color: #856404; }")
                else:
                    self.moderation_btn.setText("Модерация")
                    self.moderation_btn.setStyleSheet("QPushButton { background-color: #e8f4fd; }")
            except:
                pass
    
    def show_notification(self, message):
        """Показ уведомления в статус-баре"""
        self.statusBar().showMessage(message, 5000)  # Показываем на 5 секунд
    
    # Слоты навигации
    def show_persons(self):
        self.content_stack.setCurrentWidget(self.persons_page)
        self.statusBar().showMessage("Персоны")
    
    def show_countries(self):
        self.content_stack.setCurrentWidget(self.countries_page)
        self.statusBar().showMessage("Страны")
    
    def show_events(self):
        self.content_stack.setCurrentWidget(self.events_page)
        self.statusBar().showMessage("События")
    
    def show_documents(self):
        self.content_stack.setCurrentWidget(self.documents_page)
        self.statusBar().showMessage("Документы")
    
    def show_sources(self):
        self.content_stack.setCurrentWidget(self.sources_page)
        self.statusBar().showMessage("Источники")
    
    def show_search(self):
        self.content_stack.setCurrentWidget(self.search_page)
        self.statusBar().showMessage("Поиск")
    
    def show_moderation(self):
        """Показ страницы модерации"""
        if self.user_data['role_id'] >= 2 and hasattr(self, 'moderation_page'):
            self.content_stack.setCurrentWidget(self.moderation_page)
            self.statusBar().showMessage("Модерация заявок")
            self.update_moderation_indicator()  # Обновляем индикатор
        else:
            QMessageBox.warning(self, "Доступ запрещен", "У вас нет прав для доступа к модерации")
    
    def show_analytics(self):
        """Показ страницы аналитики"""
        if self.user_data['role_id'] >= 2 and hasattr(self, 'analytics_page'):
            self.content_stack.setCurrentWidget(self.analytics_page)
            self.statusBar().showMessage("Аналитика")
        else:
            QMessageBox.warning(self, "Доступ запрещен", "У вас нет прав для доступа к аналитике")
    
    def show_export(self):
        # Создаем и показываем окно экспорта
        from ui.windows.export_window import ExportWindow
        export_window = ExportWindow(self.user_data, self)
        export_window.show()
    
    def show_moderation_history(self):
        """Показ истории модерации"""
        QMessageBox.information(self, "История модерации", "Функция пока не реализована")
    
    def show_user_management(self):
        """Показ управления пользователями"""
        if self.user_data['role_id'] >= 3:
            from ui.windows.user_management_window import UserManagementWindow
            user_mgmt_window = UserManagementWindow(self.user_data, self)
            user_mgmt_window.show()
        else:
            QMessageBox.warning(self, "Доступ запрещен", "Только администраторы могут управлять пользователями")
    
    def refresh_current_page(self):
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
        
        # Обновляем индикатор модерации при обновлении
        if hasattr(self, 'moderation_btn'):
            self.update_moderation_indicator()
    
    def export_data(self):
        self.show_export()
    
    def show_settings(self):
        QMessageBox.information(self, "Настройки", "Настройки пока не реализованы")
    
    def show_about(self):
        QMessageBox.about(self, "О программе", 
                         "Исторический справочник v1.0\n\n"
                         "Система для управления исторической информацией\n"
                         "С системой модерации и контроля качества данных")
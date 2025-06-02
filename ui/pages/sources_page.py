from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.source_service import SourceService
from ui.pages.base_page import BasePage
from ui.dialogs.source_dialog import SourceDialog
import re

class SourcesPage(BasePage):
    def __init__(self, user_data):
        self.source_service = SourceService()
        super().__init__(user_data)
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок и кнопки
        header_layout = QHBoxLayout()
        
        title = QLabel("Источники")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Статистика (обновляется при загрузке)
        self.stats_label = QLabel("Загрузка статистики...")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        
        # Кнопка добавления
        self.add_btn = QPushButton("Добавить источник")
        self.add_btn.clicked.connect(self.add_source)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Панель поиска и фильтров
        search_group = QGroupBox("Поиск и фильтры")
        search_layout = QGridLayout(search_group)
        
        # Основной поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию источника...")
        self.search_edit.textChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("Название:"), 0, 0)
        search_layout.addWidget(self.search_edit, 0, 1)
        
        # Поиск по автору
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Поиск по автору...")
        self.author_edit.textChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("Автор:"), 0, 2)
        search_layout.addWidget(self.author_edit, 0, 3)
        
        # Фильтр по типу источника
        self.type_combo = QComboBox()
        self.type_combo.addItem("Все типы", None)
        self.type_combo.currentTextChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("Тип:"), 1, 0)
        search_layout.addWidget(self.type_combo, 1, 1)
        
        # Фильтр по наличию URL
        self.url_filter_combo = QComboBox()
        self.url_filter_combo.addItems(["Все источники", "Только с URL", "Только без URL"])
        self.url_filter_combo.currentTextChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("URL:"), 1, 2)
        search_layout.addWidget(self.url_filter_combo, 1, 3)
        
        # Сортировка
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Сортировка:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "По дате (новые первые)",
            "По дате (старые первые)",
            "По названию (А-Я)",
            "По названию (Я-А)",
            "По автору (А-Я)",
            "По типу"
        ])
        self.sort_combo.currentTextChanged.connect(self.filter_data)
        sort_layout.addWidget(self.sort_combo)
        
        # Кнопки управления
        reset_btn = QPushButton("Сбросить фильтры")
        reset_btn.clicked.connect(self.reset_filters)
        sort_layout.addWidget(reset_btn)
        
        if self.user_data['role_id'] >= 3:  # Админ
            check_urls_btn = QPushButton("Проверить URL")
            check_urls_btn.clicked.connect(self.check_urls)
            sort_layout.addWidget(check_urls_btn)
            
            find_duplicates_btn = QPushButton("Найти дубли")
            find_duplicates_btn.clicked.connect(self.find_duplicates)
            sort_layout.addWidget(find_duplicates_btn)
        
        sort_layout.addStretch()
        search_layout.addLayout(sort_layout, 2, 0, 1, 4)
        
        layout.addWidget(search_group)
        
        # Таблица источников
        self.sources_table = QTreeWidget()
        self.sources_table.setHeaderLabels([
            "ID", "Название", "Автор", "Тип", "Дата публикации", "URL", "События"
        ])
        self.sources_table.itemDoubleClicked.connect(self.view_source_details)
        
        # Настройка колонок
        header = self.sources_table.header()
        header.resizeSection(0, 50)   # ID
        header.resizeSection(1, 250)  # Название
        header.resizeSection(2, 150)  # Автор
        header.resizeSection(3, 100)  # Тип
        header.resizeSection(4, 120)  # Дата
        header.resizeSection(5, 100)  # URL
        header.resizeSection(6, 80)   # События
        
        # Контекстное меню
        self.sources_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sources_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.sources_table)
        
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
        
        # Загружаем типы источников
        self.load_source_types()
    
    def load_source_types(self):
        """Загрузка типов источников в комбобокс"""
        try:
            types = self.source_service.get_source_types(self.user_data['user_id'])
            for source_type in types:
                self.type_combo.addItem(source_type['type'], source_type['type'])
        except Exception as e:
            print(f"Ошибка загрузки типов источников: {e}")
    
    def load_data(self):
        """Загрузка данных об источниках"""
        try:
            filters = {
                'offset': self.current_page * self.page_size,
                'limit': self.page_size,
                'search_term': self.search_edit.text() if hasattr(self, 'search_edit') and self.search_edit.text() else None,
                'author': self.author_edit.text() if hasattr(self, 'author_edit') and self.author_edit.text() else None
            }
            
            # Применяем фильтр по типу
            if hasattr(self, 'type_combo') and self.type_combo.currentData():
                filters['source_type'] = self.type_combo.currentData()
            
            # Применяем фильтр по URL
            if hasattr(self, 'url_filter_combo'):
                if self.url_filter_combo.currentText() == "Только с URL":
                    filters['has_url'] = True
                elif self.url_filter_combo.currentText() == "Только без URL":
                    filters['has_url'] = False
            
            # Применяем сортировку
            if hasattr(self, 'sort_combo'):
                sort_mapping = {
                    "По дате (новые первые)": "date_desc",
                    "По дате (старые первые)": "date_asc",
                    "По названию (А-Я)": "name_asc",
                    "По названию (Я-А)": "name_desc",
                    "По автору (А-Я)": "author_asc",
                    "По типу": "type_asc"
                }
                filters['sort_by'] = sort_mapping.get(self.sort_combo.currentText(), "date_desc")
            
            result = self.source_service.get_sources(self.user_data['user_id'], filters)
            
            self.sources_table.clear()
            self.total_count = result['total_count']
            
            for source in result['sources']:
                # Форматируем дату публикации
                pub_date = ""
                if source.get('publication_date'):
                    pub_date = str(source['publication_date'])
                
                # Проверяем наличие URL
                url_status = "—"
                if source.get('url'):
                    url_status = "✓"
                    if not self.is_valid_url(source['url']):
                        url_status = "⚠"  # Предупреждение о некорректном URL
                
                # Количество связанных событий
                events_count = source.get('events_count', 0)
                events_str = str(events_count) if events_count > 0 else "—"
                
                item = QTreeWidgetItem([
                    str(source['source_id']),
                    source['name'],
                    source.get('author', ''),
                    source.get('type', ''),
                    pub_date,
                    url_status,
                    events_str
                ])
                
                # Цветовое кодирование
                if source.get('url'):
                    if self.is_valid_url(source['url']):
                        item.setForeground(5, QColor(0, 150, 0))  # Зеленый для валидных URL
                    else:
                        item.setForeground(5, QColor(200, 100, 0))  # Оранжевый для сомнительных
                
                # Выделяем источники с большим количеством связей
                if events_count > 5:
                    item.setForeground(6, QColor(0, 120, 200))  # Синий для активно используемых
                
                item.setData(0, Qt.ItemDataRole.UserRole, source)
                self.sources_table.addTopLevelItem(item)
            
            # Обновляем пагинацию
            self.update_pagination()
            
            # Обновляем статистику
            self.update_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def update_statistics(self):
        """Обновление статистики источников"""
        try:
            # Подсчитываем статистику из текущих данных
            sources_with_url = 0
            sources_with_events = 0
            unique_authors = set()
            
            for i in range(self.sources_table.topLevelItemCount()):
                item = self.sources_table.topLevelItem(i)
                source_data = item.data(0, Qt.ItemDataRole.UserRole)
                
                if source_data.get('url'):
                    sources_with_url += 1
                
                if source_data.get('events_count', 0) > 0:
                    sources_with_events += 1
                
                if source_data.get('author'):
                    unique_authors.add(source_data['author'])
            
            stats_text = f"Всего: {self.total_count} | С URL: {sources_with_url} | С событиями: {sources_with_events} | Авторов: {len(unique_authors)}"
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            self.stats_label.setText("Ошибка загрузки статистики")
    
    def is_valid_url(self, url):
        """Простая проверка валидности URL"""
        if not url:
            return False
        
        # Простая проверка формата
        url_pattern = r'^https?://[^\s]+\.[^\s]+$'
        return re.match(url_pattern, url) is not None
    
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
        self.author_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.url_filter_combo.setCurrentIndex(0)
        self.sort_combo.setCurrentIndex(0)
        self.filter_data()
    
    def add_source(self):
        """Добавление нового источника"""
        dialog = SourceDialog(self.user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()  # Обновляем список
    
    def view_source_details(self, item):
        """Просмотр деталей источника"""
        source_data = item.data(0, Qt.ItemDataRole.UserRole)
        if source_data:
            from ui.windows.source_details_window import SourceDetailsWindow
            details_window = SourceDetailsWindow(source_data, self.user_data, self)
            details_window.show()
    
    def show_context_menu(self, position):
        """Показ контекстного меню"""
        item = self.sources_table.itemAt(position)
        if item:
            menu = QMenu(self)
            
            view_action = menu.addAction("Просмотр")
            view_action.triggered.connect(lambda: self.view_source_details(item))
            
            source_data = item.data(0, Qt.ItemDataRole.UserRole)
            
            # Открыть URL, если есть
            if source_data.get('url'):
                open_url_action = menu.addAction("Открыть URL")
                open_url_action.triggered.connect(lambda: self.open_url(source_data['url']))
                
                copy_url_action = menu.addAction("Копировать URL")
                copy_url_action.triggered.connect(lambda: self.copy_url(source_data['url']))
                
                menu.addSeparator()
            
            if self.user_data['role_id'] >= 2:  # Модератор или админ
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self.edit_source(item))
                
                menu.addSeparator()
                
                # Дополнительные действия для админов
                if self.user_data['role_id'] >= 3:
                    validate_url_action = menu.addAction("Проверить URL")
                    validate_url_action.triggered.connect(lambda: self.validate_source_url(item))
            
            menu.exec(self.sources_table.mapToGlobal(position))
    
    def open_url(self, url):
        """Открытие URL в браузере"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть URL: {str(e)}")
    
    def copy_url(self, url):
        """Копирование URL в буфер обмена"""
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        # Показываем сообщение об успехе через родительское окно
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage("URL скопирован в буфер обмена", 2000)
    
    def edit_source(self, item):
        """Редактирование источника"""
        source_data = item.data(0, Qt.ItemDataRole.UserRole)
        if source_data:
            dialog = SourceDialog(self.user_data, source_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def validate_source_url(self, item):
        """Проверка URL источника"""
        source_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not source_data.get('url'):
            QMessageBox.information(self, "Информация", "У источника нет URL для проверки")
            return
        
        url = source_data['url']
        
        # Простая проверка формата
        if self.is_valid_url(url):
            QMessageBox.information(self, "Проверка URL", f"URL имеет корректный формат:\n{url}")
        else:
            QMessageBox.warning(self, "Проверка URL", f"URL имеет некорректный формат:\n{url}")
    
    def check_urls(self):
        """Проверка всех URL источников (для админов)"""
        try:
            url_issues = self.source_service.check_sources_urls(self.user_data['user_id'])
            
            if not url_issues:
                QMessageBox.information(self, "Проверка URL", "Все URL источников корректны!")
                return
            
            # Показываем результаты проверки
            dialog = QDialog(self)
            dialog.setWindowTitle("Результаты проверки URL")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            info_label = QLabel(f"Найдено проблемных URL: {len(url_issues)}")
            info_label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(info_label)
            
            # Таблица с проблемными URL
            issues_table = QTreeWidget()
            issues_table.setHeaderLabels(["Источник", "URL", "Проблема"])
            
            for issue in url_issues:
                item = QTreeWidgetItem([
                    issue.get('name', 'Неизвестно'),
                    issue.get('url', ''),
                    issue.get('issue', 'Неизвестная проблема')
                ])
                issues_table.addTopLevelItem(item)
            
            layout.addWidget(issues_table)
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить URL: {str(e)}")
    
    def find_duplicates(self):
        """Поиск дублирующихся источников (для админов)"""
        try:
            duplicates = self.source_service.find_duplicate_sources(self.user_data['user_id'])
            
            if not duplicates:
                QMessageBox.information(self, "Поиск дублей", "Дублирующиеся источники не найдены!")
                return
            
            # Показываем найденные дубли
            dialog = QDialog(self)
            dialog.setWindowTitle("Дублирующиеся источники")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            info_label = QLabel(f"Найдено потенциальных дублей: {len(duplicates)}")
            info_label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(info_label)
            
            # Список дублей
            duplicates_list = QTreeWidget()
            duplicates_list.setHeaderLabels(["ID 1", "Название 1", "ID 2", "Название 2", "Схожесть"])
            
            for duplicate in duplicates:
                item = QTreeWidgetItem([
                    str(duplicate.get('source_id_1', '')),
                    duplicate.get('name_1', ''),
                    str(duplicate.get('source_id_2', '')),
                    duplicate.get('name_2', ''),
                    f"{duplicate.get('similarity', 0):.1f}%"
                ])
                duplicates_list.addTopLevelItem(item)
            
            layout.addWidget(duplicates_list)
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось найти дубли: {str(e)}")
    
    def refresh(self):
        """Обновление данных"""
        self.load_data()
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.document_service import DocumentService
from ui.pages.base_page import BasePage
from ui.dialogs.document_dialog import DocumentDialog

class DocumentsPage(BasePage):
    def __init__(self, user_data):
        self.document_service = DocumentService()
        super().__init__(user_data)
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок и кнопки
        header_layout = QHBoxLayout()
        
        title = QLabel("Документы")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Кнопка добавления
        self.add_btn = QPushButton("Добавить документ")
        self.add_btn.clicked.connect(self.add_document)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Панель поиска и фильтров
        search_group = QGroupBox("Поиск и фильтры")
        search_layout = QGridLayout(search_group)
        
        # Основной поиск по названию
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию документа...")
        self.search_edit.textChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("Название:"), 0, 0)
        search_layout.addWidget(self.search_edit, 0, 1)
        
        # Поиск по содержимому
        self.content_search_edit = QLineEdit()
        self.content_search_edit.setPlaceholderText("Поиск в тексте документа...")
        self.content_search_edit.textChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("В тексте:"), 0, 2)
        search_layout.addWidget(self.content_search_edit, 0, 3)
        
        # Фильтры по годам создания
        self.year_from_spin = QSpinBox()
        self.year_from_spin.setRange(1, 2100)
        self.year_from_spin.setValue(1000)
        self.year_from_spin.valueChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("Создан с:"), 1, 0)
        search_layout.addWidget(self.year_from_spin, 1, 1)
        
        self.year_to_spin = QSpinBox()
        self.year_to_spin.setRange(1, 2100)
        self.year_to_spin.setValue(2024)
        self.year_to_spin.valueChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("по:"), 1, 2)
        search_layout.addWidget(self.year_to_spin, 1, 3)
        
        # Сортировка
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "По дате (новые первые)",
            "По дате (старые первые)", 
            "По названию (А-Я)",
            "По названию (Я-А)",
            "По размеру (большие первые)",
            "По размеру (маленькие первые)"
        ])
        self.sort_combo.currentTextChanged.connect(self.filter_data)
        search_layout.addWidget(QLabel("Сортировка:"), 2, 0)
        search_layout.addWidget(self.sort_combo, 2, 1)
        
        # Кнопки поиска и сброса
        search_btn = QPushButton("Найти")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn, 2, 2)
        
        reset_btn = QPushButton("Сбросить")
        reset_btn.clicked.connect(self.reset_filters)
        search_layout.addWidget(reset_btn, 2, 3)
        
        layout.addWidget(search_group)
        
        # Результаты поиска (если есть)
        self.search_results_widget = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_widget)
        self.search_results_widget.hide()
        layout.addWidget(self.search_results_widget)
        
        # Таблица документов
        self.documents_table = QTreeWidget()
        self.documents_table.setHeaderLabels([
            "ID", "Название", "Дата создания", "Размер (символов)", "Связи"
        ])
        self.documents_table.itemDoubleClicked.connect(self.view_document_details)
        
        # Настройка колонок
        header = self.documents_table.header()
        header.resizeSection(0, 50)   # ID
        header.resizeSection(1, 300)  # Название
        header.resizeSection(2, 120)  # Дата
        header.resizeSection(3, 120)  # Размер
        header.resizeSection(4, 80)   # Связи
        
        # Контекстное меню
        self.documents_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.documents_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.documents_table)
        
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
        self.is_search_mode = False
    
    def load_data(self):
        """Загрузка данных о документах"""
        try:
            filters = {
                'offset': self.current_page * self.page_size,
                'limit': self.page_size,
                'search_term': self.search_edit.text() if hasattr(self, 'search_edit') and self.search_edit.text() else None,
                'content_search': self.content_search_edit.text() if hasattr(self, 'content_search_edit') and self.content_search_edit.text() else None
            }
            
            # Применяем фильтры по годам
            if hasattr(self, 'year_from_spin'):
                filters['creating_year_from'] = self.year_from_spin.value()
                filters['creating_year_to'] = self.year_to_spin.value()
            
            # Применяем сортировку
            if hasattr(self, 'sort_combo'):
                sort_mapping = {
                    "По дате (новые первые)": "date_desc",
                    "По дате (старые первые)": "date_asc",
                    "По названию (А-Я)": "name_asc",
                    "По названию (Я-А)": "name_desc",
                    "По размеру (большие первые)": "size_desc",
                    "По размеру (маленькие первые)": "size_asc"
                }
                filters['sort_by'] = sort_mapping.get(self.sort_combo.currentText(), "date_desc")
            
            result = self.document_service.get_documents(self.user_data['user_id'], filters)
            
            self.documents_table.clear()
            self.total_count = result['total_count']
            
            for document in result['documents']:
                # Форматируем дату
                date_str = ""
                if document.get('creating_date'):
                    date_str = str(document['creating_date'])
                
                # Форматируем размер
                content_length = document.get('content_length', 0)
                size_str = f"{content_length:,}"
                
                # Информация о связях
                relations_count = document.get('persons_count', 0) + document.get('events_count', 0)
                relations_str = str(relations_count) if relations_count > 0 else "—"
                
                item = QTreeWidgetItem([
                    str(document['document_id']),
                    document['name'],
                    date_str,
                    size_str,
                    relations_str
                ])
                
                # Цветовое кодирование по размеру
                if content_length > 10000:  # Большие документы
                    item.setForeground(3, QColor(0, 120, 0))  # Зеленый
                elif content_length < 1000:  # Маленькие документы
                    item.setForeground(3, QColor(200, 100, 0))  # Оранжевый
                
                item.setData(0, Qt.ItemDataRole.UserRole, document)
                self.documents_table.addTopLevelItem(item)
            
            # Обновляем пагинацию
            self.update_pagination()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def perform_search(self):
        """Выполнение полнотекстового поиска"""
        search_text = self.content_search_edit.text().strip()
        
        if not search_text:
            self.search_results_widget.hide()
            self.is_search_mode = False
            self.filter_data()
            return
        
        try:
            # Выполняем поиск по содержимому
            search_results = self.document_service.search_documents(
                self.user_data['user_id'],
                search_text,
                search_in_content=True,
                limit=50
            )
            
            # Показываем результаты поиска
            self.show_search_results(search_results, search_text)
            self.is_search_mode = True
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", f"Произошла ошибка: {str(e)}")
    
    def show_search_results(self, search_results, search_text):
        """Показ результатов полнотекстового поиска"""
        # Очищаем предыдущие результаты
        for i in reversed(range(self.search_results_layout.count())):
            child = self.search_results_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not search_results['results']:
            self.search_results_widget.hide()
            return
        
        # Заголовок результатов
        results_title = QLabel(f"Результаты поиска по запросу '{search_text}': {search_results['total_count']} найдено")
        results_title.setStyleSheet("font-weight: bold; color: #007acc; margin: 5px;")
        self.search_results_layout.addWidget(results_title)
        
        # Список результатов с фрагментами
        results_scroll = QScrollArea()
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        for doc in search_results['results']:
            # Создаем карточку результата
            result_card = QFrame()
            result_card.setFrameStyle(QFrame.Shape.Box)
            result_card.setStyleSheet("QFrame { border: 1px solid #ccc; margin: 5px; padding: 10px; }")
            
            card_layout = QVBoxLayout(result_card)
            
            # Название документа
            title_label = QLabel(f"<b>{doc['name']}</b>")
            title_label.setStyleSheet("color: #007acc;")
            card_layout.addWidget(title_label)
            
            # Метаданные
            meta_info = f"ID: {doc['document_id']}"
            if doc.get('creating_date'):
                meta_info += f" | Дата: {doc['creating_date']}"
            if doc.get('content_length'):
                meta_info += f" | Размер: {doc['content_length']:,} символов"
            
            meta_label = QLabel(meta_info)
            meta_label.setStyleSheet("color: #666; font-size: 11px;")
            card_layout.addWidget(meta_label)
            
            # Фрагменты текста с выделением
            try:
                snippets = self.document_service.get_document_snippets(
                    self.user_data['user_id'],
                    doc['document_id'],
                    search_text,
                    snippet_count=2,
                    snippet_length=200
                )
                
                for snippet in snippets:
                    snippet_text = snippet.get('snippet', '')
                    # Простое выделение найденных слов
                    for word in search_text.split():
                        snippet_text = snippet_text.replace(word, f"<b style='background-color: #ffff00;'>{word}</b>")
                    
                    snippet_label = QLabel(f"...{snippet_text}...")
                    snippet_label.setWordWrap(True)
                    snippet_label.setStyleSheet("margin: 5px; padding: 5px; background-color: #f9f9f9;")
                    card_layout.addWidget(snippet_label)
            
            except:
                # Если не удалось получить фрагменты, показываем начало содержимого
                content_preview = doc.get('content', '')[:200] + "..."
                preview_label = QLabel(content_preview)
                preview_label.setWordWrap(True)
                preview_label.setStyleSheet("margin: 5px; padding: 5px; background-color: #f9f9f9;")
                card_layout.addWidget(preview_label)
            
            # Кнопка просмотра
            view_btn = QPushButton("Открыть документ")
            view_btn.clicked.connect(lambda checked, d=doc: self.view_document_from_search(d))
            card_layout.addWidget(view_btn)
            
            results_layout.addWidget(result_card)
        
        results_scroll.setWidget(results_widget)
        results_scroll.setMaximumHeight(300)
        self.search_results_layout.addWidget(results_scroll)
        
        self.search_results_widget.show()
    
    def view_document_from_search(self, document_data):
        """Просмотр документа из результатов поиска"""
        from ui.windows.document_details_window import DocumentDetailsWindow
        details_window = DocumentDetailsWindow(document_data, self.user_data, self)
        details_window.show()
    
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
        self.search_results_widget.hide()  # Скрываем результаты поиска
        self.is_search_mode = False
        self.load_data()
    
    def reset_filters(self):
        """Сброс всех фильтров"""
        self.search_edit.clear()
        self.content_search_edit.clear()
        self.year_from_spin.setValue(1000)
        self.year_to_spin.setValue(2024)
        self.sort_combo.setCurrentIndex(0)
        self.filter_data()
    
    def add_document(self):
        """Добавление нового документа"""
        dialog = DocumentDialog(self.user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()  # Обновляем список
    
    def view_document_details(self, item):
        """Просмотр деталей документа"""
        document_data = item.data(0, Qt.ItemDataRole.UserRole)
        if document_data:
            from ui.windows.document_details_window import DocumentDetailsWindow
            details_window = DocumentDetailsWindow(document_data, self.user_data, self)
            details_window.show()
    
    def show_context_menu(self, position):
        """Показ контекстного меню"""
        item = self.documents_table.itemAt(position)
        if item:
            menu = QMenu(self)
            
            view_action = menu.addAction("Просмотр")
            view_action.triggered.connect(lambda: self.view_document_details(item))
            
            if self.user_data['role_id'] >= 2:  # Модератор или админ
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self.edit_document(item))
                
                menu.addSeparator()
                
                # Дополнительные действия
                analyze_action = menu.addAction("Анализ содержимого")
                analyze_action.triggered.connect(lambda: self.analyze_document(item))
                
                export_action = menu.addAction("Экспорт документа")
                export_action.triggered.connect(lambda: self.export_document(item))
            
            menu.exec(self.documents_table.mapToGlobal(position))
    
    def edit_document(self, item):
        """Редактирование документа"""
        document_data = item.data(0, Qt.ItemDataRole.UserRole)
        if document_data:
            dialog = DocumentDialog(self.user_data, document_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
    
    def analyze_document(self, item):
        """Анализ содержимого документа"""
        document_data = item.data(0, Qt.ItemDataRole.UserRole)
        if document_data:
            try:
                content = document_data.get('content', '')
                words_count = len(content.split())
                chars_count = len(content)
                lines_count = len(content.split('\n'))
                
                # Подсчет наиболее частых слов
                words = content.lower().split()
                word_freq = {}
                for word in words:
                    # Простая очистка от знаков препинания
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if len(clean_word) > 3:  # Игнорируем короткие слова
                        word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
                
                # Топ-10 слов
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Создаем диалог с результатами
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Анализ документа: {document_data['name']}")
                dialog.resize(500, 400)
                
                layout = QVBoxLayout(dialog)
                
                analysis_text = QTextEdit()
                analysis_text.setReadOnly(True)
                
                analysis_content = f"""
Анализ документа: {document_data['name']}
{'=' * 50}

Основная статистика:
• Количество символов: {chars_count:,}
• Количество слов: {words_count:,}
• Количество строк: {lines_count:,}
• Средняя длина слова: {chars_count/max(words_count, 1):.1f} символов

Наиболее частые слова:
"""
                
                for i, (word, count) in enumerate(top_words, 1):
                    analysis_content += f"{i:2}. {word} ({count} раз)\n"
                
                analysis_text.setPlainText(analysis_content)
                layout.addWidget(analysis_text)
                
                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.exec()
                
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось проанализировать документ: {str(e)}")
    
    def export_document(self, item):
        """Экспорт документа"""
        document_data = item.data(0, Qt.ItemDataRole.UserRole)
        if document_data:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить документ",
                f"{document_data['name'].replace(' ', '_')}.txt",
                "Text files (*.txt);;HTML files (*.html)"
            )
            
            if filename:
                try:
                    content = document_data.get('content', '')
                    
                    if filename.endswith('.html'):
                        # Экспорт в HTML
                        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{document_data['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; font-style: italic; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{document_data['name']}</h1>
    <div class="meta">
        Дата создания: {document_data.get('creating_date', 'Не указана')}<br>
        Размер: {len(content):,} символов
    </div>
    <div>
        {content.replace('\n', '<br>')}
    </div>
</body>
</html>
                        """
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                    else:
                        # Экспорт в текстовый файл
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"{document_data['name']}\n")
                            f.write("=" * len(document_data['name']) + "\n\n")
                            if document_data.get('creating_date'):
                                f.write(f"Дата создания: {document_data['creating_date']}\n\n")
                            f.write(content)
                    
                    QMessageBox.information(self, "Успех", f"Документ сохранен в файл:\n{filename}")
                
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def refresh(self):
        """Обновление данных"""
        if self.is_search_mode:
            self.perform_search()
        else:
            self.load_data()
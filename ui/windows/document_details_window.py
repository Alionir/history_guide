# ui/windows/document_details_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from services.document_service import DocumentService
from services.relationship_service import RelationshipService

class DocumentDetailsWindow(QMainWindow):
    def __init__(self, document_data, user_data, parent=None):
        super().__init__(parent)
        self.document_data = document_data
        self.user_data = user_data
        self.document_service = DocumentService()
        self.relationship_service = RelationshipService()
        self.setup_ui()
        self.load_full_data()
    
    def setup_ui(self):
        self.setWindowTitle(f"Документ: {self.document_data['name']}")
        self.resize(1000, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        
        # Левая панель - содержимое документа
        left_panel = self.create_content_panel()
        main_splitter.addWidget(left_panel)
        
        # Правая панель - метаданные и связи
        right_panel = self.create_metadata_panel()
        main_splitter.addWidget(right_panel)
        
        # Настройка пропорций
        main_splitter.setStretchFactor(0, 3)  # Содержимое занимает больше места
        main_splitter.setStretchFactor(1, 1)  # Метаданные
        
        # Создаем меню и тулбар
        self.create_menus()
        self.create_toolbar()
        
        # Статус бар
        self.create_status_bar()
    
    def create_content_panel(self):
        """Создание панели содержимого документа"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Заголовок документа
        title_layout = QHBoxLayout()
        
        title_label = QLabel(self.document_data['name'])
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title_label.setWordWrap(True)
        title_layout.addWidget(title_label)
        
        # Кнопки быстрых действий
        if self.user_data['role_id'] >= 2:
            edit_btn = QPushButton("Редактировать")
            edit_btn.clicked.connect(self.edit_document)
            title_layout.addWidget(edit_btn)
        
        layout.addLayout(title_layout)
        
        # Панель инструментов для работы с текстом
        text_tools_layout = QHBoxLayout()
        
        # Поиск в тексте
        self.text_search = QLineEdit()
        self.text_search.setPlaceholderText("Поиск в тексте...")
        self.text_search.returnPressed.connect(self.search_in_text)
        text_tools_layout.addWidget(QLabel("Поиск:"))
        text_tools_layout.addWidget(self.text_search)
        
        search_btn = QPushButton("Найти")
        search_btn.clicked.connect(self.search_in_text)
        text_tools_layout.addWidget(search_btn)
        
        # Кнопки навигации по найденному
        self.prev_match_btn = QPushButton("◀")
        self.prev_match_btn.setMaximumWidth(30)
        self.prev_match_btn.clicked.connect(self.prev_match)
        self.prev_match_btn.setEnabled(False)
        text_tools_layout.addWidget(self.prev_match_btn)
        
        self.next_match_btn = QPushButton("▶")
        self.next_match_btn.setMaximumWidth(30)
        self.next_match_btn.clicked.connect(self.next_match)
        self.next_match_btn.setEnabled(False)
        text_tools_layout.addWidget(self.next_match_btn)
        
        # Счетчик совпадений
        self.matches_label = QLabel("")
        text_tools_layout.addWidget(self.matches_label)
        
        text_tools_layout.addStretch()
        
        # Размер шрифта
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Размер:"))
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(11)
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        font_size_layout.addWidget(self.font_size_spin)
        
        text_tools_layout.addLayout(font_size_layout)
        
        layout.addLayout(text_tools_layout)
        
        # Содержимое документа
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        content = self.document_data.get('content', 'Содержимое не загружено')
        self.content_text.setPlainText(content)
        
        # Настройка шрифта
        font = self.content_text.font()
        font.setFamily("Georgia, serif")
        font.setPointSize(11)
        self.content_text.setFont(font)
        
        layout.addWidget(self.content_text)
        
        # Переменные для поиска
        self.current_matches = []
        self.current_match_index = -1
        
        return widget
    
    def create_metadata_panel(self):
        """Создание панели метаданных и связей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Основные метаданные
        metadata_group = QGroupBox("Информация о документе")
        metadata_layout = QFormLayout(metadata_group)
        
        metadata_layout.addRow("ID:", QLabel(str(self.document_data['document_id'])))
        metadata_layout.addRow("Название:", QLabel(self.document_data['name']))
        
        # Дата создания
        date_str = str(self.document_data.get('creating_date', 'Не указана'))
        metadata_layout.addRow("Дата создания:", QLabel(date_str))
        
        # Статистика
        content = self.document_data.get('content', '')
        chars_count = len(content)
        words_count = len(content.split())
        lines_count = len(content.split('\n'))
        
        metadata_layout.addRow("Символов:", QLabel(f"{chars_count:,}"))
        metadata_layout.addRow("Слов:", QLabel(f"{words_count:,}"))
        metadata_layout.addRow("Строк:", QLabel(f"{lines_count:,}"))
        
        # Время чтения (примерно 200 слов в минуту)
        reading_time = max(1, words_count // 200)
        metadata_layout.addRow("Время чтения:", QLabel(f"~{reading_time} мин"))
        
        layout.addWidget(metadata_group)
        
        # Связи
        relations_group = QGroupBox("Связи")
        relations_layout = QVBoxLayout(relations_group)
        
        self.persons_count_label = QLabel("Персоны: загрузка...")
        self.events_count_label = QLabel("События: загрузка...")
        
        relations_layout.addWidget(self.persons_count_label)
        relations_layout.addWidget(self.events_count_label)
        
        if self.user_data['role_id'] >= 2:
            manage_relations_btn = QPushButton("Управлять связями")
            manage_relations_btn.clicked.connect(self.manage_relationships)
            relations_layout.addWidget(manage_relations_btn)
        
        layout.addWidget(relations_group)
        
        # Связанные персоны
        persons_group = QGroupBox("Связанные персоны")
        persons_layout = QVBoxLayout(persons_group)
        
        self.persons_list = QListWidget()
        self.persons_list.itemDoubleClicked.connect(self.view_person_details)
        self.persons_list.setMaximumHeight(120)
        persons_layout.addWidget(self.persons_list)
        
        layout.addWidget(persons_group)
        
        # Связанные события
        events_group = QGroupBox("Связанные события")
        events_layout = QVBoxLayout(events_group)
        
        self.events_list = QListWidget()
        self.events_list.itemDoubleClicked.connect(self.view_event_details)
        self.events_list.setMaximumHeight(120)
        events_layout.addWidget(self.events_list)
        
        layout.addWidget(events_group)
        
        # Анализ содержимого
        analysis_group = QGroupBox("Анализ")
        analysis_layout = QVBoxLayout(analysis_group)
        
        analyze_btn = QPushButton("Анализировать содержимое")
        analyze_btn.clicked.connect(self.analyze_content)
        analysis_layout.addWidget(analyze_btn)
        
        word_cloud_btn = QPushButton("Облако слов")
        word_cloud_btn.clicked.connect(self.show_word_cloud)
        analysis_layout.addWidget(word_cloud_btn)
        
        layout.addWidget(analysis_group)
        
        layout.addStretch()
        
        return widget
    
    def create_menus(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu('Файл')
        
        export_txt_action = file_menu.addAction('Экспорт в TXT', lambda: self.export_document('txt'))
        export_txt_action.setShortcut('Ctrl+S')
        
        export_html_action = file_menu.addAction('Экспорт в HTML', lambda: self.export_document('html'))
        
        file_menu.addSeparator()
        
        print_action = file_menu.addAction('Печать', self.print_document)
        print_action.setShortcut('Ctrl+P')
        
        file_menu.addSeparator()
        
        close_action = file_menu.addAction('Закрыть', self.close)
        close_action.setShortcut('Ctrl+W')
        
        # Правка
        edit_menu = menubar.addMenu('Правка')
        
        if self.user_data['role_id'] >= 2:
            edit_doc_action = edit_menu.addAction('Редактировать документ', self.edit_document)
            edit_doc_action.setShortcut('Ctrl+E')
            edit_menu.addSeparator()
        
        find_action = edit_menu.addAction('Найти в тексте', self.focus_search)
        find_action.setShortcut('Ctrl+F')
        
        select_all_action = edit_menu.addAction('Выделить всё', self.content_text.selectAll)
        select_all_action.setShortcut('Ctrl+A')
        
        copy_action = edit_menu.addAction('Копировать', self.content_text.copy)
        copy_action.setShortcut('Ctrl+C')
        
        # Просмотр
        view_menu = menubar.addMenu('Просмотр')
        
        increase_font_action = view_menu.addAction('Увеличить шрифт', self.increase_font)
        increase_font_action.setShortcut('Ctrl++')
        
        decrease_font_action = view_menu.addAction('Уменьшить шрифт', self.decrease_font)
        decrease_font_action.setShortcut('Ctrl+-')
        
        view_menu.addSeparator()
        
        refresh_action = view_menu.addAction('Обновить', self.load_full_data)
        refresh_action.setShortcut('F5')
        
        # Инструменты
        tools_menu = menubar.addMenu('Инструменты')
        
        analyze_action = tools_menu.addAction('Анализ содержимого', self.analyze_content)
        word_cloud_action = tools_menu.addAction('Облако слов', self.show_word_cloud)
        
        if self.user_data['role_id'] >= 2:
            tools_menu.addSeparator()
            manage_relations_action = tools_menu.addAction('Управление связями', self.manage_relationships)
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar('Основное')
        
        if self.user_data['role_id'] >= 2:
            edit_action = QAction('Редактировать', self)
            edit_action.triggered.connect(self.edit_document)
            toolbar.addAction(edit_action)
            toolbar.addSeparator()
        
        # Поиск
        find_action = QAction('Найти', self)
        find_action.triggered.connect(self.focus_search)
        toolbar.addAction(find_action)
        
        toolbar.addSeparator()
        
        # Экспорт
        export_action = QAction('Экспорт', self)
        export_action.triggered.connect(lambda: self.export_document('txt'))
        toolbar.addAction(export_action)
        
        # Печать
        print_action = QAction('Печать', self)
        print_action.triggered.connect(self.print_document)
        toolbar.addAction(print_action)
        
        toolbar.addSeparator()
        
        # Анализ
        analyze_action = QAction('Анализ', self)
        analyze_action.triggered.connect(self.analyze_content)
        toolbar.addAction(analyze_action)
        
        toolbar.addSeparator()
        
        # Обновить
        refresh_action = QAction('Обновить', self)
        refresh_action.triggered.connect(self.load_full_data)
        toolbar.addAction(refresh_action)
    
    def create_status_bar(self):
        """Создание статус бара"""
        self.status_bar = self.statusBar()
        
        # Информация о позиции курсора
        self.cursor_info = QLabel("Строка: 1, Колонка: 1")
        self.status_bar.addWidget(self.cursor_info)
        
        self.status_bar.addPermanentWidget(QLabel(f"Размер: {len(self.document_data.get('content', '')):,} символов"))
        
        # Отслеживание позиции курсора
        self.content_text.cursorPositionChanged.connect(self.update_cursor_info)
    
    def load_full_data(self):
        """Загрузка полных данных документа"""
        try:
            details = self.document_service.get_document_details(
                self.user_data['user_id'],
                self.document_data['document_id']
            )
            
            self.document_data.update(details['document'])
            
            # Обновляем содержимое
            content = self.document_data.get('content', '')
            self.content_text.setPlainText(content)
            
            # Обновляем статистику связей
            relationships = details['relationships_summary']['relationships']
            self.persons_count_label.setText(f"Персоны: {relationships.get('persons', 0)}")
            self.events_count_label.setText(f"События: {relationships.get('events', 0)}")
            
            # Загружаем связанные персоны
            self.persons_list.clear()
            for person in details['related_persons']:
                full_name = person.get('full_name', person['name'])
                item = QListWidgetItem(full_name)
                item.setData(Qt.ItemDataRole.UserRole, person)
                self.persons_list.addItem(item)
            
            # Загружаем связанные события
            self.events_list.clear()
            for event in details['related_events']:
                event_name = event['name']
                if event.get('start_date'):
                    year = str(event['start_date']).split('-')[0]
                    event_name += f" ({year})"
                
                item = QListWidgetItem(event_name)
                item.setData(Qt.ItemDataRole.UserRole, event)
                self.events_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def search_in_text(self):
        """Поиск в тексте документа"""
        search_text = self.text_search.text().strip()
        if not search_text:
            self.clear_search_highlights()
            return
        
        # Очищаем предыдущие результаты
        self.clear_search_highlights()
        
        # Выполняем поиск
        document = self.content_text.document()
        self.current_matches = []
        
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        
        # Формат выделения
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 255, 0, 100))  # Желтый с прозрачностью
        
        # Ищем все вхождения
        search_cursor = document.find(search_text)
        while not search_cursor.isNull():
            self.current_matches.append(search_cursor.position())
            search_cursor.setCharFormat(highlight_format)
            search_cursor = document.find(search_text, search_cursor)
        
        cursor.endEditBlock()
        
        # Обновляем UI
        if self.current_matches:
            self.current_match_index = 0
            self.matches_label.setText(f"1 из {len(self.current_matches)}")
            self.prev_match_btn.setEnabled(True)
            self.next_match_btn.setEnabled(True)
            self.goto_match(0)
        else:
            self.matches_label.setText("Не найдено")
            self.prev_match_btn.setEnabled(False)
            self.next_match_btn.setEnabled(False)
    
    def clear_search_highlights(self):
        """Очистка выделения поиска"""
        cursor = QTextCursor(self.content_text.document())
        cursor.select(QTextCursor.SelectionType.Document)
        
        # Сброс форматирования
        format = QTextCharFormat()
        cursor.setCharFormat(format)
        
        self.current_matches = []
        self.current_match_index = -1
        self.matches_label.setText("")
        self.prev_match_btn.setEnabled(False)
        self.next_match_btn.setEnabled(False)
    
    def prev_match(self):
        """Переход к предыдущему совпадению"""
        if self.current_matches and self.current_match_index > 0:
            self.current_match_index -= 1
            self.goto_match(self.current_match_index)
            self.matches_label.setText(f"{self.current_match_index + 1} из {len(self.current_matches)}")
    
    def next_match(self):
        """Переход к следующему совпадению"""
        if self.current_matches and self.current_match_index < len(self.current_matches) - 1:
            self.current_match_index += 1
            self.goto_match(self.current_match_index)
            self.matches_label.setText(f"{self.current_match_index + 1} из {len(self.current_matches)}")
    
    def goto_match(self, index):
        """Переход к конкретному совпадению"""
        if 0 <= index < len(self.current_matches):
            cursor = self.content_text.textCursor()
            cursor.setPosition(self.current_matches[index])
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(self.text_search.text()))
            self.content_text.setTextCursor(cursor)
            self.content_text.ensureCursorVisible()
    
    def focus_search(self):
        """Фокус на поле поиска"""
        self.text_search.setFocus()
        self.text_search.selectAll()
    
    def change_font_size(self, size):
        """Изменение размера шрифта"""
        font = self.content_text.font()
        font.setPointSize(size)
        self.content_text.setFont(font)
    
    def increase_font(self):
        """Увеличение размера шрифта"""
        current_size = self.font_size_spin.value()
        if current_size < 24:
            self.font_size_spin.setValue(current_size + 1)
    
    def decrease_font(self):
        """Уменьшение размера шрифта"""
        current_size = self.font_size_spin.value()
        if current_size > 8:
            self.font_size_spin.setValue(current_size - 1)
    
    def update_cursor_info(self):
        """Обновление информации о позиции курсора"""
        cursor = self.content_text.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursor_info.setText(f"Строка: {line}, Колонка: {column}")
    
    def edit_document(self):
        """Редактирование документа"""
        from ui.dialogs.document_dialog import DocumentDialog
        dialog = DocumentDialog(self.user_data, self.document_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_full_data()
    
    def manage_relationships(self):
        """Управление связями документа"""
        from ui.dialogs.relationship_dialog import RelationshipDialog
        dialog = RelationshipDialog(
            self.user_data,
            'DOCUMENT',
            self.document_data['document_id'],
            self.document_data['name'],
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_full_data()
    
    def export_document(self, format_type):
        """Экспорт документа"""
        if format_type == 'txt':
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить документ",
                f"{self.document_data['name'].replace(' ', '_')}.txt",
                "Text files (*.txt)"
            )
        else:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить документ",
                f"{self.document_data['name'].replace(' ', '_')}.html",
                "HTML files (*.html)"
            )
        
        if filename:
            try:
                content = self.document_data.get('content', '')
                
                if format_type == 'html':
                    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{self.document_data['name']}</title>
    <style>
        body {{ 
            font-family: Georgia, serif; 
            margin: 40px; 
            line-height: 1.6; 
            max-width: 800px;
        }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; }}
        .metadata {{ 
            background-color: #f5f5f5; 
            padding: 15px; 
            margin: 20px 0; 
            border-left: 4px solid #007acc;
        }}
        .content {{ 
            text-align: justify; 
            white-space: pre-line;
        }}
    </style>
</head>
<body>
    <h1>{self.document_data['name']}</h1>
    
    <div class="metadata">
        <strong>Дата создания:</strong> {self.document_data.get('creating_date', 'Не указана')}<br>
        <strong>Размер:</strong> {len(content):,} символов<br>
        <strong>Слов:</strong> {len(content.split()):,}<br>
        <strong>Экспортировано:</strong> {QDateTime.currentDateTime().toString()}
    </div>
    
    <div class="content">
        {content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}
    </div>
</body>
</html>
                    """
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"{self.document_data['name']}\n")
                        f.write("=" * len(self.document_data['name']) + "\n\n")
                        if self.document_data.get('creating_date'):
                            f.write(f"Дата создания: {self.document_data['creating_date']}\n")
                        f.write(f"Размер: {len(content):,} символов\n\n")
                        f.write(content)
                
                QMessageBox.information(self, "Успех", f"Документ сохранен в файл:\n{filename}")
            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def print_document(self):
        """Печать документа"""
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # Создаем HTML для печати
            html_content = f"""
            <h1>{self.document_data['name']}</h1>
            <p><i>Дата создания: {self.document_data.get('creating_date', 'Не указана')}</i></p>
            <hr>
            <div style="white-space: pre-line; font-family: serif;">{self.document_data.get('content', '')}</div>
            """
            
            text_document = QTextDocument()
            text_document.setHtml(html_content)
            text_document.print(printer)
    
    def analyze_content(self):
        """Анализ содержимого документа"""
        try:
            content = self.document_data.get('content', '')
            if not content:
                QMessageBox.warning(self, "Предупреждение", "Документ пуст")
                return
            
            # Базовая статистика
            chars_count = len(content)
            words = content.split()
            words_count = len(words)
            lines_count = len(content.split('\n'))
            
            # Анализ слов
            word_freq = {}
            for word in words:
                clean_word = ''.join(c.lower() for c in word if c.isalnum())
                if len(clean_word) > 3:
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
            
            # Топ-20 слов
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            # Анализ предложений
            sentences = [s.strip() for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
            
            # Создаем окно с результатами
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Анализ: {self.document_data['name']}")
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Вкладки анализа
            tabs = QTabWidget()
            
            # Вкладка основной статистики
            stats_widget = QTextEdit()
            stats_widget.setReadOnly(True)
            stats_content = f"""
АНАЛИЗ ДОКУМЕНТА: {self.document_data['name']}
{'=' * 60}

ОСНОВНАЯ СТАТИСТИКА:
• Количество символов: {chars_count:,}
• Количество слов: {words_count:,}
• Количество строк: {lines_count:,}
• Количество предложений: {len(sentences):,}
• Средняя длина слова: {chars_count/max(words_count, 1):.1f} символов
• Средняя длина предложения: {avg_sentence_length:.1f} слов
• Время чтения (200 слов/мин): {max(1, words_count // 200)} минут

СТРУКТУРНЫЙ АНАЛИЗ:
• Абзацев: {len([p for p in content.split('\n\n') if p.strip()]):,}
• Пустых строк: {content.count('\n\n'):,}
• Символов без пробелов: {len(content.replace(' ', '')):,}
            """
            stats_widget.setPlainText(stats_content)
            tabs.addTab(stats_widget, "Статистика")
            
            # Вкладка частотности слов
            words_widget = QTextEdit()
            words_widget.setReadOnly(True)
            words_content = "НАИБОЛЕЕ ЧАСТЫЕ СЛОВА:\n" + "=" * 30 + "\n\n"
            for i, (word, count) in enumerate(top_words, 1):
                percentage = (count / words_count) * 100
                words_content += f"{i:2}. {word:15} — {count:4} раз ({percentage:.1f}%)\n"
            words_widget.setPlainText(words_content)
            tabs.addTab(words_widget, "Частотность")
            
            # Вкладка сложности текста
            complexity_widget = QTextEdit()
            complexity_widget.setReadOnly(True)
            
            # Простая оценка сложности
            avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
            complexity_score = (avg_word_length * 0.4) + (avg_sentence_length * 0.6)
            
            if complexity_score < 8:
                complexity_level = "Простой"
            elif complexity_score < 12:
                complexity_level = "Средний"
            else:
                complexity_level = "Сложный"
            
            complexity_content = f"""
АНАЛИЗ СЛОЖНОСТИ ТЕКСТА:
{'=' * 30}

• Средняя длина слова: {avg_word_length:.1f} символов
• Средняя длина предложения: {avg_sentence_length:.1f} слов
• Оценка сложности: {complexity_score:.1f} баллов
• Уровень сложности: {complexity_level}

РЕКОМЕНДАЦИИ:
"""
            if complexity_score > 12:
                complexity_content += "• Текст довольно сложный для восприятия\n"
                complexity_content += "• Рекомендуется упростить структуру предложений\n"
            elif complexity_score < 6:
                complexity_content += "• Текст очень простой\n"
                complexity_content += "• Можно использовать более разнообразную лексику\n"
            else:
                complexity_content += "• Текст имеет оптимальную сложность\n"
                complexity_content += "• Хорошо сбалансирован для чтения\n"
            
            complexity_widget.setPlainText(complexity_content)
            tabs.addTab(complexity_widget, "Сложность")
            
            layout.addWidget(tabs)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            export_analysis_btn = QPushButton("Экспорт анализа")
            export_analysis_btn.clicked.connect(lambda: self.export_analysis(stats_content, words_content, complexity_content))
            buttons_layout.addWidget(export_analysis_btn)
            
            buttons_layout.addStretch()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось проанализировать документ: {str(e)}")
    
    def export_analysis(self, stats_content, words_content, complexity_content):
        """Экспорт результатов анализа"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить анализ",
            f"analysis_{self.document_data['name'].replace(' ', '_')}.txt",
            "Text files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(stats_content)
                    f.write("\n\n")
                    f.write(words_content)
                    f.write("\n\n")
                    f.write(complexity_content)
                
                QMessageBox.information(self, "Успех", f"Анализ сохранен в файл:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def show_word_cloud(self):
        """Показ облака слов (упрощенная версия)"""
        try:
            content = self.document_data.get('content', '')
            words = content.split()
            
            # Подсчет частотности
            word_freq = {}
            for word in words:
                clean_word = ''.join(c.lower() for c in word if c.isalnum())
                if len(clean_word) > 3:
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
            
            # Топ-50 слов
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
            
            if not top_words:
                QMessageBox.warning(self, "Предупреждение", "Недостаточно слов для создания облака")
                return
            
            # Создаем простое текстовое облако
            dialog = QDialog(self)
            dialog.setWindowTitle("Облако слов")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Инструкция
            info_label = QLabel("Размер слова соответствует частоте его использования в тексте")
            info_label.setStyleSheet("font-style: italic; margin: 10px;")
            layout.addWidget(info_label)
            
            # Облако слов
            cloud_widget = QTextEdit()
            cloud_widget.setReadOnly(True)
            
            # Создаем HTML облако с разными размерами шрифтов
            max_freq = top_words[0][1] if top_words else 1
            html_content = "<div style='text-align: center; line-height: 1.8;'>"
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
            
            for i, (word, freq) in enumerate(top_words):
                # Размер шрифта от 12 до 36 пикселей
                font_size = 12 + int((freq / max_freq) * 24)
                color = colors[i % len(colors)]
                
                html_content += f"""
                <span style='font-size: {font_size}px; color: {color}; margin: 5px; 
                            font-weight: bold; display: inline-block;'>
                    {word}
                </span>
                """
            
            html_content += "</div>"
            cloud_widget.setHtml(html_content)
            layout.addWidget(cloud_widget)
            
            # Статистика
            stats_label = QLabel(f"Показано {len(top_words)} наиболее частых слов из {len(word_freq)} уникальных")
            stats_label.setStyleSheet("margin: 10px; font-size: 12px; color: #666;")
            layout.addWidget(stats_label)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            save_cloud_btn = QPushButton("Сохранить облако")
            save_cloud_btn.clicked.connect(lambda: self.save_word_cloud(html_content))
            buttons_layout.addWidget(save_cloud_btn)
            
            buttons_layout.addStretch()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать облако слов: {str(e)}")
    
    def save_word_cloud(self, html_content):
        """Сохранение облака слов"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить облако слов",
            f"wordcloud_{self.document_data['name'].replace(' ', '_')}.html",
            "HTML files (*.html)"
        )
        
        if filename:
            try:
                full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Облако слов: {self.document_data['name']}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}
        h1 {{ text-align: center; color: #333; }}
        .container {{ 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Облако слов: {self.document_data['name']}</h1>
        {html_content}
        <p style='text-align: center; margin-top: 30px; color: #666; font-style: italic;'>
            Создано: {QDateTime.currentDateTime().toString()}
        </p>
    </div>
</body>
</html>
                """
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                
                QMessageBox.information(self, "Успех", f"Облако слов сохранено в файл:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def view_person_details(self, item):
        """Просмотр деталей персоны"""
        person_data = item.data(Qt.ItemDataRole.UserRole)
        if person_data:
            from ui.windows.person_details_window import PersonDetailsWindow
            details_window = PersonDetailsWindow(person_data, self.user_data, self)
            details_window.show()
    
    def view_event_details(self, item):
        """Просмотр деталей события"""
        event_data = item.data(Qt.ItemDataRole.UserRole)
        if event_data:
            from ui.windows.event_details_window import EventDetailsWindow
            details_window = EventDetailsWindow(event_data, self.user_data, self)
            details_window.show()
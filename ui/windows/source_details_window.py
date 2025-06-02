# ui/windows/source_details_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.source_service import SourceService
from services.relationship_service import RelationshipService
import re
from urllib.parse import urlparse

class SourceDetailsWindow(QMainWindow):
    def __init__(self, source_data, user_data, parent=None):
        super().__init__(parent)
        self.source_data = source_data
        self.user_data = user_data
        self.source_service = SourceService()
        self.relationship_service = RelationshipService()
        self.setup_ui()
        self.load_full_data()
    
    def setup_ui(self):
        self.setWindowTitle(f"Источник: {self.source_data['name']}")
        self.resize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель - основная информация
        left_panel = self.create_info_panel()
        main_layout.addWidget(left_panel, 2)
        
        # Правая панель - связи и дополнительная информация
        right_panel = self.create_relations_panel()
        main_layout.addWidget(right_panel, 1)
        
        # Создаем меню и тулбар
        self.create_menus()
        self.create_toolbar() 
        
        # Статус бар
        self.create_status_bar()
    
    def create_info_panel(self):
        """Создание панели основной информации"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Заголовок с названием источника
        title_layout = QHBoxLayout()
        
        name_label = QLabel(self.source_data['name'])
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        name_label.setWordWrap(True)
        title_layout.addWidget(name_label)
        
        # Кнопки быстрых действий
        if self.source_data.get('url'):
            open_url_btn = QPushButton("Открыть URL")
            open_url_btn.clicked.connect(self.open_url)
            title_layout.addWidget(open_url_btn)
        
        if self.user_data['role_id'] >= 2:
            edit_btn = QPushButton("Редактировать")
            edit_btn.clicked.connect(self.edit_source)
            title_layout.addWidget(edit_btn)
        
        layout.addLayout(title_layout)
        
        # Основная информация
        info_group = QGroupBox("Основная информация")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("ID:", QLabel(str(self.source_data['source_id'])))
        info_layout.addRow("Название:", QLabel(self.source_data['name']))
        
        # Автор
        author_text = self.source_data.get('author', 'Не указан')
        author_label = QLabel(author_text)
        if author_text != 'Не указан':
            author_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Автор:", author_label)
        
        # Тип источника
        source_type = self.source_data.get('type', 'Не указан')
        type_label = QLabel(source_type)
        info_layout.addRow("Тип:", type_label)
        
        # Дата публикации
        pub_date = str(self.source_data.get('publication_date', 'Не указана'))
        date_label = QLabel(pub_date)
        info_layout.addRow("Дата публикации:", date_label)
        
        layout.addWidget(info_group)
        
        # Информация об URL
        if self.source_data.get('url'):
            url_group = QGroupBox("Веб-ресурс")
            url_layout = QVBoxLayout(url_group)
            
            # URL
            url_text = QTextEdit()
            url_text.setMaximumHeight(60)
            url_text.setReadOnly(True)
            url_text.setPlainText(self.source_data['url'])
            url_layout.addWidget(url_text)
            
            # Анализ URL
            url_analysis = self.analyze_url(self.source_data['url'])
            
            analysis_layout = QGridLayout()
            analysis_layout.addWidget(QLabel("Домен:"), 0, 0)
            analysis_layout.addWidget(QLabel(url_analysis['domain']), 0, 1)
            
            analysis_layout.addWidget(QLabel("Протокол:"), 1, 0)
            protocol_label = QLabel(url_analysis['protocol'])
            if url_analysis['protocol'] == 'https':
                protocol_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                protocol_label.setStyleSheet("color: orange;")
            analysis_layout.addWidget(protocol_label, 1, 1)
            
            analysis_layout.addWidget(QLabel("Статус:"), 2, 0)
            status_label = QLabel(url_analysis['status'])
            if url_analysis['status'] == 'Корректный':
                status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                status_label.setStyleSheet("color: red;")
            analysis_layout.addWidget(status_label, 2, 1)
            
            url_layout.addLayout(analysis_layout)
            
            # Кнопки для работы с URL
            url_buttons_layout = QHBoxLayout()
            
            open_btn = QPushButton("Открыть в браузере")
            open_btn.clicked.connect(self.open_url)
            url_buttons_layout.addWidget(open_btn)
            
            copy_btn = QPushButton("Копировать URL")
            copy_btn.clicked.connect(self.copy_url)
            url_buttons_layout.addWidget(copy_btn)
            
            if self.user_data['role_id'] >= 3:  # Админ
                validate_btn = QPushButton("Проверить доступность")
                validate_btn.clicked.connect(self.validate_url)
                url_buttons_layout.addWidget(validate_btn)
            
            url_layout.addLayout(url_buttons_layout)
            layout.addWidget(url_group)
        
        # Дополнительная информация
        additional_group = QGroupBox("Дополнительная информация")
        additional_layout = QVBoxLayout(additional_group)
        
        # Возраст источника
        if self.source_data.get('publication_date'):
            try:
                from datetime import date
                pub_year = int(str(self.source_data['publication_date']).split('-')[0])
                current_year = date.today().year
                age = current_year - pub_year
                
                age_label = QLabel(f"Возраст: {age} лет")
                additional_layout.addWidget(age_label)
                
                # Историческая эпоха
                epoch = self.determine_historical_epoch(pub_year)
                epoch_label = QLabel(f"Эпоха: {epoch}")
                additional_layout.addWidget(epoch_label)
            except:
                pass
        
        # Категория достоверности
        reliability = self.assess_reliability()
        reliability_label = QLabel(f"Оценка достоверности: {reliability}")
        if reliability in ["Высокая", "Очень высокая"]:
            reliability_label.setStyleSheet("color: green; font-weight: bold;")
        elif reliability == "Средняя":
            reliability_label.setStyleSheet("color: orange;")
        else:
            reliability_label.setStyleSheet("color: red;")
        additional_layout.addWidget(reliability_label)
        
        layout.addWidget(additional_group)
        
        return widget
    
    def create_menus(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu('Файл')
        
        if self.source_data.get('url'):
            open_url_action = file_menu.addAction('Открыть URL', self.open_url)
            open_url_action.setShortcut('Ctrl+O')
            file_menu.addSeparator()
        
        export_menu = file_menu.addMenu('Экспорт')
        export_menu.addAction('BibTeX', self.export_bibtex)
        export_menu.addAction('RIS', self.export_ris)
        export_menu.addAction('Цитирование', self.generate_citation)
        
        file_menu.addSeparator()
        close_action = file_menu.addAction('Закрыть', self.close)
        close_action.setShortcut('Ctrl+W')
        
        # Правка
        edit_menu = menubar.addMenu('Правка')
        
        if self.user_data['role_id'] >= 2:
            edit_source_action = edit_menu.addAction('Редактировать источник', self.edit_source)
            edit_source_action.setShortcut('Ctrl+E')
            edit_menu.addSeparator()
        
        if self.source_data.get('url'):
            copy_url_action = edit_menu.addAction('Копировать URL', self.copy_url)
            copy_url_action.setShortcut('Ctrl+C')
        
        # Просмотр
        view_menu = menubar.addMenu('Просмотр')
        
        refresh_action = view_menu.addAction('Обновить', self.load_full_data)
        refresh_action.setShortcut('F5')
        view_menu.addSeparator()
        
        view_menu.addAction('Другие работы автора', self.show_author_works)
        view_menu.addAction('Похожие источники', self.find_similar_sources)
        
        # Инструменты
        tools_menu = menubar.addMenu('Инструменты')
        
        if self.source_data.get('url') and self.user_data['role_id'] >= 3:
            tools_menu.addAction('Проверить URL', self.validate_url)
        
        if self.user_data['role_id'] >= 2:
            tools_menu.addAction('Управление связями', self.manage_relationships)
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar('Основное')
        
        if self.source_data.get('url'):
            open_url_action = QAction('Открыть URL', self)
            open_url_action.triggered.connect(self.open_url)
            toolbar.addAction(open_url_action)
            toolbar.addSeparator()
        
        if self.user_data['role_id'] >= 2:
            edit_action = QAction('Редактировать', self)
            edit_action.triggered.connect(self.edit_source)
            toolbar.addAction(edit_action)
            toolbar.addSeparator()
        
        citation_action = QAction('Цитирование', self)
        citation_action.triggered.connect(self.generate_citation)
        toolbar.addAction(citation_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction('Обновить', self)
        refresh_action.triggered.connect(self.load_full_data)
        toolbar.addAction(refresh_action)
    
    def create_status_bar(self):
        """Создание статус бара"""
        self.status_bar = self.statusBar()
        
        # Информация об источнике
        info_text = f"ID: {self.source_data['source_id']}"
        if self.source_data.get('type'):
            info_text += f" | Тип: {self.source_data['type']}"
        if self.source_data.get('publication_date'):
            info_text += f" | Год: {str(self.source_data['publication_date']).split('-')[0]}"
        
        self.status_bar.showMessage(info_text)
    
    def analyze_url(self, url):
        """Анализ URL"""
        try:
            parsed = urlparse(url)
            return {
                'domain': parsed.netloc or 'Неизвестен',
                'protocol': parsed.scheme or 'Неизвестен',
                'status': 'Корректный' if parsed.netloc and parsed.scheme else 'Некорректный'
            }
        except:
            return {
                'domain': 'Ошибка анализа',
                'protocol': 'Неизвестен',
                'status': 'Некорректный'
            }
    
    def determine_historical_epoch(self, year):
        """Определение исторической эпохи"""
        if year < 500:
            return "Древний мир"
        elif year < 1000:
            return "Раннее Средневековье"
        elif year < 1500:
            return "Высокое и Позднее Средневековье"
        elif year < 1800:
            return "Новое время"
        elif year < 1900:
            return "XIX век"
        elif year < 2000:
            return "XX век"
        else:
            return "XXI век"
    
    def assess_reliability(self):
        """Оценка достоверности источника"""
        score = 0
        
        # Наличие автора
        if self.source_data.get('author'):
            score += 2
        
        # Наличие даты публикации
        if self.source_data.get('publication_date'):
            score += 2
        
        # Наличие URL
        if self.source_data.get('url'):
            score += 1
            # Протокол HTTPS
            if self.source_data['url'].startswith('https://'):
                score += 1
        
        # Тип источника
        source_type = self.source_data.get('type', '').lower()
        if any(t in source_type for t in ['книга', 'монография', 'диссертация']):
            score += 3
        elif any(t in source_type for t in ['статья', 'журнал']):
            score += 2
        elif any(t in source_type for t in ['газета', 'новости']):
            score += 1
        
        # Количество связанных событий
        events_count = self.source_data.get('events_count', 0)
        if events_count > 5:
            score += 2
        elif events_count > 0:
            score += 1
        
        # Возраст источника
        if self.source_data.get('publication_date'):
            try:
                pub_year = int(str(self.source_data['publication_date']).split('-')[0])
                age = 2024 - pub_year
                if 10 <= age <= 100:  # Оптимальный возраст для исторических источников
                    score += 1
            except:
                pass
        
        # Оценка
        if score >= 8:
            return "Очень высокая"
        elif score >= 6:
            return "Высокая"
        elif score >= 4:
            return "Средняя"
        elif score >= 2:
            return "Низкая"
        else:
            return "Очень низкая"
    
    def load_full_data(self):
        """Загрузка полных данных источника"""
        try:
            details = self.source_service.get_source_details(
                self.user_data['user_id'],
                self.source_data['source_id']
            )
            
            self.source_data.update(details['source'])
            
            # Обновляем статистику связей
            relationships = details['relationships_summary']['relationships']
            self.events_count_label.setText(f"События: {relationships.get('events', 0)}")
            
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
    
    def open_url(self):
        """Открытие URL в браузере"""
        if self.source_data.get('url'):
            try:
                QDesktopServices.openUrl(QUrl(self.source_data['url']))
                self.status_bar.showMessage("URL открыт в браузере", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть URL: {str(e)}")
    
    def copy_url(self):
        """Копирование URL в буфер обмена"""
        if self.source_data.get('url'):
            clipboard = QApplication.clipboard()
            clipboard.setText(self.source_data['url'])
            self.status_bar.showMessage("URL скопирован в буфер обмена", 3000)
    
    def validate_url(self):
        """Проверка доступности URL"""
        if not self.source_data.get('url'):
            return
        
        url = self.source_data['url']
        
        # Показываем диалог прогресса
        progress = QProgressDialog("Проверка доступности URL...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            # Здесь можно добавить реальную проверку HTTP
            # Пока делаем простую проверку формата
            import time
            time.sleep(1)  # Имитация проверки
            
            progress.hide()
            
            url_analysis = self.analyze_url(url)
            if url_analysis['status'] == 'Корректный':
                QMessageBox.information(
                    self, 
                    "Проверка URL", 
                    f"URL имеет корректный формат:\n\n"
                    f"Домен: {url_analysis['domain']}\n"
                    f"Протокол: {url_analysis['protocol']}\n\n"
                    f"Примечание: Для полной проверки доступности требуется подключение к интернету."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Проверка URL",
                    f"URL имеет некорректный формат:\n{url}"
                )
        
        except Exception as e:
            progress.hide()
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить URL: {str(e)}")
    
    def edit_source(self):
        """Редактирование источника"""
        from ui.dialogs.source_dialog import SourceDialog
        dialog = SourceDialog(self.user_data, self.source_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_full_data()
    
    def manage_relationships(self):
        """Управление связями источника"""
        from ui.dialogs.relationship_dialog import RelationshipDialog
        dialog = RelationshipDialog(
            self.user_data,
            'SOURCE',
            self.source_data['source_id'],
            self.source_data['name'],
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_full_data()
    
    def show_author_works(self):
        """Показ других работ автора"""
        if not self.source_data.get('author'):
            QMessageBox.information(self, "Информация", "Автор источника не указан")
            return
        
        try:
            # Получаем другие работы автора
            author_sources = self.source_service.get_sources(
                self.user_data['user_id'],
                {'author': self.source_data['author'], 'limit': 100}
            )
            
            # Исключаем текущий источник
            other_works = [s for s in author_sources['sources'] 
                          if s['source_id'] != self.source_data['source_id']]
            
            if not other_works:
                QMessageBox.information(
                    self, 
                    "Другие работы автора", 
                    f"Других работ автора {self.source_data['author']} не найдено"
                )
                return
            
            # Показываем окно с другими работами
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Другие работы: {self.source_data['author']}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            info_label = QLabel(f"Найдено работ автора {self.source_data['author']}: {len(other_works)}")
            info_label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(info_label)
            
            # Список работ
            works_list = QListWidget()
            
            for work in other_works:
                work_text = work['name']
                if work.get('publication_date'):
                    year = str(work['publication_date']).split('-')[0]
                    work_text += f" ({year})"
                if work.get('type'):
                    work_text += f" [{work['type']}]"
                
                item = QListWidgetItem(work_text)
                item.setData(Qt.ItemDataRole.UserRole, work)
                works_list.addItem(item)
            
            works_list.itemDoubleClicked.connect(self.view_source_from_list)
            layout.addWidget(works_list)
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить работы автора: {str(e)}")
    
    def find_similar_sources(self):
        """Поиск похожих источников"""
        try:
            # Ищем источники того же типа или автора
            filters = {}
            
            if self.source_data.get('type'):
                filters['source_type'] = self.source_data['type']
            elif self.source_data.get('author'):
                filters['author'] = self.source_data['author']
            
            if not filters:
                QMessageBox.information(self, "Поиск похожих", "Недостаточно данных для поиска похожих источников")
                return
            
            similar_sources = self.source_service.get_sources(
                self.user_data['user_id'],
                {**filters, 'limit': 50}
            )
            
            # Исключаем текущий источник
            similar = [s for s in similar_sources['sources'] 
                      if s['source_id'] != self.source_data['source_id']]
            
            if not similar:
                QMessageBox.information(self, "Похожие источники", "Похожие источники не найдены")
                return
            
            # Показываем результаты
            dialog = QDialog(self)
            dialog.setWindowTitle("Похожие источники")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            info_label = QLabel(f"Найдено похожих источников: {len(similar)}")
            info_label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(info_label)
            
            # Список похожих источников
            similar_list = QListWidget()
            
            for source in similar:
                source_text = f"{source['name']}"
                if source.get('author'):
                    source_text += f" - {source['author']}"
                if source.get('publication_date'):
                    year = str(source['publication_date']).split('-')[0]
                    source_text += f" ({year})"
                
                item = QListWidgetItem(source_text)
                item.setData(Qt.ItemDataRole.UserRole, source)
                similar_list.addItem(item)
            
            similar_list.itemDoubleClicked.connect(self.view_source_from_list)
            layout.addWidget(similar_list)
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось найти похожие источники: {str(e)}")
    
    def view_source_from_list(self, item):
        """Просмотр источника из списка"""
        source_data = item.data(Qt.ItemDataRole.UserRole)
        if source_data:
            details_window = SourceDetailsWindow(source_data, self.user_data, self)
            details_window.show()
    
    def generate_citation(self):
        """Генерация библиографической ссылки"""
        try:
            # Создаем различные форматы цитирования
            citations = self.create_citations()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Библиографическое цитирование")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Вкладки с разными форматами
            tabs = QTabWidget()
            
            for format_name, citation_text in citations.items():
                text_widget = QTextEdit()
                text_widget.setReadOnly(True)
                text_widget.setPlainText(citation_text)
                tabs.addTab(text_widget, format_name)
            
            layout.addWidget(tabs)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            copy_btn = QPushButton("Копировать")
            copy_btn.clicked.connect(lambda: self.copy_citation(tabs))
            buttons_layout.addWidget(copy_btn)
            
            save_btn = QPushButton("Сохранить в файл")
            save_btn.clicked.connect(lambda: self.save_citations(citations))
            buttons_layout.addWidget(save_btn)
            
            buttons_layout.addStretch()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать цитирование: {str(e)}")
    
    def create_citations(self):
        """Создание различных форматов цитирования"""
        citations = {}
        
        name = self.source_data['name']
        author = self.source_data.get('author', '')
        pub_date = self.source_data.get('publication_date', '')
        url = self.source_data.get('url', '')
        source_type = self.source_data.get('type', '')
        
        year = str(pub_date).split('-')[0] if pub_date else 'б.г.'
        
        # ГОСТ Р 7.0.5-2008 (российский стандарт)
        gost_citation = f"{author}. {name}"
        if source_type:
            gost_citation += f" [{source_type}]"
        if pub_date:
            gost_citation += f". – {year}"
        if url:
            gost_citation += f". – URL: {url}"
        gost_citation += "."
        
        citations["ГОСТ"] = gost_citation
        
        # APA Style
        apa_citation = f"{author} ({year}). {name}"
        if url:
            apa_citation += f". Retrieved from {url}"
        
        citations["APA"] = apa_citation
        
        # MLA Style
        mla_citation = f'{author}. "{name}." Web. {QDate.currentDate().toString("d MMM yyyy")}.'
        if url:
            mla_citation += f" <{url}>."
        
        citations["MLA"] = mla_citation
        
        # Chicago Style
        chicago_citation = f'{author}. "{name}." Accessed {QDate.currentDate().toString("MMMM d, yyyy")}.'
        if url:
            chicago_citation += f" {url}."
        
        citations["Chicago"] = chicago_citation
        
        return citations
    
    def copy_citation(self, tabs):
        """Копирование текущего цитирования"""
        current_widget = tabs.currentWidget()
        if current_widget:
            citation_text = current_widget.toPlainText()
            clipboard = QApplication.clipboard()
            clipboard.setText(citation_text)
            self.status_bar.showMessage("Цитирование скопировано в буфер обмена", 3000)
    
    def save_citations(self, citations):
        """Сохранение всех цитирований в файл"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить цитирования",
            f"citations_{self.source_data['name'].replace(' ', '_')}.txt",
            "Text files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"БИБЛИОГРАФИЧЕСКИЕ ССЫЛКИ\n")
                    f.write(f"Источник: {self.source_data['name']}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for format_name, citation in citations.items():
                        f.write(f"{format_name}:\n")
                        f.write(f"{citation}\n\n")
                
                QMessageBox.information(self, "Успех", f"Цитирования сохранены в файл:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def export_bibtex(self):
        """Экспорт в формат BibTeX"""
        try:
            # Создаем BibTeX запись
            bibtex_key = f"{self.source_data.get('author', 'Unknown').replace(' ', '')}{str(self.source_data.get('publication_date', ''))[:4]}"
            
            bibtex_content = f"""@misc{{{bibtex_key},
    title = {{{self.source_data['name']}}},
    author = {{{self.source_data.get('author', '')}}},
    year = {{{str(self.source_data.get('publication_date', '')).split('-')[0]}}},
    url = {{{self.source_data.get('url', '')}}},
    note = {{Источник: {self.source_data.get('type', '')}}}
}}"""
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить BibTeX",
                f"{bibtex_key}.bib",
                "BibTeX files (*.bib)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(bibtex_content)
                
                QMessageBox.information(self, "Успех", f"BibTeX сохранен в файл:\n{filename}")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать BibTeX: {str(e)}")
    
    def export_ris(self):
        """Экспорт в формат RIS"""
        try:
            # Создаем RIS запись
            ris_content = f"""TY  - ELEC
TI  - {self.source_data['name']}
AU  - {self.source_data.get('author', '')}
PY  - {str(self.source_data.get('publication_date', '')).split('-')[0]}
UR  - {self.source_data.get('url', '')}
N1  - {self.source_data.get('type', '')}
ER  - 
"""
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить RIS",
                f"{self.source_data['name'][:30].replace(' ', '_')}.ris",
                "RIS files (*.ris)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(ris_content)
                
                QMessageBox.information(self, "Успех", f"RIS сохранен в файл:\n{filename}")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать RIS: {str(e)}")
    
    def show_all_events(self):
        """Показ всех связанных событий"""
        try:
            # Получаем все связанные события
            all_events = self.source_service.get_source_details(
                self.user_data['user_id'],
                self.source_data['source_id']
            )['related_events']
            
            if not all_events:
                QMessageBox.information(self, "События", "Нет связанных событий")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"События, связанные с источником: {self.source_data['name']}")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Статистика
            stats_label = QLabel(f"Всего связанных событий: {len(all_events)}")
            stats_label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(stats_label)
            
            # Таблица событий
            events_table = QTreeWidget()
            events_table.setHeaderLabels(["Название", "Тип", "Дата начала", "Дата окончания", "Место"])
            
            for event in all_events:
                item = QTreeWidgetItem([
                    event['name'],
                    event.get('event_type', ''),
                    str(event.get('start_date', '')),
                    str(event.get('end_date', '')),
                    event.get('location', '')
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, event)
                events_table.addTopLevelItem(item)
            
            events_table.itemDoubleClicked.connect(self.view_event_details)
            layout.addWidget(events_table)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            export_events_btn = QPushButton("Экспорт списка")
            export_events_btn.clicked.connect(lambda: self.export_events_list(all_events))
            buttons_layout.addWidget(export_events_btn)
            
            buttons_layout.addStretch()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить события: {str(e)}")
    
    def export_events_list(self, events):
        """Экспорт списка событий"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить список событий",
            f"events_for_{self.source_data['name'].replace(' ', '_')}.txt",
            "Text files (*.txt);;CSV files (*.csv)"
        )
        
        if filename:
            try:
                if filename.endswith('.csv'):
                    # Экспорт в CSV
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Название', 'Тип', 'Дата начала', 'Дата окончания', 'Место', 'Описание'])
                        
                        for event in events:
                            writer.writerow([
                                event['name'],
                                event.get('event_type', ''),
                                event.get('start_date', ''),
                                event.get('end_date', ''),
                                event.get('location', ''),
                                event.get('description', '')[:100] + '...' if event.get('description') else ''
                            ])
                else:
                    # Экспорт в текстовый файл
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"СОБЫТИЯ, СВЯЗАННЫЕ С ИСТОЧНИКОМ\n")
                        f.write(f"Источник: {self.source_data['name']}\n")
                        f.write(f"Автор: {self.source_data.get('author', 'Не указан')}\n")
                        f.write("=" * 60 + "\n\n")
                        
                        for i, event in enumerate(events, 1):
                            f.write(f"{i}. {event['name']}\n")
                            
                            if event.get('event_type'):
                                f.write(f"   Тип: {event['event_type']}\n")
                            
                            if event.get('start_date') or event.get('end_date'):
                                period = ""
                                if event.get('start_date') and event.get('end_date'):
                                    period = f"{event['start_date']} - {event['end_date']}"
                                elif event.get('start_date'):
                                    period = f"с {event['start_date']}"
                                elif event.get('end_date'):
                                    period = f"до {event['end_date']}"
                                f.write(f"   Период: {period}\n")
                            
                            if event.get('location'):
                                f.write(f"   Место: {event['location']}\n")
                            
                            if event.get('description'):
                                desc = event['description'][:200] + "..." if len(event['description']) > 200 else event['description']
                                f.write(f"   Описание: {desc}\n")
                            
                            f.write("\n")
                
                QMessageBox.information(self, "Успех", f"Список событий сохранен в файл:\n{filename}")
            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def view_event_details(self, item):
        """Просмотр деталей события"""
        event_data = item.data(Qt.ItemDataRole.UserRole)
        if event_data:
            from ui.windows.event_details_window import EventDetailsWindow
            details_window = EventDetailsWindow(event_data, self.user_data, self)
            details_window.show()
    
    def create_relations_panel(self):
        """Создание панели связей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Статистика связей
        stats_group = QGroupBox("Связи с событиями")
        stats_layout = QVBoxLayout(stats_group)
        
        self.events_count_label = QLabel("События: загрузка...")
        stats_layout.addWidget(self.events_count_label)
        
        if self.user_data['role_id'] >= 2:
            manage_relations_btn = QPushButton("Управлять связями")
            manage_relations_btn.clicked.connect(self.manage_relationships)
            stats_layout.addWidget(manage_relations_btn)
        
        layout.addWidget(stats_group)
        
        # Связанные события
        events_group = QGroupBox("Связанные события")
        events_layout = QVBoxLayout(events_group)
        
        self.events_list = QListWidget()
        self.events_list.itemDoubleClicked.connect(self.view_event_details)
        events_layout.addWidget(self.events_list)
        
        # Кнопка показать все
        show_all_events_btn = QPushButton("Показать все события")
        show_all_events_btn.clicked.connect(self.show_all_events)
        events_layout.addWidget(show_all_events_btn)
        
        layout.addWidget(events_group)
        
        # Анализ источника
        analysis_group = QGroupBox("Анализ источника")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # Информация об авторе
        author_info_btn = QPushButton("Другие работы автора")
        author_info_btn.clicked.connect(self.show_author_works)
        analysis_layout.addWidget(author_info_btn)
        
        # Похожие источники
        similar_btn = QPushButton("Похожие источники")
        similar_btn.clicked.connect(self.find_similar_sources)
        analysis_layout.addWidget(similar_btn)
        
        # Библиографическая ссылка
        citation_btn = QPushButton("Создать цитирование")
        citation_btn.clicked.connect(self.generate_citation)
        analysis_layout.addWidget(citation_btn)
        
        layout.addWidget(analysis_group)
        
        # Экспорт и сохранение
        export_group = QGroupBox("Экспорт")
        export_layout = QVBoxLayout(export_group)
        
        export_bib_btn = QPushButton("Экспорт в BibTeX")
        export_bib_btn.clicked.connect(self.export_bibtex)
        export_layout.addWidget(export_bib_btn)
        
        export_ris_btn = QPushButton("Экспорт в RIS")
        export_ris_btn.clicked.connect(self.export_ris)
        export_layout.addWidget(export_ris_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        return widget
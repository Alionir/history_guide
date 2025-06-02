from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services.country_service import CountryService
from services.relationship_service import RelationshipService
from  utils.date_helpers import safe_date_convert
class CountryDetailsWindow(QMainWindow):
    def __init__(self, country_data, user_data, parent=None):
        super().__init__(parent)
        self.country_data = country_data
        self.user_data = user_data
        self.country_service = CountryService()
        self.relationship_service = RelationshipService()
        self.setup_ui()
        self.load_full_data()
    
    def setup_ui(self):
        self.setWindowTitle(f"Страна: {self.country_data['name']}")
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
    
    def create_info_panel(self):
        """Создание панели основной информации"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Заголовок с названием страны
        name_label = QLabel(self.country_data['name'])
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(name_label)
        
        # Основная информация
        info_group = QGroupBox("Основная информация")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("ID:", QLabel(str(self.country_data['country_id'])))
        info_layout.addRow("Название:", QLabel(self.country_data['name']))
        
        if self.country_data.get('capital'):
            info_layout.addRow("Столица:", QLabel(self.country_data['capital']))
        
        # Период существования
        period_text = self.format_existence_period()
        info_layout.addRow("Период:", QLabel(period_text))
        
        # Статус
        status = "Существует" if not self.country_data.get('dissolution_date') else "Историческое государство"
        status_label = QLabel(status)
        if status == "Историческое государство":
            status_label.setStyleSheet("color: #888; font-style: italic;")
        else:
            status_label.setStyleSheet("color: #007acc; font-weight: bold;")
        info_layout.addRow("Статус:", status_label)
        
        layout.addWidget(info_group)
        
        # Историческая информация
        history_group = QGroupBox("Историческая информация")
        history_layout = QVBoxLayout(history_group)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        description = self.country_data.get('description', 'Описание не указано')
        self.description_text.setPlainText(description)
        history_layout.addWidget(self.description_text)
        
        layout.addWidget(history_group)
        
        # Дополнительная информация
        additional_group = QGroupBox("Дополнительная информация")
        additional_layout = QVBoxLayout(additional_group)
        
        # Длительность существования
        if self.country_data.get('foundation_date') and self.country_data.get('dissolution_date'):
            try:
                from datetime import datetime
                foundation = datetime.strptime(str(self.country_data['foundation_date']), '%Y-%m-%d')
                dissolution = datetime.strptime(str(self.country_data['dissolution_date']), '%Y-%m-%d')
                duration = dissolution - foundation
                years = duration.days // 365
                duration_label = QLabel(f"Продолжительность существования: {years} лет")
                additional_layout.addWidget(duration_label)
            except:
                pass
        
        # Эпоха
        if self.country_data.get('foundation_date'):
            year = int(str(self.country_data['foundation_date']).split('-')[0])
            epoch = self.determine_historical_epoch(year)
            epoch_label = QLabel(f"Историческая эпоха: {epoch}")
            additional_layout.addWidget(epoch_label)
        
        layout.addWidget(additional_group)
        
        return widget
    
    def create_relations_panel(self):
        """Создание панели связей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Статистика связей
        stats_group = QGroupBox("Статистика связей")
        stats_layout = QVBoxLayout(stats_group)
        
        self.events_count_label = QLabel("События: загрузка...")
        self.persons_count_label = QLabel("Персоны: загрузка...")
        
        stats_layout.addWidget(self.events_count_label)
        stats_layout.addWidget(self.persons_count_label)
        
        # Кнопка управления связями
        if self.user_data['role_id'] >= 2:  # Модератор или выше
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
        
        # Кнопка "Показать все события"
        show_all_events_btn = QPushButton("Показать все события")
        show_all_events_btn.clicked.connect(self.show_all_events)
        events_layout.addWidget(show_all_events_btn)
        
        layout.addWidget(events_group)
        
        # Знаменитые персоны из страны
        persons_group = QGroupBox("Знаменитые персоны")
        persons_layout = QVBoxLayout(persons_group)
        
        self.persons_list = QListWidget()
        self.persons_list.itemDoubleClicked.connect(self.view_person_details)
        persons_layout.addWidget(self.persons_list)
        
        # Кнопка "Показать всех персон"
        show_all_persons_btn = QPushButton("Показать всех персон")
        show_all_persons_btn.clicked.connect(self.show_all_persons)
        persons_layout.addWidget(show_all_persons_btn)
        
        layout.addWidget(persons_group)
        
        return widget
    
    def create_menus(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Действия
        actions_menu = menubar.addMenu('Действия')
        
        # Редактирование - для модераторов прямое, для пользователей через заявку
        if self.user_data['role_id'] >= 2:  # Модератор
            edit_action = actions_menu.addAction('Редактировать', self.edit_country)
            edit_action.setShortcut('Ctrl+E')
        else:  # Обычный пользователь
            edit_request_action = actions_menu.addAction('Подать заявку на изменение', self.request_edit_country)
            edit_request_action.setShortcut('Ctrl+E')
        
        actions_menu.addSeparator()
        
        timeline_action = actions_menu.addAction('Временная линия', self.show_timeline)
        timeline_action.setShortcut('Ctrl+T')
        
        refresh_action = actions_menu.addAction('Обновить', self.load_full_data)
        refresh_action.setShortcut('F5')
        
        actions_menu.addSeparator()
        close_action = actions_menu.addAction('Закрыть', self.close)
        close_action.setShortcut('Ctrl+W')
        
        # Просмотр
        view_menu = menubar.addMenu('Просмотр')
        view_menu.addAction('Все события страны', self.show_all_events)
        view_menu.addAction('Все персоны страны', self.show_all_persons)
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar('Основное')
        
        # Кнопка редактирования в зависимости от роли пользователя
        if self.user_data['role_id'] >= 2:
            edit_action = QAction('Редактировать', self)
            edit_action.triggered.connect(self.edit_country)
            toolbar.addAction(edit_action)
        else:
            edit_request_action = QAction('Подать заявку на изменение', self)
            edit_request_action.triggered.connect(self.request_edit_country)
            toolbar.addAction(edit_request_action)
            
        toolbar.addSeparator()
        
        timeline_action = QAction('Временная линия', self)
        timeline_action.triggered.connect(self.show_timeline)
        toolbar.addAction(timeline_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction('Обновить', self)
        refresh_action.triggered.connect(self.load_full_data)
        toolbar.addAction(refresh_action)
    
    def load_full_data(self):
        """Загрузка полных данных о стране"""
        try:
            # Получаем детальную информацию
            details = self.country_service.get_country_details(
                self.user_data['user_id'],
                self.country_data['country_id']
            )
            
            # Обновляем данные
            self.country_data.update(details['country'])
            
            # Обновляем статистику связей
            relationships = details['relationships_summary']['relationships']
            self.events_count_label.setText(f"События: {relationships.get('events', 0)}")
            
            # Загружаем связанные события
            self.events_list.clear()
            for event in details['recent_events']:
                period = ""
                if event.get('start_date'):
                    period = f" ({str(event['start_date']).split('-')[0]})"
                
                item = QListWidgetItem(f"{event['name']}{period}")
                item.setData(Qt.ItemDataRole.UserRole, event)
                self.events_list.addItem(item)
            
            # Загружаем персон из страны
            self.persons_list.clear()
            for person in details['recent_persons']:
                life_years = ""
                if person.get('date_of_birth'):
                    birth_year = str(person['date_of_birth']).split('-')[0]
                    life_years = f" ({birth_year}"
                    if person.get('date_of_death'):
                        death_year = str(person['date_of_death']).split('-')[0]
                        life_years += f"-{death_year})"
                    else:
                        life_years += "-н.в.)"
                
                full_name = person.get('full_name', person['name'])
                item = QListWidgetItem(f"{full_name}{life_years}")
                item.setData(Qt.ItemDataRole.UserRole, person)
                self.persons_list.addItem(item)
            
            # Обновляем счетчик персон
            self.persons_count_label.setText(f"Персоны: {len(details['recent_persons'])}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def format_existence_period(self):
        """Форматирование периода существования"""
        foundation = self.country_data.get('foundation_date')
        dissolution = self.country_data.get('dissolution_date')
        
        if foundation and dissolution:
            foundation_year = str(foundation).split('-')[0]
            dissolution_year = str(dissolution).split('-')[0]
            return f"{foundation_year} - {dissolution_year}"
        elif foundation:
            foundation_year = str(foundation).split('-')[0]
            return f"с {foundation_year}"
        elif dissolution:
            dissolution_year = str(dissolution).split('-')[0]
            return f"до {dissolution_year}"
        else:
            return "Период не указан"
    
    def determine_historical_epoch(self, year):
        """Определение исторической эпохи по году"""
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
    
    def edit_country(self):
        """Прямое редактирование страны (для модераторов)"""
        from ui.dialogs.country_dialog import CountryDialog
        dialog = CountryDialog(self.user_data, self.country_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_full_data()  # Обновляем данные
    
    def request_edit_country(self):
        """Создание заявки на редактирование страны (для обычных пользователей)"""
        dialog = CountryEditRequestDialog(self.user_data, self.country_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self, 
                "Заявка отправлена", 
                "Ваша заявка на изменение данных о стране была отправлена модераторам на рассмотрение."
            )
    
    def manage_relationships(self):
        """Управление связями страны"""
        from ui.dialogs.relationship_dialog import RelationshipDialog
        dialog = RelationshipDialog(
            self.user_data,
            'COUNTRY',
            self.country_data['country_id'],
            self.country_data['name'],
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_full_data()  # Обновляем связи
    
    def show_timeline(self):
        """Показ временной линии страны"""
        try:
            timeline = self.country_service.get_countries_timeline(self.user_data['user_id'])
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Временная линия: {self.country_data['name']}")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_widget = QTextEdit()
            text_widget.setReadOnly(True)
            
            # Формируем HTML контент
            html_content = f"<h2>Временная линия: {self.country_data['name']}</h2>"
            
            # Добавляем информацию о самой стране
            period = self.format_existence_period()
            html_content += f"""
            <div style='margin: 15px 0; padding: 15px; border: 2px solid #007acc; background-color: #f0f8ff;'>
                <h3 style='color: #007acc; margin: 0;'>{self.country_data['name']}</h3>
                <p><b>Период существования:</b> {period}</p>
                <p><b>Столица:</b> {self.country_data.get('capital', 'Не указана')}</p>
            </div>
            """
            
            # Добавляем связанные события в хронологическом порядке
            events = []
            for event in self.events_list.findItems("*", Qt.MatchFlag.MatchWildcard):
                event_data = event.data(Qt.ItemDataRole.UserRole)
                if event_data and event_data.get('start_date'):
                    events.append(event_data)
            
            # Сортируем события по дате
            events.sort(key=lambda x: x.get('start_date', ''))
            
            for event in events:
                start_year = str(event['start_date']).split('-')[0] if event.get('start_date') else '?'
                html_content += f"""
                <div style='margin: 10px 0; padding: 10px; border-left: 4px solid #ff6b35;'>
                    <b style='color: #ff6b35;'>{start_year}</b> - 
                    <b>{event['name']}</b><br>
                    <i>{event.get('description', 'Описание отсутствует')[:150]}...</i>
                </div>
                """
            
            text_widget.setHtml(html_content)
            layout.addWidget(text_widget)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            export_btn = QPushButton("Экспорт в HTML")
            export_btn.clicked.connect(lambda: self.export_timeline_html(html_content))
            buttons_layout.addWidget(export_btn)
            
            buttons_layout.addStretch()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить временную линию: {str(e)}")
    
    def export_timeline_html(self, html_content):
        """Экспорт временной линии в HTML файл"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить временную линию",
            f"timeline_{self.country_data['name'].replace(' ', '_')}.html",
            "HTML files (*.html)"
        )
        
        if filename:
            try:
                full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Временная линия: {self.country_data['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h2 {{ color: #007acc; }}
        h3 {{ color: #007acc; margin: 0; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
                """
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                
                QMessageBox.information(self, "Успех", f"Временная линия сохранена в файл:\n{filename}")
            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def show_all_events(self):
        """Показ всех событий, связанных со страной"""
        try:
            # Получаем все события страны
            all_events = self.country_service.get_country_details(
                self.user_data['user_id'],
                self.country_data['country_id']
            )['recent_events']  # В реальности нужно получать все события, а не только recent
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Все события: {self.country_data['name']}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Список событий
            events_list = QListWidget()
            
            for event in all_events:
                period = ""
                if event.get('start_date') and event.get('end_date'):
                    start_year = str(event['start_date']).split('-')[0]
                    end_year = str(event['end_date']).split('-')[0]
                    period = f" ({start_year}-{end_year})"
                elif event.get('start_date'):
                    start_year = str(event['start_date']).split('-')[0]
                    period = f" ({start_year})"
                
                item_text = f"{event['name']}{period}"
                if event.get('event_type'):
                    item_text += f" [{event['event_type']}]"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, event)
                events_list.addItem(item)
            
            events_list.itemDoubleClicked.connect(self.view_event_details)
            layout.addWidget(events_list)
            
            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить события: {str(e)}")
    
    def show_all_persons(self):
        """Показ всех персон из страны"""
        try:
            # Получаем всех персон из страны
            all_persons = self.country_service.get_country_details(
                self.user_data['user_id'],
                self.country_data['country_id']
            )['recent_persons']  # В реальности нужно получать всех персон
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Знаменитые персоны: {self.country_data['name']}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Статистика
            stats_label = QLabel(f"Всего персон из {self.country_data['name']}: {len(all_persons)}")
            stats_label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(stats_label)
            
            # Список персон
            persons_list = QListWidget()
            
            for person in all_persons:
                life_years = ""
                if person.get('date_of_birth'):
                    birth_year = str(person['date_of_birth']).split('-')[0]
                    life_years = f" ({birth_year}"
                    if person.get('date_of_death'):
                        death_year = str(person['date_of_death']).split('-')[0]
                        life_years += f"-{death_year})"
                    else:
                        life_years += "-н.в.)"
                
                full_name = person.get('full_name', person['name'])
                item_text = f"{full_name}{life_years}"
                
                # Добавляем краткую информацию о роде деятельности, если есть
                if person.get('biography'):
                    bio_snippet = person['biography'][:50] + "..." if len(person['biography']) > 50 else person['biography']
                    item_text += f" - {bio_snippet}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, person)
                persons_list.addItem(item)
            
            persons_list.itemDoubleClicked.connect(self.view_person_details)
            layout.addWidget(persons_list)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            # Кнопка экспорта списка
            export_btn = QPushButton("Экспорт списка")
            export_btn.clicked.connect(lambda: self.export_persons_list(all_persons))
            buttons_layout.addWidget(export_btn)
            
            buttons_layout.addStretch()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить персон: {str(e)}")
    
    def export_persons_list(self, persons):
        """Экспорт списка персон"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить список персон",
            f"persons_{self.country_data['name'].replace(' ', '_')}.txt",
            "Text files (*.txt);;CSV files (*.csv)"
        )
        
        if filename:
            try:
                if filename.endswith('.csv'):
                    # Экспорт в CSV
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Имя', 'Фамилия', 'Отчество', 'Дата рождения', 'Дата смерти', 'Страна'])
                        
                        for person in persons:
                            writer.writerow([
                                person.get('name', ''),
                                person.get('surname', ''),
                                person.get('patronymic', ''),
                                person.get('date_of_birth', ''),
                                person.get('date_of_death', ''),
                                self.country_data['name']
                            ])
                else:
                    # Экспорт в текстовый файл
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Знаменитые персоны: {self.country_data['name']}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for person in persons:
                            full_name = person.get('full_name', person['name'])
                            f.write(f"{full_name}\n")
                            
                            if person.get('date_of_birth') or person.get('date_of_death'):
                                birth = str(person['date_of_birth']).split('-')[0] if person.get('date_of_birth') else '?'
                                death = str(person['date_of_death']).split('-')[0] if person.get('date_of_death') else 'н.в.'
                                f.write(f"  Годы жизни: {birth} - {death}\n")
                            
                            if person.get('biography'):
                                f.write(f"  Краткая биография: {person['biography'][:200]}...\n")
                            
                            f.write("\n")
                
                QMessageBox.information(self, "Успех", f"Список персон сохранен в файл:\n{filename}")
            
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def view_event_details(self, item):
        """Просмотр деталей события"""
        event_data = item.data(Qt.ItemDataRole.UserRole)
        if event_data:
            from ui.windows.event_details_window import EventDetailsWindow
            details_window = EventDetailsWindow(event_data, self.user_data, self)
            details_window.show()
    
    def view_person_details(self, item):
        """Просмотр деталей персоны"""
        person_data = item.data(Qt.ItemDataRole.UserRole)
        if person_data:
            from ui.windows.person_details_window import PersonDetailsWindow
            details_window = PersonDetailsWindow(person_data, self.user_data, self)
            details_window.show()


class CountryEditRequestDialog(QDialog):
    """Диалог для создания заявки на редактирование страны"""
    
    def __init__(self, user_data, country_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.country_data = country_data
        self.country_service = CountryService()
        self.setup_ui()
        self.load_current_data()
    
    def setup_ui(self):
        self.setWindowTitle(f"Заявка на изменение: {self.country_data['name']}")
        self.setModal(True)
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel(f"Подача заявки на изменение данных о стране")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Информация о текущих данных
        current_group = QGroupBox("Текущие данные")
        current_layout = QVBoxLayout(current_group)
        
        self.current_info = QTextEdit()
        self.current_info.setReadOnly(True)
        self.current_info.setMaximumHeight(150)
        current_layout.addWidget(self.current_info)
        
        layout.addWidget(current_group)
        
        # Форма для новых данных
        new_data_group = QGroupBox("Предлагаемые изменения")
        form_layout = QFormLayout(new_data_group)
        
        # Название страны
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(100)
        form_layout.addRow("Название:", self.name_edit)
        
        # Столица
        self.capital_edit = QLineEdit()
        self.capital_edit.setMaxLength(100)
        form_layout.addRow("Столица:", self.capital_edit)
        
        # Даты
        date_layout = QHBoxLayout()
        
        self.foundation_date_edit = QDateEdit()
        self.foundation_date_edit.setCalendarPopup(True)
        self.foundation_date_edit.setSpecialValueText("Не указана")
        self.foundation_date_edit.setDate(QDate(1, 1, 1))
        
        self.dissolution_date_edit = QDateEdit()
        self.dissolution_date_edit.setCalendarPopup(True)
        self.dissolution_date_edit.setSpecialValueText("Не указана")
        self.dissolution_date_edit.setDate(QDate(1, 1, 1))
        
        date_layout.addWidget(QLabel("Дата основания:"))
        date_layout.addWidget(self.foundation_date_edit)
        date_layout.addWidget(QLabel("Дата роспуска:"))
        date_layout.addWidget(self.dissolution_date_edit)
        
        form_layout.addRow(date_layout)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(150)
        self.description_edit.setPlaceholderText("Историческое описание страны...")
        form_layout.addRow("Описание:", self.description_edit)
        
        layout.addWidget(new_data_group)
        
        # Обоснование изменений
        reason_group = QGroupBox("Обоснование изменений")
        reason_layout = QVBoxLayout(reason_group)
        
        reason_label = QLabel("Пожалуйста, укажите причину предлагаемых изменений:")
        reason_layout.addWidget(reason_label)
        
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("Например: исправление ошибок, добавление недостающей информации, уточнение данных на основе новых источников...")
        self.reason_edit.setMaximumHeight(100)
        reason_layout.addWidget(self.reason_edit)
        
        layout.addWidget(reason_group)
        
        # Информационное сообщение
        info_label = QLabel(
            "Ваша заявка будет рассмотрена модераторами. "
            "Вы получите уведомление о принятии решения по заявке."
        )
        info_label.setStyleSheet("color: #666; font-style: italic; margin: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.submit_btn = QPushButton("Отправить заявку")
        self.submit_btn.clicked.connect(self.submit_request)
        self.submit_btn.setStyleSheet("QPushButton { background-color: #007acc; color: white; font-weight: bold; }")
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.submit_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_current_data(self):
        """Загрузка текущих данных страны"""
        # Отображаем текущие данные
        current_text = f"""Название: {self.country_data['name']}
Столица: {self.country_data.get('capital', 'Не указана')}
Дата основания: {self.country_data.get('foundation_date', 'Не указана')}
Дата роспуска: {self.country_data.get('dissolution_date', 'Не указана')}
Описание: {self.country_data.get('description', 'Не указано')[:200]}..."""
        
        self.current_info.setPlainText(current_text)
        
        # Заполняем форму текущими данными для удобства редактирования
        self.name_edit.setText(self.country_data['name'])
        
        if self.country_data.get('capital'):
            self.capital_edit.setText(self.country_data['capital'])
        
        if self.country_data.get('foundation_date'):
            try:
                from datetime import datetime
                date_obj = datetime.strptime(str(self.country_data['foundation_date']), '%Y-%m-%d')
                self.foundation_date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            except:
                pass
        
        if self.country_data.get('dissolution_date'):
            try:
                from datetime import datetime
                date_obj = datetime.strptime(str(self.country_data['dissolution_date']), '%Y-%m-%d')
                self.dissolution_date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            except:
                pass
        
        if self.country_data.get('description'):
            self.description_edit.setPlainText(self.country_data['description'])
    
    def submit_request(self):
        """Отправка заявки на изменение"""
        try:
            # Валидация данных
            if not self.name_edit.text().strip():
                QMessageBox.warning(self, "Ошибка", "Название страны обязательно для заполнения")
                return
            
            if not self.reason_edit.toPlainText().strip():
                QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите обоснование для изменений")
                return
            
            if len(self.reason_edit.toPlainText().strip()) < 10:
                QMessageBox.warning(self, "Ошибка", "Обоснование должно содержать минимум 10 символов")
                return
            
            # Подготавливаем данные для заявки
            country_data = {
                'name': self.name_edit.text().strip(),
                'capital': self.capital_edit.text().strip() if self.capital_edit.text().strip() else None,
                'description': self.description_edit.toPlainText().strip() if self.description_edit.toPlainText().strip() else None
            }
            
            # Обработка дат
            if self.foundation_date_edit.date() != QDate(1, 1, 1):
                country_data['foundation_date'] = safe_date_convert(self.foundation_date_edit.date())
            else:
                country_data['foundation_date'] = None
            
            if self.dissolution_date_edit.date() != QDate(1, 1, 1):
                country_data['dissolution_date'] = safe_date_convert(self.dissolution_date_edit.date())
            else:
                country_data['dissolution_date'] = None
            
            # Проверяем, есть ли изменения
            changes_made = self.has_changes(country_data)
            if not changes_made:
                QMessageBox.information(self, "Информация", "Вы не внесли никаких изменений в данные")
                return
            
            # Отправляем заявку
            self.submit_btn.setEnabled(False)
            self.submit_btn.setText("Отправка...")
            
            result = self.country_service.create_country_request(
                user_id=self.user_data['user_id'],
                country_data=country_data
            )
            
            if result.get('success'):
                # Логируем причину изменений (в реальной реализации это должно сохраняться в заявке)
                reason = self.reason_edit.toPlainText().strip()
                
                QMessageBox.information(
                    self, 
                    "Заявка отправлена", 
                    f"Ваша заявка на изменение данных о стране '{country_data['name']}' "
                    f"была успешно отправлена на рассмотрение модераторам.\n\n"
                    f"Номер заявки: {result.get('request_id', 'Не указан')}\n"
                    f"Обоснование: {reason[:100]}..."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка", 
                    f"Не удалось отправить заявку: {result.get('message', 'Неизвестная ошибка')}"
                )
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при отправке заявки: {str(e)}")
        
        finally:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Отправить заявку")
    
    def has_changes(self, new_data):
        """Проверка наличия изменений"""
        # Сравниваем новые данные с текущими
        current_name = self.country_data['name']
        current_capital = self.country_data.get('capital', '')
        current_description = self.country_data.get('description', '')
        
        if new_data['name'] != current_name:
            return True
        
        if (new_data.get('capital') or '') != current_capital:
            return True
        
        if (new_data.get('description') or '') != current_description:
            return True
        
        # Сравнение дат
        current_foundation = self.country_data.get('foundation_date')
        current_dissolution = self.country_data.get('dissolution_date')
        
        if str(new_data.get('foundation_date')) != str(current_foundation):
            return True
        
        if str(new_data.get('dissolution_date')) != str(current_dissolution):
            return True
        
        return False
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class ExportWindow(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        from services.export_service import ExportService
        from services.country_service import CountryService
        
        self.export_service = ExportService()
        self.country_service = CountryService()
        
        self.setup_ui()
        self.load_countries()
    
    def setup_ui(self):
        self.setWindowTitle("Экспорт данных")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Экспорт исторических данных")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Выбор типа данных
        data_group = QGroupBox("Выберите данные для экспорта")
        data_layout = QVBoxLayout(data_group)
        
        self.export_persons = QCheckBox("Персоны")
        self.export_persons.setChecked(True)
        self.export_persons.toggled.connect(self.update_filters_visibility)
        data_layout.addWidget(self.export_persons)
        
        self.export_events = QCheckBox("События (временная линия)")
        self.export_events.toggled.connect(self.update_filters_visibility)
        data_layout.addWidget(self.export_events)
        
        self.export_countries = QCheckBox("Страны")
        data_layout.addWidget(self.export_countries)
        
        self.export_documents = QCheckBox("Документы")
        data_layout.addWidget(self.export_documents)
        
        self.export_sources = QCheckBox("Источники")
        data_layout.addWidget(self.export_sources)
        
        layout.addWidget(data_group)
        
        # Формат экспорта
        format_group = QGroupBox("Формат экспорта")
        format_layout = QVBoxLayout(format_group)
        
        self.format_json = QRadioButton("JSON (подробные данные)")
        self.format_json.setChecked(True)
        format_layout.addWidget(self.format_json)
        
        self.format_csv = QRadioButton("CSV (табличные данные)")
        format_layout.addWidget(self.format_csv)
        
        self.format_xml = QRadioButton("XML (структурированные данные)")
        format_layout.addWidget(self.format_xml)
        
        layout.addWidget(format_group)
        
        # Фильтры для персон
        self.persons_filters_group = QGroupBox("Фильтры для персон")
        persons_filters_layout = QFormLayout(self.persons_filters_group)
        
        self.country_filter = QComboBox()
        self.country_filter.addItem("Все страны", None)
        persons_filters_layout.addRow("Страна:", self.country_filter)
        
        self.alive_only = QCheckBox("Только живые персоны")
        persons_filters_layout.addRow("", self.alive_only)
        
        # Диапазон лет рождения
        birth_years_layout = QHBoxLayout()
        self.birth_year_from = QSpinBox()
        self.birth_year_from.setRange(1, 2100)
        self.birth_year_from.setValue(1800)
        self.birth_year_from.setSpecialValueText("Не указано")
        birth_years_layout.addWidget(self.birth_year_from)
        
        birth_years_layout.addWidget(QLabel(" - "))
        
        self.birth_year_to = QSpinBox()
        self.birth_year_to.setRange(1, 2100)
        self.birth_year_to.setValue(2024)
        self.birth_year_to.setSpecialValueText("Не указано")
        birth_years_layout.addWidget(self.birth_year_to)
        
        persons_filters_layout.addRow("Годы рождения:", birth_years_layout)
        
        layout.addWidget(self.persons_filters_group)
        
        # Фильтры для событий
        self.events_filters_group = QGroupBox("Фильтры для событий")
        events_filters_layout = QFormLayout(self.events_filters_group)
        
        # Диапазон лет событий
        event_years_layout = QHBoxLayout()
        self.event_year_from = QSpinBox()
        self.event_year_from.setRange(1, 2100)
        self.event_year_from.setValue(1800)
        self.event_year_from.setSpecialValueText("Не указано")
        event_years_layout.addWidget(self.event_year_from)
        
        event_years_layout.addWidget(QLabel(" - "))
        
        self.event_year_to = QSpinBox()
        self.event_year_to.setRange(1, 2100)
        self.event_year_to.setValue(2024)
        self.event_year_to.setSpecialValueText("Не указано")
        event_years_layout.addWidget(self.event_year_to)
        
        events_filters_layout.addRow("Период событий:", event_years_layout)
        
        self.event_type_filter = QLineEdit()
        self.event_type_filter.setPlaceholderText("Оставьте пустым для всех типов")
        events_filters_layout.addRow("Тип события:", self.event_type_filter)
        
        layout.addWidget(self.events_filters_group)
        
        # Настройки экспорта
        settings_group = QGroupBox("Настройки экспорта")
        settings_layout = QFormLayout(settings_group)
        
        self.include_relationships = QCheckBox("Включить связи между сущностями")
        self.include_relationships.setChecked(True)
        settings_layout.addRow("", self.include_relationships)
        
        self.max_records = QSpinBox()
        self.max_records.setRange(100, 10000)
        self.max_records.setValue(1000)
        self.max_records.setSuffix(" записей")
        settings_layout.addRow("Максимум записей:", self.max_records)
        
        layout.addWidget(settings_group)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Экспортировать")
        self.export_btn.clicked.connect(self.perform_export)
        self.export_btn.setDefault(True)
        buttons_layout.addWidget(self.export_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Инициализируем видимость фильтров
        self.update_filters_visibility()
    
    def load_countries(self):
        """Загрузка списка стран для фильтра"""
        try:
            result = self.country_service.get_countries(
                self.user_data['user_id'], 
                {'limit': 200}
            )
            countries = result.get('countries', [])
            
            for country in countries:
                self.country_filter.addItem(country['name'], country['country_id'])
                
        except Exception as e:
            print(f"Ошибка загрузки стран: {e}")
    
    def update_filters_visibility(self):
        """Обновление видимости фильтров в зависимости от выбранных данных"""
        self.persons_filters_group.setVisible(self.export_persons.isChecked())
        self.events_filters_group.setVisible(self.export_events.isChecked())
    
    def perform_export(self):
        """Выполнение экспорта"""
        # Проверяем, что выбрано что-то для экспорта
        selected_data = [
            self.export_persons.isChecked(),
            self.export_events.isChecked(),
            self.export_countries.isChecked(),
            self.export_documents.isChecked(),
            self.export_sources.isChecked()
        ]
        
        if not any(selected_data):
            QMessageBox.warning(self, "Предупреждение", "Выберите данные для экспорта")
            return
        
        # Определяем формат
        if self.format_json.isChecked():
            file_ext = "json"
            file_filter = "JSON files (*.json)"
        elif self.format_csv.isChecked():
            file_ext = "csv"
            file_filter = "CSV files (*.csv)"
        else:  # XML
            file_ext = "xml"
            file_filter = "XML files (*.xml)"
        
        # Диалог выбора папки для сохранения
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для экспорта",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not export_dir:
            return
        
        try:
            self.export_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            exported_files = []
            total_steps = sum(selected_data)
            current_step = 0
            
            # Экспорт персон
            if self.export_persons.isChecked():
                self.progress_bar.setValue(int((current_step / total_steps) * 100))
                QApplication.processEvents()
                
                filters = self.get_persons_filters()
                filename = f"{export_dir}/persons_export.{file_ext}"
                
                if self.export_data_type('persons', filters, filename, file_ext):
                    exported_files.append(filename)
                
                current_step += 1
            
            # Экспорт событий
            if self.export_events.isChecked():
                self.progress_bar.setValue(int((current_step / total_steps) * 100))
                QApplication.processEvents()
                
                filters = self.get_events_filters()
                filename = f"{export_dir}/events_export.{file_ext}"
                
                if self.export_data_type('events', filters, filename, file_ext):
                    exported_files.append(filename)
                
                current_step += 1
            
            # Экспорт стран
            if self.export_countries.isChecked():
                self.progress_bar.setValue(int((current_step / total_steps) * 100))
                QApplication.processEvents()
                
                filename = f"{export_dir}/countries_export.{file_ext}"
                
                if self.export_data_type('countries', {}, filename, file_ext):
                    exported_files.append(filename)
                
                current_step += 1
            
            # Экспорт документов
            if self.export_documents.isChecked():
                self.progress_bar.setValue(int((current_step / total_steps) * 100))
                QApplication.processEvents()
                
                filename = f"{export_dir}/documents_export.{file_ext}"
                
                if self.export_data_type('documents', {}, filename, file_ext):
                    exported_files.append(filename)
                
                current_step += 1
            
            # Экспорт источников
            if self.export_sources.isChecked():
                self.progress_bar.setValue(int((current_step / total_steps) * 100))
                QApplication.processEvents()
                
                filename = f"{export_dir}/sources_export.{file_ext}"
                
                if self.export_data_type('sources', {}, filename, file_ext):
                    exported_files.append(filename)
                
                current_step += 1
            
            self.progress_bar.setValue(100)
            
            if exported_files:
                QMessageBox.information(
                    self,
                    "Экспорт завершен",
                    f"Успешно экспортировано {len(exported_files)} файл(ов):\n\n" +
                    "\n".join([f"• {file.split('/')[-1]}" for file in exported_files]) +
                    f"\n\nФайлы сохранены в: {export_dir}"
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Предупреждение", "Не удалось экспортировать данные")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Произошла ошибка: {str(e)}")
        
        finally:
            self.export_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def get_persons_filters(self):
        """Получение фильтров для персон"""
        filters = {}
        
        if self.country_filter.currentData():
            filters['country_id'] = self.country_filter.currentData()
        
        if self.alive_only.isChecked():
            filters['alive_only'] = True
        
        if self.birth_year_from.value() > 1:
            filters['birth_year_from'] = self.birth_year_from.value()
        
        if self.birth_year_to.value() > 1:
            filters['birth_year_to'] = self.birth_year_to.value()
        
        filters['limit'] = self.max_records.value()
        
        return filters
    
    def get_events_filters(self):
        """Получение фильтров для событий"""
        filters = {}
        
        if self.event_year_from.value() > 1:
            filters['year_from'] = self.event_year_from.value()
        
        if self.event_year_to.value() > 1:
            filters['year_to'] = self.event_year_to.value()
        
        if self.event_type_filter.text().strip():
            filters['event_type'] = self.event_type_filter.text().strip()
        
        filters['limit'] = self.max_records.value()
        
        return filters
    
    def export_data_type(self, data_type, filters, filename, file_format):
        """Экспорт конкретного типа данных"""
        try:
            if data_type == 'persons':
                if file_format == 'json':
                    data = self.export_service.export_persons_to_json(
                        self.user_data['user_id'], 
                        filters
                    )
                elif file_format == 'csv':
                    data = self.export_service.export_persons_to_csv(
                        self.user_data['user_id'], 
                        filters
                    )
                else:  # XML
                    data = self.export_service.export_persons_to_xml(
                        self.user_data['user_id'], 
                        filters
                    )
            
            elif data_type == 'events':
                if file_format == 'json':
                    data = self.export_service.export_events_to_json(
                        self.user_data['user_id'], 
                        filters.get('year_from'),
                        filters.get('year_to'),
                        filters.get('event_type')
                    )
                elif file_format == 'csv':
                    data = self.export_service.export_events_timeline_to_csv(
                        self.user_data['user_id'], 
                        filters.get('year_from'),
                        filters.get('year_to')
                    )
                else:  # XML
                    data = self.export_service.export_events_to_xml(
                        self.user_data['user_id'], 
                        filters.get('year_from'),
                        filters.get('year_to')
                    )
            
            elif data_type == 'countries':
                if file_format == 'json':
                    data = self.export_service.export_countries_to_json(
                        self.user_data['user_id']
                    )
                elif file_format == 'csv':
                    data = self.export_service.export_countries_to_csv(
                        self.user_data['user_id']
                    )
                else:  # XML
                    data = self.export_service.export_countries_to_xml(
                        self.user_data['user_id']
                    )
            
            elif data_type == 'documents':
                if file_format == 'json':
                    data = self.export_service.export_documents_to_json(
                        self.user_data['user_id'],
                        {'limit': self.max_records.value()}
                    )
                elif file_format == 'csv':
                    data = self.export_service.export_documents_to_csv(
                        self.user_data['user_id'],
                        {'limit': self.max_records.value()}
                    )
                else:  # XML
                    data = self.export_service.export_documents_to_xml(
                        self.user_data['user_id'],
                        {'limit': self.max_records.value()}
                    )
            
            elif data_type == 'sources':
                if file_format == 'json':
                    data = self.export_service.export_sources_to_json(
                        self.user_data['user_id'],
                        {'limit': self.max_records.value()}
                    )
                elif file_format == 'csv':
                    data = self.export_service.export_sources_to_csv(
                        self.user_data['user_id'],
                        {'limit': self.max_records.value()}
                    )
                else:  # XML
                    data = self.export_service.export_sources_to_xml(
                        self.user_data['user_id'],
                        {'limit': self.max_records.value()}
                    )
            
            # Сохраняем файл
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(data)
            
            return True
            
        except Exception as e:
            print(f"Ошибка экспорта {data_type}: {e}")
            return False


class AdvancedExportDialog(QDialog):
    """Расширенный диалог экспорта с дополнительными возможностями"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Расширенный экспорт данных")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Вкладки для разных типов экспорта
        tabs = QTabWidget()
        
        # Вкладка простого экспорта
        simple_tab = QWidget()
        simple_layout = QVBoxLayout(simple_tab)
        
        simple_export_btn = QPushButton("Открыть простой экспорт")
        simple_export_btn.clicked.connect(self.open_simple_export)
        simple_layout.addWidget(simple_export_btn)
        
        simple_layout.addStretch()
        tabs.addTab(simple_tab, "Простой экспорт")
        
        # Вкладка экспорта связей
        relationships_tab = QWidget()
        relationships_layout = QVBoxLayout(relationships_tab)
        
        rel_export_btn = QPushButton("Экспорт структуры связей")
        rel_export_btn.clicked.connect(self.export_relationships)
        relationships_layout.addWidget(rel_export_btn)
        
        rel_stats_btn = QPushButton("Экспорт статистики связей")
        rel_stats_btn.clicked.connect(self.export_relationship_stats)
        relationships_layout.addWidget(rel_stats_btn)
        
        relationships_layout.addStretch()
        tabs.addTab(relationships_tab, "Связи")
        
        # Вкладка аналитических отчетов
        analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(analytics_tab)
        
        timeline_btn = QPushButton("Экспорт временной линии")
        timeline_btn.clicked.connect(self.export_timeline)
        analytics_layout.addWidget(timeline_btn)
        
        stats_btn = QPushButton("Экспорт общей статистики")
        stats_btn.clicked.connect(self.export_general_stats)
        analytics_layout.addWidget(stats_btn)
        
        analytics_layout.addStretch()
        tabs.addTab(analytics_tab, "Аналитика")
        
        layout.addWidget(tabs)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def open_simple_export(self):
        """Открытие простого экспорта"""
        dialog = ExportWindow(self.user_data, self)
        dialog.exec()
    
    def export_relationships(self):
        """Экспорт структуры связей"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить экспорт связей",
                "relationships_structure.json",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if filename:
                from services.relationship_service import RelationshipService
                rel_service = RelationshipService()
                
                # Здесь должен быть метод экспорта связей
                QMessageBox.information(
                    self,
                    "Функция в разработке",
                    "Экспорт связей будет доступен в следующей версии"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
    
    def export_relationship_stats(self):
        """Экспорт статистики связей"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить статистику связей",
                "relationships_stats.json",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if filename:
                QMessageBox.information(
                    self,
                    "Функция в разработке",
                    "Экспорт статистики связей будет доступен в следующей версии"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
    
    def export_timeline(self):
        """Экспорт временной линии"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить временную линию",
                "timeline_export.json",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if filename:
                QMessageBox.information(
                    self,
                    "Функция в разработке",
                    "Экспорт временной линии будет доступен в следующей версии"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
    
    def export_general_stats(self):
        """Экспорт общей статистики"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить общую статистику",
                "general_statistics.json",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if filename:
                QMessageBox.information(
                    self,
                    "Функция в разработке",
                    "Экспорт общей статистики будет доступен в следующей версии"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
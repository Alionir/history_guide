# ui/pages/analytics_page.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ui.pages.base_page import BasePage
from services.analytics_service import AnalyticsService
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AnalyticsPage(BasePage):
    def __init__(self, user_data):
        super().__init__(user_data)
        self.analytics_service = AnalyticsService()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title = QLabel("Аналитика и статистика")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Создаем вкладки для разных видов аналитики
        tabs = QTabWidget()
        
        # Вкладка общей статистики
        self.create_dashboard_tab(tabs)
        
        # Вкладка качества контента (для админов)
        if self.user_data['role_id'] >= 3:
            self.create_quality_tab(tabs)
        
        # Вкладка использования системы
        if self.user_data['role_id'] >= 2:
            self.create_usage_tab(tabs)
        
        layout.addWidget(tabs)
        
        # Загружаем данные
        self.refresh()
    
    def create_dashboard_tab(self, tabs):
        """Создание вкладки дашборда"""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        
        # Карточки с основной статистикой
        cards_layout = QHBoxLayout()
        
        self.entities_card = self.create_stat_card("Сущности", "0", "Всего записей")
        self.quality_card = self.create_stat_card("Качество", "0%", "Заполненность")
        self.activity_card = self.create_stat_card("Активность", "0", "За неделю")
        
        cards_layout.addWidget(self.entities_card)
        cards_layout.addWidget(self.quality_card)
        cards_layout.addWidget(self.activity_card)
        
        dashboard_layout.addLayout(cards_layout)
        
        # Таблица топ связанных сущностей
        connections_group = QGroupBox("Самые связанные сущности")
        connections_layout = QVBoxLayout(connections_group)
        
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(4)
        self.connections_table.setHorizontalHeaderLabels(["Тип", "Название", "Связей", "Рейтинг"])
        self.connections_table.horizontalHeader().setStretchLastSection(True)
        
        connections_layout.addWidget(self.connections_table)
        dashboard_layout.addWidget(connections_group)
        
        tabs.addTab(dashboard_widget, "Дашборд")
    
    def create_quality_tab(self, tabs):
        """Создание вкладки качества контента"""
        quality_widget = QWidget()
        quality_layout = QVBoxLayout(quality_widget)
        
        # Информация о проблемах
        problems_group = QGroupBox("Проблемы качества")
        problems_layout = QVBoxLayout(problems_group)
        
        self.problems_list = QListWidget()
        problems_layout.addWidget(self.problems_list)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        fix_urls_btn = QPushButton("Проверить URL")
        fix_urls_btn.clicked.connect(self.check_urls)
        actions_layout.addWidget(fix_urls_btn)
        
        find_duplicates_btn = QPushButton("Найти дубли")
        find_duplicates_btn.clicked.connect(self.find_duplicates)
        actions_layout.addWidget(find_duplicates_btn)
        
        actions_layout.addStretch()
        
        problems_layout.addLayout(actions_layout)
        quality_layout.addWidget(problems_group)
        
        # Рекомендации
        recommendations_group = QGroupBox("Рекомендации")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(150)
        recommendations_layout.addWidget(self.recommendations_text)
        
        quality_layout.addWidget(recommendations_group)
        
        tabs.addTab(quality_widget, "Качество")
    
    def create_usage_tab(self, tabs):
        """Создание вкладки использования"""
        usage_widget = QWidget()
        usage_layout = QVBoxLayout(usage_widget)
        
        # Фильтры периода
        period_layout = QHBoxLayout()
        
        period_layout.addWidget(QLabel("Период:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 дней", "30 дней", "90 дней", "365 дней"])
        self.period_combo.setCurrentText("30 дней")
        self.period_combo.currentTextChanged.connect(self.load_usage_data)
        period_layout.addWidget(self.period_combo)
        
        period_layout.addStretch()
        
        usage_layout.addLayout(period_layout)
        
        # Таблица активности пользователей
        activity_group = QGroupBox("Активность пользователей")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(3)
        self.activity_table.setHorizontalHeaderLabels(["Пользователь", "Действий", "Последняя активность"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        
        activity_layout.addWidget(self.activity_table)
        usage_layout.addWidget(activity_group)
        
        tabs.addTab(usage_widget, "Использование")
    
    def create_stat_card(self, title, value, description):
        """Создание карточки статистики"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; }")
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff;")
        layout.addWidget(value_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(desc_label)
        
        # Сохраняем ссылку на value_label для обновления
        card.value_label = value_label
        
        return card
    
    def refresh(self):
        """Обновление всех данных"""
        self.load_dashboard_data()
        if self.user_data['role_id'] >= 3:
            self.load_quality_data()
        if self.user_data['role_id'] >= 2:
            self.load_usage_data()
    
    def load_dashboard_data(self):
        """Загрузка данных дашборда"""
        try:
            stats = self.analytics_service.get_dashboard_statistics(self.user_data['user_id'])
            
            # Обновляем карточки
            entity_counts = stats.get('entity_counts', {})
            total_entities = sum(entity_counts.values())
            self.entities_card.value_label.setText(str(total_entities))
            
            quality_metrics = stats.get('quality_metrics', {})
            # Простой расчет качества
            quality_score = self.calculate_quality_score(quality_metrics, entity_counts)
            self.quality_card.value_label.setText(f"{quality_score}%")
            
            activity = stats.get('activity_last_week', [])
            total_activity = sum(item.get('action_count', 0) for item in activity)
            self.activity_card.value_label.setText(str(total_activity))
            
            # Обновляем таблицу связей
            self.update_connections_table(stats.get('top_connected', {}))
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные дашборда: {str(e)}")
    
    def load_quality_data(self):
        """Загрузка данных качества"""
        try:
            quality_report = self.analytics_service.get_content_quality_report(self.user_data['user_id'])
            
            # Обновляем список проблем
            self.problems_list.clear()
            
            sources_issues = quality_report.get('sources_issues', {})
            if sources_issues.get('invalid_urls', 0) > 0:
                self.problems_list.addItem(f"Некорректных URL: {sources_issues['invalid_urls']}")
            
            if sources_issues.get('duplicates', 0) > 0:
                self.problems_list.addItem(f"Дублирующихся источников: {sources_issues['duplicates']}")
            
            content_gaps = quality_report.get('content_gaps', {})
            if content_gaps.get('documents_without_links', 0) > 0:
                self.problems_list.addItem(f"Документов без связей: {content_gaps['documents_without_links']}")
            
            if content_gaps.get('persons_without_biography', 0) > 0:
                self.problems_list.addItem(f"Персон без биографии: {content_gaps['persons_without_biography']}")
            
            if self.problems_list.count() == 0:
                self.problems_list.addItem("Серьезных проблем не обнаружено")
            
            # Обновляем рекомендации
            recommendations = quality_report.get('recommendations', [])
            self.recommendations_text.setPlainText('\n'.join(recommendations))
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные качества: {str(e)}")
    
    def load_usage_data(self):
        """Загрузка данных использования"""
        try:
            period_text = self.period_combo.currentText()
            days = int(period_text.split()[0])
            
            usage_data = self.analytics_service.get_usage_analytics(self.user_data['user_id'], days)
            
            # Обновляем таблицу активности
            top_users = usage_data.get('top_users', [])
            self.activity_table.setRowCount(len(top_users))
            
            for row, user in enumerate(top_users):
                self.activity_table.setItem(row, 0, QTableWidgetItem(user['username']))
                self.activity_table.setItem(row, 1, QTableWidgetItem(str(user['activity_count'])))
                self.activity_table.setItem(row, 2, QTableWidgetItem("Недавно"))  # Можно добавить реальную дату
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные использования: {str(e)}")
    
    def calculate_quality_score(self, quality_metrics, entity_counts):
        """Расчет общего показателя качества"""
        if not entity_counts:
            return 0
        
        total_score = 0
        total_weight = 0
        
        # Процент персон с биографией
        if entity_counts.get('persons', 0) > 0:
            bio_percent = (quality_metrics.get('persons_with_biography', 0) / entity_counts['persons']) * 100
            total_score += bio_percent * 0.3
            total_weight += 0.3
        
        # Процент событий с датами
        if entity_counts.get('events', 0) > 0:
            dates_percent = (quality_metrics.get('events_with_dates', 0) / entity_counts['events']) * 100
            total_score += dates_percent * 0.3
            total_weight += 0.3
        
        # Процент источников с URL
        if entity_counts.get('sources', 0) > 0:
            url_percent = (quality_metrics.get('sources_with_valid_urls', 0) / entity_counts['sources']) * 100
            total_score += url_percent * 0.4
            total_weight += 0.4
        
        return int(total_score / total_weight) if total_weight > 0 else 0
    
    def update_connections_table(self, connections_data):
        """Обновление таблицы связей"""
        all_connections = []
        
        # Собираем все связанные сущности
        for entity_type, entities in connections_data.items():
            for entity in entities:
                all_connections.append({
                    'type': entity_type,
                    'name': entity.get('name', ''),
                    'connections': entity.get('total_connections', 0)
                })
        
        # Сортируем по количеству связей
        all_connections.sort(key=lambda x: x['connections'], reverse=True)
        
        # Показываем топ 10
        top_connections = all_connections[:10]
        self.connections_table.setRowCount(len(top_connections))
        
        for row, conn in enumerate(top_connections):
            self.connections_table.setItem(row, 0, QTableWidgetItem(conn['type'].title()))
            self.connections_table.setItem(row, 1, QTableWidgetItem(conn['name']))
            self.connections_table.setItem(row, 2, QTableWidgetItem(str(conn['connections'])))
            
            # Рейтинг на основе связей
            if conn['connections'] >= 10:
                rating = "Высокий"
            elif conn['connections'] >= 5:
                rating = "Средний"
            else:
                rating = "Низкий"
            
            self.connections_table.setItem(row, 3, QTableWidgetItem(rating))
    
    def check_urls(self):
        """Проверка URL источников"""
        try:
            from services import SourceService
            source_service = SourceService()
            
            issues = source_service.check_sources_urls(self.user_data['user_id'])
            
            if issues:
                message = f"Найдено {len(issues)} проблем с URL источников"
                QMessageBox.information(self, "Проверка URL", message)
            else:
                QMessageBox.information(self, "Проверка URL", "Все URL источников корректны")
            
            self.load_quality_data()  # Обновляем данные качества
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить URL: {str(e)}")
    
    def find_duplicates(self):
        """Поиск дублирующихся источников"""
        try:
            from services import SourceService
            source_service = SourceService()
            
            duplicates = source_service.find_duplicate_sources(self.user_data['user_id'])
            
            if duplicates:
                message = f"Найдено {len(duplicates)} групп дублирующихся источников"
                QMessageBox.information(self, "Поиск дублей", message)
            else:
                QMessageBox.information(self, "Поиск дублей", "Дублирующиеся источники не найдены")
            
            self.load_quality_data()  # Обновляем данные качества
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось найти дубли: {str(e)}")
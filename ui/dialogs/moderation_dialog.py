from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel, 
                             QTextEdit, QComboBox, QSpinBox, QGroupBox, QFormLayout,
                             QMessageBox, QHeaderView, QSplitter, QFrame, QScrollArea,
                             QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette
from datetime import datetime
import json
from services import ModerationService
from core.exceptions import ValidationError, AuthorizationError

class ModerationDialog(QDialog):
    """Диалог для работы с системой модерации"""
    
    request_processed = pyqtSignal()  # Сигнал об обработке заявки
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.moderation_service = ModerationService()
        self.current_requests = []
        self.selected_request = None
        
        self.setWindowTitle("Система модерации")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Проверяем права доступа
        if user_data.get('role_id', 1) < 2:
            QMessageBox.warning(self, "Доступ запрещен", 
                              "У вас нет прав для доступа к системе модерации")
            self.reject()
            return
        
        self.setup_ui()
        self.load_pending_requests()
        
        # Автообновление каждые 30 секунд
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_pending_requests)
        self.update_timer.start(30000)
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Система модерации")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        self.stats_label = QLabel("Загрузка статистики...")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка "Заявки на рассмотрение"
        self.pending_tab = self.create_pending_tab()
        self.tab_widget.addTab(self.pending_tab, "Заявки на рассмотрение")
        
        # Вкладка "История модерации"
        self.history_tab = self.create_history_tab()
        self.tab_widget.addTab(self.history_tab, "История модерации")
        
        # Вкладка "Статистика" (только для админов)
        if self.user_data.get('role_id', 1) >= 3:
            self.stats_tab = self.create_statistics_tab()
            self.tab_widget.addTab(self.stats_tab, "Статистика")
        
        layout.addWidget(self.tab_widget)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.refresh_current_tab)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
    
    def create_pending_tab(self):
        """Создание вкладки с заявками на рассмотрение"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        
        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QFormLayout(filters_group)
        
        self.entity_type_filter = QComboBox()
        self.entity_type_filter.addItems(['Все типы', 'PERSON', 'COUNTRY', 'EVENT', 'DOCUMENT', 'SOURCE'])
        self.entity_type_filter.currentTextChanged.connect(self.apply_filters)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(['PENDING', 'APPROVED', 'REJECTED', 'Все статусы'])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        
        filters_layout.addRow("Тип сущности:", self.entity_type_filter)
        filters_layout.addRow("Статус:", self.status_filter)
        
        layout.addWidget(filters_group)
        
        # Основной сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - список заявок
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        
        # Информация о количестве заявок
        self.requests_count_label = QLabel("Загрузка заявок...")
        left_layout.addWidget(self.requests_count_label)
        
        # Таблица заявок
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(6)
        self.requests_table.setHorizontalHeaderLabels([
            'ID', 'Тип', 'Операция', 'Пользователь', 'Дата создания', 'Статус'
        ])
        
        # Настройка таблицы
        header = self.requests_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.requests_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.requests_table.setAlternatingRowColors(True)
        self.requests_table.itemSelectionChanged.connect(self.on_request_selected)
        
        left_layout.addWidget(self.requests_table)
        
        # Правая панель - детали заявки
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        # Заголовок деталей
        self.details_title = QLabel("Выберите заявку для просмотра деталей")
        self.details_title.setFont(QFont("", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.details_title)
        
        # Область прокрутки для деталей
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.details_widget = QFrame()
        self.details_layout = QVBoxLayout(self.details_widget)
        scroll_area.setWidget(self.details_widget)
        
        right_layout.addWidget(scroll_area)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.approve_button = QPushButton("Одобрить")
        self.approve_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.approve_button.clicked.connect(self.approve_request)
        self.approve_button.setEnabled(False)
        
        self.reject_button = QPushButton("Отклонить")
        self.reject_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self.reject_button.clicked.connect(self.reject_request)
        self.reject_button.setEnabled(False)
        
        actions_layout.addWidget(self.approve_button)
        actions_layout.addWidget(self.reject_button)
        actions_layout.addStretch()
        
        right_layout.addLayout(actions_layout)
        
        # Добавляем панели в сплиттер
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        return widget
    
    def create_history_tab(self):
        """Создание вкладки с историей модерации"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        
        # Фильтры для истории
        history_filters = QGroupBox("Параметры поиска")
        history_filters_layout = QFormLayout(history_filters)
        
        self.history_days = QSpinBox()
        self.history_days.setRange(1, 365)
        self.history_days.setValue(30)
        self.history_days.setSuffix(" дней")
        
        self.history_user_filter = QComboBox()
        self.history_user_filter.addItem("Все пользователи")
        self.history_user_filter.setEditable(True)
        
        history_filters_layout.addRow("Период:", self.history_days)
        history_filters_layout.addRow("Пользователь:", self.history_user_filter)
        
        load_history_button = QPushButton("Загрузить историю")
        load_history_button.clicked.connect(self.load_history)
        history_filters_layout.addRow(load_history_button)
        
        layout.addWidget(history_filters)
        
        # Таблица истории
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            'ID заявки', 'Тип', 'Операция', 'Пользователь', 'Статус', 
            'Модератор', 'Дата рассмотрения'
        ])
        
        # Настройка таблицы истории
        history_header = self.history_table.horizontalHeader()
        for i in range(7):
            history_header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSortingEnabled(True)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def create_statistics_tab(self):
        """Создание вкладки со статистикой (только для админов)"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        
        # Параметры статистики
        stats_params = QGroupBox("Параметры")
        stats_params_layout = QFormLayout(stats_params)
        
        self.stats_period = QSpinBox()
        self.stats_period.setRange(1, 365)
        self.stats_period.setValue(30)
        self.stats_period.setSuffix(" дней")
        
        load_stats_button = QPushButton("Обновить статистику")
        load_stats_button.clicked.connect(self.load_statistics)
        
        stats_params_layout.addRow("Период:", self.stats_period)
        stats_params_layout.addRow(load_stats_button)
        
        layout.addWidget(stats_params)
        
        # Основная статистика
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setMaximumHeight(200)
        
        layout.addWidget(self.stats_display)
        
        # Очистка старых заявок (только для админов)
        cleanup_group = QGroupBox("Обслуживание системы")
        cleanup_layout = QFormLayout(cleanup_group)
        
        self.cleanup_days = QSpinBox()
        self.cleanup_days.setRange(30, 365)
        self.cleanup_days.setValue(90)
        self.cleanup_days.setSuffix(" дней")
        
        cleanup_button = QPushButton("Очистить старые заявки")
        cleanup_button.clicked.connect(self.cleanup_old_requests)
        cleanup_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        
        cleanup_layout.addRow("Удалить заявки старше:", self.cleanup_days)
        cleanup_layout.addRow(cleanup_button)
        
        layout.addWidget(cleanup_group)
        
        layout.addStretch()
        
        return widget
    
    def load_pending_requests(self):
        """Загрузка заявок на рассмотрение"""
        try:
            # Определяем фильтры
            entity_type = self.entity_type_filter.currentText()
            if entity_type == 'Все типы':
                entity_type = None
            
            status = self.status_filter.currentText()
            if status == 'Все статусы':
                status = None
            
            filters = {
                'entity_type': entity_type,
                'status': status,
                'offset': 0,
                'limit': 100
            }
            
            # Получаем заявки
            result = self.moderation_service.get_pending_requests(
                moderator_id=self.user_data['user_id'],
                filters=filters
            )
            
            self.current_requests = result['requests']
            self.populate_requests_table()
            
            # Обновляем счетчик
            total_count = result.get('total_count', 0)
            pending_count = len([r for r in self.current_requests if r.get('status') == 'PENDING'])
            self.requests_count_label.setText(
                f"Всего заявок: {total_count}, на рассмотрении: {pending_count}"
            )
            
            # Обновляем статистику в заголовке
            self.update_header_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить заявки: {str(e)}")
    
    def populate_requests_table(self):
        """Заполнение таблицы заявок"""
        self.requests_table.setRowCount(len(self.current_requests))
        
        for row, request in enumerate(self.current_requests):
            # ID заявки
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(request['request_id'])))
            
            # Тип сущности
            entity_type_item = QTableWidgetItem(request['entity_type'])
            self.requests_table.setItem(row, 1, entity_type_item)
            
            # Тип операции
            operation_item = QTableWidgetItem(request['operation_type'])
            # Цветовая индикация операций
            if request['operation_type'] == 'CREATE':
                operation_item.setBackground(Qt.GlobalColor.lightGreen)
            elif request['operation_type'] == 'UPDATE':
                operation_item.setBackground(Qt.GlobalColor.yellow)
            elif request['operation_type'] == 'DELETE':
                operation_item.setBackground(Qt.GlobalColor.lightCoral)
            
            self.requests_table.setItem(row, 2, operation_item)
            
            # Пользователь
            username = request.get('requester_username', 'Неизвестно')
            self.requests_table.setItem(row, 3, QTableWidgetItem(username))
            
            # Дата создания
            created_at = request.get('created_at')
            if isinstance(created_at, datetime):
                date_str = created_at.strftime('%d.%m.%Y %H:%M')
            else:
                date_str = str(created_at) if created_at else 'Неизвестно'
            self.requests_table.setItem(row, 4, QTableWidgetItem(date_str))
            
            # Статус
            status_item = QTableWidgetItem(request['status'])
            if request['status'] == 'PENDING':
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif request['status'] == 'APPROVED':
                status_item.setBackground(Qt.GlobalColor.lightGreen)
            elif request['status'] == 'REJECTED':
                status_item.setBackground(Qt.GlobalColor.lightCoral)
            
            self.requests_table.setItem(row, 5, status_item)
    
    def on_request_selected(self):
        """Обработка выбора заявки"""
        current_row = self.requests_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_requests):
            self.selected_request = self.current_requests[current_row]
            self.show_request_details()
            
            # Активируем кнопки только для заявок со статусом PENDING
            is_pending = self.selected_request.get('status') == 'PENDING'
            self.approve_button.setEnabled(is_pending)
            self.reject_button.setEnabled(is_pending)
        else:
            self.selected_request = None
            self.clear_request_details()
            self.approve_button.setEnabled(False)
            self.reject_button.setEnabled(False)
    
    def show_request_details(self):
        """Отображение деталей выбранной заявки"""
        if not self.selected_request:
            return
        
        # Очищаем предыдущие детали
        self.clear_request_details()
        
        request = self.selected_request
        
        # Заголовок
        self.details_title.setText(
            f"Заявка #{request['request_id']} - {request['operation_type']} {request['entity_type']}"
        )
        
        # Основная информация
        info_group = QGroupBox("Информация о заявке")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("ID заявки:", QLabel(str(request['request_id'])))
        info_layout.addRow("Тип сущности:", QLabel(request['entity_type']))
        info_layout.addRow("Операция:", QLabel(request['operation_type']))
        info_layout.addRow("Пользователь:", QLabel(request.get('requester_username', 'Неизвестно')))
        info_layout.addRow("Статус:", QLabel(request['status']))
        
        created_at = request.get('created_at')
        if isinstance(created_at, datetime):
            date_str = created_at.strftime('%d.%m.%Y %H:%M:%S')
        else:
            date_str = str(created_at) if created_at else 'Неизвестно'
        info_layout.addRow("Дата создания:", QLabel(date_str))
        
        if request.get('reviewed_at'):
            reviewed_at = request['reviewed_at']
            if isinstance(reviewed_at, datetime):
                reviewed_str = reviewed_at.strftime('%d.%m.%Y %H:%M:%S')
            else:
                reviewed_str = str(reviewed_at)
            info_layout.addRow("Дата рассмотрения:", QLabel(reviewed_str))
            
            reviewer = request.get('reviewer_username', 'Неизвестно')
            info_layout.addRow("Модератор:", QLabel(reviewer))
        
        self.details_layout.addWidget(info_group)
        
        # Новые данные
        if request.get('new_data'):
            new_data_group = QGroupBox("Новые данные")
            new_data_layout = QVBoxLayout(new_data_group)
            
            new_data_text = QTextEdit()
            new_data_text.setReadOnly(True)
            new_data_text.setMaximumHeight(150)
            
            try:
                if isinstance(request['new_data'], str):
                    new_data = json.loads(request['new_data'])
                else:
                    new_data = request['new_data']
                
                formatted_data = json.dumps(new_data, ensure_ascii=False, indent=2)
                new_data_text.setPlainText(formatted_data)
            except:
                new_data_text.setPlainText(str(request['new_data']))
            
            new_data_layout.addWidget(new_data_text)
            self.details_layout.addWidget(new_data_group)
        
        # Старые данные (для UPDATE операций)
        if request.get('old_data'):
            old_data_group = QGroupBox("Текущие данные")
            old_data_layout = QVBoxLayout(old_data_group)
            
            old_data_text = QTextEdit()
            old_data_text.setReadOnly(True)
            old_data_text.setMaximumHeight(150)
            
            try:
                if isinstance(request['old_data'], str):
                    old_data = json.loads(request['old_data'])
                else:
                    old_data = request['old_data']
                
                formatted_data = json.dumps(old_data, ensure_ascii=False, indent=2)
                old_data_text.setPlainText(formatted_data)
            except:
                old_data_text.setPlainText(str(request['old_data']))
            
            old_data_layout.addWidget(old_data_text)
            self.details_layout.addWidget(old_data_group)
        
        # Комментарий
        if request.get('comment'):
            comment_group = QGroupBox("Комментарий")
            comment_layout = QVBoxLayout(comment_group)
            
            comment_label = QLabel(request['comment'])
            comment_label.setWordWrap(True)
            comment_layout.addWidget(comment_label)
            
            self.details_layout.addWidget(comment_group)
    
    def clear_request_details(self):
        """Очистка деталей заявки"""
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def approve_request(self):
        """Одобрение выбранной заявки"""
        if not self.selected_request:
            return
        
        # Получаем комментарий от пользователя
        comment, ok = self.get_comment_dialog("Одобрение заявки", 
                                             "Комментарий к одобрению (необязательно):")
        if not ok:
            return
        
        try:
            result = self.moderation_service.approve_request(
                moderator_id=self.user_data['user_id'],
                request_id=self.selected_request['request_id'],
                comment=comment if comment.strip() else None
            )
            
            if result['success']:
                QMessageBox.information(self, "Успех", "Заявка успешно одобрена")
                self.request_processed.emit()
                self.load_pending_requests()
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось одобрить заявку: {str(e)}")
    
    def reject_request(self):
        """Отклонение выбранной заявки"""
        if not self.selected_request:
            return
        
        # Получаем обязательный комментарий от пользователя
        comment, ok = self.get_comment_dialog("Отклонение заявки", 
                                             "Причина отклонения (обязательно):", required=True)
        if not ok or not comment.strip():
            QMessageBox.warning(self, "Ошибка", "Комментарий к отклонению обязателен")
            return
        
        try:
            result = self.moderation_service.reject_request(
                moderator_id=self.user_data['user_id'],
                request_id=self.selected_request['request_id'],
                comment=comment.strip()
            )
            
            if result['success']:
                QMessageBox.information(self, "Успех", "Заявка отклонена")
                self.request_processed.emit()
                self.load_pending_requests()
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отклонить заявку: {str(e)}")
    
    def get_comment_dialog(self, title, label, required=False):
        """Диалог для ввода комментария"""
        from PyQt6.QtWidgets import QInputDialog
        
        comment, ok = QInputDialog.getMultiLineText(
            self, title, label
        )
        
        if ok and required and not comment.strip():
            QMessageBox.warning(self, "Ошибка", "Комментарий обязателен")
            return self.get_comment_dialog(title, label, required)
        
        return comment, ok
    
    def apply_filters(self):
        """Применение фильтров"""
        self.load_pending_requests()
    
    def load_history(self):
        """Загрузка истории модерации"""
        try:
            # Пока загружаем общую историю, в будущем можно добавить фильтрацию по пользователю
            history = self.moderation_service.get_user_moderation_history(
                user_id=self.user_data['user_id'],  # История всех пользователей
                requesting_user_id=self.user_data['user_id'],
                offset=0,
                limit=200
            )
            
            self.populate_history_table(history['history'])
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {str(e)}")
    
    def populate_history_table(self, history_data):
        """Заполнение таблицы истории"""
        self.history_table.setRowCount(len(history_data))
        
        for row, record in enumerate(history_data):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(record['request_id'])))
            self.history_table.setItem(row, 1, QTableWidgetItem(record['entity_type']))
            self.history_table.setItem(row, 2, QTableWidgetItem(record['operation_type']))
            self.history_table.setItem(row, 3, QTableWidgetItem(record.get('requester_username', 'Неизвестно')))
            self.history_table.setItem(row, 4, QTableWidgetItem(record['status']))
            self.history_table.setItem(row, 5, QTableWidgetItem(record.get('reviewer_username', '')))
            
            reviewed_at = record.get('reviewed_at')
            if reviewed_at:
                if isinstance(reviewed_at, datetime):
                    date_str = reviewed_at.strftime('%d.%m.%Y %H:%M')
                else:
                    date_str = str(reviewed_at)
            else:
                date_str = ''
            self.history_table.setItem(row, 6, QTableWidgetItem(date_str))
    
    def load_statistics(self):
        """Загрузка статистики модерации"""
        try:
            period_days = self.stats_period.value()
            stats = self.moderation_service.get_moderation_statistics(
                admin_id=self.user_data['user_id'],
                period_days=period_days
            )
            
            self.display_statistics(stats)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить статистику: {str(e)}")
    
    def display_statistics(self, stats):
        """Отображение статистики"""
        text = f"""Статистика модерации за последние {self.stats_period.value()} дней:

Общее количество заявок: {stats.get('total_requests', 0)}
• На рассмотрении: {stats.get('pending_requests', 0)}
• Одобрено: {stats.get('approved_requests', 0)}
• Отклонено: {stats.get('rejected_requests', 0)}

Среднее время обработки: {stats.get('avg_processing_hours', 0):.1f} часов

Заявки по типам сущностей:
"""
        
        requests_by_type = stats.get('requests_by_type', {})
        if isinstance(requests_by_type, dict):
            for entity_type, count in requests_by_type.items():
                text += f"• {entity_type}: {count}\n"
        
        text += "\nТоп модераторов:\n"
        
        moderators = stats.get('most_active_moderators', [])
        if isinstance(moderators, list):
            for mod in moderators[:5]:  # Показываем топ-5
                username = mod.get('username', 'Неизвестно')
                approved = mod.get('approved_count', 0)
                rejected = mod.get('rejected_count', 0)
                total = approved + rejected
                text += f"• {username}: {total} заявок (одобрено: {approved}, отклонено: {rejected})\n"
        
        self.stats_display.setPlainText(text)
    
    def cleanup_old_requests(self):
        """Очистка старых заявок"""
        days_old = self.cleanup_days.value()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить все обработанные заявки старше {days_old} дней?\n"
            "Это действие необратимо!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            result = self.moderation_service.cleanup_old_requests(
                admin_id=self.user_data['user_id'],
                days_old=days_old
            )
            
            if result['success']:
                QMessageBox.information(
                    self, "Успех",
                    f"Удалено {result['deleted_count']} старых заявок"
                )
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Неизвестная ошибка'))
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить очистку: {str(e)}")
    
    def update_header_stats(self):
        """Обновление статистики в заголовке"""
        try:
            stats = self.moderation_service.get_moderation_statistics(
                admin_id=self.user_data['user_id'],
                period_days=7  # За последнюю неделю
            )
            
            pending = stats.get('pending_requests', 0)
            total = stats.get('total_requests', 0)
            avg_hours = stats.get('avg_processing_hours', 0)
            
            self.stats_label.setText(
                f"За 7 дней: {total} заявок | На рассмотрении: {pending} | "
                f"Среднее время: {avg_hours:.1f}ч"
            )
            
        except:
            self.stats_label.setText("Статистика недоступна")
    
    def refresh_current_tab(self):
        """Обновление текущей вкладки"""
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # Заявки на рассмотрение
            self.load_pending_requests()
        elif current_index == 1:  # История
            self.load_history()
        elif current_index == 2:  # Статистика
            self.load_statistics()
    
    def closeEvent(self, event):
        """Обработка закрытия диалога"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        event.accept()
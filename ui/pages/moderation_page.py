from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QFormLayout, QComboBox, QProgressBar,
                             QFrame, QHeaderView, QMessageBox, QSplitter,
                             QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor
from datetime import datetime
import json
from services import ModerationService
from ui.dialogs.moderation_dialog import ModerationDialog

class ModerationPage(QWidget):
    """Страница модерации в главном окне"""
    
    request_processed = pyqtSignal()  # Сигнал об обработке заявки
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.moderation_service = ModerationService()
        self.current_requests = []
        
        # Проверяем права доступа
        if user_data.get('role_id', 1) < 2:
            self.setup_no_access_ui()
            return
        
        self.setup_ui()
        self.load_data()
        
        # Автообновление каждые 60 секунд
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_data)
        self.update_timer.start(60000)
    
    def setup_no_access_ui(self):
        """UI для пользователей без доступа к модерации"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Иконка блокировки
        icon_label = QLabel("🔒")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px; color: #ccc; margin: 20px;")
        
        # Сообщение
        message_label = QLabel("Доступ к системе модерации ограничен")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("", 16))
        message_label.setStyleSheet("color: #666; margin: 10px;")
        
        # Описание
        desc_label = QLabel("Для доступа к функциям модерации требуются права модератора или администратора.")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #999; margin: 10px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label)
        layout.addWidget(desc_label)
        layout.addStretch()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок страницы
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Модерация")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Индикатор новых заявок
        self.notification_label = QLabel()
        self.notification_label.setStyleSheet("""
            QLabel {
                background-color: #f44336;
                color: white;
                padding: 4px 8px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.notification_label.hide()
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.notification_label)
        header_layout.addStretch()
        
        # Кнопка открытия полного интерфейса модерации
        open_moderation_button = QPushButton("Открыть систему модерации")
        open_moderation_button.clicked.connect(self.open_moderation_dialog)
        open_moderation_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        header_layout.addWidget(open_moderation_button)
        
        layout.addLayout(header_layout)
        
        # Дашборд статистики
        self.create_dashboard_section(layout)
        
        # Последние заявки
        self.create_recent_requests_section(layout)
        
        # Быстрые действия
        self.create_quick_actions_section(layout)
    
    def create_dashboard_section(self, parent_layout):
        """Создание секции дашборда"""
        dashboard_group = QGroupBox("Обзор")
        dashboard_layout = QVBoxLayout(dashboard_group)
        
        # Карточки статистики
        cards_layout = QHBoxLayout()
        
        # Карточка "Ожидают рассмотрения"
        self.pending_card = self.create_stat_card("Ожидают", "0", "#FF9800")
        cards_layout.addWidget(self.pending_card)
        
        # Карточка "Обработано сегодня"
        self.today_card = self.create_stat_card("Сегодня", "0", "#4CAF50")
        cards_layout.addWidget(self.today_card)
        
        # Карточка "За неделю"
        self.week_card = self.create_stat_card("За неделю", "0", "#2196F3")
        cards_layout.addWidget(self.week_card)
        
        # Карточка "Среднее время"
        self.avg_time_card = self.create_stat_card("Ср. время", "0ч", "#9C27B0")
        cards_layout.addWidget(self.avg_time_card)
        
        dashboard_layout.addLayout(cards_layout)
        
        # Прогресс-бар загрузки
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate progress
        self.loading_bar.hide()
        dashboard_layout.addWidget(self.loading_bar)
        
        parent_layout.addWidget(dashboard_group)
    
    def create_stat_card(self, title, value, color):
        """Создание карточки статистики"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                background-color: white;
                margin: 5px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        
        # Значение
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 5px;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Сохраняем ссылку на label для обновления
        card.value_label = value_label
        
        return card
    
    def create_recent_requests_section(self, parent_layout):
        """Создание секции последних заявок"""
        requests_group = QGroupBox("Последние заявки")
        requests_layout = QVBoxLayout(requests_group)
        
        # Таблица заявок (упрощенная версия)
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(5)
        self.requests_table.setHorizontalHeaderLabels([
            'ID', 'Тип', 'Операция', 'Пользователь', 'Статус'
        ])
        
        # Настройка таблицы
        self.requests_table.setMaximumHeight(200)
        self.requests_table.setAlternatingRowColors(True)
        self.requests_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.requests_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Двойной клик для открытия модерации
        self.requests_table.itemDoubleClicked.connect(self.open_moderation_dialog)
        
        requests_layout.addWidget(self.requests_table)
        
        # Кнопка "Показать все"
        show_all_layout = QHBoxLayout()
        show_all_layout.addStretch()
        
        show_all_button = QPushButton("Показать все заявки")
        show_all_button.clicked.connect(self.open_moderation_dialog)
        show_all_button.setStyleSheet("""
            QPushButton {
                color: #2196F3;
                border: none;
                text-decoration: underline;
                background: transparent;
                padding: 5px;
            }
            QPushButton:hover {
                color: #1976D2;
            }
        """)
        
        show_all_layout.addWidget(show_all_button)
        requests_layout.addLayout(show_all_layout)
        
        parent_layout.addWidget(requests_group)
    
    def create_quick_actions_section(self, parent_layout):
        """Создание секции быстрых действий"""
        actions_group = QGroupBox("Быстрые действия")
        actions_layout = QHBoxLayout(actions_group)
        
        # Кнопка просмотра ожидающих заявок
        pending_button = QPushButton("Ожидающие заявки")
        pending_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxQuestion))
        pending_button.clicked.connect(lambda: self.open_moderation_dialog(filter_pending=True))
        
        # Кнопка статистики
        stats_button = QPushButton("Статистика")
        stats_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        stats_button.clicked.connect(lambda: self.open_moderation_dialog(show_stats=True))
        
        # Кнопка обновления
        refresh_button = QPushButton("Обновить")
        refresh_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_BrowserReload))
        refresh_button.clicked.connect(self.load_data)
        
        actions_layout.addWidget(pending_button)
        actions_layout.addWidget(stats_button)
        actions_layout.addWidget(refresh_button)
        actions_layout.addStretch()
        
        parent_layout.addWidget(actions_group)
    
    def load_data(self):
        """Загрузка данных"""
        if self.user_data.get('role_id', 1) < 2:
            return
        
        self.loading_bar.show()
        
        try:
            # Загружаем статистику
            self.load_statistics()
            
            # Загружаем последние заявки
            self.load_recent_requests()
            
        except Exception as e:
            print(f"Ошибка загрузки данных модерации: {e}")
        finally:
            self.loading_bar.hide()
    
    def load_statistics(self):
        """Загрузка статистики"""
        try:
            # Статистика за неделю
            stats = self.moderation_service.get_moderation_statistics(
                admin_id=self.user_data['user_id'],
                period_days=7
            )
            
            # Обновляем карточки
            self.pending_card.value_label.setText(str(stats.get('pending_requests', 0)))
            
            # Подсчитываем обработанные сегодня (приблизительно)
            total_week = stats.get('approved_requests', 0) + stats.get('rejected_requests', 0)
            today_processed = max(0, total_week // 7)  # Грубая оценка
            self.today_card.value_label.setText(str(today_processed))
            
            self.week_card.value_label.setText(str(stats.get('total_requests', 0)))
            
            avg_hours = stats.get('avg_processing_hours', 0)
            if avg_hours > 24:
                avg_text = f"{avg_hours/24:.1f}д"
            else:
                avg_text = f"{avg_hours:.1f}ч"
            self.avg_time_card.value_label.setText(avg_text)
            
            # Обновляем уведомление
            pending_count = stats.get('pending_requests', 0)
            if pending_count > 0:
                self.notification_label.setText(f"{pending_count} новых")
                self.notification_label.show()
            else:
                self.notification_label.hide()
                
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")
    
    def load_recent_requests(self):
        """Загрузка последних заявок"""
        try:
            result = self.moderation_service.get_pending_requests(
                moderator_id=self.user_data['user_id'],
                filters={'offset': 0, 'limit': 10}
            )
            
            self.current_requests = result['requests']
            self.populate_requests_table()
            
        except Exception as e:
            print(f"Ошибка загрузки заявок: {e}")
    
    def populate_requests_table(self):
        """Заполнение таблицы заявок"""
        self.requests_table.setRowCount(len(self.current_requests))
        
        for row, request in enumerate(self.current_requests):
            # ID заявки
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(request['request_id'])))
            
            # Тип сущности
            self.requests_table.setItem(row, 1, QTableWidgetItem(request['entity_type']))
            
            # Тип операции
            operation_item = QTableWidgetItem(request['operation_type'])
            if request['operation_type'] == 'CREATE':
                operation_item.setBackground(QColor('#E8F5E8'))
            elif request['operation_type'] == 'UPDATE':
                operation_item.setBackground(QColor('#FFF3E0'))
            elif request['operation_type'] == 'DELETE':
                operation_item.setBackground(QColor('#FFEBEE'))
            
            self.requests_table.setItem(row, 2, operation_item)
            
            # Пользователь
            username = request.get('requester_username', 'Неизвестно')
            self.requests_table.setItem(row, 3, QTableWidgetItem(username))
            
            # Статус
            status_item = QTableWidgetItem(request['status'])
            if request['status'] == 'PENDING':
                status_item.setBackground(QColor('#FFF3E0'))
            elif request['status'] == 'APPROVED':
                status_item.setBackground(QColor('#E8F5E8'))
            elif request['status'] == 'REJECTED':
                status_item.setBackground(QColor('#FFEBEE'))
            
            self.requests_table.setItem(row, 4, status_item)
    
    def open_moderation_dialog(self, filter_pending=False, show_stats=False):
        """Открытие диалога модерации"""
        try:
            dialog = ModerationDialog(self.user_data, self)
            
            # Настройка диалога в зависимости от параметров
            if filter_pending:
                # Устанавливаем фильтр на ожидающие заявки
                dialog.status_filter.setCurrentText('PENDING')
                dialog.apply_filters()
            elif show_stats and hasattr(dialog, 'tab_widget'):
                # Переключаемся на вкладку статистики
                for i in range(dialog.tab_widget.count()):
                    if dialog.tab_widget.tabText(i) == "Статистика":
                        dialog.tab_widget.setCurrentIndex(i)
                        break
            
            # Подключаем сигнал обновления
            dialog.request_processed.connect(self.load_data)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть систему модерации: {str(e)}")
    
    def closeEvent(self, event):
        """Обработка закрытия страницы"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        event.accept()
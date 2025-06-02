# ui/windows/user_management_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from services import UserService

class UserManagementWindow(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.user_service = UserService()
        self.current_users = []
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        self.setWindowTitle("Управление пользователями")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title = QLabel("Управление пользователями")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_users)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Фильтры
        filter_layout = QHBoxLayout()
        
        # Поиск по имени
        filter_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите имя пользователя...")
        self.search_edit.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_edit)
        
        # Фильтр по роли
        filter_layout.addWidget(QLabel("Роль:"))
        self.role_filter = QComboBox()
        self.role_filter.addItems(["Все", "Пользователь", "Модератор", "Администратор"])
        self.role_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.role_filter)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Таблица пользователей
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Имя пользователя", "Email", "Роль", "Дата регистрации", "Действия"
        ])
        
        # Настройка таблицы
        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.users_table)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.change_role_btn = QPushButton("Изменить роль")
        self.change_role_btn.clicked.connect(self.change_user_role)
        self.change_role_btn.setEnabled(False)
        actions_layout.addWidget(self.change_role_btn)
        
        self.view_activity_btn = QPushButton("Показать активность")
        self.view_activity_btn.clicked.connect(self.view_user_activity)
        self.view_activity_btn.setEnabled(False)
        actions_layout.addWidget(self.view_activity_btn)
        
        actions_layout.addStretch()
        
        # Статистика
        self.stats_label = QLabel("Пользователей: 0")
        actions_layout.addWidget(self.stats_label)
        
        layout.addLayout(actions_layout)
        
        # Кнопки диалога
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Подключение сигналов
        self.users_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.users_table.itemDoubleClicked.connect(self.view_user_details)
    
    def load_users(self):
        """Загрузка списка пользователей"""
        try:
            users = self.user_service.get_users_list(
                self.user_data['user_id'],
                search_term=self.search_edit.text().strip() or None,
                role_filter=self.get_role_filter_value()
            )
            
            self.current_users = users
            self.populate_table()
            self.update_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пользователей: {str(e)}")
    
    def get_role_filter_value(self):
        """Получение значения фильтра роли"""
        role_text = self.role_filter.currentText()
        role_map = {
            "Пользователь": 1,
            "Модератор": 2,
            "Администратор": 3
        }
        return role_map.get(role_text)
    
    def populate_table(self):
        """Заполнение таблицы пользователями"""
        self.users_table.setRowCount(len(self.current_users))
        
        for row, user in enumerate(self.current_users):
            # ID
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['user_id'])))
            
            # Имя пользователя
            username_item = QTableWidgetItem(user['username'])
            if user['user_id'] == self.user_data['user_id']:
                username_item.setBackground(QColor('#e8f4fd'))  # Выделяем текущего пользователя
            self.users_table.setItem(row, 1, username_item)
            
            # Email
            self.users_table.setItem(row, 2, QTableWidgetItem(user['email']))
            
            # Роль
            role_name = self.get_role_name(user['role_id'])
            role_item = QTableWidgetItem(role_name)
            
            # Цветовое кодирование ролей
            if user['role_id'] == 3:  # Админ
                role_item.setBackground(QColor('#f8d7da'))
            elif user['role_id'] == 2:  # Модератор
                role_item.setBackground(QColor('#d4edda'))
            
            self.users_table.setItem(row, 3, role_item)
            
            # Дата регистрации
            created_date = user['created_at'].strftime('%d.%m.%Y') if user.get('created_at') else 'Неизвестно'
            self.users_table.setItem(row, 4, QTableWidgetItem(created_date))
            
            # Кнопки действий
            actions_widget = self.create_action_buttons(user, row)
            self.users_table.setCellWidget(row, 5, actions_widget)
    
    def create_action_buttons(self, user, row):
        """Создание кнопок действий для пользователя"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Кнопка изменения роли (только если не текущий пользователь)
        if user['user_id'] != self.user_data['user_id']:
            role_btn = QPushButton("Роль")
            role_btn.setMaximumWidth(60)
            role_btn.clicked.connect(lambda: self.change_specific_user_role(user))
            layout.addWidget(role_btn)
        
        # Кнопка активности
        activity_btn = QPushButton("История")
        activity_btn.setMaximumWidth(80)
        activity_btn.clicked.connect(lambda: self.view_specific_user_activity(user))
        layout.addWidget(activity_btn)
        
        return widget
    
    def get_role_name(self, role_id):
        """Получение названия роли по ID"""
        roles = {1: "Пользователь", 2: "Модератор", 3: "Администратор"}
        return roles.get(role_id, "Неизвестно")
    
    def apply_filters(self):
        """Применение фильтров"""
        self.load_users()
    
    def update_stats(self):
        """Обновление статистики"""
        total = len(self.current_users)
        admins = len([u for u in self.current_users if u['role_id'] == 3])
        moderators = len([u for u in self.current_users if u['role_id'] == 2])
        
        self.stats_label.setText(f"Всего: {total}, Админов: {admins}, Модераторов: {moderators}")
    
    def on_selection_changed(self):
        """Обработка изменения выделения"""
        has_selection = len(self.users_table.selectedItems()) > 0
        selected_user = self.get_selected_user()
        
        # Нельзя изменять роль самому себе
        can_change_role = has_selection and selected_user and selected_user['user_id'] != self.user_data['user_id']
        
        self.change_role_btn.setEnabled(can_change_role)
        self.view_activity_btn.setEnabled(has_selection)
    
    def get_selected_user(self):
        """Получение выбранного пользователя"""
        selected_items = self.users_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            if row < len(self.current_users):
                return self.current_users[row]
        return None
    
    def change_user_role(self):
        """Изменение роли выбранного пользователя"""
        selected_user = self.get_selected_user()
        if selected_user:
            self.change_specific_user_role(selected_user)
    
    def change_specific_user_role(self, user):
        """Изменение роли конкретного пользователя"""
        if user['user_id'] == self.user_data['user_id']:
            QMessageBox.warning(self, "Предупреждение", "Нельзя изменить собственную роль")
            return
        
        # Диалог выбора новой роли
        current_role = self.get_role_name(user['role_id'])
        
        roles = ["Пользователь", "Модератор", "Администратор"]
        new_role, ok = QInputDialog.getItem(
            self, "Изменение роли", 
            f"Выберите новую роль для пользователя {user['username']}:\nТекущая роль: {current_role}",
            roles, 0, False
        )
        
        if not ok:
            return
        
        # Конвертируем название роли в ID
        role_map = {"Пользователь": 1, "Модератор": 2, "Администратор": 3}
        new_role_id = role_map[new_role]
        
        if new_role_id == user['role_id']:
            QMessageBox.information(self, "Информация", "Роль не изменилась")
            return
        
        # Подтверждение
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Изменить роль пользователя {user['username']} с '{current_role}' на '{new_role}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            result = self.user_service.change_user_role(
                self.user_data['user_id'],
                user['user_id'],
                new_role_id
            )
            
            if result['success']:
                QMessageBox.information(self, "Успех", f"Роль пользователя {user['username']} изменена на '{new_role}'")
                self.load_users()  # Обновляем список
            else:
                QMessageBox.warning(self, "Ошибка", result.get('message', 'Не удалось изменить роль'))
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении роли: {str(e)}")
    
    def view_user_activity(self):
        """Просмотр активности выбранного пользователя"""
        selected_user = self.get_selected_user()
        if selected_user:
            self.view_specific_user_activity(selected_user)
    
    def view_specific_user_activity(self, user):
        """Просмотр активности конкретного пользователя"""
        dialog = UserActivityDialog(user, self.user_data, self)
        dialog.exec()
    
    def view_user_details(self, item):
        """Просмотр деталей пользователя при двойном клике"""
        row = item.row()
        if row < len(self.current_users):
            user = self.current_users[row]
            self.view_specific_user_activity(user)


class UserActivityDialog(QDialog):
    """Диалог для просмотра активности пользователя"""
    
    def __init__(self, user, admin_data, parent=None):
        super().__init__(parent)
        self.user = user
        self.admin_data = admin_data
        self.setup_ui()
        self.load_activity()
    
    def setup_ui(self):
        self.setWindowTitle(f"Активность пользователя: {self.user['username']}")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Информация о пользователе
        info_layout = QFormLayout()
        info_layout.addRow("Пользователь:", QLabel(self.user['username']))
        info_layout.addRow("Email:", QLabel(self.user['email']))
        info_layout.addRow("Роль:", QLabel(self.get_role_name(self.user['role_id'])))
        
        created_date = self.user['created_at'].strftime('%d.%m.%Y %H:%M') if self.user.get('created_at') else 'Неизвестно'
        info_layout.addRow("Регистрация:", QLabel(created_date))
        
        layout.addLayout(info_layout)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        
        # Период активности
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Период:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 дней", "30 дней", "90 дней"])
        self.period_combo.currentTextChanged.connect(self.load_activity)
        period_layout.addWidget(self.period_combo)
        
        period_layout.addStretch()
        
        layout.addLayout(period_layout)
        
        # Таблица активности
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels([
            "Дата", "Действие", "Сущность", "Описание"
        ])
        
        header = self.activity_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.activity_table)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def get_role_name(self, role_id):
        """Получение названия роли"""
        roles = {1: "Пользователь", 2: "Модератор", 3: "Администратор"}
        return roles.get(role_id, "Неизвестно")
    
    def load_activity(self):
        """Загрузка активности пользователя"""
        try:
            # Здесь должен быть вызов сервиса для получения активности пользователя
            # Пока создаем заглушку
            
            period_text = self.period_combo.currentText()
            days = int(period_text.split()[0])
            
            # Заглушка данных активности
            sample_activities = [
                {
                    'date': '25.05.2024 14:30',
                    'action': 'Создание персоны',
                    'entity': 'PERSON',
                    'description': 'Создал персону "Иван Петров"'
                },
                {
                    'date': '24.05.2024 16:15',
                    'action': 'Редактирование документа',
                    'entity': 'DOCUMENT',
                    'description': 'Отредактировал документ "Указ 1725 года"'
                },
                {
                    'date': '23.05.2024 11:45',
                    'action': 'Поиск',
                    'entity': 'SEARCH',
                    'description': 'Выполнил поиск "Петр I"'
                }
            ]
            
            self.activity_table.setRowCount(len(sample_activities))
            
            for row, activity in enumerate(sample_activities):
                self.activity_table.setItem(row, 0, QTableWidgetItem(activity['date']))
                self.activity_table.setItem(row, 1, QTableWidgetItem(activity['action']))
                self.activity_table.setItem(row, 2, QTableWidgetItem(activity['entity']))
                self.activity_table.setItem(row, 3, QTableWidgetItem(activity['description']))
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить активность: {str(e)}")
# ui/mixins/request_creation_mixin.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class RequestCreationMixin:
    """Миксин для добавления функциональности создания заявок на модерацию"""
    
    def add_request_buttons_to_layout(self, layout, entity_type):
        """Добавление кнопок создания заявок в layout"""
        if self.user_data['role_id'] < 2:  # Только для обычных пользователей
            request_layout = QHBoxLayout()
            
            create_btn = QPushButton(f"Создать заявку на добавление")
            create_btn.setStyleSheet("QPushButton { background-color: #d1ecf1; }")
            create_btn.clicked.connect(lambda: self.create_entity_request(entity_type, 'CREATE'))
            request_layout.addWidget(create_btn)
            
            request_layout.addStretch()
            
            help_label = QLabel("💡 Ваши изменения будут рассмотрены модераторами")
            help_label.setStyleSheet("color: #6c757d; font-size: 11px;")
            request_layout.addWidget(help_label)
            
            layout.addLayout(request_layout)
    
    def add_request_context_menu(self, table_widget, entity_type):
        """Добавление контекстного меню с заявками для таблицы"""
        if self.user_data['role_id'] < 2:  # Только для обычных пользователей
            table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table_widget.customContextMenuRequested.connect(
                lambda pos: self.show_request_context_menu(table_widget, pos, entity_type)
            )
    
    def show_request_context_menu(self, table_widget, pos, entity_type):
        """Показ контекстного меню с заявками"""
        item = table_widget.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(table_widget)
        
        # Заявка на изменение
        edit_action = menu.addAction("Создать заявку на изменение")
        edit_action.triggered.connect(lambda: self.create_edit_request(table_widget, entity_type))
        
        # Заявка на удаление
        delete_action = menu.addAction("Создать заявку на удаление")
        delete_action.triggered.connect(lambda: self.create_delete_request(table_widget, entity_type))
        
        menu.exec(table_widget.mapToGlobal(pos))
    
    def create_entity_request(self, entity_type, operation_type):
        """Создание заявки на сущность"""
        dialogs = {
            'PERSON': 'ui.dialogs.person_dialog',
            'COUNTRY': 'ui.dialogs.country_dialog', 
            'EVENT': 'ui.dialogs.event_dialog',
            'DOCUMENT': 'ui.dialogs.document_dialog',
            'SOURCE': 'ui.dialogs.source_dialog'
        }
        
        if entity_type in dialogs:
            try:
                module_name = dialogs[entity_type]
                module = __import__(module_name, fromlist=[''])
                dialog_class = getattr(module, f"{entity_type.title()}Dialog")
                
                dialog = dialog_class(None, self.user_data, self, request_mode=True)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    QMessageBox.information(
                        self, "Заявка создана", 
                        "Ваша заявка отправлена на рассмотрение модераторам"
                    )
                    if hasattr(self, 'refresh'):
                        self.refresh()
                        
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать заявку: {str(e)}")
    
    def create_edit_request(self, table_widget, entity_type):
        """Создание заявки на изменение"""
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        entity_id = int(table_widget.item(row, 0).text())  # Предполагаем, что ID в первой колонке
        
        dialogs = {
            'PERSON': 'ui.dialogs.person_dialog',
            'COUNTRY': 'ui.dialogs.country_dialog',
            'EVENT': 'ui.dialogs.event_dialog', 
            'DOCUMENT': 'ui.dialogs.document_dialog',
            'SOURCE': 'ui.dialogs.source_dialog'
        }
        
        if entity_type in dialogs:
            try:
                module_name = dialogs[entity_type]
                module = __import__(module_name, fromlist=[''])
                dialog_class = getattr(module, f"{entity_type.title()}Dialog")
                
                dialog = dialog_class(entity_id, self.user_data, self, request_mode=True)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    QMessageBox.information(
                        self, "Заявка создана",
                        "Ваша заявка на изменение отправлена на рассмотрение"
                    )
                    if hasattr(self, 'refresh'):
                        self.refresh()
                        
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать заявку: {str(e)}")
    
    def create_delete_request(self, table_widget, entity_type):
        """Создание заявки на удаление"""
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        entity_id = int(table_widget.item(row, 0).text())
        entity_name = table_widget.item(row, 1).text() if table_widget.columnCount() > 1 else "элемент"
        
        # Запрашиваем причину удаления
        reason, ok = QInputDialog.getMultiLineText(
            self, "Причина удаления",
            f"Укажите причину удаления '{entity_name}':"
        )
        
        if not ok or not reason.strip():
            return
        
        # Подтверждение
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Создать заявку на удаление '{entity_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Вызываем соответствующий сервис для создания заявки на удаление
            services = {
                'PERSON': 'PersonService',
                'COUNTRY': 'CountryService',
                'EVENT': 'EventService',
                'DOCUMENT': 'DocumentService', 
                'SOURCE': 'SourceService'
            }
            
            if entity_type in services:
                service_name = services[entity_type]
                service = getattr(self, f"{entity_type.lower()}_service", None)
                
                if service and hasattr(service, 'delete_person_request'):
                    # Используем метод создания заявки на удаление
                    method_name = f"delete_{entity_type.lower()}_request"
                    if hasattr(service, method_name):
                        method = getattr(service, method_name)
                        result = method(self.user_data['user_id'], entity_id, reason.strip())
                        
                        if result.get('success'):
                            QMessageBox.information(
                                self, "Заявка создана",
                                "Ваша заявка на удаление отправлена на рассмотрение"
                            )
                            if hasattr(self, 'refresh'):
                                self.refresh()
                        else:
                            QMessageBox.warning(
                                self, "Ошибка", 
                                result.get('message', 'Не удалось создать заявку')
                            )
                    else:
                        QMessageBox.warning(self, "Ошибка", "Функция недоступна")
                else:
                    QMessageBox.warning(self, "Ошибка", "Сервис недоступен")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заявку на удаление: {str(e)}")
    
    def show_moderation_status_indicator(self):
        """Показ индикатора статуса модерации для обычных пользователей"""
        if self.user_data['role_id'] < 2:
            status_label = QLabel("📋 Ваши изменения проходят модерацию")
            status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 5px;
                    color: #856404;
                }
            """)
            return status_label
        return None
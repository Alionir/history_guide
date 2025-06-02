from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class BasePage(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setup_ui()
    
    def setup_ui(self):
        """Базовая настройка UI - переопределяется в дочерних классах"""
        pass
    
    def refresh(self):
        """Обновление данных на странице"""
        pass

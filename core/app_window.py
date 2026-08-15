from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QStackedWidget, QFrame, QPushButton, QLabel)
from PySide6.QtCore import Qt, QSize
from .welcome_widget import WelcomeWidget
from modules.dossier_technique.widget import DossierTechniqueWidget

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CadGen Studio - AutoCAD Edition")
        self.resize(1280, 800)
        
        self.init_ui()
        
    def init_ui(self):
        # Central widget is a vertical layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header (formerly Sidebar)
        self.header = QFrame()
        self.header.setObjectName("Header")
        self.header.setFixedHeight(50)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(10)
        
        # Header Modules
        self.btn_home = QPushButton("🏠 Accueil")
        self.btn_home.setObjectName("HeaderButton")
        self.btn_home.setCheckable(True)
        self.btn_home.setChecked(True)
        self.btn_home.clicked.connect(lambda: self.switch_module(0, self.btn_home))
        header_layout.addWidget(self.btn_home)
        
        self.btn_dossier = QPushButton("📐 Dossier Technique")
        self.btn_dossier.setObjectName("HeaderButton")
        self.btn_dossier.setCheckable(True)
        self.btn_dossier.clicked.connect(lambda: self.switch_module(1, self.btn_dossier))
        header_layout.addWidget(self.btn_dossier)
        
        header_layout.addStretch()
        
        # 2. Main Stack
        self.stack = QStackedWidget()
        
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.start_module_requested.connect(lambda m: self.switch_module(1, self.btn_dossier))
        self.stack.addWidget(self.welcome_widget)
        
        self.dossier_widget = DossierTechniqueWidget()
        self.stack.addWidget(self.dossier_widget)
        
        # Add to main layout
        main_layout.addWidget(self.header)
        main_layout.addWidget(self.stack)
        
        self.current_button = self.btn_home

    def switch_module(self, index, button):
        self.stack.setCurrentIndex(index)
        
        # Update button states
        if self.current_button and self.current_button != button:
            self.current_button.setChecked(False)
            
        self.current_button = button
        self.current_button.setChecked(True)

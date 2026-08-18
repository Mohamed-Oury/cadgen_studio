from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QStackedWidget, QFrame, QPushButton, QLabel, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from .welcome_widget import WelcomeWidget
from modules.dossier_technique.widget import DossierTechniqueWidget
from modules.export_kml.widget import ExportKMLWidget
from modules.viewer_2d.widget import Viewer2DWidget
import qtawesome as qta

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CadGen Studio")
        self.resize(1280, 800)
        
        # Base style for sidebar and main window
        self.setStyleSheet("""
            QFrame#Sidebar {
                background-color: palette(window);
                border-right: 1px solid palette(mid);
            }
            QPushButton#SidebarButton {
                text-align: left;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-radius: 6px;
                margin: 2px 10px;
                background-color: transparent;
            }
            QPushButton#SidebarButton:hover {
                background-color: palette(midlight);
            }
            QPushButton#SidebarButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
            }
            QLabel#AppTitle {
                font-size: 18px;
                font-weight: bold;
                padding: 20px 10px;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        # Central widget is a horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(5)
        
        # App Title in Sidebar
        self.lbl_title = QLabel("CadGen Studio")
        self.lbl_title.setObjectName("AppTitle")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.lbl_title)
        
        # Sidebar Modules
        self.btn_home = QPushButton(" Accueil")
        self.btn_home.setIcon(qta.icon('fa5s.home'))
        self.btn_home.setObjectName("SidebarButton")
        self.btn_home.setCheckable(True)
        self.btn_home.setChecked(True)
        self.btn_home.clicked.connect(lambda: self.switch_module(0, self.btn_home))
        sidebar_layout.addWidget(self.btn_home)
        
        self.btn_dossier = QPushButton(" Dossier Technique")
        self.btn_dossier.setIcon(qta.icon('fa5s.drafting-compass'))
        self.btn_dossier.setObjectName("SidebarButton")
        self.btn_dossier.setCheckable(True)
        self.btn_dossier.clicked.connect(lambda: self.switch_module(1, self.btn_dossier))
        sidebar_layout.addWidget(self.btn_dossier)
        
        self.btn_export_kml = QPushButton(" Export Google Earth")
        self.btn_export_kml.setIcon(qta.icon('fa5s.globe-africa'))
        self.btn_export_kml.setObjectName("SidebarButton")
        self.btn_export_kml.setCheckable(True)
        self.btn_export_kml.clicked.connect(lambda: self.switch_module(2, self.btn_export_kml))
        sidebar_layout.addWidget(self.btn_export_kml)
        
        self.btn_viewer_2d = QPushButton(" Visionneuse 2D")
        self.btn_viewer_2d.setIcon(qta.icon('fa5s.search-location'))
        self.btn_viewer_2d.setObjectName("SidebarButton")
        self.btn_viewer_2d.setCheckable(True)
        self.btn_viewer_2d.clicked.connect(lambda: self.switch_module(3, self.btn_viewer_2d))
        sidebar_layout.addWidget(self.btn_viewer_2d)
        
        sidebar_layout.addStretch()
        
        # Settings / Exit at bottom
        self.btn_exit = QPushButton(" Quitter")
        self.btn_exit.setIcon(qta.icon('fa5s.sign-out-alt'))
        self.btn_exit.setObjectName("SidebarButton")
        self.btn_exit.clicked.connect(self.close)
        sidebar_layout.addWidget(self.btn_exit)
        sidebar_layout.addSpacing(20)
        
        # 2. Main Stack
        self.stack = QStackedWidget()
        
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.start_module_requested.connect(self._handle_module_request)
        self.stack.addWidget(self.welcome_widget)
        
        self.dossier_widget = DossierTechniqueWidget()
        self.stack.addWidget(self.dossier_widget)
        
        self.export_kml_widget = ExportKMLWidget()
        self.stack.addWidget(self.export_kml_widget)
        
        self.viewer_2d_widget = Viewer2DWidget()
        self.stack.addWidget(self.viewer_2d_widget)
        
        # Add to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        
        self.current_button = self.btn_home

    def _handle_module_request(self, module_id):
        if module_id == "generation-dossier-technique":
            self.switch_module(1, self.btn_dossier)
        elif module_id == "export-kml":
            self.switch_module(2, self.btn_export_kml)
        elif module_id == "viewer-2d":
            self.switch_module(3, self.btn_viewer_2d)

    def switch_module(self, index, button):
        self.stack.setCurrentIndex(index)
        
        # Update button states
        if self.current_button and self.current_button != button:
            self.current_button.setChecked(False)
            
        self.current_button = button
        self.current_button.setChecked(True)

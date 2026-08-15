import sys
from PySide6.QtWidgets import QApplication
from core.app_window import AppWindow
from core.theme import QGIS_THEME

def main():
    app = QApplication(sys.argv)
    
    # Set the QGIS light theme
    app.setStyleSheet(QGIS_THEME)
    
    window = AppWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

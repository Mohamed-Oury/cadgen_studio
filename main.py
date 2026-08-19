import sys
import os
# pyrefly: ignore [missing-import]
import qdarktheme
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QApplication
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QIcon
from core.app_window import AppWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logo.jpg")))
    
    # Setup modern theme (auto sync with OS) with Emerald Green primary color
    qdarktheme.setup_theme("auto", custom_colors={"primary": "#2ECC71"})
    
    window = AppWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

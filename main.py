import sys
import qdarktheme
from PySide6.QtWidgets import QApplication
from core.app_window import AppWindow

def main():
    app = QApplication(sys.argv)
    
    # Setup modern theme (auto sync with OS) with Emerald Green primary color
    qdarktheme.setup_theme("auto", custom_colors={"primary": "#2ECC71"})
    
    window = AppWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

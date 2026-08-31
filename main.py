import sys
import os
# pyrefly: ignore [missing-import]
import qdarktheme
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QApplication
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath
from PySide6.QtCore import Qt
from core.app_window import AppWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def create_rounded_icon(image_path, radius=60):
    src = QPixmap(image_path)
    if src.isNull():
        return QIcon(image_path)
        
    size = src.size()
    out = QPixmap(size)
    out.fill(Qt.transparent)
    
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    
    path = QPainterPath()
    path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
    
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, src)
    painter.end()
    
    return QIcon(out)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(create_rounded_icon(resource_path("assets/logo.jpg"), radius=150))
    
    # Setup modern theme (auto sync with OS) with Emerald Green primary color
    qdarktheme.setup_theme("auto", custom_colors={"primary": "#2ECC71"})
    
    window = AppWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

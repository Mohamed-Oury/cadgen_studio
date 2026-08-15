QGIS_THEME = """
/* QGIS Style Light Theme */

QWidget {
    background-color: #F0F0F0;
    color: #333333;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #F0F0F0;
}

QDockWidget {
    background-color: #E8E8E8;
    color: #333333;
}

QDockWidget::title {
    background-color: #D0D0D0;
    text-align: left;
    padding-left: 10px;
    padding-top: 4px;
    padding-bottom: 4px;
}

QFrame#Header {
    background-color: #E8E8E8;
    border-bottom: 1px solid #CCCCCC;
}

QPushButton#HeaderButton {
    background-color: transparent;
    color: #333333;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton#HeaderButton:hover {
    background-color: #D0D0D0;
}

QPushButton#HeaderButton:checked {
    background-color: #0078D7;
    color: #FFFFFF;
}

QPushButton {
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #B0B0B0;
    border-radius: 3px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #E0EFFF;
    border: 1px solid #0078D7;
}

QPushButton:pressed {
    background-color: #CCE4F7;
    color: #333333;
}

QPushButton#SidebarButton {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    text-align: left;
    padding: 10px 20px;
    font-size: 14px;
}

QPushButton#SidebarButton:hover {
    background-color: #D8D8D8;
}

QPushButton#SidebarButton:checked {
    background-color: #FFFFFF;
    border-left: 3px solid #0078D7;
    color: #0078D7;
    font-weight: bold;
}

QPushButton#PrimaryButton {
    background-color: #0078D7;
    color: #FFFFFF;
    font-weight: bold;
    border: none;
}

QPushButton#PrimaryButton:hover {
    background-color: #005A9E;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #B0B0B0;
    border-radius: 2px;
    padding: 4px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #0078D7;
}

QTableWidget {
    background-color: #FFFFFF;
    color: #333333;
    gridline-color: #E0E0E0;
    border: 1px solid #CCCCCC;
}

QHeaderView::section {
    background-color: #F0F0F0;
    color: #333333;
    padding: 4px;
    border: 1px solid #CCCCCC;
}

QTableWidget::item:selected {
    background-color: #CCE4F7;
    color: #333333;
}

QScrollBar:vertical {
    border: none;
    background-color: #F0F0F0;
    width: 14px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background-color: #C0C0C0;
    min-height: 20px;
    border-radius: 7px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A0A0A0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QLabel {
    color: #333333;
}

QLabel#WelcomeTitle {
    font-size: 28px;
    font-weight: bold;
    color: #0078D7;
}

QLabel#WelcomeSubtitle {
    font-size: 14px;
    color: #666666;
}
"""

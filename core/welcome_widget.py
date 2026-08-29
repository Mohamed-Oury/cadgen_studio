 # pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt, Signal
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QColor
# pyrefly: ignore [missing-import]
import qtawesome as qta

class WelcomeWidget(QWidget):
    start_module_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(40)

        # Hero Section
        title = QLabel("CadGen Studio")
        title.setObjectName("WelcomeTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: palette(text);")

        subtitle = QLabel("Outils Topographiques et Fonciers Avancés")
        subtitle.setObjectName("WelcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #A0AEC0; margin-bottom: 20px;")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Cards Section
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)
        cards_layout.setAlignment(Qt.AlignCenter)
        
        # Card 1: Dossier Technique
        card1 = self.create_module_card(
            title="Dossier Technique",
            desc="Générer des dossiers techniques à partir de fichiers DXF.",
            icon_name="fa5s.drafting-compass",
            module_id="generation-dossier-technique"
        )
        cards_layout.addWidget(card1)

        # Card 2: Export KML
        card2 = self.create_module_card(
            title="Export Google Earth",
            desc="Convertir vos plans DXF en KML/KMZ pour visualisation spatiale.",
            icon_name="fa5s.globe-africa",
            module_id="export-kml"
        )
        cards_layout.addWidget(card2)
        
        # Card 3: Visionneuse 2D
        card3 = self.create_module_card(
            title="Visionneuse 2D",
            desc="Visualiser et mesurer des distances et surfaces sur vos DXF.",
            icon_name="fa5s.search-location",
            module_id="viewer-2d"
        )
        cards_layout.addWidget(card3)
        
        main_layout.addLayout(cards_layout)

    def create_module_card(self, title, desc, icon_name, module_id):
        card = QFrame()
        card.setFixedSize(300, 220)
        card.setObjectName("ModuleCard")
        card.setStyleSheet("""
            QFrame#ModuleCard {
                background-color: palette(base);
                border-radius: 12px;
                border: 1px solid palette(midlight);
            }
            QFrame#ModuleCard:hover {
                border: 1px solid palette(primary);
                background-color: palette(window);
            }
        """)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon
        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon(icon_name, color='#2ECC71').pixmap(48, 48))
        lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_icon)
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: palette(text);")
        layout.addWidget(lbl_title)
        
        # Description
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setStyleSheet("font-size: 13px; color: #A0AEC0;")
        layout.addWidget(lbl_desc)
        
        layout.addStretch()
        
        # Button
        btn = QPushButton("Ouvrir")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: palette(primary);
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #27AE60;
            }
        """)
        btn.clicked.connect(lambda: self.start_module_requested.emit(module_id))
        layout.addWidget(btn)
        
        return card

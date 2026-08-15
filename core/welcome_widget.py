from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class WelcomeWidget(QWidget):
    start_module_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        title = QLabel("CadGen Studio")
        title.setObjectName("WelcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Outils Topographiques et Fonciers Avancés")
        subtitle.setObjectName("WelcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        btn_start = QPushButton("Ouvrir: Génération Dossier Technique")
        btn_start.setObjectName("PrimaryButton")
        btn_start.setFixedSize(300, 40)
        btn_start.clicked.connect(lambda: self.start_module_requested.emit("generation-dossier-technique"))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(btn_start, alignment=Qt.AlignCenter)

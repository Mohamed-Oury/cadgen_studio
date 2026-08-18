import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QFileDialog, QMessageBox, QFrame)
from PySide6.QtCore import Qt
import qtawesome as qta
from .interactive_view import InteractiveDXFView
from modules.dossier_technique.core.dxf_parser import DXFParser

class Viewer2DWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.dxf_filepath = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top Toolbar
        toolbar = QFrame()
        toolbar.setObjectName("Toolbar")
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("""
            QFrame#Toolbar {
                background-color: palette(base);
                border-radius: 8px;
                border: 1px solid palette(midlight);
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 5, 15, 5)
        toolbar_layout.setSpacing(15)

        # 1. Load Button
        self.btn_load = QPushButton(" Charger DXF")
        self.btn_load.setIcon(qta.icon('fa5s.folder-open'))
        self.btn_load.clicked.connect(self._load_dxf)
        toolbar_layout.addWidget(self.btn_load)
        
        # Zoom Extents Button
        self.btn_zoom = QPushButton(" Zoom Étendu")
        self.btn_zoom.setIcon(qta.icon('fa5s.expand'))
        self.btn_zoom.clicked.connect(lambda: self.viewer.zoom_extents())
        toolbar_layout.addWidget(self.btn_zoom)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(line)

        # 2. Mode Buttons
        self.btn_nav = QPushButton(" Navigation")
        self.btn_nav.setIcon(qta.icon('fa5s.hand-paper'))
        self.btn_nav.setCheckable(True)
        self.btn_nav.setChecked(True)
        self.btn_nav.clicked.connect(lambda: self._set_mode("nav"))
        
        self.btn_dist = QPushButton(" Mesurer Distance")
        self.btn_dist.setIcon(qta.icon('fa5s.ruler'))
        self.btn_dist.setCheckable(True)
        self.btn_dist.clicked.connect(lambda: self._set_mode("distance"))
        
        self.btn_area = QPushButton(" Surface du Lot")
        self.btn_area.setIcon(qta.icon('fa5s.vector-square'))
        self.btn_area.setCheckable(True)
        self.btn_area.clicked.connect(lambda: self._set_mode("area"))
        
        # Apply button styles for active state
        self._apply_mode_style([self.btn_nav, self.btn_dist, self.btn_area])
        
        toolbar_layout.addWidget(self.btn_nav)
        toolbar_layout.addWidget(self.btn_dist)
        toolbar_layout.addWidget(self.btn_area)
        
        toolbar_layout.addStretch()
        
        # Info labels right aligned
        self.lbl_info = QLabel("Aucun fichier chargé.")
        self.lbl_info.setStyleSheet("color: palette(mid); font-style: italic;")
        toolbar_layout.addWidget(self.lbl_info)

        main_layout.addWidget(toolbar)

        # Viewer
        self.viewer = InteractiveDXFView()
        self.viewer.distance_measured.connect(self._on_distance_measured)
        self.viewer.lot_info_found.connect(self._on_lot_info_found)
        main_layout.addWidget(self.viewer)

    def _apply_mode_style(self, buttons):
        style = """
            QPushButton {
                padding: 8px 15px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: palette(midlight);
            }
            QPushButton:checked {
                background-color: palette(primary);
                color: white;
                border: none;
                font-weight: bold;
            }
        """
        for btn in buttons:
            btn.setStyleSheet(style)

    def _set_mode(self, mode):
        self.btn_nav.setChecked(mode == "nav")
        self.btn_dist.setChecked(mode == "distance")
        self.btn_area.setChecked(mode == "area")
        
        self.viewer.set_mode(mode)
        
        if mode == "nav":
            self.lbl_info.setText("Mode: Panoramique & Zoom")
        elif mode == "distance":
            self.lbl_info.setText("Cliquez sur 2 points pour mesurer la distance.")
        elif mode == "area":
            self.lbl_info.setText("Cliquez à l'intérieur d'un lot pour afficher sa surface.")

    def _load_dxf(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier DXF", "", "Fichiers DXF (*.dxf)"
        )
        if filepath:
            self.dxf_filepath = filepath
            
            # Parse lots for area mode
            parser = DXFParser(filepath)
            success, msg = parser.load()
            if success:
                parser.extract_lots_and_ilots()
            else:
                parser = None
                
            # Render on view
            self.lbl_info.setText("Chargement en cours...")
            success, msg = self.viewer.load_dxf(filepath, dxf_parser=parser)
            
            if success:
                self.lbl_info.setText(f"Fichier chargé: {os.path.basename(filepath)}")
                self._set_mode("nav")
            else:
                QMessageBox.critical(self, "Erreur", msg)
                self.lbl_info.setText("Erreur de chargement.")

    def _on_distance_measured(self, distance):
        self.lbl_info.setText(f"Distance mesurée : {distance:.2f} m")

    def _on_lot_info_found(self, text, area):
        if area > 0:
            self.lbl_info.setText(f"{text} | Surface : {area:.2f} m²")
        else:
            self.lbl_info.setText(text)

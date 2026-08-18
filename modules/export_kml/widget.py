import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QFileDialog, QMessageBox, QComboBox, QGroupBox)
from PySide6.QtCore import Qt
import qtawesome as qta
from .core import KMLExporter

class ExportKMLWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.dxf_filepath = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("Export vers Google Earth (KML/KMZ)")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Convertissez vos fichiers DXF en fichiers géoréférencés pour Google Earth.")
        subtitle.setStyleSheet("color: palette(mid); font-size: 14px;")
        layout.addWidget(subtitle)

        # Settings Group
        group = QGroupBox("Paramètres d'Export")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(15)

        # DXF Selection
        dxf_layout = QHBoxLayout()
        self.lbl_dxf = QLabel("Aucun fichier sélectionné")
        self.lbl_dxf.setStyleSheet("color: palette(mid); font-style: italic;")
        
        btn_select_dxf = QPushButton(" Sélectionner Fichier DXF")
        btn_select_dxf.setIcon(qta.icon('fa5s.folder-open'))
        btn_select_dxf.clicked.connect(self._select_dxf)
        
        dxf_layout.addWidget(btn_select_dxf)
        dxf_layout.addWidget(self.lbl_dxf)
        dxf_layout.addStretch()
        group_layout.addLayout(dxf_layout)

        # EPSG Selection
        epsg_layout = QHBoxLayout()
        epsg_layout.addWidget(QLabel("Système de Coordonnées source :"))
        
        self.combo_epsg = QComboBox()
        self.combo_epsg.addItem("WGS 84 / UTM zone 30N (EPSG:32630)", "32630")
        self.combo_epsg.addItem("Adindan / UTM zone 30N (EPSG:28193)", "28193")
        self.combo_epsg.setMinimumWidth(300)
        
        epsg_layout.addWidget(self.combo_epsg)
        epsg_layout.addStretch()
        group_layout.addLayout(epsg_layout)

        layout.addWidget(group)

        # Export Button
        self.btn_export = QPushButton(" Générer le Fichier KML")
        self.btn_export.setIcon(qta.icon('fa5s.globe-africa'))
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: palette(primary);
                color: white;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27AE60;
            }
            QPushButton:disabled {
                background-color: palette(mid);
            }
        """)
        self.btn_export.clicked.connect(self._export_kml)
        layout.addWidget(self.btn_export, alignment=Qt.AlignRight)

        layout.addStretch()

    def _select_dxf(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le fichier DXF", "", "Fichiers DXF (*.dxf)"
        )
        if filepath:
            self.dxf_filepath = filepath
            self.lbl_dxf.setText(os.path.basename(filepath))
            self.lbl_dxf.setStyleSheet("color: palette(text); font-weight: bold;")
            self.btn_export.setEnabled(True)

    def _export_kml(self):
        if not self.dxf_filepath:
            return

        # Propose to save the KML
        default_name = os.path.splitext(os.path.basename(self.dxf_filepath))[0] + ".kml"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le fichier KML", default_name, "Google Earth KML (*.kml)"
        )

        if not save_path:
            return

        epsg_code = self.combo_epsg.currentData()
        
        # Disable button during export
        self.btn_export.setEnabled(False)
        self.btn_export.setText(" Génération en cours...")

        exporter = KMLExporter(self.dxf_filepath, epsg_code)
        success, message = exporter.export(save_path)

        # Re-enable button
        self.btn_export.setEnabled(True)
        self.btn_export.setText(" Générer le Fichier KML")

        if success:
            QMessageBox.information(self, "Succès", message)
        else:
            QMessageBox.critical(self, "Erreur", message)

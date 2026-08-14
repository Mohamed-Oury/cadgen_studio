from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QGroupBox, QLabel, QHBoxLayout, QComboBox)

class FormWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Groupe: Données Cibles
        group_cible = QGroupBox("Lot Sélectionné")
        layout_cible = QFormLayout(group_cible)
        
        self.lbl_ilot = QLabel("-")
        self.lbl_lot = QLabel("-")
        self.lbl_surface = QLabel("-")
        
        layout_cible.addRow("Îlot:", self.lbl_ilot)
        layout_cible.addRow("Lot:", self.lbl_lot)
        layout_cible.addRow("Surface calculée:", self.lbl_surface)
        
        layout.addWidget(group_cible)
        
        # Groupe: Informations Administratives
        group_admin = QGroupBox("Données Administratives")
        layout_admin = QFormLayout(group_admin)
        
        self.in_demandeur = QLineEdit()
        self.in_demandeur.setPlaceholderText("Ex: M. GBANE EL HADJ ABDOU")
        
        self.in_centre = QLineEdit()
        self.in_centre.setPlaceholderText("Ex: FERKESSEDOUGOU-WALOUROU")
        
        self.in_dossier = QLineEdit()
        self.in_dossier.setPlaceholderText("Ex: CK/0726/FERKE/DT_M. GBANE")
        
        self.in_tf = QLineEdit()
        self.in_tf.setPlaceholderText("Ex: 1070")
        
        self.in_livre_foncier = QLineEdit()
        self.in_livre_foncier.setPlaceholderText("Ex: KORHOGO")
        
        self.in_section = QLineEdit()
        self.in_section.setPlaceholderText("Ex: ...")
        
        self.in_date_consultation = QLineEdit()
        self.in_date_consultation.setPlaceholderText("Ex: 31-07-2026")
        
        layout_admin.addRow("Demandeur:", self.in_demandeur)
        layout_admin.addRow("Centre:", self.in_centre)
        layout_admin.addRow("N° Dossier:", self.in_dossier)
        layout_admin.addRow("T.F. No / Morcellement:", self.in_tf)
        layout_admin.addRow("Livre Foncier:", self.in_livre_foncier)
        layout_admin.addRow("Section:", self.in_section)
        layout_admin.addRow("Date de consultation:", self.in_date_consultation)
        
        layout.addWidget(group_admin)
        
        # Groupe: Configuration Echelles
        group_scales = QGroupBox("Configuration des Échelles")
        layout_scales = QFormLayout(group_scales)
        
        self.combo_scale_1 = QComboBox()
        self.combo_scale_1.addItems(["1/5 000", "1/2 500"])
        
        self.combo_scale_2 = QComboBox()
        self.combo_scale_2.addItems(["1/500", "1/200"])
        
        layout_scales.addRow("Plan Situation (Echelle 1):", self.combo_scale_1)
        layout_scales.addRow("Plan de Masse (Echelle 2):", self.combo_scale_2)
        
        layout.addWidget(group_scales)
        
        # Boutons
        layout_btn = QHBoxLayout()
        self.btn_preview = QPushButton("Aperçu PDF")
        self.btn_generate = QPushButton("Générer (PDF + DXF)")
        self.btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        layout_btn.addWidget(self.btn_preview)
        layout_btn.addWidget(self.btn_generate)
        
        layout.addLayout(layout_btn)
        
        layout.addStretch()

    def update_selection(self, ilot_name, lot_name, surface):
        self.lbl_ilot.setText(ilot_name)
        self.lbl_lot.setText(lot_name)
        self.lbl_surface.setText(f"{surface:.3f} m²")
        
    def get_data(self):
        return {
            "demandeur": self.in_demandeur.text(),
            "centre": self.in_centre.text(),
            "dossier": self.in_dossier.text(),
            "tf": self.in_tf.text(),
            "livre_foncier": self.in_livre_foncier.text(),
            "section": self.in_section.text(),
            "date_consultation": self.in_date_consultation.text(),
            "ilot": self.lbl_ilot.text(),
            "lot": self.lbl_lot.text(),
            "surface": self.lbl_surface.text(),
            "echelle_1": self.combo_scale_1.currentText(),
            "echelle_2": self.combo_scale_2.currentText()
        }

import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QLineEdit, QComboBox, QPushButton, QFormLayout, 
                                 QMessageBox, QGroupBox, QScrollArea, QFileDialog)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta

class AttributePanelWidget(QWidget):
    # Signal émis quand les attributs changent (utile pour rafraîchir la thématique)
    attributes_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dxf_filepath = None
        self.current_lot_id = None # e.g. "Ilot_1|Lot_1"
        self.attributes_db = {} # Format: {"Ilot_1|Lot_1": {"proprietaire": "...", "statut": "...", "titre": "...", "surface": 0.0}}
        self._setup_ui()
        self.setFixedWidth(300)
        self.hide() # Caché par défaut

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre du panneau
        header_layout = QHBoxLayout()
        title = QLabel("Table Attributaire")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        btn_close = QPushButton()
        btn_close.setIcon(qta.icon('fa5s.times'))
        btn_close.setFlat(True)
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close, alignment=Qt.AlignRight)
        
        main_layout.addLayout(header_layout)
        
        # Conteneur défilant
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 10, 0, 0)
        
        # Info du lot sélectionné
        self.group_lot = QGroupBox("Lot Sélectionné")
        lot_layout = QVBoxLayout(self.group_lot)
        self.lbl_lot_name = QLabel("Aucun lot sélectionné")
        self.lbl_lot_name.setStyleSheet("font-weight: bold; color: palette(primary);")
        lot_layout.addWidget(self.lbl_lot_name)
        
        self.lbl_lot_area = QLabel("Surface : -")
        lot_layout.addWidget(self.lbl_lot_area)
        
        content_layout.addWidget(self.group_lot)
        
        # Formulaire d'édition
        self.group_form = QGroupBox("Attributs (Métadonnées)")
        form_layout = QFormLayout(self.group_form)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        self.input_proprio = QLineEdit()
        self.input_proprio.setPlaceholderText("Nom du propriétaire...")
        form_layout.addRow("Propriétaire :", self.input_proprio)
        
        self.combo_statut = QComboBox()
        self.combo_statut.addItems(["Disponible", "Réservé", "Vendu"])
        form_layout.addRow("Statut :", self.combo_statut)
        
        self.input_titre = QLineEdit()
        self.input_titre.setPlaceholderText("N° Titre Foncier...")
        form_layout.addRow("Titre Foncier :", self.input_titre)
        
        content_layout.addWidget(self.group_form)
        
        # Bouton Sauvegarder
        self.btn_save = QPushButton(" Enregistrer")
        self.btn_save.setIcon(qta.icon('fa5s.save'))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: palette(primary);
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        self.btn_save.clicked.connect(self._save_current_lot)
        content_layout.addWidget(self.btn_save)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Boutons d'export en bas (fixés)
        export_layout = QHBoxLayout()
        
        self.btn_export_geojson = QPushButton(" GeoJSON")
        self.btn_export_geojson.setIcon(qta.icon('fa5s.file-export', color='#2ecc71'))
        self.btn_export_geojson.clicked.connect(self._export_geojson)
        export_layout.addWidget(self.btn_export_geojson)
        
        self.btn_export_html = QPushButton(" HTML")
        self.btn_export_html.setIcon(qta.icon('fa5s.globe', color='#3498db'))
        self.btn_export_html.clicked.connect(self._on_export_html)
        export_layout.addWidget(self.btn_export_html)
        
        self.btn_export_dxf = QPushButton(" DXF")
        self.btn_export_dxf.setIcon(qta.icon('fa5s.drafting-compass', color='#e67e22'))
        self.btn_export_dxf.clicked.connect(self._on_export_dxf_enrichi)
        export_layout.addWidget(self.btn_export_dxf)
        
        main_layout.addLayout(export_layout)

        self._enable_form(False)

    def _export_geojson(self):
        if not self.dxf_filepath:
            return
            
        base, _ = os.path.splitext(self.dxf_filepath)
        default_name = f"{base}.geojson"
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le fichier GeoJSON", default_name, "GeoJSON (*.geojson)"
        )
        
        if not save_path:
            return
            
        try:
            # On va récupérer les coordonnées depuis le viewer parent
            viewer = self.parent().findChild(QWidget, "Toolbar").parentWidget().findChild(QWidget, "").parentWidget().viewer
            # C'est plus sûr de récupérer le widget 2d
        except:
            pass
        
        # Pour être plus propre, je devrais passer le parser au panneau ou demander au parent
        parent_widget = self.parentWidget()
        while parent_widget and not hasattr(parent_widget, 'viewer'):
            parent_widget = parent_widget.parentWidget()
            
        if not parent_widget or not hasattr(parent_widget, 'viewer') or not parent_widget.viewer.dxf_parser:
            QMessageBox.warning(self, "Attention", "Aucun lot trouvé dans le fichier DXF.")
            return
            
        parser = parent_widget.viewer.dxf_parser
        features = []
        
        if hasattr(parser, 'ilots') and parser.ilots:
            for ilot_name, ilot_data in parser.ilots.items():
                for lot_name, lot_data in ilot_data["lots"].items():
                    poly = lot_data["geom"]
                    lot_id = f"{ilot_name}|{lot_name}"
                    
                    # Propriétés attributaires
                    props = {
                        "Ilot": ilot_name,
                        "Lot": lot_name,
                        "Surface": poly.area
                    }
                    db_props = self.attributes_db.get(lot_id, {})
                    props.update(db_props)
                    
                    # Géométrie (GeoJSON utilise Longitude, Latitude - ici on gardera les coordonnées locales EPSG si on ne connaît pas la source)
                    # Coordinates = [[[x, y], [x, y], ...]]
                    coords = [[list(coord) for coord in list(poly.exterior.coords)]]
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": coords
                        },
                        "properties": props
                    }
                    features.append(feature)
        
        # Fallback polylines (si aucun lot parsé via les calques standards)
        if not features and hasattr(parent_widget.viewer, 'doc') and parent_widget.viewer.doc:
            from shapely.geometry import Polygon
            msp = parent_widget.viewer.doc.modelspace()
            for entity in msp:
                if entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                    points = []
                    for p in entity.vertices():
                        if hasattr(p, 'dxf'):
                            points.append((p.dxf.location.x, p.dxf.location.y))
                        else:
                            points.append((p[0], p[1]))
                    if len(points) >= 3:
                        try:
                            poly = Polygon(points)
                            if poly.is_valid and poly.area > 0:
                                cx, cy = int(poly.centroid.x), int(poly.centroid.y)
                                lot_name = f"Poly_{cx}_{cy}"
                                ilot_name = entity.dxf.layer
                                lot_id = f"{ilot_name}|{lot_name}"
                                
                                props = {
                                    "Layer": ilot_name,
                                    "Surface": poly.area
                                }
                                db_props = self.attributes_db.get(lot_id, {})
                                props.update(db_props)
                                
                                coords = [[list(coord) for coord in list(poly.exterior.coords)]]
                                feature = {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": coords
                                    },
                                    "properties": props
                                }
                                features.append(feature)
                        except:
                            pass
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Succès", f"Export GeoJSON réussi : {len(features)} éléments.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export GeoJSON : {e}")

    def load_database(self, dxf_filepath):
        self.dxf_filepath = dxf_filepath
        self.attributes_db = {}
        self.current_lot_id = None
        self._enable_form(False)
        self.lbl_lot_name.setText("Aucun lot sélectionné")
        self.lbl_lot_area.setText("Surface : -")
        
        if not self.dxf_filepath:
            return
            
        json_path = self._get_json_path()
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.attributes_db = json.load(f)
            except Exception as e:
                print(f"Erreur de lecture DB locale: {e}")

    def _get_json_path(self):
        if not self.dxf_filepath:
            return ""
        base, _ = os.path.splitext(self.dxf_filepath)
        return f"{base}_cadgen.json"

    def _save_database(self):
        if not self.dxf_filepath:
            return
        json_path = self._get_json_path()
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.attributes_db, f, indent=4, ensure_ascii=False)
            self.attributes_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder : {e}")

    def set_selected_lot(self, ilot_name, lot_name, area):
        if not self.dxf_filepath:
            return
            
        self.current_lot_id = f"{ilot_name}|{lot_name}"
        self.lbl_lot_name.setText(f"Îlot: {ilot_name} | Lot: {lot_name}")
        self.lbl_lot_area.setText(f"Surface : {area:.2f} m²")
        
        # Charger les données si existantes
        data = self.attributes_db.get(self.current_lot_id, {})
        self.input_proprio.setText(data.get("proprietaire", ""))
        self.input_titre.setText(data.get("titre", ""))
        
        statut = data.get("statut", "Disponible")
        idx = self.combo_statut.findText(statut)
        if idx >= 0:
            self.combo_statut.setCurrentIndex(idx)
        else:
            self.combo_statut.setCurrentIndex(0)
            
        # Mettre à jour la surface en base
        if self.current_lot_id not in self.attributes_db:
            self.attributes_db[self.current_lot_id] = {}
        self.attributes_db[self.current_lot_id]["surface"] = area
            
        self._enable_form(True)
        self.show()

    def _save_current_lot(self):
        if not self.current_lot_id:
            return
            
        if self.current_lot_id not in self.attributes_db:
            self.attributes_db[self.current_lot_id] = {}
            
        self.attributes_db[self.current_lot_id].update({
            "proprietaire": self.input_proprio.text().strip(),
            "statut": self.combo_statut.currentText(),
            "titre": self.input_titre.text().strip()
        })
        
        self._save_database()
        
    def _enable_form(self, enabled):
        self.group_form.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)

    def _on_export_html(self):
        if not self.dxf_filepath:
            return
            
        base, _ = os.path.splitext(self.dxf_filepath)
        default_name = f"{base}_carte.html"
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer la carte HTML", default_name, "Fichier HTML (*.html)"
        )
        
        if not save_path:
            return
            
        from .exports import export_web_html
        export_web_html(self, self.attributes_db, save_path)

    def _on_export_dxf_enrichi(self):
        if not self.dxf_filepath:
            return
            
        base, _ = os.path.splitext(self.dxf_filepath)
        default_name = f"{base}_enrichi.dxf"
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le DXF enrichi", default_name, "Fichier DXF (*.dxf)"
        )
        
        if not save_path:
            return
            
        from .exports import export_dxf_enriched
        export_dxf_enriched(self, self.dxf_filepath, self.attributes_db, save_path)

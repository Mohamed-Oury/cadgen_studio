import os
import csv
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QFileDialog, QMessageBox, QFrame,
                                 QDialog, QListWidget, QListWidgetItem, QLineEdit,
                                 QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
                                 QComboBox)
# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt
# pyrefly: ignore [missing-import]
import qtawesome as qta
from .interactive_view import InteractiveDXFView
from modules.dossier_technique.core.dxf_parser import DXFParser
from .attributes_panel import AttributePanelWidget

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
        toolbar.setFixedHeight(110)
        toolbar.setStyleSheet("""
            QFrame#Toolbar {
                background-color: palette(base);
                border-radius: 8px;
                border: 1px solid palette(midlight);
            }
        """)
        
        toolbar_vlayout = QVBoxLayout(toolbar)
        toolbar_vlayout.setContentsMargins(15, 5, 15, 5)
        toolbar_vlayout.setSpacing(10)
        
        toolbar_layout_top = QHBoxLayout()
        toolbar_layout_bottom = QHBoxLayout()
        
        toolbar_vlayout.addLayout(toolbar_layout_top)
        toolbar_vlayout.addLayout(toolbar_layout_bottom)

        # 1. Load Button
        self.btn_load = QPushButton(" Charger DXF")
        self.btn_load.setIcon(qta.icon('fa5s.folder-open'))
        self.btn_load.clicked.connect(self._load_dxf)
        toolbar_layout_top.addWidget(self.btn_load)
        
        # Zoom Extents Button
        self.btn_zoom = QPushButton(" Zoom Étendu")
        self.btn_zoom.setIcon(qta.icon('fa5s.expand'))
        self.btn_zoom.clicked.connect(lambda: self.viewer.zoom_extents())
        toolbar_layout_top.addWidget(self.btn_zoom)
        
        # Zoom In Button
        self.btn_zoom_in = QPushButton("")
        self.btn_zoom_in.setIcon(qta.icon('fa5s.search-plus'))
        self.btn_zoom_in.clicked.connect(lambda: self.viewer.zoom_in())
        toolbar_layout_top.addWidget(self.btn_zoom_in)
        
        # Zoom Out Button
        self.btn_zoom_out = QPushButton("")
        self.btn_zoom_out.setIcon(qta.icon('fa5s.search-minus'))
        self.btn_zoom_out.clicked.connect(lambda: self.viewer.zoom_out())
        toolbar_layout_top.addWidget(self.btn_zoom_out)
        
        # Layers Button
        self.btn_layers = QPushButton(" Calques")
        self.btn_layers.setIcon(qta.icon('fa5s.layer-group'))
        self.btn_layers.clicked.connect(self._open_layers_dialog)
        self.btn_layers.setEnabled(False) # Disabled until a DXF is loaded
        toolbar_layout_top.addWidget(self.btn_layers)
        
        # VRD Button
        self.btn_vrd = QPushButton(" Métré VRD")
        self.btn_vrd.setIcon(qta.icon('fa5s.ruler-combined', color='#3498db'))
        self.btn_vrd.clicked.connect(self._open_vrd_dialog)
        self.btn_vrd.setEnabled(False) # Disabled until a DXF is loaded
        toolbar_layout_top.addWidget(self.btn_vrd)
        
        toolbar_layout_top.addStretch()
        
        # Info labels right aligned on top line
        self.lbl_info = QLabel("Aucun fichier chargé.")
        self.lbl_info.setStyleSheet("color: #A0AEC0; font-style: italic;")
        toolbar_layout_top.addWidget(self.lbl_info)

        # 2. Mode Buttons (Bottom Line)
        self.btn_nav = QPushButton(" Naviguer")
        self.btn_nav.setIcon(qta.icon('fa5s.hand-paper'))
        self.btn_nav.setCheckable(True)
        self.btn_nav.setChecked(True)
        self.btn_nav.clicked.connect(lambda: self._set_mode("nav"))
        
        self.btn_dist = QPushButton(" Distance")
        self.btn_dist.setIcon(qta.icon('fa5s.ruler'))
        self.btn_dist.setCheckable(True)
        self.btn_dist.clicked.connect(lambda: self._set_mode("distance"))
        
        self.btn_area = QPushButton(" Surface")
        self.btn_area.setIcon(qta.icon('fa5s.vector-square'))
        self.btn_area.setCheckable(True)
        self.btn_area.clicked.connect(lambda: self._set_mode("area"))
        
        self.btn_coords = QPushButton(" Coords")
        self.btn_coords.setIcon(qta.icon('fa5s.map-marker-alt'))
        self.btn_coords.setCheckable(True)
        self.btn_coords.clicked.connect(lambda: self._set_mode("coords"))
        
        self.btn_info = QPushButton(" Infos")
        self.btn_info.setIcon(qta.icon('fa5s.info-circle'))
        self.btn_info.setCheckable(True)
        self.btn_info.clicked.connect(lambda: self._set_mode("info"))
        
        # Apply button styles for active state
        self._apply_mode_style([self.btn_nav, self.btn_dist, self.btn_area, self.btn_coords, self.btn_info])
        
        toolbar_layout_bottom.addWidget(self.btn_nav)
        toolbar_layout_bottom.addWidget(self.btn_dist)
        toolbar_layout_bottom.addWidget(self.btn_area)
        toolbar_layout_bottom.addWidget(self.btn_coords)
        toolbar_layout_bottom.addWidget(self.btn_info)
        
        toolbar_layout_bottom.addStretch()
        
        main_layout.addWidget(toolbar)
        
        # Secondary Toolbar for Search
        search_toolbar = QFrame()
        search_toolbar.setFixedHeight(50)
        search_toolbar.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border-bottom: 1px solid palette(mid);
            }
        """)
        search_toolbar_layout = QHBoxLayout(search_toolbar)
        search_toolbar_layout.setContentsMargins(15, 5, 15, 5)
        
        lbl_search = QLabel("Recherche Spatiale :")
        lbl_search.setStyleSheet("font-weight: bold;")
        search_toolbar_layout.addWidget(lbl_search)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Entrez un nom de propriétaire, numéro de lot, etc. puis appuyez sur Entrée...")
        self.txt_search.returnPressed.connect(self._on_search)
        search_toolbar_layout.addWidget(self.txt_search)
        
        self.btn_search = QPushButton(" Chercher")
        self.btn_search.setIcon(qta.icon('fa5s.search'))
        self.btn_search.clicked.connect(self._on_search)
        self.btn_search.setEnabled(False)
        self.btn_search.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                background-color: palette(primary);
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
            QPushButton:disabled {
                background-color: palette(midlight);
            }
        """)
        
        search_toolbar_layout.addWidget(self.btn_search)
        
        # Add Theme combo to the right
        search_toolbar_layout.addStretch()
        
        lbl_theme = QLabel("Thème :")
        search_toolbar_layout.addWidget(lbl_theme)
        
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Aucun", "Par Surface", "Par Statut"])
        self.combo_theme.currentTextChanged.connect(self._apply_theme)
        search_toolbar_layout.addWidget(self.combo_theme)
        
        main_layout.addWidget(search_toolbar)

        # Main View Area with Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.viewer = InteractiveDXFView()
        self.viewer.distance_measured.connect(self._on_distance_measured)
        self.viewer.lot_info_found.connect(self._on_lot_info_found)
        self.viewer.lot_coords_found.connect(self._on_lot_coords_found)
        self.splitter.addWidget(self.viewer)
        
        # Attribute Panel
        self.attr_panel = AttributePanelWidget()
        self.attr_panel.attributes_changed.connect(self._apply_theme)
        self.splitter.addWidget(self.attr_panel)
        
        # Set stretch factors (Viewer takes most space)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.splitter)

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
        self.btn_coords.setChecked(mode == "coords")
        self.btn_info.setChecked(mode == "info")
        
        self.viewer.set_mode(mode)
        
        if mode == "nav":
            self.lbl_info.setText("Mode: Panoramique & Zoom")
        elif mode == "distance":
            self.lbl_info.setText("Cliquez sur 2 points pour mesurer la distance.")
        elif mode == "area":
            self.lbl_info.setText("Cliquez à l'intérieur d'un lot pour afficher sa surface.")
        elif mode == "coords":
            self.lbl_info.setText("Cliquez sur un lot pour extraire ses coordonnées.")
        elif mode == "info":
            self.lbl_info.setText("Cliquez sur un lot pour afficher ses propriétés.")

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
                self.btn_layers.setEnabled(True)
                self.btn_vrd.setEnabled(True)
                self.txt_search.setEnabled(True)
                self.btn_search.setEnabled(True)
                self.visible_layers = set(self.viewer.get_layers())
                
                # Charger la base de données locale
                self.attr_panel.load_database(filepath)
            else:
                QMessageBox.critical(self, "Erreur", msg)
                self.lbl_info.setText("Erreur de chargement.")

    def _apply_theme(self, text=None):
        theme = self.combo_theme.currentText()
        self.viewer.apply_theme(theme, self.attr_panel.attributes_db)

    def _on_distance_measured(self, distance):
        self.lbl_info.setText(f"Distance mesurée : {distance:.2f} m")

    def _on_lot_info_found(self, text, area, lot_name=None, ilot_name=None):
        if area > 0:
            self.lbl_info.setText(f"{text} | Surface : {area:.2f} m²")
            if self.viewer.current_mode == "info" and lot_name and ilot_name:
                self.attr_panel.set_selected_lot(ilot_name, lot_name, area)
        else:
            self.lbl_info.setText(text)
            
    def _on_lot_coords_found(self, title, coords):
        if not coords:
            self.lbl_info.setText("Aucun lot trouvé à cet emplacement")
            return
            
        self.lbl_info.setText(f"{title} | {len(coords)} points extraits")
        
        dialog = CoordsDialog(title, coords, self)
        dialog.exec()

    def _open_layers_dialog(self):
        all_layers = self.viewer.get_layers()
        if not all_layers:
            return
            
        dialog = LayersDialog(all_layers, self)
        # Check all layers initially if not set
        if not hasattr(self, 'visible_layers'):
            self.visible_layers = set(all_layers)
            
        dialog.set_visible_layers(self.visible_layers)
        
        def on_layers_changed(visible):
            self.visible_layers = visible
            self.viewer._render_scene(self.visible_layers)
            
        dialog.layers_changed.connect(on_layers_changed)
        dialog.exec()
        
    def _on_search(self):
        query = self.txt_search.text().strip()
        if not query:
            return
            
        found = self.viewer.search_and_zoom(query)
        if not found:
            QMessageBox.information(self, "Recherche", f"Aucun texte correspondant à '{query}' n'a été trouvé.")
        else:
            self.lbl_info.setText(f"Résultat trouvé pour '{query}'")

    def _open_vrd_dialog(self):
        if not self.viewer.doc:
            return
        from .vrd_dialog import VRDDialog
        dialog = VRDDialog(self, self.viewer.doc)
        dialog.exec()

# pyrefly: ignore [missing-import]
from PySide6.QtCore import Signal

class LayersDialog(QDialog):
    layers_changed = Signal(set)
    
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionnaire de Calques")
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.resize(300, 400)
        
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        for layer in layers:
            item = QListWidgetItem(layer)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)
            
        self.list_widget.itemChanged.connect(self._on_item_changed)
            
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        btn_all = QPushButton("Tout cocher")
        btn_none = QPushButton("Tout décocher")
        btn_all.clicked.connect(self.check_all)
        btn_none.clicked.connect(self.uncheck_all)
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_none)
        layout.addLayout(btn_layout)
        
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)

    def _on_item_changed(self, item):
        self.layers_changed.emit(self.get_visible_layers())
        
    def check_all(self):
        self.list_widget.blockSignals(True)
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)
        self.list_widget.blockSignals(False)
        self.layers_changed.emit(self.get_visible_layers())
            
    def uncheck_all(self):
        self.list_widget.blockSignals(True)
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
        self.list_widget.blockSignals(False)
        self.layers_changed.emit(self.get_visible_layers())
            
    def set_visible_layers(self, visible_layers):
        self.list_widget.blockSignals(True)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() in visible_layers:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        self.list_widget.blockSignals(False)
                
    def get_visible_layers(self):
        visible = set()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                visible.add(item.text())
        return visible

class CoordsDialog(QDialog):
    def __init__(self, title, coords, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Coordonnées - {title}")
        self.resize(400, 500)
        self.coords = coords
        
        layout = QVBoxLayout(self)
        
        lbl_desc = QLabel(f"<b>{title}</b><br>{len(coords)} points extraits.")
        layout.addWidget(lbl_desc)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["N°", "X", "Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        self.table.setRowCount(len(coords))
        for i, (x, y) in enumerate(coords):
            item_n = QTableWidgetItem(str(i + 1))
            item_n.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, item_n)
            
            item_x = QTableWidgetItem(f"{x:.3f}")
            item_x.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, item_x)
            
            item_y = QTableWidgetItem(f"{y:.3f}")
            item_y.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, item_y)
            
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        
        self.btn_export = QPushButton(" Exporter en CSV")
        self.btn_export.setIcon(qta.icon('fa5s.file-csv'))
        self.btn_export.clicked.connect(self._export_csv)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        btn_layout.addWidget(self.btn_export)
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
    def _export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exporter les coordonnées", "coordonnees_lot.csv", "Fichiers CSV (*.csv)"
        )
        if not filepath:
            return
            
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Point", "X", "Y"])
                for i, (x, y) in enumerate(self.coords):
                    writer.writerow([i + 1, f"{x:.3f}", f"{y:.3f}"])
            QMessageBox.information(self, "Export réussi", f"Fichier sauvegardé avec succès :\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exportation : {e}")

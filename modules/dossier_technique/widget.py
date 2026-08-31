import sys
import os
import tempfile
import webbrowser
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QMessageBox, QStackedWidget, QComboBox, QSpinBox, QGroupBox, QFormLayout, QApplication, QScrollArea, QListWidget, QListWidgetItem)
# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt
from .core.dxf_parser import DXFParser
from .core.dxf_exporter import DXFExporter
from .core.word_generator import WordGenerator
from .pdf.pdf_generator import PDFGenerator
from .ui.map_viewer import MapViewer
from .ui.form_widget import FormWidget
from modules.viewer_2d.widget import LayersDialog

class DossierTechniqueWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.dxf_parser = None
        self.selected_lots_list = []
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- LEFT PANEL (Stack) ---
        self.left_stack = QStackedWidget()
        self.left_stack.setFixedWidth(520)
        
        # Page 1: Selection
        self.page_selection = QWidget()
        sel_layout = QVBoxLayout(self.page_selection)
        
        self.label_info = QLabel("1. Veuillez charger un fichier DXF de lotissement.")
        self.label_info.setWordWrap(True)
        sel_layout.addWidget(self.label_info)
        
        self.btn_load_dxf = QPushButton("Charger Fichier DXF")
        self.btn_load_dxf.setObjectName("PrimaryButton")
        self.btn_load_dxf.clicked.connect(self.load_dxf)
        sel_layout.addWidget(self.btn_load_dxf)
        
        sel_layout.addSpacing(10)
        
        self.btn_layers = QPushButton(" Calques d'arrière-plan")
        # pyrefly: ignore [missing-import]
        import qtawesome as qta
        self.btn_layers.setIcon(qta.icon('fa5s.layer-group'))
        self.btn_layers.clicked.connect(self._open_layers_dialog)
        self.btn_layers.setEnabled(False)
        sel_layout.addWidget(self.btn_layers)
        
        sel_layout.addSpacing(10)
        
        self.label_sel_count = QLabel("0 lot(s) sélectionné(s)")
        sel_layout.addWidget(self.label_sel_count)
        
        self.btn_process = QPushButton("2. Traiter les lots sélectionnés")
        self.btn_process.setObjectName("PrimaryButton")
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.go_to_edition)
        sel_layout.addWidget(self.btn_process)
        
        sel_layout.addStretch()
        self.left_stack.addWidget(self.page_selection)
        
        # Page 2: Edition
        self.page_edition = QWidget()
        ed_layout = QVBoxLayout(self.page_edition)
        
        self.btn_back_sel = QPushButton("← Retour à la Sélection")
        self.btn_back_sel.clicked.connect(self.go_to_selection)
        ed_layout.addWidget(self.btn_back_sel)
        
        ed_layout.addSpacing(10)
        
        # Scrollable Content
        self.edition_content_widget = QWidget()
        edition_content_layout = QVBoxLayout(self.edition_content_widget)
        edition_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Lot selector
        self.combo_lots = QComboBox()
        self.combo_lots.currentIndexChanged.connect(self.on_edition_lot_changed)
        edition_content_layout.addWidget(QLabel("Lot en cours d'édition :"))
        edition_content_layout.addWidget(self.combo_lots)
        
        # Scale inputs
        scale_group = QGroupBox("Échelles Aperçu")
        scale_layout = QFormLayout(scale_group)
        
        self.spin_scale_5000 = QSpinBox()
        self.spin_scale_5000.setRange(500, 20000)
        self.spin_scale_5000.setSingleStep(500)
        self.spin_scale_5000.setValue(5000)
        self.spin_scale_5000.valueChanged.connect(self.update_map_preview)
        
        self.spin_scale_500 = QSpinBox()
        self.spin_scale_500.setRange(100, 5000)
        self.spin_scale_500.setSingleStep(100)
        self.spin_scale_500.setValue(500)
        self.spin_scale_500.valueChanged.connect(self.update_map_preview)
        
        scale_layout.addRow("Échelle globale (1/) :", self.spin_scale_5000)
        scale_layout.addRow("Échelle détaillée (1/) :", self.spin_scale_500)
        edition_content_layout.addWidget(scale_group)
        
        self.form_widget = FormWidget()
        edition_content_layout.addWidget(self.form_widget)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setWidget(self.edition_content_widget)
        ed_layout.addWidget(self.scroll_area)
        
        self.form_widget.btn_preview.clicked.connect(self.preview_pdf)
        self.form_widget.btn_generate.clicked.connect(self.generate_documents)
        self.form_widget.btn_generate_dxf.clicked.connect(self.generate_dxf)
        
        self.left_stack.addWidget(self.page_edition)
        
        main_layout.addWidget(self.left_stack)
        
        # --- RIGHT PANEL (Map Viewer) ---
        map_layout = QVBoxLayout()
        main_layout.addLayout(map_layout, stretch=1)
        
        # Map Viewer
        self.map_viewer = MapViewer()
        self.map_viewer.selection_changed.connect(self.on_selection_changed)
        self.map_viewer.mouse_moved.connect(self.on_mouse_moved)
        map_layout.addWidget(self.map_viewer)
        
        # Toolbar (Zoom & Coordinates) at the bottom
        toolbar_widget = QWidget()
        toolbar_widget.setFixedHeight(40)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 10, 0, 0)
        
        self.label_coords = QLabel("X: ---  Y: ---")
        self.btn_zoom_center = QPushButton("Centrer Sélection")
        self.btn_zoom_in = QPushButton("Zoom +")
        self.btn_zoom_out = QPushButton("Zoom -")
        
        self.btn_zoom_center.clicked.connect(self.zoom_center)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        toolbar_layout.addWidget(self.label_coords)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_zoom_center)
        toolbar_layout.addWidget(self.btn_zoom_out)
        toolbar_layout.addWidget(self.btn_zoom_in)
        map_layout.addWidget(toolbar_widget)

    def zoom_center(self):
        self.map_viewer.zoom_to_selection()

    def zoom_in(self):
        self.map_viewer.scale(1.15, 1.15)
        
    def zoom_out(self):
        self.map_viewer.scale(1.0 / 1.15, 1.0 / 1.15)

    def on_mouse_moved(self, x, y):
        self.label_coords.setText(f"X: {x:.2f}  Y: {y:.2f}")

    def on_selection_changed(self, lots):
        self.selected_lots_list = lots
        count = len(lots)
        self.label_sel_count.setText(f"{count} lot(s) sélectionné(s)")
        self.btn_process.setEnabled(count > 0)
        
        # Synchronisation en mode édition
        if self.left_stack.currentIndex() == 1 and count == 1:
            ilot_name, lot_name = lots[0]
            combo_text = f"Îlot: {ilot_name} - Lot: {lot_name}"
            index = self.combo_lots.findText(combo_text)
            if index >= 0:
                self.combo_lots.setCurrentIndex(index)

    def go_to_edition(self):
        if not self.selected_lots_list:
            return
            
        self.combo_lots.blockSignals(True)
        self.combo_lots.clear()
        for ilot, lot in self.selected_lots_list:
            self.combo_lots.addItem(f"Îlot: {ilot} - Lot: {lot}", userData=(ilot, lot))
        self.combo_lots.blockSignals(False)
        
        self.left_stack.setCurrentIndex(1)
        # Select first by default
        self.combo_lots.setCurrentIndex(0)
        self.on_edition_lot_changed()

    def go_to_selection(self):
        self.left_stack.setCurrentIndex(0)
        if self.map_viewer.preview_box_5000:
            self.map_viewer.preview_box_5000.hide()
        if self.map_viewer.preview_box_500:
            self.map_viewer.preview_box_500.hide()

    def on_edition_lot_changed(self):
        if self.combo_lots.currentIndex() == -1:
            return
            
        ilot_name, lot_name = self.combo_lots.currentData()
        self.form_widget.lbl_ilot.setText(str(ilot_name))
        self.form_widget.lbl_lot.setText(str(lot_name))
        
        # Mettre à jour la surface
        if self.dxf_parser:
            ilot = self.dxf_parser.ilots.get(ilot_name, {})
            lot_info = ilot.get("lots", {}).get(lot_name)
            if lot_info:
                surface = lot_info['geom'].area
                self.form_widget.lbl_surface.setText(f"{surface:.2f} m²")
        
        # Center map on this lot and update preview
        self.update_map_preview()

    def update_map_preview(self):
        if self.combo_lots.currentIndex() == -1 or not self.dxf_parser:
            return
            
        ilot_name, lot_name = self.combo_lots.currentData()
        ilot = self.dxf_parser.ilots.get(ilot_name, {})
        lot_info = ilot.get("lots", {}).get(lot_name)
        
        if lot_info:
            polygon = lot_info['geom']
            centroid = polygon.centroid
            
            # Simple conversion rule: assume scale dictates paper width coverage
            # Real conversion needs actual paper size / scale. Let's approximate for visual feedback:
            # Paper width ~ 210mm. At 1/1000, 210mm = 210m.
            scale_5000 = self.spin_scale_5000.value()
            scale_500 = self.spin_scale_500.value()
            
            w_5000 = 0.210 * scale_5000
            h_5000 = 0.297 * scale_5000
            
            w_500 = 0.210 * scale_500
            h_500 = 0.297 * scale_500
            
            self.map_viewer.update_preview_boxes(centroid.x, centroid.y, w_5000, h_5000, w_500, h_500)
            self.map_viewer.preview_box_5000.show()
            self.map_viewer.preview_box_500.show()
            
            # Center view slightly
            self.map_viewer.centerOn(centroid.x, -centroid.y)

    def load_dxf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier DXF", "", "Fichiers DXF (*.dxf)")
        if file_path:
            self.label_info.setText(f"Analyse en cours: {os.path.basename(file_path)}")
            QApplication.processEvents()
            
            try:
                self.dxf_parser = DXFParser(file_path)
                success, msg = self.dxf_parser.load()
                
                if success:
                    self.dxf_parser.extract_lots_and_ilots()
                    lots_data = self.dxf_parser.ilots
                    
                    if not lots_data:
                        QMessageBox.warning(self, "Attention", "Aucun îlot ou lot trouvé dans ce fichier.")
                        self.label_info.setText("Fichier vide ou aucun lot détecté.")
                        self.map_viewer.scene.clear()
                        return
                    
                    self.map_viewer.draw_lots(lots_data)
                    self.map_viewer.draw_background_layers(self.dxf_parser.background_layers)
                    
                    self.btn_layers.setEnabled(True)
                    self.visible_layers = set(self.dxf_parser.background_layers.keys())
                    
                    self.label_info.setText(f"Fichier chargé: {os.path.basename(file_path)}")
                    self.selected_lots_list = []
                    self.on_selection_changed([])
                    self.btn_process.setEnabled(False)
                else:
                    QMessageBox.critical(self, "Erreur", msg)
                    self.label_info.setText("Erreur de chargement.")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'analyse du fichier DXF:\n{str(e)}")
                self.label_info.setText("Erreur de chargement.")

    def _open_layers_dialog(self):
        all_layers = list(self.dxf_parser.background_layers.keys())
        if not all_layers:
            return
            
        # pyrefly: ignore [missing-import]
        from PySide6.QtWidgets import QDialog
        dialog = LayersDialog(all_layers, self)
        
        if not hasattr(self, 'visible_layers'):
            self.visible_layers = set(all_layers)
            
        dialog.set_visible_layers(self.visible_layers)
        
        def on_layers_changed(visible):
            self.visible_layers = visible
            for layer_name in all_layers:
                self.map_viewer.toggle_layer(layer_name, layer_name in self.visible_layers)
                
        dialog.layers_changed.connect(on_layers_changed)
        dialog.exec()

    def preview_pdf(self):
        try:
            self._generate_pdf(preview=True)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'aperçu PDF:\n{str(e)}")

    def generate_documents(self):
        if not self.dxf_parser or self.combo_lots.currentIndex() == -1:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un lot valide avant de générer les documents.")
            return
            
        try:
            pdf_path = self._generate_pdf(preview=False)
            word_path = self._generate_word()
            QMessageBox.information(self, "Succès", "Génération des documents terminée avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération des documents:\n{str(e)}")

    def _generate_pdf(self, preview=False):
        if not self.dxf_parser:
            raise Exception("Aucun fichier DXF n'a été chargé.")
            
        data = self.form_widget.get_data()
        ilot_name = data.get("ilot")
        lot_name = data.get("lot")
        
        ilot = self.dxf_parser.ilots.get(ilot_name, {})
        lot_info = ilot.get("lots", {}).get(lot_name)
        
        if not lot_info:
            raise Exception(f"Les informations pour l'îlot {ilot_name} / lot {lot_name} ne sont pas disponibles.")
            
        data["bornes"] = lot_info.get("bornes", [])
        data["scale_5000"] = self.spin_scale_5000.value()
        data["scale_500"] = self.spin_scale_500.value()
        
        voisins = {}
        for name, v_info in ilot.get("lots", {}).items():
            if name != lot_name:
                voisins[name] = v_info.get("bornes", [])
        data["voisins"] = voisins
        
        out_dir = self.form_widget.get_output_dir()
        pdf_gen = PDFGenerator(output_dir=tempfile.gettempdir() if preview else out_dir)
        prefix = "preview_" if preview else "DT_"
        pdf_filename = f"{prefix}{ilot_name}_{lot_name}.pdf"
        output_path = pdf_gen.generate_pdf(pdf_filename, data)
        
        if preview:
            # pyrefly: ignore [missing-import]
            from PySide6.QtGui import QDesktopServices
            # pyrefly: ignore [missing-import]
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
        return output_path

    def _generate_word(self):
        if not self.dxf_parser:
            raise Exception("Aucun fichier DXF n'a été chargé.")
            
        data = self.form_widget.get_data()
        ilot_name = data.get("ilot")
        lot_name = data.get("lot")
        
        ilot = self.dxf_parser.ilots.get(ilot_name, {})
        lot_info = ilot.get("lots", {}).get(lot_name)
        
        if not lot_info:
            raise Exception(f"Les informations pour l'îlot {ilot_name} / lot {lot_name} ne sont pas disponibles.")
            
        data["bornes"] = lot_info.get("bornes", [])
        data["scale_5000"] = self.spin_scale_5000.value()
        data["scale_500"] = self.spin_scale_500.value()
        
        voisins = {}
        for name, v_info in ilot.get("lots", {}).items():
            if name != lot_name:
                voisins[name] = v_info.get("bornes", [])
        data["voisins"] = voisins
        
        out_dir = self.form_widget.get_output_dir()
        word_gen = WordGenerator(output_dir=out_dir)
        word_filename = f"DT_{ilot_name}_{lot_name}.docx"
        return word_gen.generate_word(word_filename, data)

    def generate_dxf(self):
        if not self.dxf_parser or self.combo_lots.currentIndex() == -1:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un lot valide avant de générer le DXF.")
            return
            
        try:
            data = self.form_widget.get_data()
            ilot_name = data.get("ilot")
            lot_name = data.get("lot")
            
            ilot = self.dxf_parser.ilots.get(ilot_name, {})
            lot_info = ilot.get("lots", {}).get(lot_name)
            
            if not lot_info:
                QMessageBox.warning(self, "Attention", "Données du lot non trouvées.")
                return
                
            voisins = {}
            for name, v_info in ilot.get("lots", {}).items():
                if name != lot_name:
                    voisins[name] = v_info.get("bornes", [])
            data["voisins"] = voisins
            
            exporter = DXFExporter()
            out_dir = self.form_widget.get_output_dir()
            output_filename = os.path.join(out_dir, f"Extrait_{ilot_name}_Lot_{lot_name}.dxf")
            exporter.export_lot(output_filename, lot_info, data)
            QMessageBox.information(self, "Succès", f"Fichier {output_filename} généré avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du fichier DXF:\n{str(e)}")

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QHBoxLayout)
import os
import tempfile
import webbrowser
from core.dxf_parser import DXFParser
from core.dxf_exporter import DXFExporter
from pdf.pdf_generator import PDFGenerator
from ui.map_viewer import MapViewer
from ui.form_widget import FormWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CadGen Studio Desktop")
        self.resize(1024, 768)
        self.dxf_parser = None
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.label_info = QLabel("Veuillez charger un fichier DXF de lotissement.")
        layout.addWidget(self.label_info)
        
        self.btn_load_dxf = QPushButton("Charger Fichier DXF")
        self.btn_load_dxf.clicked.connect(self.load_dxf)
        layout.addWidget(self.btn_load_dxf)
        
        # Layout principal horizontal
        h_layout = QHBoxLayout()
        layout.addLayout(h_layout)
        
        # Map Layout
        map_layout = QVBoxLayout()
        h_layout.addLayout(map_layout, stretch=2)
        
        # Remplacer le placeholder par MapViewer
        self.map_viewer = MapViewer()
        self.map_viewer.lot_selected.connect(self.on_lot_selected)
        map_layout.addWidget(self.map_viewer)
        
        # Boutons de Zoom
        zoom_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton("Zoom In (+)")
        self.btn_zoom_out = QPushButton("Zoom Out (-)")
        zoom_layout.addWidget(self.btn_zoom_in)
        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addStretch()
        map_layout.addLayout(zoom_layout)
        
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        # Ajouter le formulaire à droite
        self.form_widget = FormWidget()
        h_layout.addWidget(self.form_widget, stretch=1)
        
        self.form_widget.btn_preview.clicked.connect(self.preview_pdf)
        self.form_widget.btn_generate.clicked.connect(self.generate_documents)

    def zoom_in(self):
        self.map_viewer.scale(1.15, 1.15)
        
    def zoom_out(self):
        self.map_viewer.scale(1.0 / 1.15, 1.0 / 1.15)

    def preview_pdf(self):
        data = self.form_widget.get_data()
        ilot_name = data.get("ilot")
        lot_name = data.get("lot")
        
        if ilot_name == "-" or lot_name == "-":
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un lot sur la carte.")
            return
            
        ilot = self.dxf_parser.ilots.get(ilot_name, {})
        lot_info = ilot.get("lots", {}).get(lot_name)
        
        if lot_info:
            data["bornes"] = lot_info.get("bornes", [])
            pdf_gen = PDFGenerator(output_dir=tempfile.gettempdir())
            pdf_filename = f"preview_{ilot_name}_{lot_name}.pdf"
            output_path = pdf_gen.generate_pdf(pdf_filename, data)
            
            # Ouvrir avec l'afficheur système
            webbrowser.open(f"file://{output_path}")

    def generate_documents(self):
        data = self.form_widget.get_data()
        ilot_name = data.get("ilot")
        lot_name = data.get("lot")
        
        if ilot_name == "-" or lot_name == "-":
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un lot sur la carte.")
            return
            
        ilot = self.dxf_parser.ilots.get(ilot_name, {})
        lot_info = ilot.get("lots", {}).get(lot_name)
        
        if lot_info:
            data["bornes"] = lot_info.get("bornes", [])
            
            # Export DXF
            dxf_exporter = DXFExporter(output_dir=".")
            dxf_filename = f"Extrait_{ilot_name}_{lot_name}.dxf"
            dxf_exporter.export_lot(dxf_filename, lot_info)
            
            # Export PDF
            pdf_gen = PDFGenerator(output_dir=".")
            pdf_filename = f"DT_{ilot_name}_{lot_name}.pdf"
            pdf_gen.generate_pdf(pdf_filename, data)
            
            QMessageBox.information(self, "Succès", f"Fichiers générés:\n- {dxf_filename}\n- {pdf_filename}")
            
    def on_lot_selected(self, ilot_name, lot_name):
        self.label_info.setText(f"Sélection: Ilot {ilot_name} - Lot {lot_name}")
        
        # Retrieve lot geometry to get area
        if self.dxf_parser and ilot_name in self.dxf_parser.ilots:
            ilot = self.dxf_parser.ilots[ilot_name]
            if lot_name in ilot["lots"]:
                lot_info = ilot["lots"][lot_name]
                surface = lot_info["geom"].area
                self.form_widget.update_selection(ilot_name, lot_name, surface)

    def load_dxf(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Ouvrir DXF", "", "Fichiers DXF (*.dxf)")
        if filepath:
            self.label_info.setText(f"Chargement en cours : {filepath}")
            self.dxf_parser = DXFParser(filepath)
            success, msg = self.dxf_parser.load()
            
            if success:
                # Extraire les géométries
                self.dxf_parser.extract_lots_and_ilots()
                nb_ilots = len(self.dxf_parser.ilots)
                
                # Mettre à jour l'affichage
                self.map_viewer.draw_lots(self.dxf_parser.ilots)
                
                QMessageBox.information(self, "Succès", f"{msg}\nIlots extraits: {nb_ilots}")
                self.label_info.setText(f"Fichier chargé: {filepath} | {nb_ilots} îlots")
            else:
                QMessageBox.critical(self, "Erreur", msg)
                self.label_info.setText("Erreur lors du chargement.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

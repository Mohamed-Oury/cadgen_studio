import ezdxf
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

class VRDDialog(QDialog):
    def __init__(self, parent, doc):
        super().__init__(parent)
        self.doc = doc
        self.setWindowTitle("Calcul de Métré VRD")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        
        self.layout = QVBoxLayout(self)
        
        self.lbl_info = QLabel("Cochez les calques correspondant à vos réseaux pour calculer la longueur totale :")
        self.lbl_info.setWordWrap(True)
        self.layout.addWidget(self.lbl_info)
        
        # Liste des calques
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        
        self._populate_layers()
        
        # Resultat
        self.lbl_result = QLabel("Longueur totale : 0.00 m")
        self.lbl_result.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; color: #2980b9;")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_result)
        
        # Boutons
        btn_layout = QHBoxLayout()
        self.btn_calc = QPushButton("Calculer le Métré")
        self.btn_calc.clicked.connect(self._calculate_length)
        self.btn_calc.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("padding: 8px;")
        
        btn_layout.addWidget(self.btn_calc)
        btn_layout.addWidget(self.btn_close)
        
        self.layout.addLayout(btn_layout)
        
    def _populate_layers(self):
        if not self.doc:
            return
            
        # Get unique layers from modelspace entities rather than just doc.layers 
        # to ensure we only show layers that actually contain entities
        msp = self.doc.modelspace()
        active_layers = set()
        for entity in msp:
            if hasattr(entity.dxf, 'layer'):
                active_layers.add(entity.dxf.layer)
                
        for layer in sorted(active_layers):
            item = QListWidgetItem(layer)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
            
    def _calculate_length(self):
        if not self.doc:
            return
            
        selected_layers = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_layers.append(item.text())
                
        if not selected_layers:
            QMessageBox.warning(self, "Attention", "Veuillez cocher au moins un calque.")
            return
            
        total_length = 0.0
        msp = self.doc.modelspace()
        
        for entity in msp:
            if hasattr(entity.dxf, 'layer') and entity.dxf.layer in selected_layers:
                try:
                    if entity.dxftype() == 'LINE':
                        start = entity.dxf.start
                        end = entity.dxf.end
                        # Using 2D distance
                        length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
                        total_length += length
                        
                    elif entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                        points = list(entity.vertices())
                        for i in range(len(points) - 1):
                            p1 = points[i]
                            p2 = points[i+1]
                            
                            x1, y1 = (p1.dxf.location.x, p1.dxf.location.y) if hasattr(p1, 'dxf') else (p1[0], p1[1])
                            x2, y2 = (p2.dxf.location.x, p2.dxf.location.y) if hasattr(p2, 'dxf') else (p2[0], p2[1])
                            
                            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                            total_length += length
                            
                        # Si fermée, rajouter la distance entre le dernier et le premier point
                        if entity.is_closed:
                            p1 = points[-1]
                            p2 = points[0]
                            x1, y1 = (p1.dxf.location.x, p1.dxf.location.y) if hasattr(p1, 'dxf') else (p1[0], p1[1])
                            x2, y2 = (p2.dxf.location.x, p2.dxf.location.y) if hasattr(p2, 'dxf') else (p2[0], p2[1])
                            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                            total_length += length
                            
                    elif entity.dxftype() == 'ARC':
                        # L'arc est défini par un rayon et des angles en degrés
                        import math
                        radius = entity.dxf.radius
                        start_angle = entity.dxf.start_angle
                        end_angle = entity.dxf.end_angle
                        
                        # Gestion du sens trigo
                        diff = end_angle - start_angle
                        if diff < 0:
                            diff += 360
                            
                        # Arc length = R * Theta (en radians)
                        length = radius * math.radians(diff)
                        total_length += length
                except Exception as e:
                    print(f"Erreur lors du calcul sur une entité {entity.dxftype()}: {e}")
                    
        self.lbl_result.setText(f"Longueur totale : {total_length:,.2f} m".replace(',', ' '))

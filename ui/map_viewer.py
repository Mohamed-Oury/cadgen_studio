from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QPainter
from PySide6.QtCore import Qt, QPointF, Signal

class MapViewer(QGraphicsView):
    lot_selected = Signal(str, str)  # Emit (ilot_name, lot_name)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Panning and zooming state
        self._is_panning = False
        self._last_pan_point = None

        self.lot_items = {}
        
    def draw_lots(self, lots_data):
        self.scene.clear()
        self.lot_items.clear()
        
        default_pen = QPen(Qt.black)
        default_pen.setWidth(0) # Cosmetic pen (1 pixel regardless of zoom)
        
        default_brush = QBrush(QColor(200, 220, 255, 100)) # Light blue with alpha
        
        for ilot_name, ilot_data in lots_data.items():
            for lot_name, lot_info in ilot_data.get('lots', {}).items():
                polygon = lot_info['geom']
                
                # Convert shapely polygon to QPolygonF
                qpoly = QPolygonF()
                for x, y in polygon.exterior.coords:
                    # Y axis is inverted in QGraphicsView compared to standard cartesian
                    qpoly.append(QPointF(x, -y))
                    
                item = QGraphicsPolygonItem(qpoly)
                item.setPen(default_pen)
                item.setBrush(default_brush)
                item.setFlag(QGraphicsItem.ItemIsSelectable)
                
                # Store data in item for click events
                item.setData(0, ilot_name)
                item.setData(1, lot_name)
                
                self.scene.addItem(item)
                self.lot_items[(ilot_name, lot_name)] = item
                
        # Fit view to scene
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, QGraphicsPolygonItem):
                ilot_name = item.data(0)
                lot_name = item.data(1)
                
                # Reset previous selection styles
                for i in self.scene.items():
                    if isinstance(i, QGraphicsPolygonItem):
                        i.setBrush(QBrush(QColor(200, 220, 255, 100)))
                        
                # Highlight selected
                item.setBrush(QBrush(QColor(255, 100, 100, 150))) # Reddish
                
                self.lot_selected.emit(ilot_name, lot_name)
